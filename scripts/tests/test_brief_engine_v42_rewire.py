#!/usr/bin/env python3
"""test_brief_engine_v42_rewire.py — B057c-A rewire regression guard.

Mohamed ruled REWIRE (fork B057c, answered "A" 2026-06-21): build_production_brief_engine.py
must read the LIVE Thin-Brain v4.2 keys, not the 7 dropped pre-v4.2 keys it silently read as
empty. These tests pin that rewire so it cannot regress:

  1. The engine declares ZERO orphaned intel reads (the live keys it reads all exist in v4.2).
  2. intel_health() is NOT degraded against the live intelligence_layer.json — the strict
     Rule #8 guard passes, i.e. every PRIMARY key resolves non-empty.
  3. generate_brief() emits a NON-EMPTY intelligence_layer block — the exact severed wire the
     fork closed (must/never patterns, winning formulas, universal red-lines, occasion verdict).
  4. PRIMARY_INTEL_KEYS contains none of the 7 dropped keys (no silent relapse to dead reads).

Zero-LLM: generate_brief() builds from files only; sample-caption generation (the one Claude
call) is downstream of the block under test and not exercised here.
"""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import build_production_brief_engine as B  # noqa: E402
import intel_consumer_health as H  # noqa: E402

DROPPED_PRE_V42_KEYS = {
    "sector_playbooks", "universal_rules", "anti_patterns", "occasion_rules",
    "visual_rules", "caption_rules", "format_rules",
}
ENGINE_FILE = "build_production_brief_engine.py"


class TestBriefEngineV42Rewire(unittest.TestCase):
    def test_engine_has_zero_orphaned_reads(self):
        orphans = [r for r in H.orphaned_intel_reads() if r["file"] == ENGINE_FILE]
        self.assertEqual(
            orphans, [],
            f"{ENGINE_FILE} still reads dropped intel keys: "
            f"{sorted(r['key'] for r in orphans)} — rewire regressed (B057c-A)",
        )

    def test_primary_keys_are_v42_not_dropped(self):
        relapsed = DROPPED_PRE_V42_KEYS.intersection(B.PRIMARY_INTEL_KEYS)
        self.assertEqual(relapsed, set(),
                         f"PRIMARY_INTEL_KEYS relapsed to dropped keys: {relapsed}")
        # every declared primary key must actually exist in the live layer
        live = set(B.INTELLIGENCE.keys())
        missing = [k for k in B.PRIMARY_INTEL_KEYS if k not in live]
        self.assertEqual(missing, [], f"PRIMARY_INTEL_KEYS not in live v4.2 layer: {missing}")

    def test_intel_health_not_degraded_on_live_layer(self):
        h = B.intel_health()
        self.assertFalse(h["degraded"],
                         f"v4.2 PRIMARY intel degraded — empty keys: {h['missing_keys']}")
        # strict Rule #8 guard must not raise
        B.assert_intel_complete()

    def test_brief_intelligence_layer_is_non_empty(self):
        brief = B.generate_brief("food_and_beverage", "national_day", "brand_building")
        il = brief["intelligence_layer"]
        self.assertTrue(il["must_use_patterns"], "must_use_patterns empty — severed wire")
        self.assertTrue(il["never_use_patterns"], "never_use_patterns empty — severed wire")
        self.assertTrue(il["winning_formulas"], "winning_formulas empty — severed wire")
        self.assertTrue(il["universal_rules"], "universal_rules empty — severed wire")
        # winning_formulas carry the proven-pattern shape
        self.assertIn("formula", il["winning_formulas"][0])
        # known major occasion resolves to a real approach + 'use' verdict
        self.assertEqual(il["occasion_verdict"], "use")
        self.assertTrue(il["occasion_approach"], "occasion_approach empty for national_day")
        # total_corpus comes from sector_facts obs_count (real number, not the 648 default)
        self.assertGreater(brief["data_sources"]["total_corpus"], 0)


if __name__ == "__main__":
    unittest.main()
