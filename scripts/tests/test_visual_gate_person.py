#!/usr/bin/env python3
"""Locks B144 — the person-mention check in the visual gate. A caption naming a real TITLED
person (الأمير/الشيخ/الدكتور/معالي/سمو + اسم) is a trust land-mine ("named real people" is a
recorded kill, Rule #13); the human MUST verify it before publish. These tests lock:
(1) a titled name RAISES the person_named check, (2) a clean/plain-first-name caption does NOT,
(3) the detector is the shared truth_guards.PERSON_AR (one-boundary law — not redefined here)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import visual_gate_checklist as vg
from truth_guards import PERSON_AR

HANDLE = "eatjurisha"  # has profile/red_lines.json, state.json, year_map.json


def _ids(card):
    return {it["id"] for it in vg.checklist_for(HANDLE, card)["items"]}


class TestVisualGatePerson(unittest.TestCase):
    def test_titled_person_raises_check(self):
        card = {"captions": ["برعاية صاحب السمو الأمير محمد بن سلمان، نحتفل اليوم 🇸🇦"],
                "idea": {"scene_ar": "مشهد احتفالي"}}
        self.assertIn("person_named", _ids(card))

    def test_clean_caption_no_check(self):
        card = {"captions": ["بخار الجريش، عطر دافي يريح القلوب ويجدد الذاكرة 🇸🇦"],
                "idea": {"scene_ar": "مشهد هادئ"}}
        self.assertNotIn("person_named", _ids(card))

    def test_plain_first_name_no_check(self):
        # PERSON_AR targets HONORIFIC+name (real public figures), not fictional first names
        card = {"captions": ["في صباح العيد، تجلس فاطمة في شرفتها تحتسي قهوتها"],
                "idea": {"scene_ar": "مشهد"}}
        self.assertNotIn("person_named", _ids(card))

    def test_uses_shared_detector(self):
        self.assertIs(vg.PERSON_AR, PERSON_AR)

    def test_named_string_listed_in_check(self):
        card = {"captions": ["كلمة معالي الوزير أحمد في الحفل"],
                "idea": {"scene_ar": "s"}}
        item = next(it for it in vg.checklist_for(HANDLE, card)["items"] if it["id"] == "person_named")
        self.assertIn("معالي", item["check"])
        self.assertEqual(item["source"], "truth_guards.PERSON_AR (B144)")


if __name__ == "__main__":
    unittest.main()
