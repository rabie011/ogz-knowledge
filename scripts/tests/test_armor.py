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


class TestV6BriefHashtags(unittest.TestCase):
    def test_brief_real_tags_survive_v6_pattern(self):
        # June 13: the 41-brand v6 path called apply_guards without real_hashtags —
        # the brand's own brief tags died. This mirrors the fixed call exactly.
        brief_hashtags = "#انتم_والبيك_جيران #صنع_في_السعودية"
        tags = {x.lstrip("#") for x in brief_hashtags.split() if x.startswith("#")}
        s, k = apply_guards(["جيرة عمر، وطعم ما يتغير #انتم_والبيك_جيران #حظك_حلو"],
                            "البيك", {}, real_hashtags=tags)
        self.assertIn("#انتم_والبيك_جيران", s[0])
        self.assertNotIn("#حظك_حلو", s[0])


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

    def test_all_killed_returns_empty_NEVER_readmits(self):
        """Rule #8 (June 14 root-hunt fix): when EVERY option carries his taste-kill ruling,
        taste_guard returns EMPTY — it must NOT re-admit the least-bad killed line. The old
        `kept=[options[0]]` re-shipped a caption his ruling just killed (THE leak behind his
        'all the same / repetition' complaint). The caller regenerates with feedback or holds
        the slot; a ruled-against caption never ships."""
        from render_client_slot import taste_guard
        kept, killed = taste_guard(["لمة العيلة عند جدتي"], self.KP)
        self.assertEqual(kept, [])          # refuses — does NOT re-admit the killed line
        self.assertEqual(len(killed), 1)    # and reports what it killed, for the regen feedback

    def test_inactive_pattern_no_kill(self):
        from render_client_slot import taste_guard
        kept, killed = taste_guard(["العيلة كلها هنا"], [])
        self.assertFalse(killed)


class TestFewShotNotPoisonedByBannedGold(unittest.TestCase):
    """June 14 root-hunt of Mohamed's 'all the same / repetition' complaint: the gold few-shot
    was teaching the pen the exact formulas he banned (all 6 jurisha gold were delivery-CTA or
    family-scene). A gold line matching an ACTIVE kill_pattern must never lead the few-shot."""

    def test_jurisha_fewshot_has_no_banned_core(self):
        import json
        from pathlib import Path
        from render_client_slot import load_client, TASTE_GUARD_LEXICON
        B = Path(__file__).parent.parent.parent
        if not (B / "clients/eatjurisha/profile/gold.json").exists():
            self.skipTest("no jurisha gold")
        c = load_client("eatjurisha")
        active = [k.get("pattern") for k in c.get("kill_patterns", []) if isinstance(k, dict)]
        if not active:
            self.skipTest("no active kill_patterns")
        leaked = [e for e in c["exemplars"]
                  if any(p in TASTE_GUARD_LEXICON and TASTE_GUARD_LEXICON[p].search(e) for p in active)]
        self.assertEqual(leaked, [], f"few-shot still teaches a banned formula: {leaked}")


class TestSceneDiversity(unittest.TestCase):
    """his ruling: «if the idea is family they can't use it for all the posts»"""

    def test_core_detection(self):
        from render_client_slot import scene_core
        self.assertIn("family", scene_core("لمة العيلة حول السفرة"))
        self.assertIn("craving", scene_core("ريحة القرمشة وصلت"))
        self.assertFalse(scene_core("نص محايد بلا أي مشهد"))

    def test_worn_core_sinks(self):
        from render_client_slot import diversity_prefer
        opts = ["العيلة مجتمعة الليلة", "ريحة القهوة تسبق الخطوات"]
        recent = [{"family"}, {"family"}]  # last 2 slots were family
        out = diversity_prefer(opts, recent)
        self.assertEqual(out[0], "ريحة القهوة تسبق الخطوات")

    def test_no_repeat_no_reorder(self):
        from render_client_slot import diversity_prefer
        opts = ["العيلة مجتمعة", "ريحة القهوة"]
        out = diversity_prefer(opts, [{"family"}, {"craving"}])
        self.assertEqual(out, opts)  # no worn core → original pen order stands

    def test_never_drops(self):
        from render_client_slot import diversity_prefer
        opts = ["العيلة مجتمعة الليلة"]
        out = diversity_prefer(opts, [{"family"}, {"family"}])
        self.assertEqual(len(out), 1)


