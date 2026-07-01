#!/usr/bin/env python3
"""occasion_keys.py — THE one shared occasion-key normalization for the weiblocks export.

Audit finding (Rule #6 consumer-law, 3 broken joins): sector.typical_occasions, brand_observation
.occasions_seen/example_captions, and occasion.occasion_key each used DIFFERENT naming conventions
(YAML long slugs vs spec short keys vs scraped free-text), so cross-entity joins silently failed.
One-enforced-boundary lesson: normalize in ONE module read by every builder — never per-script maps.

normalize(slug) -> (occasion_key | None, kept_original)
  - returns the spec occasion_key when the slug maps to a SHIPPED occasion
  - returns None for non-occasion tokens (evergreen/general/seasonal) — caller keeps the original
    in extra; joins must never carry a key that doesn't resolve.
"""

# canonical spec keys = exports/weiblocks_v1/occasions.json occasion_key values (14 shipped)
SHIPPED_KEYS = {
    "ramadan", "eid_fitr", "eid_adha", "hajj_season", "national_day", "founding_day",
    "riyadh_season", "jeddah_season", "white_friday", "singles_day", "mothers_day",
    "esports_world_cup", "leap_conference", "soundstorm",
}

# every alias seen across the corpus (YAML long slugs, scraped tokens, Arabic-cluster shorts)
ALIASES = {
    # YAML long slugs (06_saudi_calendar source + 05_sector_defaults typical_occasions)
    "eid_al_fitr": "eid_fitr", "eid_al_adha": "eid_adha",
    "saudi_national_day": "national_day", "saudi_founding_day": "founding_day",
    "arab_mothers_day": "mothers_day", "mdl_beast": "soundstorm",
    "11_11_shopping": "singles_day", "mdl_beast_soundstorm": "soundstorm",
    # scraped observation tokens
    "hajj": "hajj_season", "eid": "eid_fitr", "day_of_arafah": "hajj_season",
    "national day": "national_day", "founding day": "founding_day",
    # identity for keys already canonical
    **{k: k for k in SHIPPED_KEYS},
}

# tokens that are NOT occasions — callers must not emit them as occasion keys
NON_OCCASION = {"evergreen", "general", "seasonal", "daily", "none", "", "vision_2030",
                "unknown", "n/a", "na"}


def normalize(slug):
    """-> (occasion_key or None, original). None = keep original out of key fields (extra only)."""
    if slug is None:
        return None, slug
    s = str(slug).strip().lower()
    if s in NON_OCCASION:
        return None, slug
    return ALIASES.get(s), slug


def normalize_list(slugs):
    """map a list -> (sorted unique resolved keys, unresolved originals)."""
    keys, unresolved = set(), []
    for s in (slugs or []):
        k, orig = normalize(s)
        if k:
            keys.add(k)
        elif str(s).strip():
            unresolved.append(orig)
    return sorted(keys), unresolved
