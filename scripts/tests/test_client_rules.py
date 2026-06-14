#!/usr/bin/env python3
"""Guards the client-rules organ gate (RABIE NO-GO 2026-06-14: 24 old mistakes shipped because
nothing read the client's confirmed organs). Locks: real-person/family-voice/face/family/format/
cross-brand/brand-register are enforced, and the Rule #9 boundary (title+preposition is NOT a
named person) never false-fires."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import client_rules as cr

OV_ALL = {"real_person_mentions": "off", "family_voice_lines": "blocked_permanent",
          "face_visibility": "never", "family_member_visibility": "never"}


class TestClientRules(unittest.TestCase):

    def _kinds(self, post, handle="eatjurisha"):
        return {k for k, sev, det in cr.violations(post, handle) if sev == "block"}

    def test_named_person_blocked_but_title_alone_clean(self):
        self.assertEqual(cr._named_person("الكابتن عادل هو بطلنا"), "الكابتن عادل")  # named → caught
        self.assertIsNone(cr._named_person("الكابتن في جيبك"))                        # title+prep → NOT a person
        self.assertIsNone(cr._named_person("استراحة هادئة بعد يوم طويل"))             # neutral

    def test_family_voice_line_blocked(self):
        v = self._kinds({"captions": ["أختي الصغيرة تقول: بابا كأنك تعرف"]})
        self.assertIn("family_voice", v)

    def test_face_and_family_visibility_in_visual(self):
        v = self._kinds({"captions": ["طبق دافئ"], "visual": {"phone_shoot_card": [
            "تأكد من وجود ابتسامات وتبادل نظرات دافئة بين الجالسين، مع الأطفال يلعبون"]}})
        self.assertIn("face_visibility", v)
        self.assertIn("family_visibility", v)

    def test_cloud_kitchen_blocks_dinein_and_cart(self):
        self.assertIn("format_storefront", self._kinds({"captions": ["عربة الطعام في السوق الشعبي"]}, "eatjurisha"))
        self.assertIn("format_dinein", self._kinds({"captions": ["نجلس في المطعم حول الطاولة"]}, "eatjurisha"))

    def test_cross_brand_gym_on_food(self):
        self.assertIn("cross_brand", self._kinds({"captions": ["بعد التمرين في الصالة الرياضية، نكافئ أنفسنا بالبيك"]}, "albaik"))

    def test_brand_register_english_legal_name(self):
        self.assertIn("brand_register", self._kinds({"captions": ["صوت عبوة «ALBAIK® Food Systems Company» يتفتح"]}, "albaik"))

    def test_clean_post_passes(self):
        self.assertEqual(self._kinds({"captions": ["البخار يتصاعد من طبق الجريش، ولحظة دفء تبدأ"],
                                      "visual": {"phone_shoot_card": ["لقطة مقربة للطبق واليدين فقط"]}}), set())


if __name__ == "__main__":
    unittest.main()
