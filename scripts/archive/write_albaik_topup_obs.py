#!/usr/bin/env python3
"""
write_albaik_topup_obs.py
SESSION C — AlBaik (@albaik) Ref-008 top-up: 25→50 obs
Coverage: March 2025 – January 2026 (gaps in existing corpus)
Engagement range: 494–12,464 likes
Run: python3 scripts/write_albaik_topup_obs.py
"""
import json, re
from pathlib import Path
from datetime import datetime, timezone

BASE     = Path(__file__).parent.parent
OUT      = BASE / "11_who_to_learn_from" / "observations" / "f_and_b"
NOW      = "2026-05-25T10:00:00Z"

ACCOUNT_NORM = "OGZ-F-AND-B-Reference-008"
ACCOUNT_ULID = "01KRKHS8R9HB73WWWGKXVDMC3D"
SECTOR       = "f_and_b"

ULIDS = [
    "01KSE6DAF9Q4960ANW93MV43TW",  # 0  DK7AbSvPiRI  2025-06-15  video  12464
    "01KSE6DAF99QAK6WJ3W07FC0XF",  # 1  DO_SOHvDl3n  2025-09-24  video   9666
    "01KSE6DAF9DF4QT7VJ1KAC4DVB",  # 2  DIeMLLANU0P  2025-04-15  video   6360
    "01KSE6DAF9RP9W6PDD196C1JFZ",  # 3  DH1ZHuYNVnv  2025-03-30  video   6017
    "01KSE6DAF95ZQSMM9TXHA5XHJM",  # 4  DOn5XjwDTl2  2025-09-15  crsl    4592
    "01KSE6DAF9CY8D5AA6B6C2BZ0C",  # 5  DRzpf6YAcIR  2025-12-03  video   2922
    "01KSE6DAF915GG144H2AN7W3D6",  # 6  DSXzMZukaUS  2025-12-17  video   2851
    "01KSE6DAF9PXX5N1606T3CWYTG",  # 7  DTIi3mPk-Z6  2026-01-05  video   2687
    "01KSE6DAF9TR8Z5SWM0JYH6JXT",  # 8  DRAZ_tpgt2f  2025-11-13  video   2120
    "01KSE6DAF9FHD6F63AP8FZP7E1",  # 9  DNzUdstUFOT  2025-08-26  video   2583
    "01KSE6DAF9AEPJYS1B4MRBP5JV",  # 10 DKp11_dNgGs  2025-06-08  crsl    2064
    "01KSE6DAF9D6CJ5B46K7YBF5Y2",  # 11 DMaODC4vbHc  2025-07-22  video   1989
    "01KSE6DAF919XQWWXH3GNYWHJZ",  # 12 DIrI4DINEtd  2025-04-20  video   1945
    "01KSE6DAF9WT2VHHJDSG2PXXCG",  # 13 DImarStN2qC  2025-04-18  photo   1639
    "01KSE6DAF9TRNG0SV7P2WD3E0A",  # 14 DPEfJCPDRQM  2025-09-26  video   1731
    "01KSE6DAF90NAGK9D8T7FJNYK8",  # 15 DKr4_5kNOXr  2025-06-09  video   1575
    "01KSE6DAF95RY2VR9E0E76BFMF",  # 16 DM96urhNP7U  2025-08-05  crsl    1080
    "01KSE6DAF9W4ZSSQFGSTJW3YAG",  # 17 DImDqScNUfw  2025-04-18  video    900
    "01KSE6DAF9JSZZVN4Y2ATHS819",  # 18 DNjKwg4NZmS  2025-08-19  video    743
    "01KSE6DAF9PAVTMNQF0E4QFH70",  # 19 DKhw2IONAh1  2025-06-05  crsl     734
    "01KSE6DAF98EBTRCSVDMZQXXHY",  # 20 DI32MrttHCt  2025-04-25  video    690
    "01KSE6DAF96WGGPMZ3Q2HBNQN2",  # 21 DPzCn8PDYDt  2025-10-14  video    662
    "01KSE6DAF9TBXY3M30ZT6EHFJA",  # 22 DKfrNLRtvso  2025-06-04  video    608
    "01KSE6DAF9T6JX64JS79T5GNKH",  # 23 DOVh_KnjeWo  2025-09-08  crsl     586
    "01KSE6DAF96E0WQF9ZTJ21YSZN",  # 24 DOBkYCIjZ0G  2025-08-31  photo    494
]

NO_FLAGS = []
CLEAN    = "clean"


