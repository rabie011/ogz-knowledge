#!/usr/bin/env python3
"""
build_composition_setting_synergy.py
Composition × setting combos — which pairings dominate Saudi content?
documentary_candid × event_venue = 100%, overhead_spread × restaurant_indoor = 89%
Output: logs/composition_setting_synergy.json
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
    comp_alone = defaultdict(list)
    set_alone  = defaultdict(list)

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        vis = d.get("visual_observations",{})
        cs  = vis.get("composition_style","")
        st  = vis.get("setting","")
        sec = d.get("sector","")
        occ = d.get("occasion","") or "evergreen"
        if cs: comp_alone[cs].append(e)
        if st: set_alone[st].append(e)
        if cs and st:
            key = f"{cs} × {st}"
            combo_eng[key].append(e)
            if sec: sec_combo[sec][key].append(e)
            if occ: occ_combo[occ][key].append(e)

    global_avg = _avg([v for vals in comp_alone.values() for v in vals]) or 0

    # All combos with n >= 3
    all_combos = {
        k: {"count":len(v),"avg_engagement":_avg(v),"lift_vs_avg":round((_avg(v) or 0)-global_avg,3)}
        for k,v in combo_eng.items() if len(v) >= 3
    }

    ranked = sorted(all_combos.items(), key=lambda x:-(x[1]["avg_engagement"] or 0))

    # Best combo per sector
    best_by_sector = {}
    for sec, combos in sec_combo.items():
        ranked_s = sorted([(k,v) for k,v in combos.items() if len(v)>=3],
                          key=lambda x:-(_avg(x[1]) or 0))
        best_by_sector[sec] = [
            {"combo":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in ranked_s[:5]
        ]

    # Best combo per occasion
    best_by_occasion = {}
    for occ, combos in occ_combo.items():
        total = sum(len(v) for v in combos.values())
        if total < 5: continue
        ranked_o = sorted([(k,v) for k,v in combos.items() if len(v)>=2],
                          key=lambda x:-(_avg(x[1]) or 0))
        best_by_occasion[occ] = [
            {"combo":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in ranked_o[:3]
        ]

    rules = []
    if ranked:
        top3 = [r[0] for r in ranked[:3]]
        rules.append(f"Elite combos: {' | '.join(top3)}")
        worst = ranked[-1]
        rules.append(f"Weakest combo: '{worst[0]}' ({worst[1]['avg_engagement']:.0%})")

    out = {
        "total_combos":      len(all_combos),
        "global_avg":        round(global_avg,3),
        "all_combos_ranked": [{"combo":k,**v} for k,v in ranked],
        "best_by_sector":    best_by_sector,
        "best_by_occasion":  best_by_occasion,
        "agency_rules":      rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"composition_setting_synergy.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Composition × setting synergy — {len(all_combos)} valid combos  (global {global_avg:.0%})")
    print("Top 12 combos:")
    for combo, data in ranked[:12]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {combo:<52}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/composition_setting_synergy.json")

if __name__ == "__main__":
    main()
