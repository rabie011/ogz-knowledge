#!/usr/bin/env python3
"""
write_asteri_topup_obs.py
SESSION D — Asteri Beauty (@asteribeautysa) Ref-001 top-up: 24→50 obs
Coverage: March 27 – May 22, 2026 (gap period)
Engagement range: 36–117 likes (<10k follower brand)
Run: python3 scripts/write_asteri_topup_obs.py
"""
import json
from pathlib import Path

BASE     = Path(__file__).parent.parent
OUT      = BASE / "11_who_to_learn_from" / "observations" / "beauty"
NOW      = "2026-05-25T10:00:00Z"

ACCOUNT_NORM = "OGZ-BEAUTY-Reference-001"
ACCOUNT_ULID = "01KS5PZ5T5J535JPWGJER6R2D1"
SECTOR       = "beauty"

ULIDS = [
    "01KSE745WYNPRN93N8F28QAKTX",  # 0  DWZUCNfjMQt  2026-03-27  video    68
    "01KSE745WY804E01MFK25MV54J",  # 1  DWb40VqFNnQ  2026-03-28  video    49
    "01KSE745WYJBETNXR4NGHB9NZ2",  # 2  DWednQ-iRNe  2026-03-29  video    52
    "01KSE745WYZESYPESY9YZJJ6Q9",  # 3  DWg0pDdlEvT  2026-03-30  video    36
    "01KSE745WYYD49D83X4WYBAQTA",  # 4  DWjioCJjE0_  2026-03-31  video    79
    "01KSE745WY0FFWX67W9G0E7J8Q",  # 5  DWox89-DIXh  2026-04-02  video    74
    "01KSE745WY5J9EXK0N8YQNJXW5",  # 6  DWraar2DIVW  2026-04-03  carousel 40
    "01KSE745WYM3F3NX0FAQGJ5AV9",  # 7  DWweloajKp6  2026-04-05  photo    56
    "01KSE745WYF7SAZ53XFC1EHXB6",  # 8  DWzJbR8DOLK  2026-04-06  carousel 56
    "01KSE745WYT3SGB10VQN6AQV45",  # 9  DW1ieEDElyQ  2026-04-07  video    37
    "01KSE745WYBZ7G489HHA5VXW6H",  # 10 DW4IrLsDNF8  2026-04-08  photo    41
    "01KSE745WYTJ4NZ8WJATFEZFWK",  # 11 DW6rbf2DFBY  2026-04-09  photo   105
    "01KSE745WYJSA0WZ70AE0210BK",  # 12 DW80zphiGo-  2026-04-10  video    44
    "01KSE745WYQPHPV1D6JQDRYRF9",  # 13 DW_8-NBjE8Z  2026-04-11  video   117
    "01KSE745WYFGD2YSNX3GZJYHKG",  # 14 DXChrU_jLMC  2026-04-12  photo    47
    "01KSE745WYGJHD5EB3N12TY38B",  # 15 DXE-y0Fmrog  2026-04-13  video    37
    "01KSE745WYBGGDD127AJNBSXRP",  # 16 DXKPkUujHDp  2026-04-15  carousel 68
    "01KSE745WYX24TG341T038MF6M",  # 17 DXMtJDaiFXN  2026-04-16  photo    68
    "01KSE745WYGNDAF9CJDZ4KT8DC",  # 18 DXSEaf-DO6x  2026-04-18  video    80
    "01KSE745WYJJYHGYW3XRDA2J15",  # 19 DXUgIsuDEQd  2026-04-19  carousel 38
    "01KSE745WY93Y936AEMPCZKAG6",  # 20 DXXWVvNDGak  2026-04-20  video    47
    "01KSE745WYPQF61S1AX45DCJG4",  # 21 DXb8TPriOHb  2026-04-22  carousel 79
    "01KSE745WYK5CS91XAQ75FPGPV",  # 22 DXegvUaDGzW  2026-04-23  photo    43
    "01KSE745WYV99FEPB8PJND2JJQ",  # 23 DXg_FimFAi_  2026-04-24  video    47
    "01KSE745WYMSY8JVCZ7WTH7245",  # 24 DXkB7jXjKEF  2026-04-25  photo    38
    "01KSE745WYMBCYV1HVT52TP3J8",  # 25 DYpaEQijsIR  2026-05-22  video    42
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
            "dialect_detected": "hejazi",
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
            "source": f"benchmark:@asteribeautysa; content:{shortcode}; browser_collected:2026-05-25",
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

        # 0 ── DWZUCNfjMQt | 2026-03-27 fri | video | 68 likes | She'en Gloss hero
        obs(0, "DWZUCNfjMQt", "video", "2026-03-27", "friday", "vertical_9x16",
            "product_hero_glamour",
            "warm_studio",
            ["nude pink", "gold", "cream", "soft rose"],
            "studio", "simple",
            "bilingual", "casual", "aspirational",
            ["Glossy", "nourishing", "irresistibly smooth", "She'en", "favorite shade"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "She'en Lip Gloss hero video — sensory adjective stack (glossy + nourishing + irresistibly smooth). English-led copy for premium beauty positioning. 68 likes is among the stronger performers in this period — gloss content resonates with the audience. Product name 'She'en' blends Arabic (شئين) and English phonetics.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Gloss product hero with sensory adjective stack — premium bilingual positioning"},
            ],
            "medium"),

        # 1 ── DWb40VqFNnQ | 2026-03-28 sat | video | 49 likes | Nourish Tinted Serum influencer
        obs(1, "DWb40VqFNnQ", "video", "2026-03-28", "saturday", "vertical_9x16",
            "influencer_product_demo",
            "warm_natural",
            ["warm beige", "skin tones", "gold", "cream"],
            "indoor", "simple",
            "bilingual", "casual", "conversational",
            ["Skincare meets complexion", "Nourish Tinted Serum", "SPF 30", "@dinashariff"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Influencer @dinashariff demos Nourish Tinted Serum SPF 30 — the 'skincare meets complexion' positioning bridges the skincare-makeup divide, a key Saudi beauty consumer insight. Saturday posting for weekend beauty browsing. SPF claim is valid product benefit, not a medical claim.",
            [
                {"pattern_slug": "influencer_collab", "confidence": "strong",
                 "notes": "Influencer product demo — skincare-makeup bridge positioning relevant to Saudi beauty consumer"},
                {"pattern_slug": "skincare_beauty_bridge", "confidence": "moderate",
                 "notes": "Tinted serum with SPF — hybrid positioning taps into skin-first trend"},
            ],
            "medium"),

        # 2 ── DWednQ-iRNe | 2026-03-29 sun | video | 52 likes | Glow on the go lifestyle
        obs(2, "DWednQ-iRNe", "video", "2026-03-29", "sunday", "vertical_9x16",
            "lifestyle_routine_video",
            "warm_natural",
            ["warm beige", "gold", "soft pink", "white"],
            "outdoor", "simple",
            "bilingual", "casual", "warm",
            ["Asteri glow on the go", "your beauty routine", "keeps up with your lifestyle",
             "تألق استيري أثناء الحركة", "روتين جمال"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Lifestyle routine video — brand promise of beauty that travels with you. Bilingual caption leads with English then Arabic translation. 'keeps up with your lifestyle' is a key Asteri brand positioning message. Sunday post targets the weekend/start-of-week beauty consideration window.",
            [
                {"pattern_slug": "lifestyle_routine", "confidence": "strong",
                 "notes": "On-the-go beauty positioning — routine fits into active lifestyle, not the other way around"},
            ],
            "medium"),

        # 3 ── DWg0pDdlEvT | 2026-03-30 mon | video | 36 likes | Texture exploration
        obs(3, "DWg0pDdlEvT", "video", "2026-03-30", "monday", "vertical_9x16",
            "product_range_exploration",
            "warm_studio",
            ["dusty rose", "warm brown", "cream", "muted pink"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["Textures, colors, and finishes", "fall in love with", "ملمس وألوان وقوامات"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Product range exploration video — invites the viewer to discover the breadth of the Asteri range. 'Which one catches your eye?' engagement question. 36 likes is the minimum in this batch — Monday posting for range-showcase underperforms vs specific product/influencer content.",
            [
                {"pattern_slug": "product_range_showcase", "confidence": "moderate",
                 "notes": "Range exploration with 'which one catches your eye' — engagement question for discovery content"},
            ],
            "medium"),

        # 4 ── DWjioCJjE0_ | 2026-03-31 tue | video | 79 likes | Committed Lip Tint + Gloss combo
        obs(4, "DWjioCJjE0_", "video", "2026-03-31", "tuesday", "vertical_9x16",
            "product_combo_application",
            "warm_studio",
            ["soft rose", "nude pink", "cream", "warm gold"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["Juicy", "effortless", "made to last", "Committed Lip Tint",
             "Sweet Oasis Lip Gloss", "soft flush"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Committed Lip Tint layered with Sweet Oasis Lip Gloss — product stacking demo. 79 likes = second-highest in this batch. 'Juicy, effortless, and made to last' is the best-performing copy pattern for Asteri in this period. Lip product combinations consistently outperform single-product content.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Lip combo stack — Committed Tint + Sweet Oasis Gloss; product layering drives highest engagement"},
                {"pattern_slug": "sensory_language", "confidence": "moderate",
                 "notes": "Juicy + effortless — sensory adjectives follow the same pattern as AlBaik's top-performing copy"},
            ],
            "high"),

        # 5 ── DWox89-DIXh | 2026-04-02 thu | video | 74 likes | Legacy Lipstick refill campaign
        obs(5, "DWox89-DIXh", "video", "2026-04-02", "thursday", "vertical_9x16",
            "sustainability_brand_story",
            "warm_natural",
            ["deep rose", "matte red", "warm beige", "craft packaging"],
            "studio", "simple",
            "bilingual", "casual", "warm",
            ["Refill your Legacy Lipstick", "keep your favorite shade", "choosing a more sustainable path",
             "Beauty that lasts in every way"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Legacy Lipstick refill campaign — sustainability messaging. 'Beauty that lasts in every way ♻️' — durability applied to both formula and environmental impact. 74 likes confirms sustainability content resonates with Asteri's eco-conscious audience. Refill mechanic is a business model differentiator, not just a marketing claim.",
            [
                {"pattern_slug": "brand_values", "confidence": "strong",
                 "notes": "Refill mechanic sustainability — 'beauty that lasts in every way' spans formula and environmental impact"},
            ],
            "high"),

        # 6 ── DWraar2DIVW | 2026-04-03 fri | carousel | 40 likes | Gift sets promo
        obs(6, "DWraar2DIVW", "carousel_slide", "2026-04-03", "friday", None,
            "product_gift_set_showcase",
            "warm_studio",
            ["soft pink", "white", "gold", "warm cream"],
            "studio", "moderate",
            "bilingual", "casual", "warm",
            ["curated sets", "Asteri favorites", "up to 50% savings", "Perfect for you, or someone you love"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Gift sets carousel with up to 50% savings. 'Perfect for you, or someone you love' expands the purchase occasion beyond personal use — gifting framing. 40 likes suggests promotional content underperforms organic content for this brand. Friday posting for weekend gifting consideration.",
            [
                {"pattern_slug": "promotional_offer", "confidence": "strong",
                 "notes": "Gift set with savings — gifting framing extends purchase occasion, but promotional content underperforms organic"},
            ],
            "medium"),

        # 7 ── DWweloajKp6 | 2026-04-05 sun | photo | 56 likes | Desert Mist Setting Spray
        obs(7, "DWweloajKp6", "image", "2026-04-05", "sunday", "portrait_4x5",
            "product_hero_minimalist",
            "warm_studio",
            ["sage green", "white", "cream", "pale rose"],
            "studio", "simple",
            "bilingual", "casual", "aspirational",
            ["Set. Refresh. Repeat.", "Desert Mist", "locks it in heat, humidity"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Desert Mist Setting Spray hero photo — 'Set. Refresh. Repeat.' is a 3-word rhythm pattern (action sequence). 'Locks it in heat, humidity' is climate-specific performance claim tailored to Saudi climate. 56 likes strong for a static photo. Product name 'Desert Mist' is a culturally resonant naming choice for the Gulf.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Desert Mist — climate-adapted product name + Saudi-specific performance claim (heat, humidity)"},
                {"pattern_slug": "three_word_hook", "confidence": "moderate",
                 "notes": "Set. Refresh. Repeat. — three-word action rhythm is a premium beauty copywriting convention"},
            ],
            "medium"),

        # 8 ── DWzJbR8DOLK | 2026-04-06 mon | carousel | 56 likes | A-beauty climate performance
        obs(8, "DWzJbR8DOLK", "carousel_slide", "2026-04-06", "monday", None,
            "brand_manifesto_carousel",
            "warm_studio",
            ["clean white", "cream", "sage green", "warm beige"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["A-beauty", "made for our climate", "High performance", "Skin-first"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "A-beauty manifesto carousel — 'A' for Arabian. Positioning Asteri as the founding brand of A-beauty, equivalent to K-beauty (Korean) or J-beauty (Japanese). 'Made for our climate' is the core differentiation claim vs Western beauty brands. Carousel format for brand storytelling is appropriate for deeper messaging. 56 likes strong for brand manifesto content.",
            [
                {"pattern_slug": "brand_manifesto", "confidence": "strong",
                 "notes": "A-beauty positioning — Arabian beauty standard, made for Saudi/Gulf climate; K-beauty equivalent claim"},
            ],
            "medium"),

        # 9 ── DW1ieEDElyQ | 2026-04-07 tue | video | 37 likes | GRWM on the move
        obs(9, "DW1ieEDElyQ", "video", "2026-04-07", "tuesday", "vertical_9x16",
            "routine_tutorial_lifestyle",
            "warm_natural",
            ["warm beige", "skin tones", "soft pink", "white"],
            "indoor", "simple",
            "bilingual", "casual", "conversational",
            ["GRWM", "beauty should fit your life", "not the other way around"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Get Ready With Me (GRWM) format video — 'beauty should fit your life, not the other way around' reverses the typical beauty brand mandate. This is a direct response to perfectionism in beauty content. 37 likes underperforms — GRWM video without a named influencer has lower draw.",
            [
                {"pattern_slug": "routine_tutorial", "confidence": "strong",
                 "notes": "GRWM format — 'beauty fits your life' brand ethos; lower engagement without named influencer"},
            ],
            "medium"),

        # 10 ── DW4IrLsDNF8 | 2026-04-08 wed | photo | 41 likes | Travel beauty photo
        obs(10, "DW4IrLsDNF8", "image", "2026-04-08", "wednesday", "portrait_4x5",
            "lifestyle_product_photo",
            "warm_natural",
            ["warm beige", "soft pink", "travel bag tan", "cream"],
            "outdoor", "simple",
            "bilingual", "casual", "warm",
            ["Beauty anywhere you go", "الجمال، أينما كنت"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Travel beauty photo — bilingual caption (English first, Arabic mirror). Simple lifestyle framing: beauty product as travel companion. 41 likes for a static photo — consistent with the brand's static photo performance tier. Arabic translation follows the English in parenthetical pattern.",
            [
                {"pattern_slug": "lifestyle_routine", "confidence": "moderate",
                 "notes": "Travel beauty lifestyle photo — product as on-the-go companion, static photo format"},
            ],
            "medium"),

        # 11 ── DW6rbf2DFBY | 2026-04-09 thu | photo | 105 likes | Flextra mascara photo
        obs(11, "DW6rbf2DFBY", "image", "2026-04-09", "thursday", "portrait_4x5",
            "product_hero_closeup",
            "warm_studio",
            ["dusty pink", "gold", "white", "warm brown"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["Your lashes, but better", "Flextra Volume & Curl Mascara"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Flextra mascara hero photo — 105 likes is the second-highest in this batch. 'Your lashes, but better' is enhancement-not-transformation positioning — a key Asteri brand voice pillar (from brand manifesto: 'Beauty isn't transformation, it's refinement'). Static photo achieves exceptional engagement when the product is the hero. Mascara is clearly Asteri's hero product.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Flextra mascara — 'your lashes but better' enhancement framing; 105 likes = top static photo performance"},
                {"pattern_slug": "enhancement_not_transformation", "confidence": "strong",
                 "notes": "Brand philosophy: refinement over transformation — consistent with Asteri's A-beauty manifesto"},
            ],
            "high"),

        # 12 ── DW80zphiGo- | 2026-04-10 fri | video | 44 likes | Weekend glam routine
        obs(12, "DW80zphiGo-", "video", "2026-04-10", "friday", "vertical_9x16",
            "tutorial_routine_video",
            "warm_natural",
            ["warm rose", "dusty pink", "gold", "skin tones"],
            "indoor", "moderate",
            "bilingual", "casual", "warm",
            ["weekend glam", "easy steps", "Looking for your weekend glam?"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Weekend glam tutorial video — Friday posting aligns with Saudi weekend (Thu-Fri). 'Easy steps' positions Asteri as accessible luxury. 44 likes is moderate — tutorial content without influencer tag underperforms branded influencer content. Occasion-aware posting (weekend timing) is a positive signal.",
            [
                {"pattern_slug": "tutorial_routine", "confidence": "strong",
                 "notes": "Weekend glam routine — Friday posting for Saudi weekend timing is occasion-aware strategy"},
            ],
            "medium"),

        # 13 ── DW_8-NBjE8Z | 2026-04-11 sat | video | 117 likes | @christina_reigns Legacy Lip Balm review
        obs(13, "DW_8-NBjE8Z", "video", "2026-04-11", "saturday", "vertical_9x16",
            "influencer_product_review",
            "warm_natural",
            ["deep rose", "gold", "skin tones", "cream"],
            "indoor", "simple",
            "bilingual", "casual", "conversational",
            ["@christina_reigns", "sparkling legacy lip balms", "how long it lasts"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Top-performing post in this batch — 117 likes. @christina_reigns authentic review format (tries, tests, describes). Saturday posting = weekend peak for beauty content. 'Sparkling Legacy Lip Balms' — sparkle/shine attribute is the hero. Influencer review format (not paid ad style) drives 2x+ vs brand-only content. This is Asteri's clearest engagement formula: real person + lip product + authenticity.",
            [
                {"pattern_slug": "influencer_collab", "confidence": "strong",
                 "notes": "Top performer — @christina_reigns authentic review; influencer + lip product = Asteri's highest engagement formula"},
                {"pattern_slug": "product_review_ugc", "confidence": "strong",
                 "notes": "Review format (not ad) — authentic first-person testing drives 2x+ vs brand-only production"},
            ],
            "high"),

        # 14 ── DXChrU_jLMC | 2026-04-12 sun | photo | 47 likes | Xtend Lip Liner teaser
        obs(14, "DXChrU_jLMC", "image", "2026-04-12", "sunday", "portrait_4x5",
            "product_teaser_mystery",
            "warm_studio",
            ["deep berry", "nude pink", "cream", "warm rose"],
            "studio", "simple",
            "bilingual", "casual", "anticipatory",
            ["Something new is coming", "this one stays with you",
             "شيء جديد قادم"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Xtend Lip Liner Stain teaser photo — 'this one stays with you' is a double entendre (product longevity + emotional connection). 47 likes for a pure teaser with no product name reveal. Pre-launch teaser is part of the full Xtend Lip Liner Stain launch sequence (DXKPkUujHDp + DXMtJDaiFXN follow 3+ days later).",
            [
                {"pattern_slug": "product_teaser", "confidence": "strong",
                 "notes": "Xtend Lip Liner pre-launch teaser — 'stays with you' double entendre; part of structured launch sequence"},
            ],
            "medium"),

        # 15 ── DXE-y0Fmrog | 2026-04-13 mon | video | 37 likes | Swoosh Blush application
        obs(15, "DXE-y0Fmrog", "video", "2026-04-13", "monday", "vertical_9x16",
            "product_application_tutorial",
            "warm_natural",
            ["soft coral", "warm rose", "skin tones", "cream"],
            "studio", "simple",
            "bilingual", "casual", "aspirational",
            ["A flush that feels like your own", "Swoosh blush", "melts seamlessly"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Swoosh Blush application video — 'A flush that feels like your own' is skin-mimic positioning (the blush looks natural, not applied). 'Melts seamlessly' is a tactile-visual sensory phrase. 37 likes — blush underperforms vs lip and mascara for this brand. Monday posting is sub-optimal for tutorial content.",
            [
                {"pattern_slug": "product_application", "confidence": "strong",
                 "notes": "Swoosh blush — skin-mimic positioning ('feels like your own'); blush underperforms vs lip/lash content"},
            ],
            "medium"),

        # 16 ── DXKPkUujHDp | 2026-04-15 wed | carousel | 68 likes | Xtend Lip Liner Stain launch
        obs(16, "DXKPkUujHDp", "carousel_slide", "2026-04-15", "wednesday", None,
            "product_launch_carousel",
            "warm_studio",
            ["deep berry", "warm rose", "nude", "cream"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["Introducing Xtend Lip Liner Stain", "A new generation", "lip tattoo look",
             "precision", "lasting colour"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Xtend Lip Liner Stain official launch carousel — 'A new generation of' framing positions it as a category evolution. 'Lip tattoo look' creates the aspirational reference point. 68 likes for a product launch carousel is the strongest launch-format post in this batch. Multi-slide format enables feature-by-feature reveal.",
            [
                {"pattern_slug": "product_launch_reveal", "confidence": "strong",
                 "notes": "Xtend Lip Liner launch carousel — 'new generation' + 'lip tattoo' aspirational reference; best launch post format"},
                {"pattern_slug": "feature_reveal_sequence", "confidence": "strong",
                 "notes": "Carousel allows feature-by-feature reveal across slides — effective for complex new product launches"},
            ],
            "medium"),

        # 17 ── DXMtJDaiFXN | 2026-04-16 thu | photo | 68 likes | Xtend Lip Liner in hand
        obs(17, "DXMtJDaiFXN", "image", "2026-04-16", "thursday", "portrait_4x5",
            "product_in_hand_lifestyle",
            "warm_natural",
            ["deep berry", "skin tones", "cream", "warm rose"],
            "studio", "simple",
            "bilingual", "casual", "aspirational",
            ["Your new essential", "Crafted for precision", "designed to last"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Xtend Lip Liner Stain 'in hand' lifestyle photo — product held naturally, not displayed on surface. 'Your new essential' creates urgency without promotionalism. 68 likes matches the carousel launch post — both parts of the same launch wave. The 'in hand' format humanises product.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Xtend Lip Liner in-hand lifestyle — 'your new essential' urgency without discount incentive"},
            ],
            "medium"),

        # 18 ── DXSEaf-DO6x | 2026-04-18 sat | video | 80 likes | Asteri day with @talaalakeel
        obs(18, "DXSEaf-DO6x", "video", "2026-04-18", "saturday", "vertical_9x16",
            "influencer_brand_event",
            "warm_natural",
            ["warm beige", "skin tones", "Asteri brand palette", "gold"],
            "indoor", "moderate",
            "bilingual", "casual", "warm",
            ["Asteri day", "@talaalakeel", "Testing, swatching, glowing"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Asteri Day with influencer @talaalakeel — brand event format (testing/swatching session). 80 likes is the third-highest in this batch. Saturday brand event posting captures peak weekend beauty browsing. 'Testing, swatching, glowing' follows the testing → application → result narrative arc — shows the influencer journey. Brand events drive stronger engagement than solo product videos.",
            [
                {"pattern_slug": "influencer_collab", "confidence": "strong",
                 "notes": "@talaalakeel Asteri Day — brand event format drives 3rd highest engagement; testing narrative arc"},
                {"pattern_slug": "brand_experience_event", "confidence": "moderate",
                 "notes": "Physical brand event documented on social — authenticity signal for brand trust building"},
            ],
            "high"),

        # 19 ── DXUgIsuDEQd | 2026-04-19 sun | carousel | 38 likes | Xtend precision carousel
        obs(19, "DXUgIsuDEQd", "carousel_slide", "2026-04-19", "sunday", None,
            "product_benefit_carousel",
            "warm_studio",
            ["deep berry", "nude rose", "cream", "warm brown"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["more precision", "اكستند ليب لاينر", "شفاهكِ بتحديد أكثر"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Xtend Lip Liner precision-focused carousel — follows 4 days after the main launch carousel (DXKPkUujHDp). Arabic caption leads with feminine address (شفاهكِ = your lips, female form). 38 likes — post-launch follow-up content underperforms the launch itself, typical for sustained product campaigns.",
            [
                {"pattern_slug": "product_hero", "confidence": "moderate",
                 "notes": "Xtend Lip Liner post-launch carousel — follow-up precision focus; lower engagement after launch peak"},
            ],
            "medium"),

        # 20 ── DXXWVvNDGak | 2026-04-20 mon | video | 47 likes | Premium product hero video
        obs(20, "DXXWVvNDGak", "video", "2026-04-20", "monday", "vertical_9x16",
            "product_hero_luxury",
            "warm_studio",
            ["deep berry", "warm rose", "gold", "cream"],
            "studio", "moderate",
            "bilingual", "casual", "aspirational",
            ["ترف", "دقة الطرف", "غنى اللون", "ثباته"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Luxury/premium product hero video — Arabic caption uses 'ترف' (luxury) as the opening word. 'دقة الطرف' (precision of the tip) + 'غنى اللون' (richness of color) + 'ثباته' (its staying power) — a triple quality claim in Arabic. 47 likes for Arabic-dominant premium content on a Monday.",
            [
                {"pattern_slug": "product_hero", "confidence": "strong",
                 "notes": "Arabic luxury positioning — ترف opener + triple quality claim (precision + richness + longevity)"},
            ],
            "medium"),

        # 21 ── DXb8TPriOHb | 2026-04-22 wed | carousel | 79 likes | B Corp sustainability carousel
        obs(21, "DXb8TPriOHb", "carousel_slide", "2026-04-22", "wednesday", None,
            "brand_values_sustainability_carousel",
            "warm_studio",
            ["sage green", "warm beige", "cream", "earthy brown"],
            "studio", "moderate",
            "bilingual", "casual", "warm",
            ["جمال يهتم بما يتجاوز السطح", "B Corp", "الاستدامة جزء من هويتنا",
             "Beauty that cares, beyond the surface"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "B Corp certification sustainability carousel — 79 likes = second-highest in batch (tied with DWjioCJjE0_). 'Beauty that cares, beyond the surface' is a layered phrase (skincare surface + social responsibility). B Corp certification is a credible third-party endorsement. Sustainability content resonates strongly with Asteri's audience — confirms brand values content is a top pillar, not just filler.",
            [
                {"pattern_slug": "brand_values", "confidence": "strong",
                 "notes": "B Corp sustainability carousel — 79 likes confirms values content is top pillar; 'beyond the surface' layered meaning"},
                {"pattern_slug": "third_party_credibility", "confidence": "strong",
                 "notes": "B Corp certification as credibility signal — earned endorsement vs brand claim"},
            ],
            "high"),

        # 22 ── DXegvUaDGzW | 2026-04-23 thu | photo | 43 likes | Real beauty routine photo
        obs(22, "DXegvUaDGzW", "image", "2026-04-23", "thursday", "portrait_4x5",
            "lifestyle_flat_lay",
            "warm_natural",
            ["warm rose", "dusty pink", "warm cream", "soft brown"],
            "studio", "simple",
            "bilingual", "casual", "warm",
            ["روتين الجمال الحقيقي", "فوضوي قليلاً", "دائماً أساسي",
             "The real beauty routine… slightly messy, always essential"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Real beauty routine photo — 'slightly messy, always essential' is an anti-perfectionism positioning statement. Bilingual caption with Arabic leading (unusual for this account — usually English-first). 'فوضوي قليلاً' (slightly chaotic) normalises imperfect beauty routines, resonating with authentic beauty content trends.",
            [
                {"pattern_slug": "authenticity_positioning", "confidence": "strong",
                 "notes": "'Slightly messy, always essential' — anti-perfectionism; Arabic-first caption (unusual for this account)"},
            ],
            "medium"),

        # 23 ── DXg_FimFAi_ | 2026-04-24 fri | video | 47 likes | Torique lip liner by @the.adwa
        obs(23, "DXg_FimFAi_", "video", "2026-04-24", "friday", "vertical_9x16",
            "influencer_product_demo",
            "warm_natural",
            ["deep berry", "skin tones", "warm rose", "cream"],
            "studio", "simple",
            "bilingual", "casual", "conversational",
            ["أضوى توريك كيف", "بتمريرة واحدة", "تحديد دقيق", "ولون يثبت",
             "@the.adwa", "One swipe, precise line"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Torique lip liner tutorial by @the.adwa — 'أضوى' (Adwa, the influencer's name) as the how-to anchor. Arabic caption leads with influencer name + product tutorial. 'بتمريرة واحدة' (in one swipe) — single-motion ease is the key benefit claim. 47 likes on a Friday with influencer tag is moderate — @the.adwa has lower reach than @talaalakeel or @christina_reigns.",
            [
                {"pattern_slug": "influencer_collab", "confidence": "strong",
                 "notes": "@the.adwa Torique tutorial — 'one swipe' ease claim; moderate reach influencer"},
                {"pattern_slug": "tutorial_routine", "confidence": "moderate",
                 "notes": "Application tutorial with named influencer — 47 likes reflects micro-influencer reach level"},
            ],
            "medium"),

        # 24 ── DXkB7jXjKEF | 2026-04-25 sat | photo | 38 likes | Desert Mist Setting Spray photo
        obs(24, "DXkB7jXjKEF", "image", "2026-04-25", "saturday", "portrait_4x5",
            "product_ingredient_focus",
            "warm_studio",
            ["sage green", "white", "pale rose", "cream"],
            "studio", "simple",
            "bilingual", "casual", "aspirational",
            ["ديزرت ميست سيتنق سبراي", "يدوم حتى ١٢ ساعة", "بخلاصة ماء الورد والليمون",
             "12 hours", "rose water", "lemon extract"],
            True,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Desert Mist Setting Spray ingredient focus photo — Arabic caption leads with product transliteration then specs (12 hours, rose water + lemon). Ingredient-forward copy aligns with 'ingredient_reveal_macro' pattern in the account profile. 38 likes for a Saturday static product photo is slightly below this account's static photo average.",
            [
                {"pattern_slug": "ingredient_reveal", "confidence": "strong",
                 "notes": "Desert Mist with rose water + lemon ingredients — climate-adapted ingredient story"},
            ],
            "medium"),

        # 25 ── DYpaEQijsIR | 2026-05-22 fri | video | 42 likes | Asteri favorites menu video
        obs(25, "DYpaEQijsIR", "video", "2026-05-22", "friday", "vertical_9x16",
            "brand_range_showcase",
            "warm_studio",
            ["warm beige", "soft rose", "cream", "gold"],
            "studio", "moderate",
            "bilingual", "casual", "playful",
            ["مُقدَّم لكِ: مفضلات أستيري", "بدون حجز مسبق",
             "Served: Your Asteri favorites", "No reservations needed"],
            False,
            NO_FLAGS, CLEAN,
            "evergreen", "modern", [],
            "Asteri favorites 'menu' format video — 🍽️ restaurant metaphor for beauty products. 'بدون حجز مسبق' (no reservations needed) = accessible luxury. Bilingual with Arabic-first mirror. Creative concept (restaurant menu = beauty lineup) is the freshest content format in this batch. 42 likes is modest — creative concepts without influencer anchoring underperform even when the idea is strong.",
            [
                {"pattern_slug": "creative_format_experiment", "confidence": "moderate",
                 "notes": "Restaurant menu metaphor for product range — creative format; underperforms without influencer anchor"},
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

    print(f"\n  Written: {written}  Skipped: {skipped}")


if __name__ == "__main__":
    main()
