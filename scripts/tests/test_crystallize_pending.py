#!/usr/bin/env python3
"""Locks the ONE crystallize 'needs Mohamed's tap' predicate (B229, Rule #6 consumer law +
the one-module law). The digest renderer and apply_rulings' re-push must read the IDENTICAL
pending set, or a card drafted under a status no reader greps sits stranded — exactly what
happened to six `awaiting_mohamed` LAW cards (drafted 2026-06-12, surfaced 2026-06-21). These
tests lock: (1) DRAFT and awaiting_mohamed both count as pending; (2) accepted/ratified/
dropped/superseded are terminal (never re-shown); (3) ordering is file-order stable so
law_draft_<idx> resolves the card it pushed; (4) dedupe marks the weaker recurring-pattern
duplicate superseded and removes it from the pending set."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import feedback_lib as fl


def _q():
    """A fixture queue mirroring the real shape: DRAFT + awaiting_mohamed (pending),
    ACCEPTED + RATIFIED (terminal), and a recurring-pattern dupe pair (3x vs 4x)."""
    return {
        "cards": [
            {"draft": "founder_taste: recurring 'factual_error' (3x across batches)",
             "status": "DRAFT — Mohamed's yes/no only"},
            {"draft": "founder_taste: recurring 'factual_error' (4x across batches)",
             "status": "DRAFT — Mohamed's yes/no only"},
            {"draft": "operational law candidate: a law lives in ONE module",
             "status": "DRAFT — Mohamed's yes/no only"},
            {"draft": "LAW: assert at the SYSTEM layer", "status": "awaiting_mohamed"},
            {"draft": "LAW: the judge sees the FULL POST", "status": "awaiting_mohamed"},
            {"draft": "operational law candidate: cta_saturation",
             "status": "RATIFIED by Mohamed 2026-06-13 → law"},
            {"draft": "founder_taste: recurring 'too_generic' (4x)",
             "status": "ACCEPTED BY MOHAMED 2026-06-12"},
        ],
        "items": [{"unrelated": True}],
    }


class TestCrystallizePending(unittest.TestCase):
    def test_cards_never_falls_through_to_items(self):
        # the queue carries BOTH `cards` and an unrelated `items` key — the helper takes cards
        self.assertEqual(len(fl.crystallize_cards(_q())), 7)
        self.assertEqual(fl.crystallize_cards({"items": [{"x": 1}]}), [])

    def test_awaiting_mohamed_counts_as_pending(self):
        pend = fl.pending_crystallize(fl.crystallize_cards(_q()))
        statuses = [c["status"] for c in pend]
        # the six-cards-stranded bug: awaiting_mohamed MUST be surfaced
        self.assertTrue(any("awaiting_mohamed" == s for s in statuses))
        self.assertTrue(any("DRAFT" in s for s in statuses))

    def test_terminal_verdicts_excluded(self):
        pend = fl.pending_crystallize(fl.crystallize_cards(_q()))
        for c in pend:
            st = c["status"].lower()
            self.assertNotIn("ratified", st)
            self.assertNotIn("accepted", st)
        # 3 DRAFT + 2 awaiting = 5 pending out of 7
        self.assertEqual(len(pend), 5)

    def test_pending_order_is_file_order_stable(self):
        # law_draft_<idx> resolves drafts[idx]; the push and the resolver must agree on order
        cards = fl.crystallize_cards(_q())
        pend = fl.pending_crystallize(cards)
        self.assertEqual([cards.index(c) for c in pend], [0, 1, 2, 3, 4])

    def test_dedupe_supersedes_weaker_recurring_dupe(self):
        cards = fl.crystallize_cards(_q())
        n = fl.dedupe_crystallize(cards)
        self.assertEqual(n, 1)  # the 3x factual_error superseded by the 4x
        # the weaker one is now terminal and drops out of pending
        weaker = cards[0]
        self.assertIn("superseded", weaker["status"].lower())
        self.assertNotIn(weaker, fl.pending_crystallize(cards))
        # the stronger one survives
        self.assertIn(cards[1], fl.pending_crystallize(cards))
        self.assertEqual(len(fl.pending_crystallize(cards)), 4)

    def test_dedupe_idempotent(self):
        cards = fl.crystallize_cards(_q())
        fl.dedupe_crystallize(cards)
        self.assertEqual(fl.dedupe_crystallize(cards), 0)  # nothing new to supersede


if __name__ == "__main__":
    unittest.main()
