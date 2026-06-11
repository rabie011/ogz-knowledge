#!/usr/bin/env python3
"""Write 38 new observations for @pizzahutsaudi (OGZ-F-AND-B-Reference-038).
Brings total from 12 → 50 obs. Covers Mar 11–May 24 2026.
Occasion diversity: evergreen(34) + ramadan(2) + eid_al_fitr(1) + saudi_flag_day(1).
Format diversity: image(14) + carousel(12) + video(12).
"""
import json, pathlib

REPO = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')
OUT  = REPO / '11_who_to_learn_from' / 'observations' / 'f_and_b'
OUT.mkdir(parents=True, exist_ok=True)

ACCOUNT_NORM = "OGZ-F-AND-B-Reference-038"
ACCOUNT_ULID = "01KS5XZ0Y071HFE865V215DE1C"
SECTOR       = "f_and_b"
NOW          = "2026-05-25T01:20:00Z"

def obs(ulid, shortcode, content_type, capture_date, day_of_week, aspect_ratio,
        composition_style, lighting, colors, setting, visual_complexity,
        language, register, tone, notable_phrases, cta, caption_text, hashtag_count, has_emoji,
        soft_flags, compliance,
        occasion, heritage, hosp_cues, free_notes,
        patterns, engagement_potential):
    ct = "carousel_slide" if content_type == "carousel" else content_type
    return {
        "observation_ulid": ulid,
        "schema_version": 1,
        "account_handle_normalized": ACCOUNT_NORM,
        "account_ulid": ACCOUNT_ULID,
        "sector": SECTOR,
        "content_ref": {
            "filename": f"{shortcode}.jpg",
            "platform": "instagram",
            "content_type": ct,
            "capture_date": capture_date,
            "source_url": f"https://www.instagram.com/p/{shortcode}/",
            "aspect_ratio": aspect_ratio,
            "day_of_week": day_of_week,
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
            "caption_text": caption_text,
            "caption_word_count": len(caption_text.split()) if caption_text else None,
            "hashtag_count": hashtag_count,
            "has_emoji": has_emoji,
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
            "source": f"benchmark:@pizzahutsaudi; content:{shortcode}.jpg",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b",
        },
        "occasion": occasion,
    }


SOFT_DISCOUNT = [{"flag_type": "discount_dominant_no_cultural_warmth",
                  "description": "discount_dominant_no_cultural_warmth"}]
SOFT_ITALIAN  = [{"flag_type": "Italian_origin_as_aspirational",
                  "description": "Italian_origin_as_aspirational_no_saudi_frame"}]
SOFT_WESTERN  = [{"flag_type": "western_social_mechanic_no_cultural_identity",
                  "description": "western_social_mechanic_no_cultural_identity"}]


