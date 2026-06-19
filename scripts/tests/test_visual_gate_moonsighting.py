#!/usr/bin/env python3
"""Locks B048 — the moonsighting recheck in the visual gate. ramadan/eid/hajj slots carry a
Gregorian date the year_map fixed months ago, but hijri dates shift with the actual moon sighting
(±1-2 days). Auto-publishing risks an Eid greeting on the WRONG day — a one-shot trust break (his
taste law: conservative cultural defaults, never look unprofessional). year_map.py sets
slot.moonsighting_check on the moon-dependent occasions; checklist_for is its CONSUMER (Rule #6).
These tests lock: (1) a moonsighting slot RAISES the check, (2) a daily/non-moon slot does NOT,
(3) the named occasion + date ride in the check text, (4) a missing/absent slot never raises it."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import visual_gate_checklist as vg

HANDLE = "eatjurisha"  # has profile/red_lines.json, state.json, year_map.json


def _ids(card):
    return {it["id"] for it in vg.checklist_for(HANDLE, card)["items"]}


class TestVisualGateMoonsighting(unittest.TestCase):
    def test_moonsighting_slot_raises_check(self):
        card = {"captions": ["لقمة دافية"], "idea": {"scene_ar": "مشهد"},
                "slot": {"occasion": "eid_al_fitr", "date": "2027-03-09", "moonsighting_check": True}}
        self.assertIn("moonsighting_recheck", _ids(card))

    def test_non_moon_slot_no_check(self):
        card = {"captions": ["لقمة دافية"], "idea": {"scene_ar": "مشهد"},
                "slot": {"occasion": "saudi_national_day", "date": "2026-09-23", "moonsighting_check": False}}
        self.assertNotIn("moonsighting_recheck", _ids(card))

    def test_missing_slot_no_check(self):
        # a card with no slot embedded must never raise it (no crash, no false flag)
        card = {"captions": ["لقمة دافية"], "idea": {"scene_ar": "مشهد"}}
        self.assertNotIn("moonsighting_recheck", _ids(card))

    def test_occasion_and_date_in_check_text(self):
        card = {"captions": ["x"], "idea": {"scene_ar": "s"},
                "slot": {"occasion": "ramadan", "date": "2027-02-08", "moonsighting_check": True}}
        item = next(it for it in vg.checklist_for(HANDLE, card)["items"]
                    if it["id"] == "moonsighting_recheck")
        self.assertIn("ramadan", item["check"])
        self.assertIn("2027-02-08", item["check"])
        self.assertEqual(item["source"], "year_map.moonsighting_check (B048)")
        self.assertIn("REQUIRES-HUMAN-VERIFY", item["check"])


if __name__ == "__main__":
    unittest.main()
