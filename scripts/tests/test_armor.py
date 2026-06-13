#!/usr/bin/env python3
"""B116+B117 — THE ARMOR SUITE: caption_filter + truth_guards under real killed captions.

Every fixture is a REAL kill with provenance — a caption that actually shipped wrong,
or that Mohamed actually struck. A test that never saw a real kill proves nothing
about the moat (RABIE, D4). Scar → scar tissue (Rule #4 step 7).

Run: python3 -m unittest discover -s scripts/tests -v
Wired into make_sure as the armor_tests gate.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from caption_filter import (check, cultural_check, dialect_check, length_check,
                            offer_check)
from truth_guards import apply_guards, ungrounded


class TestCulturalGate(unittest.TestCase):
    def test_dua_with_brand_dies(self):
        # the g2 wire case — prayer_as_commercial_backdrop (Allah token + brand token)
        ok, hits = cultural_check("اللهم بارك سفرتنا مع البيك")
        self.assertFalse(ok, hits)

    def test_sidr_banned(self):
        # Mohamed 2026-06-13 01:23 verbatim: «we can't use the word سدر it means boobs»
        ok, hits = cultural_check("عسل سدر أصلي من المنحل")
        self.assertFalse(ok, hits)

    def test_clean_caption_passes(self):
        ok, hits = cultural_check("قهوتك الصباحية جاهزة، مرّ علينا")
        self.assertTrue(ok, hits)


class TestDialectGate(unittest.TestCase):
    def test_egyptian_markers_die(self):
        # Mohamed 2026-06-13 ×2: «عدل الكابشن الكتبابه غلط ومش سعودي»
        ok, hits = dialect_check("مش هتلاقي زي كده في أي مكان، عايز تجرب؟")
        self.assertFalse(ok)
        self.assertGreaterEqual(len(hits), 2, hits)

    def test_saudi_caption_passes(self):
        ok, hits = dialect_check("ما تلقى مثل كذا بأي مكان — الحين وصل عندنا")
        self.assertTrue(ok, hits)

    def test_msa_passes(self):
        # فصحى is not a dialect violation (قوي is valid MSA — excluded from markers)
        ok, hits = dialect_check("نكهة قوية تستحق التجربة")
        self.assertTrue(ok, hits)

    def test_dialect_wired_into_check(self):
        passes, reasons = check("مش عايز أروح دلوقتي للمطعم")
        self.assertFalse(passes)
        self.assertTrue(any(r.startswith("dialect:") for r in reasons), reasons)


class TestLengthAndOffer(unittest.TestCase):
    def test_short_law_15_words(self):
        # his ruling: SHORT = 15 words max (short_caption_number → w15)
        long_cap = "اليوم نحتفل مع كل العائلة الكريمة بمناسبة العيد السعيد ونقدم لكم أشهى الأطباق الشعبية الأصيلة من مطبخنا إلى بيتكم مباشرة"
        ok, _ = length_check(long_cap)
        self.assertFalse(ok)
        ok2, _ = length_check("جريشة الليلة على سفرتكم")
        self.assertTrue(ok2)

    def test_unconfirmed_offer_dies(self):
        # prices_off_until_truth: offer language without a confirmed offer = kill
        ok, hits = offer_check("عرض خاص! خصم ٢٠٪ على كل الطلبات", has_confirmed_offer=False)
        self.assertFalse(ok, hits)
        ok2, _ = offer_check("عرض خاص! خصم ٢٠٪", has_confirmed_offer=True)
        self.assertTrue(ok2)


class TestTruthGuards(unittest.TestCase):
    """Each fixture is the REAL caption that created the guard."""

    def test_g1_invented_program(self):
        # June 12 zoom-r7: fabricated training program + certification
        s, k = apply_guards(["خريج برنامج البيك الصيفي، شيف معتمد يقدم لكم الأفضل"],
                            "البيك كرسبي دجاج", {})
        self.assertEqual(len([x for x in k if x["guard"] == "event_claim"]), 1, k)

    def test_g3_hallucinated_prince(self):
        # June 11 — the worst truth violation: invented a real person's presence
        s, k = apply_guards(["احتفلنا بحضور الأمير سعود بن عبدالله بن جلوي"],
                            "البيك كرسبي", {"documented_moment": False})
        self.assertTrue(any(x["guard"] == "ungrounded_name" for x in k), k)

    def test_g3_promo_name_needs_corpus(self):
        # June 11 «التوأم كرسبي بيك x2» — invented promo name
        bad = ungrounded("جرب التوأم كرسبي بيك اليوم", "البيك دجاج كرسبي وجبات", False)
        self.assertIsNotNone(bad)
        ok = ungrounded("جرب التوأم كرسبي بيك اليوم",
                        "البيك دجاج التوأم كرسبي بيك عروضنا", False)
        self.assertIsNone(ok)

    def test_g8_consultation_lie(self):
        # June 12 — the consultation lie survived two regens; fake service = real calls
        s, k = apply_guards(["احجز استشارة مجانية مع خبير التغذية الآن"],
                            "مطعم صحي وجبات", {})
        self.assertTrue(any(x["guard"] == "service_claim" for x in k), k)

    def test_family_voice_ruling(self):
        # Mohamed portal ruling 2026-06-12: family-voice lines BLOCKED for all brands
        s, k = apply_guards(["أمي جابت البيك وقالت هذا أحسن عشاء"], "البيك", {})
        self.assertTrue(any(x["guard"] == "family_voice_blocked" for x in k), k)

    def test_g2_offer_on_eid(self):
        s, k = apply_guards(["خصم ٢٠٪ بمناسبة عيد الفطر المبارك"],
                            "مطعم", {"occasion": "eid_al_fitr"})
        self.assertTrue(any(x["guard"] == "offer_on_emotional" for x in k), k)

    def test_g4_journey_filler(self):
        s, k = apply_guards(["انطلقوا معنا في رحلة النكهات الفريدة"], "مطعم", {})
        self.assertTrue(any(x["guard"] == "bilingual_filler" for x in k), k)

    def test_g5_single_cta_across_set(self):
        # second option has non-CTA content → its CTA sentence is stripped
        s, k = apply_guards(["جريشة الليلة تجمع أهل البيت، اطلبوا الآن",
                             "نكهة البيت وصلت لباب بيتك وريحتها فاحت. اطلبوا من التطبيق"],
                            "جريشة أهل البيت تطبيق نكهة", {})
        cta_count = sum("اطلب" in x for x in s)
        self.assertLessEqual(cta_count, 1, s)

    def test_g5_least_bad_keeps_bare_cta(self):
        # documented soft edge: a second option that is ONLY a CTA survives intact —
        # destroying it entirely would violate never-zero/least-bad
        s, k = apply_guards(["اطلبوا الآن من جاهز", "اطلبوها اليوم"],
                            "جاهز اطلب", {})
        self.assertEqual(len(s), 2)

    def test_g6_word_collision(self):
        s, k = apply_guards(["اطلب من جاهز جاهز اليوم"], "جاهز توصيل اطلب اليوم من", {})
        self.assertTrue(s and "جاهز جاهز" not in s[0], s)

    def test_never_zero_survivors(self):
        # the least-bad rule: human eyes decide downstream, the set never empties
        s, k = apply_guards(["خصم ٥٠٪ على كل شيء"], "", {"occasion": "ramadan"})
        self.assertEqual(len(s), 1)

    def test_foreign_hashtag_stripped_real_kept(self):
        # B039 class: the brand's REAL hashtag survives; a foreign one dies
        s, k = apply_guards(["قعدة الويكند #مننا_ويفهم_جونا #فولو_فور_فولو"],
                            "بارنز قهوة", real_hashtags={"مننا_ويفهم_جونا"})
        self.assertTrue(s, k)
        self.assertIn("#مننا_ويفهم_جونا", s[0])
        self.assertNotIn("#فولو_فور_فولو", s[0])


class TestTasteGuard(unittest.TestCase):
    """June 13: kill_patterns was a WRITE-ONLY organ — his family×7 ruling changed
    nothing at render. This suite pins the wire."""

    KP = [{"pattern": "family_scene_overuse"}, {"pattern": "delivery_app_cta_overuse"}]

    def test_family_scene_killed(self):
        from render_client_slot import taste_guard
        kept, killed = taste_guard(
            ["العيلة كلها حول السفرة الليلة", "قهوتك الصباحية وصلت"], self.KP)
        self.assertEqual(len(killed), 1, (kept, killed))
        self.assertEqual(killed[0][1], "family_scene_overuse")
        self.assertEqual(kept, ["قهوتك الصباحية وصلت"])

    def test_app_cta_killed_but_ready_is_innocent(self):
        from render_client_slot import taste_guard
        kept, killed = taste_guard(
            ["اطلبها من جاهز الحين", "جريشة جاهزة على سفرتك"], self.KP)
        self.assertEqual(len(killed), 1, (kept, killed))
        self.assertIn("جريشة جاهزة على سفرتك", kept)  # جاهزة = ready, not the app

    def test_never_empties(self):
        from render_client_slot import taste_guard
        kept, killed = taste_guard(["لمة العيلة عند جدتي"], self.KP)
        self.assertEqual(len(kept), 1)  # least-bad survives flagged

    def test_inactive_pattern_no_kill(self):
        from render_client_slot import taste_guard
        kept, killed = taste_guard(["العيلة كلها هنا"], [])
        self.assertFalse(killed)


class TestWornGoldQuarantine(unittest.TestCase):
    def test_dropped_gold_never_fewshots(self):
        # his drop_conflicted ruling 2026-06-13: the exact caption that sat in few-shot
        from render_client_slot import STANDING_WORN
        struck = "وهل في أحلى من لحظة تجمعنا حول البيك في العيد"
        self.assertTrue(any(w in struck for w in STANDING_WORN))
        clean = "كنز صغير لبطل صغير"
        self.assertFalse(any(w in clean for w in STANDING_WORN))


if __name__ == "__main__":
    unittest.main()
