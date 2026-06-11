#!/usr/bin/env python3
"""THE CRYSTALLIZE LOOP (cross-client learning — RABIE's pyramid addition, June 11).
Mohamed's Rule #4 step 7 (every pain becomes a permanent rule) applied across clients:
scan ALL clients' append-only event ledgers; any coded rejection reason appearing
≥3 times ACROSS clients drafts a kill/default-change card — queued to Mohamed as a
60-second yes/no. The machine drafts; only Mohamed crystallizes (no AI rule-making).

Codes counted (from the pyramid's rejection-recovery play):
  culture_breach | off_voice | wrong_goal | too_generic | factual_error | unexplained
Usage: python3 scripts/crystallize_loop.py            # scan + draft
"""
import json, glob, collections
from pathlib import Path

BASE = Path(__file__).parent.parent
TODAY = "2026-06-11"
THRESHOLD = 3
CODES = {"culture_breach", "off_voice", "wrong_goal", "too_generic", "factual_error", "unexplained"}


def scan() -> dict:
    """Count coded reasons across every client ledger. Returns code → [(client, ts, note)]."""
    hits = collections.defaultdict(list)
    for lf in glob.glob(str(BASE / "clients/*/events/*.jsonl")):
        client = Path(lf).parts[-3]
        for line in open(lf):
            try:
                e = json.loads(line)
            except Exception:
                continue
            code = e.get("reason_code")
            if code in CODES:
                hits[code].append({"client": client, "ts": e.get("ts"), "note": (e.get("note") or "")[:80]})
    return hits


def draft_cards(hits: dict) -> list:
    """≥THRESHOLD occurrences across ≥2 clients → a draft card for Mohamed. Never auto-applies."""
    cards = []
    for code, evs in hits.items():
        clients = {e["client"] for e in evs}
        if len(evs) >= THRESHOLD and len(clients) >= 2:
            cards.append({
                "draft": f"founder_taste candidate: recurring '{code}' ({len(evs)}x across {len(clients)} clients)",
                "evidence": evs[:5],
                "proposed_action": {"culture_breach": "new cultural default (strictest) — and park the theme",
                                      "too_generic": "new kill pattern from the common shape of these rejections",
                                      "factual_error": "truth-gate tightening at the failing node",
                                      "off_voice": "voice-law amendment proposal (hate-line candidates)",
                                      "wrong_goal": "goal-ratio gate tightening",
                                      "unexplained": "human call — pattern exists but reason unknown"}.get(code, "review"),
                "status": "DRAFT — Mohamed's yes/no only",
                "drafted": TODAY,
            })
    return cards


def main():
    hits = scan()
    total = sum(len(v) for v in hits.values())
    print(f"scanned ledgers: {len(glob.glob(str(BASE / 'clients/*/events/*.jsonl')))} files, {total} coded events")
    for code, evs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        print(f"  {code}: {len(evs)} ({len({e['client'] for e in evs})} clients)")
    cards = draft_cards(hits)
    out = BASE / "data/crystallize_queue.json"
    existing = json.loads(out.read_text()) if out.exists() else {"cards": []}
    seen = {c["draft"] for c in existing["cards"]}
    new = [c for c in cards if c["draft"] not in seen]
    existing["cards"] += new
    existing["last_run"] = TODAY
    out.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    print(f"\n{len(new)} new draft cards → data/crystallize_queue.json (queue total: {len(existing['cards'])})")
    if not total:
        print("honest state: ledgers are young — the machine waits for real verdicts. It runs; it does not invent.")


if __name__ == "__main__":
    main()
