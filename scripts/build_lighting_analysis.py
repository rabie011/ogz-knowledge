#!/usr/bin/env python3
"""
build_lighting_analysis.py
Lighting style × engagement — which lighting converts in Saudi content?
Output: logs/lighting_analysis.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""),None)

def main():
    lighting_eng    = defaultdict(list)
    sector_lighting = defaultdict(lambda: defaultdict(list))
    occ_lighting    = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        lit = d.get("visual_observations",{}).get("lighting","")
        if not lit: continue
        e   = _eng(d)
        if e is None: continue
        lighting_eng[lit].append(e)
        sec = d.get("sector","")
        if sec: sector_lighting[sec][lit].append(e)
        occ = d.get("occasion","") or ""
        if occ and occ != "evergreen": occ_lighting[occ][lit].append(e)

    global_avg = sum(v for vals in lighting_eng.values() for v in vals) / max(sum(len(v) for v in lighting_eng.values()),1)

    by_lighting = {}
    for lit, vals in sorted(lighting_eng.items(), key=lambda x: -sum(x[1])/max(len(x[1]),1)):
        avg = round(sum(vals)/len(vals),3)
        by_lighting[lit] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg,3),
            "high_rate": round(sum(1 for v in vals if v>=0.75)/len(vals),3),
        }

    # Best lighting per sector
    best_by_sector = {}
    for sec, lits in sector_lighting.items():
        ranked = sorted(lits.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_sector[sec] = [
            {"lighting": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:3]
        ]

    ranked = sorted(by_lighting.items(), key=lambda x: x[1]["avg_engagement"], reverse=True)
    best   = ranked[0][0] if ranked else "—"
    worst  = ranked[-1][0] if ranked else "—"

    out = {
        "total_obs": sum(len(v) for v in lighting_eng.values()),
        "global_avg": round(global_avg,3),
        "by_lighting": by_lighting,
        "best_by_sector": best_by_sector,
        "agency_rules": [
            f"Best lighting: '{best}' ({by_lighting[best]['avg_engagement']:.0%} eng)",
            f"Avoid: '{worst}' ({by_lighting[worst]['avg_engagement']:.0%} eng)",
        ] if ranked else [],
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "lighting_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Lighting × engagement — {out['total_obs']} obs  (global avg {global_avg:.0%})")
    for lit, data in list(by_lighting.items())[:10]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {lit:<22}  {data['avg_engagement']:.0%}  lift {lift:>6}  n={data['count']}")
    for rule in out["agency_rules"]:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/lighting_analysis.json")

if __name__ == "__main__":
    main()
