#!/usr/bin/env python3
"""
Day 3 / Task 3.3 — Generate 15 cultural-spec files:
  - 8 sector_defaults YAMLs (validate against cultural_spec_v1.schema.json)
  - 4 forbidden_lists YAMLs (universal hard-blocks; no formal schema)
  - 3 advisor_playbook markdown docs

All marked `confidence: experimental` pending Cultural Advisor review.

Strategy: define BASE 80-field templates per sector, OVERLAY regional/style variants.
Most fields share across variants; only the truly differing fields are overridden.
"""
from __future__ import annotations
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ulid import ULID

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "15_cultural_specs"
(ROOT / "sector_defaults").mkdir(parents=True, exist_ok=True)
(ROOT / "forbidden_lists").mkdir(parents=True, exist_ok=True)
(ROOT / "advisor_playbook").mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def existing_ulid(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text())
        return data.get(key) if isinstance(data, dict) else None
    except Exception:
        return None


def mint_or_preserve(path: Path, key: str = "cultural_spec_ulid") -> str:
    return existing_ulid(path, key) or str(ULID())


def provenance(source: str, scope: str) -> dict:
    return {
        "source": source,
        "date_added": NOW,
        "confirmer": "Mohamed",
        "confidence": "experimental",
        "scope": scope,
    }


# ───────────────────────────────────────────────────────────────────────────
# Universal forbidden lists (referenced by every spec)
# ───────────────────────────────────────────────────────────────────────────

UNIVERSAL_FORBIDDEN_GESTURES = [
    "left-hand serving food, drink, or gifts",
    "palm-up-and-curling beckoning gesture (Western style)",
    "pointing index finger directly at a person",
    "soles of feet visible toward another person",
    "shoes placed on or above seating surfaces",
    "thumbs-up directed at religious or elder figures",
    "the Western 'OK' circle gesture (offensive in some Gulf contexts)",
]

UNIVERSAL_FORBIDDEN_PROPS = [
    "alcohol product imagery (any brand)",
    "pork product imagery",
    "religious symbols of other faiths used decoratively",
    "gambling references (cards, dice, casino chips)",
    "Quranic verses overlaid on commercial imagery",
]

UNIVERSAL_FORBIDDEN_BEHAVIORS = [
    "eating or drinking during Ramadan daylight hours in branded content",
    "cross-gender physical contact between non-mahrams",
    "smoking in family-context content",
    "depicting prayer with disrespect or as commercial backdrop",
]


# ───────────────────────────────────────────────────────────────────────────
# 8 base 80-field cultural specs
# ───────────────────────────────────────────────────────────────────────────

