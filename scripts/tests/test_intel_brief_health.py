"""Tests for the brief-level intel health flag (Rule #6 consumer wire + Rule #8 refuse).

intel_consumer_health.py already DETECTS orphaned reads at the source level (for the
orchestra). The gap this closes: a produced brief must itself DECLARE whether it ran on
degraded primary intel, so the downstream produce/judge stages (Rule #13 judge-before-he-
sees) can see it. These tests cover the pure auditor, the strict guard, and a live
assertion that pins the CURRENT real state (the 7 Thin-Brain-v3.0 keys are genuinely
absent — eyeballed, Rule #9). When B057c is resolved (strip OR rewire), the live
assertion below flips and must be updated — that is the intended tripwire.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_production_brief_engine as bpe  # noqa: E402


FULL = {k: ["x"] for k in bpe.PRIMARY_INTEL_KEYS}


class TestIntelBriefHealth(unittest.TestCase):
    def test_full_intel_not_degraded(self):
        h = bpe.intel_health(FULL)
        self.assertFalse(h["degraded"])
        self.assertEqual(h["missing_keys"], [])
        self.assertEqual(set(h["present_keys"]), set(bpe.PRIMARY_INTEL_KEYS))

    def test_missing_keys_flagged(self):
        drop = bpe.PRIMARY_INTEL_KEYS[:2]          # drop two live v4.2 PRIMARY keys
        partial = {k: v for k, v in FULL.items() if k not in drop}
        h = bpe.intel_health(partial)
        self.assertTrue(h["degraded"])
        self.assertEqual(set(h["missing_keys"]), set(drop))

    def test_empty_values_count_as_missing(self):
        # an empty {} / [] / None is a severed wire dressed as data — must flag
        probe = bpe.PRIMARY_INTEL_KEYS[0]
        for empty in ({}, [], None, ""):
            h = bpe.intel_health({**FULL, probe: empty})
            self.assertIn(probe, h["missing_keys"], f"empty={empty!r}")

    def test_checked_is_exactly_primary_keys(self):
        self.assertEqual(bpe.intel_health(FULL)["checked"], bpe.PRIMARY_INTEL_KEYS)

    def test_strict_guard_raises_on_degraded(self):
        with self.assertRaises(bpe.IntelDegeneracyError):
            bpe.assert_intel_complete({})
        # and returns the health dict when complete
        self.assertFalse(bpe.assert_intel_complete(FULL)["degraded"])

    def test_live_intel_healthy_after_b057c_rewire(self):
        # TRIPWIRE FLIPPED: B057c-A (rewire) landed 2026-06-22. The engine now reads the live
        # v4.2 keys, so intel_health() against the real layer must be NOT degraded — every
        # PRIMARY key resolves non-empty. If this fails, a v4.2 key went empty/absent (a real
        # severed wire) or the rewire regressed onto the dropped keys.
        h = bpe.intel_health(bpe.INTELLIGENCE)
        self.assertFalse(h["degraded"],
                         f"v4.2 PRIMARY intel degraded — empty/absent keys: {h['missing_keys']}")
        self.assertEqual(h["missing_keys"], [])


if __name__ == "__main__":
    unittest.main()
