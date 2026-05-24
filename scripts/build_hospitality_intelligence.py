#!/usr/bin/env python3
"""
build_hospitality_intelligence.py
Mine 508 hospitality_cues instances × engagement.
Key for F&B briefs: which hospitality cues drive Saudi audience engagement?
Output: logs/hospitality_intelligence.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

# Hospitality cue taxonomy
CUE_GROUPS = {
    "sharing":       ["sharing","communal","family","together","gathering","generosity","كرم","مشاركة","عائلة"],
    "occasion":      ["eid","ramadan","iftar","suhoor","national day","celebration","feast","عيد","رمضان","إفطار"],
    "product_pride": ["fresh","handmade","artisan","quality","premium","special","طازج","يدوي"],
    "welcome":       ["welcome","warmth","hospitality","host","invite","أهلاً","مرحبا","ترحيب"],
    "heritage":      ["traditional","heritage","classic","authentic","original","تراث","أصيل","كلاسيك"],
    "sensory":       ["taste","aroma","texture","flavour","smell","ذوق","رائحة","نكهة"],
    "abundance":     ["variety","choice","selection","spread","generous portion","وفرة","تنوع"],
}

def _classify_cue(cue: str) -> list:
    c = cue.lower()
    cats = [grp for grp, kws in CUE_GROUPS.items() if any(kw in c for kw in kws)]
    return cats or ["other"]

def _avg(vals):
    return round(sum(vals) / len(vals), 3) if vals else None

def main():
    cue_eng   = defaultdict(list)
    group_eng = defaultdict(list)
    cue_count = Counter()
    sec_cues  = defaultdict(lambda: defaultdict(list))
    occ_cues  = defaultdict(lambda: defaultdict(list))

    total_with_cues = 0

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        cues = d.get("cultural_notes", {}).get("hospitality_cues", [])
        if not cues: continue
        e    = ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
        if e is None: continue
        sec  = d.get("sector", "")
        occ  = d.get("occasion", "") or "evergreen"
        total_with_cues += 1

        for cue in cues:
            cue = str(cue).strip().lower()
            if len(cue) < 2: continue
            cue_count[cue] += 1
            cue_eng[cue].append(e)
            if sec: sec_cues[sec][cue].append(e)
            if occ: occ_cues[occ][cue].append(e)
            for grp in _classify_cue(cue):
                group_eng[grp].append(e)

    global_avg = sum(v for vals in cue_eng.values() for v in vals) / max(
        sum(len(v) for v in cue_eng.values()), 1)

    # Top cues by frequency × engagement
    top_cues = {}
    for cue, count in cue_count.most_common(40):
        vals = cue_eng[cue]
        avg  = _avg(vals)
        top_cues[cue] = {
            "count": count,
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg, 3) if avg else None,
        }

    # Group analysis
    by_group = {
        grp: {"count": len(v), "avg_engagement": _avg(v),
              "lift_vs_avg": round(_avg(v) - global_avg, 3) if _avg(v) else None}
        for grp, v in sorted(group_eng.items(), key=lambda x: -(_avg(x[1]) or 0))
    }

    # Best cues per sector
    best_by_sector = {}
    for sec, cues in sec_cues.items():
        ranked = sorted(cues.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_by_sector[sec] = [
            {"cue": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:5] if len(v) >= 2
        ]

    # Best cues per occasion
    best_by_occasion = {}
    for occ, cues in occ_cues.items():
        total = sum(len(v) for v in cues.values())
        if total < 4: continue
        ranked = sorted(cues.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_by_occasion[occ] = [
            {"cue": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:3] if len(v) >= 2
        ]

    # Elite cues: lift ≥ +0.10, n ≥ 3
    elite = sorted(
        [{"cue": k, **v} for k, v in top_cues.items()
         if (v["lift_vs_avg"] or 0) >= 0.10 and v["count"] >= 3],
        key=lambda x: -(x["lift_vs_avg"] or 0)
    )

    rules = []
    if by_group:
        best_g = list(by_group.items())[0]
        rules.append(f"Best hospitality group: '{best_g[0]}' ({best_g[1]['avg_engagement']:.0%})")
    if elite:
        rules.append(f"Elite cues: {', '.join(c['cue'] for c in elite[:4])}")

    out = {
        "obs_with_cues":    total_with_cues,
        "unique_cues":      len(cue_count),
        "total_instances":  sum(cue_count.values()),
        "global_avg":       round(global_avg, 3),
        "top_cues":         top_cues,
        "by_cue_group":     by_group,
        "elite_cues":       elite,
        "best_by_sector":   best_by_sector,
        "best_by_occasion": best_by_occasion,
        "agency_rules":     rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "hospitality_intelligence.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Hospitality intelligence — {total_with_cues} obs, {len(cue_count)} unique cues\n")
    print("Top 10 cues by frequency:")
    for cue, data in list(top_cues.items())[:10]:
        lv = data['lift_vs_avg'] or 0
        lift = f"+{lv:.2f}" if lv >= 0 else f"{lv:.2f}"
        print(f"  {cue:<35}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nBy cue group:")
    for grp, data in by_group.items():
        lv = data['lift_vs_avg'] or 0
        lift = f"+{lv:.2f}" if lv >= 0 else f"{lv:.2f}"
        print(f"  {grp:<15}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/hospitality_intelligence.json")

if __name__ == "__main__":
    main()
