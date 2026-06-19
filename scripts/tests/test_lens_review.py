"""Tests for B063 lens-review consumer (Rule #6 wire + Rule #8 refuse-guard)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import lens_review as lr  # noqa: E402


class TestLensReview(unittest.TestCase):
    def test_review_file_loads_and_covers_all_lensed_occasions(self):
        rv = lr.load_review()["reviews"]
        facts = json.loads(lr.FACTS.read_text())
        lensed = {o for o, v in facts.items() if (v.get("sector_lenses") or {})}
        self.assertTrue(lensed, "fixture: no lensed occasions on disk")
        # every lensed occasion must be judged — no silent gaps in the pass
        self.assertEqual(lensed - set(rv), set(),
                         "lensed occasions missing from the RABIE pass")

    def test_flagged_are_real_and_low_rated(self):
        rv = lr.load_review()["reviews"]
        for occ in lr.flagged():
            self.assertIn(occ, rv)
            self.assertLess(rv[occ]["rating"], 3, f"{occ} flagged but rating>=3")

    def test_flag_agrees_with_rating(self):
        # no rubber-stamp: flag iff rating<3, for every occasion
        for occ, r in lr.load_review()["reviews"].items():
            self.assertEqual(bool(r.get("flag")), r["rating"] < 3, occ)

    def test_every_review_has_a_reason(self):
        for occ, r in lr.load_review()["reviews"].items():
            self.assertTrue(r.get("why", "").strip(), f"{occ} has no reason")

    def test_verify_passes_on_live_data(self):
        self.assertEqual(lr.verify(), [], "verify should be clean against live lenses")

    def test_verify_catches_phantom_occasion(self):
        errs = lr._verify_against({"ghost_occasion": {"rating": 2, "flag": True, "why": "x"}}, {})
        self.assertTrue(any("absent" in e for e in errs), errs)

    def test_verify_catches_flag_rating_mismatch(self):
        # rating 4 but flagged True — a rubber-stamp/mismatch must be refused
        facts = {"x": {"sector_lenses": {"f_and_b": {}}}}
        errs = lr._verify_against({"x": {"rating": 4, "flag": True, "why": "x"}}, facts)
        self.assertTrue(any("disagrees" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
