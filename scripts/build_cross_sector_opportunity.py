#!/usr/bin/env python3
"""
build_cross_sector_opportunity.py
Cross-sector opportunity analysis: what should each sector STEAL from the best?
F&B = 70%, Retail = 49%, Beauty = 42%.
What specific signals, if adopted, close each gap?
Output: logs/cross_sector_opportunity.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _pct(c,t): return round(c/t,3) if t else 0


def main():
    # Per-sector signal distributions + engagement
    DIMS = {
        "content_type":     lambda d: d.get("content_ref",{}).get("content_type",""),
        "aspect_ratio":     lambda d: d.get("content_ref",{}).get("aspect_ratio","") or "",
        "setting":          lambda d: d.get("visual_observations",{}).get("setting","") or "",
        "lighting":         lambda d: d.get("visual_observations",{}).get("lighting","") or "",
        "composition":      lambda d: d.get("visual_observations",{}).get("composition_style","") or "",
        "visual_complexity":lambda d: d.get("visual_observations",{}).get("visual_complexity","") or "",
        "heritage_framing": lambda d: d.get("cultural_notes",{}).get("heritage_vs_modern","") or "",
        "tone":             lambda d: (d.get("voice_observations",{}).get("tone","") or "")[:25],
        "register":         lambda d: (d.get("voice_observations",{}).get("register","") or "")[:25],
        "production_quality":lambda d: d.get("quality_assessment",{}).get("production_quality","") or "",
        "day_of_week":      lambda d: d.get("content_ref",{}).get("day_of_week","") or "",
    }

    sec_dist = defaultdict(lambda: {dim: Counter() for dim in DIMS})  # sector → dim → val → count
    sec_eng_by_dim_val = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # sector → dim → val → [eng]
    sec_eng = defaultdict(list)
    global_dim_eng = defaultdict(lambda: defaultdict(list))  # dim → val → [eng] (all sectors)

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        sec = d.get("sector","")
        if not sec: continue
        if e is not None: sec_eng[sec].append(e)
        for dim, extractor in DIMS.items():
            val = extractor(d)
            if val and str(val).strip():
                val = str(val).strip()
                sec_dist[sec][dim][val] += 1
                if e is not None:
                    sec_eng_by_dim_val[sec][dim][val].append(e)
                    global_dim_eng[dim][val].append(e)

    sec_avgs = {s: _avg(v) or 0 for s,v in sec_eng.items()}
    best_sector = max(sec_avgs, key=sec_avgs.get)

    # Global best value per dimension (corpus-wide)
    global_best_val = {}
    for dim, val_eng in global_dim_eng.items():
        best = max(val_eng.items(), key=lambda x: (_avg(x[1]) or 0) * (len(x[1]) >= 5))
        if len(best[1]) >= 5:
            global_best_val[dim] = {"value": best[0], "avg_engagement": _avg(best[1]), "n": len(best[1])}

    # For each underperforming sector, find opportunities
    opportunity_reports = {}

    for target_sec in sorted(sec_avgs, key=sec_avgs.get):
        if sec_avgs[target_sec] >= sec_avgs[best_sector]: continue  # skip the best sector

        gap = round(sec_avgs[best_sector] - sec_avgs[target_sec], 3)
        opportunities = []

        for dim in DIMS:
            target_total = sum(sec_dist[target_sec][dim].values())
            best_total   = sum(sec_dist[best_sector][dim].values())
            if not target_total or not best_total: continue

            # What does the BEST sector do in this dimension?
            best_val_in_best_sec = sec_dist[best_sector][dim].most_common(1)
            if not best_val_in_best_sec: continue
            best_sec_dominant     = best_val_in_best_sec[0][0]
            best_sec_dominant_pct = _pct(best_val_in_best_sec[0][1], best_total)

            # What does TARGET sector do?
            target_top = sec_dist[target_sec][dim].most_common(1)
            target_dominant = target_top[0][0] if target_top else None
            target_dominant_pct = _pct(target_top[0][1], target_total) if target_top else 0

            # Is there a meaningful difference?
            if best_sec_dominant == target_dominant: continue  # already aligned

            # What's the engagement of the best sector's dominant vs the target sector's current dominant?
            best_val_eng  = _avg(sec_eng_by_dim_val[best_sector][dim].get(best_sec_dominant, []))
            target_val_eng= _avg(sec_eng_by_dim_val[target_sec][dim].get(target_dominant, [])) if target_dominant else None
            global_best_e = (global_best_val.get(dim) or {}).get("avg_engagement")

            # Target's current usage of the best value
            target_usage_of_best = _pct(sec_dist[target_sec][dim].get(best_sec_dominant, 0), target_total)

            if best_val_eng and (target_val_eng is None or best_val_eng > (target_val_eng or 0)):
                potential_uplift = round(best_val_eng - (target_val_eng or sec_avgs[target_sec]), 3)
                if potential_uplift >= 0.05:
                    opportunities.append({
                        "dimension":          dim,
                        "adopt_this":         best_sec_dominant,
                        "adopt_from_sector":  best_sector,
                        "adoption_rate_in_best": best_sec_dominant_pct,
                        "target_current":     target_dominant,
                        "target_current_pct": target_dominant_pct,
                        "target_uses_already":target_usage_of_best,
                        "expected_eng_if_adopted": best_val_eng,
                        "current_eng":        target_val_eng,
                        "potential_uplift":   potential_uplift,
                    })

        opportunities.sort(key=lambda x: -x["potential_uplift"])

        # Also: what IS the target sector already doing right that they should keep?
        keepers = []
        for dim in DIMS:
            target_total = sum(sec_dist[target_sec][dim].values())
            if not target_total: continue
            top_val = sec_dist[target_sec][dim].most_common(1)
            if not top_val: continue
            val     = top_val[0][0]
            val_eng = _avg(sec_eng_by_dim_val[target_sec][dim].get(val, []))
            if val_eng and val_eng >= (sec_avgs[target_sec] + 0.10):
                keepers.append({
                    "dimension": dim,
                    "value": val,
                    "pct": _pct(top_val[0][1], target_total),
                    "avg_engagement": val_eng,
                })
        keepers.sort(key=lambda x: -x["avg_engagement"])

        opportunity_reports[target_sec] = {
            "sector":          target_sec,
            "current_avg":     sec_avgs[target_sec],
            "best_sector_avg": sec_avgs[best_sector],
            "gap_to_close":    gap,
            "top_opportunities": opportunities[:6],
            "keep_doing":      keepers[:3],
        }

    # Summary rules
    rules = []
    for sec, rep in sorted(opportunity_reports.items(), key=lambda x: -x[1]["gap_to_close"]):
        if rep["top_opportunities"]:
            top = rep["top_opportunities"][0]
            rules.append(
                f"{sec} ({rep['current_avg']:.0%}): adopt {top['dimension']}={top['adopt_this']} "
                f"from {top['adopt_from_sector']} → +{top['potential_uplift']:.0%} potential"
            )

    out = {
        "generated_at": "2026-05-24T00:00:00Z",
        "sector_avg_rankings": sorted(sec_avgs.items(), key=lambda x: -x[1]),
        "best_sector": best_sector,
        "global_best_per_dimension": global_best_val,
        "opportunity_reports": opportunity_reports,
        "agency_rules": rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"cross_sector_opportunity.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Cross-sector opportunity analysis\n")
    print(f"Sector performance: {dict(sorted(sec_avgs.items(), key=lambda x: -x[1]))}\n")
    for sec, rep in sorted(opportunity_reports.items(), key=lambda x: -x[1]["gap_to_close"]):
        print(f"  {sec} ({rep['current_avg']:.0%}) — gap to close: {rep['gap_to_close']:.0%}")
        for opp in rep["top_opportunities"][:4]:
            already = f" (already uses {opp['target_uses_already']:.0%})" if opp["target_uses_already"] > 0 else ""
            print(f"    ADOPT: {opp['dimension']}={opp['adopt_this']}  +{opp['potential_uplift']:.0%}{already}")
        for k in rep["keep_doing"][:2]:
            print(f"    KEEP:  {k['dimension']}={k['value']}  ({k['avg_engagement']:.0%})")
        print()
    for r in rules: print(f"  ▸ {r}")
    print(f"  Output → logs/cross_sector_opportunity.json")

if __name__ == "__main__":
    main()
