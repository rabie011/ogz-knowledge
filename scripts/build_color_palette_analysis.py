#!/usr/bin/env python3
"""
build_color_palette_analysis.py
Mine color_palette_dominant — 474/474 coverage, completely unmined.
Each obs has a list of dominant colors (e.g., ['golden brown', 'green', 'cream']).
Agency questions:
  - Which dominant colors appear in high-engagement posts?
  - Do gold/earth tones outperform cool/modern colors?
  - How many colors in the palette is optimal?
  - What color combos win for each occasion?
Output: logs/color_palette_analysis.json
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

# Color family clustering — map raw color strings → canonical families
COLOR_FAMILIES = {
    "warm_heritage": ["gold","golden","amber","bronze","copper","tan","caramel","cream","beige","ivory","wheat","brown","golden_brown","sand"],
    "rich_red":      ["red","crimson","maroon","burgundy","scarlet","rose","brick","terracotta"],
    "fresh_green":   ["green","mint","sage","olive","emerald","lime","teal"],
    "deep_dark":     ["black","dark","charcoal","navy","midnight","ebony"],
    "clean_white":   ["white","pearl","snow","off_white","light","pale"],
    "vibrant_pop":   ["orange","yellow","coral","pink","magenta","fuchsia","violet","purple"],
    "cool_blue":     ["blue","sky","azure","cobalt","indigo","royal_blue"],
}


def classify_color(color_str: str) -> str:
    c = color_str.lower().replace("_"," ").replace("-"," ").strip()
    for family, keywords in COLOR_FAMILIES.items():
        if any(k in c for k in keywords):
            return family
    return "other"


def normalize_color(c: str) -> str:
    return re.sub(r'\s+', '_', c.lower().strip())


def main():
    # Individual color tracking
    by_color  = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter()})
    # Color family tracking
    by_family = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter()})
    # Palette size (number of colors) tracking
    by_palette_size = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Heritage color dominance (how many warm_heritage colors in palette)
    by_heritage_ratio = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Color × occasion
    color_occ = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    obs_with_colors = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv  = data.get("visual_observations",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}
        cn  = data.get("cultural_notes",{}) or {}

        palette = vv.get("color_palette_dominant") or []
        if isinstance(palette, str):
            # Try to parse if it's a stringified list
            try:
                import ast
                palette = ast.literal_eval(palette)
            except:
                palette = [palette] if palette.strip() else []
        if not isinstance(palette, list):
            palette = []

        if not palette:
            continue

        obs_with_colors += 1
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector","unknown") or "unknown"
        occ     = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"

        # Palette size
        size_label = str(min(len(palette), 5)) if len(palette) < 5 else "5+"
        by_palette_size[size_label]["count"]  += 1
        by_palette_size[size_label]["high"]   += is_high
        by_palette_size[size_label]["sum"]    += eng

        # Per-color and per-family
        families_in_palette = set()
        heritage_count = 0
        for color_raw in palette:
            if not color_raw or not str(color_raw).strip(): continue
            color = normalize_color(str(color_raw))
            family = classify_color(color)
            if family == "warm_heritage":
                heritage_count += 1

            by_color[color]["count"]  += 1
            by_color[color]["high"]   += is_high
            by_color[color]["sum"]    += eng
            by_color[color]["sectors"][sector] += 1

            if family not in families_in_palette:
                families_in_palette.add(family)
                by_family[family]["count"]  += 1
                by_family[family]["high"]   += is_high
                by_family[family]["sum"]    += eng
                by_family[family]["sectors"][sector] += 1

            if len(color_occ[color][occ]) == 2 or True:
                color_occ[color][occ]["count"] += 1
                color_occ[color][occ]["high"]  += is_high

        # Heritage color ratio in palette
        if palette:
            ratio = heritage_count / len(palette)
            ratio_label = "high_heritage" if ratio >= 0.5 else "low_heritage"
            by_heritage_ratio[ratio_label]["count"]  += 1
            by_heritage_ratio[ratio_label]["high"]   += is_high
            by_heritage_ratio[ratio_label]["sum"]    += eng

    # Individual color table (2+ appearances)
    color_table = []
    for color, d in by_color.items():
        n = d["count"]
        if n < 2: continue
        rate = round(d["high"]/n, 3)
        color_table.append({
            "color": color,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "dominant_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    color_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Family table
    family_table = []
    for family, d in by_family.items():
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        family_table.append({
            "color_family": family,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    family_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Palette size table
    size_table = []
    for size, d in by_palette_size.items():
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        size_table.append({
            "palette_size": size,
            "obs_count": n,
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    size_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Heritage ratio table
    heritage_table = []
    for ratio_label, d in by_heritage_ratio.items():
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        heritage_table.append({
            "heritage_color_ratio": ratio_label,
            "obs_count": n,
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    heritage_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Key findings
    findings = []
    if family_table:
        best = family_table[0]
        findings.append(
            f"Best color family: '{best['color_family']}' = {int(best['high_engagement_rate']*100)}% high eng "
            f"(n={best['obs_count']}, {'+' if best['lift_vs_baseline']>=0 else ''}{int(best['lift_vs_baseline']*100)}pp)"
        )
        worst = family_table[-1]
        findings.append(
            f"Worst color family: '{worst['color_family']}' = {int(worst['high_engagement_rate']*100)}% (n={worst['obs_count']})"
        )
    if color_table:
        best_col = color_table[0]
        findings.append(f"Highest-performing single color: '{best_col['color']}' = {int(best_col['high_engagement_rate']*100)}% (n={best_col['obs_count']})")
    if heritage_table:
        high_h = next((r for r in heritage_table if "high" in r["heritage_color_ratio"]), None)
        low_h  = next((r for r in heritage_table if "low"  in r["heritage_color_ratio"]), None)
        if high_h and low_h:
            diff = high_h["high_engagement_rate"] - low_h["high_engagement_rate"]
            findings.append(
                f"Heritage colors (gold/cream/amber) dominating palette: {int(high_h['high_engagement_rate']*100)}% vs "
                f"non-heritage: {int(low_h['high_engagement_rate']*100)}% ({'+' if diff>=0 else ''}{int(diff*100)}pp)"
            )
    if size_table:
        best_size = size_table[0]
        findings.append(f"Optimal palette size: {best_size['palette_size']} colors = {int(best_size['high_engagement_rate']*100)}% high eng")

    # Agency rules
    agency_rules = []
    if family_table:
        top_families = [f["color_family"] for f in family_table[:3]]
        agency_rules.append(f"Prioritise these color families in art direction: {', '.join(top_families)}")
    if size_table:
        agency_rules.append(f"Optimal palette size: {size_table[0]['palette_size']} dominant colors — don't over-complicate the palette")
    high_heritage = next((r for r in heritage_table if "high" in r["heritage_color_ratio"]), None)
    low_heritage  = next((r for r in heritage_table if "low"  in r["heritage_color_ratio"]), None)
    if high_heritage and low_heritage:
        if high_heritage["lift_vs_baseline"] > low_heritage["lift_vs_baseline"]:
            agency_rules.append("Use warm heritage colors (gold, cream, amber) as dominant palette — they outperform cool modern colors")
        else:
            agency_rules.append("Modern color palettes outperform heritage tones — align with brand positioning")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_color_data": obs_with_colors,
        "color_family_table": family_table,
        "top_individual_colors": color_table[:25],
        "palette_size_table": size_table,
        "heritage_color_ratio_table": heritage_table,
        "agency_rules": agency_rules,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "color_palette_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Color palette analysis: {obs_with_colors}/{total} obs")
    print(f"\nColor family → engagement:")
    print(f"  {'Family':<22} {'HighEng':>8}  {'Lift':>7}  {'n':>4}")
    print("  " + "─"*48)
    for r in family_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['color_family']:<22} {int(r['high_engagement_rate']*100):>7}%  {lift:>7}  {r['obs_count']:>4}")
    print(f"\nTop individual colors:")
    for r in color_table[:10]:
        print(f"  {r['color']:<28} {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nPalette size → engagement:")
    for r in size_table:
        print(f"  {r['palette_size']:<8} colors  {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nHeritage color dominance:")
    for r in heritage_table:
        print(f"  {r['heritage_color_ratio']:<20} {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/color_palette_analysis.json")


if __name__ == "__main__":
    main()
