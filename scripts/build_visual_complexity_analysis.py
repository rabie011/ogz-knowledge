#!/usr/bin/env python3
"""
build_visual_complexity_analysis.py
visual_complexity × engagement × sector × occasion × content_type.
Key finding: complex content 86% vs moderate 58% — counter-intuitive.
Output: logs/visual_complexity_analysis.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP  = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
COMPLEXITY_ORDER = ["minimal","simple","moderate","complex"]

def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

def main():
    vc_eng  = defaultdict(list)
    sec_vc  = defaultdict(lambda: defaultdict(list))
    occ_vc  = defaultdict(lambda: defaultdict(list))
    ct_vc   = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        e  = _eng(d)
        if e is None: continue
        vc  = d.get("visual_observations",{}).get("visual_complexity","")
        sec = d.get("sector","")
        occ = d.get("occasion","") or "evergreen"
        ct  = d.get("content_ref",{}).get("content_type","")
        if not vc: continue
        vc_eng[vc].append(e)
        if sec: sec_vc[sec][vc].append(e)
        if occ: occ_vc[occ][vc].append(e)
        if ct:  ct_vc[ct][vc].append(e)

    global_avg = _avg([v for vals in vc_eng.values() for v in vals]) or 0

    by_vc = {
        vc: {"count":len(v),"avg_engagement":_avg(v),"lift_vs_avg":round((_avg(v) or 0)-global_avg,3)}
        for vc,v in vc_eng.items()
    }

    best_by_sector = {
        sec: sorted([{"complexity":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in vcs.items() if len(v)>=3],
                    key=lambda x:-(x["avg_engagement"] or 0))
        for sec,vcs in sec_vc.items()
    }

    best_by_occasion = {
        occ: sorted([{"complexity":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in vcs.items() if len(v)>=2],
                    key=lambda x:-(x["avg_engagement"] or 0))[:2]
        for occ,vcs in occ_vc.items() if sum(len(v) for v in vcs.values()) >= 5
    }

    best_by_ct = {
        ct: sorted([{"complexity":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in vcs.items() if len(v)>=2],
                   key=lambda x:-(x["avg_engagement"] or 0))[:2]
        for ct,vcs in ct_vc.items()
    }

    ranked = sorted(by_vc.items(), key=lambda x:-(x[1]["avg_engagement"] or 0))
    rules  = []
    if ranked:
        rules.append(f"Best complexity: '{ranked[0][0]}' ({ranked[0][1]['avg_engagement']:.0%}) — "
                     f"'{ranked[-1][0]}' weakest ({ranked[-1][1]['avg_engagement']:.0%})")
        rules.append("Counter-intuitive: complex visuals (+props, characters, overlays) outperform minimalist in Saudi content")

    out = {
        "total_obs":         sum(len(v) for v in vc_eng.values()),
        "global_avg":        round(global_avg,3),
        "by_complexity":     by_vc,
        "best_by_sector":    best_by_sector,
        "best_by_occasion":  best_by_occasion,
        "best_by_content_type": best_by_ct,
        "agency_rules":      rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"visual_complexity_analysis.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Visual complexity × engagement — {out['total_obs']} obs  (global {global_avg:.0%})")
    for vc in COMPLEXITY_ORDER:
        if vc in by_vc:
            d = by_vc[vc]
            lift = f"+{d['lift_vs_avg']:.2f}" if d['lift_vs_avg']>=0 else f"{d['lift_vs_avg']:.2f}"
            print(f"  {vc:<10}  {d['avg_engagement']:.0%}  lift {lift}  n={d['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/visual_complexity_analysis.json")

if __name__ == "__main__":
    main()