class TestBatchDiversityGate(unittest.TestCase):
    """B_div_gate — the hard answer to his 06-13 «still family / make them different».
    diversity_prefer only soft-reorders; THIS blocks a batch over-concentrated on one core."""

    def test_jurish_dish_not_sport(self):
        # ZOOM-OUT scar June 13: bare substring جري matched جريش/جريشة (jurisha's dish) →
        # 48% of a FOOD brand tagged energy_sport (a phantom reported to Mohamed as fact).
        from render_client_slot import scene_core
        self.assertEqual(scene_core("منتج حقيقي: رز كابلي وجريش"), {"product_shoutout"})
        self.assertNotIn("energy_sport", scene_core("جريش بالحجم العائلي"))
        self.assertIn("energy_sport", scene_core("تمرين الصباح ولياقة"))  # real sport still fires

    def test_label_prefix_authoritative(self):
        from render_client_slot import scene_core
        self.assertEqual(scene_core("family: لمة العيلة"), {"family"})
        self.assertEqual(scene_core("eid: جمعة العيد"), {"occasion"})
        self.assertEqual(scene_core("قناة: اطلب عبر جاهز"), {"channel_cta"})

    def test_coverage_reported(self):
        from render_client_slot import batch_diversity_check
        slots = [{"date": f"d{i}", "angle_theme": "نص محايد بلا مشهد"} for i in range(10)]
        r = batch_diversity_check(slots, 0.30)
        self.assertLess(r["coverage"], 0.5)  # all-unclassified
        self.assertFalse(r["ok"])            # low coverage is NOT a silent green
        self.assertTrue(r["low_coverage"])

    def test_six_family_ideas_caught(self):
        from render_client_slot import batch_diversity_check
        slots = [{"date": f"d{i}", "angle_theme": "لمة العيلة حول السفرة"} for i in range(6)]
        slots += [{"date": f"e{i}", "angle_theme": "قهوة الصباح وحدك بهدوء"} for i in range(4)]
        r = batch_diversity_check(slots, 0.30)
        self.assertFalse(r["ok"])
        fam = next(v for v in r["violations"] if v["key"] == "family")
        self.assertEqual(fam["count"], 6)  # 6/10 = 60% > 30%
        self.assertTrue(fam["slots"])      # names the excess to re-roll

    def test_recipe_overuse_caught(self):
        from render_client_slot import batch_diversity_check
        slots = [{"date": f"d{i}", "angle_theme": "نص محايد", "formula": "CF_01"} for i in range(7)]
        slots += [{"date": f"e{i}", "angle_theme": "نص", "formula": "CF_02"} for i in range(3)]
        r = batch_diversity_check(slots, 0.30)
        self.assertTrue(any(v["kind"] == "recipe" and v["key"] == "CF_01" for v in r["violations"]))

    def test_diverse_batch_passes(self):
        from render_client_slot import batch_diversity_check
        cores = ["لمة العيلة", "قهوة وحدك بهدوء", "ريحة القرمشة", "برد الشتا",
                 "شلة الأصحاب", "طاقة بعد الجري", "ذكريات زمان", "بطل صغير"]
        slots = [{"date": f"d{i}", "angle_theme": c, "formula": f"CF_{i:02d}"} for i, c in enumerate(cores)]
        r = batch_diversity_check(slots, 0.30)
        self.assertTrue(r["ok"], r["violations"])

    def test_empty_batch_safe(self):
        from render_client_slot import batch_diversity_check
        self.assertTrue(batch_diversity_check([], 0.30)["ok"])


class TestWornGoldQuarantine(unittest.TestCase):
    def test_dropped_gold_never_fewshots(self):
        # his drop_conflicted ruling 2026-06-13: the exact caption that sat in few-shot
        from render_client_slot import STANDING_WORN
        struck = "وهل في أحلى من لحظة تجمعنا حول البيك في العيد"
        self.assertTrue(any(w in struck for w in STANDING_WORN))
        clean = "كنز صغير لبطل صغير"
        self.assertFalse(any(w in clean for w in STANDING_WORN))

    def test_clishy_fixture_killed_at_filter(self):
        # his ★3 «the caption is clishy» (judge2_eatjurisha_2027-02-22) PASSED the
        # filter on June 13 — worn formulas are now filter-enforced. ذكريات itself
        # stays legal (protected by his own ★5 gold) — the FORMULA dies, not the word.
        passes, reasons = check("جريّشة وذكريات التأسيس في كل لقمة. اطلبوا الآن من هنقرستيشن!")
        self.assertFalse(passes)
        self.assertTrue(any(r.startswith("worn:") for r in reasons), reasons)
        ok, _ = check("ذكريات التأسيس حاضرة على سفرتنا اليوم")
        self.assertTrue(ok)  # ذكريات alone is his ★5-protected territory

    def test_approved_with_complaint_quarantined(self):
        # his 01:21 note on a ★4 approve: «why يرفع المعنويات dosent feel good» —
        # approval stands in gold, the phrase never teaches
        from render_client_slot import STANDING_WORN
        self.assertTrue(any(w in "والآن دور البيك يرفع المعنويات" for w in STANDING_WORN))


if __name__ == "__main__":
    unittest.main()
