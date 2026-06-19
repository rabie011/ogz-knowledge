#!/usr/bin/env python3
"""Guards the TASTE→CREATION shadow METRIC reader (B268). Two contracts that matter:
(1) Rule #9 — below FLOOR runs the reader REFUSES to quote an aggregate (status INSUFFICIENT, no
    number reaches Mohamed);
(2) B268 control — shadow_entry keeps order_diff = advisory-vs-BASELINE both before and after the
    gate flips, so the active-vs-random comparison never loses its control when ship becomes the
    taste order. Built against a fixture log (no live data needed)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import taste_rank as tr
import taste_shadow_metric as tsm


def _write_log(rows):
    d = tempfile.mkdtemp()
    p = Path(d) / "taste_shadow_log.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


class TestFloorRefusal(unittest.TestCase):
    """Rule #9: a mean over too-few runs is noise — refuse to quote it."""

    def test_empty_log_is_insufficient(self):
        m = tsm.compute([])
        self.assertEqual(m["status"], "INSUFFICIENT")
        self.assertEqual(m["n_runs"], 0)
        self.assertNotIn("mean_order_diff", m)  # NO number is exposed below the floor

    def test_below_floor_is_insufficient(self):
        rows = [{"n": 3, "order_diff": 1, "wire_live": False} for _ in range(tsm.FLOOR - 1)]
        m = tsm.compute(rows)
        self.assertEqual(m["status"], "INSUFFICIENT")
        self.assertNotIn("displacement_ratio", m)

    def test_missing_log_file_is_insufficient_not_crash(self):
        m = tsm.metric(path=Path(tempfile.mkdtemp()) / "nope.jsonl")
        self.assertEqual(m["status"], "INSUFFICIENT")

    def test_at_floor_quotes_a_number(self):
        rows = [{"n": 3, "order_diff": 1, "wire_live": False} for _ in range(tsm.FLOOR)]
        m = tsm.compute(rows)
        self.assertEqual(m["status"], "OK")
        self.assertIn("mean_order_diff", m)


class TestDivergenceMath(unittest.TestCase):
    def test_random_expected_is_n_minus_one(self):
        # expected fixed points of a uniform permutation = 1, so displaced = n-1
        self.assertEqual(tsm._random_expected_diff(5), 4)
        self.assertEqual(tsm._random_expected_diff(1), 0)
        self.assertEqual(tsm._random_expected_diff(0), 0)

    def test_taste_agrees_gives_zero_ratio(self):
        """Every run: taste agrees with baseline (order_diff 0) → ratio 0, full gap vs random."""
        rows = [{"n": 4, "order_diff": 0, "wire_live": False} for _ in range(tsm.FLOOR)]
        m = tsm.compute(rows)
        self.assertEqual(m["mean_order_diff"], 0.0)
        self.assertEqual(m["displacement_ratio"], 0.0)
        self.assertEqual(m["mean_random_diff"], 3.0)         # n-1 = 3
        self.assertEqual(m["active_vs_random_gap"], 3.0)     # taste diverges far LESS than random

    def test_taste_scatters_like_random_gives_ratio_one(self):
        rows = [{"n": 4, "order_diff": 3, "wire_live": False} for _ in range(tsm.FLOOR)]
        m = tsm.compute(rows)
        self.assertEqual(m["displacement_ratio"], 1.0)       # order_diff == random expectation
        self.assertEqual(m["active_vs_random_gap"], 0.0)

    def test_gate_open_flag_tracks_wire_live(self):
        rows = ([{"n": 4, "order_diff": 1, "wire_live": False} for _ in range(4)]
                + [{"n": 4, "order_diff": 1, "wire_live": True} for _ in range(2)])
        m = tsm.compute(rows)
        self.assertEqual(m["gate_open_runs"], 2)
        self.assertTrue(m["control_independent"])

    def test_all_closed_runs_flagged_preliminary(self):
        rows = [{"n": 4, "order_diff": 1, "wire_live": False} for _ in range(tsm.FLOOR)]
        m = tsm.compute(rows)
        self.assertFalse(m["control_independent"])
        self.assertIn("preliminary", m)                      # honest: no independent control yet

    def test_tolerates_torn_line(self):
        p = _write_log([{"n": 3, "order_diff": 1, "wire_live": False} for _ in range(tsm.FLOOR)])
        with open(p, "a", encoding="utf-8") as f:
            f.write('{"n": 3, "order_diff":')                # a torn final write
        m = tsm.metric(path=p)
        self.assertEqual(m["status"], "OK")                  # the good rows still read; no crash
        self.assertEqual(m["n_runs"], tsm.FLOOR)


class TestBaselineControl(unittest.TestCase):
    """B268's core: order_diff stays advisory-vs-BASELINE after the gate flips, so the active-vs-
    random comparison keeps its control even when ship order BECOMES the taste order."""

    STRONG = {"strengths": {"A loved": 1.4, "B rejected": -1.2},
              "n_comparisons": {"A loved": 4, "B rejected": 4}}

    def test_gate_closed_baseline_equals_ship(self):
        """Closed gate: no baseline passed → defaults to ship; order_diff = taste-vs-system."""
        t = {**self.STRONG, "held_out_live_n_testable": 0, "held_out_live_pct": None,
             "held_out_agreement_degenerate": True}
        ship = ["B rejected", "A loved"]                     # system shipped weak-first
        _, meta = tr.select(ship, t)
        e = tr.shadow_entry(ship, meta)
        self.assertEqual(e["baseline_order_idx"], [0, 1])
        self.assertEqual(e["ship_order_idx"], [0, 1])        # ship == baseline while closed
        self.assertEqual(e["advisory_order_idx"], [1, 0])    # taste wants the strong one first
        self.assertEqual(e["order_diff"], 2)

    def test_gate_open_control_survives_reorder(self):
        """Open gate: ship BECOMES the taste order. If order_diff were advisory-vs-ship it would be a
        degenerate 0. Passing the pre-taste baseline keeps order_diff = advisory-vs-baseline (the
        real displacement) — the control survives."""
        t = {**self.STRONG, "held_out_live_n_testable": 6, "held_out_live_pct": 70,
             "held_out_agreement_degenerate": False}
        baseline = ["B rejected", "A loved"]                 # the system's pre-taste pick (control)
        ship, meta = tr.select(baseline, t)                  # gate open → ship reordered strong-first
        self.assertEqual(ship, ["A loved", "B rejected"])    # taste steered it
        e = tr.shadow_entry(ship, meta, baseline_caps=baseline)
        self.assertTrue(e["wire_live"])
        self.assertEqual(e["order_diff"], 2)                 # NOT 0 — control preserved (B268)
        self.assertEqual(e["advisory_order_idx"], [1, 0])    # taste vs the baseline frame
        self.assertEqual(e["ship_order_idx"], [1, 0])        # ship now equals advisory (gate open)

    def test_baseline_defaults_keep_old_callers_working(self):
        """Backward compat: shadow_entry(ship, meta) with no baseline behaves as before."""
        meta = {"wire_live": False, "advisory_rank": ["x", "y"]}
        e = tr.shadow_entry(["x", "y"], meta)
        self.assertEqual(e["order_diff"], 0)
        self.assertIn("baseline_order_idx", e)


if __name__ == "__main__":
    unittest.main()
