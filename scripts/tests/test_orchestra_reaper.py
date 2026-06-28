"""Tests for the SCHEDULED reaper (orchestra_reaper.py) + its deploy config.

The scheduled reaper is the autonomous guard against the claude-code session
leak. Two things must hold:
  1. its etime parser is correct (a wrong parse = wrong age = wrong reap), and
  2. the deploy plist reaps age-leaked sessions PREVENTIVELY, not gated behind a
     high load (the June 28 fix: a 29.8h detached session survived at load 4.5
     because the plist passed `--max-load 6`; the age+TTY+ancestor triple is the
     real safety invariant, so the load gate only made the reaper reactive).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import orchestra_reaper as r  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEPLOY_PLIST = os.path.join(REPO, "deploy", "launchagents", "com.abraham.reaper.plist")


class TestEtimeHours(unittest.TestCase):
    def test_seconds_only(self):
        self.assertAlmostEqual(r._etime_hours("30"), 30 / 3600)

    def test_mm_ss(self):
        self.assertAlmostEqual(r._etime_hours("04:50"), (4 * 60 + 50) / 3600)

    def test_hh_mm_ss(self):
        self.assertAlmostEqual(r._etime_hours("12:39:40"), 12 + 39 / 60 + 40 / 3600)

    def test_days(self):
        # 1-16:00:00 = 40h
        self.assertAlmostEqual(r._etime_hours("01-16:00:00"), 40.0)

    def test_29h_leak_above_floor(self):
        # the live June 28 leak: 29.8h detached session is well above MIN_AGE_H
        self.assertGreater(r._etime_hours("01-05:48:00"), r.MIN_AGE_H)


class TestDeployPlistPreventive(unittest.TestCase):
    """Locks the June 28 fix: scheduled reaper must reap on age, not gate on load."""

    def setUp(self):
        if not os.path.exists(DEPLOY_PLIST):
            self.skipTest("deploy plist not tracked")
        with open(DEPLOY_PLIST) as f:
            self.plist = f.read()

    def test_actually_reaps(self):
        # a dry-run-only scheduler would never kill anything
        self.assertIn("--reap", self.plist)

    def test_no_load_gate(self):
        # the load gate made the reaper reactive (clean up only after load is bad)
        self.assertNotIn("--max-load", self.plist)

    def test_runs_the_scheduled_reaper(self):
        self.assertIn("orchestra_reaper.py", self.plist)


if __name__ == "__main__":
    unittest.main()
