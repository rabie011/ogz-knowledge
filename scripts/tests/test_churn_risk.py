"""B092: churn-risk dashboard + rubber-stamp detector — pure-function tests with injected data.

Covers the escalation rules AND the honesty contract (Rule #9): an INSUFFICIENT signal must
never escalate risk, and absent inputs must never crash (Pre-Build Q2).
"""
import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import churn_risk as cr


def _ans(ts, answer="x", item_id="i"):
    return {"ts": ts.isoformat(), "_t": ts, "answer": answer, "item_id": item_id}


def _session(n, start, gap_sec, answer_fn):
    """n taps starting at `start`, `gap_sec` apart, answer = answer_fn(i)."""
    return [_ans(start + timedelta(seconds=gap_sec * i), answer=answer_fn(i)) for i in range(n)]


NOW = datetime(2026, 6, 22, 12, 0, 0)


class TestHonestyAndAbsence(unittest.TestCase):
    def test_no_answers_is_insufficient_not_crash(self):
        d = cr.compute([], None, NOW)
        self.assertEqual(d["risk"], "INSUFFICIENT")

    def test_load_answers_absent_file(self):
        self.assertEqual(cr.load_answers("/nonexistent/path.jsonl"), [])

    def test_single_session_no_latency_or_completion_trend(self):
        s = _session(5, NOW - timedelta(minutes=2), 20, lambda i: f"a{i}")
        d = cr.compute(s, None, NOW)
        self.assertIsNone(d["signals"]["latency"]["trend"])
        self.assertIsNone(d["signals"]["completion"]["ratio"])

    def test_flat_receipts_absent_is_insufficient(self):
        self.assertIsNone(cr.flat_receipts(None)["flag"])
        self.assertIsNone(cr.flat_receipts({"n_receipts": 0})["flag"])

    def test_insufficient_signals_do_not_escalate(self):
        # one recent, well-spaced, varied session + no receipts → everything insufficient/clean → GREEN
        s = _session(5, NOW - timedelta(minutes=3), 30, lambda i: f"a{i}")
        d = cr.compute(s, None, NOW)
        self.assertEqual(d["risk"], "GREEN")


class TestRubberStamp(unittest.TestCase):
    def test_fast_and_samey_flags(self):
        s = _session(6, NOW - timedelta(minutes=1), 2, lambda i: "same")
        self.assertTrue(cr.rubber_stamp(s, cr.DEFAULTS)["flag"])

    def test_fast_but_varied_does_not_flag(self):
        s = _session(6, NOW - timedelta(minutes=1), 2, lambda i: f"diff{i}")
        self.assertFalse(cr.rubber_stamp(s, cr.DEFAULTS)["flag"])

    def test_samey_but_slow_does_not_flag(self):
        s = _session(6, NOW - timedelta(minutes=30), 60, lambda i: "same")
        self.assertFalse(cr.rubber_stamp(s, cr.DEFAULTS)["flag"])

    def test_too_few_taps_is_insufficient(self):
        s = _session(2, NOW - timedelta(seconds=4), 2, lambda i: "same")
        self.assertIsNone(cr.rubber_stamp(s, cr.DEFAULTS)["flag"])

    def test_rubber_stamp_drives_red(self):
        s = _session(6, NOW - timedelta(minutes=1), 2, lambda i: "same")
        d = cr.compute(s, None, NOW)
        self.assertEqual(d["risk"], "RED")


class TestSilence(unittest.TestCase):
    def test_red_when_long_silent(self):
        s = _session(5, NOW - timedelta(days=10), 30, lambda i: f"a{i}")
        d = cr.compute(s, None, NOW)
        self.assertEqual(d["risk"], "RED")
        self.assertGreater(d["days_silent"], 7)

    def test_yellow_when_mid_silent(self):
        s = _session(5, NOW - timedelta(days=4), 30, lambda i: f"a{i}")
        d = cr.compute(s, None, NOW)
        self.assertEqual(d["risk"], "YELLOW")


class TestTrends(unittest.TestCase):
    def _series(self, sizes, gaps):
        """Build len(sizes) separate sessions (1 day apart, newest last), each `sizes[k]` taps with
        `gaps[k]`-sec spacing and varied answers. The newest ends near NOW."""
        out = []
        k = len(sizes)
        for idx, (n, g) in enumerate(zip(sizes, gaps)):
            start = NOW - timedelta(days=(k - idx))
            out += _session(n, start, g, lambda i, idx=idx: f"s{idx}_{i}")
        return out

    def test_latency_rising_flags_yellow(self):
        # 3 prior sessions @20s, 3 recent @60s → recent pooled median ~60 vs prior ~20 = x3
        d = cr.compute(self._series([4, 4, 4, 4, 4, 4], [20, 20, 20, 60, 60, 60]), None, NOW)
        self.assertEqual(d["risk"], "YELLOW")
        self.assertGreaterEqual(d["signals"]["latency"]["trend"], cr.DEFAULTS["latency_rise_factor"])

    def test_latency_insufficient_pooled_gaps_does_not_escalate(self):
        # one fat gap in the recent window must NOT flag while pooled gaps < latency_min_gaps
        s = self._series([8, 8, 8], [20, 20, 20])  # only 3 comparable → recent window needs r+1=4
        d = cr.compute(s, None, NOW)
        self.assertIsNone(d["signals"]["latency"]["trend"])

    def test_completion_falling_flags_yellow(self):
        # recent mean 3 verdicts vs prior mean 8 → 0.375 <= 0.6 (all sessions comparable)
        d = cr.compute(self._series([8, 8, 8, 3, 3, 3], [20] * 6), None, NOW)
        self.assertEqual(d["risk"], "YELLOW")

    def test_tiny_trailing_session_does_not_escalate(self):
        # the degenerate scar (2026-06-22): a 1-tap trailing session must NOT read as collapse.
        s = self._series([8, 8, 8, 8], [20] * 4)
        s += _session(1, NOW - timedelta(minutes=1), 0, lambda i: "rejected")
        d = cr.compute(s, None, NOW)
        # the 1-tap session is not comparable → trends ignore it → no escalation from it
        self.assertNotEqual(d["risk"], "RED")

    def test_flat_receipts_flags(self):
        s = _session(5, NOW - timedelta(minutes=3), 30, lambda i: f"a{i}")
        d = cr.compute(s, {"n_receipts": 4, "moved": 0}, NOW)
        self.assertTrue(d["signals"]["flat_receipts"]["flag"])
        self.assertEqual(d["risk"], "YELLOW")


if __name__ == "__main__":
    unittest.main()
