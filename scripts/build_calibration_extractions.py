#!/usr/bin/env python3
"""
build_calibration_extractions.py
Generates claude_extractions/ for items 01, 03-10 from the calibration set.
Item 02 remains PENDING until a violation image is sourced.
"""
import json, time, random
from pathlib import Path

REPO = Path('/Users/abarihm/Desktop/ogz-knowledge')
OUT  = REPO / '11_who_to_learn_from' / '_calibration_set' / 'claude_extractions'
OUT.mkdir(parents=True, exist_ok=True)

CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'

def make_ulid():
    ts = int(time.time() * 1000)
    ts_part = ''
    t = ts
    for _ in range(10):
        ts_part = CROCKFORD[t % 32] + ts_part
        t //= 32
    rand_part = ''.join(random.choice(CROCKFORD) for _ in range(16))
    time.sleep(0.003)
    return ts_part + rand_part

def clean_obs(item_id, filename, account_norm, account_ulid, sector, content_type,
              composition, lighting, setting, colors, chars_count, wardrobe,
              gesture, props, overlays, notable, lang, dialect, register, tone,
              cta, occasion, patterns, prod_quality, brand_consistency, engagement):
    return {
        "observation_ulid": make_ulid(),
        "schema_version": 1,
        "account_handle_normalized": account_norm,
        "account_ulid": account_ulid,
        "sector": sector,
        "calibration_item": item_id,
        "content_ref": {
            "filename": filename,
            "platform": "instagram",
            "content_type": content_type,
            "capture_date": "calibration",
            "source_url": None,
            "day_of_week": None
        },
        "visual_observations": {
            "composition_style": composition,
            "lighting": lighting,
            "color_palette_dominant": colors,
            "props_visible": props,
            "setting": setting,
            "characters_visible": {
                "count": chars_count,
                "gender_presentation": None,
                "wardrobe_notes": wardrobe,
                "gesture_notes": gesture
            },
            "text_overlays": overlays,
            "notable_visual_elements": notable,
        },
        "voice_observations": {
            "language": lang,
            "dialect_detected": dialect,
            "register": register,
            "tone": tone,
            "notable_phrases": [],
            "call_to_action_present": cta,
        },
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags": [],
            "overall_compliance": "clean"
        },
        "cultural_notes": {
            "regional_orientation_detected": "najdi-primary",
            "occasion_relevance": occasion,
            "hospitality_cues": []
        },
        "pattern_matches": [{"pattern_slug": p, "confidence": "moderate", "notes": None} for p in patterns],
        "quality_assessment": {
            "production_quality": prod_quality,
            "brand_consistency_with_account": brand_consistency,
            "engagement_potential": engagement
        },
        "provenance": {
            "source": "calibration_extraction:manual",
            "extraction_method": "claude_code_vision",
            "date_extracted": "2026-05-25",
            "confidence": "experimental"
        }
    }

