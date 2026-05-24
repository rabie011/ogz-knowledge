#!/usr/bin/env python3
"""
build_content_type_analysis.py
Full format decision tree:
  content_type × aspect_ratio × editing_pace × sector × occasion
Output: logs/content_type_analysis.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""), None)

def _avg(vals):
    return round(sum(vals) / len(vals), 3) if vals else None

def main():
    ct_eng   = defaultdict(list)
    ar_eng   = defaultdict(list)
    combo_eng= defaultdict(list)   # (content_type, aspect_ratio)
    sec_ct   = defaultdict(lambda: defaultdict(list))
    occ_ct   = defaultdict(lambda: defaultdict(list))
    pace_ct  = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        e    = _eng(d)
        if e is None: continue
        cr   = d.get("content_ref", {})
        ct   = cr.get("content_type", "")
        ar   = cr.get("aspect_ratio", "")
        pace = cr.get("editing_pace", "")
        sec  = d.get("sector", "")
        occ  = d.get("occasion", "") or "evergreen"

        if ct: ct_eng[ct].append(e)
        if ar: ar_eng[ar].append(e)
        if ct and ar: combo_eng[(ct, ar)].append(e)
        if ct and sec: sec_ct[sec][ct].append(e)
        if ct and occ: occ_ct[occ][ct].append(e)
        if ct and pace: pace_ct[ct][pace].append(e)

    global_avg = sum(v for vals in ct_eng.values() for v in vals) / max(
        sum(len(v) for v in ct_eng.values()), 1)

    by_ct = {
        ct: {"count": len(v), "avg_engagement": _avg(v),
             "lift_vs_avg": round(_avg(v) - global_avg, 3),
             "high_rate": round(sum(1 for x in v if x >= 0.75) / len(v), 3)}
        for ct, v in ct_eng.items()
    }

    by_ar = {
        ar: {"count": len(v), "avg_engagement": _avg(v),
             "lift_vs_avg": round(_avg(v) - global_avg, 3)}
        for ar, v in ar_eng.items()
    }

    # Combo matrix (content_type × aspect_ratio), min n=3
    combo_matrix = {}
    for (ct, ar), vals in combo_eng.items():
        if len(vals) < 3: continue
        combo_matrix[f"{ct}__{ar}"] = {
            "content_type": ct, "aspect_ratio": ar,
            "count": len(vals), "avg_engagement": _avg(vals),
            "lift_vs_avg": round(_avg(vals) - global_avg, 3),
        }

    # Best content type per sector
    best_by_sector = {}
    for sec, cts in sec_ct.items():
        ranked = sorted(cts.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_by_sector[sec] = [
            {"content_type": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked if len(v) >= 3
        ]

    # Best content type per occasion
    best_by_occasion = {}
    for occ, cts in occ_ct.items():
        total = sum(len(v) for v in cts.values())
        if total < 5: continue
        ranked = sorted(cts.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_by_occasion[occ] = [
            {"content_type": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked if len(v) >= 2
        ]

    # Editing pace per content type
    pace_by_ct = {}
    for ct, paces in pace_ct.items():
        ranked = sorted(paces.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        pace_by_ct[ct] = [
            {"pace": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked if len(v) >= 2
        ]

    ranked_ct = sorted(by_ct.items(), key=lambda x: x[1]["avg_engagement"] or 0, reverse=True)
    ranked_ar = sorted(by_ar.items(), key=lambda x: x[1]["avg_engagement"] or 0, reverse=True)
    best_combo = sorted(combo_matrix.values(), key=lambda x: x["avg_engagement"] or 0, reverse=True)

    rules = []
    if ranked_ct:
        rules.append(f"Best format: {ranked_ct[0][0]} ({ranked_ct[0][1]['avg_engagement']:.0%}) "
                     f"— worst: {ranked_ct[-1][0]} ({ranked_ct[-1][1]['avg_engagement']:.0%})")
    if ranked_ar:
        rules.append(f"Best ratio: {ranked_ar[0][0]} ({ranked_ar[0][1]['avg_engagement']:.0%})")
    if best_combo:
        bc = best_combo[0]
        rules.append(f"Best combo: {bc['content_type']} + {bc['aspect_ratio']} ({bc['avg_engagement']:.0%}, n={bc['count']})")

    out = {
        "total_obs":            sum(len(v) for v in ct_eng.values()),
        "global_avg":           round(global_avg, 3),
        "by_content_type":      dict(sorted(by_ct.items(), key=lambda x: -(x[1]["avg_engagement"] or 0))),
        "by_aspect_ratio":      dict(sorted(by_ar.items(), key=lambda x: -(x[1]["avg_engagement"] or 0))),
        "combo_matrix":         sorted(combo_matrix.values(), key=lambda x: -(x["avg_engagement"] or 0)),
        "best_by_sector":       best_by_sector,
        "best_by_occasion":     best_by_occasion,
        "editing_pace_by_type": pace_by_ct,
        "agency_rules":         rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "content_type_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Content type analysis — {out['total_obs']} obs  (global avg {global_avg:.0%})\n")
    print("By content type:")
    for ct, data in out["by_content_type"].items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {ct:<18}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nBy aspect ratio:")
    for ar, data in out["by_aspect_ratio"].items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {ar:<20}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nTop combos (content_type × ratio):")
    for c in best_combo[:6]:
        print(f"  {c['content_type']:<18} × {c['aspect_ratio']:<15}  {c['avg_engagement']:.0%}  n={c['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/content_type_analysis.json")

if __name__ == "__main__":
    main()
