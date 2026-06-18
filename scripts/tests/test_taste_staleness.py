#!/usr/bin/env python3
"""Locks the FOUNDER-TASTE STALENESS tripwire (B114, June 17). founder_taste.json IS the bar the
critic judges against; if he keeps rating but the bar is never refreshed the writeback loop is
broken. These tests lock: (1) _max_date_in picks the newest stamped date, (2) stale only when his
latest rating is >14d newer than the bar, (3) honest no-data semantics never manufacture an alarm,
(4) the live repo is currently fresh (numbers, not feelings — Rule #9)."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import crystallize_loop as cl


class TestTasteStaleness(unittest.TestCase):
    def setUp(self):
        self._orig_base = cl.BASE

    def tearDown(self):
        cl.BASE = self._orig_base

    def _scratch(self, meta, pick_dates):
        d = Path(tempfile.mkdtemp())
        (d / "data").mkdir()
        (d / "data/founder_taste.json").write_text(json.dumps({"_meta": meta, "kills": []}))
        lines = [json.dumps({"ts": f"{dt}T12:00:00", "winner_caption": f"w{i}",
                             "loser_caption": f"l{i}"}) for i, dt in enumerate(pick_dates)]
        (d / "data/pairwise_prefs.jsonl").write_text("\n".join(lines))
        cl.BASE = d
        return d

    def test_max_date_in_picks_newest(self):
        self.assertEqual(str(cl._max_date_in(["built 2026-06-01", "2026-06-12 harvest", "x"])),
                         "2026-06-12")
        self.assertIsNone(cl._max_date_in(["no date here", ""]))

    def test_fresh_when_gap_within_threshold(self):
        self._scratch({"built": "2026-06-12"}, ["2026-06-16"])  # 4d
        st = cl.founder_taste_staleness()
        self.assertTrue(st["available"])
        self.assertFalse(st["stale"])
        self.assertEqual(st["gap_days"], 4)

    def test_stale_when_gap_exceeds_threshold(self):
        self._scratch({"built": "2026-06-01"}, ["2026-06-20"])  # 19d > 14
        st = cl.founder_taste_staleness()
        self.assertTrue(st["stale"])
        self.assertEqual(st["gap_days"], 19)

    def test_boundary_exactly_threshold_is_fresh(self):
        self._scratch({"built": "2026-06-01"}, ["2026-06-15"])  # exactly 14d → not stale
        self.assertFalse(cl.founder_taste_staleness()["stale"])

    def test_no_live_ratings_is_not_stale(self):
        self._scratch({"built": "2026-01-01"}, [])  # ancient bar but nothing to be behind
        st = cl.founder_taste_staleness()
        self.assertFalse(st["stale"])
        self.assertIsNone(st["latest_rating_date"])

    def test_seed_picks_do_not_count_as_a_rating_session(self):
        d = Path(tempfile.mkdtemp())
        (d / "data").mkdir()
        (d / "data/founder_taste.json").write_text(json.dumps({"_meta": {"built": "2026-01-01"}}))
        (d / "data/pairwise_prefs.jsonl").write_text(json.dumps(
            {"ts": "2026-06-20T00:00:00", "source": "seed_from_ratings",
             "winner_caption": "w", "loser_caption": "l"}))
        cl.BASE = d
        st = cl.founder_taste_staleness()
        self.assertFalse(st["stale"])  # seeds are historical, never a fresh session

    def test_missing_file_is_honest_no_alarm(self):
        cl.BASE = Path(tempfile.mkdtemp())  # no data/ at all
        st = cl.founder_taste_staleness()
        self.assertFalse(st["available"])
        self.assertFalse(st["stale"])

    def test_live_repo_currently_fresh(self):
        """Eyes-on the real files this shift: the bar is not stale (would fail loudly if it were)."""
        st = cl.founder_taste_staleness()
        self.assertFalse(st["stale"], f"founder_taste went stale: {st}")


if __name__ == "__main__":
    unittest.main()
