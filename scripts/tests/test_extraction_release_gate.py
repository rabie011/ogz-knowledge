#!/usr/bin/env python3
"""B130 — tests for the extraction release gate (Rule #8 REFUSE-don't-warn, fail-CLOSED)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import extraction_release_gate as gate  # noqa: E402


class TestExtractionReleaseGate(unittest.TestCase):
    def setUp(self):
        # isolated temp gate file per test (no touching the real data/ artifact)
        self.tmp = Path(__file__).resolve().parent / "_tmp_gate.json"
        if self.tmp.exists():
            self.tmp.unlink()

    def tearDown(self):
        if self.tmp.exists():
            self.tmp.unlink()

    def _write(self, obj):
        self.tmp.write_text(json.dumps(obj), encoding="utf-8")

    def test_missing_artifact_blocks(self):
        # fail-CLOSED: no run on record => blocked
        blocked, reason = gate.release_blocked(self.tmp)
        self.assertTrue(blocked)
        self.assertIn("no calibration accuracy run", reason)

    def test_level1_passed_releases(self):
        self._write({"ts": "2026-06-19T00:00:00Z", "exit_code": 0, "level1_passed": True})
        blocked, reason = gate.release_blocked(self.tmp)
        self.assertFalse(blocked)
        self.assertIn("Level 1 passed", reason)

    def test_level1_failed_blocks(self):
        self._write({"ts": "2026-06-19T00:00:00Z", "exit_code": 1, "level1_passed": False})
        blocked, reason = gate.release_blocked(self.tmp)
        self.assertTrue(blocked)
        self.assertIn("FAILED Level 1", reason)

    def test_level2_fail_still_releases(self):
        # the gate hard-blocks on Level 1 (safety) only — a Level-2/3 quality miss keeps L1 pass
        self._write({"ts": "2026-06-19T00:00:00Z", "exit_code": 2, "level1_passed": True,
                     "completeness": 0.5})
        blocked, _ = gate.release_blocked(self.tmp)
        self.assertFalse(blocked)

    def test_malformed_artifact_blocks(self):
        self.tmp.write_text("{not valid json", encoding="utf-8")
        blocked, reason = gate.release_blocked(self.tmp)
        self.assertTrue(blocked)

    def test_assert_exits_nonzero_when_blocked(self):
        with self.assertRaises(SystemExit) as cm:
            gate.assert_release_allowed(self.tmp)  # missing => blocked => exit
        self.assertNotEqual(cm.exception.code, 0)

    def test_assert_returns_reason_when_allowed(self):
        self._write({"ts": "2026-06-19T00:00:00Z", "exit_code": 0, "level1_passed": True})
        reason = gate.assert_release_allowed(self.tmp)
        self.assertIn("Level 1 passed", reason)


if __name__ == "__main__":
    unittest.main()
