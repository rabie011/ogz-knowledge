#!/usr/bin/env python3
"""Guards make_sure's UNBREAKABILITY (June 20, hard-to-break mandate June 16).

Root scar: a transient session-start load spike pushed the unittest sub-call past its 120s
timeout and make_sure threw an UNCAUGHT subprocess.TimeoutExpired — aborting all 20 OTHER checks.
The self-check organ that must never lie died silently (worse than a red: no signal at all).

The fix: every timeout-bearing child runs through _safe_run, which degrades a TimeoutExpired or
OSError into a RED result (returncode 124) instead of raising. A hung child now records its check
RED -> visible ALARM, never crashes the whole shift. These tests pin that contract."""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms


class TestSafeRun(unittest.TestCase):
    def test_timeout_degrades_to_red_not_raise(self):
        """A child that exceeds its timeout returns rc=124, never raises (the whole point)."""
        r = ms._safe_run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.3)
        self.assertEqual(r.returncode, 124)
        self.assertIn("TIMEOUT/ERROR", r.stderr)

    def test_launch_error_degrades_to_red(self):
        """A binary that does not exist returns rc=124, never raises OSError."""
        r = ms._safe_run(["this_binary_does_not_exist_xyz"], capture_output=True)
        self.assertEqual(r.returncode, 124)

    def test_success_passes_through_unchanged(self):
        """A normal call is untouched — _safe_run is transparent on the happy path."""
        r = ms._safe_run([sys.executable, "-c", "print('ok')"],
                         capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertIn("ok", r.stdout)

    def test_failed_check_reads_as_not_green(self):
        """The degraded result fails the `rc == 0` test every check uses -> ALARM, not green."""
        r = ms._safe_run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.3)
        self.assertFalse(r.returncode == 0)


if __name__ == "__main__":
    unittest.main()
