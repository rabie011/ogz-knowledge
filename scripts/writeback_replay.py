#!/usr/bin/env python3
"""B082 — writeback_replay.py: the nightly replay core (June 19, RABIE's pick).

Replays each client's HUMAN-CONFIRMED ledger verdicts into DERIVED organ state:

  1. truth_pack — a `truth_confirmed` event promotes a matching product_candidate's
     provenance.confidence candidate→confirmed and lifts it into the `confirmed` list.
     (Covers "promote provenance confidences" + "confirm truth_pack".)

  2. taste.json kills — a verdict event carrying a `reason_code` that is a KNOWN
     founder_taste kill slug propagates that slug into the client's taste.kills.
     It NEVER invents a kill: only a slug that already exists in data/founder_taste.json
     and is carried in the STRUCTURED reason_code field (never parsed from free text) can
     propagate (Rule #9 — no metric/state from unverified substrings).

IDEMPOTENT BY DESIGN: derived additions are recomputed from the FULL ledger every run and
written only when they change (organ_write → versioned + atomic). Re-running yields the
same organs and no new events. Every applied change appends a writeback event to
events/writeback.jsonl (deduped by a content key) — the human ledger stays human-hands-only
(B156). Replay never invents, never double-applies.

CONSUMER (Rule #6 — a writer ships with its reader): the derived state this writes is read
downstream — taste.kills by the caption/visual guards, truth_pack.confirmed by the renderer
and truth guards. The output is consumed the same cycle; no severed wire.

Usage:
    python3 scripts/writeback_replay.py                 # replay every pilot client
    python3 scripts/writeback_replay.py --handle eatjurisha
    python3 scripts/writeback_replay.py --dry-run       # report changes, write nothing
"""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent

# A verdict counts only if a HUMAN confirmed it. Provisional (RABIE) verdicts and machine
# rows never move derived state — trust moves on human hands only (B156, mirrors approvers).
_HUMAN_CONFIRMERS = {"mohamed", "client", "mohamed_client", "alhareth"}


def _norm(s) -> str:
    return (s or "").strip()


def _is_confirmed(ev: dict) -> bool:
    if ev.get("confirmer") in _HUMAN_CONFIRMERS:
        return True
    stamp = str(ev.get("stamp", "")).upper()
    # explicit human stamp; PROVISIONAL stamps are excluded
    return stamp.startswith("CONFIRMED BY") and "PROVISIONAL" not in stamp


def _founder_kill_vocab() -> set:
    """The ONLY kill slugs allowed to propagate — the confirmed founder vocabulary."""
    d = json.loads((BASE / "data/founder_taste.json").read_text())
    return {_norm(k.get("name")) for k in d.get("kills", []) if k.get("name")}


def load_crosswalk(founder_kills: set) -> dict:
    """The CONFIRMED reason_code → founder-kill translation (B083 severed-wire fix).

    The three live reason_code vocabularies (portal answers, client-ledger events, founder
    kills) are disjoint, so a kill never propagates by raw-name match. This returns ONLY the
    entries Mohamed has CONFIRMED (status=='confirmed') whose target is a real founder-kill
    slug — proposals and nulls translate to nothing (Rule #12: we never author taste; his tap
    flips a proposal to confirmed). Empty until he taps → propagation stays an honest 0."""
    path = BASE / "data/reason_code_crosswalk.json"
    if not path.exists():
        return {}
    try:
        rows = json.loads(path.read_text()).get("map", [])
    except Exception:
        return {}
    out = {}
    for r in rows:
        if r.get("status") != "confirmed":
            continue
        code = _norm(r.get("code"))
        kill = _norm(r.get("proposed_kill"))
        if code and kill and kill in founder_kills:
            out[code] = kill
    return out


def _change_key(handle: str, kind: str, subject: str) -> str:
    raw = f"{handle}|{kind}|{subject}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def derive(events, truth_pack: dict, taste: dict, founder_kills: set, crosswalk: dict | None = None):
    """PURE core — no IO, no clock. Returns (new_truth_pack, new_taste, changes).

    Deterministic and idempotent: it re-derives the additions from the full event list,
    so applying the result twice produces no further changes. `changes` is the list of
    derivations made *relative to the organs passed in*.
    """
    tp = json.loads(json.dumps(truth_pack))   # deep copy — never mutate caller's dict
    ts = json.loads(json.dumps(taste))
    crosswalk = crosswalk or {}
    changes = []

    candidates = tp.setdefault("product_candidates", [])
    confirmed = tp.setdefault("confirmed", [])
    confirmed_names = {_norm(c.get("name")) for c in confirmed}
    kills = ts.setdefault("kills", [])

    for ev in events:
        if not _is_confirmed(ev):
            continue
        etype = ev.get("type")
        subj = _norm(ev.get("subject"))

        # 1. truth_pack provenance promotion: truth_confirmed → candidate becomes confirmed
        if etype == "truth_confirmed" and subj:
            for cand in candidates:
                if _norm(cand.get("name")) != subj:
                    continue
                prov = cand.setdefault("provenance", {})
                if prov.get("confidence") != "confirmed":
                    prov["confidence"] = "confirmed"
                    prov["promoted_by"] = "writeback_replay"
                    changes.append({"kind": "provenance_promoted", "subject": subj,
                                    "confirmer": ev.get("confirmer")})
            if subj not in confirmed_names:
                confirmed.append({
                    "name": subj,
                    "source": "writeback:truth_confirmed",
                    "confirmer": ev.get("confirmer"),
                    "confidence": "confirmed",
                    "date": ev.get("ts"),
                })
                confirmed_names.add(subj)
                changes.append({"kind": "truth_confirmed", "subject": subj,
                                "confirmer": ev.get("confirmer")})

        # 2. taste kills propagation: a STRUCTURED reason_code that is — directly OR via the
        #    CONFIRMED crosswalk — a known founder kill. The crosswalk translates the live
        #    verdict vocabularies (too_generic, cliche, ...) into founder-kill slugs; without
        #    it the wire is severed (B083), because the vocabularies are disjoint.
        rc = _norm(ev.get("reason_code"))
        mapped = rc if rc in founder_kills else crosswalk.get(rc)
        if mapped and mapped in founder_kills and mapped not in kills:
            kills.append(mapped)
            changes.append({"kind": "kill_propagated", "subject": mapped,
                            "confirmer": ev.get("confirmer"),
                            "via": ("crosswalk:" + rc) if mapped != rc else "direct"})

    return tp, ts, changes


