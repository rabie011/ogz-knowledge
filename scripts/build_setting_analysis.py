#!/usr/bin/env python3
"""
build_setting_analysis.py
Setting × engagement — restaurant_indoor vs studio vs digital_graphic etc.
Output: logs/setting_analysis.json
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
    setting_eng  = defaultdict(list)
    sec_setting  = defaultdict(lambda: defaultdict(list))
    occ_setting  = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        stt = d.get("visual_observations",{}).get("setting","")
        if not stt: continue
        e   = _eng(d)
        if e is None: continue
        setting_eng[stt].append(e)
        sec = d.get("sector","")
        if sec: sec_setting[sec][stt].append(e)
        occ = d.get("occasion","") or ""
        if occ: occ_setting[occ][stt].append(e)

    global_avg = sum(v for vals in setting_eng.values() for v in vals) / max(sum(len(v) for v in setting_eng.values()),1)

    by_setting = {}
    for stt, vals in sorted(setting_eng.items(), key=lambda x: -len(x[1])):
        avg = round(sum(vals)/len(vals),3)
        by_setting[stt] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg,3),
            "high_rate": round(sum(1 for v in vals if v>=0.75)/len(vals),3),
        }

    best_by_sector = {}
    for sec, stts in sec_setting.items():
        ranked = sorted(stts.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_sector[sec] = [
            {"setting": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:3] if len(v) >= 3
        ]

    best_by_occasion = {}
    for occ, stts in occ_setting.items():
        total = sum(len(v) for v in stts.values())
        if total < 5: continue
        ranked = sorted(stts.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_occasion[occ] = [
            {"setting": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:2] if len(v) >= 2
        ]

    ranked = sorted(by_setting.items(), key=lambda x: x[1]["avg_engagement"], reverse=True)
    rules  = []
    if ranked:
        rules.append(f"Best setting: '{ranked[0][0]}' ({ranked[0][1]['avg_engagement']:.0%})")
        worst = ranked[-1]
        rules.append(f"Weakest setting: '{worst[0]}' ({worst[1]['avg_engagement']:.0%})")

    out = {
        "total_obs": sum(len(v) for v in setting_eng.values()),
        "global_avg": round(global_avg,3),
        "by_setting": by_setting,
        "best_by_sector": best_by_sector,
        "best_by_occasion": best_by_occasion,
        "agency_rules": rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "setting_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Setting × engagement — {out['total_obs']} obs  (global avg {global_avg:.0%})")
    for stt, data in list(by_setting.items())[:12]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {stt:<25}  {data['avg_engagement']:.0%}  lift {lift:>6}  n={data['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/setting_analysis.json")

if __name__ == "__main__":
    main()
