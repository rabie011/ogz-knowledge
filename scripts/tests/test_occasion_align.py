#!/usr/bin/env python3
"""Guards occasion alignment (Mohamed 2026-06-14: "confirmed with occasion, everything aligned").
Locks: (1) a DAILY slot caption that invents a holiday is misaligned; (2) an OCCASION slot caption
must match its occasion and no other; (3) the Rule #9 substring scar never fires (عيد in سعيد/
يعيدني, الحج in الحجم); (4) pre_ship_gate HARD-blocks a daily occasion-fabrication."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import occasion_align as oa
import pre_ship_gate as gate


class TestOccasionAlign(unittest.TestCase):

    def test_daily_inventing_eid_is_misaligned(self):
        slot = {"type": "daily", "occasion": None}
        self.assertTrue(oa.caption_misaligned(slot, "كل عام وانتم بخير، العيد أحلى مع جريشتنا"))

    def test_daily_inventing_ramadan_is_misaligned(self):
        slot = {"type": "daily", "occasion": None}
        self.assertTrue(oa.caption_misaligned(slot, "نستعد لرمضان بالسحور المميز"))

    def test_daily_plain_everyday_is_clean(self):
        slot = {"type": "daily", "occasion": None}
        self.assertIsNone(oa.caption_misaligned(slot, "استراحة بعد يوم طويل، طبق جريش دافئ"))

    def test_substring_scar_never_fires(self):
        """Rule #9: عيد inside سعيد/يعيدني and الحج inside الحجم are NOT occasions."""
        slot = {"type": "daily", "occasion": None}
        for safe in ("سعيد بلقائكم اليوم", "والجريش يعيدني للهدوء", "جريشة بالحجم العائلي",
                     "نعيد الكرّة كل أسبوع"):
            self.assertIsNone(oa.caption_misaligned(slot, safe), f"false positive on «{safe}»")
        self.assertEqual(oa.occ_hits("سعيد بالحجم"), set())

    def test_occasion_slot_must_match(self):
        eid_slot = {"type": "occasion", "occasion": "eid_al_fitr"}
        self.assertIsNone(oa.caption_misaligned(eid_slot, "عيدكم مبارك، جريشة العيد وصلت"))   # matches
        self.assertTrue(oa.caption_misaligned(eid_slot, "نستعد لرمضان بالسحور"))               # wrong occasion

    def test_gate_hard_blocks_daily_fabrication(self):
        post = {"slot": {"type": "daily", "occasion": None},
                "captions": ["كل عام وانتم بخير، العيد يبدأ بجريشتنا"]}
        v = gate.gate(post, "eatjurisha")
        self.assertTrue(v["block"], "daily occasion-fabrication must HARD-block at the gate")
        self.assertTrue(any("occasion misalignment" in h for h in v["hard_kills"]))


if __name__ == "__main__":
    unittest.main()
