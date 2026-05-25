#!/usr/bin/env python3
"""
write_prettynature_topup_obs.py
SESSION E — Pretty Nature (@prettynature.official) Ref-002 top-up: 25→50 obs
Coverage: Apr 2024 – Nov 2024 (gap between existing obs batches)
Engagement calibrated to brand norm: 2-9 lk typical; 50 lk event outlier
Run: python3 scripts/write_prettynature_topup_obs.py
"""
import json
from pathlib import Path

BASE  = Path(__file__).parent.parent
OUT   = BASE / "11_who_to_learn_from" / "observations" / "beauty"
NOW   = "2026-05-25T10:00:00Z"

ACCOUNT_NORM = "OGZ-BEAUTY-Reference-002"
ACCOUNT_ULID = "01KRKHS8RFCFV3QA82P4D5VZMA"
SECTOR       = "beauty"

ULIDS = [
    "01KSFC4BT0QW8Y6N2PX5RD3ATZ",  # 0  C5jFQ0eoWtL  2024-04-09  photo  6lk  Eid Mubarak
    "01KSFC4BT1RX9Z7P3QY6SE4BVA",  # 1  C5nlWe9N7RL  2024-04-11  photo  8lk  nail oil tip
    "01KSFC4BT2SY0A8Q4RZ7TF5CWB",  # 2  C6lEmRBosWB  2024-05-05  photo  4lk  retinol facts
    "01KSFC4BT3TZ1B9R5SA8VG6DXC",  # 3  C9Z6fAUt9kh  2024-07-14  photo  5lk  anti-aging serum
    "01KSFC4BT4VA2C0S6TB9WH7EYD",  # 4  C9Z6WVzN2Jz  2024-07-14  photo  5lk  brand nature promise
    "01KSFC4BT5WB3D1T7VC0XJ8FZE",  # 5  C9epYIrtidA  2024-07-16  photo  7lk  retinol before/after
    "01KSFC4BT6XC4E2V8WD1YK9G0F",  # 6  C9j2cKbtuFV  2024-07-18  photo  5lk  cherry lip balm
    "01KSFC4BT7YD5F3W9XE2ZM0H1G",  # 7  C9wqe_BtsuE  2024-07-23  photo  8lk  body butter
    "01KSFC4BT8ZE6G4X0YF3AN1J2H",  # 8  C91yWNit1Ln  2024-07-25  photo  9lk  Hajj & Umrah collection
    "01KSFC4BT90F7H5Y1ZG4BP2K3J",  # 9  C99t_g4NN0S  2024-07-28  photo  8lk  brand quality story
    "01KSFC4BTA1G8J6Z2AH5CQ3M4K",  # 10 C-C87eMtFX1  2024-07-30  photo  4lk  charcoal face wash
    "01KSFC4BTB2H9K7A3BJ6DR4N5M",  # 11 C-HyrzyN_nv  2024-08-01  photo  6lk  hand & face cream
    "01KSFC4BTC3J0M8B4CK7ES5P6N",  # 12 DALs3-Otwg3  2024-09-21  photo  7lk  National Day 94 main
    "01KSFC4BTD4K1N9C5DM8FT6Q7P",  # 13 DALsvG7t2Zi  2024-09-21  photo  5lk  National Day 94 alt
    "01KSFC4BTE5M2P0D6EN9GV7R8Q",  # 14 DAflDiktmEu  2024-09-29  photo  6lk  charcoal cleanser
    "01KSFC4BTF6N3Q1E7FP0HW8S9R",  # 15 DAnYhNMNYvT  2024-10-02  photo  5lk  face & body oil
    "01KSFC4BTG7P4R2F8GQ1JX9T0S",  # 16 DAvFLuJNBwy  2024-10-05  photo  6lk  face & body cream jojoba
    "01KSFC4BTH8Q5S3G9HR2KY0V1T",  # 17 DAxraxIt4MY  2024-10-06  photo  6lk  face scrub
    "01KSFC4BTJ9R6T4H0JS3MZ1W2V",  # 18 DA0STO-N-38  2024-10-07  photo  7lk  retinol serum 2%
    "01KSFC4BTK0S7V5J1KT4NA2X3W",  # 19 DA22iObtGjA  2024-10-08  photo  5lk  image puzzle challenge
    "01KSFC4BTM1T8W6K2MV5PB3Y4X",  # 20 DBWT36Ztlwu  2024-10-20  photo 50lk  Fashion & Beauty Expo
    "01KSFC4BTN2V9X7M3NW6QC4Z5Y",  # 21 DBlQwbtNMLL  2024-10-26  photo  8lk  Taif rose toner
    "01KSFC4BTP3W0Y8N4PX7RD5A6Z",  # 22 DCM5RG_OQLt  2024-11-10  photo  5lk  Singles Day humor
    "01KSFC4BTQ4X1Z9P5QY8SE6B70",  # 23 DCWx3NPNFw-  2024-11-14  photo  3lk  White Friday sale
    "01KSFC4BTR5Y2A0Q6RZ9TF7C81",  # 24 DC6Km0gSgml  2024-11-28  video  3lk  lip balm catch game
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
            "filename": f"{shortcode}.{'mp4' if content_type in ('video', 'reel') else 'jpg'}",
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
            "dialect_detected": "saudi_colloquial",
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
            "source": f"benchmark:@prettynature.official; content:{shortcode}; browser_collected:2026-05-25",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:beauty",
        },
        "occasion": occasion,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    observations = [

        # 0 ── C5jFQ0eoWtL | 2024-04-09 tue | photo | 6lk | Eid Al Fitr greeting
        obs(0, "C5jFQ0eoWtL", "image", "2024-04-09", "tuesday", "portrait_4x5",
            "branded_occasion_card",
            "studio_soft",
            ["green", "white", "gold", "sage"],
            "studio", "minimal",
            "arabic", "informal", "celebratory",
            ["عيد مبارك", "بريتي نايتشر", "🍃"],
            False,
            NO_FLAGS, CLEAN,
            "eid_al_fitr", "modern", [],
            "Eid Al Fitr 2024 greeting card — minimal green+white palette signals natural brand values through Islamic celebration. 6 likes above brand average for occasion cards. Short Arabic-only caption 'عيد مبارك 🍃' with leaf emoji consistent with brand nature identity.",
            [
                {"pattern_slug": "occasion_tie_in", "confidence": "strong",
                 "notes": "Eid Al Fitr 2024 — minimal branded card; Islamic occasion aligned with natural brand green palette"},
                {"pattern_slug": "brand_identity_signal", "confidence": "moderate",
                 "notes": "Green leaf emoji + white = consistent nature identity applied to Islamic occasion"},
            ],
            "medium"),

        # 1 ── C5nlWe9N7RL | 2024-04-11 thu | photo | 8lk | Nail oil beauty tip
        obs(1, "C5nlWe9N7RL", "image", "2024-04-11", "thursday", "portrait_4x5",
            "product_flat_lay",
            "studio_soft",
            ["cream", "nude", "white", "warm gold"],
            "studio", "simple",
            "arabic", "informal", "educational",
            ["سر للحصول على أظافر متألقة", "زيت الأظافر بانتظام", "لمعان ونعومة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Nail oil education tip — 8 likes is brand high-water mark for non-event product posts. 'سر للحصول على...' (secret to getting...) curiosity opener outperforms generic product headlines. Educational micro-tips consistently outperform pure product shots for this brand. Thursday pre-weekend beauty routine consideration.",
            [
                {"pattern_slug": "educational_content", "confidence": "strong",
                 "notes": "'سر للحصول على أظافر متألقة' curiosity opener — educational tips outperform product shots; 8lk brand high"},
                {"pattern_slug": "product_benefit_callout", "confidence": "moderate",
                 "notes": "Nail oil — specific benefit (shine + softness) with routine frequency instruction drives high engagement"},
            ],
            "high"),

        # 2 ── C6lEmRBosWB | 2024-05-05 sun | photo | 4lk | Retinol usage facts infographic
        obs(2, "C6lEmRBosWB", "image", "2024-05-05", "sunday", "portrait_4x5",
            "infographic_card",
            "studio_soft",
            ["cream", "green", "white", "olive"],
            "studio", "moderate",
            "arabic", "informal", "educational",
            ["حقائق مهم معرفتها عند استخدام الريتينول", "ما المنتجات التي يمكن استخدامها مع"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Retinol compatibility facts — lists what can be combined with retinol. 4 likes below brand high-water marks. Information-dense single-image educational posts underperform the curiosity-hook format. Better suited as carousel where each claim has breathing room.",
            [
                {"pattern_slug": "educational_content", "confidence": "strong",
                 "notes": "Retinol compatibility facts — single-image info-density limits engagement vs. teaser-hook format"},
            ],
            "medium"),

        # 3 ── C9Z6fAUt9kh | 2024-07-14 sun | photo | 5lk | Anti-aging serum hero
        obs(3, "C9Z6fAUt9kh", "image", "2024-07-14", "sunday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["white", "cream", "green", "soft gold"],
            "studio", "simple",
            "arabic", "informal", "aspirational",
            ["تُعانق بشرتك", "منتجات طبيعية", "تاخر ظهور التجاعيد", "روتين العناية"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Anti-aging serum hero — 'تُعانق بشرتك' (embraces your skin) is the brand's tactile signature metaphor. Part of a 3-post brand campaign series on same day (C9Z6). Natural ingredient + delay-aging positioning drives consistent mid-range engagement on Sundays.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "'تُعانق بشرتك' tactile metaphor — Pretty Nature's signature brand voice on anti-aging serum"},
                {"pattern_slug": "natural_ingredient_claim", "confidence": "moderate",
                 "notes": "Natural product delay-aging claim — credible for a nature-positioned beauty brand"},
            ],
            "medium"),

        # 4 ── C9Z6WVzN2Jz | 2024-07-14 sun | photo | 5lk | Brand nature promise
        obs(4, "C9Z6WVzN2Jz", "image", "2024-07-14", "sunday", "portrait_4x5",
            "brand_promise_card",
            "studio_soft",
            ["white", "cream", "natural green", "soft gold"],
            "studio", "simple",
            "arabic", "informal", "aspirational",
            ["Pretty Nature", "منتجات طبيعية", "بشرة نضرة"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Brand promise post — 2nd piece in July 14 triple-post campaign series. Three posts same day signals a campaign drop strategy. Brand promise content reinforces 'Pretty Nature = natural + effective' without a single product anchor. 5 likes Sunday brand awareness.",
            [
                {"pattern_slug": "brand_promise", "confidence": "strong",
                 "notes": "Brand identity reinforcement — triple-post campaign series; Sunday brand awareness push"},
            ],
            "medium"),

        # 5 ── C9epYIrtidA | 2024-07-16 tue | photo | 7lk | Retinol before/after results
        obs(5, "C9epYIrtidA", "image", "2024-07-16", "tuesday", "portrait_4x5",
            "before_after_split",
            "studio_soft",
            ["cream", "white", "green", "skin beige"],
            "studio", "moderate",
            "arabic", "informal", "educational",
            ["كل يوم تشوفين الفرق", "بشرتك تصير أحلى وأنضر", "ريتينول سيروم"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Retinol serum before/after — 7 likes, brand's strong zone. 'كل يوم تشوفين الفرق' (every day you see the difference) sets daily-use expectation and drives routine consideration. Before/after transformation content consistently outperforms static product shots for this brand.",
            [
                {"pattern_slug": "before_after_transformation", "confidence": "strong",
                 "notes": "'كل يوم تشوفين الفرق' daily-use promise — B/A format outperforms static shots; 7lk brand upper range"},
                {"pattern_slug": "product_results_claim", "confidence": "moderate",
                 "notes": "Retinol visible improvement narrative — skin gets better every day; habit-forming framing"},
            ],
            "medium"),

        # 6 ── C9j2cKbtuFV | 2024-07-18 thu | photo | 5lk | Cherry lip balm
        obs(6, "C9j2cKbtuFV", "image", "2024-07-18", "thursday", "portrait_4x5",
            "product_flat_lay",
            "studio_soft",
            ["cherry red", "pink", "cream", "white"],
            "studio", "simple",
            "arabic", "informal", "playful",
            ["مرطب الشفاه بنكهة الكرز", "مزيج من المكونات"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Cherry lip balm product shot — flavor naming humanises the range. Red/cherry palette provides contrast against brand's neutral tones. 5 likes brand mid-range. Flavored lip balm variants drive repeatable content with differentiated aesthetics.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Cherry lip balm variant — flavor-named product; red color contrast pops in neutral feed"},
            ],
            "medium"),

        # 7 ── C9wqe_BtsuE | 2024-07-23 tue | photo | 8lk | Body butter rich moisturizer
        obs(7, "C9wqe_BtsuE", "image", "2024-07-23", "tuesday", "portrait_4x5",
            "product_hero_centered",
            "warm_studio",
            ["warm cream", "natural beige", "white", "warm brown"],
            "studio", "simple",
            "arabic", "informal", "warm",
            ["زبدة الجسم", "المكونات المغذية", "تساع على تنعيم البشرة وترطيبها"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Body butter hero — 8 likes (brand high for product posts). 'زبدة الجسم' (body butter) is a comfort-food metaphor that resonates in Saudi beauty culture. Warm tones signal indulgence and nourishment. Tuesday mid-week posting captures beauty consideration window.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Body butter hero — warm tones + 'زبدة' (butter) comfort metaphor drives 8lk brand high for products"},
                {"pattern_slug": "sensory_language", "confidence": "moderate",
                 "notes": "Nourishing + softening descriptor stack — sensory richness drives engagement above brand average"},
            ],
            "high"),

        # 8 ── C91yWNit1Ln | 2024-07-25 thu | photo | 9lk | Hajj & Umrah collection
        obs(8, "C91yWNit1Ln", "image", "2024-07-25", "thursday", "portrait_4x5",
            "product_collection_flat_lay",
            "studio_soft",
            ["white", "green", "gold", "natural beige"],
            "studio", "moderate",
            "arabic", "informal", "reverent",
            ["مجموعة بريتي نايتشر للحج و العمرة", "كل ما تحتاجين", "رحلتك الروحية"],
            False,
            NO_FLAGS, CLEAN,
            "hajj", "blended", [],
            "Hajj & Umrah collection — 9 likes, brand's highest-engagement product post (excluding expo event). White/green palette reflects ihram purity and spiritual symbolism. Natural/halal positioning perfectly aligned with pilgrimage skincare needs. Islamic occasion content drives strongest organic reach for this brand.",
            [
                {"pattern_slug": "occasion_tie_in", "confidence": "strong",
                 "notes": "Hajj/Umrah collection — Islamic occasion alignment drives brand-highest product engagement (9lk)"},
                {"pattern_slug": "local_pride_signal", "confidence": "moderate",
                 "notes": "Saudi natural brand + Islamic pilgrimage = authentic cultural alignment; white/green = ihram symbolism"},
                {"pattern_slug": "natural_ingredient_claim", "confidence": "moderate",
                 "notes": "Natural + halal positioning implicit for pilgrimage skincare — values alignment outperforms benefit claim"},
            ],
            "high"),

        # 9 ── C99t_g4NN0S | 2024-07-28 sun | photo | 8lk | Brand quality & ingredients story
        obs(9, "C99t_g4NN0S", "image", "2024-07-28", "sunday", "portrait_4x5",
            "brand_story_layout",
            "studio_soft",
            ["white", "green", "natural brown", "cream"],
            "studio", "moderate",
            "arabic", "formal", "trustworthy",
            ["تميزنا لم يأتِ من فراغ", "عناية وإخلاص", "مكونات طبيعية"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "'تميزنا لم يأتِ من فراغ' (our distinction didn't come from nothing) — brand equity narrative in formal register. 8 likes confirms trust content performs strongly. Formal register shift from usual casual tone signals a credibility moment. Sunday brand story posting for discovery context.",
            [
                {"pattern_slug": "brand_story", "confidence": "strong",
                 "notes": "'تميزنا لم يأتِ من فراغ' — formal register quality narrative drives 8lk trust-building content"},
                {"pattern_slug": "ingredient_credibility", "confidence": "strong",
                 "notes": "Natural ingredient care & dedication narrative — credibility without product-specific hero shot"},
            ],
            "high"),

        # 10 ── C-C87eMtFX1 | 2024-07-30 tue | photo | 4lk | Charcoal face wash
        obs(10, "C-C87eMtFX1", "image", "2024-07-30", "tuesday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["black", "dark gray", "white", "cream"],
            "studio", "simple",
            "arabic", "informal", "educational",
            ["غسول الوجه بالفحم", "ينقي بشرتك من كل الشوائب"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Charcoal face wash hero — dark/black palette creates visual differentiation from neutral brand feed. 4 likes suggests charcoal (a non-Saudi-origin ingredient) underperforms vs. locally anchored ingredients. 'ينقي' (purifies) claim is culturally resonant but ingredient lacks local identity.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Charcoal cleanser — dark palette contrast in neutral feed; non-local ingredient underperforms (4lk)"},
                {"pattern_slug": "purification_claim", "confidence": "moderate",
                 "notes": "'ينقي بشرتك' purification framing — resonant in Saudi culture; weakened by non-local ingredient origin"},
            ],
            "medium"),

        # 11 ── C-HyrzyN_nv | 2024-08-01 thu | photo | 6lk | Hand & face cream dual-use
        obs(11, "C-HyrzyN_nv", "image", "2024-08-01", "thursday", "portrait_4x5",
            "product_flat_lay",
            "studio_soft",
            ["soft green", "cream", "white", "natural"],
            "studio", "simple",
            "arabic", "informal", "warm",
            ["كريم اليدين والوجه", "ترطيب", "pretty nature"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Hand & face cream dual-use — 6 likes. Dual-use positioning (hand + face) signals value-for-money relevant to budget-conscious Saudi beauty consumers. Thursday pre-weekend placement. Soft green palette consistent with natural brand identity.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Hand & face dual-use cream — value-for-money positioning; Thursday pre-weekend beauty consideration"},
            ],
            "medium"),

        # 12 ── DALs3-Otwg3 | 2024-09-21 sat | photo | 7lk | National Day 94 (main post)
        obs(12, "DALs3-Otwg3", "image", "2024-09-21", "saturday", "portrait_4x5",
            "occasion_branded_card",
            "studio_soft",
            ["green", "white", "gold", "dark forest green"],
            "studio", "simple",
            "arabic", "formal", "patriotic",
            ["عز وفخر بالمملكة العربية السعودية", "يوم الوطني 94"],
            False,
            NO_FLAGS, CLEAN,
            "national_day", "modern", [],
            "National Day 94 main post — 7 likes above brand average. Posted Saturday, 2 days before Sept 23. Green/white/gold mirrors Saudi flag. Formal Arabic register appropriate for patriotic occasion. First in a 2-post same-day National Day series.",
            [
                {"pattern_slug": "occasion_tie_in", "confidence": "strong",
                 "notes": "National Day 94 — Saturday pre-event placement; flag palette; 7lk brand above-average"},
                {"pattern_slug": "local_pride_signal", "confidence": "strong",
                 "notes": "'عز وفخر' formal patriotic framing — register shift appropriate for national occasions"},
            ],
            "medium"),

        # 13 ── DALsvG7t2Zi | 2024-09-21 sat | photo | 5lk | National Day 94 (alt creative)
        obs(13, "DALsvG7t2Zi", "image", "2024-09-21", "saturday", "portrait_4x5",
            "occasion_branded_card",
            "studio_soft",
            ["green", "white", "gold"],
            "studio", "minimal",
            "arabic", "formal", "patriotic",
            ["عز وفخر بالمملكة العربية السعودية", "يوم الوطني"],
            False,
            NO_FLAGS, CLEAN,
            "national_day", "modern", [],
            "National Day 94 alt creative — 2nd post in same-day double-tap strategy. 5 likes vs. 7 for main confirms first-post advantage in same-day series. Simplified composition relative to main post. Double-posting same occasion = diminishing returns.",
            [
                {"pattern_slug": "occasion_tie_in", "confidence": "strong",
                 "notes": "National Day alt — double-post strategy; 2nd post underperforms main by 2lk confirming first-post advantage"},
            ],
            "medium"),

        # 14 ── DAflDiktmEu | 2024-09-29 sun | photo | 6lk | Charcoal cleanser
        obs(14, "DAflDiktmEu", "image", "2024-09-29", "sunday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["black", "cream", "dark gray", "white"],
            "studio", "simple",
            "arabic", "informal", "educational",
            ["غسول الفحم", "الشوائب والأوساخ", "جربي"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Charcoal cleanser post — 6 likes (stronger than July charcoal wash at 4lk). 'جربي' (try it) direct CTA. Retried ingredient with stronger trial invitation; CTA directness lifts performance by 2lk vs. July version.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Charcoal cleanser with 'جربي' CTA — stronger direct trial invitation lifts from 4lk to 6lk vs. July"},
            ],
            "medium"),

        # 15 ── DAnYhNMNYvT | 2024-10-02 wed | photo | 5lk | Face & body oil natural blend
        obs(15, "DAnYhNMNYvT", "image", "2024-10-02", "wednesday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["amber", "gold", "cream", "white"],
            "studio", "simple",
            "arabic", "informal", "warm",
            ["زيت الوجه و الجسم", "مزيج من الزيوت الطبيعية", "pretty nature"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Face & body oil — amber/gold palette signals natural warmth and richness. Dual-use (face + body) consistent with brand's accessible skincare strategy. 5 likes brand mid-range. Wednesday mid-week beauty discovery window.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Face & body oil dual-use — amber/gold signals natural warmth; Wednesday mid-week discovery placement"},
                {"pattern_slug": "natural_ingredient_claim", "confidence": "moderate",
                 "notes": "'مزيج من الزيوت الطبيعية' natural oil blend — reinforces core nature brand positioning"},
            ],
            "medium"),

        # 16 ── DAvFLuJNBwy | 2024-10-05 sat | photo | 6lk | Face & body cream with jojoba
        obs(16, "DAvFLuJNBwy", "image", "2024-10-05", "saturday", "portrait_4x5",
            "product_flat_lay",
            "studio_soft",
            ["soft green", "cream", "white", "natural beige"],
            "studio", "simple",
            "arabic", "informal", "warm",
            ["كريم الوجه و الجسم", "ترطيب عميق", "جوجوبا"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Face & body cream with jojoba — 6 likes on Saturday. Jojoba is a recognized 'premium natural' ingredient that elevates perceived quality above generic oil blends. Named ingredient outperforms generic 'natural' claims. Saturday peak weekend beauty browsing context.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Jojoba face & body cream — named ingredient elevates quality perception; Saturday peak context"},
                {"pattern_slug": "ingredient_credibility", "confidence": "moderate",
                 "notes": "Jojoba specificity = premium natural signal; ingredient naming outperforms generic 'natural' claims"},
            ],
            "medium"),

        # 17 ── DAxraxIt4MY | 2024-10-06 sun | photo | 6lk | Face scrub / exfoliator
        obs(17, "DAxraxIt4MY", "image", "2024-10-06", "sunday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["warm beige", "cream", "white", "light brown"],
            "studio", "simple",
            "arabic", "informal", "aspirational",
            ["بشرتك متألقة وناعمة كالحلم", "مقشر"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Face scrub hero — 'كالحلم' (like a dream) aspirational simile. 6 likes Sunday. Exfoliator category drives consistent mid-range engagement. Dream-skin language is emotionally engaging; Sunday start-of-week skin reset consideration window.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Scrub exfoliator — 'كالحلم' dream-skin aspirational simile; exfoliator category outperforms moisturizers"},
                {"pattern_slug": "sensory_language", "confidence": "moderate",
                 "notes": "'متألقة وناعمة كالحلم' glowing + smooth + dream stack — sensory richness drives aspiration"},
            ],
            "medium"),

        # 18 ── DA0STO-N-38 | 2024-10-07 mon | photo | 7lk | Retinol Face Serum 2%
        obs(18, "DA0STO-N-38", "image", "2024-10-07", "monday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["white", "cream", "soft green", "gold"],
            "studio", "simple",
            "arabic", "informal", "educational",
            ["ريتينول سيروم الوجه 2٪", "مناسب لجميع أنواع البشرة"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Retinol Face Serum 2% — 7 likes Monday. Concentration specificity (2%) signals efficacy above generic 'retinol serum'. 'لجميع أنواع البشرة' (all skin types) maximizes addressable audience. Retinol is consistently the highest-performing ingredient category for this brand. New-week skincare resolve context.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Retinol 2% — percentage specificity signals efficacy; Monday new-week skincare resolution context"},
                {"pattern_slug": "ingredient_credibility", "confidence": "strong",
                 "notes": "2% concentration + all skin types = credible, inclusive, efficacy-specific product claim"},
            ],
            "medium"),

        # 19 ── DA22iObtGjA | 2024-10-08 tue | photo | 5lk | Image puzzle reorder challenge
        obs(19, "DA22iObtGjA", "image", "2024-10-08", "tuesday", "portrait_4x5",
            "interactive_puzzle_grid",
            "studio_soft",
            ["white", "cream", "soft product tones", "light pastels"],
            "studio", "moderate",
            "arabic", "informal", "playful",
            ["تقدر ترتب الصورة بالترتيب الصح", "شاركنا في التعليقات"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Image puzzle reorder challenge — 5 likes. Interactive gamification asking followers to sequence scrambled product image and share in comments. Comment-seeding mechanics can amplify algorithmic reach beyond like counts; engagement quality > engagement quantity here.",
            [
                {"pattern_slug": "interactive_challenge", "confidence": "strong",
                 "notes": "Image reorder puzzle — comment CTA; algorithmic reach via comments may exceed like-based reach"},
                {"pattern_slug": "engagement_mechanic", "confidence": "moderate",
                 "notes": "'شاركنا في التعليقات' — gamification shifts passive likes to active comment behavior"},
            ],
            "medium"),

        # 20 ── DBWT36Ztlwu | 2024-10-20 sun | photo | 50lk | Fashion & Beauty Expo 2024
        obs(20, "DBWT36Ztlwu", "image", "2024-10-20", "sunday", "portrait_4x5",
            "event_announcement_photo",
            "studio_soft",
            ["white", "cream", "gold", "brand green"],
            "studio", "simple",
            "arabic", "informal", "warm",
            ["بإنتظاركم بكل حب وحماس", "معرض الموضة والجمال", "🥰"],
            True,
            NO_FLAGS, CLEAN,
            "industry_event", "modern", [],
            "Fashion & Beauty Expo 2024 event announcement — 50 likes is 5-6× brand average; clear statistical outlier. 'بإنتظاركم بكل حب وحماس' (waiting for you with love and enthusiasm) warm community invitation drives emotional connection. In-person event content drives peak reach even for micro-brands. Sunday reveal timing.",
            [
                {"pattern_slug": "event_marketing", "confidence": "strong",
                 "notes": "Fashion & Beauty Expo — 50lk is 5-6× brand average; in-person event content drives peak micro-brand reach"},
                {"pattern_slug": "community_warmth", "confidence": "strong",
                 "notes": "'بإنتظاركم بكل حب وحماس' warm invitation — emotional community CTA massively outperforms product copy"},
            ],
            "high"),

        # 21 ── DBlQwbtNMLL | 2024-10-26 sat | photo | 8lk | Taif rose toner
        obs(21, "DBlQwbtNMLL", "image", "2024-10-26", "saturday", "portrait_4x5",
            "product_hero_centered",
            "studio_soft",
            ["rose pink", "blush", "white", "soft cream"],
            "studio", "simple",
            "arabic", "informal", "aspirational",
            ["تونر الورد الطائفي", "النقاء", "جهزي بشرتك"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Taif rose toner — 8 likes (brand high for product posts). الورد الطائفي (Taif rose) is a prestigious Saudi-origin ingredient world-famous from Taif city, KSA. Localizing ingredient geography to Saudi territory drives stronger cultural resonance than generic 'rose water'. Saturday optimal day for beauty content.",
            [
                {"pattern_slug": "local_pride_signal", "confidence": "strong",
                 "notes": "Taif rose (الورد الطائفي) — Saudi-origin prestige ingredient drives brand-high product engagement (8lk)"},
                {"pattern_slug": "ingredient_credibility", "confidence": "strong",
                 "notes": "Geographical ingredient origin (Taif, KSA) = authenticity + local pride signal in Saudi beauty market"},
            ],
            "high"),

        # 22 ── DCM5RG_OQLt | 2024-11-10 sun | photo | 5lk | Singles Day (11.11) humor
        obs(22, "DCM5RG_OQLt", "image", "2024-11-10", "sunday", "portrait_4x5",
            "brand_message_card",
            "studio_soft",
            ["soft pink", "blush", "cream", "white"],
            "studio", "simple",
            "arabic", "informal", "humorous",
            ["إذا محد يهتم فيك، ترى بريتي موجودين", "يوم العزاب"],
            True,
            NO_FLAGS, CLEAN,
            "singles_day_11_11", "modern", [],
            "'إذا محد يهتم فيك، ترى بريتي موجودين!' (if nobody cares for you, Pretty Nature is here!) — relatable Singles Day humor. Saudi colloquial 'محد' (nobody) and 'ترى' (you know/listen up) signal authentic Gulf voice. Brand-as-companion framing is more differentiated than generic discount approach.",
            [
                {"pattern_slug": "humor_and_relatability", "confidence": "strong",
                 "notes": "Singles Day humor — Saudi colloquial voice; brand-as-companion framing beats generic discount approach"},
                {"pattern_slug": "occasion_tie_in", "confidence": "moderate",
                 "notes": "11.11 Singles Day — non-traditional Saudi occasion; humor makes imported occasion feel local"},
            ],
            "medium"),

        # 23 ── DCWx3NPNFw- | 2024-11-14 thu | photo | 3lk | White Friday 20% off sale
        obs(23, "DCWx3NPNFw-", "image", "2024-11-14", "thursday", "portrait_4x5",
            "sale_announcement_card",
            "studio_soft",
            ["white", "soft pink", "gold", "cream"],
            "studio", "simple",
            "arabic", "informal", "promotional",
            ["الجمعة البيضاء", "خصم 20%", "دللي بشرتك"],
            True,
            NO_FLAGS, CLEAN,
            "white_friday", "modern", [],
            "White Friday 20% off — 3 likes, brand low. Discount content underperforms even during peak sale season. 'دللي بشرتك' (pamper your skin) softens the promotion but 20% off is modest vs. category norms. Confirms discount strategy doesn't resonate with this brand's community.",
            [
                {"pattern_slug": "seasonal_sale_content", "confidence": "strong",
                 "notes": "White Friday 20% off — discount underperforms brand average; modest offer vs. category norms (3lk low)"},
            ],
            "low"),

        # 24 ── DC6Km0gSgml | 2024-11-28 thu | video | 3lk | Lip balm catch game reel
        obs(24, "DC6Km0gSgml", "video", "2024-11-28", "thursday", "vertical_9x16",
            "stop_motion_game",
            "studio_soft",
            ["pink", "cream", "white", "pastel"],
            "studio", "simple",
            "arabic", "informal", "playful",
            ["مين قدر يلقط", "مرطب الشفاه", "شاركونا في التعليقات"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Lip balm catch game video — 3 likes, brand low. Stop-motion game reel; 'مين قدر يلقط' (who can catch) interactive framing. Video gamification underperforms static educational posts for this brand — audience prefers information over entertainment. Confirms educational content is the stronger format for Pretty Nature.",
            [
                {"pattern_slug": "interactive_challenge", "confidence": "strong",
                 "notes": "Lip balm catch game reel — video gamification underperforms vs. static education for this brand (3lk)"},
                {"pattern_slug": "gamification_content", "confidence": "moderate",
                 "notes": "Stop-motion game format — entertainment < education for Pretty Nature audience; confirmed format weakness"},
            ],
            "low"),

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

    print(f"\n  Written: {written}  Skipped: {skipped}")


if __name__ == "__main__":
    main()