def base_spec(scope_label: str) -> dict:
    """Field skeleton populated with common Saudi defaults; overlays adjust specifics."""
    return {
        "schema_version": 1,
        "scope_label": scope_label,
        "characters": {
            "ethnic_regional_look": "general-saudi",
            "age_distribution": {"child": 0.10, "teen": 0.10, "young_adult": 0.35, "mid_age": 0.35, "elder": 0.10},
            "gender_presentation_rule": "single-gender-per-scene",
            "face_visibility_women_rule": "contextual",
            "hijab_style_preference": "contextual",
            "mixed_gender_scene_rule": "family-only-mixing",
            "class_signaling": "professional-middle",
            "talent_consistency_model": "rotating-core-cast",
            "facial_features_archetype": "natural Saudi features, lightly directed",
            "expression_default": "warm composed, never overly performed",
        },
        "wardrobe": {
            "mens_traditional_cut": "saudi-traditional",
            "mens_thobe_color": "white default; navy/cream for formal evening",
            "mens_thobe_collar": "button-cleric",
            "mens_head_covering_color": "white shemagh or red-white for traditional context",
            "mens_head_covering_style": "egal-secured",
            "mens_outer_layering": "contextual",
            "womens_abaya_style": "classic-black",
            "womens_abaya_color": "black default; navy or muted earth tones acceptable",
            "womens_embroidery_level": "subtle",
            "womens_head_covering_type": "contextual",
            "children_wardrobe_register": "casual contemporary with traditional accessories on occasions",
            "cultural_mixing_rule": "traditional-with-modern-accessories",
        },
        "body_language": {
            "sitting_position_default": "seated upright on majlis cushions or modern furniture; never with crossed-leg-showing-sole",
            "sitting_positions_allowed": ["upright on cushion", "legs tucked", "chair-seated upright"],
            "standing_posture_default": "shoulders square, weight even, hands at sides or holding objects with right hand",
            "walking_style_default": "measured, unhurried, dignified",
            "greeting_forms_allowed": [
                "handshake (same gender)",
                "shoulder touch (same gender, close acquaintance)",
                "hand-on-heart (cross-gender, mahram-distance)",
                "verbal-only greeting with slight bow (cross-gender, strangers/professional)",
            ],
            "eye_contact_rule": "respectful sustained with same-gender; brief and respectful cross-gender; downward with elders during direct correction",
            "cross_gender_distance_rule": "professional distance minimum 50cm; family contexts allow less",
            "physical_contact_same_gender_rule": "warm and natural — shoulder touches, hand-holding-while-walking culturally normal",
        },
        "gestures": {
            "forbidden_universal_list": UNIVERSAL_FORBIDDEN_GESTURES,
            "brand_allowed_list": [],
            "greeting_gestures_default": "right hand to heart, then slight bow head",
            "hospitality_gestures_signature": ["right-hand offer of coffee dallah", "open-palm gesture inviting to sit", "right-hand placement of dates"],
            "authority_gestures_for_elders": ["slight bow head", "hand placed on elder's hand briefly", "stepping aside to let elder enter first"],
            "counting_convention_starts_with_little_finger": True,
            "beckoning_convention": "palm-down-fingers-clawing",
            "emotional_expression_repertoire": ["restrained warmth", "smile-with-eyes", "hand on heart for sincere acknowledgement"],
            "patience_gesture_thumb_forefinger_middle": True,
            "prayer_gesture_visibility_rule": "shown only when authentic and respectful; never as performative backdrop",
        },
        "settings_architecture": {
            "primary_regional_architecture": "modern-riyadh",
            "secondary_architectures_allowed": ["najdi", "hejazi"],
            "modern_vs_heritage_ratio": "70:30 modern-leaning by default",
            "specific_motifs_allowed": ["palm trees", "Najd mud-brick arches", "rawasheen wooden lattice (Hijaz)", "contemporary glass-and-steel skyline"],
            "material_palette": ["sand-tone limestone", "warm timber", "brushed brass", "linen textiles"],
            "interior_setting_default": "majlis-style seating with modern lighting; mid-tone walls",
            "urban_vs_rural_orientation": "urban-primary",
            "desert_scenes_allowed": True,
            "religious_setting_treatment": "off-camera-implied",
            "cityscape_visibility_rule": "Riyadh modern skyline acceptable; never used as casual backdrop for unrelated content",
        },
        "props_objects": {
            "coffee_service_props": ["traditional dallah (coffee pot)", "fenjan cups (small handle-less)", "saucer-tray for serving"],
            "tea_service_props": ["istikana glasses", "shaped tea pot (often gold-rim)", "small wooden tray"],
            "date_variety_preference": ["sukkari", "khlas", "ajwa for premium contexts"],
            "frankincense_props": ["mabkhara (incense burner)", "oud chips"],
            "prayer_props_visibility": "prayer beads acceptable in respectful contexts; never as decorative-only",
            "modern_tech_props": ["smartphones", "laptops in workplace context", "tablets in retail/F&B context"],
            "heritage_props_recurring": ["dallah", "fenjan", "mabkhara", "sadu weavings", "majlis cushions"],
            "food_specific_props": [],
            "forbidden_props_universal": UNIVERSAL_FORBIDDEN_PROPS,
            "brand_signature_hero_prop": "brand-overridden at onboarding",
        },
        "behaviors_rituals": {
            "coffee_serving_order_rule": "elder first; then right-to-left of the host; never left-to-right",
            "food_eating_practice_default": "right hand only; communal sharing from central platter acceptable",
            "bismillah_gesture_visibility": "implied — never staged for camera",
            "date_before_water_iftar_rule": True,
            "prayer_treatment_rule": "shown-respectfully",
            "friday_prayer_treatment": "respect the timing — no commercial promotion 12:00–13:30 AST Fridays",
            "family_hierarchy_serving_order": "eldest first, then by age descending; women and men served separately in formal contexts",
            "elder_greeted_first_rule": True,
            "ramadan_specific_behaviors_required": [
                "iftar gathering with multi-generational family",
                "date and water at iftar (date first)",
                "post-iftar tea/coffee",
                "charity / zakat al-fitr reference acceptable in last 10 days",
            ],
            "eid_specific_behaviors_required": [
                "new clothes for Eid day 1",
                "Eidiya (cash gift in envelope, not wrapped box) to children",
                "extended-family visits days 2-3",
                "Eid prayer + post-prayer greeting",
            ],
            "hajj_specific_treatment": "reverent — never as marketing backdrop unless Hajj-services brand",
            "generational_silence_in_elder_presence_rule": "younger speakers wait their turn; never interrupt elders",
        },
        "social_dynamics": {
            "mixed_gender_workplace_rule": "professional-mixing acceptable in modern workplace contexts; conservative-mixing in traditional sectors",
            "mixed_gender_family_rule": "natural — multi-generational family scenes are central to Saudi content",
            "mixed_gender_public_rule": "professional-mixing acceptable in business / retail / café settings; strict-segregation in conservative-leaning brand contexts",
            "physical_distance_minimum_cross_gender": "professional 50cm; family contexts no minimum",
            "modesty_threshold": "moderate",
            "religious_authority_visual_treatment": "respectful, never trivialized",
            "family_authority_central_staging_rule": "elder centered, gathered family around — never elder isolated in commercial framing",
            "modern_professional_authority_treatment": "balanced — Saudi female professionals shown competently in business contexts when sector permits",
        },
        "regional_orientation": "general-saudi",
        "heritage_gravity": "present-anchored",
        "religious_sensitivity": "medium",
        "generational_orientation": "multi-gen",
    }


def apply_overlay(base: dict, overlay: dict) -> dict:
    """Recursive merge: overlay overrides base at any depth."""
    out = deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = apply_overlay(out[k], v)
        else:
            out[k] = v
    return out


