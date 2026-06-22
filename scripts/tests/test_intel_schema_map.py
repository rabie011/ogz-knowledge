"""B057c — guard the Thin-Brain rewire map (Rule #6 + #9).

build_production_brief_engine.py reads 7 PRIMARY_INTEL_KEYS that Thin-Brain v4.2 dropped
(intel_health() already flags every degraded brief honestly — Rule #6/#8). data/
intel_schema_map_b057c.json is RABIE's provisional ruling on the rewire-vs-strip fork:
it names, for each dropped key, the NEW v4.2 key(s) the live reader must rewire onto.

A rewire target that does not actually exist in the live intelligence_layer.json would be
a NEW severed wire dressed as a fix. These tests make that impossible to ship silently:
every mapped new-key (and every supplement key) is asserted present in the live file
(Rule #9 — verified, not assumed), and the map is asserted complete + shape-honest. When
B057b actually rewires the code, these stay green only if the targets remain real.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_production_brief_engine as bpe  # noqa: E402

BASE = Path(__file__).resolve().parent.parent.parent
MAP_PATH = BASE / "data" / "intel_schema_map_b057c.json"
INTEL_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"


class TestIntelSchemaMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(MAP_PATH.read_text())
        cls.map = cls.doc["map"]
        cls.live = json.loads(INTEL_PATH.read_text())

    # the 7 pre-v4.2 keys the map documents the migration FROM (B057c source set)
    DROPPED_PRE_V42 = {
        "sector_playbooks", "universal_rules", "anti_patterns", "occasion_rules",
        "visual_rules", "caption_rules", "format_rules",
    }

    def test_map_covers_every_dropped_key(self):
        # the rewire map must rule on every dropped key the engine used to read — no key
        # left undecided. (Post-B057c-A the map keys are the migration SOURCE set, not the
        # engine's current PRIMARY_INTEL_KEYS, which are the rewired v4.2 TARGETS.)
        self.assertEqual(set(self.map.keys()), self.DROPPED_PRE_V42)

    def test_rewire_complete_primary_keys_disjoint_from_dropped(self):
        # B057c-A landed: the engine's live PRIMARY keys must contain NONE of the dropped
        # keys — if one reappears, the rewire regressed back onto a severed wire.
        relapsed = self.DROPPED_PRE_V42.intersection(bpe.PRIMARY_INTEL_KEYS)
        self.assertEqual(relapsed, set(), f"PRIMARY_INTEL_KEYS relapsed to dropped keys: {relapsed}")

    def test_every_mapped_new_key_exists_in_live_file(self):
        # Rule #9: a rewire target is not real until eyeballed against the live file.
        # A non-existent target would just re-create the severance under a new name.
        for old_key, entry in self.map.items():
            targets = list(entry.get("new_keys", [])) + list(entry.get("supplement_keys", []))
            self.assertTrue(targets, f"{old_key}: no rewire target named")
            for nk in targets:
                self.assertIn(
                    nk, self.live,
                    f"{old_key} -> '{nk}' is not present in the live intelligence_layer.json "
                    f"(would be a new severed wire, Rule #6)",
                )
                self.assertTrue(
                    self.live[nk],
                    f"{old_key} -> '{nk}' is present but EMPTY in the live file "
                    f"(severed wire dressed as data, Rule #6)",
                )

    def test_every_entry_declares_equivalence_and_shape_gap(self):
        # the shape gap is the whole point — a 1:1 variable swap would mis-feed live briefs.
        valid = {"full", "partial", "none"}
        for old_key, entry in self.map.items():
            self.assertIn(entry.get("equivalence"), valid, f"{old_key}: bad equivalence")
            self.assertTrue(entry.get("shape_gap"), f"{old_key}: shape_gap must be documented")

    def test_manual_reader_named_and_standalone_readers_parked(self):
        # CALL-PATH CORRECTED 2026-06-20 (Rule #9): no reader is auto-live. The brief engine
        # is MANUAL-ONLY (enricher excludes it; produce_batch doesn't use it) — rewire-or-strip;
        # the 3 standalone readers park for DELETE APPROVED (strip is a deletion — never autonomous).
        self.assertIn("build_production_brief_engine.py", self.doc["manual_only_reader_to_rewire_or_strip"])
        self.assertEqual(
            set(self.doc["standalone_readers_park_for_delete_approved"]),
            {"calibrate_cd_router.py", "creative_pipeline.py", "overnight_improver.py"},
        )


if __name__ == "__main__":
    unittest.main()