def obs(i, shortcode, content_type, capture_date, day_of_week, aspect_ratio,
        composition_style, lighting, colors, setting, visual_complexity,
        language, register, tone, notable_phrases, cta,
        soft_flags, compliance, occasion, heritage, hosp_cues,
        free_notes, patterns, engagement_potential):
    ulid = ULIDS[i]
    path = OUT / f"{ulid}.json"
    if path.exists():
        return None
    return {
        "observation_ulid": ulid,
        "schema_version": 1,
        "account_handle_normalized": ACCOUNT_NORM,
        "account_ulid": ACCOUNT_ULID,
        "sector": SECTOR,
        "content_ref": {
            "filename": f"{shortcode}.{'mp4' if content_type == 'video' else 'jpg'}",
            "platform": "instagram",
            "content_type": content_type,
            "capture_date": capture_date,
            "source_url": f"https://www.instagram.com/p/{shortcode}/",
            "day_of_week": day_of_week,
            "aspect_ratio": aspect_ratio,
        },
        "visual_observations": {
            "composition_style": composition_style,
            "lighting": lighting,
            "color_palette_dominant": colors,
            "setting": setting,
            "visual_complexity": visual_complexity,
        },
        "voice_observations": {
            "language": language,
            "dialect_detected": "najdi",
            "register": register,
            "tone": tone,
            "notable_phrases": notable_phrases,
            "call_to_action_present": cta,
        },
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags": soft_flags,
            "overall_compliance": compliance,
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": occasion,
            "hospitality_cues": hosp_cues,
            "heritage_vs_modern": heritage,
            "free_notes": free_notes,
        },
        "pattern_matches": patterns,
        "quality_assessment": {
            "production_quality": "professional",
            "brand_consistency_with_account": "strong",
            "engagement_potential": engagement_potential,
        },
        "provenance": {
            "source": f"benchmark:@albaik; content:{shortcode}; browser_collected:2026-05-25",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b",
        },
        "occasion": occasion,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    observations = [

        # 0 ── DK7AbSvPiRI | 2025-06-15 | video | 12,464 likes | Twin Combo LTO (top performer)
        obs(0, "DK7AbSvPiRI", "video", "2025-06-15", "sunday", "vertical_9x16",
            "product_hero_close_up",
            "dramatic_moody",
            ["golden brown", "red", "white", "orange"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["كومبو التوأم", "على ذوووقك", "اطلبه الآن", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Highest-engagement product promo in this batch (12,464 likes). Twin Combo LTO with elongated 'ذوووق' conveying indulgence. Classic AlBaik product-first formula: sensory promise + urgency + hashtag. Proves duo-combo framing is a consistent engagement driver for this account.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Ultra-minimal copy with maximum product focus — AlBaik's proven top-performing format"},
                {"pattern_slug": "limited_time_promo", "confidence": "strong",
                 "notes": "Twin Combo LTO urgency driver with timer emoji"},
            ],
            "high"),

        # 1 ── DO_SOHvDl3n | 2025-09-24 | video | 9,666 likes | Beekiz Halapo launch
        obs(1, "DO_SOHvDl3n", "video", "2025-09-24", "wednesday", "vertical_9x16",
            "product_launch_reveal",
            "dramatic_moody",
            ["deep red", "orange", "golden brown", "white"],
            "studio", "complex",
            "arabic", "casual", "bold",
            ["برجر بيكيز", "لهاليبو", "حامض حلو حراق", "قرمشة", "يدهش الاحاسيس"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Second highest-engagement post in batch. Beekiz Burger with Halapo sauce — 4-sensation copy strategy (sour + sweet + spicy + crispy). 'يدهش الاحاسيس' (shocks the senses) is exceptionally visceral for food copy. New-product hype near National Day week amplified reach.",
            [
                {"pattern_slug": "product_launch_reveal", "confidence": "strong",
                 "notes": "New product debut with sensation-stacking copy — 4 sensory descriptors in one line"},
                {"pattern_slug": "sensory_language", "confidence": "strong",
                 "notes": "يدهش الاحاسيس — rare visceral phrasing in Saudi F&B copy, likely key to viral spread"},
            ],
            "high"),

        # 2 ── DIeMLLANU0P | 2025-04-15 | video | 6,360 likes | F1 Saudi GP Race Combo
        obs(2, "DIeMLLANU0P", "video", "2025-04-15", "tuesday", "vertical_9x16",
            "event_collab_product_hero",
            "dramatic_moody",
            ["red", "black", "white", "gold"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["عيش أجواء", "كومبو_السباق", "فورمولا1", "دبل الإثارة", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "F1 Saudi GP limited-edition 'Race Combo' — double-excitement framing mirrors the race itself. AlBaik activates sports events by renaming existing products with event-themed copy rather than creating new SKUs. Hashtag #أسس_وان ties to official race campaign. 6,360 likes confirms sports-event collab as tier-1 content pillar.",
            [
                {"pattern_slug": "event_collab_product", "confidence": "strong",
                 "notes": "F1 Saudi GP activation — race-themed combo rename with urgency messaging"},
                {"pattern_slug": "limited_time_promo", "confidence": "strong",
                 "notes": "LTO urgency embedded in event context doubles motivation to act"},
            ],
            "high"),

        # 3 ── DH1ZHuYNVnv | 2025-03-30 | video | 6,017 likes | Ramadan greeting
        obs(3, "DH1ZHuYNVnv", "video", "2025-03-30", "sunday", "vertical_9x16",
            "brand_occasion_greeting",
            "warm_soft",
            ["gold", "deep green", "white", "cream"],
            "studio", "simple",
            "arabic", "formal", "warm",
            ["أطيب الأماني", "كل عام وأنتم بخير"],
            False,
            NO_FLAGS, CLEAN,
            "ramadan", "heritage", ["ramadan_iftar_timing"],
            "Ramadan greeting video with 6,017 likes — confirms occasion content outperforms product promo frequency expectations. Minimal copy: only 1 sentence + tagline. Warm-heritage tone shift from AlBaik's usual bold brand voice shows seasonal code-switching. Single #البيك hashtag.",
            [
                {"pattern_slug": "occasion_greeting", "confidence": "strong",
                 "notes": "Ramadan warm-tone greeting — minimal copy maximises emotional resonance"},
                {"pattern_slug": "tone_code_switch", "confidence": "medium",
                 "notes": "Brand switches from bold/product to formal/warm for Ramadan — consistent pattern across Saudi F&B"},
            ],
            "high"),

        # 4 ── DOn5XjwDTl2 | 2025-09-15 | carousel | 4,592 likes | Khamis Mushait opening
        obs(4, "DOn5XjwDTl2", "carousel_slide", "2025-09-15", "monday", "landscape_4x3",
            "location_expansion_announcement",
            "natural_light",
            ["green", "brown", "white", "AlBaik red"],
            "outdoor", "moderate",
            "arabic", "casual", "warm",
            ["البيك_في_خميس_مشيط", "مرحبا تراحيب المطر", "لسرعة خدمتكم"],
            True,
            NO_FLAGS, CLEAN,
            "brand_campaign", "modern", ["regional_welcoming"],
            "New AlBaik location in Khamis Mushait with 4,592 likes — highest-engagement expansion announcement in the dataset. 'مرحبا تراحيب المطر' (welcome like the rain's welcome) is a poetic regional idiom, signaling cultural attunement to Aseer region's rainy climate. Menu limited at launch (4-piece chicken + 10-piece mashab only). Carousel format documents the community excitement.",
            [
                {"pattern_slug": "expansion_announcement", "confidence": "strong",
                 "notes": "New location reveal with regional idiom — cultural attunement to Aseer drives hyper-local engagement"},
                {"pattern_slug": "community_welcome", "confidence": "strong",
                 "notes": "Carousel documents community excitement, building anticipation across multiple slides"},
            ],
            "high"),

        # 5 ── DRzpf6YAcIR | 2025-12-03 | video | 2,922 likes | Twin Duo 2x LTO
        obs(5, "DRzpf6YAcIR", "video", "2025-12-03", "wednesday", "vertical_9x16",
            "product_hero_close_up",
            "dramatic_moody",
            ["golden brown", "red", "white", "orange"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["التوأم اللذيذ", "2x", "ساندويتشين فيليه الدجاج", "اطلب الآن", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Twin Duo 2x — double-sandwich format LTO. Bilingual '2x' numeral in Arabic copy demonstrates AlBaik's hybrid copywriting approach. Duo/twin combo is clearly a recurring product architecture (same pattern as DK7AbSvPiRI June 2025). High performer at 2,922 likes confirms twin-format works year-round.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Twin 2x combo — recurring LTO product architecture with consistent high engagement"},
                {"pattern_slug": "limited_time_promo", "confidence": "strong",
                 "notes": "LTO urgency framing with bilingual 2x numeral — hybrid copy style"},
            ],
            "high"),

        # 6 ── DSXzMZukaUS | 2025-12-17 | video | 2,851 likes | Twin Combo December
        obs(6, "DSXzMZukaUS", "video", "2025-12-17", "wednesday", "vertical_9x16",
            "product_hero_close_up",
            "dramatic_moody",
            ["golden brown", "red", "white", "cream"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["عرض التوأم", "على ذوووقك", "اطلبه الآن", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "December Twin Combo LTO rerun with 2,851 likes. Nearly identical copy pattern to June version (DK7AbSvPiRI) confirms AlBaik uses proven copy templates across LTO cycles. Wednesday posting pattern recurring for Twin Combo. Demonstrates the formula is formulaic by design — consistency over creativity in product promo.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Twin Combo LTO rerun — identical template to June version, intentional formula repetition"},
                {"pattern_slug": "limited_time_promo", "confidence": "strong",
                 "notes": "Same ذوووق elongation and timer emoji as June — AlBaik's proven product promo template"},
            ],
            "high"),

        # 7 ── DTIi3mPk-Z6 | 2026-01-05 | video | 2,687 likes | Crispy Bik Filet new launch
        obs(7, "DTIi3mPk-Z6", "video", "2026-01-05", "monday", "vertical_9x16",
            "new_product_launch_reveal",
            "dramatic_moody",
            ["golden brown", "white", "orange", "cream"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["جديد", "كرسبي بيك فيليه المقرمش", "جربه الآن"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Crispy Bik Filet new product launch — January 2026. Opening word 'جديد' (new) as caption anchor matches Double Crispy Bik launch pattern (DXzkeYyjdUb May 2026). Product naming convention: modifier + Bik + descriptor. Texture word 'المقرمش' (the crispy one) central to sensory positioning. 2,687 likes for a new launch is strong performance.",
            [
                {"pattern_slug": "product_launch_reveal", "confidence": "strong",
                 "notes": "جديد opener + texture focus — AlBaik's standard new product launch copy template"},
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Close-up texture focus identical to Double Crispy Bik launch — consistent format"},
            ],
            "high"),

        # 8 ── DRAZ_tpgt2f | 2025-11-13 | video | 2,120 likes | Fish Burger Combo LTO
        obs(8, "DRAZ_tpgt2f", "video", "2025-11-13", "thursday", "vertical_9x16",
            "product_hero_close_up",
            "dramatic_moody",
            ["ocean blue", "golden brown", "white", "AlBaik red"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["كومبو برجر سمك", "طعم تغوص فيه", "اطلب الآن", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Fish Burger Combo LTO with 2,120 likes. 'طعم تغوص فيه' (a taste you dive into) — aquatic metaphor for fish product, clever sensory alignment. Fish combo appears as a seasonal LTO product (not permanent menu), consistent with AlBaik's strategy of limited rotation to maintain excitement. Thursday posting for weekend consideration.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Fish combo with aquatic metaphor — sensory copy aligned to product category"},
                {"pattern_slug": "limited_time_promo", "confidence": "strong",
                 "notes": "LTO fish product — seasonal rotation strategy to drive urgency"},
            ],
            "high"),

        # 9 ── DNzUdstUFOT | 2025-08-26 | video | 2,583 likes | Big Bik Combo Challenge
        obs(9, "DNzUdstUFOT", "video", "2025-08-26", "tuesday", "vertical_9x16",
            "product_challenge_hero",
            "dramatic_moody",
            ["deep red", "golden brown", "white", "black"],
            "studio", "moderate",
            "arabic", "casual", "bold",
            ["التحدي صار أكبر", "بيج_بيك_كومبو", "اطلبه الآن", "لفترة محدودة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Big Bik Combo with challenge framing — 'التحدي صار أكبر' (the challenge got bigger) uses competitive language for a combo meal. Gamification of food ordering is an AlBaik technique. Big Bik is a supersized product line (premium tier). 2,583 likes confirms size-challenge positioning resonates with Saudi youth audience.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Big Bik Combo with challenge/competition framing — gamification of food ordering"},
                {"pattern_slug": "challenge_mechanic", "confidence": "medium",
                 "notes": "التحدي صار أكبر — challenge language for food product, appeals to youth competitive instinct"},
            ],
            "high"),

        # 10 ── DKp11_dNgGs | 2025-06-08 | carousel | 2,064 likes | Hajj pilgrims service
        obs(10, "DKp11_dNgGs", "carousel_slide", "2025-06-08", "sunday", "landscape_3x2",
            "pilgrimage_documentary",
            "natural_light",
            ["white", "gold", "green", "AlBaik red"],
            "outdoor", "moderate",
            "arabic", "formal", "reverent",
            ["يسر_وطمأنينة", "ضيوف الرحمن", "الحمد لله", "شرف خدمة"],
            False,
            NO_FLAGS, CLEAN,
            "hajj", "heritage", ["pilgrimage_service", "hospitality_pride"],
            "Hajj pilgrims service carousel with 2,064 likes. Hashtag #يسر_وطمأنينة (ease and peace of mind) is deeply spiritual — Quranic resonance. AlBaik serving Hajj pilgrims is a brand pillar tied to its Makkah origins. 'شرف خدمة' (honor of serving) frames commercial food service as spiritual duty. This is AlBaik's most culturally distinctive content type.",
            [
                {"pattern_slug": "occasion_pillar", "confidence": "strong",
                 "notes": "Hajj service positioning — AlBaik's unique brand asset as Makkah-origin F&B brand"},
                {"pattern_slug": "brand_values", "confidence": "strong",
                 "notes": "شرف خدمة framing — commercial service elevated to spiritual duty, uniquely Saudi brand positioning"},
            ],
            "high"),

        # 11 ── DMaODC4vbHc | 2025-07-22 | video | 1,989 likes | Esports World Cup Combo
        obs(11, "DMaODC4vbHc", "video", "2025-07-22", "tuesday", "vertical_9x16",
            "event_collab_product_hero",
            "dramatic_moody",
            ["dark charcoal", "neon green", "AlBaik red", "white"],
            "studio", "complex",
            "arabic", "casual", "bold",
            ["عيش أجواء البطولة", "كأس_العالم_للرياضات_الإلكترونية", "كومبو"],
            True,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "Esports World Cup Combo — AlBaik sponsored the Esports World Cup in Riyadh 2025. 'عيش أجواء البطولة' (live the championship atmosphere) mirrors F1 copy strategy. AlBaik's esports sponsorship positions the brand with Gen-Z/young-millennial audience. 1,989 likes shows esports activation performs near-equivalent to F1 activation.",
            [
                {"pattern_slug": "event_collab_product", "confidence": "strong",
                 "notes": "Esports World Cup combo — same event-renaming strategy as F1 Race Combo"},
                {"pattern_slug": "youth_culture_collab", "confidence": "strong",
                 "notes": "Esports sponsorship targets Gen-Z — AlBaik's multi-generational audience strategy"},
            ],
            "high"),

        # 12 ── DIrI4DINEtd | 2025-04-20 | video | 1,945 likes | F1 AlBaik Academy kids
        obs(12, "DIrI4DINEtd", "video", "2025-04-20", "sunday", "vertical_9x16",
            "brand_event_documentary",
            "warm_natural",
            ["AlBaik red", "white", "black", "yellow"],
            "indoor", "moderate",
            "arabic", "casual", "warm",
            ["أبنائنا", "جيل المستقبل", "فورمولا1", "حماس"],
            False,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "AlBaik Academy kids at F1 Saudi GP — CSR meets sports activation. 'أبنائنا' (our sons/children) and 'جيل المستقبل' (the future generation) frame the brand as invested in youth development, not just food. Warm documentary tone contrasts with the usual bold product content. 1,945 likes confirms community/CSR content outperforms expectations.",
            [
                {"pattern_slug": "community_engagement", "confidence": "strong",
                 "notes": "Kids at F1 — CSR + sports activation hybrid, warm-tone documentary style"},
                {"pattern_slug": "brand_csr_pillar", "confidence": "medium",
                 "notes": "AlBaik Academy youth program shown at major event — brand investment in next generation"},
            ],
            "high"),

        # 13 ── DImarStN2qC | 2025-04-18 | photo | 1,639 likes | F1 fan invitation
        obs(13, "DImarStN2qC", "image", "2025-04-18", "friday", "portrait_4x5",
            "event_invitation_poster",
            "warm_natural",
            ["AlBaik red", "white", "black", "race track grey"],
            "indoor", "simple",
            "arabic", "casual", "bold",
            ["المضمار", "زورونا", "فورمولا1"],
            True,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "F1 fan invitation photo — AlBaik invites fans to visit their F1 presence. Friday posting maximises reach for weekend event attendance. Portrait photo format (not reel) for static event announcement. 1,639 likes for a static photo during event week is strong — F1 halo effect. Demonstrates multi-format content strategy: video for product, photo for event invitation.",
            [
                {"pattern_slug": "event_invitation", "confidence": "strong",
                 "notes": "Static photo invitation for live event — Friday pre-weekend posting optimises attendance conversion"},
            ],
            "high"),

        # 14 ── DPEfJCPDRQM | 2025-09-26 | video | 1,731 likes | National Day recap
        obs(14, "DPEfJCPDRQM", "video", "2025-09-26", "friday", "vertical_9x16",
            "occasion_recap_montage",
            "warm_soft",
            ["green", "white", "gold", "AlBaik red"],
            "outdoor", "moderate",
            "arabic", "casual", "warm",
            ["لحظات فخر وفرح", "بحب الوطن", "ذكريات تبقى", "عشناها معاكم"],
            False,
            NO_FLAGS, CLEAN,
            "national_day", "modern", [],
            "National Day 95 recap video — 'ذكريات تبقى' (memories remain) frames the brand as a participant in national pride, not a spectator. 'عشناها معاكم' (we lived them with you) collapses the brand-consumer distance. Post-event recap on Friday (2 days after Sept 23) keeps national day engagement alive. 1,731 likes confirms extended national occasion window.",
            [
                {"pattern_slug": "national_occasion", "confidence": "strong",
                 "notes": "National Day recap with brand-as-participant framing — معاكم collapses brand/audience distance"},
                {"pattern_slug": "post_occasion_content", "confidence": "medium",
                 "notes": "Recap posted 3 days after event — extends occasion engagement window beyond the day itself"},
            ],
            "high"),

        # 15 ── DKr4_5kNOXr | 2025-06-09 | video | 1,575 likes | Hajj pride
        obs(15, "DKr4_5kNOXr", "video", "2025-06-09", "monday", "vertical_9x16",
            "pilgrimage_documentary",
            "warm_golden",
            ["white", "gold", "green", "stone beige"],
            "outdoor", "simple",
            "arabic", "formal", "reverent",
            ["نفخر", "ضيوف بيت الله الحرام", "لحظات الرضا", "جزءًا من"],
            False,
            NO_FLAGS, CLEAN,
            "hajj", "heritage", ["pilgrimage_service", "spiritual_pride"],
            "Hajj pride video — 'نفخر بأن نكون جزءًا من لحظات الرضا' (we are proud to be part of moments of contentment) pairs corporate pride with spiritual satisfaction. Different from DKp11_dNgGs (documentary carousel) — this is a more personal brand testimony. Hajj content performs consistently for AlBaik given their Makkah heritage. 1,575 likes.",
            [
                {"pattern_slug": "brand_values", "confidence": "strong",
                 "notes": "Hajj pride testimony — نفخر + spiritual contentment language, uniquely AlBaik heritage asset"},
                {"pattern_slug": "occasion_pillar", "confidence": "medium",
                 "notes": "Second Hajj post within 2 days — AlBaik sustains occasion coverage over multiple posts"},
            ],
            "high"),

        # 16 ── DM96urhNP7U | 2025-08-05 | carousel | 1,080 likes | AlBaik Academy kids closing
        obs(16, "DM96urhNP7U", "carousel_slide", "2025-08-05", "tuesday", "landscape_3x2",
            "csr_event_documentary",
            "warm_natural",
            ["AlBaik red", "white", "yellow", "blue"],
            "indoor", "moderate",
            "arabic", "casual", "warm",
            ["أبطال_البيت", "اختتمنا بفخر", "أولياء أمورهم الكرام"],
            False,
            NO_FLAGS, CLEAN,
            "brand_campaign", "modern", [],
            "AlBaik Academy summer kids program closing ceremony carousel. 'أبطال_البيت' (champions of the home/AlBaik) branded hashtag for the youth academy. Closing ceremony carousel documents parents + children together — community warmth signal. AlBaik Academy is a structured CSR initiative that generates consistent medium-engagement community content.",
            [
                {"pattern_slug": "community_engagement", "confidence": "strong",
                 "notes": "AlBaik Academy closing ceremony — branded youth CSR program with أبطال_البيت hashtag"},
                {"pattern_slug": "brand_csr_pillar", "confidence": "strong",
                 "notes": "Structured academy program signals long-term youth investment, not one-off activation"},
            ],
            "medium"),

        # 17 ── DImDqScNUfw | 2025-04-18 | video | 900 likes | F1 brand partnership
        obs(17, "DImDqScNUfw", "video", "2025-04-18", "friday", "vertical_9x16",
            "brand_collab_cinematic",
            "dramatic_moody",
            ["AlBaik red", "black", "white", "race track silver"],
            "outdoor", "moderate",
            "arabic", "casual", "bold",
            ["البيك ينطلق", "فورمولا1", "السرعة والحماس", "اسس_وانطلق_بلا_حدود"],
            False,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "F1 brand partnership video without direct product mention — pure brand activation. 'اسس_وانطلق_بلا_حدود' (launch without limits) is a campaign slogan, not a product CTA. Lower engagement (900) vs product-focused F1 post (6,360) confirms product-first strategy even in sports activations. Posted same day as DImarStN2qC (Apr 18 = Friday).",
            [
                {"pattern_slug": "event_sponsorship", "confidence": "medium",
                 "notes": "Pure brand activation without product — significantly lower engagement than product-tied F1 content"},
            ],
            "medium"),

        # 18 ── DNjKwg4NZmS | 2025-08-19 | video | 743 likes | Royal presence at AlBaik event
        obs(18, "DNjKwg4NZmS", "video", "2025-08-19", "tuesday", "vertical_9x16",
            "vip_event_documentary",
            "formal_neutral",
            ["AlBaik red", "white", "gold", "formal navy"],
            "indoor", "simple",
            "arabic", "formal", "respectful",
            ["صاحب السمو الأمير", "سعود بن عبدالله بن جلوي", "حضور وتشريف"],
            False,
            NO_FLAGS, CLEAN,
            "brand_campaign", "blended", [],
            "Royal prince presence at AlBaik Academy event — 743 likes. Formal protocol language ('حضور وتشريف' = royal attendance and honor). Prince Saud bin Abdullah bin Jiluwi is Governor of Eastern Province, connecting AlBaik to highest Saudi authority. Lower engagement reflects institutional content vs consumer content — this post serves brand legitimacy not engagement.",
            [
                {"pattern_slug": "institutional_milestone", "confidence": "strong",
                 "notes": "Royal presence confirms AlBaik's status as Saudi institution — brand legitimacy signal, not engagement play"},
            ],
            "medium"),

        # 19 ── DKhw2IONAh1 | 2025-06-05 | carousel | 734 likes | Eid Al-Adha greeting
        obs(19, "DKhw2IONAh1", "carousel_slide", "2025-06-05", "thursday", "square_1x1",
            "occasion_greeting_card",
            "warm_soft",
            ["deep green", "gold", "white", "cream"],
            "studio", "simple",
            "arabic", "formal", "warm",
            ["عيد أضحى مبارك", "كل عام وأنتم بخير"],
            False,
            NO_FLAGS, CLEAN,
            "eid_al_adha", "heritage", ["eid_celebration"],
            "Eid Al-Adha greeting carousel — 734 likes. Lower engagement vs Ramadan (6,017) likely because Eid Al-Adha is shorter in social attention span. Bilingual hashtag #البيك #ALBAIK signals cross-audience targeting. Square carousel format for greeting cards is standard across Saudi F&B brands. Minimal copy follows heritage-greeting convention.",
            [
                {"pattern_slug": "occasion_greeting", "confidence": "strong",
                 "notes": "Eid Al-Adha greeting — standard Saudi brand convention, lower engagement than Ramadan"},
            ],
            "medium"),

        # 20 ── DI32MrttHCt | 2025-04-25 | video | 690 likes | AlBaik 50th anniversary
        obs(20, "DI32MrttHCt", "video", "2025-04-25", "friday", "vertical_9x16",
            "brand_anniversary_tribute",
            "warm_golden",
            ["AlBaik red", "gold", "white", "deep brown"],
            "studio", "moderate",
            "arabic", "formal", "bold",
            ["50 عاماً", "يواصل انطلاقته", "عالم الابتكار", "البيك"],
            False,
            NO_FLAGS, CLEAN,
            "brand_campaign", "blended", [],
            "AlBaik 50th anniversary video — 690 likes. Surprisingly low for a milestone post, suggesting anniversary content underperforms expectations for this brand. 'يواصل انطلاقته في عالم الابتكار' (continues its journey in the world of innovation) combines heritage (50 years) with future-orientation (innovation). Institutional content vs engaging product content — consistent AlBaik pattern: product > brand story.",
            [
                {"pattern_slug": "brand_milestone", "confidence": "strong",
                 "notes": "50th anniversary — lower than expected engagement; confirms product > brand story for AlBaik"},
            ],
            "medium"),

        # 21 ── DPzCn8PDYDt | 2025-10-14 | video | 662 likes | Saudi national team WC support
        obs(21, "DPzCn8PDYDt", "video", "2025-10-14", "tuesday", "vertical_9x16",
            "patriotic_support",
            "warm_soft",
            ["green", "white", "gold", "AlBaik red"],
            "outdoor", "simple",
            "arabic", "casual", "warm",
            ["بالتوفيق للمنتخب السعودي", "المونديال", "مع_الأخضر_قدام"],
            False,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "Saudi national team World Cup qualifier support — 662 likes. Campaign hashtag #مع_الأخضر_قدام (forward with the Green) is the official national team rally cry. 662 likes is below AlBaik's average — supporting the national team generates moderate engagement for brands when not tied to a product offer. Patriotic content requires product hook to maximise AlBaik performance.",
            [
                {"pattern_slug": "national_support", "confidence": "strong",
                 "notes": "Saudi team WC support with #مع_الأخضر_قدام — patriotic content underperforms without product hook"},
            ],
            "medium"),

        # 22 ── DKfrNLRtvso | 2025-06-04 | video | 608 likes | Hajj pilgrims welcome
        obs(22, "DKfrNLRtvso", "video", "2025-06-04", "wednesday", "vertical_9x16",
            "pilgrimage_welcome",
            "warm_golden",
            ["white", "gold", "green", "stone beige"],
            "outdoor", "simple",
            "arabic", "formal", "warm",
            ["مرحباً بضيوف الرحمن", "حجًا مبرورًا", "سعيًا مشكوراً"],
            False,
            NO_FLAGS, CLEAN,
            "hajj", "heritage", ["pilgrimage_welcome", "spiritual_hospitality"],
            "Hajj welcome video — 'مرحباً بضيوف الرحمن' (welcome to the guests of the Most Merciful). Classical Islamic formula for welcoming pilgrims. Posted before the main Hajj dates. 608 likes lower than post-Hajj content (DKr4_5kNOXr 1,575) — retrospective pride content outperforms advance welcome messages.",
            [
                {"pattern_slug": "occasion_pillar", "confidence": "strong",
                 "notes": "Hajj welcome with Islamic formula — AlBaik's Makkah heritage makes this authentic, not performative"},
            ],
            "medium"),

        # 23 ── DOVh_KnjeWo | 2025-09-08 | carousel | 586 likes | Esports World Cup recap
        obs(23, "DOVh_KnjeWo", "carousel_slide", "2025-09-08", "monday", "landscape_3x2",
            "event_recap_photojournalism",
            "dramatic_moody",
            ["dark charcoal", "neon green", "AlBaik red", "white"],
            "indoor", "moderate",
            "arabic", "casual", "warm",
            ["ختام مشاركتنا", "كأس_العالم_للرياضات_الالكترونية"],
            False,
            NO_FLAGS, CLEAN,
            "sporting_event", "modern", [],
            "Esports World Cup closing recap carousel — 586 likes. Post-event summary following AlBaik's sponsorship. Lower engagement than mid-event content (DMaODC4vbHc 1,989) — closing recap has less urgency than live activation. Documentary carousel style. Confirms: AlBaik's event content follows a pre/during/post arc with decreasing engagement toward the end.",
            [
                {"pattern_slug": "community_recap", "confidence": "medium",
                 "notes": "Post-event recap — lower engagement than live activation; closing content underperforms opening"},
            ],
            "medium"),

        # 24 ── DOBkYCIjZ0G | 2025-08-31 | photo | 494 likes | Delivery app promotion
        obs(24, "DOBkYCIjZ0G", "image", "2025-08-31", "sunday", "square_1x1",
            "app_promotion_static",
            "warm_soft",
            ["AlBaik red", "white", "home icon cream", "light grey"],
            "studio", "simple",
            "arabic", "casual", "friendly",
            ["من بيكك لبيتك", "حمل التطبيق", "الرابط موجود في البايو"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "'من بيكك لبيتك' (from your AlBaik to your home) — brand delivery app campaign tagline with wordplay on 'بيك' (AlBaik) and 'بيت' (home). 494 likes is the lowest in this batch — app download CTAs perform poorly vs product content for AlBaik. Square static photo for app promo is the weakest format/content combination. Pattern: AlBaik's delivery channel underexploited relative to dine-in brand strength.",
            [
                {"pattern_slug": "digital_service_promo", "confidence": "strong",
                 "notes": "من بيكك لبيتك delivery CTA — wordplay on brand name; 494 likes = weakest in batch, app promos underperform"},
            ],
            "medium"),
    ]

    written = 0
    skipped = 0
    for ob in observations:
        if ob is None:
            skipped += 1
            continue
        ulid = ob["observation_ulid"]
        path = OUT / f"{ulid}.json"
        path.write_text(json.dumps(ob, ensure_ascii=False, indent=2))
        written += 1
        print(f"  ✓ {ulid}  {ob['content_ref']['capture_date']}  {ob['content_ref']['content_type']:<14}  {ob['quality_assessment']['engagement_potential']}")

    print(f"\n  Written: {written}  Skipped (already exist): {skipped}")
    print(f"  AlBaik obs total (after): {len(list(OUT.parent.rglob('*.json'))) + written}")


if __name__ == "__main__":
    main()
