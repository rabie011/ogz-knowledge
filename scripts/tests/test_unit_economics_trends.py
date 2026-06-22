#!/usr/bin/env python3
"""Guards UNIT-ECONOMICS TREND LINES (B097). All on synthetic fixtures in a tempdir (no live
data, deterministic injected ts). The contracts that matter:
(1) collect_snapshot counts REAL outbound questions + net sector priors, never guessed;
(2) HONESTY — a single point is "baseline"/status BASELINE, never an alarm (Rule #9);
(3) questions-per-client falling reads as 'improving', rising as 'regressing' (Mohamed's law);
(4) net sector priors rising reads as 'improving';
(5) a regression flips status to REGRESSING and names the line;
(6) Rule #6 — an appended snapshot reads back through the series."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import unit_economics_trends as uet


def _client_questions(base: Path, client: str, n: int):
    d = base / "clients" / client / "presentations"
    d.mkdir(parents=True, exist_ok=True)
    (d / "outbound_questions.json").write_text(
        json.dumps([{"q": f"q{i}"} for i in range(n)]), encoding="utf-8")


def _priors(base: Path, n_drafts: int = 0, n_demotions: int = 0):
    dd = base / "data"
    dd.mkdir(parents=True, exist_ok=True)
    (dd / "sector_prior_drafts.json").write_text(json.dumps({"n_drafts": n_drafts}), encoding="utf-8")
    (dd / "prior_demotions.json").write_text(json.dumps({"n_demotions": n_demotions}), encoding="utf-8")


class TestUnitEconomicsTrends(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_collect_snapshot_counts_real(self):
        _client_questions(self.base, "albaik", 4)
        _client_questions(self.base, "eatjurisha", 6)
        _priors(self.base, n_drafts=3, n_demotions=1)
        snap = uet.collect_snapshot(self.base)
        self.assertEqual(snap["questions_per_client"], {"albaik": 4, "eatjurisha": 6})
        self.assertEqual(snap["avg_questions_per_client"], 5.0)
        self.assertEqual(snap["net_sector_priors"], 2)

    def test_single_point_is_baseline_never_alarm(self):
        uet.append_snapshot({"avg_questions_per_client": 4.0, "net_sector_priors": 0}, "t0", self.base)
        h = uet.trend_health(base=self.base)
        self.assertEqual(h["n_points"], 1)
        self.assertEqual(h["status"], "BASELINE")
        self.assertEqual(h["questions_per_client"]["verdict"], "baseline")
        self.assertEqual(h["regressing"], [])

    def test_questions_falling_is_improving(self):
        uet.append_snapshot({"avg_questions_per_client": 6.0, "net_sector_priors": 0}, "t0", self.base)
        uet.append_snapshot({"avg_questions_per_client": 4.0, "net_sector_priors": 0}, "t1", self.base)
        h = uet.trend_health(base=self.base)
        self.assertEqual(h["questions_per_client"]["verdict"], "improving")
        self.assertEqual(h["status"], "HEALTHY")

    def test_questions_rising_is_regressing(self):
        uet.append_snapshot({"avg_questions_per_client": 4.0, "net_sector_priors": 1}, "t0", self.base)
        uet.append_snapshot({"avg_questions_per_client": 7.0, "net_sector_priors": 1}, "t1", self.base)
        h = uet.trend_health(base=self.base)
        self.assertEqual(h["questions_per_client"]["verdict"], "regressing")
        self.assertEqual(h["status"], "REGRESSING")
        self.assertIn("questions_per_client", h["regressing"])

    def test_priors_rising_is_improving(self):
        uet.append_snapshot({"avg_questions_per_client": 4.0, "net_sector_priors": 0}, "t0", self.base)
        uet.append_snapshot({"avg_questions_per_client": 4.0, "net_sector_priors": 3}, "t1", self.base)
        h = uet.trend_health(base=self.base)
        self.assertEqual(h["sector_prior_hit_rate"]["verdict"], "improving")
        self.assertEqual(h["sector_prior_hit_rate"]["last"], 3)

    def test_record_if_changed_is_self_deduping(self):
        _client_questions(self.base, "albaik", 4)
        _priors(self.base, n_drafts=0, n_demotions=0)
        r1 = uet.record_if_changed(self.base, ts="t0")
        self.assertTrue(r1["recorded"])                       # first point lands
        r2 = uet.record_if_changed(self.base, ts="t1")
        self.assertFalse(r2["recorded"])                      # identical → no duplicate
        self.assertEqual(r2["reason"], "unchanged")
        self.assertEqual(len(uet.read_series(self.base)), 1)
        _client_questions(self.base, "albaik", 2)             # state changes
        r3 = uet.record_if_changed(self.base, ts="t2")
        self.assertTrue(r3["recorded"])                       # change → new point
        self.assertEqual(len(uet.read_series(self.base)), 2)

    def test_append_reads_back_rule6(self):
        uet.append_snapshot({"avg_questions_per_client": 5.0, "net_sector_priors": 2}, "t0", self.base)
        series = uet.read_series(self.base)
        self.assertEqual(len(series), 1)
        self.assertEqual(series[0]["ts"], "t0")
        self.assertEqual(series[0]["avg_questions_per_client"], 5.0)


if __name__ == "__main__":
    unittest.main()