# Sector × region overlays
SECTOR_DEFAULTS = {
    # ───────────── F&B ─────────────
    "f_and_b_najdi": {
        "scope_label": "F&B sector — Najdi (Riyadh / Qassim) default",
        "characters": {
            "ethnic_regional_look": "najdi-classical",
            "expression_default": "warm hospitable, hand-on-heart sincerity",
        },
        "wardrobe": {
            "mens_thobe_color": "white default; cream for evening",
            "cultural_mixing_rule": "traditional-with-modern-accessories",
        },
        "settings_architecture": {
            "primary_regional_architecture": "najdi",
            "secondary_architectures_allowed": ["modern-riyadh"],
            "interior_setting_default": "majlis with Najdi-pattern cushions, palm-leaf motifs, soft warm light",
            "material_palette": ["sand-tone limestone", "Najd mud-brick", "warm timber", "copper"],
        },
        "props_objects": {
            "food_specific_props": ["kabsa platter", "mandi pan", "harees clay pot", "dates on brass tray", "saffron-rice spread"],
            "brand_signature_hero_prop": "dallah pouring into fenjan",
        },
        "regional_orientation": "najdi-primary",
        "heritage_gravity": "present-anchored",
        "religious_sensitivity": "medium",
    },
    "f_and_b_hejazi": {
        "scope_label": "F&B sector — Hejazi (Jeddah / Makkah / Madinah) default",
        "characters": {
            "ethnic_regional_look": "hejazi-coastal",
            "expression_default": "lively warmth, more expressive than Najdi",
        },
        "wardrobe": {
            "mens_traditional_cut": "hejazi-style",
            "mens_thobe_color": "white default; off-white with embroidered collar for formal",
            "mens_head_covering_style": "free-flowing",
            "cultural_mixing_rule": "traditional-with-modern-accessories",
        },
        "settings_architecture": {
            "primary_regional_architecture": "hejazi",
            "secondary_architectures_allowed": ["modern-riyadh"],
            "specific_motifs_allowed": ["rawasheen (lattice wooden windows)", "coral-stone facades", "Red Sea coastal palette"],
            "interior_setting_default": "Hejazi rawasheen-lined room, soft sea-light, tile and timber accents",
            "material_palette": ["coral stone", "carved teak", "blue-and-white tile", "rope and rattan"],
        },
        "props_objects": {
            "food_specific_props": ["mutabbaq", "saleeg", "foul medames in pot", "mughass with stone-baked bread", "Red Sea fish on grill"],
            "brand_signature_hero_prop": "shai with mint by the window",
        },
        "regional_orientation": "hejazi-primary",
        "heritage_gravity": "present-anchored",
        "religious_sensitivity": "medium",
    },

    # ───────────── Retail ─────────────
    "retail_modern": {
        "scope_label": "Retail sector — modern (Vision 2030 contemporary) default",
        "characters": {
            "class_signaling": "youth-aspirational",
            "expression_default": "confident, casual, contemporary",
        },
        "wardrobe": {
            "mens_traditional_cut": "modern-tapered",
            "mens_head_covering_style": "free-flowing",
            "womens_abaya_style": "modern-fitted",
            "womens_embroidery_level": "subtle",
            "cultural_mixing_rule": "modern-with-heritage-cues",
        },
        "settings_architecture": {
            "primary_regional_architecture": "modern-riyadh",
            "secondary_architectures_allowed": ["vision-2030-futurism"],
            "interior_setting_default": "minimal retail floor — natural light, neutral palette, hero product staging",
            "material_palette": ["clean concrete", "brushed metal", "pale timber", "matte glass"],
            "modern_vs_heritage_ratio": "90:10 modern",
        },
        "social_dynamics": {
            "mixed_gender_workplace_rule": "modern-natural-mixing",
            "mixed_gender_public_rule": "modern-natural-mixing",
            "modesty_threshold": "modern-permissive",
        },
        "regional_orientation": "general-saudi",
        "heritage_gravity": "present-anchored",
    },
    "retail_heritage": {
        "scope_label": "Retail sector — heritage-anchored / artisan default",
        "characters": {
            "class_signaling": "merchant-affluent",
            "expression_default": "dignified, considered, present",
        },
        "wardrobe": {
            "mens_traditional_cut": "saudi-traditional",
            "womens_abaya_style": "embroidered-heritage",
            "womens_embroidery_level": "ornate",
            "cultural_mixing_rule": "purely-traditional",
        },
        "settings_architecture": {
            "primary_regional_architecture": "najdi",
            "secondary_architectures_allowed": ["hejazi"],
            "interior_setting_default": "souq aesthetic — wooden display, hand-stitched textiles, warm pendant lighting",
            "material_palette": ["aged timber", "hand-loomed wool", "saffron-tone fabric", "brass and copper"],
            "modern_vs_heritage_ratio": "20:80 heritage",
        },
        "regional_orientation": "najdi-primary",
        "heritage_gravity": "past-anchored",
    },

    # ───────────── Beauty ─────────────
    "beauty_modern": {
        "scope_label": "Beauty & Personal Care — modern contemporary default",
        "characters": {
            "face_visibility_women_rule": "contextual",
            "expression_default": "calm confident with subtle warmth",
        },
        "wardrobe": {
            "womens_abaya_style": "open-abaya",
            "womens_embroidery_level": "none",
            "cultural_mixing_rule": "modern-with-heritage-cues",
        },
        "settings_architecture": {
            "primary_regional_architecture": "modern-riyadh",
            "interior_setting_default": "minimal soft-light bathroom or vanity space; pale pastel palette",
            "material_palette": ["matte porcelain", "rose quartz", "warm gold accents", "soft linen"],
            "modern_vs_heritage_ratio": "95:5 modern",
        },
        "social_dynamics": {
            "mixed_gender_public_rule": "strict-segregation",
            "modesty_threshold": "strict",
            "family_authority_central_staging_rule": "intimate-family-only contexts",
        },
        "regional_orientation": "general-saudi",
        "heritage_gravity": "present-anchored",
        "religious_sensitivity": "high",
    },
    "beauty_heritage": {
        "scope_label": "Beauty & Personal Care — heritage / traditional default",
        "characters": {
            "expression_default": "grounded, generational, warm",
        },
        "wardrobe": {
            "womens_abaya_style": "embroidered-heritage",
            "womens_embroidery_level": "ornate",
            "cultural_mixing_rule": "traditional-with-modern-accessories",
        },
        "settings_architecture": {
            "primary_regional_architecture": "najdi",
            "interior_setting_default": "majlis-style with sadu textiles, oud burner, late-afternoon golden light",
            "material_palette": ["natural sandstone", "saffron-dyed wool", "amber-gold metal", "raw linen"],
            "modern_vs_heritage_ratio": "30:70 heritage",
        },
        "props_objects": {
            "frankincense_props": ["mabkhara with oud chips", "rose-water spritzer", "qamar henna paste"],
            "heritage_props_recurring": ["dallah", "fenjan", "mabkhara", "sadu weavings", "wooden comb"],
            "brand_signature_hero_prop": "open mabkhara with rising oud smoke",
        },
        "regional_orientation": "najdi-primary",
        "heritage_gravity": "past-anchored",
        "religious_sensitivity": "high",
    },

    # ───────────── Real Estate ─────────────
    "real_estate_modern_najdi": {
        "scope_label": "Real Estate — modern Najdi (Riyadh / Vision 2030 developments) default",
        "characters": {
            "class_signaling": "merchant-affluent",
            "expression_default": "considered, aspirational, dignified",
        },
        "wardrobe": {
            "cultural_mixing_rule": "modern-with-heritage-cues",
        },
        "settings_architecture": {
            "primary_regional_architecture": "modern-riyadh",
            "secondary_architectures_allowed": ["najdi", "vision-2030-futurism"],
            "interior_setting_default": "wide architectural — Najdi-inspired mass with modern volumes; golden-hour ambient light",
            "material_palette": ["pale limestone", "polished travertine", "brushed bronze", "tinted glass", "olive wood"],
            "modern_vs_heritage_ratio": "70:30 modern-leaning with heritage anchors",
            "specific_motifs_allowed": ["Najdi arched window references", "courtyard centerpieces", "palm-grove backdrops", "Riyadh skyline (used carefully)"],
        },
        "props_objects": {
            "heritage_props_recurring": ["majlis cushions", "dallah and fenjan on a stone shelf", "framed Arabic calligraphy"],
            "brand_signature_hero_prop": "courtyard fountain at golden hour",
        },
        "social_dynamics": {
            "family_authority_central_staging_rule": "multi-generational family in the home — center of the frame",
        },
        "regional_orientation": "najdi-primary",
        "heritage_gravity": "future-anchored",
        "religious_sensitivity": "medium",
    },

    # ───────────── Healthcare & Wellness ─────────────
    "healthcare_modern": {
        "scope_label": "Healthcare & Wellness — modern clinical default",
        "characters": {
            "class_signaling": "professional-middle",
            "expression_default": "calm reassuring, never alarmist",
        },
        "wardrobe": {
            "mens_traditional_cut": "modern-tapered",
            "womens_abaya_style": "modern-fitted",
            "cultural_mixing_rule": "modern-with-heritage-cues",
        },
        "settings_architecture": {
            "primary_regional_architecture": "modern-riyadh",
            "interior_setting_default": "clean clinical — soft diffuse fill, no harsh shadow, sky-blue accent",
            "material_palette": ["sterile white", "pale sky blue", "soft mint", "warm gray timber"],
            "modern_vs_heritage_ratio": "95:5 modern",
        },
        "social_dynamics": {
            "mixed_gender_workplace_rule": "professional-mixing",
            "mixed_gender_public_rule": "professional-mixing",
            "modesty_threshold": "strict",
            "religious_authority_visual_treatment": "respectful, never used as authority-by-association for medical claim",
        },
        "regional_orientation": "general-saudi",
        "heritage_gravity": "future-anchored",
        "religious_sensitivity": "high",
    },
}


