#!/usr/bin/env python3
"""B130 — tests for the extraction release gate (Rule #8 REFUSE-don't-warn, fail-CLOSED)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import extraction_release_gate as gate  # noqa: E402
import test_extraction_accuracy as acc  # noqa: E402  (the grader module; imported for its pure loaders/graders, not run as a test)


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


class TestNegativeControlArtifact(unittest.TestCase):
    """B126 — guard the moat's ONE left-hand-serving negative control (item_02) with a STANDING,
    deterministic test. No LLM: it grades the COMMITTED extraction artifact against GROUND_TRUTH via
    the existing accuracy grader. On Jun-11 GPT-4o misread the hand as right and item_02 regressed to
    'clean' — nothing in the suite caught it because the requirement lived only in docs (severed wire,
    Rule #6). This class is the reader those docs never had: if item_02_extraction.json ever stops
    triggering left_hand_serving, `python3 -m unittest discover -s scripts/tests` goes RED."""

    NEG_CONTROL_ID = "item_02"
    NEG_CONTROL_BLOCK = "left_hand_serving"

    def setUp(self):
        self.gt = acc.load_ground_truth()
        self.extractions = acc.load_extractions()
        if not self.gt or self.NEG_CONTROL_ID not in self.extractions:
            self.skipTest("calibration set not present on this box")

    def test_ground_truth_still_declares_the_negative_control(self):
        # the control itself must not be silently softened out of GROUND_TRUTH.yaml
        item = next((i for i in self.gt.get("items", []) if i.get("id") == self.NEG_CONTROL_ID), None)
        self.assertIsNotNone(item, f"{self.NEG_CONTROL_ID} missing from GROUND_TRUTH")
        expected = {b.get("entry_name") for b in (item.get("expected_hard_blocks") or [])}
        self.assertIn(self.NEG_CONTROL_BLOCK, expected,
                      "GROUND_TRUTH no longer expects the left_hand_serving hard block on item_02")

    def test_committed_extraction_triggers_left_hand_serving(self):
        # the real moat check: the stored extraction must still fire the hard block
        extraction = self.extractions[self.NEG_CONTROL_ID]
        triggered = {b.get("entry_name")
                     for b in extraction.get("compliance_check", {}).get("hard_blocks_triggered", [])}
        self.assertIn(self.NEG_CONTROL_BLOCK, triggered,
                      "item_02 regressed: committed extraction no longer detects left_hand_serving "
                      "(the exact Jun-11 GPT-4o failure this guard exists to catch)")

    def test_level1_grader_passes_on_committed_artifacts(self):
        # end-to-end through the same grader the release gate relies on
        self.assertTrue(acc.level_1_hard_block(self.gt, self.extractions),
                        "Level-1 hard-block detection failed on committed calibration artifacts")


if __name__ == "__main__":
    unittest.main()
