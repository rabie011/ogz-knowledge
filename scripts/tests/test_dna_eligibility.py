#!/usr/bin/env python3
"""B050 — DNA-eligibility gate for the feed-cloner (v6) path.

The feed-cloner clones a brand's real feed voice. If the brand's DNA is thin or missing
there is no voice to clone, so v6 must fall back to the angle-brain path instead of
producing a hollow clone (Rule #8: the gate bites, never warns-and-continues).

Rule #9 scar baked in here: the original spec said ">=20 real captions", but the
extractor caps exemplars at 10 (every audited brand has 7-10). This test pins the
mechanism to a tunable floor so the impossible literal can never silently re-enter and
kill the v6 path for every brand. This test IS the reader/guard on that gate (Rule #6).

Run: python3 -m unittest discover -s scripts/tests -q
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from v5_prompt import dna_eligibility, load_dna, MIN_DNA_EXEMPLARS


def _a_real_brand_with_dna() -> str:
    """albaik is a pilot brand and ships DNA; fall back to any DNA file if it moves."""
    if load_dna("albaik"):
        return "albaik"
    for f in (Path(__file__).parent.parent.parent / "logs" / "brand_dna").glob("*_dna_v*.json"):
        name = f.name.rsplit("_dna_v", 1)[0]
        if load_dna(name):
            return name
    raise unittest.SkipTest("no brand DNA files on disk")


class TestDNAEligibility(unittest.TestCase):
    def setUp(self):
        self.brand = _a_real_brand_with_dna()

    def test_default_floor_is_reachable(self):
        # the data caps exemplars at 10; a real floor must sit at or below that, never 20
        self.assertLessEqual(MIN_DNA_EXEMPLARS, 10, "floor above the extractor cap kills v6")
        self.assertGreaterEqual(MIN_DNA_EXEMPLARS, 1)

    def test_real_brand_is_eligible(self):
        r = dna_eligibility(self.brand)
        self.assertTrue(r["eligible"], r)
        self.assertEqual(r["reason"], "ok")
        self.assertGreaterEqual(r["exemplars"], MIN_DNA_EXEMPLARS)

    def test_missing_dna_is_ineligible_with_reason(self):
        r = dna_eligibility("___definitely_no_such_brand___")
        self.assertFalse(r["eligible"])
        self.assertEqual(r["exemplars"], 0)
        self.assertTrue(r["reason"].startswith("no_dna_file:"), r["reason"])

    def test_thin_dna_is_ineligible(self):
        # raise the floor above the real count -> the same brand becomes ineligible,
        # proving the gate is count-driven (this is the impossible-20 case, generalized)
        n = dna_eligibility(self.brand)["exemplars"]
        r = dna_eligibility(self.brand, min_exemplars=n + 1)
        self.assertFalse(r["eligible"], r)
        self.assertTrue(r["reason"].startswith("thin_dna:"), r["reason"])


if __name__ == "__main__":
    unittest.main()
