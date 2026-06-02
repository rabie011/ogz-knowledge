"""
normalize_gpt.py — Single source of truth for normalizing GPT output.

Every script that receives GPT-structured output MUST pass it through
these normalizers. Fixes bugs #1, #9, #15, #36, #37 from month 1.

Usage:
    from lib.normalize_gpt import normalize_obs_fields, normalize_slug, normalize_sector
"""
import re

# ─── Enum Maps ──────────────────────────────────────────────────────────────

CONFIDENCE_MAP = {
    "high": "strong", "medium": "moderate", "low": "weak",
    "strong": "strong", "moderate": "moderate", "weak": "weak",
}

ENGAGEMENT_MAP = {
    "high": "high", "medium": "medium", "low": "low",
}

COMPLIANCE_MAP = {
    "clean": "clean", "soft_flagged": "soft_flagged", "hard_blocked": "hard_blocked",
    "flagged": "soft_flagged", "blocked": "hard_blocked",
}

QUALITY_MAP = {
    "professional": "professional", "semi_professional": "semi_professional",
    "ugc": "ugc", "low": "low",
    "semi-professional": "semi_professional", "user_generated": "ugc",
}

LANGUAGE_MAP = {
    "arabic": "arabic", "english": "english", "bilingual": "bilingual", "none": "none",
    "arabic_and_english": "bilingual", "mixed": "bilingual", "ar": "arabic", "en": "english",
}

CONTENT_TYPE_MAP = {
    "image": "image", "video": "video", "carousel_slide": "carousel_slide",
    "story": "story", "reel": "reel",
    "carousel": "carousel_slide", "photo": "image", "reels": "reel",
}


# ─── Slug Normalizer ───────────────────────────────────────────────────────

def normalize_slug(raw: str) -> str:
    """Normalize a pattern slug: lowercase, underscores, no special chars."""
    if not raw or not isinstance(raw, str):
        return ""
    s = raw.strip().lower().replace(" ", "_").replace("-", "_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s


# ─── Sector Normalizer ─────────────────────────────────────────────────────

SECTOR_ALIASES = {
    "food_and_beverage": "f_and_b",
    "beauty": "beauty_personal_care",
    "retail": "retail_lifestyle",
    "food": "f_and_b",
    "fnb": "f_and_b",
    "f&b": "f_and_b",
    "wellness": "healthcare_wellness",
    "health": "healthcare_wellness",
    "healthcare": "healthcare_wellness",
    "realestate": "real_estate",
    "real-estate": "real_estate",
}

CANONICAL_SECTORS = {
    "f_and_b", "beauty_personal_care", "retail_lifestyle",
    "fashion", "real_estate", "healthcare_wellness",
}

def normalize_sector(raw: str) -> str:
    """Resolve a sector string to its canonical form."""
    if not raw or not isinstance(raw, str):
        return ""
    s = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if s in CANONICAL_SECTORS:
        return s
    return SECTOR_ALIASES.get(s, s)


# ─── Type Coercion ─────────────────────────────────────────────────────────

def to_bool(val) -> bool | None:
    """Convert GPT string booleans to actual bools. Returns None if ambiguous."""
    if isinstance(val, bool):
        return val
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("true", "yes", "1", "full", "present"):
        return True
    if s in ("false", "no", "0", "none", "absent"):
        return False
    return None


def normalize_enum(val: str, enum_map: dict, default: str = "") -> str:
    """Look up a value in an enum map, return default if not found."""
    if not val or not isinstance(val, str):
        return default
    return enum_map.get(val.strip().lower(), default)


# ─── Full Obs Field Normalizer ─────────────────────────────────────────────

def normalize_obs_fields(obs: dict) -> dict:
    """Normalize all GPT-derived fields in an observation dict. Mutates in place."""

    # content_ref
    cr = obs.get("content_ref", {})
    if cr.get("content_type"):
        cr["content_type"] = normalize_enum(cr["content_type"], CONTENT_TYPE_MAP, cr["content_type"])

    # quality_assessment
    qa = obs.get("quality_assessment", {})
    if qa.get("engagement_potential"):
        qa["engagement_potential"] = normalize_enum(qa["engagement_potential"], ENGAGEMENT_MAP, qa["engagement_potential"])
    if qa.get("overall_compliance"):
        qa["overall_compliance"] = normalize_enum(qa["overall_compliance"], COMPLIANCE_MAP, "clean")
    if qa.get("production_quality"):
        qa["production_quality"] = normalize_enum(qa["production_quality"], QUALITY_MAP, qa["production_quality"])

    # voice_observations
    vo = obs.get("voice_observations", {})
    if vo.get("language"):
        vo["language"] = normalize_enum(vo["language"], LANGUAGE_MAP, vo["language"])

    # visual_observations
    vis = obs.get("visual_observations", {})
    hp = vis.get("human_presence")
    if hp is not None and not isinstance(hp, bool):
        vis["human_presence"] = to_bool(hp)

    # pattern_matches
    for pm in obs.get("pattern_matches", []):
        if pm.get("pattern_slug"):
            pm["pattern_slug"] = normalize_slug(pm["pattern_slug"])
        if pm.get("confidence"):
            pm["confidence"] = normalize_enum(pm["confidence"], CONFIDENCE_MAP, "moderate")

    # sector
    if obs.get("sector"):
        obs["sector"] = normalize_sector(obs["sector"])

    return obs
