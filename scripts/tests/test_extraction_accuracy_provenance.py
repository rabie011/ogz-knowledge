#!/usr/bin/env python3
"""B126 — Level 1 moat-honesty gate: a negative control only proves the moat when the
SYSTEM produced the detection (a real vision run). A hand-authored extraction with the
hard block pre-filled is a Rule #12 false green and MUST fail Level 1 (Rule #8: refuse-
don't-warn). These tests pin that behaviour so the moat proof can never be fabricated."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import test_extraction_accuracy as grader  # noqa: E402


# a ground truth with one negative control expecting left_hand_serving
GT = {
    "items": [
        {
            "id": "item_neg",
            "expected_hard_blocks": [{"entry_name": "left_hand_serving"}],
        }
    ]
}


def _extraction(*, extraction_method, block=True):
    """A minimal extraction: the block IS detected; only provenance varies."""
    return {
        "compliance_check": {
            "hard_blocks_triggered": (
                [{"entry_name": "left_hand_serving"}] if block else []
            )
        },
        "provenance": {"extraction_method": extraction_method},
    }


class TestNegativeControlProvenance(unittest.TestCase):
    def test_vision_sourced_block_passes(self):
        # real vision run + block detected => the honest, passing case (mirrors item_02)
        ext = {"item_neg": _extraction(extraction_method="gpt-4o_vision")}
        self.assertTrue(grader.level_1_hard_block(GT, ext))

    def test_hand_authored_block_fails(self):
        # block IS present but provenance is NOT a vision run => fabricated proof => FAIL
        ext = {"item_neg": _extraction(extraction_method="hand_authored")}
        self.assertFalse(grader.level_1_hard_block(GT, ext))

    def test_missing_provenance_fails(self):
        # no extraction_method at all => cannot prove the system produced it => FAIL
        ext = {"item_neg": {"compliance_check": {
            "hard_blocks_triggered": [{"entry_name": "left_hand_serving"}]}}}
        self.assertFalse(grader.level_1_hard_block(GT, ext))

    def test_vision_sourced_but_block_missing_still_fails(self):
        # honest provenance but the system did NOT detect the block => FAIL (the original
        # Level-1 contract still bites; the provenance gate does not mask a miss)
        ext = {"item_neg": _extraction(extraction_method="gpt-4o_vision", block=False)}
        self.assertFalse(grader.level_1_hard_block(GT, ext))

    def test_clean_items_unaffected(self):
        # an item with no expected blocks is skipped entirely — provenance gate never runs
        gt_clean = {"items": [{"id": "item_clean", "expected_hard_blocks": []}]}
        ext = {"item_clean": {"provenance": {"extraction_method": "hand_authored"}}}
        self.assertTrue(grader.level_1_hard_block(gt_clean, ext))


if __name__ == "__main__":
    unittest.main()
