#!/usr/bin/env python3
"""
build_format_occasion_matrix.py
Content format (video / carousel / image / reel / story) × 16 canonical occasions.
Agency question: "For Ramadan, should we produce a video or a carousel?"
Also: format × sector, format × composition (production alignment check).
Output: logs/format_occasion_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

# Format normalisation
FORMAT_NORM = {
    "video": "video",
    "reel": "video",
    "instagram_reel": "video",
    "carousel_slide": "carousel",
    "carousel": "carousel",
    "image": "image",
    "photo": "image",
    "static_image": "image",
    "story": "story",
    "instagram_story": "story",
    "graphic": "graphic",
    "infographic": "graphic",
}


def norm_format(raw: str) -> str:
    return FORMAT_NORM.get(raw.lower().strip(), raw.lower().strip() or "unknown")


def main():
    # format × occasion
    fmt_occ    = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0,"sum":0.0}))
    # format × sector
    fmt_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0,"sum":0.0}))
    # format × composition
    fmt_comp   = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # format base stats
    fmt_base   = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"occasions":Counter(),"sectors":Counter()})
    # occasion base stats
    occ_base   = defaultdict(lambda: {"count":0,"formats":Counter()})

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cr  = data.get("content_ref",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}
        cn  = data.get("cultural_notes",{}) or {}
        vv  = data.get("visual_observations",{}) or {}

        raw_fmt = str(cr.get("content_type","") or "").lower()
        fmt     = norm_format(raw_fmt) if raw_fmt else "unknown"
        occ     = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"
        sector  = data.get("sector","unknown") or "unknown"
        comp    = str(vv.get("composition_style","") or "").lower() or "unknown"

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        fmt_occ[fmt][occ]["count"] += 1
        fmt_occ[fmt][occ]["high"]  += is_high
        fmt_occ[fmt][occ]["sum"]   += eng

        fmt_sector[fmt][sector]["count"] += 1
        fmt_sector[fmt][sector]["high"]  += is_high
        fmt_sector[fmt][sector]["sum"]   += eng

        fmt_comp[fmt][comp]["count"] += 1
        fmt_comp[fmt][comp]["high"]  += is_high

        fmt_base[fmt]["count"]  += 1
        fmt_base[fmt]["high"]   += is_high
        fmt_base[fmt]["sum"]    += eng
        fmt_base[fmt]["occasions"][occ] += 1
        fmt_base[fmt]["sectors"][sector] += 1

        occ_base[occ]["count"] += 1
        occ_base[occ]["formats"][fmt] += 1

    # Format performance table
    fmt_table = []
    for fmt, d in fmt_base.items():
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        fmt_table.append({
            "format": fmt,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "top_occasion": d["occasions"].most_common(1)[0][0] if d["occasions"] else None,
            "top_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    fmt_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Format × occasion matrix (best format per occasion)
    best_format_per_occasion = {}
    full_fmt_occ_matrix = []
    for fmt, occs in fmt_occ.items():
        for occ, d in occs.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            full_fmt_occ_matrix.append({
                "format": fmt, "occasion": occ, "count": n,
                "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
            })
            if n >= 2 and rate > best_format_per_occasion.get(occ, {}).get("rate", -1):
                best_format_per_occasion[occ] = {
                    "format": fmt, "rate": rate, "n": n,
                    "recommendation": _fmt_recommendation(fmt, rate)
                }
    full_fmt_occ_matrix.sort(key=lambda x: (-x["high_eng_rate"], -x["count"]))

    # Format × sector matrix
    fmt_sector_table = []
    for fmt, sectors in fmt_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            fmt_sector_table.append({
                "format": fmt, "sector": sector, "count": n,
                "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
            })
    fmt_sector_table.sort(key=lambda x: (-x["high_eng_rate"], -x["count"]))

    # Occasion format mix (what formats each occasion uses)
    occasion_format_mix = {}
    for occ, d in occ_base.items():
        total_occ = d["count"]
        mix = {fmt: round(cnt/total_occ, 3) for fmt, cnt in d["formats"].items()}
        occasion_format_mix[occ] = {
            "total_obs": total_occ,
            "format_mix": dict(sorted(mix.items(), key=lambda x: -x[1])),
            "dominant_format": d["formats"].most_common(1)[0][0] if d["formats"] else None,
        }

    # Key findings
    findings = []
    if fmt_table:
        best = fmt_table[0]
        findings.append(f"Best format overall: '{best['format']}' = {int(best['high_engagement_rate']*100)}% high eng (n={best['obs_count']})")
        worst = fmt_table[-1]
        findings.append(f"Worst format: '{worst['format']}' = {int(worst['high_engagement_rate']*100)}% (n={worst['obs_count']})")
    for occ, info in sorted(best_format_per_occasion.items()):
        if info["n"] >= 3:
            findings.append(f"{occ.replace('_',' ').title()}: best format = '{info['format']}' at {int(info['rate']*100)}% (n={info['n']})")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "format_engagement_table": fmt_table,
        "best_format_per_occasion": best_format_per_occasion,
        "format_x_occasion_matrix": full_fmt_occ_matrix,
        "format_x_sector": fmt_sector_table,
        "occasion_format_distribution": occasion_format_mix,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "format_occasion_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Format × Occasion matrix: {total} obs")
    print(f"\nFormat performance:")
    print(f"  {'Format':<16} {'HighEng':>8}  {'Lift':>7}  {'n':>4}")
    print("  " + "─"*42)
    for r in fmt_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['format']:<16} {int(r['high_engagement_rate']*100):>7}%  {lift:>7}  {r['obs_count']:>4}")
    print(f"\nBest format per occasion (n≥2):")
    for occ, info in sorted(best_format_per_occasion.items()):
        print(f"  {occ.replace('_',' '):<30} → {info['format']:<12} {int(info['rate']*100):>3}%  n={info['n']}")
    print(f"\nOutput: logs/format_occasion_matrix.json")


def _fmt_recommendation(fmt: str, rate: float) -> str:
    if rate >= 0.75:   return f"strongly_recommend_{fmt}"
    elif rate >= 0.55: return f"recommend_{fmt}"
    elif rate >= 0.40: return f"use_cautiously_{fmt}"
    else:              return f"avoid_{fmt}_for_this_occasion"


if __name__ == "__main__":
    main()
