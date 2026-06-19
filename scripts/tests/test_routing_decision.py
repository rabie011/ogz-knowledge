#!/usr/bin/env python3
"""Locks B051 (June 19 2026): every routing call is observable, and the log has a READER that
catches the June-14 '100% paradox' scar (Rule #6 — no write-only organ). These tests assert:
1. route_decision carries the full audit record and never disagrees with route_brain;
2. the log round-trips (write → read);
3. routing_spread flags single-brain domination and clears a healthy spread.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import brain_router as br


class TestRoutingDecision(unittest.TestCase):
    def test_decision_primary_equals_route_brain(self):
        """The audit record must never diverge from the live answer — same input, same brain."""
        slots = [
            {"occasion": "saudi_national_day"},
            {"occasion": "saudi_founding_day"},
            {"occasion": "ramadan"},
            {"occasion": "eid_al_fitr"},
            {"type": "competitor_reference"},
            {"date": "2026-09-23"},
            {"date": "2027-02-22"},
            {},
        ]
        for slot in slots:
            for alt in (0, 1, 2):
                self.assertEqual(br.route_decision(slot, alt)["primary"],
                                 br.route_brain(slot, alt),
                                 f"drift on {slot} alt={alt}")

    def test_decision_shape_and_triggers(self):
        d = br.route_decision({"occasion": "saudi_national_day"})
        # B053: now sourced from the YAML (heritage+metaphor), not the drifted hardcode
        self.assertEqual(d["trigger_reason"], "yaml_occasion_override")
        self.assertEqual(d["primary"], "heritage")
        self.assertIn("heritage_falls_back_to_firaasa_when_no_root", d["safety_locks"])
        e = br.route_decision({"occasion": "ramadan"}, 0)
        # YAML truth: ramadan = authenticity + heritage (old code wrongly said firaasa+authenticity)
        self.assertEqual((e["primary"], e["secondary"]), ("authenticity", "heritage"))
        self.assertEqual(e["two_cd_diagnostic"], ["authenticity", "heritage"])
        self.assertEqual(e["trigger_reason"], "yaml_occasion_override")
        day = br.route_decision({"date": "2026-09-23"})
        self.assertEqual(day["trigger_reason"], "daily_rotation")
        self.assertIsNotNone(day["daily_seed"])
        # deterministic router computes no soft scores — honest empty, not invented (Rule #9)
        self.assertEqual(day["scores"], {})

    def test_log_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "routing_decision.jsonl"
            br.log_routing_decision(br.route_decision({"date": "2026-09-23"}), run_id="t:1", path=p)
            br.log_routing_decision(br.route_decision({"occasion": "ramadan"}, 1), run_id="t:2", path=p)
            recs = br.read_routing_decisions(p)
            self.assertEqual(len(recs), 2)
            self.assertEqual(recs[0]["run_id"], "t:1")
            self.assertIn("ts", recs[0])
            self.assertIn("primary", recs[1])

    def test_spread_flags_single_brain_domination(self):
        """The June-14 scar: a whole batch on one brain. The reader must catch it."""
        all_paradox = [{"primary": "paradox"} for _ in range(6)]
        flagged = br.routing_spread(all_paradox)
        self.assertTrue(flagged["single_brain_domination"])
        self.assertEqual(flagged["dominant_brain"], "paradox")
        self.assertEqual(flagged["dominance_ratio"], 1.0)

    def test_spread_passes_healthy_mix(self):
        mixed = [{"primary": b} for b in ("metaphor", "paradox", "firaasa", "authenticity")]
        ok = br.routing_spread(mixed)
        self.assertFalse(ok["single_brain_domination"])
        self.assertEqual(len(ok["brains_used"]), 4)

    def test_spread_empty_is_safe(self):
        s = br.routing_spread([])
        self.assertEqual(s["total"], 0)
        self.assertFalse(s["single_brain_domination"])

    # ---- B053: router consumes the provenance-backed YAML, not a drifted hardcode ----

    def test_yaml_occasion_overrides_match_source_of_truth(self):
        """Each occasion routes to the brain the YAML documents — caught the drift on 3 occasions."""
        cases = {
            "ramadan": "authenticity",          # was wrongly firaasa
            "eid_al_fitr": "firaasa",
            "eid_al_adha": "heritage",          # was wrongly firaasa
            "saudi_national_day": "heritage",
            "saudi_founding_day": "heritage",
        }
        for occ, lead in cases.items():
            d = br.route_decision({"occasion": occ}, 0)
            self.assertEqual(d["primary"], lead, f"{occ} should lead with {lead}")
            self.assertEqual(d["trigger_reason"], "yaml_occasion_override")

    def test_national_day_keeps_metaphor_secondary(self):
        """National Day wants heritage AND metaphor — the old hardcode dropped metaphor entirely."""
        d = br.route_decision({"occasion": "saudi_national_day"}, 0)
        self.assertEqual(d["secondary"], "metaphor")
        d2 = br.route_decision({"occasion": "saudi_national_day"}, 1)  # alt flips the lead
        self.assertEqual(d2["primary"], "metaphor")

    def test_uncovered_emotional_occasion_keeps_validated_pair(self):
        """Occasions the YAML doesn't specify (mothers' day, hajj) must NOT regress to daily."""
        for occ in ("arab_mothers_day", "hajj_season"):
            d = br.route_decision({"occasion": occ}, 0)
            self.assertEqual(d["trigger_reason"], "emotional_pair")
            self.assertEqual((d["primary"], d["secondary"]), ("firaasa", "authenticity"))

    def test_sector_safety_lock_blocks_forbidden_brain(self):
        """healthcare_wellness forbids paradox — a daily slot that would route there must be swapped
        (the real myfitness.sa gap). The router previously had no sector lock at all."""
        # find a date whose daily rotation lands on paradox, then assert the sector lock saves it
        paradox_slot = next(({"date": f"2026-01-{d:02d}"} for d in range(1, 28)
                             if br.route_decision({"date": f"2026-01-{d:02d}"})["primary"] == "paradox"), None)
        self.assertIsNotNone(paradox_slot, "expected some date to route to paradox")
        locked = br.route_decision({**paradox_slot, "sector": "healthcare_wellness"})
        self.assertNotEqual(locked["primary"], "paradox")
        self.assertTrue(any(s.startswith("sector_forbids:healthcare_wellness")
                            for s in locked["safety_locks"]))
        self.assertIn("sector_lock:healthcare_wellness", locked["overrides"])

    def test_sector_without_lock_is_untouched(self):
        """A sector with no forbidden brains (real_estate) must not alter routing."""
        plain = br.route_decision({"date": "2026-01-05"})
        with_sector = br.route_decision({"date": "2026-01-05", "sector": "real_estate"})
        self.assertEqual(with_sector["primary"], plain["primary"])
        self.assertNotIn("sector_lock:real_estate", with_sector["overrides"])


if __name__ == "__main__":
    unittest.main()
