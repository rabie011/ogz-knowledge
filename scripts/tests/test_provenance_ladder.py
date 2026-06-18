#!/usr/bin/env python3
"""Locks the provenance ladder census (B086, June 19): it must be a faithful
COUNT of fingerprint_status's lights — never a new inference. We assert the
structural invariants (rungs sum to total, % is right, every light is one of the
three known rungs and nothing leaks), NOT the live counts, which move as clients
confirm organs (Rule #9 — never lock a number that legitimately changes)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import provenance_ladder as pl
from fingerprint_status import status, G, Y, R


class TestProvenanceLadder(unittest.TestCase):
    def setUp(self):
        self.c = pl.census()

    def test_shape(self):
        for k in ("per_organ", "per_client", "overall"):
            self.assertIn(k, self.c)
        self.assertTrue(self.c["per_client"], "no clients with a profile — fixture gone")

    def test_rungs_sum_to_total_everywhere(self):
        buckets = [self.c["overall"], *self.c["per_organ"].values(), *self.c["per_client"].values()]
        for d in buckets:
            self.assertEqual(d["confirmed"] + d["inferred"] + d["default"], d["total"])

    def test_pct_confirmed_is_consistent(self):
        for d in [self.c["overall"], *self.c["per_organ"].values(), *self.c["per_client"].values()]:
            expect = round(100 * d["confirmed"] / d["total"], 1) if d["total"] else 0.0
            self.assertEqual(d["pct_confirmed"], expect)

    def test_overall_equals_sum_of_clients(self):
        o = self.c["overall"]
        for rung in pl.RUNGS + ("total",):
            self.assertEqual(o[rung], sum(cl[rung] for cl in self.c["per_client"].values()))

    def test_census_faithfully_mirrors_fingerprint_lights(self):
        """The ground-truth check: rebuild the count straight from status() and
        demand the census match it exactly. No light may be dropped or re-rung."""
        light_rung = {G: "confirmed", Y: "inferred", R: "default"}
        per_client_expected = {}
        for h in pl._clients():
            row = {r: 0 for r in pl.RUNGS}
            for _organ, light, _note in status(h)["rows"]:
                self.assertIn(light, light_rung, f"unmapped light {light!r} — census would miscount")
                row[light_rung[light]] += 1
            per_client_expected[h] = row
        for h, exp in per_client_expected.items():
            for rung in pl.RUNGS:
                self.assertEqual(self.c["per_client"][h][rung], exp[rung],
                                 f"{h}/{rung} census diverged from fingerprint_status")

    def test_production_ready_means_zero_defaults(self):
        """The readiness LAW must stay anchored to 🔴=0, matching fingerprint_status."""
        for h, d in self.c["per_client"].items():
            reds = sum(1 for _o, light, _n in status(h)["rows"] if light == R)
            self.assertEqual(d["default"], reds, f"{h} default count != fingerprint 🔴 count")


if __name__ == "__main__":
    unittest.main()
