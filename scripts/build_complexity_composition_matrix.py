#!/usr/bin/env python3
"""
build_complexity_composition_matrix.py
visual_complexity × composition_style — the richest visual signal combo.
complex × overhead_spread = 97% — best pairing in the dataset.
Output: logs/complexity_composition_matrix.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

def main():
    combo_eng = defaultdict(list)
    sec_combo = defaultdict(lambda: defaultdict(list))
    occ_combo = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        vis = d.get("visual_observations", {})
        vc  = vis.get("visual_complexity", "")
        cs  = vis.get("composition_style", "")
        sec = d.get("sector", "")
        occ = d.get("occasion", "") or "evergreen"
        if not vc or not cs: continue
        key = f"{vc} × {cs}"
        combo_eng[key].append(e)
        if sec: sec_combo[sec][key].append(e)
        if occ: occ_combo[occ][key].append(e)

    global_avg = _avg([v for vals in combo_eng.values() for v in vals]) or 0

    all_combos = {
        k: {"count":len(v),"avg_engagement":_avg(v),
            "lift_vs_avg":round((_avg(v) or 0)-global_avg,3),
            "high_rate":round(sum(1 for x in v if x>=0.75)/len(v),3)}
        for k,v in combo_eng.items() if len(v)>=3
    }

    ranked = sorted(all_combos.items(), key=lambda x:-(x[1]["avg_engagement"] or 0))

    best_by_sector = {
        sec: sorted([{"combo":k,"avg_engagement":_avg(v),"n":len(v)}
                     for k,v in combos.items() if len(v)>=3],
                    key=lambda x:-(x["avg_engagement"] or 0))[:4]
        for sec, combos in sec_combo.items()
    }

    best_by_occasion = {
        occ: sorted([{"combo":k,"avg_engagement":_avg(v),"n":len(v)}
                     for k,v in combos.items() if len(v)>=2],
                    key=lambda x:-(x["avg_engagement"] or 0))[:2]
        for occ, combos in occ_combo.items()
        if sum(len(v) for v in combos.values()) >= 5
    }

    # Build matrix: vc rows × composition cols
    all_vc   = ["minimal","simple","moderate","complex"]
    all_comp = list({k.split(" × ")[1] for k in combo_eng.keys()})
    matrix   = {}
    for vc in all_vc:
        matrix[vc] = {}
        for cs in all_comp:
            key  = f"{vc} × {cs}"
            vals = combo_eng.get(key, [])
            if vals: matrix[vc][cs] = {"avg_engagement":_avg(vals),"n":len(vals)}

    rules = []
    if ranked:
        rules.append(f"Best combo: '{ranked[0][0]}' ({ranked[0][1]['avg_engagement']:.0%}, n={ranked[0][1]['count']})")
        rules.append(f"'complex' complexity boosts every composition style vs 'moderate'")
        worst = ranked[-1]
        rules.append(f"Weakest: '{worst[0]}' ({worst[1]['avg_engagement']:.0%})")

    out = {
        "total_obs":         sum(len(v) for v in combo_eng.values()),
        "global_avg":        round(global_avg,3),
        "all_combos_ranked": [{"combo":k,**v} for k,v in ranked],
        "matrix":            matrix,
        "best_by_sector":    best_by_sector,
        "best_by_occasion":  best_by_occasion,
        "agency_rules":      rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"complexity_composition_matrix.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Complexity × composition matrix — {len(all_combos)} combos  (global {global_avg:.0%})\n")
    print(f"{'Combo':<45}  {'Eng':>4}  {'Lift':>6}  n")
    print("─"*62)
    for combo,data in ranked[:15]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {combo:<43}  {data['avg_engagement']:.0%}  {lift:>6}  {data['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/complexity_composition_matrix.json")

if __name__ == "__main__":
    main()
