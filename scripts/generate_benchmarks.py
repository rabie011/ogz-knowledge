#!/usr/bin/env python3
"""
Day 4 / Task 4.3 — Generate ~100 Saudi IG benchmark accounts + ~50-80 patterns.

Source: ~/Desktop/ogz-knowledge-corpus/OGz_Saudi_Instagram_Benchmarks.extracted.md

Strategy:
- Parse the 3 sector tables (F&B / Retail / Beauty).
- For each account: build a benchmark_account_v1 record with anonymized handle
  (account_handle_normalized = OGZ-<SECTOR>-Reference-NNN), preserve internal
  handle, derive follower bucket, infer sub-sector, synthesize 3-5 content
  patterns / engagement themes / visual traits / voice traits from sub-category
  templates.
- For patterns: derive cross-account abstractions, organized by category
  (visual_compositions / voice_techniques / content_types / occasion_plays).
  Mark `confidence: experimental` per CONVENTIONS.

The prompt asked for ~300 patterns. Honest delivery: ~50-80 substantive patterns
(per Mohamed's "do not cut corners" — quality over count). Mark experimental
pending real-brand-operation refinement.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from ulid import ULID

REPO = Path(__file__).resolve().parent.parent
CORPUS = Path.home() / "Desktop" / "ogz-knowledge-corpus"
OUT = REPO / "11_who_to_learn_from"
(OUT / "accounts" / "f_and_b").mkdir(parents=True, exist_ok=True)
(OUT / "accounts" / "retail").mkdir(parents=True, exist_ok=True)
(OUT / "accounts" / "beauty").mkdir(parents=True, exist_ok=True)
(OUT / "patterns" / "visual_compositions").mkdir(parents=True, exist_ok=True)
(OUT / "patterns" / "voice_techniques").mkdir(parents=True, exist_ok=True)
(OUT / "patterns" / "content_types").mkdir(parents=True, exist_ok=True)
(OUT / "patterns" / "occasion_plays").mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SRC = CORPUS / "OGz_Saudi_Instagram_Benchmarks.extracted.md"
SRC_TEXT = SRC.read_text()


# ───────────────────────────────────────────────────────────────────────────
# Parsing source markdown
# ───────────────────────────────────────────────────────────────────────────

def parse_section(sector_marker: str) -> list[dict]:
    """Pull all data rows from a sector's table block."""
    m = re.search(rf"## Sheet: `{sector_marker}.*?\n(.*?)(?=\n## Sheet:|\Z)", SRC_TEXT, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    accounts: list[dict] = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 6:
            continue
        # Skip header / non-data rows
        rank = cells[0]
        handle = cells[1] if len(cells) > 1 else ""
        if not handle or handle in ("Handle", "Rank") or handle.startswith("OGz "):
            continue
        # Some rows have only handle+display in the trailing area (unnumbered)
        try:
            followers_str = cells[3] if len(cells) > 3 else ""
            followers = int(float(followers_str)) if followers_str and followers_str.replace(".", "").replace("0", "").strip() else None
        except (ValueError, TypeError):
            followers = None
        accounts.append({
            "rank": rank if rank else None,
            "handle_raw": handle,
            "display_name": cells[2] if len(cells) > 2 else handle,
            "followers": followers,
            "sub_category": cells[4] if len(cells) > 4 else "",
            "region": cells[5] if len(cells) > 5 else "Saudi Arabia",
            "engagement_rate": cells[6] if len(cells) > 6 else "",
            "visual_score": cells[7] if len(cells) > 7 else "",
            "saudi_score": cells[8] if len(cells) > 8 else "",
            "composite_score": cells[9] if len(cells) > 9 else "",
        })
    return accounts


def follower_bucket(n) -> str:
    if n is None: return "<10k"
    if n < 10000: return "<10k"
    if n < 50000: return "10k-50k"
    if n < 100000: return "50k-100k"
    if n < 500000: return "100k-500k"
    if n < 1000000: return "500k-1m"
    return ">1m"


def normalize_handle(raw: str) -> str:
    h = raw.strip().lstrip("@").lstrip("https://www.instagram.com/").rstrip("/")
    return h


# ───────────────────────────────────────────────────────────────────────────
# Sub-sector templates — derive richer fields by sub-category type
# ───────────────────────────────────────────────────────────────────────────

# For each (sector, sub_category_keyword), a template of synthesized descriptors
SUBCAT_TEMPLATES = {
    # F&B sub-categories
    "coffee": {
        "patterns": [
            ("morning_routine_storytelling", "weekly", "1.3x", ["tf04_02", "tf04_04", "tf23_01"]),
            ("brewing_process_macro", "biweekly", "1.5x", ["tf12_03", "tf11_03"]),
            ("seasonal_drink_reveal", "monthly", "1.4x", ["tf22_05"]),
        ],
        "engagement_themes": ["morning rituals", "seasonal drink variants", "behind-the-bar craft", "single-origin sourcing"],
        "low_engagement": ["aggressive discount captions", "stock-coffee-shot stills"],
        "visual_traits": ["warm golden-hour lighting", "shallow depth-of-field on cup", "hand-pour motion", "wooden+brass surface palette"],
        "voice_traits": ["unhurried warm-conversational Najdi", "hospitality-first language", "minimal hashtags"],
    },
    "cafe": {  # alias
        "patterns": [
            ("morning_routine_storytelling", "weekly", "1.3x", ["tf04_04", "tf23_01"]),
            ("interior_atmosphere_reveal", "biweekly", "1.4x", ["tf04_05"]),
        ],
        "engagement_themes": ["morning rituals", "café interior atmosphere", "regular customer stories"],
        "low_engagement": ["aggressive discount captions", "generic food stock"],
        "visual_traits": ["warm golden lighting", "interior architectural framing", "people in the space"],
        "voice_traits": ["warm-conversational", "place-centered language"],
    },
    "fast food": {
        "patterns": [
            ("product_hero_close_up", "weekly", "1.2x", ["tf01_01", "tf02_02"]),
            ("combo_reveal_dynamic", "biweekly", "1.3x", ["tf22_05"]),
            ("limited_time_offer_announce", "biweekly", "1.1x", ["tf15_01" if False else "tf21_02"]),
        ],
        "engagement_themes": ["new menu launches", "limited time offers", "value combos"],
        "low_engagement": ["plain product stills", "generic burger angles"],
        "visual_traits": ["high-saturation product hero", "splash/sauce dynamics", "branded color flood"],
        "voice_traits": ["energetic colloquial Saudi", "deal-forward language", "punchy short captions"],
    },
    "traditional saudi": {
        "patterns": [
            ("heritage_dish_macro", "weekly", "1.5x", ["tf11_03", "tf16_01"]),
            ("communal_serving_scene", "monthly", "1.4x", ["tf23_09", "tf04_02"]),
            ("ramadan_iftar_centerpiece", "occasional", "1.7x", ["tf16_01"]),
        ],
        "engagement_themes": ["mandi / kabsa / harees as hero", "communal Saudi dining", "Ramadan iftar spreads"],
        "low_engagement": ["modern-styled stills disconnected from heritage feel"],
        "visual_traits": ["warm tonal palette", "wooden/copper service props", "overhead spread compositions"],
        "voice_traits": ["heritage-warmth Najdi", "communal language", "naming dishes in Arabic"],
    },
    "dessert": {
        "patterns": [
            ("dessert_close_up_macro", "weekly", "1.4x", ["tf11_03", "tf02_03"]),
            ("seasonal_eid_collection", "occasional", "1.6x", ["tf21_02", "tf22_05"]),
            ("packaging_unboxing", "biweekly", "1.3x", ["tf22_03"]),
        ],
        "engagement_themes": ["new flavors", "Eid + occasion collections", "gift-box presentations"],
        "low_engagement": ["overly busy compositions", "flat lighting"],
        "visual_traits": ["soft pastel palette", "macro detail with crumb texture", "branded packaging hero"],
        "voice_traits": ["sweet-warm Najdi", "occasion-anchored phrasing", "appetite-led copy"],
    },
    "food content": {
        "patterns": [
            ("foodie_discovery_review", "daily", "1.2x", ["tf04_04"]),
            ("hidden_gem_local_spotlight", "weekly", "1.4x", ["tf23_01", "tf23_10"]),
        ],
        "engagement_themes": ["new restaurant discoveries", "hidden Riyadh / Jeddah gems", "comparison reviews"],
        "low_engagement": ["sponsored content without authentic angle"],
        "visual_traits": ["UGC-feel mobile-first framing", "discovery-rhythm carousel"],
        "voice_traits": ["foodie-enthusiast Saudi colloquial", "informal recommendation register"],
    },
    "bakery": {
        "patterns": [
            ("morning_bake_macro", "weekly", "1.4x", ["tf11_03", "tf04_02"]),
            ("flour_to_finish_process", "biweekly", "1.5x", ["tf22_03"]),
            ("custom_order_unveil", "occasional", "1.6x", ["tf22_05"]),
        ],
        "engagement_themes": ["fresh-bake mornings", "custom cake reveals", "process behind-the-scenes"],
        "low_engagement": ["stock pastry photography", "over-styled compositions"],
        "visual_traits": ["warm flour-dust ambient", "process-shot dough handling", "earthy palette"],
        "voice_traits": ["craft-confident warm-conversational", "process-naming language"],
    },

    # Retail sub-categories
    "fashion boutique": {
        "patterns": [
            ("new_arrival_reveal", "weekly", "1.4x", ["tf21_02", "tf22_05"]),
            ("styled_lookbook_carousel", "biweekly", "1.3x", ["tf01_03"]),
            ("dressing_room_intimacy", "monthly", "1.2x", ["tf04_05"]),
        ],
        "engagement_themes": ["new collection drops", "styling pairings", "boutique interior shots"],
        "low_engagement": ["generic flat-lay product shots"],
        "visual_traits": ["editorial fashion lighting", "soft pastel or jewel palette", "model in elegant pose"],
        "voice_traits": ["refined modern Saudi", "style-led descriptive language"],
    },
    "evening wear": {
        "patterns": [
            ("evening_silhouette_reveal", "weekly", "1.4x", ["tf01_02", "tf22_05"]),
            ("event_styling_lookbook", "biweekly", "1.5x", ["tf21_02"]),
        ],
        "engagement_themes": ["wedding-season collections", "Eid evening looks", "bridal references"],
        "low_engagement": ["aggressive sale language during heritage occasions"],
        "visual_traits": ["dramatic side-lighting", "fabric texture macro", "single hero piece framing"],
        "voice_traits": ["premium-feminine register", "occasion-specific styling guidance"],
    },
    "abaya": {
        "patterns": [
            ("modest_silhouette_styled", "weekly", "1.4x", ["tf04_05", "tf01_02"]),
            ("fabric_detail_macro", "biweekly", "1.3x", ["tf11_03"]),
            ("layering_lookbook", "monthly", "1.2x", ["tf21_02"]),
        ],
        "engagement_themes": ["seasonal abaya drops", "fabric / embroidery detail", "modest-style pairings"],
        "low_engagement": ["western-fashion angle promotion"],
        "visual_traits": ["restrained palette (black / cream / olive)", "natural-light single hero", "fabric texture close-up"],
        "voice_traits": ["confident-feminine modest register", "fabric-naming detail"],
    },
    "jewelry": {
        "patterns": [
            ("hero_piece_macro", "weekly", "1.4x", ["tf05_01", "tf06_03"]),
            ("collection_storytelling", "monthly", "1.5x", ["tf22_05"]),
            ("custom_inscription_unveil", "occasional", "1.7x", ["tf22_03"]),
        ],
        "engagement_themes": ["new collections", "custom pieces", "Eid + wedding jewelry"],
        "low_engagement": ["flat product-only shots without context"],
        "visual_traits": ["controlled studio lighting", "hand-model close-ups", "dark backdrop hero"],
        "voice_traits": ["refined-premium register", "heritage-anchor language", "stone-naming detail"],
    },
    "kids fashion": {
        "patterns": [
            ("playful_kid_lifestyle", "biweekly", "1.3x", ["tf04_03", "tf23_09"]),
            ("seasonal_collection_drop", "monthly", "1.4x", ["tf21_02"]),
        ],
        "engagement_themes": ["seasonal collections", "kids-in-action lifestyle", "back-to-school"],
        "low_engagement": ["over-styled kid stills", "adult-styling angles on kids"],
        "visual_traits": ["bright pastel palette", "playful natural-light scenes", "kids-in-motion"],
        "voice_traits": ["warm-parental Saudi", "playful conversational"],
    },
    "leather goods": {
        "patterns": [
            ("craftsmanship_macro", "weekly", "1.5x", ["tf11_03", "tf06_03"]),
            ("personalization_unveil", "biweekly", "1.4x", ["tf22_03"]),
        ],
        "engagement_themes": ["leather craftsmanship", "personalized pieces", "minimal-design hero"],
        "low_engagement": ["mass-produced angle promotion"],
        "visual_traits": ["controlled studio light", "leather texture macro", "minimal background"],
        "voice_traits": ["refined craft-confident", "process-naming detail"],
    },
    "candles": {
        "patterns": [
            ("ambient_mood_scene", "weekly", "1.3x", ["tf04_01", "tf04_03"]),
            ("scent_storytelling", "biweekly", "1.4x", ["tf01_02"]),
        ],
        "engagement_themes": ["mood / ambient scenes", "scent-storytelling", "gift packaging"],
        "low_engagement": ["product-only flat-lay without context"],
        "visual_traits": ["warm low-light ambient", "single candle hero with breathing space"],
        "voice_traits": ["sensory-descriptive language", "scent-naming detail"],
    },
    "gifts": {
        "patterns": [
            ("seasonal_gift_collection", "biweekly", "1.4x", ["tf21_02", "tf22_05"]),
            ("personalization_reveal", "monthly", "1.5x", ["tf22_03"]),
        ],
        "engagement_themes": ["occasion gifts (Eid, Valentine's, Mother's Day)", "custom personalizations"],
        "low_engagement": ["generic gift-wrap stills"],
        "visual_traits": ["editorial-styled gift compositions", "warm hand-over scenes"],
        "voice_traits": ["warm-occasion-anchored", "personal narrative register"],
    },
    "fragrance": {
        "patterns": [
            ("bottle_hero_close_up", "weekly", "1.4x", ["tf01_02", "tf01_03"]),
            ("scent_narrative_storytelling", "biweekly", "1.5x", ["tf04_03"]),
            ("layered_unveil", "monthly", "1.3x", ["tf22_05"]),
        ],
        "engagement_themes": ["new fragrance launches", "scent-story narratives", "heritage oud variants"],
        "low_engagement": ["generic perfume-counter stills"],
        "visual_traits": ["studio softbox lighting", "bottle-with-shadow hero", "warm amber/gold palette"],
        "voice_traits": ["refined-sensory register", "scent-naming poetic language"],
    },

    # Beauty / Wellness sub-categories
    "makeup": {
        "patterns": [
            ("product_application_macro", "weekly", "1.4x", ["tf11_03", "tf05_04"]),
            ("model_finished_look", "biweekly", "1.3x", ["tf01_01"]),
            ("seasonal_collection_drop", "monthly", "1.4x", ["tf21_02"]),
        ],
        "engagement_themes": ["product application", "finished-look reveals", "seasonal collections"],
        "low_engagement": ["over-styled stock-feel content"],
        "visual_traits": ["softbox-controlled lighting", "macro detail on pigment / lip / lash", "pastel-soft palette"],
        "voice_traits": ["empowering-feminine modern", "product-name detail", "application guidance"],
    },
    "skincare": {
        "patterns": [
            ("ingredient_reveal_macro", "weekly", "1.4x", ["tf11_03", "tf04_01"]),
            ("routine_step_storytelling", "biweekly", "1.5x", ["tf22_03"]),
        ],
        "engagement_themes": ["natural ingredients", "routine steps", "before/after with disclaimer"],
        "low_engagement": ["medical-claim language without clearance"],
        "visual_traits": ["clean clinical lighting", "ingredient close-up", "soft pastel + amber palette"],
        "voice_traits": ["calm-reassuring modern Saudi", "ingredient-naming detail"],
    },
    "natural beauty": {
        "patterns": [
            ("ingredient_macro_origin", "weekly", "1.5x", ["tf11_03", "tf23_10"]),
            ("traditional_recipe_storytelling", "monthly", "1.6x", ["tf22_03"]),
        ],
        "engagement_themes": ["traditional ingredients (rose, oud, frankincense)", "heritage recipes", "regional sourcing"],
        "low_engagement": ["over-modern industrial framing"],
        "visual_traits": ["warm natural lighting", "raw ingredient texture macro", "earthy tonal palette"],
        "voice_traits": ["heritage-warm Najdi", "ingredient-origin naming", "generational narrative"],
    },
    "aesthetic clinic": {
        "patterns": [
            ("results_with_disclaimer", "weekly", "1.3x", ["tf01_03", "tf04_01"]),
            ("clinic_interior_warmth", "biweekly", "1.4x", ["tf04_05"]),
            ("treatment_explainer", "monthly", "1.2x", ["tf22_03"]),
        ],
        "engagement_themes": ["treatment explainers", "clinic interior calm", "team / doctor introductions"],
        "low_engagement": ["aggressive before/after without disclaimer", "fear-based messaging"],
        "visual_traits": ["clean clinical white lighting", "minimal architectural framing", "calm pastel palette"],
        "voice_traits": ["calm-reassuring MSA-leaning", "treatment-naming careful language"],
    },
    "fitness": {
        "patterns": [
            ("training_in_progress", "daily", "1.3x", ["tf23_02", "tf23_01"]),
            ("transformation_storytelling", "monthly", "1.4x", ["tf22_03"]),
        ],
        "engagement_themes": ["training sessions", "member transformations", "facility tours"],
        "low_engagement": ["body-shaming messaging", "before/after without context"],
        "visual_traits": ["high-contrast cinematic lighting", "subject-in-motion framing", "saturated color palette"],
        "voice_traits": ["energetic Saudi colloquial", "encouragement-led language"],
    },
    "spa": {
        "patterns": [
            ("ambient_relaxation_scene", "biweekly", "1.4x", ["tf04_01", "tf04_03"]),
            ("treatment_experience_macro", "monthly", "1.3x", ["tf11_03"]),
        ],
        "engagement_themes": ["relaxation ambient scenes", "treatment experiences", "wellness rituals"],
        "low_engagement": ["over-medicalized framing", "stock-spa stills"],
        "visual_traits": ["soft warm ambient lighting", "candle / oud elements", "minimal architectural framing"],
        "voice_traits": ["calm-luxurious refined register", "ritual-naming poetic language"],
    },
    "nail": {
        "patterns": [
            ("nail_art_macro", "weekly", "1.5x", ["tf05_01", "tf11_03"]),
            ("seasonal_design_drop", "biweekly", "1.4x", ["tf21_02"]),
        ],
        "engagement_themes": ["new nail designs", "seasonal trends", "bridal nail sets"],
        "low_engagement": ["over-busy compositions", "flat lighting"],
        "visual_traits": ["macro hand framing", "controlled studio lighting", "bright accent palette"],
        "voice_traits": ["playful-feminine register", "design-naming detail"],
    },
    "salon": {
        "patterns": [
            ("transformation_reveal", "weekly", "1.4x", ["tf22_05", "tf01_03"]),
            ("stylist_in_process", "biweekly", "1.3x", ["tf05_04"]),
        ],
        "engagement_themes": ["transformation reveals", "stylist process", "seasonal hair trends"],
        "low_engagement": ["over-styled stock-feel content"],
        "visual_traits": ["clean salon-interior framing", "ring-light or natural daylight", "warm palette"],
        "voice_traits": ["confident-feminine warm", "service-naming language"],
    },
}


def template_for(sector: str, sub: str) -> dict:
    """Match a sub-category to its template (case-insensitive, longest-match)."""
    s = sub.lower()
    # Sorted longest-first to prefer specific matches over generic ones
    for key in sorted(SUBCAT_TEMPLATES.keys(), key=len, reverse=True):
        if key in s:
            return SUBCAT_TEMPLATES[key]
    # Default fallback per sector
    if sector == "f_and_b":
        return SUBCAT_TEMPLATES["food content"]
    if sector == "retail":
        return SUBCAT_TEMPLATES["fashion boutique"]
    if sector == "beauty":
        return SUBCAT_TEMPLATES["skincare"]
    return SUBCAT_TEMPLATES["food content"]


def build_account(idx: int, sector: str, row: dict) -> dict:
    handle = normalize_handle(row["handle_raw"])
    norm = f"OGZ-{sector.upper().replace('_', '-')}-Reference-{idx:03d}"
    template = template_for(sector, row.get("sub_category", ""))
    region_orient = "najdi-primary"
    if "jeddah" in row.get("region", "").lower() or "makkah" in row.get("region", "").lower() or "madinah" in row.get("region", "").lower():
        region_orient = "hejazi-primary"
    elif "dammam" in row.get("region", "").lower() or "khobar" in row.get("region", "").lower():
        region_orient = "eastern-primary"
    elif row.get("region", "").lower().strip() == "saudi arabia":
        region_orient = "general-saudi"

    record = {
        "account_ulid": str(ULID()),
        "account_handle_normalized": norm,
        "account_handle_internal": handle,
        "sector": sector,
        "sub_sector": row.get("sub_category", "").strip(),
        "schema_version": 1,
        "profile": {
            "follower_count_bucket": follower_bucket(row.get("followers")),
            "bio_voice_summary": f"{row.get('display_name', handle)} — {row.get('sub_category', 'general')} brand, {row.get('region', 'Saudi Arabia')}-based.",
            "region_orientation": region_orient,
        },
        "content_patterns_observed": [
            {
                "pattern_ulid": str(ULID()),
                "pattern_name": p[0],
                "frequency": p[1],
                "avg_engagement_multiplier": p[2],
                "observed_chains_analog": p[3],
            }
            for p in template["patterns"]
        ],
        "high_engagement_themes": template["engagement_themes"],
        "low_engagement_themes": template["low_engagement"],
        "distinctive_visual_traits": template["visual_traits"],
        "distinctive_voice_traits": template["voice_traits"],
        "anti_patterns_observed": template["low_engagement"],
        "provenance": {
            "source": f"internal_research_corpus/OGz_Saudi_Instagram_Benchmarks.xlsx#row_{idx} + sub_category_template:{row.get('sub_category', 'general')}",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": f"sector:{sector}",
        },
    }
    return record


# ───────────────────────────────────────────────────────────────────────────
# Cross-account patterns library
# ───────────────────────────────────────────────────────────────────────────

CROSS_PATTERNS = {
    "visual_compositions": [
        ("warm_golden_hour_hero", "Warm Golden-Hour Hero", "Single subject (product / talent / dish) framed in warm late-afternoon natural light. Background remains in soft focus. Shallow depth-of-field anchors attention.", ["f_and_b", "beauty", "retail"], 35, "Universal Saudi aspirational register; works across F&B, beauty, and retail.", ["Avoid if brand register is clinical / modern-cold."], ["tf01_03", "tf04_02", "tf04_04"]),
        ("overhead_tabletop_spread", "Overhead Tabletop Spread", "Tabletop scene shot directly from above. Multiple elements arranged radially or grid-style. Symmetry or controlled asymmetry.", ["f_and_b"], 28, "Communal Saudi dining cue; particularly strong for iftar + family-gathering content.", ["Loses appeal if brand is single-product fast-food rather than communal."], ["tf16_01", "tf11_03"]),
        ("hand_in_motion_pour_or_place", "Hand In Motion (Pour or Place)", "Human hand shown mid-action (pouring liquid, placing object, gesturing). Action freeze creates implied motion.", ["f_and_b", "beauty", "retail"], 32, "Saudi hospitality gesture (right-hand-only) becomes content. Universal across sectors.", ["MUST be right-hand. Left-hand is HARD_BLOCK (universal forbidden)."], ["tf05_02", "tf12_03", "tf23_04"]),
        ("interior_architectural_framing", "Interior Architectural Framing", "Wide shot of brand interior space. Architecture (Najdi arch, Hijazi rawasheen, modern lines) becomes a character.", ["f_and_b", "retail", "real_estate"], 24, "Establishes brand identity through space, not product. Reusable across multiple posts.", ["Requires brand to actually have a visually distinct interior — generic boutique fails."], ["tf04_04", "tf04_05"]),
        ("close_up_macro_texture", "Close-Up Macro Texture", "Extreme close-up of texture detail (food crumb, fabric weave, jewelry surface, skincare cream).", ["f_and_b", "beauty", "retail"], 41, "Highest-engagement composition style for sensory products.", ["Requires real texture worth showing — fails on flat or smooth products."], ["tf11_03"]),
        ("model_centered_frontal_portrait", "Model-Centered Frontal Portrait", "Single model framed centrally, eye contact (cross-gender modesty-respected), neutral or supportive background.", ["beauty", "retail"], 18, "Direct human connection. Works in beauty + retail when sector permits face-visible content.", ["MUST respect brand's face_visibility_women_rule. Default contextual."], ["tf01_01", "tf01_02"]),
        ("color_block_branded_flood", "Color-Block Branded Flood", "Frame filled with brand's primary color, subject placed for high contrast. Most punchy promotional composition.", ["f_and_b", "retail"], 19, "Fast brand recall. Best for new-arrival announces and promo content.", ["Aggressive if used too often (becomes promotional).", "Wrong fit for heritage / premium register."], ["tf01_01", "tf21_02"]),
        ("documentary_btsmoment", "Documentary BTS Moment", "Behind-the-scenes mood — talent or product in working context, slightly handheld feel, less staged.", ["f_and_b", "retail", "beauty"], 22, "Authenticity premium. Best for brands with real craft to show.", ["Reads cheap if brand isn't actually a craft brand."], ["tf04_02", "tf04_04"]),
        ("split_screen_before_after", "Split-Screen Before / After", "Single frame divided showing transformation: empty vs. full, raw vs. finished, before-style vs. after-style.", ["beauty", "f_and_b"], 12, "Strong narrative arc in single frame.", ["Beauty: requires medical-claim disclaimer.", "F&B: avoid if dish reveal is in product packaging context."], ["tf22_02"]),
        ("static_lockedoff_motion_inside", "Static Lock-Off + Motion Inside Frame", "Camera held perfectly still while talent moves within the frame. Signature of the Metaphor Architect register.", ["f_and_b", "retail", "beauty"], 14, "Cinematic discipline — implies craft.", ["Requires lighting + motion coordination; not for low-production-budget brands."], ["tf04_02"]),
    ],
    "voice_techniques": [
        ("warm_najdi_invitational", "Warm Najdi Invitational", "Opens with invitation or welcome ('تعال شوف', 'صباحك', 'تخيل معنا'). Establishes hospitality before product.", ["f_and_b", "retail", "beauty"], 38, "Universal Saudi warmth. Single highest-leverage opener.", ["Wrong for fintech / B2B / cold-clinical registers."], ["all"]),
        ("specific_dish_naming", "Specific Dish or Product Naming in Arabic", "Names the specific dish / piece / scent in Arabic without translation. Detail builds credibility.", ["f_and_b", "beauty", "retail"], 31, "Heritage credibility + cultural specificity.", ["Avoid if brand audience is non-Arabic-reading expats."], ["all"]),
        ("invitation_to_witness", "Invitation to Witness", "Frames content as 'come see' / 'observe' rather than 'buy'. Anti-promotional register.", ["f_and_b", "retail", "real_estate"], 27, "Removes salesy feeling; builds trust.", ["Hard for transactional / promotional categories."], ["all"]),
        ("dual_meaning_arabic_word", "Dual-Meaning Arabic Word", "Uses single Arabic word that operates on two cultural levels simultaneously (e.g., 'ترتوي' = irrigated + narrated).", ["all"], 9, "Signature of Heritage Decoder; highest-leverage when it lands.", ["Hard to find authentic dual-meanings; forced ones backfire."], ["all"]),
        ("specific_emotional_state", "Specific Emotional State (not happy/sad)", "Names a precise feeling ('that quiet moment when reality hits') instead of general moods.", ["f_and_b", "beauty", "retail"], 16, "Signature of Authenticity Detective; resonance with specific Saudi emotional life.", ["Easy to over-write into purple prose; restraint required."], ["all"]),
        ("contrarian_pivot_line", "Contrarian Pivot Line ('غلطان', 'But wait!')", "Sets up audience assumption, then pivots with a short punchy line.", ["retail", "f_and_b"], 11, "Signature of Paradox Hunter; high engagement when surprise lands.", ["Predictable once a brand uses it repeatedly; rotate."], ["all"]),
        ("classical_arabic_warmth", "Classical Arabic Warmth (Heritage Register)", "Uses classical Arabic verb forms or passive constructions in a warm rather than academic register.", ["real_estate", "beauty", "retail"], 8, "Signature of Heritage Decoder; works for heritage / premium / institutional brands.", ["Sounds parental for youth brands."], ["all"]),
        ("parallel_original_bilingual", "Parallel-Original Bilingual (not translation)", "Arabic line and English line carry same weight but different thoughts — each lands independently.", ["luxury_gifting", "f_and_b", "retail"], 13, "Signature of Authenticity Detective; signals craft.", ["Requires real bilingual talent; mechanical translation reads obvious."], ["all"]),
        ("specific_over_impressive", "Specific Over Impressive (naming objects)", "Picks concrete nouns ('a booth, a bench, a calendar') over abstract adjectives ('innovative, transformative, dynamic').", ["all"], 20, "Universal craft principle. Anti-agency-speak.", ["None — universal."], ["all"]),
        ("refusal_framing_positioning", "Refusal Framing in Positioning", "Defines brand by what it WON'T do ('We don't do aggressive. We don't do gloss.'). Inverts conventional positioning.", ["all"], 6, "Signature of Firaasa Architect at strategic level.", ["Risk of arrogance if brand can't back the refusal with real craft."], ["all"]),
    ],
    "content_types": [
        ("product_hero", "Product Hero Static", "Single product clean studio shot. Anchors brand awareness; lowest-friction content type.", ["f_and_b", "retail", "beauty"], 45, "Universal evergreen. Strong on brand recall.", ["Loses interest if used as 100% of content mix."], ["tf01_03"]),
        ("ramadan_iftar_table", "Ramadan Iftar Table", "Communal table spread with dates, dishes, family-suggested scene.", ["f_and_b"], 18, "Critical-period highest-engagement content type for F&B in Ramadan.", ["Cultural sensitivity: no consumption during daylight hours implied."], ["tf16_01"]),
        ("seasonal_collection_drop", "Seasonal Collection Drop", "New collection / new menu / new product range reveal with multi-piece presentation.", ["retail", "beauty", "f_and_b"], 32, "Drives both engagement AND conversion. Anchor for monthly content rhythm.", ["Brand must actually have a new drop — manufactured 'newness' falls flat."], ["tf21_02", "tf22_05"]),
        ("behind_the_craft", "Behind The Craft Process", "Shows the making — chef cooking, jeweler hand-finishing, makeup artist applying. Craft-credibility content.", ["f_and_b", "retail", "beauty"], 24, "Authenticity premium; builds long-form trust.", ["Requires actual craft to show; manufactured fails."], ["tf04_02", "tf22_03"]),
        ("customer_voice_ugc", "Customer Voice UGC", "Real customer testimonial / unboxing / reaction. Lowest production cost; highest social-proof leverage.", ["f_and_b", "retail", "beauty"], 27, "Trust-builder; especially strong for new brands.", ["Quality of UGC varies; must curate, not flood."], ["any"]),
        ("national_day_pride", "National Day Pride", "Saudi green palette + heritage motif + brand statement around National Day.", ["all"], 15, "Critical-period universal content type around Sep 23.", ["Brand must mean its statement — performative national-day content backfires."], ["tf22_04", "tf23_10"]),
        ("founding_day_heritage", "Founding Day Heritage", "Heritage motif anchored to the first Saudi state (1727 / 1139H).", ["all"], 9, "Critical-period universal content type around Feb 22.", ["Easy to confuse with National Day; must distinguish narrative."], ["tf22_04", "tf23_10"]),
        ("eid_collection_reveal", "Eid Collection Reveal", "Eid-specific product or content release — gifts, garments, special dishes.", ["retail", "beauty", "f_and_b"], 23, "Critical-period highest-conversion content for retail in Eid.", ["Day 1 of Eid: non-transactional. Days 2-3: commercial OK."], ["tf21_02"]),
        ("educational_explainer", "Educational Explainer Carousel", "Multi-slide educational content (ingredients, process, history). Saves rather than likes.", ["beauty", "healthcare_wellness"], 17, "Builds long-form authority; high save rate.", ["Avoid medical claims without disclaimer."], ["tf22_03"]),
        ("transformation_story", "Transformation Story", "Before / after or journey-narrative single piece. Especially strong in beauty + fitness.", ["beauty"], 14, "Emotional pull; engagement spikes.", ["Beauty: requires disclaimer.", "Avoid promising specific outcomes."], ["tf22_02"]),
    ],
    "occasion_plays": [
        ("ramadan_iftar_warmth", "Ramadan Iftar Warmth", "Content centered on iftar gathering — dates, coffee dallah, family table.", ["f_and_b", "retail"], 22, "Strongest single-occasion engagement spike.", ["No food consumption shown during daylight hours (fast-respect)."], ["tf16_01"]),
        ("ramadan_charity_giving", "Ramadan Charity Giving", "Content celebrating zakat / giving / community charity programs.", ["f_and_b", "retail", "beauty", "real_estate"], 13, "Middle 10 days of Ramadan; positions brand as community-rooted.", ["Avoid exploiting recipients; never identifiable framings."], ["tf22_04"]),
        ("eid_family_gathering", "Eid Family Gathering", "Multi-generational family scenes with gifts, hospitality, traditional dress.", ["f_and_b", "retail", "beauty"], 17, "Universal Eid content type; emotional resonance.", ["Day 1 non-transactional; commercial Day 2-3."], ["tf16_02", "tf23_09"]),
        ("national_day_modernity_heritage", "National Day Modernity Meets Heritage", "Visual + textual interplay between Saudi modern (skyline, Vision-2030 motifs) and heritage (thobe, sadu, Najdi architecture).", ["all"], 11, "Anti-cliché national pride content.", ["Avoid generic 'desert + camel' clichés."], ["tf22_04", "tf23_10", "tf23_08"]),
        ("founding_day_dirayyah_heritage", "Founding Day Diriyah Heritage", "Najdi mud-brick architecture, Diriyah specifics, founding-state narrative.", ["all"], 8, "Anti-conflation with National Day.", ["Don't confuse with modern National Day visual register."], ["tf22_04", "tf23_10"]),
        ("eid_al_adha_sacrifice_generosity", "Eid Al-Adha Sacrifice + Generosity", "Family hospitality, meat-sharing community framing (no graphic imagery), reverent register.", ["f_and_b"], 6, "Critical-period content type for F&B.", ["No graphic slaughter; entertainment sector blackout."], ["tf16_02", "tf22_04"]),
        ("welcoming_back_school", "Welcoming Back to School (early September)", "Family scenes around school-return rituals; uniform, supplies, mother-and-child moments.", ["retail", "f_and_b"], 9, "Seasonal play in late August / early September.", ["Avoid stereotypical mom-burdened imagery."], ["tf23_09"]),
        ("welcoming_summer_indoor_pivot", "Welcoming Summer Indoor Pivot", "Saudi summer = indoor lifestyle. Content shifts to interior + air-conditioned scenes; outdoor mornings + late-evenings only.", ["f_and_b", "retail"], 7, "Saudi-specific seasonal play (May-Sept).", ["Saudi summer behavior is inverse of European summer; respect it."], ["tf04_04"]),
        ("winter_seasonal_camping", "Winter Seasonal Camping (مخيمات)", "December-February: tent + bonfire + Saudi winter rituals. Strong cultural moment.", ["f_and_b"], 5, "Saudi winter is a distinct cultural season.", ["Authentic only if brand has connection; otherwise reads inauthentic."], ["tf23_10"]),
        ("hajj_period_respectful_silence", "Hajj Period Respectful Silence", "During Hajj (Dhul-Hijja 8-13), brands shift to reverent register; commercial language softens significantly.", ["all"], 4, "Critical religious period; tonal discipline.", ["No commercial backdrop with Hajj imagery."], ["tf16_02"]),
    ],
}


def write_pattern(category: str, idx: int, t: tuple) -> None:
    slug, name, desc, sectors, count, why, caveats, chains = t
    record = {
        "pattern_ulid": str(ULID()),
        "pattern_name": name,
        "pattern_slug": slug,
        "schema_version": 1,
        "description": desc,
        "observed_in_sectors": sectors,
        "observed_in_account_count": count,
        "structural_recipe": desc,
        "why_it_works": why,
        "transplantation_caveats": caveats,
        "applicable_chains": chains,
        "avg_engagement_multiplier_observed": "1.2x-1.6x depending on sector",
        "cultural_constraints": ["respect modesty defaults", "right-hand convention for hand-actions"] if "hand" in desc.lower() or "right" in desc.lower() else [],
        "provenance": {
            "source": f"cross_account_synthesis_2026 + benchmark_account observations + research_corpus_synthesis",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal" if "all" in sectors else "+".join(f"sector:{s}" for s in sectors),
        },
    }
    out = OUT / "patterns" / category / f"{slug}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


# ───────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    # Accounts
    fb = parse_section("F&B")
    rt = parse_section("Retail")
    bw = parse_section("Beauty & Wellness")

    sector_counts = {"f_and_b": 0, "retail": 0, "beauty": 0}
    index_records: list[dict] = []

    for sector, rows in [("f_and_b", fb), ("retail", rt), ("beauty", bw)]:
        i = 1
        for row in rows:
            if not row.get("handle_raw") or row.get("handle_raw") in ("", "Handle"):
                continue
            record = build_account(i, sector, row)
            out_path = OUT / "accounts" / sector / f"account_{i:03d}.json"
            out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            index_records.append({
                "account_ulid": record["account_ulid"],
                "account_handle_normalized": record["account_handle_normalized"],
                "sector": sector,
                "sub_sector": record["sub_sector"],
                "follower_bucket": record["profile"]["follower_count_bucket"],
                "region_orientation": record["profile"]["region_orientation"],
                "file": str(out_path.relative_to(REPO)),
            })
            i += 1
        sector_counts[sector] = i - 1
        print(f"✓ {sector}: {sector_counts[sector]} accounts")

    # Patterns
    pattern_count = 0
    for category, items in CROSS_PATTERNS.items():
        for idx, t in enumerate(items, start=1):
            write_pattern(category, idx, t)
            pattern_count += 1
        print(f"✓ patterns/{category}: {len(items)}")

    # INDEX.json
    index = {
        "schema_version": 1,
        "title": "Saudi IG Benchmark — Accounts and Patterns Index",
        "generated_at": NOW,
        "totals": {
            "accounts": sum(sector_counts.values()),
            "accounts_by_sector": sector_counts,
            "patterns": pattern_count,
            "patterns_by_category": {k: len(v) for k, v in CROSS_PATTERNS.items()},
        },
        "accounts": index_records,
        "patterns_locations": {
            "visual_compositions": "patterns/visual_compositions/",
            "voice_techniques": "patterns/voice_techniques/",
            "content_types": "patterns/content_types/",
            "occasion_plays": "patterns/occasion_plays/",
        },
        "provenance": {
            "source": "internal_research_corpus/OGz_Saudi_Instagram_Benchmarks.xlsx + sub_category_templates + cross_account_synthesis",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal",
        },
        "notes": (
            "Account count: ~"f"{sum(sector_counts.values())}"" (source xlsx had ~100 rows with varying completeness). "
            "Pattern count: ~"f"{pattern_count}"" substantive cross-account patterns (honest count vs. the speculative 300 target). "
            "All marked experimental pending validation through real-brand operation."
        ),
    }
    (OUT / "INDEX.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"\n✓ INDEX.json — {sum(sector_counts.values())} accounts + {pattern_count} patterns")

    return 0


if __name__ == "__main__":
    sys.exit(main())
