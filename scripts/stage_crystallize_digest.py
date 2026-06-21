#!/usr/bin/env python3
"""CRYSTALLIZE BRIDGE (June 13 zoom-out catch #2): the drafts queue told Mohamed
nightly that law drafts await him — with NO surface to ever answer. This stages ONE
digest card (never a flood) when his open queue has room (<6 cards), and his
review_now tap re-pushes the top 3 drafts as individual yes/no cards (handled by
apply_rulings). Runs in the make_sure drive chain — idempotent, queue-disciplined.

Rule #4 step 7 closes mechanically: every pain CAN become a permanent rule again.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, crystallize_cards, pending_crystallize

DIGEST_ID = "crystallize_digest"


def main():
    b = base()
    cq = b / "data/crystallize_queue.json"
    if not cq.exists():
        return print("no crystallize queue")
    d = json.loads(cq.read_text())
    drafts = pending_crystallize(crystallize_cards(d))
    q = json.loads((b / "data/decision_queue.json").read_text())
    open_cards = [i for i in q["items"] if i.get("status") != "answered"]
    if any(i["id"] == DIGEST_ID for i in q["items"]):
        return print("digest already staged (any status) — one per harvest")
    if not drafts:
        return print("no drafts awaiting him")
    if len(open_cards) >= 6:
        return print(f"queue at {len(open_cards)} — digest waits for room (<6)")
    import queue_decision as qd
    qd.push_attributed({
        "id": DIGEST_ID,
        "title": f"{len(drafts)} law drafts crystallized from the week's scars — review?",
        "tag": "Law", "clock": "", "priority": "normal",
        "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
        "kind": "buttons", "judge_lane": False, "lane": "strategy",
        "why": "Every fixed pain this week drafted a permanent-law candidate (Rule #4 step 7). "
               "They sat in a queue with no way to reach your thumb — this card is the bridge.",
        "need": "One tap: review the top 3 now (they arrive as 3 yes/no cards) or park for D6.",
        "did": f"Held all {len(drafts)} drafts with their evidence receipts in "
               "data/crystallize_queue.json; nothing becomes law without your yes.",
        "options": [
            {"v": "review_now", "label": "⚖️ Show me the top 3 (one tap each)", "rec": True},
            {"v": "later", "label": "📅 Park for the D6 sitting"}],
    }, made_by="system:apply_rulings", via="scripts/apply_rulings.py",
       reason=f"crystallize bridge — {len(drafts)} drafts need a tap surface")
    print(f"digest staged: {len(drafts)} drafts behind one card")


if __name__ == "__main__":
    main()