def _load_writeback_keys(handle: str) -> set:
    wf = BASE / "clients" / handle / "events/writeback.jsonl"
    if not wf.exists():
        return set()
    keys = set()
    for ln in wf.read_text().splitlines():
        try:
            keys.add(json.loads(ln).get("key"))
        except Exception:
            pass
    return keys


def replay_client(handle: str, dry_run: bool = False) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    tp_path, taste_path = pdir / "truth_pack.json", pdir / "taste.json"
    if not tp_path.exists() or not taste_path.exists():
        return {"handle": handle, "skipped": "missing organs", "changes": []}

    ledger = BASE / "clients" / handle / "events/ledger.jsonl"
    events = []
    if ledger.exists():
        for ln in ledger.read_text().splitlines():
            ln = ln.strip()
            if ln:
                try:
                    events.append(json.loads(ln))
                except Exception:
                    pass

    truth_pack = json.loads(tp_path.read_text())
    taste = json.loads(taste_path.read_text())
    founder_kills = _founder_kill_vocab()
    crosswalk = load_crosswalk(founder_kills)

    new_tp, new_taste, changes = derive(events, truth_pack, taste, founder_kills, crosswalk)

    # B102: project HUMAN-CONFIRMED intake answers into red_lines / goals / fingerprint.
    # The reader (Rule #6) that actually runs the intake projector — without this, a confirmed
    # answer dies in the ledger. Acts only on intake_answer events carrying a routing target.
    from intake_projection import project_intake, ALLOWED_TARGETS
    intake_organs = {}
    for t in ALLOWED_TARGETS:
        p = pdir / (t + ".json")
        if p.exists():
            intake_organs[t] = json.loads(p.read_text())
    new_intake, intake_changes = project_intake(events, intake_organs)
    changes = changes + intake_changes

    if dry_run or not changes:
        return {"handle": handle, "changes": changes, "wrote": False}

    from organ_write import write_organ
    if new_tp != truth_pack:
        write_organ(tp_path, new_tp)
    if new_taste != taste:
        write_organ(taste_path, new_taste)
    for t, new_organ in new_intake.items():
        if new_organ != intake_organs.get(t):
            write_organ(pdir / (t + ".json"), new_organ)

    # every applied change → a deduped writeback event (NOT the human ledger)
    seen = _load_writeback_keys(handle)
    wf = BASE / "clients" / handle / "events/writeback.jsonl"
    wf.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(wf, "a") as f:
        for ch in changes:
            key = _change_key(handle, ch["kind"], ch["subject"])
            if key in seen:
                continue
            seen.add(key)
            # B084b: this is a MACHINE replay record, not a human tap. confirmer is the
            # SYSTEM; the human who confirmed the underlying ledger verdict is preserved in
            # source_confirmer (provenance only). If we wrote confirmer="mohamed" here, the
            # events-integrity audit (verify_events_wired, which scans events/*.jsonl incl.
            # this file) would read it as his decision left un-CONFIRMED-stamped — a false
            # red AND an impersonation of his tap. Mirror writeback_moments.py.
            f.write(json.dumps({
                "ts": ch.get("ts") or date.today().isoformat(),
                "type": "writeback_" + ch["kind"],
                "subject": ch["subject"],
                "confirmer": "writeback_replay",
                "source_confirmer": ch.get("confirmer"),
                "stamp": "DERIVED (writeback_replay)",
                "source": "writeback_replay",
                "key": key,
            }, ensure_ascii=False) + "\n")
            written += 1
    return {"handle": handle, "changes": changes, "wrote": True, "events_appended": written}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", help="one client; default = all pilots")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.handle:
        handles = [args.handle]
    else:
        handles = sorted(p.name for p in (BASE / "clients").iterdir()
                         if p.is_dir() and (p / "profile/truth_pack.json").exists())

    total = 0
    for h in handles:
        r = replay_client(h, dry_run=args.dry_run)
        n = len(r.get("changes", []))
        total += n
        tag = "DRY" if args.dry_run else ("WROTE" if r.get("wrote") else "no-op")
        if r.get("skipped"):
            tag = "skip:" + r["skipped"]
        print(f"  {h}: {n} change(s) [{tag}]")
        for ch in r.get("changes", []):
            print(f"      → {ch['kind']}: {ch['subject']}")
    print(f"\nwriteback_replay: {total} derivation(s) across {len(handles)} client(s)"
          + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
