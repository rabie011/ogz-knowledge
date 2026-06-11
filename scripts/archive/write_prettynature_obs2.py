#!/usr/bin/env python3
"""
write_prettynature_obs2.py
Observations 13-25 for @prettynature.official (beauty sector)
Account ULID: 01KRKHS8RFCFV3QA82P4D5VZMA
"""

import json, os

OUT_DIR = os.path.join(os.path.dirname(__file__), "../11_who_to_learn_from/observations/beauty")
os.makedirs(OUT_DIR, exist_ok=True)

ACCOUNT_ULID = "01KRKHS8RFCFV3QA82P4D5VZMA"
ACCOUNT_HANDLE_NORMALIZED = "OGZ-BEAUTY-Reference-002"
SECTOR = "beauty"


def obs(ulid, shortcode, content_type, capture_date,
        composition_style, lighting, colors, props, setting,
        chars_count, chars_gender, chars_dress, chars_gesture,
        overlays,
        language, dialect, register, tone, notable_phrases, cta,
        hard_blocks, soft_flags, compliance,
        region, occasion, hosp_cues, heritage, free_notes,
        patterns,
        prod_quality, brand_consistency, engagement_potential):

    char_node = {"count": chars_count}
    if chars_gender:
        char_node["gender_presentation"] = chars_gender
    if chars_dress:
        char_node["wardrobe_notes"] = chars_dress
    if chars_gesture:
        char_node["gesture_notes"] = chars_gesture

    record = {
        "observation_ulid": ulid,
        "schema_version": 1,
        "account_handle_normalized": ACCOUNT_HANDLE_NORMALIZED,
        "account_ulid": ACCOUNT_ULID,
        "sector": SECTOR,
        "content_ref": {
            "filename": f"{shortcode}.jpg",
            "platform": "instagram",
            "content_type": content_type,
            "capture_date": capture_date,
            "source_url": f"https://www.instagram.com/p/{shortcode}/"
        },
        "visual_observations": {
            "composition_style": composition_style,
            "lighting": lighting,
            "color_palette_dominant": colors,
            "props_visible": props,
            "setting": setting,
            "characters_visible": char_node,
            "text_overlays": overlays
        },
        "voice_observations": {
            "language": language,
            "dialect_detected": dialect,
            "register": register,
            "tone": tone,
            "notable_phrases": notable_phrases,
            "call_to_action_present": cta
        },
        "compliance_check": {
            "hard_blocks_triggered": hard_blocks,
            "soft_flags": soft_flags,
            "overall_compliance": compliance
        },
        "cultural_notes": {
            "regional_orientation_detected": region,
            "occasion_relevance": occasion,
            "hospitality_cues": hosp_cues
        },
        "pattern_matches": [
            {"pattern_slug": p["slug"], "confidence": p["conf"], "notes": p.get("notes")}
            for p in patterns
        ],
        "quality_assessment": {
            "production_quality": prod_quality,
            "brand_consistency_with_account": brand_consistency,
            "engagement_potential": engagement_potential
        },
        "provenance": {
            "source": f"benchmark:@prettynature.official; content:{shortcode}.jpg",
            "date_added": "2026-05-23T22:00:00Z",
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:beauty"
        }
    }
    return ulid, record


