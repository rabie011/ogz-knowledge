#!/usr/bin/env python3
"""
Locks B125f — the GPT-4o FIRST-vote compliance read (the WRITER that B125's
apply_second_vote reader was severed from). Pins:

  - normalize() is CONSERVATIVE: a block forces hard_blocked; unknown/missing label
    with no block is a NON-pass (soft_flagged), never a silent "clean".
  - it accepts both the nested (compliance_check) and flat GPT shapes.
  - the output shape round-trips THROUGH vision_second_vote.reconcile() — proving the
    wire B125f→B125 is real (consumer law, Rule #6): the first vote's output is a valid
    single_result for the second vote.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import compliance_read as cr
import vision_second_vote as v


class TestNormalize(unittest.TestCase):
    def test_clean_passthrough(self):
        out = cr.normalize({"overall_compliance": "clean", "hard_blocks_triggered": []})
        self.assertEqual(out["overall_compliance"], "clean")
        self.assertEqual(out["hard_blocks_triggered"], [])

    def test_block_forces_hard_blocked(self):
        # even if the model mislabels it "clean", a real block wins.
        out = cr.normalize({
            "overall_compliance": "clean",
            "hard_blocks_triggered": [{"entry_name": "left_hand_serving", "severity": "severe"}],
        })
        self.assertEqual(out["overall_compliance"], "hard_blocked")
        self.assertEqual(len(out["hard_blocks_triggered"]), 1)
        self.assertEqual(out["hard_blocks_triggered"][0]["raised_by"], "compliance_read")

    def test_unknown_label_no_block_is_nonpass(self):
        out = cr.normalize({"overall_compliance": "totally_fine"})
        self.assertEqual(out["overall_compliance"], "soft_flagged")

    def test_missing_everything_is_nonpass(self):
        out = cr.normalize({})
        self.assertEqual(out["overall_compliance"], "soft_flagged")
        self.assertEqual(out["hard_blocks_triggered"], [])

    def test_accepts_nested_compliance_check(self):
        out = cr.normalize({"compliance_check": {
            "overall_compliance": "hard_blocked",
            "hard_blocks_triggered": [{"entry_name": "alcohol"}],
        }})
        self.assertEqual(out["overall_compliance"], "hard_blocked")
        self.assertEqual(out["hard_blocks_triggered"][0]["entry_name"], "alcohol")

    def test_garbage_block_entries_dropped(self):
        out = cr.normalize({"overall_compliance": "clean",
                            "hard_blocks_triggered": [{"no_name": 1}, "junk", None]})
        self.assertEqual(out["hard_blocks_triggered"], [])
        self.assertEqual(out["overall_compliance"], "clean")

    def test_non_dict_input(self):
        out = cr.normalize("not a dict")
        self.assertEqual(out["overall_compliance"], "soft_flagged")


class TestWireToSecondVote(unittest.TestCase):
    """The output of the first vote must be a valid single_result for reconcile()."""

    def test_first_vote_feeds_second_vote_clean(self):
        first = cr.normalize({"overall_compliance": "clean", "hard_blocks_triggered": []})
        # second vote unavailable (Anthropic dry) -> reconcile returns first unchanged.
        result, verdict = v.reconcile(first, None)
        self.assertEqual(verdict, "unavailable")
        self.assertEqual(result["overall_compliance"], "clean")

    def test_first_vote_block_is_respected_by_reconcile(self):
        first = cr.normalize({"hard_blocks_triggered": [{"entry_name": "left_hand_serving"}]})
        self.assertTrue(v._single_is_blocked(first))
        result, verdict = v.reconcile(first, {"left_hand_on_food": True})
        # already blocked -> agree on the safe side, never downgrade.
        self.assertEqual(verdict, "agree")
        self.assertEqual(result["overall_compliance"], "hard_blocked")

    def test_second_vote_escalates_clean_first(self):
        first = cr.normalize({"overall_compliance": "clean", "hard_blocks_triggered": []})
        result, verdict = v.reconcile(first, {"left_hand_on_food": True})
        self.assertEqual(verdict, "disagree")
        self.assertEqual(result["overall_compliance"], "hard_blocked")


class TestComplianceReadEdge(unittest.TestCase):
    def test_compliance_read_mocked(self):
        fake = {"compliance_check": {"overall_compliance": "clean", "hard_blocks_triggered": []}}
        with mock.patch.object(cr, "_call_gpt_vision", return_value=fake):
            out = cr.compliance_read("/any/render.png", handle="albaik")
        self.assertEqual(out["overall_compliance"], "clean")
        self.assertEqual(out["raised_by"], "compliance_read")

    def test_compliance_read_raises_on_api_failure(self):
        # Rule #8: a read that cannot read must NOT pass silently.
        with mock.patch.object(cr, "_call_gpt_vision", side_effect=RuntimeError("api down")):
            with self.assertRaises(RuntimeError):
                cr.compliance_read("/any/render.png")


if __name__ == "__main__":
    unittest.main()
