#!/usr/bin/env python3
"""Guards make_sure's surfacing of the TASTE→CREATION wire (B266-268, Rule #6/#9).

The wire's measurement reader (taste_shadow_metric) was built and tested, but the HEARTBEAT the
orchestra reads every fire never surfaced it — the wire's proof filling toward the FLOOR was
invisible, so a one-run/one-tap-away wait read as a stall. make_sure now surfaces it. The one
contract that must never break: a NUMBER is exposed ONLY when status==OK — while INSUFFICIENT,
make_sure shows status + n_runs/floor and NOTHING numeric (Rule #9: no unverified aggregate reaches
Mohamed). Tested through the pure helper so no live heartbeat run is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms
import taste_shadow_metric as tsm


class TestTasteWireSurface(unittest.TestCase):
    def test_insufficient_exposes_no_number(self):
        """Below FLOOR: status + runs only, never a numeric aggregate (Rule #9)."""
        s = ms.taste_wire_surface(tsm.compute([]))  # empty log → INSUFFICIENT
        self.assertEqual(s["_taste_wire_status"], "INSUFFICIENT")
        self.assertEqual(s["_taste_wire_runs"], f"0/{tsm.FLOOR}")
        self.assertNotIn("_taste_wire_gap", s)
        self.assertNotIn("_taste_wire_control_independent", s)

    def test_thin_log_still_insufficient_no_number(self):
        """One real row is still < FLOOR — no number leaks."""
        row = {"n": 4, "order_diff": 2, "wire_live": False,
               "ship_order_idx": [0, 1, 2, 3], "advisory_order_idx": [1, 0, 2, 3],
               "baseline_order_idx": [0, 1, 2, 3]}
        s = ms.taste_wire_surface(tsm.compute([row]))
        self.assertEqual(s["_taste_wire_status"], "INSUFFICIENT")
        self.assertNotIn("_taste_wire_gap", s)

    def test_ok_exposes_the_gap(self):
        """At/above FLOOR distinct runs: the active_vs_random gap IS surfaced."""
        rows = [{"n": 4, "order_diff": d, "wire_live": False,
                 "ship_order_idx": [i], "advisory_order_idx": [i],
                 "baseline_order_idx": [i]}
                for i, d in enumerate(range(tsm.FLOOR + 1))]
        m = tsm.compute(rows)
        self.assertEqual(m["status"], "OK")  # fixture sanity
        s = ms.taste_wire_surface(m)
        self.assertEqual(s["_taste_wire_status"], "OK")
        self.assertIn("_taste_wire_gap", s)
        self.assertIn("_taste_wire_control_independent", s)
        self.assertEqual(s["_taste_wire_gap"], m["active_vs_random_gap"])


if __name__ == "__main__":
    unittest.main()
