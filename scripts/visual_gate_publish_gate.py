#!/usr/bin/env python3
"""VISUAL-GATE PUBLISH BLOCK (B143 — the missing tooth, 2026-06-19).

Turns the moonsighting (B048) / real-person-named (B144) FLAG into a BLOCK
(Rule #8: gates bite, they don't whisper). The interim cultural law stands:
HUMAN EYES ARE THE VISUAL GATE — a card carrying a REQUIRES-HUMAN-VERIFY item may
NOT reach publish until a human recorded all_clear=True (record_tick). This is the
CONSUMER (Rule #6) of that tick.

Why it re-derives FRESH instead of reading the cached visual_gate: the albaik
2027-03-09 Eid card proved a cached blob goes STALE — its slot says
moonsighting_check=true, but its cached gate (attached before B048) has no
moonsighting item. Trusting the blob would let that Eid card publish on the wrong
day — a one-shot trust break. publish_blocked() re-reads the slot every time.

Two populations, reported separately (no silent caps):
  - publish-MARKED cards (slot.status / status in PUBLISH_STATES, or publish_ready):
    any blocked one is a HARD failure → exit 1 under --enforce.
  - planned cards: an AUDIT count of how many WOULD block today (visibility only).

Currently 0 cards are publish-marked, so --enforce is green now and BITES the moment
a moon/person card is marked for publish without a human tick.

Usage:
  python3 scripts/visual_gate_publish_gate.py            # audit, exit 0
  python3 scripts/visual_gate_publish_gate.py --enforce  # exit 1 if a MARKED card is blocked
  python3 scripts/visual_gate_publish_gate.py --json out.json
"""
import argparse, glob, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import visual_gate_checklist as vg

BASE = Path(__file__).parent.parent
PUBLISH_STATES = {"ready_to_publish", "publish", "approved", "scheduled", "live"}


def is_publish_marked(card: dict) -> bool:
    """A card explicitly moved toward publish — the only set --enforce hard-fails on.
    Planned/draft cards are audited, not failed (humans simply haven't reviewed yet)."""
    if card.get("publish_ready") is True:
        return True
    if (card.get("status") or "") in PUBLISH_STATES:
        return True
    if ((card.get("slot") or {}).get("status") or "") in PUBLISH_STATES:
        return True
    return False


def scan(handles=None):
    handles = handles or [p.name for p in (BASE / "clients").iterdir() if (p / "posts").is_dir()]
    marked_blocked, audit_would_block, total = [], [], 0
    for h in handles:
        for f in sorted(glob.glob(str(BASE / "clients" / h / "posts" / "*.json"))):
            card = json.loads(Path(f).read_text())
            total += 1
            blocked, reason = vg.publish_blocked(h, card)
            if not blocked:
                continue
            rec = {"file": f.split("clients/")[-1], "handle": h, "reason": reason}
            (marked_blocked if is_publish_marked(card) else audit_would_block).append(rec)
    return marked_blocked, audit_would_block, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enforce", action="store_true",
                    help="exit 1 if any PUBLISH-MARKED card is blocked")
    ap.add_argument("--handle", help="limit to one handle")
    ap.add_argument("--json", help="write full result to this path")
    a = ap.parse_args()

    handles = [a.handle] if a.handle else None
    marked, audit, total = scan(handles)

    print(f"VISUAL-GATE PUBLISH BLOCK — scanned {total} cards")
    print(f"  publish-marked & BLOCKED: {len(marked)}")
    print(f"  planned cards that WOULD block today (audit): {len(audit)}")
    for r in marked[:10]:
        print(f"   ⛔ {r['file']} — {r['reason']}")
    for r in audit[:5]:
        print(f"   · would-block {r['file']} — {r['reason']}")
    if len(audit) > 5:
        print(f"   · …+{len(audit) - 5} more planned cards would block (need human tick)")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"total": total, "marked_blocked": marked, "audit_would_block": audit},
            ensure_ascii=False, indent=2))

    if a.enforce and marked:
        print(f"\n❌ REFUSED: {len(marked)} publish-marked card(s) have no human visual-gate tick.")
        sys.exit(1)
    print("\n✅ no publish-marked card is blocked" + ("" if not audit else
          f" ({len(audit)} planned cards still await a human tick before they may publish)"))
    sys.exit(0)


if __name__ == "__main__":
    main()