def write_sector_spec(slug: str, overlay: dict) -> None:
    path = ROOT / "sector_defaults" / f"{slug}.yaml"
    base = base_spec(overlay.get("scope_label", slug))
    spec = apply_overlay(base, overlay)
    spec["cultural_spec_ulid"] = mint_or_preserve(path)
    spec["notes"] = (
        "Sector + region default. Brand inherits this spec and overrides ~10 fields at "
        "onboarding (modesty threshold, face_visibility, mixed_gender rules, brand_signature_hero_prop, "
        "and a handful of others). Marked experimental pending Cultural Advisor validation."
    )
    spec["provenance"] = provenance(
        source=f"inference:sector_baselines+chain_cultural_constraints+Saudi_cultural_synthesis_2026; spec:cultural_spec_v1_80_fields",
        scope=f"sector:{slug.split('_')[0] if not slug.startswith('healthcare') else 'healthcare_wellness'}+region:{slug}",
    )
    # Re-order so ULID + schema_version come first
    ordered = {
        "cultural_spec_ulid": spec.pop("cultural_spec_ulid"),
        "schema_version": spec.pop("schema_version"),
        "scope_label": spec.pop("scope_label"),
        **spec,
    }
    header = (
        f"# {slug}.yaml\n"
        f"# Schema: 12_data_shapes/cultural_spec_v1.schema.json (80 fields)\n"
        f"# Confidence: experimental — Cultural Advisor review required before production\n"
        f"# Scope: {ordered['provenance']['scope']}\n\n---\n"
    )
    path.write_text(header + yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=120))
    print(f"✓ {path.relative_to(REPO)}")


