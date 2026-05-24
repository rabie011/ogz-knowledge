#!/usr/bin/env python3
"""
build_day_of_week_analysis.py
Posting day × engagement analysis — when do top Saudi brands post?
Output: logs/day_of_week_analysis.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP  = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
DAYS_ORD = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""),None)

def main():
    day_eng   = defaultdict(list)
    day_count = Counter()
    sector_day= defaultdict(lambda: defaultdict(list))
    occasion_day = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        day = d.get("content_ref",{}).get("day_of_week")
        if not day: continue
        e   = _eng(d)
        if e is None: continue
        day_eng[day].append(e)
        day_count[day] += 1
        sec = d.get("sector","")
        if sec: sector_day[sec][day].append(e)
        occ = d.get("occasion","") or ""
        if occ: occasion_day[occ][day].append(e)

    global_avg = sum(v for vals in day_eng.values() for v in vals) / max(sum(len(v) for v in day_eng.values()),1)

    by_day = {}
    for day in DAYS_ORD:
        vals = day_eng[day]
        if not vals: continue
        avg = round(sum(vals)/len(vals),3)
        by_day[day] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg, 3),
            "high_rate": round(sum(1 for v in vals if v>=0.75)/len(vals),3),
        }

    # Best day per sector
    best_by_sector = {}
    for sec, days in sector_day.items():
        best = max(days.items(), key=lambda x: sum(x[1])/max(len(x[1]),1))
        best_by_sector[sec] = {
            "best_day": best[0],
            "avg_engagement": round(sum(best[1])/len(best[1]),3),
            "n": len(best[1]),
        }

    # Best day per occasion
    best_by_occasion = {}
    for occ, days in occasion_day.items():
        if sum(len(v) for v in days.values()) < 5: continue
        best = max(days.items(), key=lambda x: sum(x[1])/max(len(x[1]),1))
        best_by_occasion[occ] = {
            "best_day": best[0],
            "avg_engagement": round(sum(best[1])/len(best[1]),3),
            "n": sum(len(v) for v in days.values()),
        }

    # Ranked days
    ranked = sorted(by_day.items(), key=lambda x: x[1]["avg_engagement"], reverse=True)
    agency_rule = f"Best posting day: {ranked[0][0].title()} (avg {ranked[0][1]['avg_engagement']:.0%}) — worst: {ranked[-1][0].title()} ({ranked[-1][1]['avg_engagement']:.0%})"

    out = {
        "total_obs_with_date": sum(day_count.values()),
        "global_avg_engagement": round(global_avg,3),
        "by_day": by_day,
        "ranked_days": [d for d,_ in ranked],
        "best_by_sector": best_by_sector,
        "best_by_occasion": best_by_occasion,
        "agency_rule": agency_rule,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "day_of_week_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Day of week analysis — {sum(day_count.values())} obs")
    for day in DAYS_ORD:
        if day in by_day:
            b = by_day[day]
            lift = f"+{b['lift_vs_avg']:.2f}" if b['lift_vs_avg']>=0 else f"{b['lift_vs_avg']:.2f}"
            print(f"  {day:<12}  {b['avg_engagement']:.0%}  lift {lift:>6}  n={b['count']}")
    print(f"\n  ▸ {agency_rule}")
    print("  Output → logs/day_of_week_analysis.json")

if __name__ == "__main__":
    main()