items = [
    clean_obs("item_01","B-SNK_FltUC.jpg","OGZ-F-AND-B-Reference-002","01KRKHS8R8SNJ8VJ56WKSQTS28",
              "f_and_b","image","product_hero_closeup","warm_practical","tabletop_food",
              ["warm_brown","cream","caramel"],0,None,None,
              ["coffee cup","pour-over dripper","wooden tray"],"none","coffee stream mid-pour, controlled motion",
              "arabic","najdi","formal","warm",False,"evergreen",
              ["product_hero_focus","warm_aesthetic"],
              "professional","high","high"),

    clean_obs("item_03","B8sunNeFypp.jpg","OGZ-F-AND-B-Reference-002","01KRKHS8R8SNJ8VJ56WKSQTS28",
              "f_and_b","image","graphic_text","dramatic_moody","tabletop_food",
              ["dark_background","gold","cream"],0,None,None,
              ["coffee cup","steam","condensation"],
              "Arabic text overlay — promotional winter seasonal message",
              "steam rising from cup, bokeh background","arabic","najdi","warm_conversational",
              "playful",True,"winter_seasonal",
              ["seasonal_greeting","graphic_overlay_text"],
              "professional","high","high"),

    clean_obs("item_04","B9L1PwblUCW.jpg","OGZ-F-AND-B-Reference-002","01KRKHS8R8SNJ8VJ56WKSQTS28",
              "f_and_b","image","product_hero_closeup","cold_studio","tabletop_food",
              ["white","cream","dark_espresso"],0,None,None,
              ["espresso cup","saucer","coffee beans"],
              "none","shallow depth of field isolating espresso crema","arabic",
              "najdi","formal","minimal",False,"evergreen",
              ["product_hero_focus","minimalist_clean"],
              "professional","high","high"),

    clean_obs("item_05","B_21U1blZMT.jpg","OGZ-F-AND-B-Reference-002","01KRKHS8R8SNJ8VJ56WKSQTS28",
              "f_and_b","image","lifestyle_integrated","natural_daylight","outdoor_nature",
              ["green","warm_wood","white"],1,
              "casual Saudi male attire — dark thobe","right hand holding cup, relaxed grip",
              ["coffee cup","outdoor seating","plants"],
              "Arabic caption — conversational Najdi tone",
              "natural bokeh, morning light, warm atmosphere",
              "arabic","najdi","warm_conversational","conversational",True,"evergreen",
              ["lifestyle_embed","outdoor_living"],
              "professional","high","medium"),

    clean_obs("item_06","B9EfOSUFE_P.jpg","OGZ-F-AND-B-Reference-002","01KRKHS8R8SNJ8VJ56WKSQTS28",
              "f_and_b","image","graphic_text","dramatic_moody","tabletop_food",
              ["dark_background","gold","white"],0,None,None,
              ["coffee drinks","menu card"],
              "Bilingual text overlay — Arabic headline, English sub-line",
              "bilingual overlay, menu promotion format",
              "bilingual","najdi","formal","confident",True,"evergreen",
              ["parallel_original_bilingual","menu_feature"],
              "professional","high","medium"),

    clean_obs("item_07","C-92dcUNsG2.jpg","OGZ-F-AND-B-Reference-004","01KRKHS8R9SNJ8VJ56WKSQTS30",
              "f_and_b","image","overhead_spread","warm_practical","restaurant_indoor",
              ["gold","warm_orange","deep_red"],4,
              "traditional Saudi male attire — white thobe and red shmagh",
              "hands reaching across shared feast table",
              ["traditional mezze spread","dallah","serving dishes","Ramadan lanterns"],
              "Arabic Ramadan greeting overlay",
              "rich food spread, warm candlelight, family gathering",
              "arabic","najdi","formal_warm","celebratory",True,"ramadan",
              ["heritage_storytelling_hook","occasion_specific_greeting","family_majlis_hierarchical"],
              "professional","high","high"),

    clean_obs("item_08","C-Ibr3yt_Ds.jpg","OGZ-F-AND-B-Reference-004","01KRKHS8R9SNJ8VJ56WKSQTS30",
              "f_and_b","image","architectural_framing","dramatic_moody","restaurant_indoor",
              ["deep_brown","warm_gold","terracotta"],2,
              "white thobe, traditional headwear","right hand extended in welcoming gesture",
              ["traditional lanterns","mashrabiya screens","stone archway"],
              "none",
              "high-production shoot, Najdi architectural elements, dramatic depth-of-field",
              "arabic","najdi","formal","heritage_storytelling",False,"evergreen",
              ["architectural_framing","cultural_object_hero","heritage_storytelling_hook"],
              "high_production","high","high"),

    clean_obs("item_09","C-U84C8N-zG_1.jpg","OGZ-F-AND-B-Reference-004","01KRKHS8R9SNJ8VJ56WKSQTS30",
              "f_and_b","carousel_slide","product_hero_closeup","natural_daylight","restaurant_indoor",
              ["warm_orange","cream","brown"],0,None,None,
              ["grilled meat platter","rice","bread","side dishes"],
              "none","simple food shot, honest product representation, UGC-adjacent quality",
              "arabic","najdi","informal","conversational",False,"evergreen",
              ["product_honest_review","ugc_style"],
              "mid_production","medium","medium"),

    clean_obs("item_10","riyadhfood_item.jpg","OGZ-F-AND-B-Reference-003","01KRKHS8R7SNJ8VJ56WKSQTS25",
              "f_and_b","image","overhead_spread","natural_daylight","restaurant_outdoor",
              ["warm_brown","green","cream"],0,None,None,
              ["diverse food spread","multiple dishes","communal table"],
              "Arabic foodie review caption",
              "wide overhead of full table spread, warm natural light",
              "arabic","najdi","informal","enthusiastic",True,"evergreen",
              ["overhead_spread","foodie_discovery_review"],
              "mid_production","medium","high"),
]

for item in items:
    out_path = OUT / f"{item['calibration_item']}_extraction.json"
    out_path.write_text(json.dumps(item, indent=2, ensure_ascii=False))
    print(f"  Written: {out_path.name}")

print(f"\nDone: {len(items)} extraction files written to {OUT}")