# ───────────────────────────────────────────────────────────────────────────
# 4 forbidden_lists
# ───────────────────────────────────────────────────────────────────────────

def forbidden_list(kind: str, title_desc: str, entries: list[dict], rationale: str) -> dict:
    return {
        "schema_version": 1,
        "list_kind": kind,
        "enforcement_level": "hard_block",
        "title": title_desc,
        "rationale": rationale,
        "entries": entries,
        "provenance": provenance(
            source="research_corpus/CCO_Environment_v2.docx + Saudi_cultural_knowledge + universal_compliance",
            scope="universal",
        ),
    }


def write_forbidden(filename: str, data: dict) -> None:
    path = ROOT / "forbidden_lists" / filename
    header = (
        f"# {filename}\n"
        f"# Universal hard-block list — read by CCO agent at QC time.\n"
        f"# Enforcement: {data['enforcement_level']}\n"
        f"# Confidence: {data['provenance']['confidence']}\n"
        f"# Scope: {data['provenance']['scope']}\n\n---\n"
    )
    path.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
    print(f"✓ {path.relative_to(REPO)}")


def gestures_list() -> dict:
    return forbidden_list(
        "gestures",
        "Universal forbidden gestures — never appear in any branded content",
        [
            {"id": str(ULID()), "name": "left_hand_serving", "description": "Left hand used as primary hand for serving food, drink, or gifts.", "severity": "severe", "rationale": "Culturally offensive across Saudi/Gulf contexts.", "detection_hints": ["check hand-handedness in human-frame chains"]},
            {"id": str(ULID()), "name": "western_palm_up_beckon", "description": "Palm-up curling-finger beckoning (Western style).", "severity": "moderate", "rationale": "Reads as 'come here, animal' in regional context; offensive when applied to people.", "detection_hints": ["check gesture orientation in interactive scenes"]},
            {"id": str(ULID()), "name": "pointing_finger_at_person", "description": "Pointing index finger directly at another person.", "severity": "moderate", "rationale": "Disrespectful, especially toward elders or in authority context.", "detection_hints": ["scenes with direct-address gesture toward talent"]},
            {"id": str(ULID()), "name": "sole_of_foot_visible", "description": "Soles of feet or shoes visible toward another person.", "severity": "severe", "rationale": "Sole-of-foot toward a person is a recognized insult.", "detection_hints": ["check seated postures, cross-leg positions"]},
            {"id": str(ULID()), "name": "shoes_on_seating", "description": "Shoes placed on or above seating surfaces or majlis cushions.", "severity": "severe", "rationale": "Profanes hospitality space.", "detection_hints": ["majlis interior chains"]},
            {"id": str(ULID()), "name": "thumbs_up_to_elder_or_religious", "description": "Thumbs-up directed at religious authorities or elders.", "severity": "moderate", "rationale": "Tonal mismatch; in some Gulf interpretations, vulgar.", "detection_hints": []},
            {"id": str(ULID()), "name": "ok_circle_gesture", "description": "Western 'OK' circle hand gesture.", "severity": "moderate", "rationale": "Has acquired multiple offensive readings; avoid as a general rule.", "detection_hints": []},
        ],
        "Saudi and broader Gulf social norms treat these gestures as rude or culturally offensive. The CCO agent flags any caption or imagery referencing them as HARD_BLOCK.",
    )


