#!/usr/bin/env python3
"""
build_composition_analysis.py
Composition style × engagement — product_hero vs graphic_text vs overhead_spread etc.
Output: logs/composition_analysis.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""),None)

def main():
    comp_eng = defaultdict(list)
    sec_comp = defaultdict(lambda: defaultdict(list))
    occ_comp = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        comp = d.get("visual_observations",{}).get("composition_style","")
        if not comp: continue
        e    = _eng(d)
        if e is None: continue
        comp_eng[comp].append(e)
        sec = d.get("sector","")
        if sec: sec_comp[sec][comp].append(e)
        occ = d.get("occasion","") or ""
        if occ: occ_comp[occ][comp].append(e)

    global_avg = sum(v for vals in comp_eng.values() for v in vals) / max(sum(len(v) for v in comp_eng.values()),1)

    by_comp = {}
    for comp, vals in sorted(comp_eng.items(), key=lambda x: -len(x[1])):
        avg = round(sum(vals)/len(vals),3)
        by_comp[comp] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg,3),
            "high_rate": round(sum(1 for v in vals if v>=0.75)/len(vals),3),
        }

    best_by_sector = {}
    for sec, comps in sec_comp.items():
        ranked = sorted(comps.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_sector[sec] = [
            {"composition": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:3] if len(v) >= 3
        ]

    best_by_occasion = {}
    for occ, comps in occ_comp.items():
        total = sum(len(v) for v in comps.values())
        if total < 5: continue
        ranked = sorted(comps.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_occasion[occ] = [
            {"composition": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:2] if len(v) >= 2
        ]

    ranked = sorted(by_comp.items(), key=lambda x: x[1]["avg_engagement"], reverse=True)
    rules  = []
    if ranked:
        rules.append(f"Best composition: '{ranked[0][0]}' ({ranked[0][1]['avg_engagement']:.0%})")
        most_common = sorted(by_comp.items(), key=lambda x: x[1]["count"], reverse=True)[0]
        rules.append(f"Most used: '{most_common[0]}' ({most_common[1]['count']} obs, {most_common[1]['avg_engagement']:.0%})")

    out = {
        "total_obs": sum(len(v) for v in comp_eng.values()),
        "global_avg": round(global_avg,3),
        "by_composition": by_comp,
        "best_by_sector": best_by_sector,
        "best_by_occasion": best_by_occasion,
        "agency_rules": rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "composition_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Composition x engagement -- {out['total_obs']} obs  (global avg {global_avg:.0%})")
    for comp, data in list(by_comp.items())[:12]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {comp:<30}  {data['avg_engagement']:.0%}  lift {lift:>6}  n={data['count']}")
    for rule in rules:
        print(f"\n  > {rule}")
    print("  Output -> logs/composition_analysis.json")

if __name__ == "__main__":
    main()
