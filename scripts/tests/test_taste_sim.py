"""TASTE-SIM tests — the honest active-vs-random measurement (June 18).

Locks: (1) the metric is scored over ALL oracle pairs with neutral-strength for unseen captions
(so it cannot trivially hit 100% on the 1 pair seen — the bug caught at build time); (2) active
selection is at least as fast as random (speedup >= 1.0); (3) determinism (same seed → same
active number); (4) the ordinal rating labels map correctly. The number itself is a SIMULATION on
his rescued ratings, never quoted as his live agreement (Rule #9)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import taste_sim as ts


class TestTasteSim(unittest.TestCase):
    def test_rating_scale_maps_labels_and_numbers(self):
        self.assertEqual(ts._to_score("excellent"), 3.0)
        self.assertEqual(ts._to_score("FAIL"), 0.0)
        self.assertEqual(ts._to_score(2), 2.0)
        self.assertIsNone(ts._to_score(None))
        self.assertIsNone(ts._to_score("nonsense-label"))

    def test_agreement_neutral_for_unseen(self):
        # empty strength → every pair is a coin-flip → exactly 0.5, never trivially 1.0
        oracle = {"x": 3.0, "y": 0.0, "z": 1.0}
        pairs = [("x", "y"), ("x", "z"), ("y", "z")]
        self.assertAlmostEqual(ts._agreement({}, pairs, oracle), 0.5)
        # x=2.0 beats both y=1.0 and unseen z (default 1.0) → 2 correct; (y,z) ties at 1.0 → 0.5
        self.assertAlmostEqual(ts._agreement({"x": 2.0, "y": 1.0}, pairs, oracle), (1.0 + 1.0 + 0.5) / 3)

    def test_simulate_runs_and_is_honest(self):
        # max_taps bounds the O(pairs²) replay so test cost stays flat as the oracle grows
        # (active crosses 0.9 at ~tap 7 on the current 142-pair oracle — ample headroom under 30).
        res = ts.simulate(threshold=0.9, random_trials=10, seed=42, max_taps=30)
        if not res.get("ok"):
            self.skipTest("no rescued-rating oracle present in this checkout")
        # structure
        for k in ("active_taps_to_threshold", "random_taps_to_threshold_mean", "speedup_x", "active_curve"):
            self.assertIn(k, res)
        # the curve must START near coin-flip, not at 1.0 (guards the metric-scoping bug)
        self.assertLess(res["active_curve"][0], 0.75)
        self.assertGreaterEqual(max(res["active_curve"]), 0.9)
        # active is at least as fast as random — the only claim we make
        self.assertGreaterEqual(res["speedup_x"], 1.0)
        # honesty note must flag it as a simulation
        self.assertIn("SIMULATION", res["note"])

    def test_determinism(self):
        a = ts.simulate(threshold=0.9, random_trials=5, seed=7, max_taps=30)
        b = ts.simulate(threshold=0.9, random_trials=5, seed=7, max_taps=30)
        if not a.get("ok"):
            self.skipTest("no oracle")
        self.assertEqual(a["active_taps_to_threshold"], b["active_taps_to_threshold"])
        self.assertEqual(a["random_taps_to_threshold_mean"], b["random_taps_to_threshold_mean"])


if __name__ == "__main__":
    unittest.main()
