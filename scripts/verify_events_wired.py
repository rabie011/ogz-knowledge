#!/usr/bin/env python3
"""
verify_events_wired.py  —  B121 (Immune System)
Orphaned-send / events-integrity audit over clients/*/events/*.jsonl + pick_set records.

WHY (Rule #6 Consumer Law + Rule #8 Refuse-don't-warn): a send with no terminal event is a
SEVERED WIRE — the #1 recurring scar of the orchestra (the gold wire shipped severed 3×; his
portal rulings sat unconsumed). This audit makes that class of bug impossible to ship silently.

It REFUSES (exit 1) only on the DANGEROUS, unambiguous failures — never on legacy schema gaps:
  ERROR (ship-blocking):
    • a ledger line that does not parse as JSON               (corruption)
    • a confirmer==mohamed event NOT stamped CONFIRMED        (his tap left provisional = revertible/lost)
    • a pick_selected that selected nothing                   (severed gold wire)
    • a send/pick_set with a send_id no terminal event resolves  (orphaned send)
  WARN (surfaced, non-blocking):
    • a missing required field on a pre-schema legacy line
    • an unknown event type

Usage:
  python3 scripts/verify_events_wired.py          # human audit, exit 0/1
  python3 scripts/verify_events_wired.py --json    # machine-readable summary
"""
import json, glob, os, sys, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REQUIRED_KEYS = ("ts", "type", "confirmer", "stamp")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
KNOWN_TYPES = {
    "voice_rating", "compare_verdict", "version_verdict", "occasion_gold", "intake_answer",
    "pick_selected", "crystallize_accepted", "red_line_added", "batch_rating",
    "competitor_reference", "send", "pick_set",
}
# forward-looking: events that record a SEND awaiting a terminal, keyed by send_id (or subject).
# A send is resolved by ANY later event carrying  resolves == <send_id>.
SEND_TYPES = {"send", "pick_set"}
RESOLVE_KEY = "resolves"


def audit(repo=REPO):
    """Returns (findings, stats). findings = [(severity, ledger_rel, line_no, msg), ...]."""
    findings = []
    stats = {"ledgers": 0, "events": 0, "mohamed_terminals": 0,
             "picks": 0, "sends": 0, "orphans": 0}
    repo = Path(repo)
    for lf in sorted(glob.glob(str(repo / "clients/*/events/*.jsonl"))):
        stats["ledgers"] += 1
        rel = os.path.relpath(lf, repo)
        sends = {}          # send_id -> line_no
        resolved = set()    # send_ids that some terminal event resolves
        with open(lf, encoding="utf-8") as fh:
            for n, raw in enumerate(fh, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    e = json.loads(raw)
                except Exception as ex:
                    findings.append(("ERROR", rel, n, f"unparseable JSON: {ex}"))
                    continue
                stats["events"] += 1

                # schema (legacy gaps = WARN, never ship-blocking)
                for k in REQUIRED_KEYS:
                    if not e.get(k):
                        findings.append(("WARN", rel, n, f"missing required field '{k}'"))
                if e.get("ts") and not TS_RE.match(str(e["ts"])):
                    findings.append(("WARN", rel, n, f"malformed ts: {e['ts']!r}"))
                t = e.get("type")
                if t and t not in KNOWN_TYPES:
                    findings.append(("WARN", rel, n, f"unknown event type: {t!r}"))

                # DANGEROUS classes = ERROR
                if e.get("confirmer") == "mohamed":
                    stats["mohamed_terminals"] += 1
                    if "CONFIRMED" not in str(e.get("stamp", "")).upper():
                        findings.append(("ERROR", rel, n,
                            f"mohamed decision not CONFIRMED-stamped: stamp={e.get('stamp')!r}"))
                if t == "pick_selected":
                    stats["picks"] += 1
                    if not (e.get("line") or e.get("note") or e.get("subject")):
                        findings.append(("ERROR", rel, n,
                            "pick_selected selected nothing (no line/note/subject) — severed wire"))

                # send / terminal bookkeeping
                if t in SEND_TYPES:
                    stats["sends"] += 1
                    sid = e.get("send_id") or e.get("subject")
                    if sid:
                        sends[sid] = n
                    else:
                        findings.append(("ERROR", rel, n,
                            f"{t} has no send_id/subject — cannot be tracked to a terminal"))
                r = e.get(RESOLVE_KEY)
                if r:
                    resolved.add(r)

        for sid, n in sends.items():
            if sid not in resolved:
                stats["orphans"] += 1
                findings.append(("ERROR", rel, n,
                    f"orphaned send {sid!r} — no terminal event resolves it (Rule #6)"))
    return findings, stats


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    findings, stats = audit()
    errors = [f for f in findings if f[0] == "ERROR"]
    if "--json" in argv:
        print(json.dumps({
            "stats": stats, "errors": len(errors),
            "findings": [{"sev": s, "ledger": l, "line": ln, "msg": m} for s, l, ln, m in findings],
        }, ensure_ascii=False))
    else:
        print("=" * 60)
        print("EVENTS-WIRED AUDIT (B121) — orphaned-send / integrity")
        print("=" * 60)
        print(f"ledgers={stats['ledgers']} events={stats['events']} "
              f"mohamed_terminals={stats['mohamed_terminals']} picks={stats['picks']} "
              f"sends={stats['sends']} orphans={stats['orphans']}")
        for s, l, ln, m in findings:
            print(f"  {'❌' if s == 'ERROR' else '⚠️ '} {l}:{ln} — {m}")
        print("\n✅ all events wired — no orphaned sends, no severed terminals"
              if not errors else f"\n❌ {len(errors)} integrity violation(s) — REFUSING (Rule #8)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
