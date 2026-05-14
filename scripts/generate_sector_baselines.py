#!/usr/bin/env python3
"""
Day 2 / Task 2.1 — Generate 5 sector baseline YAML files.

Sources:
- F&B / Retail / Beauty values: corpus/OGz_OpenClaw_Prompt_Requirements.extracted.md
  (sheet "Sector Baselines" — 3-year OGz Studios content history)
- Real Estate / Healthcare values: extrapolated from chain `sectors_allowed` + general
  Saudi market knowledge. Flagged `confidence: experimental` with a `notes` block
  that explicitly marks the extrapolation.

Each file validates against 12_data_shapes/sector_baseline_v1.schema.json.

Idempotent: if a sector YAML already exists with a `sector_baseline_ulid`, we
preserve that ULID and overwrite the rest. Otherwise we mint a fresh ULID.

Usage:
    .venv/bin/python scripts/generate_sector_baselines.py
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ulid import ULID

REPO = Path(__file__).resolve().parent.parent
INDEX = json.load(open(REPO / "02_what_to_build" / "INDEX.json"))
OUT_DIR = REPO / "05_sector_defaults"
OUT_DIR.mkdir(exist_ok=True)

CHAIN_BY_SHORT = {c["chain_id_short"]: c for c in INDEX["chains"]}


def chain_ref(chain_id_short: str, score: float) -> dict:
    """Build an eligible-chain reference."""
    if chain_id_short not in CHAIN_BY_SHORT:
        raise KeyError(f"chain not found: {chain_id_short}")
    c = CHAIN_BY_SHORT[chain_id_short]
    return {
        "chain_ulid": c["chain_ulid"],
        "chain_id_short": c["chain_id_short"],
        "score": score,
    }


def existing_ulid(yaml_path: Path) -> str | None:
    if not yaml_path.exists():
        return None
    try:
        data = yaml.safe_load(yaml_path.read_text())
        return data.get("sector_baseline_ulid")
    except Exception:
        return None


def mint_or_preserve(yaml_path: Path) -> str:
    return existing_ulid(yaml_path) or str(ULID())


NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def common_provenance(source_ref: str, scope: str, confidence: str = "experimental") -> dict:
    return {
        "source": source_ref,
        "date_added": NOW,
        "confirmer": "Mohamed",
        "confidence": confidence,
        "scope": scope,
    }


# ───────────────────────────────────────────────────────────────────────────
# F&B — Food & Beverage
# Source: OGz_OpenClaw_Prompt_Requirements xlsx, "Sector Baselines" sheet
# ───────────────────────────────────────────────────────────────────────────
def f_and_b():
    path = OUT_DIR / "f_and_b.yaml"
    return {
        "sector_baseline_ulid": mint_or_preserve(path),
        "sector_slug": "f_and_b",
        "sector_name_en": "Food & Beverage",
        "sector_name_ar": "الأطعمة والمشروبات",
        "schema_version": 1,
        "default_voice": {
            "register": "warm-conversational",
            "formality": "casual",
            "dialect_default": "najdi",
            "msa_tolerance": "low",
            "english_codeswitching_tolerance": "moderate",
        },
        "default_visual": {
            "primary_palette": ["#C9472B", "#E8D5B4", "#1F2A2E", "#F2A359"],
            "secondary_accents": ["#FFD500", "#28D9A8"],
            "lighting_default": "warm natural daylight, late afternoon golden hour for hero shots",
            "composition_default": "lifestyle photography, hand-held framing, food centered with environmental context",
            "texture_default": "tactile food texture, condensation on glassware, steam on hot dishes",
        },
        "default_cinematography": {
            "lens_default": "50mm prime · shallow depth",
            "depth_of_field": "shallow (subject sharp, background creamy)",
            "camera_height": "eye-level or slight overhead for tabletop",
            "motion_grammar": "slow pour · short hold · cut on action; no whip-pans",
        },
        "default_cultural_spec": {
            "bilingual_ratio": "Arabic-primary 80/20",
            "humor_tolerance": "minimal",
            "religious_sensitivity": "medium",
            "modesty_level": "moderate",
            "tone_attributes": ["warm", "family-focused", "community"],
            "tone_anti_attributes": ["aggressive", "formal"],
            "visual_style": ["lifestyle photography", "warm tones"],
            "visual_anti_style": ["dark moody", "documentary"],
            "ramadan_relevance": "critical",
            "eid_fitr_relevance": "critical",
            "eid_adha_relevance": "high",
            "national_day_relevance": "high",
            "founding_day_relevance": "medium",
            "summer_shift_intensity": "major",
            "posting_frequency_default": "5x per week",
            "posting_time_weekday_default": "19:00 AST",
            "posting_time_ramadan_default": "20:30 AST (post-iftar)",
            "content_mix": {"awareness_pct": 40, "engagement_pct": 35, "conversion_pct": 25},
            "confidence_floor": 0.6,
        },
        "default_eligible_chains": [
            chain_ref("tf16_01", 1.0),   # Ramadan Iftar Spread — occasion-critical
            chain_ref("tf02_02", 0.95),  # Beverage Pour Crown Splash — dynamic hero
            chain_ref("tf02_03", 0.92),  # Sauce Splash Around Food
            chain_ref("tf04_02", 0.90),  # Kitchen Window Morning — lifestyle
            chain_ref("tf04_04", 0.88),  # Café Outdoor Terrace
            chain_ref("tf11_03", 0.85),  # Food Texture Extreme Macro
            chain_ref("tf12_03", 0.85),  # Beverage Pour Stream
            chain_ref("tf23_01", 0.83),  # Saudi Woman Lifestyle — Coffee Moment
            chain_ref("tf01_03", 0.80),  # Product Hero Static — workhorse
            chain_ref("tf22_04", 0.78),  # Occasion Announcement Video
        ],
        "default_occasions_priority": [
            {"occasion_slug": "ramadan", "priority": 1.0},
            {"occasion_slug": "eid_al_fitr", "priority": 0.95},
            {"occasion_slug": "eid_al_adha", "priority": 0.80},
            {"occasion_slug": "saudi_national_day", "priority": 0.75},
            {"occasion_slug": "saudi_founding_day", "priority": 0.55},
        ],
        "default_kpis_focus": [
            "footfall",
            "delivery_orders",
            "saves_per_post",
            "story_completion_rate",
            "share_rate",
        ],
        "forbidden_topics_sector_specific": [
            "alcohol references",
            "pork references",
            "misleading health claims",
            "competitor disparagement",
            "non-halal certification implied",
        ],
        "default_cd_brain_routing_bias": {
            "cd_01_firaasa": 0.70,
            "cd_02_metaphor": 0.55,
            "cd_03_authenticity": 0.90,
            "cd_04_heritage": 0.75,
            "cd_05_paradox": 0.45,
        },
        "notes": "Anchored in OGz 3-year content history. Najdi dialect default reflects Riyadh SME mix; brands targeting Hijaz override at onboarding. Ramadan tier is critical — schedule lead time 21+ days.",
        "provenance": common_provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Sector_Baselines",
            scope="sector:f_and_b",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Retail
# Source: OpenClaw xlsx + chain library
# ───────────────────────────────────────────────────────────────────────────
def retail():
    path = OUT_DIR / "retail.yaml"
    return {
        "sector_baseline_ulid": mint_or_preserve(path),
        "sector_slug": "retail",
        "sector_name_en": "Retail",
        "sector_name_ar": "التجزئة",
        "schema_version": 1,
        "default_voice": {
            "register": "practical-direct",
            "formality": "neutral",
            "dialect_default": "mixed_najdi_msa",
            "msa_tolerance": "moderate",
            "english_codeswitching_tolerance": "moderate",
        },
        "default_visual": {
            "primary_palette": ["#1A1A1A", "#FFFFFF", "#C09F6F", "#E5E5E5"],
            "secondary_accents": ["#3349EB", "#E602BB"],
            "lighting_default": "clean studio with controlled key + fill, soft shadows",
            "composition_default": "product-focused, minimal background, ample negative space",
            "texture_default": "clean minimal, hard surfaces, fabric texture for soft goods",
        },
        "default_cinematography": {
            "lens_default": "85mm prime or 24-70mm zoom",
            "depth_of_field": "controlled (medium); product fully resolved",
            "camera_height": "product eye-level",
            "motion_grammar": "still hero · 360 rotation · pack-shot reveal",
        },
        "default_cultural_spec": {
            "bilingual_ratio": "balanced 50/50",
            "humor_tolerance": "none",
            "religious_sensitivity": "medium",
            "modesty_level": "moderate",
            "tone_attributes": ["practical", "trustworthy", "direct"],
            "tone_anti_attributes": ["flashy", "exclusive"],
            "visual_style": ["product-focused", "clean minimal"],
            "visual_anti_style": ["documentary"],
            "ramadan_relevance": "high",
            "eid_fitr_relevance": "critical",
            "eid_adha_relevance": "medium",
            "national_day_relevance": "high",
            "founding_day_relevance": "medium",
            "summer_shift_intensity": "minor",
            "posting_frequency_default": "4x per week",
            "posting_time_weekday_default": "18:00 AST",
            "posting_time_ramadan_default": "21:00 AST",
            "content_mix": {"awareness_pct": 35, "engagement_pct": 35, "conversion_pct": 30},
            "confidence_floor": 0.6,
        },
        "default_eligible_chains": [
            chain_ref("tf01_03", 0.95),  # Product Hero Static — retail workhorse
            chain_ref("tf04_05", 0.92),  # Retail Boutique Interior
            chain_ref("tf03_01", 0.90),  # Single Overhead Spotlight
            chain_ref("tf03_02", 0.88),  # Ring Backlight Halo
            chain_ref("tf05_01", 0.85),  # Hand Model With Ring
            chain_ref("tf02_05", 0.82),  # Smoke Ring Mystique — premium
            chain_ref("tf21_02", 0.80),  # New Arrival / Launch
            chain_ref("tf22_03", 0.78),  # Product Unboxing Loop
            chain_ref("tf22_05", 0.75),  # New Arrival Reveal Video
            chain_ref("tf23_04", 0.72),  # Hands-Only Product Interaction
        ],
        "default_occasions_priority": [
            {"occasion_slug": "eid_al_fitr", "priority": 1.0},
            {"occasion_slug": "ramadan", "priority": 0.90},
            {"occasion_slug": "saudi_national_day", "priority": 0.85},
            {"occasion_slug": "eid_al_adha", "priority": 0.75},
            {"occasion_slug": "saudi_founding_day", "priority": 0.55},
        ],
        "default_kpis_focus": [
            "online_sales_conversion",
            "click_through_rate",
            "average_order_value",
            "return_customer_rate",
        ],
        "forbidden_topics_sector_specific": [
            "prohibited product imagery (alcohol/pork/gambling)",
            "false pricing claims",
            "exaggerated discount language",
            "competitor disparagement",
        ],
        "default_cd_brain_routing_bias": {
            "cd_01_firaasa": 0.75,
            "cd_02_metaphor": 0.65,
            "cd_03_authenticity": 0.80,
            "cd_04_heritage": 0.60,
            "cd_05_paradox": 0.70,
        },
        "notes": "Retail dialect blend (Najdi/MSA) reflects nationwide reach. Eid Al-Fitr is the single biggest commercial moment — 21+ day lead. Discount language must be tone-aligned, not aggressive.",
        "provenance": common_provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Sector_Baselines",
            scope="sector:retail",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Beauty & Personal Care
# Source: OpenClaw xlsx + chain library
# ───────────────────────────────────────────────────────────────────────────
def beauty():
    path = OUT_DIR / "beauty.yaml"
    return {
        "sector_baseline_ulid": mint_or_preserve(path),
        "sector_slug": "beauty",
        "sector_name_en": "Beauty & Personal Care",
        "sector_name_ar": "العناية والجمال",
        "schema_version": 1,
        "default_voice": {
            "register": "nurturing-confident",
            "formality": "casual",
            "dialect_default": "najdi",
            "msa_tolerance": "low",
            "english_codeswitching_tolerance": "moderate",
        },
        "default_visual": {
            "primary_palette": ["#F5BEB7", "#E8D6A0", "#FFFFFF", "#2A2520"],
            "secondary_accents": ["#C09F6F", "#28D9A8"],
            "lighting_default": "soft diffused window light, ring light for product, pastel mood",
            "composition_default": "people-centered or product-as-still-life, calm rhythm",
            "texture_default": "soft pastel, satin finish, fabric softness, water beads",
        },
        "default_cinematography": {
            "lens_default": "85mm portrait or 100mm macro",
            "depth_of_field": "shallow for beauty close-up; medium for routine flow",
            "camera_height": "slight elevation or eye-level for talent",
            "motion_grammar": "slow zoom · soft glide · application reveal",
        },
        "default_cultural_spec": {
            "bilingual_ratio": "Arabic-primary 80/20",
            "humor_tolerance": "minimal",
            "religious_sensitivity": "medium",
            "modesty_level": "high",
            "modesty_threshold_note": "Default: hands/product only or fully-covered talent. Brand can override at onboarding for face-visible content with explicit permission.",
            "tone_attributes": ["nurturing", "empowering", "inspirational"],
            "tone_anti_attributes": ["aggressive", "formal"],
            "visual_style": ["people-centered", "soft pastel"],
            "visual_anti_style": ["bold graphic"],
            "ramadan_relevance": "medium",
            "eid_fitr_relevance": "high",
            "eid_adha_relevance": "low",
            "national_day_relevance": "high",
            "founding_day_relevance": "medium",
            "summer_shift_intensity": "minor",
            "posting_frequency_default": "4x per week",
            "posting_time_weekday_default": "20:00 AST",
            "posting_time_ramadan_default": "21:00 AST",
            "content_mix": {"awareness_pct": 45, "engagement_pct": 35, "conversion_pct": 20},
            "confidence_floor": 0.6,
        },
        "default_eligible_chains": [
            chain_ref("tf03_03", 0.92),  # Column Light From Above
            chain_ref("tf04_01", 0.90),  # Bathroom Marble Counter
            chain_ref("tf04_03", 0.88),  # Bedroom Side Table Morning
            chain_ref("tf06_01", 0.85),  # Twin Softbox Studio Reveal
            chain_ref("tf23_01", 0.85),  # Saudi Woman Lifestyle — Coffee Moment
            chain_ref("tf01_01", 0.82),  # Floating Product Levitation
            chain_ref("tf02_01", 0.80),  # Splash Ring Around Product
            chain_ref("tf22_03", 0.78),  # Product Unboxing Loop
            chain_ref("tf21_02", 0.75),  # New Arrival / Launch
            chain_ref("tf22_05", 0.72),  # New Arrival Reveal Video
        ],
        "default_occasions_priority": [
            {"occasion_slug": "eid_al_fitr", "priority": 0.90},
            {"occasion_slug": "saudi_national_day", "priority": 0.80},
            {"occasion_slug": "ramadan", "priority": 0.65},
            {"occasion_slug": "saudi_founding_day", "priority": 0.55},
            {"occasion_slug": "eid_al_adha", "priority": 0.40},
        ],
        "default_kpis_focus": [
            "saves_per_post",
            "engagement_rate",
            "online_sales_conversion",
            "ugc_reshare_rate",
        ],
        "forbidden_topics_sector_specific": [
            "medical / treatment claims without clearance",
            "prescription drug references",
            "before/after with implied permanence",
            "skin-tone hierarchy",
            "weight-loss promises",
        ],
        "default_cd_brain_routing_bias": {
            "cd_01_firaasa": 0.65,
            "cd_02_metaphor": 0.80,
            "cd_03_authenticity": 0.85,
            "cd_04_heritage": 0.55,
            "cd_05_paradox": 0.50,
        },
        "notes": "Modesty defaults are HIGH — face-visible talent requires explicit brand permission at onboarding. Beauty is people-led but the default storyboard centers hands, product, and product-in-use; brand override unlocks face-visible flows.",
        "provenance": common_provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Sector_Baselines",
            scope="sector:beauty",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Real Estate — EXTRAPOLATED. No source coverage in xlsx.
# Anchors: chain `sectors_allowed: home` + Saudi market knowledge.
# ───────────────────────────────────────────────────────────────────────────
def real_estate():
    path = OUT_DIR / "real_estate.yaml"
    return {
        "sector_baseline_ulid": mint_or_preserve(path),
        "sector_slug": "real_estate",
        "sector_name_en": "Real Estate",
        "sector_name_ar": "العقارات",
        "schema_version": 1,
        "default_voice": {
            "register": "authoritative-aspirational",
            "formality": "neutral",
            "dialect_default": "mixed_najdi_msa",
            "msa_tolerance": "high",
            "english_codeswitching_tolerance": "moderate",
        },
        "default_visual": {
            "primary_palette": ["#1F2A2E", "#C09F6F", "#E8D5B4", "#FFFFFF"],
            "secondary_accents": ["#3349EB"],
            "lighting_default": "golden-hour exterior · architectural backlight · controlled interior key",
            "composition_default": "wide architectural with strong leading lines; symmetry for hero shots",
            "texture_default": "marble · brushed metal · linen · stone; minimal decorative clutter",
        },
        "default_cinematography": {
            "lens_default": "16-35mm wide for interiors · 24-70mm exteriors",
            "depth_of_field": "deep (everything sharp); shallow only on accent shots",
            "camera_height": "eye-level for human-scale rooms; slightly elevated for masterplans",
            "motion_grammar": "slow gimbal walk-through · push-in · top-down drone for masterplans",
        },
        "default_cultural_spec": {
            "bilingual_ratio": "balanced 50/50",
            "humor_tolerance": "none",
            "religious_sensitivity": "medium",
            "modesty_level": "moderate",
            "tone_attributes": ["aspirational", "trustworthy", "premium"],
            "tone_anti_attributes": ["casual", "humorous"],
            "visual_style": ["architectural photography", "wide environmental"],
            "visual_anti_style": ["documentary", "candid lifestyle"],
            "ramadan_relevance": "medium",
            "eid_fitr_relevance": "medium",
            "eid_adha_relevance": "low",
            "national_day_relevance": "high",
            "founding_day_relevance": "high",
            "summer_shift_intensity": "minor",
            "posting_frequency_default": "3x per week",
            "posting_time_weekday_default": "20:00 AST",
            "posting_time_ramadan_default": "21:30 AST",
            "content_mix": {"awareness_pct": 50, "engagement_pct": 25, "conversion_pct": 25},
            "confidence_floor": 0.6,
        },
        "default_eligible_chains": [
            chain_ref("tf04_05", 0.92),  # Retail Boutique Interior — luxury interior aesthetic
            chain_ref("tf04_01", 0.90),  # Bathroom Marble Counter
            chain_ref("tf04_02", 0.88),  # Kitchen Window Morning
            chain_ref("tf04_03", 0.85),  # Bedroom Side Table Morning
            chain_ref("tf06_03", 0.83),  # Gallery Pedestal Solo — architectural framing
            chain_ref("tf13_04", 0.80),  # Kitchen Countertop Morning
            chain_ref("tf23_08", 0.78),  # Saudi Workplace Moment — Modern Office
            chain_ref("tf23_10", 0.75),  # Saudi Outdoor Lifestyle — Heritage Setting
            chain_ref("tf21_02", 0.72),  # New Arrival / Launch — project launch
            chain_ref("tf22_04", 0.70),  # Occasion Announcement Video
        ],
        "default_occasions_priority": [
            {"occasion_slug": "saudi_national_day", "priority": 0.90},
            {"occasion_slug": "saudi_founding_day", "priority": 0.85},
            {"occasion_slug": "eid_al_fitr", "priority": 0.55},
            {"occasion_slug": "ramadan", "priority": 0.50},
            {"occasion_slug": "eid_al_adha", "priority": 0.30},
        ],
        "default_kpis_focus": [
            "qualified_lead_volume",
            "viewing_bookings",
            "brand_lift",
            "long_form_engagement",
        ],
        "forbidden_topics_sector_specific": [
            "guaranteed-return language (regulator-sensitive)",
            "unverifiable comparison claims",
            "race / nationality-targeted pricing implication",
            "exact financing terms without licensed-broker disclosure",
        ],
        "default_cd_brain_routing_bias": {
            "cd_01_firaasa": 0.85,
            "cd_02_metaphor": 0.70,
            "cd_03_authenticity": 0.65,
            "cd_04_heritage": 0.90,
            "cd_05_paradox": 0.55,
        },
        "notes": "EXTRAPOLATED — source xlsx did not cover Real Estate. Values inferred from chain sectors_allowed:home + Saudi market patterns (Vision 2030 mega-projects, Najdi/Hijazi interior preferences, founding-day patriotism strong for real estate brands). MUST be validated by Cultural Advisor before production use.",
        "provenance": common_provenance(
            source_ref="inference:chain_sectors_allowed_home + Saudi_market_knowledge_2026",
            scope="sector:real_estate",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Healthcare & Wellness — EXTRAPOLATED. No source coverage in xlsx.
# Anchors: chain library + beauty/wellness overlap + Saudi clinical norms.
# ───────────────────────────────────────────────────────────────────────────
def healthcare_wellness():
    path = OUT_DIR / "healthcare_wellness.yaml"
    return {
        "sector_baseline_ulid": mint_or_preserve(path),
        "sector_slug": "healthcare_wellness",
        "sector_name_en": "Healthcare & Wellness",
        "sector_name_ar": "الرعاية الصحية والعافية",
        "schema_version": 1,
        "default_voice": {
            "register": "calm-reassuring",
            "formality": "neutral",
            "dialect_default": "msa_with_dialect_layer",
            "msa_tolerance": "high",
            "english_codeswitching_tolerance": "low",
        },
        "default_visual": {
            "primary_palette": ["#FFFFFF", "#E8F0F4", "#1FBDFF", "#1F2A2E"],
            "secondary_accents": ["#28D9A8", "#F5BEB7"],
            "lighting_default": "clean diffuse fill, no harsh shadows, clinical-but-warm",
            "composition_default": "centered subject, ample whitespace, calm symmetry",
            "texture_default": "smooth surfaces, gentle gradients, minimal pattern",
        },
        "default_cinematography": {
            "lens_default": "35-50mm; controlled handheld OK",
            "depth_of_field": "medium (subject prominent, environment present)",
            "camera_height": "eye-level; never below subject",
            "motion_grammar": "slow push · steady-cam · no jolt cuts",
        },
        "default_cultural_spec": {
            "bilingual_ratio": "Arabic-primary 70/30",
            "humor_tolerance": "none",
            "religious_sensitivity": "high",
            "modesty_level": "high",
            "modesty_threshold_note": "Same-gender depiction default for personal-care contexts. Mixed-gender allowed only in family or general-clinic contexts.",
            "tone_attributes": ["reassuring", "credible", "respectful"],
            "tone_anti_attributes": ["alarmist", "humorous", "sales-pressured"],
            "visual_style": ["clean clinical", "human-warmth-balanced"],
            "visual_anti_style": ["bold graphic", "documentary realism"],
            "ramadan_relevance": "low",
            "eid_fitr_relevance": "low",
            "eid_adha_relevance": "low",
            "national_day_relevance": "medium",
            "founding_day_relevance": "low",
            "summer_shift_intensity": "minor",
            "posting_frequency_default": "3x per week",
            "posting_time_weekday_default": "10:00 AST",
            "posting_time_ramadan_default": "11:00 AST",
            "content_mix": {"awareness_pct": 60, "engagement_pct": 25, "conversion_pct": 15},
            "confidence_floor": 0.7,
        },
        "default_eligible_chains": [
            chain_ref("tf04_01", 0.85),  # Bathroom Marble Counter — clinical clean
            chain_ref("tf23_01", 0.82),  # Saudi Woman Lifestyle — Coffee Moment (wellness)
            chain_ref("tf23_09", 0.80),  # Saudi Mother & Daughter Moment — family wellness
            chain_ref("tf03_03", 0.78),  # Column Light From Above — clinical lighting
            chain_ref("tf06_01", 0.75),  # Twin Softbox Studio Reveal — clean product
            chain_ref("tf01_03", 0.72),  # Product Hero Static
            chain_ref("tf16_02", 0.70),  # Occasion Greeting
            chain_ref("tf22_04", 0.68),  # Occasion Announcement Video
            chain_ref("tf21_02", 0.65),  # New Arrival / Launch
            chain_ref("tf23_04", 0.62),  # Hands-Only Product Interaction
        ],
        "default_occasions_priority": [
            {"occasion_slug": "saudi_national_day", "priority": 0.60},
            {"occasion_slug": "saudi_founding_day", "priority": 0.40},
            {"occasion_slug": "ramadan", "priority": 0.50},
            {"occasion_slug": "eid_al_fitr", "priority": 0.40},
            {"occasion_slug": "eid_al_adha", "priority": 0.30},
        ],
        "default_kpis_focus": [
            "appointment_bookings",
            "qualified_inquiry_volume",
            "trust_indicators",
            "long_form_engagement",
        ],
        "forbidden_topics_sector_specific": [
            "medical claims without SFDA / MoH clearance",
            "prescription drug references in promotional context",
            "before/after with implied medical outcomes",
            "weight-loss promises with timelines",
            "fear-based messaging on diagnoses",
            "patient identifiable information",
        ],
        "default_cd_brain_routing_bias": {
            "cd_01_firaasa": 0.80,
            "cd_02_metaphor": 0.55,
            "cd_03_authenticity": 0.90,
            "cd_04_heritage": 0.45,
            "cd_05_paradox": 0.35,
        },
        "notes": "EXTRAPOLATED — source xlsx did not cover Healthcare/Wellness. Values inferred from beauty/wellness chain overlap + Saudi SFDA + MoH regulatory environment + Vision 2030 health-sector growth. Confidence floor raised to 0.7 due to regulatory risk. MUST be validated by Cultural Advisor and a healthcare-marketing compliance reviewer before production use.",
        "provenance": common_provenance(
            source_ref="inference:beauty_sector_overlap + Saudi_health_regulatory_2026",
            scope="sector:healthcare_wellness",
        ),
    }


def write_yaml(data: dict, path: Path) -> None:
    """Write YAML with our conventions: leading comment, --- separator, 2-space indent."""
    header = f"# {path.name}\n# Schema: 12_data_shapes/sector_baseline_v1.schema.json\n# Confidence: {data['provenance']['confidence']}\n# Scope: {data['provenance']['scope']}\n\n---\n"
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    path.write_text(header + body)


def main() -> int:
    sectors = [f_and_b(), retail(), beauty(), real_estate(), healthcare_wellness()]
    for s in sectors:
        path = OUT_DIR / f"{s['sector_slug']}.yaml"
        write_yaml(s, path)
        print(f"✓ {path.relative_to(REPO)}  ({len(s['default_eligible_chains'])} chains · "
              f"{s['provenance']['confidence']})")
    print(f"\nWrote {len(sectors)} sector baselines to {OUT_DIR.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