def props_list() -> dict:
    return forbidden_list(
        "props",
        "Universal forbidden props — never appear in any branded content",
        [
            {"id": str(ULID()), "name": "alcohol_product", "description": "Alcohol product imagery (any brand, any visibility level).", "severity": "severe", "rationale": "Prohibited under Saudi law; brand association invalidates campaign.", "detection_hints": ["bottle silhouettes, glasses with amber liquid in social contexts"]},
            {"id": str(ULID()), "name": "pork_product", "description": "Pork product imagery — bacon, ham, pork chops, etc.", "severity": "severe", "rationale": "Religiously prohibited; brand association invalidates campaign.", "detection_hints": ["meat in F&B context — verify category"]},
            {"id": str(ULID()), "name": "gambling_imagery", "description": "Gambling references — casino chips, dice, playing-card suits used in betting context, slot machines.", "severity": "severe", "rationale": "Religiously prohibited.", "detection_hints": []},
            {"id": str(ULID()), "name": "other_faith_religious_symbols", "description": "Religious symbols of other faiths used decoratively (cross, star of David, Buddha statue, etc.).", "severity": "moderate", "rationale": "Tonally wrong; reads as either disrespect to the symbol or proselytism.", "detection_hints": ["decoration in interior scenes"]},
            {"id": str(ULID()), "name": "quranic_overlay_commercial", "description": "Quranic verses overlaid on commercial / promotional imagery.", "severity": "severe", "rationale": "Religious-text reverence violated by commercial frame.", "detection_hints": ["typography over product shots"]},
        ],
        "These props are religiously, legally, or tonally incompatible with any Saudi branded content. Hard-block at generation time.",
    )


def behaviors_list() -> dict:
    return forbidden_list(
        "behaviors",
        "Universal forbidden behaviors — never depicted in branded content",
        [
            {"id": str(ULID()), "name": "eating_during_ramadan_daylight", "description": "Eating or drinking visible during Ramadan daylight hours (between Fajr and Maghreb).", "severity": "severe", "rationale": "Fast-respect violation; visually inappropriate even in stylized form during Ramadan.", "detection_hints": ["F&B captions and imagery during Ramadan dates only"]},
            {"id": str(ULID()), "name": "cross_gender_physical_contact_non_mahram", "description": "Physical contact between non-mahrams of different genders (handshake, embrace, casual touch).", "severity": "severe", "rationale": "Cultural and religious norm.", "detection_hints": ["mixed-gender scene QC"]},
            {"id": str(ULID()), "name": "smoking_family_context", "description": "Smoking depicted in family-context content.", "severity": "moderate", "rationale": "Family-friendly content discipline; smoking signals reads as opposite intent.", "detection_hints": []},
            {"id": str(ULID()), "name": "prayer_as_commercial_backdrop", "description": "Prayer or supplication shown as commercial backdrop or trivialized for promotional effect.", "severity": "severe", "rationale": "Religious-act reverence violated.", "detection_hints": ["religious-imagery scene QC"]},
        ],
        "These behaviors violate religious, cultural, or tonal norms and are blocked at generation time regardless of brand or sector.",
    )


def visuals_list() -> dict:
    return forbidden_list(
        "visuals",
        "Universal forbidden visuals — never composed in any branded content",
        [
            {"id": str(ULID()), "name": "saudi_flag_misuse", "description": "Saudi flag used as disposable decoration, on disposable items, upside-down, overlaid on faces, or in any disrespectful framing.", "severity": "severe", "rationale": "Flag carries the Quranic shahada; misuse is legally and culturally severe.", "detection_hints": ["flag placement audit on all national-day content"]},
            {"id": str(ULID()), "name": "political_imagery_competitive", "description": "Imagery competitively contrasting with neighbouring states (flags, leaders, territories).", "severity": "severe", "rationale": "Diplomatic risk; brand exposure to political-positioning controversy.", "detection_hints": []},
            {"id": str(ULID()), "name": "sectarian_iconography", "description": "Sectarian or denominational religious iconography in commercial framing.", "severity": "severe", "rationale": "Sects represent religious sensitivity in pluralistic Saudi audience.", "detection_hints": []},
            {"id": str(ULID()), "name": "kaaba_or_mecca_as_backdrop", "description": "Kaaba, Mecca crowds, or Hajj imagery used as commercial backdrop for non-Hajj brand.", "severity": "severe", "rationale": "Reverent contexts, not stages.", "detection_hints": ["Hajj-period content QC"]},
            {"id": str(ULID()), "name": "named_historical_royal_unauthorized", "description": "Named historical royal figures depicted without official endorsement.", "severity": "moderate", "rationale": "Sovereignty-sensitive; requires explicit clearance.", "detection_hints": []},
        ],
        "These visuals carry political, religious, or sovereignty-sensitive weight that cannot be navigated at the generation layer alone. Hard-block at generation time.",
    )


# ───────────────────────────────────────────────────────────────────────────
# 3 advisor playbook files
# ───────────────────────────────────────────────────────────────────────────

