#!/usr/bin/env python3
"""
build_visual_dna_profiles.py
Per-account visual fingerprint aggregating:
  - Dominant setting (canonical)
  - Dominant media type
  - Dominant color family
  - Character presence rate
  - Lighting style
  - Composition style

Plus fleet-wide visual patterns and setting × engagement correlations.
Output: logs/visual_dna_profiles.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}

COLOR_FAMILIES = [
    ("neutral_warm",  ["nude", "cream", "beige", "ivory", "skin", "linen", "sand", "wheat", "oat"]),
    ("warm_red",      ["red", "crimson", "scarlet", "berry", "maroon", "wine", "cherry", "rust"]),
    ("pink_rose",     ["pink", "rose", "blush", "peach", "coral", "salmon", "lilac", "mauve"]),
    ("amber_gold",    ["amber", "gold", "honey", "caramel", "mustard", "yellow", "saffron", "ochre", "tan", "bronze", "copper", "golden"]),
    ("brown_earth",   ["brown", "earth", "terracotta", "sienna", "umber", "chocolate", "mocha", "espresso", "coffee", "cocoa"]),
    ("green",         ["green", "sage", "olive", "mint", "emerald", "forest", "teal", "khaki", "lime"]),
    ("blue",          ["blue", "navy", "indigo", "cobalt", "royal", "sky", "cerulean", "denim"]),
    ("purple",        ["purple", "violet", "lavender", "plum", "aubergine"]),
    ("white_light",   ["white", "light", "bright", "pale", "soft", "clean", "airy", "fresh"]),
    ("black_dark",    ["black", "dark", "charcoal", "graphite", "deep", "noir", "onyx", "shadow"]),
    ("grey",          ["grey", "gray", "silver", "slate", "ash", "smoke", "stone"]),
    ("mixed_vibrant", ["vibrant", "bold", "colourful", "colorful", "rainbow", "multi", "rich"]),
]


def classify_color(color_str: str) -> str:
    v = color_str.lower().strip()
    for family, keywords in COLOR_FAMILIES:
        if any(k in v for k in keywords):
            return family
    return "other"


def top_val(counter):
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def main():
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "settings": Counter(),
        "media_types": Counter(),
        "color_families": Counter(),
        "lightings": Counter(),
        "compositions": Counter(),
        "char_present": 0,
        "eng_sum": 0.0,
        "high_count": 0,
        # Per-setting engagement
        "setting_eng": defaultdict(lambda: {"count": 0, "high": 0}),
    })

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        sector  = data.get("sector", "unknown") or "unknown"
        accounts[account]["sector"] = sector
        accounts[account]["obs_count"] += 1

        qa      = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        accounts[account]["eng_sum"]    += eng
        accounts[account]["high_count"] += is_high

        cr = data.get("content_ref", {}) or {}
        mt = str(cr.get("content_type", "unknown") or "unknown").lower().strip()
        accounts[account]["media_types"][mt] += 1

        vo = data.get("visual_observations", {}) or {}

        setting = vo.get("setting")
        if setting and isinstance(setting, str):
            accounts[account]["settings"][setting] += 1
            accounts[account]["setting_eng"][setting]["count"] += 1
            accounts[account]["setting_eng"][setting]["high"]  += is_high

        lighting = vo.get("lighting")
        if lighting and isinstance(lighting, str):
            accounts[account]["lightings"][str(lighting).lower().strip()[:40]] += 1

        composition = vo.get("composition_style")
        if composition and isinstance(composition, str):
            accounts[account]["compositions"][str(composition).lower().strip()[:40]] += 1

        colors = vo.get("color_palette_dominant") or []
        for color in colors:
            if isinstance(color, str) and color.strip():
                fam = classify_color(color)
                accounts[account]["color_families"][fam] += 1

        cv = vo.get("characters_visible")
        char_count = 0
        if isinstance(cv, dict):
            char_count = int(cv.get("count", 0) or 0)
        elif isinstance(cv, list):
            char_count = len(cv)
        if char_count > 0:
            accounts[account]["char_present"] += 1

    # Build profiles
    profiles = []
    for account, info in sorted(accounts.items()):
        n = info["obs_count"]
        if n == 0:
            continue

        avg_eng  = round(info["eng_sum"] / n, 3)
        high_rate = round(info["high_count"] / n, 3)

        # Best and worst settings by engagement for this account
        setting_eng_ranked = []
        for setting, se in info["setting_eng"].items():
            nn = se["count"]
            if nn >= 2:
                rate = round(se["high"] / nn, 3)
                setting_eng_ranked.append({"setting": setting, "count": nn, "high_eng_rate": rate})
        setting_eng_ranked.sort(key=lambda x: -x["high_eng_rate"])

        profile = {
            "account": account,
            "sector": info["sector"],
            "obs_count": n,
            "avg_engagement": avg_eng,
            "high_engagement_rate": high_rate,
            "visual_fingerprint": {
                "dominant_setting": top_val(info["settings"]),
                "dominant_media_type": top_val(info["media_types"]),
                "dominant_color_family": top_val(info["color_families"]),
                "dominant_lighting": top_val(info["lightings"]),
                "dominant_composition": top_val(info["compositions"]),
                "character_presence_rate": round(info["char_present"] / n, 3),
            },
            "setting_distribution": dict(info["settings"].most_common(5)),
            "media_type_distribution": dict(info["media_types"].most_common()),
            "color_family_distribution": dict(info["color_families"].most_common(5)),
            "lighting_distribution": dict(info["lightings"].most_common(5)),
            "best_performing_setting": setting_eng_ranked[0] if setting_eng_ranked else None,
            "worst_performing_setting": setting_eng_ranked[-1] if len(setting_eng_ranked) > 1 else None,
        }
        profiles.append(profile)

    # Fleet-wide visual patterns
    fleet_settings   = Counter()
    fleet_media      = Counter()
    fleet_colors     = Counter()
    fleet_lightings  = Counter()
    fleet_comps      = Counter()

    for info in accounts.values():
        fleet_settings.update(info["settings"])
        fleet_media.update(info["media_types"])
        fleet_colors.update(info["color_families"])
        fleet_lightings.update(info["lightings"])
        fleet_comps.update(info["compositions"])

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_accounts": len(profiles),
        "fleet_visual_summary": {
            "dominant_setting": top_val(fleet_settings),
            "dominant_media_type": top_val(fleet_media),
            "dominant_color_family": top_val(fleet_colors),
            "setting_distribution": dict(fleet_settings.most_common(12)),
            "media_type_distribution": dict(fleet_media.most_common()),
            "color_family_distribution": dict(fleet_colors.most_common(10)),
            "top_lighting_styles": dict(fleet_lightings.most_common(10)),
            "top_composition_styles": dict(fleet_comps.most_common(10)),
        },
        "account_visual_dna_profiles": sorted(profiles, key=lambda x: -x["avg_engagement"]),
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "visual_dna_profiles.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Visual DNA profiles for {len(profiles)} accounts")
    print(f"\nFleet visual summary:")
    print(f"  Dominant setting:    {top_val(fleet_settings)}")
    print(f"  Dominant media type: {top_val(fleet_media)}")
    print(f"  Dominant color:      {top_val(fleet_colors)}")
    print(f"\nAccount visual fingerprints (sorted by avg engagement):")
    for prof in profiles:
        vf = prof["visual_fingerprint"]
        print(f"  {prof['account'][-30:]:<32} | "
              f"eng={int(prof['avg_engagement']*100)}% | "
              f"setting={vf['dominant_setting'] or 'N/A'} | "
              f"media={vf['dominant_media_type'] or 'N/A'} | "
              f"color={vf['dominant_color_family'] or 'N/A'} | "
              f"chars={int(vf['character_presence_rate']*100)}%")
    print(f"\nOutput: logs/visual_dna_profiles.json")


if __name__ == "__main__":
    main()
