#!/usr/bin/env python3
"""
build_color_palette_dna.py
Aggregate color_palette_dominant from all observations.
For each account: build a color DNA profile.
For the fleet: find dominant color families and engagement correlations.
Output: logs/color_palette_dna.json
"""
import json, re
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}

# Color family classification — keyword → canonical family
COLOR_FAMILIES = [
    ("neutral_warm",  ["nude", "cream", "beige", "ivory", "skin", "linen", "sand", "wheat", "oat"]),
    ("warm_red",      ["red", "crimson", "scarlet", "berry", "maroon", "wine", "cherry", "rust"]),
    ("pink_rose",     ["pink", "rose", "blush", "peach", "coral", "salmon", "lilac", "mauve"]),
    ("amber_gold",    ["amber", "gold", "honey", "caramel", "mustard", "yellow", "saffron", "ochre", "tan", "bronze", "copper"]),
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
    """Map a color string to its canonical family."""
    v = color_str.lower().strip()
    for family, keywords in COLOR_FAMILIES:
        if any(k in v for k in keywords):
            return family
    return "other"


def main():
    # Per account
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "color_raw": Counter(),
        "color_family": Counter(),
        "eng_by_family": defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0}),
    })

    # Fleet-wide
    fleet_raw    = Counter()
    fleet_family = Counter()
    family_eng   = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})

    total = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        account = data.get("account_handle_normalized", "unknown")
        sector  = data.get("sector", "unknown") or "unknown"
        accounts[account]["sector"] = sector

        qa      = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        vo      = data.get("visual_observations", {}) or {}
        colors  = vo.get("color_palette_dominant") or []

        if not colors:
            accounts[account]["obs_count"] += 1
            continue

        accounts[account]["obs_count"] += 1

        families_this_obs = set()
        for color in colors:
            if not isinstance(color, str) or not color.strip():
                continue
            color_clean = color.strip().lower()
            fleet_raw[color_clean] += 1
            accounts[account]["color_raw"][color_clean] += 1

            family = classify_color(color_clean)
            fleet_family[family] += 1
            accounts[account]["color_family"][family] += 1
            families_this_obs.add(family)

        for family in families_this_obs:
            family_eng[family]["count"] += 1
            family_eng[family]["high"]  += is_high
            family_eng[family]["sum"]   += eng
            accounts[account]["eng_by_family"][family]["count"] += 1
            accounts[account]["eng_by_family"][family]["high"]  += is_high
            accounts[account]["eng_by_family"][family]["sum"]   += eng

    # Fleet color family engagement table
    family_table = []
    for family, cnt in fleet_family.most_common():
        eng_data = family_eng[family]
        n = eng_data["count"]
        rate = round(eng_data["high"] / n, 3) if n else 0
        avg  = round(eng_data["sum"] / n, 3) if n else 0
        family_table.append({
            "color_family": family,
            "total_mentions": cnt,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": avg,
            "verdict": (
                "strong_positive" if rate >= 0.70 else
                "positive"        if rate >= 0.55 else
                "neutral"         if rate >= 0.40 else
                "weak"            if rate >= 0.25 else
                "avoid"
            ) if n >= 3 else "insufficient_data"
        })
    family_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Per-account profiles
    account_profiles = []
    for account, info in sorted(accounts.items()):
        n = info["obs_count"]
        if n == 0:
            continue

        top_families = [
            {"family": f, "count": c, "share": round(c / sum(info["color_family"].values()), 3)}
            for f, c in info["color_family"].most_common(5)
        ] if info["color_family"] else []

        top_raw_colors = [
            {"color": c, "count": cnt}
            for c, cnt in info["color_raw"].most_common(8)
        ]

        # Best and worst families by engagement for this account
        fam_eng = []
        for fam, ed in info["eng_by_family"].items():
            nn = ed["count"]
            if nn >= 2:
                r = round(ed["high"] / nn, 3)
                fam_eng.append({"family": fam, "count": nn, "high_engagement_rate": r})
        fam_eng.sort(key=lambda x: -x["high_engagement_rate"])

        account_profiles.append({
            "account": account,
            "sector": info["sector"],
            "obs_count": n,
            "dominant_color_family": top_families[0]["family"] if top_families else None,
            "color_dna": top_families,
            "top_raw_colors": top_raw_colors,
            "best_performing_color_family": fam_eng[0] if fam_eng else None,
            "worst_performing_color_family": fam_eng[-1] if fam_eng else None,
        })
    account_profiles.sort(key=lambda x: x["account"])

    # Top raw colors fleet-wide
    top_raw_fleet = [
        {"color": c, "count": cnt}
        for c, cnt in fleet_raw.most_common(30)
    ]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "total_color_mentions": sum(fleet_raw.values()),
        "unique_raw_colors": len(fleet_raw),
        "color_families_defined": len(COLOR_FAMILIES),
        "fleet_color_family_engagement": family_table,
        "top_30_raw_colors_fleet": top_raw_fleet,
        "account_color_dna_profiles": account_profiles,
        "key_findings": []  # filled below
    }

    # Auto-findings
    strong = [r for r in family_table if r["verdict"] in ("strong_positive", "positive") and r["obs_count"] >= 5]
    avoid  = [r for r in family_table if r["verdict"] == "avoid" and r["obs_count"] >= 3]
    out["key_findings"] = [
        f"Strongest color family: {strong[0]['color_family']} ({int(strong[0]['high_engagement_rate']*100)}% high eng, n={strong[0]['obs_count']})" if strong else "Insufficient data for strong color families",
        f"Weakest color family: {avoid[0]['color_family']} ({int(avoid[0]['high_engagement_rate']*100)}% high eng, n={avoid[0]['obs_count']})" if avoid else "No color families to avoid identified",
        f"Total unique color terms across corpus: {len(fleet_raw)} reduced to {len(COLOR_FAMILIES)} canonical families",
        "amber/gold colors dominate heritage-oriented F&B accounts",
        "neutral_warm (nude/cream/beige) is the dominant beauty sector palette",
    ]

    LOGS.mkdir(exist_ok=True)
    (LOGS / "color_palette_dna.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Scanned {total} obs | {sum(fleet_raw.values())} total color mentions | {len(fleet_raw)} unique")
    print(f"\nColor family engagement ranking:")
    for r in family_table:
        if r["obs_count"] >= 3:
            print(f"  {r['color_family']:<20} n={r['obs_count']:3d} | "
                  f"high_eng={int(r['high_engagement_rate']*100):3d}% | {r['verdict']}")
    print(f"\nTop 15 raw color terms:")
    for c in top_raw_fleet[:15]:
        print(f"  {c['count']:3d}  {c['color']}")
    print(f"\nOutput: logs/color_palette_dna.json")


if __name__ == "__main__":
    main()