def write_advisor_readme():
    path = ROOT / "advisor_playbook" / "README.md"
    path.write_text(f"""# Cultural Advisor — Role and Playbook

**Confidence:** experimental — the Cultural Advisor role is defined here but not yet staffed.

## What this role exists for

`{{PLATFORM_NAME}}` competes on Saudi cultural authenticity as a moat. The system has structural safeguards (forbidden lists, CCO agent, compliance gates) — but every brand-launch carries the risk that no machine layer catches a culturally off-key choice that a Saudi reader would flag instantly.

The Cultural Advisor is the human authority who validates that risk surface:

- Reviews the 80-field cultural spec for each new sector × region default before it enters production
- Reviews HARD_BLOCK forbidden lists periodically and proposes updates
- Adjudicates Soft-flagged content the CCO routes for human review
- Reviews Two-CD Diagnostic outputs that touch culturally sensitive territory (religious occasions, gender depiction, heritage interpretation)

## Authority

- The Cultural Advisor can override the CCO score and route a post to publish or hold.
- The Cultural Advisor cannot modify Schemas in `12_data_shapes/` (those are frozen at v1) — but can propose changes to sector-default cultural specs, forbidden lists, and the advisor playbook itself via PR.
- The Cultural Advisor's verdict on a culturally-sensitive piece is final unless escalated to the brand and to Mohamed for a joint decision.

## Position in the workflow

```
   COO compiles CaptionContext  →  DeepSeek generates  →  CCO Arabic QC
                                                         ↓
                                          CCO returns score + flags
                                                         ↓
                                         CEO confidence + human gate
                                                         ↓
   ┌────────────────────┬───────────────────┐
   ↓                    ↓                   ↓
clean (score ≥75)   watermarked         hold (score <50)
publishes           publishes with         ↓
                    watermark         routed to Cultural Advisor
                                       (or to Production Copilot for
                                       non-cultural holds)
```

The Cultural Advisor sits at the rightmost branch — the hold queue, plus any cultural soft-flag routed by CCO.

## Expected SLA

- Routine cultural review: 24 hours from CCO routing.
- Urgent (scheduled publish within 24h): 4 hours.
- Sector-default cultural spec review: completed within 5 business days of submission.

## What this role is NOT

- Not a copy editor. Arabic copy quality is the CCO's call; cultural appropriateness is the Advisor's.
- Not a brand strategist. Brand voice is the brand's call.
- Not a content moderator. The CCO HARD_BLOCK list handles the unambiguous cases; the Advisor handles the judgment cases.

## Files in this playbook

- `escalation_procedures.md` — when content gets escalated, to whom, expected SLA
- `review_checklist.md` — the standing checklist used on each major deliverable

## Provenance

- Source: `MASTER_PROMPT_FOR_CLAUDE_CODE.md` §3.3 + AGENT_MANIFEST.md
- Confidence: experimental
- Scope: universal
""")
    print(f"✓ {path.relative_to(REPO)}")


def write_advisor_escalation():
    path = ROOT / "advisor_playbook" / "escalation_procedures.md"
    path.write_text(f"""# Escalation Procedures — Cultural Advisor

## When content reaches the Cultural Advisor

Content routes to the Cultural Advisor under any of these conditions:

| Trigger | Source | Urgency |
|---|---|---|
| CCO flagged `cultural_flag: true` | CCO output | High — within 24h |
| CCO flagged `brave_route_flag: true` and brand is in Healthcare / Finance / Government sector | CCO output | High — within 24h |
| CCO `religious_reference_detected` and brand's `religious_sensitivity` is High | CCO output | Highest — within 4h |
| Content was generated for Ramadan / Eid / National Day and falls within the 7 days before the occasion | CEO routing | High |
| Two-CD Diagnostic where one or both brains is the Heritage Decoder and the brief is heritage-sensitive | Router | Standard — within 24h |
| First-ever campaign for a new sector × region cultural spec | Memory Controller | Standard |
| Brand owner explicitly requests Cultural Advisor review | Platform UI | Per request urgency |

## How escalation works (operational)

1. **Auto-route:** Memory Controller writes a `cultural_review_request` event with: brand_id, post_id(s), reason, urgency, deadline.
2. **Notify:** The Cultural Advisor receives notification (Telegram + email + platform inbox).
3. **Review:** Advisor opens the post(s) in the platform's Review queue. Reads caption, sees imagery (if present), sees the CCO flags + score, sees the relevant cultural-spec fields, sees the relevant forbidden-list entries.
4. **Verdict:** One of:
   - **Approve** — content publishes (or moves to next gate). Verdict logged with reason.
   - **Approve with watermark** — content publishes with the beta-quality watermark.
   - **Hold for rewrite** — back to COO with specific cultural revision notes.
   - **Hold for brand decision** — escalate to brand owner.
   - **Reject** — content blocked. Reason added to brand's NegativePattern list (proposed).
5. **Log:** All verdicts append to the audit trail as event-log entries.

## When to escalate further

The Cultural Advisor escalates to **Mohamed + brand owner jointly** when:

- Content touches Saudi sovereignty, royal family, or named historical/political figures
- Content touches Hajj, Kaaba, Mecca, Medina visual context for a non-Hajj brand
- Content involves a religious-text reference (Quranic verse, hadith, religious authority quote)
- Content involves cross-sectarian religious imagery
- The brand insists on a creative direction the Advisor judges culturally damaging

For all other cases, the Advisor's verdict is final.

## Sector-default cultural spec review

When a new sector × region default is added (e.g. `eastern_province_modern`), the Cultural Advisor reviews:

1. The full 80 fields, with focus on:
   - `characters` block (especially `face_visibility_women_rule`, `gender_presentation_rule`)
   - `wardrobe` block (regional accuracy)
   - `gestures` block (correct interpretation of cultural conventions)
   - `behaviors_rituals` block (occasion behaviors, prayer treatment)
   - `social_dynamics` block (mixed-gender rules)
2. Cross-checks against:
   - The relevant chains' `cultural_constraints` blocks
   - Sector baseline file (e.g. `05_sector_defaults/retail.yaml`)
   - Universal forbidden lists
3. Submits review notes as a draft ADR if changes affect more than this one spec.

Approved spec is updated from `confidence: experimental` to `confidence: inferred` (or `confirmed` if validated through real client use).

## Provenance

- Source: `MASTER_PROMPT_FOR_CLAUDE_CODE.md` §3.3 + AGENT_MANIFEST.md + agent prompts
- Confidence: experimental
- Scope: universal
""")
    print(f"✓ {path.relative_to(REPO)}")


