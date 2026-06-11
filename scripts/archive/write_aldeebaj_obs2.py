#!/usr/bin/env python3
"""
write_aldeebaj_obs2.py
Observations 13-25 for @aldeebajofficial (retail sector)
Account ULID: 01KRKHS8RBHMMSCHPYWXGGFKNT
Note: Al Deebaj is a Pakistani modest-fashion brand with broad Muslim market reach (Saudi/Gulf/Pakistan).
"""

import json, os

OUT_DIR = os.path.join(os.path.dirname(__file__), "../11_who_to_learn_from/observations/retail")
os.makedirs(OUT_DIR, exist_ok=True)

ACCOUNT_ULID = "01KRKHS8RBHMMSCHPYWXGGFKNT"
ACCOUNT_HANDLE_NORMALIZED = "OGZ-RETAIL-Reference-001"
SECTOR = "retail"


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
            "source": f"benchmark:@aldeebajofficial; content:{shortcode}.jpg",
            "date_added": "2026-05-23T22:00:00Z",
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:retail"
        }
    }
    return ulid, record


observations = [

    # 1 — DYXpXxpIEUD — Cairo Collection thobe, single model in Islamic arch (May 15)
    obs(
        "01KSB647PEERHEFAH7JEAKWK40",
        "DYXpXxpIEUD", "video", "2026-05-15",
        "model hero in editorial Islamic interior — single full-length",
        "natural daylight, bright interior with white arch, airy",
        ["light grey", "white", "warm sand", "black accents"],
        ["grey hooded thobe", "Islamic mashrabiya arch panel", "pampas grass arrangement", "wicker chair", "black leather loafers"],
        "stylised home/interior setting — Islamic arch doorway with arabesque lattice, modern modest aesthetic",
        1, "male", "grey hooded thobe with black trim, loafers, sunglasses in hand", "holding sunglasses downward, walking pose, neutral stance",
        [{"language": "english", "content_summary": "Minimal design. Premium feel. Powerful presence. Discover the all-new Cairo Collection Thobes"}],
        "english", "none",  "aspirational", "confident",
        ["Minimal design. Premium feel. Powerful presence.", "Cairo Collection"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Cairo Collection frames Moroccan/North African thobe silhouette (hood) for Gulf/Saudi market. Islamic arch and arabesque props signal heritage setting within modern modest fashion aesthetic. English-dominant caption.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "single full-body model in editorial arch setting"},
            {"slug": "seasonal_collection_drop", "conf": "strong", "notes": "Cairo Collection new product launch announcement"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 2 — DYXQFl2IGdz — CAIRŌ split editorial image (May 15)
    obs(
        "01KSB647PHNXVPWADR6Y6835JE",
        "DYXQFl2IGdz", "image", "2026-05-15",
        "split-panel editorial — studio top half + interior setting bottom half",
        "clean studio white (top) / warm interior (bottom)",
        ["white", "brown", "warm sand", "off-white"],
        ["brown hooded thobe", "CAIRŌ collection branding typography", "white ceramic vase", "Islamic arch interior"],
        "composite editorial layout — split between catalogue studio and lifestyle interior",
        1, "male", "brown hooded thobe with embroidery, round sunglasses at eye level", "hand raising sunglasses to eye level — stylish gesture",
        [{"language": "english", "content_summary": "MODEST THOBES heading; CAIRŌ collection name; product showcased in dual context"}],
        "english", "none", "aspirational", "sophisticated",
        ["MODEST THOBES", "CAIRŌ"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Split panel format creates editorial magazine feel — studio flatness above, warmth below. CAIRŌ branding evokes Arab world heritage (Egypt) to position product culturally beyond Pakistan origin.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "full-length model featured in both panels"},
            {"slug": "split_screen_before_after", "conf": "moderate", "notes": "two-panel layout contrasts studio and lifestyle contexts"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 3 — DYXC4XDzPu6 — Cairo Collection duo shot, grey + taupe thobes (May 15)
    obs(
        "01KSB647PMV8W3BWV4F0MXHN5H",
        "DYXC4XDzPu6", "image", "2026-05-15",
        "duo model portrait — two full-length models side by side",
        "bright studio with Islamic mashrabiya arch, natural daylight",
        ["light grey", "taupe brown", "white", "warm sand"],
        ["grey hooded thobe", "taupe hooded thobe", "Islamic mashrabiya arch backdrop", "pampas grass"],
        "editorial studio with Islamic arch — two-model product catalogue",
        2, "male", "grey hooded thobe (left) + taupe hooded thobe (right), both with round sunglasses", "left: hands clasped at front (modest); right: open-hand gesture outward",
        [{"language": "english", "content_summary": "Caption: Inspired by timeless Arab elegance. Cairo Collection by Al Deebaj — crafted for men who carry sophistication effortlessly"}],
        "english", "none", "aspirational", "elegant",
        ["timeless Arab elegance", "Cairo Collection"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Two colour variants shown together — standard retail catalogue approach for modest menswear. Islamic arch and arabesque latticework props reinforce Arab cultural positioning. 'Arab elegance' caption claim explicitly anchors brand in Arab identity.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "full-length duo model shot for product catalogue"},
            {"slug": "seasonal_collection_drop", "conf": "moderate", "notes": "Cairo Collection new arrival featured"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 4 — DYXCeOgTOMd — Cairo Collection duo, cream + chocolate thobes (May 15)
    obs(
        "01KSB647PQA2ETA5AFQBKN4J3E",
        "DYXCeOgTOMd", "image", "2026-05-15",
        "duo model portrait — two full-length models, one closer to camera",
        "bright studio, Islamic arch and ceramic vases backdrop",
        ["cream", "chocolate brown", "white", "warm sand"],
        ["cream hooded thobe with embroidery", "chocolate brown hooded thobe", "Islamic arch", "tall white ceramic vases", "pampas grass"],
        "editorial studio — Islamic heritage setting with elegant ceramic props",
        2, "male", "cream hooded thobe with embroidered placket (background) + dark chocolate hooded thobe (foreground), round sunglasses", "foreground model facing camera directly; background slightly turned",
        [{"language": "english", "content_summary": "This Eid, wear elegance. Premium Jubbahs by Al Deebaj — timeless style, premium quality and unbeatable value"}],
        "english", "none", "aspirational", "occasion-driven",
        ["This Eid, wear elegance", "Premium Jubbahs"],
        True,
        [], [], "clean",
        "general_saudi", "eid", [],
        "blended",
        "Eid occasion pegged — premium jubbah positioning. Cream variant shows embroidery detail. Foreground-background layering adds depth. Same set as other Cairo Collection shots — efficient campaign production.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "duo model portrait, Eid-positioned campaign"},
            {"slug": "eid_collection_reveal", "conf": "strong", "notes": "explicit Eid occasion tie-in with premium positioning"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 5 — DYXAVZqN6Bz — Brand spokesperson video for Islamic caps (May 15)
    obs(
        "01KSB647PTXDDFN4FCKRKZS5H4",
        "DYXAVZqN6Bz", "video", "2026-05-15",
        "talking-head spokesperson — upper body, direct address to camera",
        "blue/teal gradient studio, cinematic warmth",
        ["blue", "teal", "white", "dark"],
        ["bearded man in white thobe", "black knitted Islamic cap (taqiyah/kufi)", "leather office chair", "blue gradient backdrop"],
        "brand studio — spokesperson seated at desk addressing camera directly",
        1, "male", "white thobe/qamis, black knitted Islamic kufi, wristwatch", "hands clasped in front of chest, engaged expression, speaking",
        [{"language": "english", "content_summary": "Premium Islamic Caps By Al Deebaj — Top off your Sunnah style with premium elegance; link to website"}],
        "english", "none", "informative", "authoritative",
        ["Sunnah style", "premium elegance", "Islamic Caps"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Spokesperson format builds brand trust through direct-address authority. Wearing the product (kufi cap) while presenting it is authentic product testimonial. 'Sunnah style' framing anchors product in Islamic religious practice.",
        [
            {"slug": "invitation_to_witness", "conf": "strong", "notes": "direct-camera address invites audience into brand world"},
            {"slug": "product_hero", "conf": "moderate", "notes": "Islamic cap featured on presenter as wearable product demo"},
        ],
        "semi_professional", "moderate", "medium"
    ),

    # 6 — DYW0EaAOe-P — Beige abaya lifestyle, woman at café from behind (May 15)
    obs(
        "01KSB647PXKR8S4B04FQ260H4Z",
        "DYW0EaAOe-P", "video", "2026-05-15",
        "lifestyle candid — woman from behind at modern café setting",
        "bright natural daylight, glass and metal modern interior",
        ["beige", "blush", "light grey", "white"],
        ["beige/blush abaya with tiered skirt", "matching full hijab (niqab-style, face covered)", "iced beverage with red straw", "wooden café chair", "leather crossbody bag"],
        "modern café/commercial interior — candid lifestyle moment",
        1, "female", "beige/blush full-cover abaya, niqab covering face, crossbody bag", "seated, holding iced drink — relaxed lifestyle pose",
        [{"language": "english", "content_summary": "Effortless elegance in every detail. Beautiful beige abaya with attached inner — perfect flow, timeless charm, everyday luxury. By Al Deebaj"}],
        "english", "none", "aspirational", "relaxed",
        ["Effortless elegance", "everyday luxury", "timeless charm"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "From-behind candid eliminates face visibility — maximum modesty compliance. Iced beverage in modern café setting signals aspirational urban Saudi/Gulf lifestyle. No face shown enables wide audience relatability across conservative spectrum.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "moderate", "notes": "model is primary focus though shot from behind — lifestyle framing"},
            {"slug": "warm_golden_hour_hero", "conf": "moderate", "notes": "natural daylight through glass creates warm aspirational ambience"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 7 — DYTKbBTIP_I — Faizan Shaikh influencer in Madinah streets (May 14)
    obs(
        "01KSB647Q0P17VSHSJ9QR21XGS",
        "DYTKbBTIP_I", "video", "2026-05-14",
        "documentary street scene — influencer in Madinah",
        "bright outdoor daylight, Madinah urban streetscape",
        ["black", "grey", "warm stone", "blue sky"],
        ["black thobe/jubbah", "black knitted kufi cap", "pigeons on street", "Madinah hotel buildings in BG", "plastic bread bag"],
        "Madinah street — authentic urban religious city environment near Masjid al-Nabawi",
        1, "male", "black thobe, black kufi, glasses, tactical bag, white Adidas slides", "feeding pigeons with right hand — relaxed, natural",
        [{"language": "english", "content_summary": "MashaAllah — Faizan Shaikh spotted wearing Al Deebaj Thobe in the beautiful streets of Madinah. A moment of style, simplicity and sunnah together"}],
        "english", "none", "authentic", "reverent",
        ["MashaAllah", "streets of Madinah", "style, simplicity and sunnah"],
        True,
        [],
        [{"flag_type": "religious_city_as_brand_context", "description": "Madinah streets used as brand backdrop — reverent religious city; not Kaaba/Mecca (not hard block) but warrants editorial care in campaign use"}],
        "clean",
        "general_saudi", "none", [],
        "blended",
        "Influencer UGC-style content: Faizan Shaikh (Muslim content creator) organically wearing brand in Madinah. 'Style, simplicity and sunnah' tagline trio is powerful Islamic positioning. Madinah setting adds spiritual authenticity — high emotional resonance for target audience.",
        [
            {"slug": "documentary_btsmoment", "conf": "strong", "notes": "candid influencer moment in real-world religious city environment"},
            {"slug": "invitation_to_witness", "conf": "moderate", "notes": "MashaAllah framing invites audience to witness a blessed/inspiring moment"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 8 — DYTKIYsogLg — Moroccan Thobe collection, trio group at night (May 14)
    obs(
        "01KSB647Q3V89CY9KC9NB0E27D",
        "DYTKIYsogLg", "video", "2026-05-14",
        "group model shot — three models in garden at night",
        "night exterior lighting, warm ambient, garden/olive trees",
        ["black", "white cream", "dark navy", "green foliage"],
        ["three jubbahs/thobes (black, cream, navy)", "olive tree backdrop", "tile flooring", "terrace/garden setting"],
        "night garden exterior — three-model editorial group for Moroccan collection",
        3, "male", "black jubbah (left), cream/white jubbah (centre), dark navy jubbah with embroidery (right), all with sandals/loafers", "grouped pose — centre model hands clasped; right arm on shoulder of centre",
        [{"language": "english", "content_summary": "Introducing the Moroccan Thobe by Al Deebaj — where timeless tradition meets modern elegance. Premium fabric, graceful fit and a look that speaks class"}],
        "english", "none", "aspirational", "ceremonial",
        ["timeless tradition meets modern elegance", "Moroccan Thobe", "speaks class"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Three-model group creates collective masculine modest fashion statement. Night exterior with olive trees adds cultural warmth. Moroccan thobe silhouette (hooded, embroidery) bridges North African and Gulf modest fashion traditions.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "three-model group centred in frame — product catalogue with diversity"},
            {"slug": "seasonal_collection_drop", "conf": "strong", "notes": "Moroccan Thobe collection introduction announcement"},
        ],
        "semi_professional", "strong", "high"
    ),

    # 9 — DYSI4sKiIGA — Eid Jubbahs catalogue, three models studio, price overlay (May 13)
    obs(
        "01KSB647Q6B8ZAWHMSX53E305N",
        "DYSI4sKiIGA", "carousel_slide", "2026-05-13",
        "product catalogue studio — three full-body models on white",
        "clean white studio, bright even lighting",
        ["grey blue", "cream off-white", "dark navy", "white"],
        ["grey jubbah (left model)", "cream jubbah (centre, no sunglasses)", "dark navy jubbah (right)", "price badge Rs.4999"],
        "clean white studio catalogue — three-model product shot with price display",
        3, "male", "grey jubbah (left, sunglasses), cream jubbah (centre, no glasses, looking directly), dark navy jubbah (right, sunglasses)", "left: one arm folded; centre: sunglasses in hand downward; right: one hand on hip",
        [{"language": "english", "content_summary": "Wear Jubba This Eid! Rs.4999 Only"}],
        "english", "none", "promotional", "direct",
        ["Wear Jubba This Eid!", "Rs.4999 Only"],
        True,
        [],
        [{"flag_type": "non_saudi_currency", "description": "Price shown in Pakistani Rupees (Rs.4999) — confirms primary market is Pakistan, not Saudi Arabia; may create confusion for Saudi audience"}],
        "clean",
        "general_saudi", "eid", [],
        "modern",
        "Eid-peg + fixed price proposition. Pakistani Rupee pricing confirms brand origin. Three-model shot is standard D2C modest fashion catalogue formula. Simple 'Wear Jubba This Eid' CTA is direct and occasion-relevant.",
        [
            {"slug": "model_centered_frontal_portrait", "conf": "strong", "notes": "three models in clean studio for Eid collection price presentation"},
            {"slug": "eid_collection_reveal", "conf": "strong", "notes": "explicit Eid occasion call-to-action with price point"},
        ],
        "semi_professional", "moderate", "high"
    ),

    # 10 — DYSA8kyoZfY — Floral blue abaya, fabric detail tripartite video (May 13)
    obs(
        "01KSB647Q940N6M934DB73C9VE",
        "DYSA8kyoZfY", "video", "2026-05-13",
        "tripartite vertical strip composition — fabric macro, back view, accessory",
        "bright interior natural light, minimal white setting",
        ["sky blue", "white", "light grey", "black"],
        ["blue floral chiffon abaya", "matching blue floral hijab", "black chain crossbody bag"],
        "modern minimalist interior — three-panel strip showing garment details",
        1, "female", "light blue floral chiffon abaya, matching floral hijab (face not shown — back view)", "walking away from camera (back view), handbag in right hand",
        [{"language": "english", "content_summary": "Elegance in every fold — Wrapped in grace, styled with soul by @aldeebajofficial"}],
        "english", "none", "aspirational", "graceful",
        ["Elegance in every fold", "Wrapped in grace, styled with soul"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "modern",
        "Tripartite strip is an editorial technique common in fashion reels — shows fabric texture, full silhouette, accessory detail. Blue floral print is feminine and modest. Back-view protects model identity while showcasing garment drape.",
        [
            {"slug": "close_up_macro_texture", "conf": "strong", "notes": "top panel shows floral chiffon fabric macro — texture detail"},
            {"slug": "model_centered_frontal_portrait", "conf": "moderate", "notes": "middle panel shows full back-view silhouette of model in abaya"},
        ],
        "semi_professional", "strong", "medium"
    ),

    # 11 — DYR5kPIIrY2 — Woman in embroidered abaya pouring tea, gold teapot (May 13)
    obs(
        "01KSB647QDR50JBC58J0JDAD55",
        "DYR5kPIIrY2", "video", "2026-05-13",
        "lifestyle product scene — woman serving tea with embroidered abaya in frame",
        "warm soft interior light, beige/cream tones",
        ["mint green", "gold", "white", "red", "beige"],
        ["mint green embroidered abaya", "ornate gold-trimmed porcelain teapot", "white teacup", "marble and gold serving tray", "red roses", "hands with light blue nail polish"],
        "elegant home interior — tea service moment with luxury props",
        1, "female", "mint green embroidered abaya with silver floral embroidery on sleeve cuffs (face not shown)", "right hand reaching to ornate teapot lid — graceful serving motion",
        [{"language": "english", "content_summary": "Formal Abaya @aldeebajofficial — no further caption text (hashtags only)"}],
        "english", "none", "aspirational", "elegant",
        ["Formal Abaya"],
        True,
        [], [], "clean",
        "general_saudi", "none",
        ["gold porcelain dallah-adjacent teapot", "marble serving tray", "red roses — hospitality ritual staging"],
        "blended",
        "Tea service moment is Saudi/Gulf hospitality code — linking abaya to the graceful hosting role. Gold-trimmed teapot echoes Saudi dallah (coffee pot) aesthetic. Red roses add femininity. Face never shown — full modesty compliance. Right hand in active serving posture.",
        [
            {"slug": "warm_golden_hour_hero", "conf": "moderate", "notes": "warm indoor ambience with gold props elevates to golden-hour emotional register"},
            {"slug": "hand_in_motion_pour_or_place", "conf": "strong", "notes": "right hand reaching to teapot in graceful serving motion"},
        ],
        "professional", "strong", "high"
    ),

    # 12 — DYJ5X-YtGD2 — Arabic fragrance for Jubbah, in-store product demo (May 10)
    obs(
        "01KSB647QGHWY3CMPK00R2F6X3",
        "DYJ5X-YtGD2", "video", "2026-05-10",
        "in-store product demonstration — bearded presenter spraying fragrance",
        "interior retail store lighting, warm ambient",
        ["blue grey", "dark brown", "white", "warm wood"],
        ["blue jubbah/thobe", "fragrance spray bottle", "glass display case", "retail shelving with products", "wall clock"],
        "Al Deebaj retail store interior — behind-the-counter product demonstration",
        1, "male", "blue jubbah with dark embroidery on chest, ring on finger", "spraying perfume from bottle toward camera/viewer",
        [{"language": "english", "content_summary": "An Arabic fragrance for Jubbah — hashtag fragrance, perfume, viral reels"}],
        "english", "none", "informative", "inviting",
        ["Arabic fragrance for Jubbah"],
        True,
        [], [], "clean",
        "general_saudi", "none", [],
        "blended",
        "Cross-sell mechanic: pairing jubbah garment with branded Arabic fragrance. In-store setting adds authenticity. 'Arabic fragrance' claim anchors product in regional identity. Store environment with wooden shelving evokes traditional retail warmth.",
        [
            {"slug": "documentary_btsmoment", "conf": "strong", "notes": "in-store candid demonstrating product within real retail environment"},
            {"slug": "product_hero", "conf": "moderate", "notes": "fragrance bottle featured as product extension for jubbah wearers"},
        ],
        "semi_professional", "moderate", "medium"
    ),

    # 13 — DYHpyA4CJ5I — Mother's Day carousel opener, Urdu branding (May 09)
    obs(
        "01KSB647QKW9262PEJCKJAXNNS",
        "DYHpyA4CJ5I", "carousel_slide", "2026-05-09",
        "branded announcement slide — typographic with floral illustration",
        "clean white studio, bright",
        ["white", "pink", "light pink", "green"],
        ["Al Deebaj Arabic logo", "flower bouquet illustration (daisy/carnation)", "bold typographic layout", "arrow CTA pointing down"],
        "clean white brand announcement slide — first carousel panel",
        0, None, None, None,
        [{"language": "english", "content_summary": "AMMI KI PASAND (Urdu: Mother's choice); LOOK AT THE BOTTOM; AVAIL UPTO 40% ON MOTHER'S DAY; Al Deebaj Arabic logo"}],
        "english", "none", "promotional", "warm",
        ["AMMI KI PASAND", "AVAIL UPTO 40% ON MOTHER'S DAY"],
        True,
        [],
        [{"flag_type": "urdu_primary_language", "description": "AMMI KI PASAND is Urdu (Pakistani/South Asian) — confirms brand's primary market is Pakistani diaspora; not Arabic-first for Saudi audience"},
         {"flag_type": "western_occasion_import", "description": "Mother's Day is a Western/global commercial occasion not rooted in Islamic or Saudi calendar"}],
        "clean",
        "general_saudi", "none", [],
        "modern",
        "AMMI KI PASAND (Urdu: mother's choice) reveals brand's Pakistani-first identity. This is a strong cultural signal — Al Deebaj positions itself for Muslim South Asian audience, not exclusively Saudi. Mother's Day discount up to 40% is aggressive promotional mechanic. Arrow CTA invites carousel engagement.",
        [
            {"slug": "seasonal_collection_drop", "conf": "strong", "notes": "Mother's Day occasion-pegged promotional carousel launch"},
            {"slug": "invitation_to_witness", "conf": "moderate", "notes": "arrow and 'look at the bottom' mechanics invite carousel scroll — engagement driver"},
        ],
        "semi_professional", "moderate", "medium"
    ),

]


for ulid, record in observations:
    path = os.path.join(OUT_DIR, f"{ulid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"  wrote {ulid}.json  [{record['content_ref']['filename']}]")

print(f"\nDone — {len(observations)} observations written to {OUT_DIR}")
