#!/usr/bin/env python3
"""
Locks B125 — the Claude-vision SECOND VOTE fail-safe (Rule #8 REFUSE-don't-warn,
Rule #20 consult-before-build).

The trap DeepSeek caught and this test pins shut: a second-vote that hard-blocks
when the vote is UNAVAILABLE (no credits / API error) is a SPOF that DoS-es the whole
brain on any hiccup. The fail-safe behaviour is: UNAVAILABLE -> fall back to the
single-model result UNCHANGED (the single model is already conservative). The second
vote may only ESCALATE a "clean" to "hard_blocked" on an explicit successful
disagreement; it must never downgrade a block, and never block on its own failure.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import vision_second_vote as v


class TestReconcile(unittest.TestCase):
    def _clean(self):
        return {"overall_compliance": "clean", "hard_blocks_triggered": []}

    def _blocked(self):
        return {
            "overall_compliance": "hard_blocked",
            "hard_blocks_triggered": [{"entry_name": "left_hand_serving", "severity": "severe"}],
        }

    # ── the SPOF guard: unavailable must NEVER block ──────────────────────────
    def test_unavailable_does_not_block_clean(self):
        out, verdict = v.reconcile(self._clean(), None)
        self.assertEqual(verdict, "unavailable")
        self.assertEqual(out["overall_compliance"], "clean")
        self.assertEqual(out["hard_blocks_triggered"], [])

    def test_unavailable_preserves_existing_block(self):
        out, verdict = v.reconcile(self._blocked(), None)
        self.assertEqual(verdict, "unavailable")
        self.assertEqual(out["overall_compliance"], "hard_blocked")

    # ── escalation: second vote catches what the single model missed ─────────
    def test_disagree_escalates_clean_to_block(self):
        second = {"hand_on_food": True, "which_hand": "left", "overall_compliance": "hard_blocked"}
        out, verdict = v.reconcile(self._clean(), second)
        self.assertEqual(verdict, "disagree")
        self.assertEqual(out["overall_compliance"], "hard_blocked")
        names = [b.get("entry_name") for b in out["hard_blocks_triggered"]]
        self.assertIn("left_hand_serving", names)

    def test_uncertain_hand_on_food_escalates(self):
        second = {"hand_on_food": True, "which_hand": "uncertain", "overall_compliance": "clean"}
        out, verdict = v.reconcile(self._clean(), second)
        self.assertEqual(verdict, "disagree")
        self.assertEqual(out["overall_compliance"], "hard_blocked")

    # ── agreement: no spurious escalation, no downgrade ──────────────────────
    def test_agree_clean_stays_clean(self):
        second = {"hand_on_food": True, "which_hand": "right", "overall_compliance": "clean"}
        out, verdict = v.reconcile(self._clean(), second)
        self.assertEqual(verdict, "agree")
        self.assertEqual(out["overall_compliance"], "clean")

    def test_second_vote_never_downgrades_a_block(self):
        # single blocked, second says clean -> stay blocked (conservative), verdict agree
        second = {"hand_on_food": False, "which_hand": "none", "overall_compliance": "clean"}
        out, verdict = v.reconcile(self._blocked(), second)
        self.assertEqual(out["overall_compliance"], "hard_blocked")
        self.assertEqual(verdict, "agree")

    def test_reconcile_does_not_mutate_caller(self):
        single = self._clean()
        second = {"hand_on_food": True, "which_hand": "left"}
        v.reconcile(single, second)
        self.assertEqual(single["overall_compliance"], "clean")  # caller dict untouched

    # ── the impure edge degrades to "unavailable", never raises ──────────────
    def test_second_vote_read_returns_none_on_failure(self):
        # bogus path -> _call_anthropic_vision raises -> mapped to None (unavailable)
        self.assertIsNone(v.second_vote_read(Path("/nonexistent/does_not_exist.jpg")))

    def test_apply_second_vote_failsafe_endtoend(self):
        # no live credits -> unavailable -> single result returned unchanged, no block
        out, verdict = v.apply_second_vote(self._clean(), Path("/nonexistent/x.jpg"))
        self.assertEqual(verdict, "unavailable")
        self.assertEqual(out["overall_compliance"], "clean")


if __name__ == "__main__":
    unittest.main()
