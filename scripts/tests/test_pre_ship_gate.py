#!/usr/bin/env python3
"""Guards the pre-ship quality gate so the 2026-06-14 issue class CANNOT recur:
  - the SUBSTRING false-positive class (جريشة scar): حج in بالحجم, جاهز the delivery app
    must NOT trigger a sacred-worship kill.
  - the TRUE cultural kills Mohamed cares about MUST fire (royal family, Hajj sales-hook,
    imported new-culture).
  - jurisha cloud-kitchen (no dine-in).
Run by `make_sure` every cycle (unittest discover -s scripts/tests)."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pre_ship_gate as g


def _post(caption, occasion="evergreen", scene=""):
    return {"captions": [caption], "idea": {"scene_ar": scene}, "slot": {"occasion": occasion}}


class TestGateFalsePositives(unittest.TestCase):
    """The جريشة scar must never recur — no substring kills."""

    def test_size_word_not_sacred(self):
        # بالحجم contains حج; جاهز is the delivery app — neither is sacred-worship
        v = g.gate(_post("جريشة بالحجم العائلي، اطلبها من جاهز توصلك بسرعة"), "eatjurisha")
        self.assertNotIn("sacred-worship (Hajj/Umrah/Haram) used as a sales hook", v["hard_kills"],
                         f"FALSE POSITIVE: {v['hard_kills']}")

    def test_booking_word_not_sacred(self):
        v = g.gate(_post("احجز طاولتك واستمتع بالحجز المسبق"), "albaik")
        self.assertNotIn("sacred-worship (Hajj/Umrah/Haram) used as a sales hook", v["hard_kills"])

    def test_clean_post_passes(self):
        v = g.gate(_post("جريش سعودي أصيل، نكهة تشبع وتدفّي القلب"), "eatjurisha")
        self.assertNotEqual(v["verdict"], "KILL", f"clean post killed: {v['hard_kills']}")


class TestGateTruePositives(unittest.TestCase):
    """The cultural misses Mohamed rejected MUST be caught."""

    def test_royal_family_killed(self):
        v = g.gate(_post("في يوم الوطن تجتمع عائلة آل سعود حول الطاولة", "saudi_national_day"), "eatjurisha")
        self.assertEqual(v["verdict"], "KILL")
        self.assertTrue(any("royal" in k for k in v["hard_kills"]))

    def test_hajj_sales_hook_killed(self):
        v = g.gate(_post("بعد الطواف، اطلبوا الجريش طعم الوطن", "hajj_season"), "eatjurisha")
        self.assertEqual(v["verdict"], "KILL")
        self.assertTrue(any("sacred" in k for k in v["hard_kills"]))

    def test_new_culture_killed(self):
        v = g.gate(_post("بيض ملون يزيّن مائدة العيد", "eid_al_fitr"), "eatjurisha")
        self.assertEqual(v["verdict"], "KILL")
        self.assertTrue(any("new-culture" in k for k in v["hard_kills"]))

    def test_new_culture_with_definite_article_killed(self):
        # the blind spot: 'بيض الملون' (with ال) must KILL too, not just 'بيض ملون'
        v = g.gate(_post("الجد يلوّن بيض الملون مع الأحفاد صباح العيد", "eid_al_fitr"), "albaik")
        self.assertEqual(v["verdict"], "KILL", "بيض الملون (with ال) slipped the gate")

    def test_jurisha_dine_in_killed(self):
        v = g.gate(_post("تفضلوا إلى مطعمنا والجلسة في صالتنا"), "eatjurisha")
        self.assertEqual(v["verdict"], "KILL")
        self.assertTrue(any("cloud" in k.lower() or "dine" in k.lower() for k in v["hard_kills"]))


if __name__ == "__main__":
    unittest.main()