records = [

    # 1 — DYuHpJlACDR — May 24 2026 (Sun) — carousel portrait_4x5 — 50% discount wait teaser
    obs("01KSE2JDGD7PW8C3JTBBNVYSFK",
        "DYuHpJlACDR", "carousel", "2026-05-24", "sunday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["كل شي يستاهل الانتظار", "50% خصم"], True,
        "كل شي يستاهل الانتظار\nخصوصًا من يكون 50% خصم 🍕❤️", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: discount wait mechanic — 'everything is worth the wait, especially at 50% off'. No cultural storytelling, pure deal activation.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% off with emoji hook"}],
        "low"),

    # 2 — DYo-kylAIx1 — May 22 2026 (Fri) — image portrait_4x5 — "everyone agreed" brand love
    obs("01KSE2JDGD7PW8C3JTBBNVYSFM",
        "DYo-kylAIx1", "image", "2026-05-22", "friday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["ما يحتاج تصويت", "الجميع اتفق على حبه"], False,
        "ما يحتاج تصويت، لأن الجميع اتفق على حبه❤️🍕", 2, True,
        SOFT_WESTERN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Social engagement mechanic — implied consensus brand love. Poster/magazine format. No Saudi cultural resonance.",
        [{"pattern_slug": "product_hero", "confidence": "moderate", "notes": "poster-style product image with 'best offer' overlay"}],
        "medium"),

    # 3 — DYHmliXAP1y — May 9 2026 (Sat) — carousel portrait_4x5 — 50% guest promo
    obs("01KSE2JDGD7PW8C3JTBBNVYSFN",
        "DYHmliXAP1y", "carousel", "2026-05-09", "saturday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["هذا مو أي ضيف", "HUT50"], True,
        "هذا مو أي ضيف. هذا عرض 50%  على طلبات الاستلام + التوصيل\nاستخدم كود: HUT50🍕❤️", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% discount carousel using 'guest' metaphor for offer. Promo code CTA. Pure transactional no cultural value.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% offer with promo code HUT50"}],
        "low"),

    # 4 — DYCWGKdjGRd — May 7 2026 (Thu) — carousel portrait_4x5 — how to hold pizza tutorial
    obs("01KSE2JDGD7PW8C3JTBBNVYSFP",
        "DYCWGKdjGRd", "carousel", "2026-05-07", "thursday", "portrait_4x5",
        "educational_step_sequence", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["مو منطقي كل المكونات تطيح", "تعلمتوا"], False,
        "مو منطقي كل المكونات تطيح عشان طريقة مسكك للبيتزا؟\nها بشروا تعلمتوا؟🍕❤️", 2, True,
        SOFT_WESTERN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: How-to-hold-pizza engagement carousel — global QSR social mechanic. Playful but culturally rootless Saudi-wise.",
        [{"pattern_slug": "educational_explainer", "confidence": "moderate", "notes": "step carousel on pizza-holding technique — social engagement hook"}],
        "medium"),

    # 5 — DYCPQzUgNmY — May 7 2026 (Thu) — carousel portrait_4x5 — Italian crust reveal
    obs("01KSE2JDGD7PW8C3JTBBNVYSFQ",
        "DYCPQzUgNmY", "carousel", "2026-05-07", "thursday", "portrait_4x5",
        "product_reveal_sequence", "cold_studio", ["cream","red","white"], "studio", "complex",
        "arabic", "casual", "excitement",
        ["فتحنا لك شي جديد", "العجينة الإيطالية الجديدة", "تداعب حواسك"], True,
        "فتحنا لك شي جديد،  بس التجربة عليك.👀🍕\nالعجينة الإيطالية الجديدة خفيفة وهشة تداعب حواسك من أول لقمة.🤌✨", 2, True,
        SOFT_ITALIAN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Italian crust launch carousel — sensory copy 'caresses your senses'. Italian origin positioned as quality signal. No Saudi cultural launch hook.",
        [{"pattern_slug": "seasonal_collection_drop", "confidence": "strong", "notes": "new Italian crust reveal carousel"},
         {"pattern_slug": "close_up_macro_texture", "confidence": "moderate", "notes": "dough texture showcase"}],
        "medium"),

    # 6 — DX_c0wRgBmZ — May 6 2026 (Wed) — image portrait_4x5 — loyalty points app
    obs("01KSE2JDGD7PW8C3JTBBNVYSFR",
        "DX_c0wRgBmZ", "image", "2026-05-06", "wednesday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","orange"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["وش أحلى من بيتزا؟ بيتزا + نقاط أكثر", "ضاعف نقاطك"], True,
        "وش أحلى من بيتزا؟ بيتزا + نقاط أكثر! \nضاعف نقاطك من خلال طلبات التطبيق، كل طلب يعطيك قيمة أكبر، وطعم مميز كالعادة، لا تفوتها، واطلب الحين من التطبيق💯❤️", 3, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Loyalty points app promo. Global QSR mechanic — double your points. No cultural identity, pure transactional activation.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "moderate", "notes": "loyalty points promotion via app"}],
        "low"),

    # 7 — DX9BT9szkF6 — May 5 2026 (Tue) — video vertical_9x16 — Italian crust reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSFS",
        "DX9BT9szkF6", "video", "2026-05-05", "tuesday", "vertical_9x16",
        "product_reveal_sequence", "warm product spotlight", ["cream","red","orange"], "studio", "complex",
        "arabic", "casual", "excitement",
        ["جديدنا غير", "عجينة إيطالية أصلية", "أقرب للأصل"], True,
        "جديدنا غير!\nعجينة إيطالية أصلية بقوام خفيف، تعطيك تجربة أقرب للأصل بكل تفاصيلها. جربها الحين وخلك الحكم😍🍕", 3, True,
        SOFT_ITALIAN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Italian crust launch reel. 'Original Italian dough' positions authenticity via foreign origin. 'Be the judge' creates engagement hook. No Saudi cultural entry point.",
        [{"pattern_slug": "seasonal_collection_drop", "confidence": "strong", "notes": "Italian crust campaign hero reel"},
         {"pattern_slug": "close_up_macro_texture", "confidence": "moderate", "notes": "dough texture close-up"}],
        "medium"),

    # 8 — DXyk2zvAIVj — May 1 2026 (Fri) — carousel portrait_4x5 — brand gratitude/UGC
    obs("01KSE2JDGD7PW8C3JTBBNVYSFT",
        "DXyk2zvAIVj", "carousel", "2026-05-01", "friday", "portrait_4x5",
        "ugc_showcase", "warm_studio", ["red","white","cream"], "studio", "simple",
        "arabic", "casual", "warm",
        ["شكراً من القلب", "يطربوا القلب"], False,
        "شكراً من القلب لكل اللي يطربوا القلب❤️", 3, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: Brand gratitude post — 'thank you from the heart'. Likely UGC celebration or milestone. Warm tone but no genuine cultural depth; global QSR social playbook.",
        [{"pattern_slug": "user_content_repost", "confidence": "moderate", "notes": "gratitude carousel — UGC or milestone celebration"}],
        "medium"),

    # 9 — DXwWKXTDNBZ — Apr 30 2026 (Thu) — carousel portrait_4x5 — teaser pre-launch
    obs("01KSE2JDGD7PW8C3JTBBNVYSFV",
        "DXwWKXTDNBZ", "carousel", "2026-04-30", "thursday", "portrait_4x5",
        "teaser_graphic", "flat_graphic", ["red","white","dark_brown"], "studio", "simple",
        "arabic", "casual", "mystery",
        ["الإشارة واضحة", "الجديد أقرب مما تتوقع"], False,
        "الإشارة واضحة والجديد أقرب مما تتوقع🍕❤️", 3, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: Pre-launch teaser for Italian crust campaign. Mystery mechanic. No Saudi cultural framing for the reveal.",
        [{"pattern_slug": "teaser_announcement", "confidence": "strong", "notes": "pre-launch teaser — 'new thing closer than you think'"}],
        "low"),

    # 10 — DXt9mbjAJGf — Apr 29 2026 (Wed) — carousel portrait_4x5 — 50% first app order
    obs("01KSE2JDGD7PW8C3JTBBNVYSFW",
        "DXt9mbjAJGf", "carousel", "2026-04-29", "wednesday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["بتلقى خيرنا بدون ما تجرب غيرنا", "HUT50"], True,
        "بتلقى خيرنا بدون ما تجرب غيرنا، حمل التطبيق الحين واحصل على خصم %50 على أول طلب كود:  HUT50🔥📲", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% first-order app promo. 'You'll find our goodness without trying others' — exclusive but still purely transactional. Global QSR playbook.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% first-app-order promo carousel with HUT50 code"}],
        "low"),

    # 11 — DXt5copDE-3 — Apr 29 2026 (Wed) — image portrait_4x5 — surprise teaser
    obs("01KSE2JDGD7PW8C3JTBBNVYSFX",
        "DXt5copDE-3", "image", "2026-04-29", "wednesday", "portrait_4x5",
        "teaser_graphic", "flat_graphic", ["red","white","dark_brown"], "studio", "simple",
        "arabic", "casual", "mystery",
        ["تحبون المفاجآت", "مفاجأتنا غيييير", "وش تتوقعون"], False,
        "تحبون المفاجآت ولا ما تحبونها، مفاجأتنا غيييير، وش تتوقعون 👀🍕", 3, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: Audience engagement teaser — 'do you like surprises? ours is different, what do you expect?'. Classic global social mechanic. No Saudi cultural specificity.",
        [{"pattern_slug": "teaser_announcement", "confidence": "strong", "notes": "surprise teaser with audience engagement hook"}],
        "medium"),

    # 12 — DXrELsnjA2M — Apr 28 2026 (Tue) — image portrait_4x5 — 30% promo code
    obs("01KSE2JDGD7PW8C3JTBBNVYSFY",
        "DXrELsnjA2M", "image", "2026-04-28", "tuesday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["بيتزاهت دايم غييييييييير", "NEXT30", "خصم %30"], True,
        "بيتزاهت دايم غييييييييير، استخدم كود NEXT30\nواحصل على خصم %30 على طلبات التوصيل والاستلام من الفرع 🍕🔥", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 30% discount promo code NEXT30. Exaggerated 'different' (غييييييييير) as brand voice — global playbook word. Comments show promo code issues = poor customer experience.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "30% off promo with NEXT30 code"}],
        "low"),

    # 13 — DXoz93jDDfE — Apr 27 2026 (Mon) — image portrait_4x5 — Mega Week promo
    obs("01KSE2JDGD7PW8C3JTBBNVYSFZ",
        "DXoz93jDDfE", "image", "2026-04-27", "monday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["الحي يحييك", "حياكم على عروض أسبوع الميجا"], True,
        "الحي يحييك، حياكم على عروض أسبوع الميجا لا تفوتكم 🍕😍", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Mega Week deal announcement. Comments asking price/offer details — text-heavy discount image with no product shown. Low engagement expected.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "Mega Week promo announcement"}],
        "low"),

    # 14 — DXlstWLgIar — Apr 26 2026 (Sun) — carousel portrait_4x5 — luck/try your luck
    obs("01KSE2JDGD7PW8C3JTBBNVYSG0",
        "DXlstWLgIar", "carousel", "2026-04-26", "sunday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","orange"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["انطح فالك", "بيتزاهت لا يفوتك"], True,
        "انطح فالك، بيتزاهت لا يفوتك🍕🔥", 2, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: 'Try your luck / Pizza Hut can't be missed' — colloquial playful CTA carousel. No product narrative, pure brand presence post.",
        [{"pattern_slug": "product_hero", "confidence": "moderate", "notes": "colloquial CTA carousel — try your luck hook"}],
        "low"),

    # 15 — DXj5wiUE6a7 — Apr 25 2026 (Sat) — video vertical_9x16 — humorous order-size reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG1",
        "DXj5wiUE6a7", "video", "2026-04-25", "saturday", "vertical_9x16",
        "social_skit", "natural mixed", ["red","white","neutral"], "restaurant interior", "moderate",
        "arabic", "casual", "humorous",
        ["وش حجم البيتزا ونوعها بعد اذنك"], False,
        "وش حجم البيتزا ونوعها بعد اذنك 😅🤣", 2, True,
        SOFT_WESTERN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Humorous skit-style reel — customer asking politely 'what size and type please?' Comedy format borrowed from global social content playbook. No Saudi cultural identity.",
        [{"pattern_slug": "social_skit", "confidence": "strong", "notes": "humorous customer order skit reel"}],
        "medium"),

    # 16 — DXhTHSak-Z6 — Apr 24 2026 (Fri) — video vertical_9x16 — HUT50 discount reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG2",
        "DXhTHSak-Z6", "video", "2026-04-24", "friday", "vertical_9x16",
        "product_reveal_sequence", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["ما نلعب عليكم", "HUT50"], True,
        "ما نلعب عليكم، خصم %50 لك\nلو أول مرة تستخدم تطبيق بيتزاهت استخدم كود: HUT50🍕🤩", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% first-app-order reel. 'We're not playing with you' as authenticity hook. Pure transactional, no cultural substance.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% HUT50 reel promo"}],
        "low"),

    # 17 — DXUgkw5k8OL — Apr 19 2026 (Sun) — video vertical_9x16 — 2 pizzas 29 SAR
    obs("01KSE2JDGD7PW8C3JTBBNVYSG3",
        "DXUgkw5k8OL", "video", "2026-04-19", "sunday", "vertical_9x16",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "simple",
        "arabic", "casual", "transactional",
        ["٢ بيتزا كبير ب٢٩ ريال", "صفقة ما تتفوت"], True,
        "٢ بيتزا كبير ب٢٩ ريال للوحدة\nاتوقع انها صفقة ما تتفوت، أطلب الحين🍕🤩", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Price-first reel — 2 large pizzas for 29 SAR each. 'Deal you can't miss.' Pure discount activation.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "2-for-29 price reel"}],
        "low"),

    # 18 — DXRUOL7gNqR — Apr 18 2026 (Sat) — carousel portrait_4x5 — 50% PH50 carousel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG4",
        "DXRUOL7gNqR", "carousel", "2026-04-18", "saturday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["وقت البيتزا", "PH50"], True,
        "وقت البيتزا وب 50% خصم بعد على البيتزا الكبير \nاطلب الحين واستخدم كود: PH50🍕🔥 ", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% PH50 discount carousel. 'Pizza time' framing — time-urgency + promo code. Typical global QSR discount mechanics.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% PH50 promo carousel"}],
        "low"),

    # 19 — DXPRxlHgIFd — Apr 17 2026 (Fri) — image portrait_4x5 — PH50 half-price
    obs("01KSE2JDGD7PW8C3JTBBNVYSG5",
        "DXPRxlHgIFd", "image", "2026-04-17", "friday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["ادفع نص السعر وعلينا النص الثاني", "PH50", "بالعافية عليكم"], True,
        "ادفع نص السعر وعلينا النص الثاني\nباستخدام كود: PH50 \nبالعافية عليكم🍕❤️", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% PH50 code image. 'Pay half, we cover the other half' — social deal framing. 'بالعافية عليكم' weak hospitality signal but promo-driven not genuine.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "PH50 half-price image promo"}],
        "low"),

    # 20 — DXMfTtIjFu2 — Apr 16 2026 (Thu) — carousel portrait_4x5 — colloquial deal CTA
    obs("01KSE2JDGD7PW8C3JTBBNVYSG6",
        "DXMfTtIjFu2", "carousel", "2026-04-16", "thursday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["تفضلوا على قل الكلافة", "يبيض الوجه"], True,
        "تفضلوا على قل الكلافة، تراه يبيض الوجه، اطلبوا الحيييييييين 😎🍕", 2, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: Colloquial deal CTA — 'come with dignity, it'll brighten your face'. Playful Saudi dialect but no genuine cultural depth. Pure deal hook.",
        [{"pattern_slug": "product_hero", "confidence": "moderate", "notes": "colloquial deal CTA carousel"}],
        "low"),

    # 21 — DXKQXXNk1G9 — Apr 15 2026 (Wed) — video vertical_9x16 — CSR passion reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG7",
        "DXKQXXNk1G9", "video", "2026-04-15", "wednesday", "vertical_9x16",
        "documentary_csr", "natural mixed", ["red","white","neutral"], "restaurant interior", "moderate",
        "arabic", "casual", "caring",
        ["هنا الشغف هو اللغة الوحيدة"], False,
        "هنا الشغف هو اللغة الوحيدة 🍕❤️", 2, True,
        [], "clean",
        "evergreen", "modern", ["accessible_workspace"],
        "Tier 4: CSR reel for 'Opportunities for All' (#فرص_للجميع) — passion language, accessible franchise employment. Genuine CSR value but global QSR template, no Saudi cultural specificity.",
        [{"pattern_slug": "educational_explainer", "confidence": "moderate", "notes": "CSR accessibility showcase reel — franchise jobs for all"}],
        "medium"),

    # 22 — DXKBLEck3bf — Apr 15 2026 (Wed) — video vertical_9x16 — PH50 reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG8",
        "DXKBLEck3bf", "video", "2026-04-15", "wednesday", "vertical_9x16",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "simple",
        "arabic", "casual", "transactional",
        ["خصم %50", "PH50"], True,
        "خصم %50 على البيتزا الكبير\nاستخدم كود: PH50🍕🔥", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Straightforward 50% PH50 code reel. Minimal text, maximum discount visibility.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% off large pizza reel — PH50 code"}],
        "low"),

    # 23 — DXCvdY8AP-h — Apr 12 2026 (Sun) — video vertical_9x16 — dual offer reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSG9",
        "DXCvdY8AP-h", "video", "2026-04-12", "sunday", "vertical_9x16",
        "product_hero", "warm product spotlight", ["red","cream","white"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["يملى العين والكرش بعد", "عرض الثنائي"], True,
        "يملى العين والكرش بعد، عرض الثنائي اطلب الحين😍🍕", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Dual pizza deal reel — 'fills the eye and stomach too'. Sensory-lite copy. No cultural context. Pure deal activation.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "moderate", "notes": "dual-offer reel with sensory copy hook"}],
        "low"),

    # 24 — DXCHu6TDDdY — Apr 12 2026 (Sun) — image portrait_4x5 — gathering deal image
    obs("01KSE2JDGD7PW8C3JTBBNVYSGA",
        "DXCHu6TDDdY", "image", "2026-04-12", "sunday", "portrait_4x5",
        "product_catalogue", "cold_studio", ["red","cream","white"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["لمة حلوة", "محسومة محسومة"], True,
        "لمة حلوة جبنالها الوجبة الصح، ٢ بيتزا كبير ب٣٥ ريال للوحدة + ٢ بيبسي فز مجانًا، \nمحسومة محسومة🫧🍕", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Gathering deal image — 'sweet gathering, we got the right meal'. Gathering (لمة) is culturally relevant word but used as deal hook, not genuine hospitality narrative.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "gathering deal — 2 pizzas + 2 Pepsi bundle"}],
        "low"),

    # 25 — DW8vq-jE5M9 — Apr 10 2026 (Fri) — video vertical_9x16 — buy 2 get 1 reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSGB",
        "DW8vq-jE5M9", "video", "2026-04-10", "friday", "vertical_9x16",
        "product_hero", "cold_studio", ["red","cream","white"], "studio", "moderate",
        "arabic", "casual", "playful",
        ["2 عليك ووحدة مننا هدية", "اعزم اهلك أو اخوياك"], True,
        "2 عليك ووحدة مننا هدية، اعزم اهلك أو اخوياك على بيتزاهت 🍕3️⃣", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Buy 2 get 1 free reel. 'Invite your family or friends' — social hook used for deal. اعزم (invite/treat) is hospitality-adjacent but purely transactional.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "buy 2 get 1 free reel with social invite hook"}],
        "medium"),

    # 26 — DW34izrDPNf — Apr 8 2026 (Wed) — image portrait_4x5 — central region deal
    obs("01KSE2JDGD7PW8C3JTBBNVYSGC",
        "DW34izrDPNf", "image", "2026-04-08", "wednesday", "portrait_4x5",
        "product_catalogue", "cold_studio", ["red","cream","white"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["يا حي الله العروض الزينة", "متوفر في المنطقة الوسطى فقط"], True,
        "يا حي الله العروض الزينة، 2 بيتزا كبير بـ29 ريال للوحدة، اطلب الحين\nمتوفر في المنطقة الوسطى فقط❤️🍕", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Regional deal image — 2 pizzas for 29 SAR, Central Region only. Geographic limitation fragments audience. Discount-first no cultural identity.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "regional deal image — central region only"}],
        "low"),

    # 27 — DWhCElzE0RV — Mar 30 2026 (Mon) — video vertical_9x16 — all roads to PH reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSGD",
        "DWhCElzE0RV", "video", "2026-03-30", "monday", "vertical_9x16",
        "social_skit", "natural mixed", ["red","neutral","white"], "street or car", "moderate",
        "arabic", "casual", "playful",
        ["كل الطرق تؤدي إلى بيتزاهت"], False,
        "كل الطرق تؤدي إلى بيتزاهت 🍕🚗🔥", 2, True,
        SOFT_WESTERN, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 'All roads lead to Pizza Hut' — allusion to Latin proverb adapted for brand. Skit or drive-to-store concept. No Saudi cultural identity.",
        [{"pattern_slug": "social_skit", "confidence": "moderate", "notes": "all-roads-to-PH brand reel — drive-to-store"}],
        "low"),

    # 28 — DWd7YfgjNBx — Mar 29 2026 (Sun) — carousel portrait_4x5 — 30% return deal
    obs("01KSE2JDGD7PW8C3JTBBNVYSGE",
        "DWd7YfgjNBx", "carousel", "2026-03-29", "sunday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["إذا اشتقنا لك", "NEXT30", "للي يستاهل يرجع"], True,
        "إذا اشتقنا لك بيتزاهت السعودية \n30% خصم مع كود NEXT30 للي يستاهل يرجع ويرجع بخصم🎉🍕", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Re-engagement promo — 'if we miss you, come back with 30% off'. Lapsed customer mechanic with promo code. Global QSR retention playbook.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "re-engagement 30% NEXT30 deal carousel"}],
        "low"),

    # 29 — DWb4kSmk-Ch — Mar 28 2026 (Sat) — video vertical_9x16 — empty plate = delicious
    obs("01KSE2JDGD7PW8C3JTBBNVYSGF",
        "DWb4kSmk-Ch", "video", "2026-03-28", "saturday", "vertical_9x16",
        "product_reveal_sequence", "natural mixed", ["cream","red","neutral"], "restaurant interior", "moderate",
        "arabic", "casual", "playful",
        ["اللذيذ تعرفه من شكل الطبق بعد الأكل"], False,
        "اللذيذ تعرفه من شكل الطبق بعد الأكل🍕✨😋", 2, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: 'You know it's delicious from the empty plate after eating'. Sensory-implied quality reel. No visual richness described. Generic global F&B social concept.",
        [{"pattern_slug": "close_up_macro_texture", "confidence": "weak", "notes": "implied quality via empty plate reveal"}],
        "medium"),

    # 30 — DWbdRK4gAio — Mar 28 2026 (Sat) — image portrait_4x5 — Giant Box gathering
    obs("01KSE2JDGD7PW8C3JTBBNVYSGG",
        "DWbdRK4gAio", "image", "2026-03-28", "saturday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "warm",
        ["إذا اللمة كبيرة", "الحب لازم يكون بحجمها", "جاينت بوكس"], True,
        "إذا اللمة كبيرة، الحب لازم يكون بحجمها،\nيعني جاينت بوكس من بيتزاهت🍕❤️", 2, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: Giant Box product showcase — 'if the gathering is big, the love must match its size'. Cultural gathering (لمة) word used as size-upsell mechanic. Warm tone but product-first.",
        [{"pattern_slug": "product_hero", "confidence": "strong", "notes": "Giant Box product image — size matches gathering size"}],
        "medium"),

    # 31 — DWZTm5YkxV6 — Mar 27 2026 (Fri) — video vertical_9x16 — CSR sign language reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSGH",
        "DWZTm5YkxV6", "video", "2026-03-27", "friday", "vertical_9x16",
        "documentary_csr", "natural mixed", ["red","white","neutral"], "restaurant interior", "moderate",
        "arabic", "casual", "caring",
        ["الطعم اللي تحبه", "البصمة اللي نفتخر فيها"], False,
        "الطعم اللي تحبه بالبصمة اللي نفتخر فيها 🤟🏼🧏🏼‍♂️", 2, True,
        [], "clean",
        "evergreen", "modern", ["accessible_workspace"],
        "Tier 4: CSR reel for accessible employment (#فرص_للجميع) — sign language and hearing-impaired staff. 'The taste you love with the imprint we're proud of'. Genuine CSR value, global QSR template.",
        [{"pattern_slug": "educational_explainer", "confidence": "moderate", "notes": "CSR reel — sign language accessible franchise employment"}],
        "medium"),

    # 32 — DWWaiFgDOsQ — Mar 26 2026 (Thu) — image portrait_4x5 — new crust product teaser
    obs("01KSE2JDGD7PW8C3JTBBNVYSGJ",
        "DWWaiFgDOsQ", "image", "2026-03-26", "thursday", "portrait_4x5",
        "product_hero", "cold_studio", ["cream","red","white"], "studio", "moderate",
        "arabic", "casual", "excitement",
        ["العجينة ما كانت رهيبة ما ينفع نكمل", "خفيفة على الكرش وثقيلة بطعمها"], False,
        "إذا العجينة ما كانت رهيبة\nما ينفع  نكمل🍕 \nعجينتنا الجديدة خفيفة على الكرش وثقيلة بطعمها😋🔥", 2, True,
        [], "clean",
        "evergreen", "modern", [], "Tier 4: New crust teaser image — 'if the dough isn't incredible, we can't continue'. Light on stomach but heavy on taste. Pre-campaign Italian crust teaser with no Saudi cultural frame.",
        [{"pattern_slug": "teaser_announcement", "confidence": "moderate", "notes": "new crust product teaser image"}],
        "medium"),

    # 33 — DWTpaPwjJMa — Mar 25 2026 (Wed) — image portrait_4x5 — 50% first order HUT50
    obs("01KSE2JDGD7PW8C3JTBBNVYSGK",
        "DWTpaPwjJMa", "image", "2026-03-25", "wednesday", "portrait_4x5",
        "product_hero", "cold_studio", ["red","white","cream"], "studio", "moderate",
        "arabic", "casual", "transactional",
        ["أول طلب بنص السعر", "ليه تقاوم؟", "HUT50"], True,
        "إذا أول طلب عليك بنص السعر\nليه تقاوم؟ 50% لاول طلب عبر التطبيق مع كود HUT50❤️🍕", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: 50% first-app-order HUT50 image. 'Why resist?' rhetorical hook. Pure transactional. Global QSR first-order acquisition mechanic.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "50% HUT50 first-app-order image"}],
        "low"),

    # 34 — DWRlqKGk-Wi — Mar 24 2026 (Tue) — video vertical_9x16 — dual deal reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSGM",
        "DWRlqKGk-Wi", "video", "2026-03-24", "tuesday", "vertical_9x16",
        "product_hero", "cold_studio", ["red","cream","white"], "studio", "simple",
        "arabic", "casual", "transactional",
        ["عرض الثنائي", "صفقة ما تتعوض"], True,
        "🤝🔥عرض الثنائي، صفقة ما تتعوض", 2, True,
        SOFT_DISCOUNT, "soft_flagged",
        "evergreen", "modern", [], "Tier 4: Dual deal reel. 'A deal that can't be replaced' — urgency framing. Minimal caption, product-focus. Pure discount.",
        [{"pattern_slug": "discount_price_dominant", "confidence": "strong", "notes": "dual deal reel — unbeatable deal claim"}],
        "low"),

    # 35 — DWE-HQGgMCS — Mar 19 2026 (Thu) — image portrait_4x5 — Eid Al-Fitr pizza post
    obs("01KSE2JDGD7PW8C3JTBBNVYSGN",
        "DWE-HQGgMCS", "image", "2026-03-19", "thursday", "portrait_4x5",
        "occasion_branded_hero", "warm product spotlight", ["red","white","gold"], "studio", "moderate",
        "arabic", "casual", "celebratory",
        ["العيد فرحة", "عيدية", "وكل عام وأنتم بخير"], False,
        "العيد فرحة وعيدية وخلاقين جديدة وبيتزا🍕✨ ​\nوكل عام وأنتم بخير 🌙🎉​", 3, True,
        [{"flag_type": "occasion_branding_without_cultural_depth",
          "description": "Eid greeting used as brand content without genuine celebration narrative"}],
        "soft_flagged",
        "eid_al_fitr", "modern", [], "Tier 4: Eid Al-Fitr branded image — 'Eid is joy, Eid money, new clothes and pizza'. Occasion acknowledge but pizza is listed alongside Eid traditions (not integrated into them). No cultural ritual storytelling.",
        [{"pattern_slug": "occasion_branded_hero", "confidence": "moderate", "notes": "Eid Al-Fitr brand image — occasion mentioned but not woven into product story"}],
        "medium"),

    # 36 — DV-9ayqDKoi — Mar 17 2026 (Tue) — carousel portrait_4x5 — Ramadan coverage
    obs("01KSE2JDGD7PW8C3JTBBNVYSGP",
        "DV-9ayqDKoi", "carousel", "2026-03-17", "tuesday", "portrait_4x5",
        "occasion_branded_hero", "warm studio", ["red","white","gold"], "studio", "moderate",
        "arabic", "casual", "warm",
        ["سواء كنت لحالك", "مع العائلة", "بيتزا هت مجهز لك رمضان بطريقته"], False,
        "سواء كنت لحالك، او مع العائلة او عزيمة فجأة،\nبيتزا هت مجهز لك رمضان بطريقته 🍕🌙✨", 3, True,
        [{"flag_type": "occasion_branding_without_cultural_depth",
          "description": "Ramadan coverage uses occasion but no iftar/suhoor/gathering cultural integration"}],
        "soft_flagged",
        "ramadan", "modern", [], "Tier 4: Ramadan coverage carousel — 'whether you're alone, with family, or a sudden invite, Pizza Hut is ready for Ramadan its own way'. Occasion acknowledged but no Arabic/Islamic cultural signals beyond 🌙 emoji.",
        [{"pattern_slug": "occasion_branded_hero", "confidence": "moderate", "notes": "Ramadan carousel — all scenarios covered but no authentic cultural warmth"}],
        "medium"),

    # 37 — DV6ctogk6QL — Mar 15 2026 (Sun) — video vertical_9x16 — Ramadan gathering reel
    obs("01KSE2JDGD7PW8C3JTBBNVYSGQ",
        "DV6ctogk6QL", "video", "2026-03-15", "sunday", "vertical_9x16",
        "occasion_branded_hero", "warm mixed", ["red","white","gold"], "natural", "moderate",
        "arabic", "casual", "warm",
        ["رمضان دايم يجمعنا", "تكتمل الجمعة لو كانت على بيتزاهت"], False,
        "رمضان دايم يجمعنا، وتكتمل الجمعة لو كانت على بيتزاهت🍕🌙✨", 3, True,
        [{"flag_type": "occasion_branding_without_cultural_depth",
          "description": "Ramadan gathering narrative with brand insertion but no cultural ritual integration"}],
        "soft_flagged",
        "ramadan", "modern", [], "Tier 4: Ramadan gathering reel — 'Ramadan always brings us together, the gathering is complete with Pizza Hut'. Gathering warmth (الجمعة) attempted but brand inserted awkwardly into Ramadan ritual. No iftar visual language.",
        [{"pattern_slug": "occasion_branded_hero", "confidence": "moderate", "notes": "Ramadan gathering reel — جمعة/gathering concept with brand CTA"}],
        "medium"),

    # 38 — DVwH5dgDOSF — Mar 11 2026 (Wed) — image portrait_4x5 — Saudi Flag Day post
    obs("01KSE2JDGD7PW8C3JTBBNVYSGR",
        "DVwH5dgDOSF", "image", "2026-03-11", "wednesday", "portrait_4x5",
        "occasion_branded_hero", "warm studio", ["green","white","red"], "studio", "moderate",
        "arabic", "formal", "patriotic",
        ["راية التوحيد", "قصة وطن ورمز للعزة"], False,
        "راية التوحيد، قصة وطن ورمز للعزة🇸🇦", 3, True,
        [{"flag_type": "occasion_branding_without_cultural_depth",
          "description": "Saudi Flag Day mentioned as caption but no product/brand integration or cultural storytelling"}],
        "soft_flagged",
        "saudi_flag_day", "modern", [], "Tier 4: Saudi Flag Day image — 'The flag of unification, a story of a nation and symbol of pride.' No Pizza Hut product in caption; brand posting on occasion to signal patriotism. Genuine occasion sentiment but disconnected from brand identity or cultural storytelling.",
        [{"pattern_slug": "occasion_branded_hero", "confidence": "strong", "notes": "Saudi Flag Day brand post — flag sentiment without product or cultural narrative"}],
        "medium"),

]

written = 0
for r in records:
    p = OUT / f"{r['observation_ulid']}.json"
    p.write_text(json.dumps(r, ensure_ascii=False, indent=2))
    written += 1

print(f"Written: {written} new observations for @pizzahutsaudi → {OUT}")
print(f"Total Ref-038 obs will be: 12 existing + {written} new = {12 + written}")
