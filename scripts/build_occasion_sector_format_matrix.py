#!/usr/bin/env python3
"""
build_occasion_sector_format_matrix.py
3-way: occasion × sector × content_type engagement matrix.
Eid al-Fitr × F&B × video = 100%. National Day × F&B × image = 90%.
The definitive format-per-occasion-per-sector decision table.
Output: logs/occasion_sector_format_matrix.json
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
    triple  = defaultdict(list)   # (occ, sec, ct) → eng
    pair_os = defaultdict(list)   # (occ, sec)     → eng (no format filter)
    pair_oc = defaultdict(list)   # (occ, ct)       → eng

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        occ = d.get("occasion","") or "evergreen"
        sec = d.get("sector","")
        ct  = d.get("content_ref",{}).get("content_type","")
        if occ and sec and ct:
            triple[(occ,sec,ct)].append(e)
            pair_os[(occ,sec)].append(e)
            pair_oc[(occ,ct)].append(e)

    global_avg = _avg([v for vals in pair_os.values() for v in vals]) or 0

    # Build 3-way table
    rows = []
    for (occ,sec,ct), vals in triple.items():
        if len(vals) < 2: continue
        avg  = _avg(vals) or 0
        rows.append({
            "occasion":      occ,
            "sector":        sec,
            "content_type":  ct,
            "count":         len(vals),
            "avg_engagement":avg,
            "lift_vs_avg":   round(avg-global_avg,3),
        })
    rows.sort(key=lambda x: -x["avg_engagement"])

    # Best format per (occasion, sector) — the key lookup table
    best_format = {}
    for (occ,sec), occ_sec_rows in defaultdict(list, {(r["occasion"],r["sector"]):[r] for r in rows}).items():
        best = max(occ_sec_rows, key=lambda x: (x["avg_engagement"],x["count"]))
        best_format[f"{occ}__{sec}"] = {
            "best_format": best["content_type"],
            "avg_engagement": best["avg_engagement"],
            "n": best["count"],
        }

    # Re-build properly
    best_format_table = {}
    from collections import defaultdict as dd
    by_occ_sec = dd(list)
    for r in rows: by_occ_sec[(r["occasion"],r["sector"])].append(r)
    for (occ,sec), rlist in by_occ_sec.items():
        best = max(rlist, key=lambda x: (x["avg_engagement"],x["count"]))
        worst= min(rlist, key=lambda x: x["avg_engagement"])
        best_format_table[f"{occ}__{sec}"] = {
            "occasion": occ, "sector": sec,
            "best_format": best["content_type"],
            "best_eng":    best["avg_engagement"],
            "best_n":      best["count"],
            "worst_format":worst["content_type"],
            "worst_eng":   worst["avg_engagement"],
            "all_formats": sorted(rlist, key=lambda x:-x["avg_engagement"]),
        }

    # Quick-ref matrix: occasion → sector → best_format
    occ_sec_matrix = defaultdict(dict)
    for (occ,sec), rlist in by_occ_sec.items():
        best = max(rlist, key=lambda x: (x["avg_engagement"],x["count"]))
        occ_sec_matrix[occ][sec] = f"{best['content_type']} ({best['avg_engagement']:.0%}, n={best['count']})"

    rules = []
    if rows:
        top = rows[0]
        rules.append(f"Best combo: {top['occasion']} × {top['sector']} × {top['content_type']} = {top['avg_engagement']:.0%}")
    for occ in ["eid_al_fitr","ramadan","national_day","founding_day","evergreen"]:
        best_row = next((r for r in rows if r["occasion"]==occ and r["count"]>=3), None)
        if best_row:
            rules.append(f"{occ}: use {best_row['content_type']} ({best_row['avg_engagement']:.0%}, n={best_row['count']})")

    out = {
        "total_obs":          sum(len(v) for v in triple.values()),
        "global_avg":         round(global_avg,3),
        "full_table":         rows,
        "best_format_table":  list(best_format_table.values()),
        "quick_ref_matrix":   dict(occ_sec_matrix),
        "agency_rules":       rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"occasion_sector_format_matrix.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Occasion × sector × format — {len(rows)} combos  (global {global_avg:.0%})\n")
    print(f"{'Occasion':<22}  {'Sector':<12}  {'Format':<18}  Eng   n")
    print("─"*70)
    for r in rows[:20]:
        lift = f"+{r['lift_vs_avg']:.2f}" if r['lift_vs_avg']>=0 else f"{r['lift_vs_avg']:.2f}"
        print(f"  {r['occasion']:<20}  {r['sector'][:10]:<12}  {r['content_type']:<18}  {r['avg_engagement']:.0%}  {r['count']}")
    for rule in rules: print(f"\n  ▸ {rule}")
    print("  Output → logs/occasion_sector_format_matrix.json")

if __name__ == "__main__":
    main()