observations = [

    # 1 — DDWo17at2Kn — Rose Face Polish new product launch (Dec 09 2024)
    obs(
        "01KSB5QAHG12372P1JVZKHHPH8",
        "DDWo17at2Kn", "image", "2024-12-09",
        "product hero with nature elements — tube on moss rock water splash",
        "bright studio with nature-softened green gradient",
        ["sage green", "soft pink", "white", "brown"],
        ["rose face polish tube", "moss-covered rock", "water splash", "botanical leaves"],
        "natural/studio hybrid — product on mossy rock with flowing water",
        0, None, None, None,
        [{"language": "arabic", "content_summary": "جديد badge — new product; نظفي بشرتك / جددي إشراقتك (cleanse your skin / renew your radiance); Rose Face Polish label in English"}],
        "arabic", "khaleeji", "aspirational", "fresh",
        ["نظفي بشرتك", "جددي إشراقتك", "جديد"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "New launch post using nature-embedded hero — moss, water, botanical; Taif rose in product name (heritage ingredient in modern format)",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "tube centre frame, full product visibility"},
            {"slug": "seasonal_collection_drop", "conf": "moderate", "notes": "new product launch announcement with جديد badge"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 2 — DDRt-retemw — Rose Daily Cleanser new launch (Dec 07 2024)
    obs(
        "01KSB5QAHKB0SBBM164Y28QDW5",
        "DDRt-retemw", "image", "2024-12-07",
        "product hero with bubble/bokeh background",
        "bright studio with bokeh soap-bubble effect on green",
        ["sage green", "soft pink", "white"],
        ["rose daily cleanser tube", "soap bubbles floating", "dot-pattern corners"],
        "studio beauty shot — tube floating in bubble field",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "جديد badge; Rose Daily Cleanser label; Arabic 'غسول يومي طبيعي / لطف ونقاء بلمسة ورد طائفي' (natural daily cleanser / gentle purity with Taif rose touch)"}],
        "arabic", "khaleeji", "aspirational", "gentle",
        ["غسول يومي طبيعي", "ورد طائفي", "لطف ونقاء"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Taif rose (ورد طائفي) is Saudi heritage ingredient anchoring a modern skincare product. Bubble visual device common in Korean/global beauty aesthetic.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "tube centred, clean studio"},
            {"slug": "educational_explainer", "conf": "moderate", "notes": "caption details Taif rose + green tea + aloe vera ingredients"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 3 — DDJuLMCt48N — Rose Toner new launch (Dec 04 2024)
    obs(
        "01KSB5QAHPZDKDX10DS5HFT3QT",
        "DDJuLMCt48N", "image", "2024-12-04",
        "product hero inside large soap bubble sphere",
        "studio green with floating bubble/sphere elements",
        ["sage green", "peach", "amber", "white"],
        ["rose toner bottle (amber glass, 200ml)", "large translucent sphere bubble", "small floating bubbles"],
        "surreal/studio — product encased in soap bubble sphere",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "جديد badge; Rose Toner label; Arabic 'تونر الورد الطائفي الطبيعي / نقاوة وإشراقة ما لها مثيل' (Natural Taif Rose Toner / purity and radiance unmatched)"}],
        "arabic", "khaleeji", "aspirational", "elegant",
        ["تونر الورد الطائفي الطبيعي", "نقاوة وإشراقة ما لها مثيل"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Taif rose anchor in modern product; bubble sphere device elevates product hero to semi-editorial feel",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "bottle centred inside sphere, full label visible"},
            {"slug": "close_up_macro_texture", "conf": "moderate", "notes": "bubble sphere adds translucent liquid visual texture"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 4 — DDEltKRNQWJ — Full range on wood tray, ghosted Saudi woman (Dec 02 2024)
    obs(
        "01KSB5QAHR1KCQ18JJBFT5VH86",
        "DDEltKRNQWJ", "image", "2024-12-02",
        "full product range flat lay on wood tray with ghosted human backdrop",
        "soft studio green with white gradient at base",
        ["white", "sage green", "natural wood", "soft grey"],
        ["8-product range on wooden serving tray", "cream jars", "serums", "tubes", "bottles"],
        "studio product grouping — wooden tray elevates range, Saudi woman ghosted softly in background",
        1, "female", "hijab, modest dress (ghosted, soft blur)", None,
        [{"language": "arabic", "content_summary": "عناية من قلب الطبيعة / لبشرة تتألق من جديد (Care from the heart of nature / for skin that shines anew)"}],
        "arabic", "khaleeji", "aspirational", "warm",
        ["عناية من قلب الطبيعة", "لبشرة تتألق من جديد"],
        False,
        [],
        [{"flag_type": "face_visibility_moderate", "description": "Ghosted female face visible in background; modestly dressed with hijab but face partially shown — acceptable but note for audience sensitivity"}],
        "clean",
        "general_saudi", "none", [],
        "modern",
        "Wood tray as prop humanises and grounds brand in natural hospitality context. Caption 'من قلب الطبيعة' echoes brand name Pretty Nature. Ghosted woman: hijab worn, no hard block.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "full range displayed on wood tray"},
            {"slug": "specific_emotional_state", "conf": "moderate", "notes": "aspirational skin transformation framing"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 5 — DCjC7TrtWwf — White Friday promotion (Nov 19 2024)
    obs(
        "01KSB5QAHVJJ5JDTZXHDPNDP8C",
        "DCjC7TrtWwf", "image", "2024-11-19",
        "multi-product promo grid on circular podiums",
        "bright studio, sage green with vertical stripe texture",
        ["sage green", "soft pink", "peach", "white"],
        ["rose toner bottle", "two rose face polish tubes", "rose gel mask jar", "circular display podiums", "rose leaf prop"],
        "promotional studio layout — 4 products on stepped circular podiums",
        0, None, None, None,
        [{"language": "arabic", "content_summary": "بكج عناية من الورد الورد للورد (Rose care package — all rose); خصم 20% (20% discount); كود FIRST20 (code FIRST20); WHITE FRIDAY text vertical on side"}],
        "arabic", "khaleeji", "promotional", "exciting",
        ["بكج عناية من الورد", "خصم 20%", "WHITE FRIDAY"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "White Friday is the Saudi localisation of Black Friday — culturally appropriate. Rose bundle packaging plays on brand identity.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "four products displayed together as bundle"},
            {"slug": "seasonal_collection_drop", "conf": "strong", "notes": "White Friday sale promotion with discount code"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 6 — DCM5abGOFJQ — Singles Day (Singles' Day, Nov 10 2024)
    obs(
        "01KSB5QAHXBMFBKKWXMS6ADPXF",
        "DCM5abGOFJQ", "image", "2024-11-10",
        "3D rendered gift boxes on studio green",
        "dark forest green, dramatic studio lighting",
        ["forest green", "white", "olive gold", "terrazzo grey"],
        ["three 3D rendered gift boxes with olive ribbons", "gift bag silhouette"],
        "stylised studio — 3D rendered gift presentation no real product shown",
        0, None, None, None,
        [{"language": "arabic", "content_summary": "خصم 20% علي مجموعة الورد (20% on rose collection); بكود SINGLE20 (code SINGLE20); caption references يوم العزّاب (Singles Day)"}],
        "arabic", "khaleeji", "playful", "warm",
        ["يوم العزّاب", "دلّعي نفسك", "SINGLE20"],
        True,
        [],
        [{"flag_type": "western_occasion_import", "description": "Singles Day (Nov 11) is a Chinese/Western commercial occasion not rooted in Saudi calendar — soft flag for cultural fit mismatch"}],
        "clean",
        "general_saudi", "none", [],
        "modern",
        "Brand cleverly reframes Singles Day as self-care gifting. Caption 'إذا محد يهتم فيك، ترى بريتي موجودين' (if no one cares for you, Pretty Nature does) — emotional self-gifting hook.",
        [
            {"slug": "specific_emotional_state", "conf": "strong", "notes": "self-care / self-gifting emotional frame for solo consumers"},
            {"slug": "seasonal_collection_drop", "conf": "moderate", "notes": "occasion-pegged promo with discount code"},
        ],
        "semi_professional", "moderate", "medium"
    ),

    # 7 — DCB8oZ_NqNa — Guess-the-word engagement post (Nov 06 2024)
    obs(
        "01KSB5QAJ08M5RN35DXZ54KVFQ",
        "DCB8oZ_NqNa", "image", "2024-11-06",
        "ingredient close-up with gamified text overlay",
        "clean bright sage green studio",
        ["sage green", "brown", "white cream", "warm tan"],
        ["argan/shea nuts (2 whole + 1 cracked)", "wooden bowl with white shea butter", "letter 'ال' text overlay"],
        "ingredient spotlight — raw botanical against green BG",
        0, None, None, None,
        [{"language": "arabic", "content_summary": "خمّني الكلمة (guess the word); ال [letter clue for شيا/shea] — engagement mechanic inviting comments"}],
        "arabic", "khaleeji", "playful", "curious",
        ["خمّني الكلمة"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Gamified ingredient education: audience guesses the active ingredient (shea butter). Strong community engagement mechanic — comment-bait format. Ingredient close-up naturalises brand credentials.",
        [
            {"slug": "invitation_to_witness", "conf": "strong", "notes": "direct call to comment/guess — comment-bait community mechanic"},
            {"slug": "close_up_macro_texture", "conf": "strong", "notes": "raw shea/argan ingredients macro-photographed on clean BG"},
            {"slug": "educational_explainer", "conf": "moderate", "notes": "ingredient reveal educates audience about active ingredient"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 8 — DB8eyZQtIxe — Charcoal Face Wash (Nov 04 2024)
    obs(
        "01KSB5QAJ2EQCD423VVZ80WRTA",
        "DB8eyZQtIxe", "image", "2024-11-04",
        "product hero on circular white platform with water foam",
        "sky blue gradient, cloud-like soft background",
        ["sky blue", "white", "light grey"],
        ["charcoal face wash pump bottle (white, 200ml)", "circular white platform", "foam/water droplets", "charcoal icon on bottle"],
        "studio sky aesthetic — product elevated on white disc over sky-blue ground",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "charcoal face wash label in English; Arabic 'بشرة منتعشة وصحية / يزيل الشوائب / ينظف المسام' (refreshed healthy skin / removes impurities / cleanses pores)"}],
        "arabic", "khaleeji", "informative", "confident",
        ["يزيل الشوائب", "ينظف المسام", "بشرة منتعشة وصحية"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Charcoal cleanser category — no cultural conflict. Sky/cloud BG reinforces 'fresh' and 'clean' brand promise. Bilingual product name signals cosmopolitan Saudi DTC brand.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "pump bottle centred on elevated white platform"},
            {"slug": "educational_explainer", "conf": "strong", "notes": "caption details oily skin targeting, deep pore cleaning use case"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 9 — DB3U0z3Nbos — Jasmine Hand & Face Cream, hands applying (Nov 02 2024)
    obs(
        "01KSB5QAJ5QRP9RRPKCRK76FA2",
        "DB3U0z3Nbos", "image", "2024-11-02",
        "product lifestyle with hands-in-use and botanical prop",
        "clean white/cream studio with soft shadow",
        ["sky blue", "white", "light blue", "green"],
        ["jasmine hand and face cream tube (light blue)", "aloe vera plant", "cream swirl on surface"],
        "lifestyle beauty shot — two hands applying cream with product and aloe prop",
        1, "female", "bare hands only visible — modest, no jewellery", "gentle cream application (right hand over left)",
        [{"language": "bilingual", "content_summary": "hand and face cream label; Arabic 'غني بزبدة المانجو وزيت الأرجان' (rich in mango butter and argan oil)"}],
        "arabic", "khaleeji", "aspirational", "gentle",
        ["زبدة المانجو", "زيت الأرجان", "رائحة الياسمين الفواحة"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Hands-in-use lifestyle shot — shows product in action without full model. Right-hand dominance in application visible (no left-hand serving issue — it is passive/supporting). Jasmine and argan oil heritage ingredients.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "product tube featured with in-use lifestyle hands"},
            {"slug": "hand_in_motion_pour_or_place", "conf": "strong", "notes": "hands actively applying cream — usage demonstration"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 10 — DBvfu67tOig — Cuticle Oil, elegant hand holding bottle (Oct 30 2024)
    obs(
        "01KSB5QAJ7RV3MB3KQ050N3Z31",
        "DBvfu67tOig", "image", "2024-10-30",
        "product-and-hand hero — bottle held by elegant fingers",
        "clean silver-grey studio, soft shadow",
        ["light grey", "white", "cream/beige", "pale green"],
        ["cuticle oil bottle (small white glass, 20ml)", "plant botanical label on bottle", "manicured female hand"],
        "beauty editorial — hand holding product against clean grey",
        1, "female", "bare hand with neat manicure, no jewellery visible", "right hand holding bottle upright (no pour/application)",
        [{"language": "bilingual", "content_summary": "cuticle oil label in English; Arabic 'ترطيب وتغذية للأظافر والجلد المحيط بها' (moisturises and nourishes nails and surrounding skin)"}],
        "arabic", "khaleeji", "informative", "elegant",
        ["ترطيب وتغذية للأظافر", "الجلد المحيط بها"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Cuticle oil is a niche product — educational caption details niche use. Botanical minimalist label design signals premium DTC positioning. Editorial hand-hold shot consistent with brand visual identity.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "bottle featured front-centre held by hand"},
            {"slug": "hand_in_motion_pour_or_place", "conf": "moderate", "notes": "hand pose frames product elegantly though not in active pour"},
        ],
        "professional", "strong", "medium"
    ),

    # 11 — DBs9ccrtjQg — Raspberry Body Butter jar (Oct 29 2024)
    obs(
        "01KSB5QAJA7YP0V97MWSJPWKHA",
        "DBs9ccrtjQg", "image", "2024-10-29",
        "product hero on elevated podium — two-tone studio background",
        "split green/yellow studio with geometric shadows",
        ["forest green", "olive yellow", "white cream", "warm brown"],
        ["raspberry body butter jar (270g, white with raspberry icon)", "circular podium"],
        "studio product hero — jar on pedestal, split colour wall behind",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "body butter label + Raspberry Body Butter in English; Arabic 'ترطب وتنعم بعمق / رائحة منعشة' (deep moisture and softness / refreshing scent)"}],
        "arabic", "khaleeji", "aspirational", "sensory",
        ["ترطب وتنعم بعمق", "رائحة منعشة"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Split background with geometric shadow creates dramatic studio feel. Body butter category is strong in Saudi beauty market (dry climate). Raspberry scent is a Western appeal but product suits local need.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "jar on podium, full label visible"},
            {"slug": "color_block_branded_flood", "conf": "moderate", "notes": "split green/yellow BG creates colour-dominant composition"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 12 — DBqVjQCt8tz — Fragrance-free Lip Balm (Oct 28 2024)
    obs(
        "01KSB5QAJCJ7N8D0THV3R41V3E",
        "DBqVjQCt8tz", "image", "2024-10-28",
        "product hero with water splash dynamic",
        "clean white/light grey studio with water splash elements",
        ["teal", "white", "light grey", "silver water"],
        ["lip balm stick (teal, 3ml)", "water splash droplets", "water crystals scattered"],
        "studio dynamic — product surrounded by water splash for freshness",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "Lip balm label in English; Arabic 'خالي من العطور / يرطب ويغذي' (fragrance-free / moisturises and nourishes); ingredients listed in Arabic and English"}],
        "arabic", "khaleeji", "informative", "clean",
        ["خالي من العطور", "يرطب ويغذي", "البشرة الحساسة"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Fragrance-free claim targets sensitive skin — a specific positioning message. Water splash adds kinetic energy to small product. Teal colour differentiates from brand's dominant pink/green palette.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "lip balm centred with water splash backdrop"},
            {"slug": "close_up_macro_texture", "conf": "moderate", "notes": "water droplets and splash create macro liquid texture"},
            {"slug": "specific_over_impressive", "conf": "moderate", "notes": "fragrance-free specific claim targets sensitive skin segment"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 13 — DBn03_FNYxI — Taif Rose Face Wash, new product, daisy flowers (Oct 27 2024)
    obs(
        "01KSB5QAJF1SPYBAP50NXA8SQR",
        "DBn03_FNYxI", "image", "2024-10-27",
        "product hero angled on pedestal with scattered daisy props",
        "clean light grey studio with delicate floral props",
        ["soft pink", "light grey", "white", "sage green accents"],
        ["rose daily cleanser tube (pink, angled on circular pedestal)", "scattered daisy flowers", "grey arch backdrop element"],
        "editorial product placement — angled tube on pedestal with botanical flowers",
        0, None, None, None,
        [{"language": "bilingual", "content_summary": "جديدنا badge (our new product); Face wash label; Arabic 'تنظيف عميق / بشرة رطبة' (deep cleansing / moisturised skin)"}],
        "arabic", "khaleeji", "aspirational", "fresh",
        ["تنظيف عميق", "بشرة رطبة", "جديدنا"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Daisy flowers add feminine botanical softness to new-product announcement. Angled tube framing is more editorial than straight-on hero. 'جديدنا' (our new) creates brand intimacy vs generic 'جديد'.",
        [
            {"slug": "product_hero", "conf": "strong", "notes": "tube angled on pedestal, centred composition"},
            {"slug": "seasonal_collection_drop", "conf": "strong", "notes": "new product announcement with جديدنا badge"},
        ],
        "semi_professional", "strong", "medium"
    ),

]


for ulid, record in observations:
    path = os.path.join(OUT_DIR, f"{ulid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"  wrote {ulid}.json  [{record['content_ref']['filename']}]")

print(f"\nDone — {len(observations)} observations written to {OUT_DIR}")