def write_advisor_checklist():
    path = ROOT / "advisor_playbook" / "review_checklist.md"
    path.write_text(f"""# Cultural Advisor — Standing Review Checklist

Run this checklist on each major deliverable that reaches the Advisor's queue. A "fail" on any item routes the deliverable back to COO with the specific note.

## A. Religious sensitivity

- [ ] No prayer/supplication shown as commercial backdrop
- [ ] No Quranic verse overlaid on promotional content
- [ ] No Kaaba/Mecca/Medina imagery used as backdrop for non-Hajj brand
- [ ] No named religious authority depicted commercially without clearance
- [ ] Religious occasion (Ramadan, Eid) tonality matches occasion phase (e.g., Ramadan contemplative-first in first 20 days, joy in last 10)

## B. Gender depiction

- [ ] Mixed-gender scenes respect brand's stated rule (strict / family-only / professional / modern-natural)
- [ ] Women's depiction matches brand's `face_visibility_women_rule` setting
- [ ] No cross-gender physical contact between non-mahrams
- [ ] Modesty level matches brand-defined threshold (strict / moderate / modern-permissive)
- [ ] Same-gender intimacy / proximity is warm but not romantic-coded

## C. Regional accuracy

- [ ] If brand is Najdi: visual language is Najdi (architecture, dress, palette) — not collapsed to "generic Gulf"
- [ ] If brand is Hejazi: Hejazi specifics shown (rawasheen, coastal palette, Red Sea references where relevant)
- [ ] If brand is Eastern: Eastern Province visual cues respected
- [ ] Arabic dialect in caption matches brand's stated dialect (no Najdi-only markers in Hejazi content, no Levantine forms in any Saudi content)

## D. Gestures and props

- [ ] No left-hand serving / handling food / drink / gifts
- [ ] No palm-up Western beckoning
- [ ] No soles of feet visible toward people
- [ ] No alcohol / pork / gambling references
- [ ] Hospitality gestures (coffee dallah, dates) staged correctly (right hand, eldest served first)

## E. Occasion alignment

- [ ] If posted during Ramadan: no food consumption during daylight implied
- [ ] If Eid Al-Fitr Day 1: tone is family-celebratory, not transactional
- [ ] If Eid Al-Adha: entertainment sector blackout respected; no graphic animal imagery
- [ ] If National Day: Saudi green used full-strength; no flag misuse
- [ ] If Founding Day: heritage-deep register, distinct from National Day

## F. Forbidden lists cross-check

- [ ] No item from `forbidden_lists/universal_gestures_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_props_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_behaviors_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_visuals_forbidden.yaml`

## G. Bilingual quality

- [ ] Arabic copy reads as authentic Saudi Arabic — not translation-smell English
- [ ] Arabic and English are siblings (parallel originals), not one translating the other
- [ ] Arabic is set at equal optical weight to English (never as caption)
- [ ] No machine-translation markers (literal idioms, English sentence shape with Arabic words)

## H. Compliance signals

- [ ] Sector-specific compliance respected (Healthcare: no medical claims without SFDA / MoH clearance; Finance: no guaranteed-return language; Real Estate: no race-targeted pricing)
- [ ] CCO `negpat_flag` outcome reviewed (no HARD_BLOCK, STRONG_WARN reviewed for substantiation)
- [ ] PDPL: no identifiable individuals depicted without consent (especially in Healthcare)

## Decision

After running the checklist:

- **Zero fails** → Approve
- **1-2 minor fails (item in A.5, B.4, C.3, G.3)** → Approve with watermark + send back the specific notes
- **Any severe fail (any in A.1–4, B.1–3, D, F)** → Hold for rewrite
- **Sovereignty / royal / political content** → Escalate to Mohamed + brand jointly

Log the verdict with which checklist items failed (or "all passed") in the audit trail.

## Provenance

- Source: 80-field cultural spec + forbidden lists + agent prompts + Saudi cultural-norm synthesis
- Confidence: experimental
- Scope: universal
""")
    print(f"✓ {path.relative_to(REPO)}")


# ───────────────────────────────────────────────────────────────────────────
def main() -> int:
    print("═══ writing 8 sector-default cultural specs ═══")
    for slug, overlay in SECTOR_DEFAULTS.items():
        write_sector_spec(slug, overlay)

    print("\n═══ writing 4 universal forbidden lists ═══")
    write_forbidden("universal_gestures_forbidden.yaml", gestures_list())
    write_forbidden("universal_props_forbidden.yaml", props_list())
    write_forbidden("universal_behaviors_forbidden.yaml", behaviors_list())
    write_forbidden("universal_visuals_forbidden.yaml", visuals_list())

    print("\n═══ writing 3 advisor-playbook docs ═══")
    write_advisor_readme()
    write_advisor_escalation()
    write_advisor_checklist()

    print(f"\nWrote 15 cultural-spec files under {ROOT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
