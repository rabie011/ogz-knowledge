#!/usr/bin/env python3
"""
build_visual_sector_intel.py
Per-sector visual intelligence: best lighting, setting, color palette,
and composition by sector — derived from engagement_potential correlations.

Output: logs/visual_sector_intel.json
"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
OUT      = BASE / "logs" / "visual_sector_intel.json"

MIN_N = 5   # minimum observations to report a finding


def _rate(vals: list[int]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def build():
    # Collect sector × dimension × value → engagement values
    sector_light   = defaultdict(lambda: defaultdict(list))
    sector_setting = defaultdict(lambda: defaultdict(list))
    sector_palette = defaultdict(lambda: defaultdict(list))
    sector_comp    = defaultdict(lambda: defaultdict(list))
    sector_total   = defaultdict(list)

    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue

        sector = d.get("sector", "")
        if not sector:
            continue

        qa = d.get("quality_assessment") or {}
        ep = qa.get("engagement_potential", "")
        high = int(ep == "high")
        sector_total[sector].append(high)

        vo = d.get("visual_observations") or {}

        light = (vo.get("lighting") or "").strip()
        if light:
            sector_light[sector][light].append(high)

        setting = (vo.get("setting") or "").strip()
        if setting and setting not in ("unknown", ""):
            sector_setting[sector][setting].append(high)

        palette = vo.get("color_palette_dominant") or []
        for c in palette[:2]:
            c = (c or "").strip().lower()
            if c:
                sector_palette[sector][c].append(high)

        comp = (vo.get("composition_style") or "").strip()
        if comp:
            sector_comp[sector][comp].append(high)

    # Build per-sector summaries
    result = {}
    for sector in sorted(sector_total.keys()):
        sector_avg = _rate(sector_total[sector])
        n_total    = len(sector_total[sector])

        def _top_bottom(dim_dict, top_n=3):
            valid = {k: v for k, v in dim_dict.items() if len(v) >= MIN_N}
            if not valid:
                return [], []
            ranked = sorted(valid.items(), key=lambda x: _rate(x[1]), reverse=True)
            tops = [
                {"value": k, "engagement_rate": round(_rate(v), 3),
                 "lift": round(_rate(v) - sector_avg, 3), "n": len(v)}
                for k, v in ranked[:top_n]
            ]
            bottoms = [
                {"value": k, "engagement_rate": round(_rate(v), 3),
                 "lift": round(_rate(v) - sector_avg, 3), "n": len(v)}
                for k, v in ranked[-top_n:] if _rate(v) < sector_avg
            ]
            return tops, bottoms

        light_top,   light_bottom   = _top_bottom(sector_light[sector])
        setting_top, setting_bottom = _top_bottom(sector_setting[sector])
        palette_top, palette_bottom = _top_bottom(sector_palette[sector], top_n=5)
        comp_top,    comp_bottom    = _top_bottom(sector_comp[sector])

        result[sector] = {
            "total_obs":    n_total,
            "sector_avg":   round(sector_avg, 3),
            "lighting": {
                "best":  light_top,
                "worst": light_bottom,
            },
            "setting": {
                "best":  setting_top,
                "worst": setting_bottom,
            },
            "color_palette": {
                "top_colors": palette_top,
            },
            "composition": {
                "best":  comp_top,
                "worst": comp_bottom,
            },
            "agency_directives": _build_directives(
                sector, sector_avg, light_top, setting_top, comp_top
            ),
        }

    out = {
        "schema_version": 1,
        "generated_at":   datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_obs":      sum(len(v) for v in sector_total.values()),
        "sectors":        result,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Visual sector intel — {len(result)} sectors | {out['total_obs']} obs")
    for sector, data in result.items():
        avg = data["sector_avg"]
        best_light = data["lighting"]["best"][0]["value"] if data["lighting"]["best"] else "—"
        best_setting = data["setting"]["best"][0]["value"] if data["setting"]["best"] else "—"
        print(
            f"  {sector:25}  avg={avg:.0%}  "
            f"best_light={best_light:20}  best_setting={best_setting}"
        )
    print(f"\nOutput: logs/visual_sector_intel.json")


def _build_directives(sector, avg, light_top, setting_top, comp_top) -> list[str]:
    directives = []
    if light_top:
        best = light_top[0]
        if best["lift"] > 0.10:
            directives.append(
                f"Use '{best['value']}' lighting for {sector} — "
                f"{best['engagement_rate']:.0%} eng rate ({best['lift']:+.0%} lift)"
            )
    if setting_top:
        best = setting_top[0]
        if best["lift"] > 0.10:
            directives.append(
                f"Prioritise '{best['value']}' settings — "
                f"{best['engagement_rate']:.0%} eng ({best['lift']:+.0%} lift)"
            )
    if comp_top:
        best = comp_top[0]
        if best["lift"] > 0.05:
            directives.append(
                f"'{best['value']}' composition outperforms sector avg by {best['lift']:+.0%}"
            )
    return directives


if __name__ == "__main__":
    build()
