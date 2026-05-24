#!/usr/bin/env python3
"""
build_props_taxonomy.py
Mine props_visible (638 obs) for taxonomy + engagement signals.
Output: logs/props_taxonomy.json
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

TAXONOMY = {
    "food_vessels":   ["plate","bowl","cup","glass","mug","tray","platter","dish"],
    "arabic_culture": ["dallah","dates","qahwa","khanjal","majlis","incense","oud","ghawa","bukhoor","attar"],
    "nature_organic": ["flowers","rose","petals","leaves","herbs","spices","cinnamon","cardamom","greenery"],
    "branded":        ["logo","brand","packaging","box","bag","label","product","bottle","jar","can"],
    "luxury":         ["gold","marble","crystal","candle","velvet","silk","linen"],
    "tech":           ["phone","camera","ipad","tablet","laptop"],
    "table":          ["napkin","cutlery","fork","spoon","knife","tablecloth","table setting"],
    "human_body":     ["hands","feet","face","hair","lips","eye"],
}

def _classify(prop):
    p = prop.lower()
    cats = [cat for cat, kws in TAXONOMY.items() if any(kw in p for kw in kws)]
    return cats or ["other"]

def main():
    prop_eng  = defaultdict(list)
    group_eng = defaultdict(list)
    prop_count= Counter()
    sec_props = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d     = json.loads(f.read_text())
        props = d.get("visual_observations",{}).get("props_visible",[])
        if not props: continue
        e     = _eng(d)
        if e is None: continue
        sec   = d.get("sector","")
        for prop in props:
            prop = prop.strip().lower()
            if len(prop) < 2: continue
            prop_count[prop] += 1
            prop_eng[prop].append(e)
            if sec: sec_props[sec][prop].append(e)
            for cat in _classify(prop):
                group_eng[cat].append(e)

    global_avg = sum(v for vals in prop_eng.values() for v in vals) / max(sum(len(v) for v in prop_eng.values()),1)

    top_props = {}
    for prop, count in prop_count.most_common(50):
        vals = prop_eng[prop]
        avg  = round(sum(vals)/len(vals),3)
        top_props[prop] = {"count": count, "avg_engagement": avg, "lift_vs_avg": round(avg-global_avg,3)}

    by_group = {}
    for grp, vals in sorted(group_eng.items(), key=lambda x: -len(x[1])):
        avg = round(sum(vals)/len(vals),3)
        by_group[grp] = {"count": len(vals), "avg_engagement": avg, "lift_vs_avg": round(avg-global_avg,3)}

    best_by_sector = {}
    for sec, props in sec_props.items():
        ranked = sorted(props.items(), key=lambda x: (sum(x[1])/max(len(x[1]),1), len(x[1])), reverse=True)
        best_by_sector[sec] = [
            {"prop": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:5] if len(v) >= 2
        ]

    elite = sorted([{"prop":k,**v} for k,v in top_props.items() if v["lift_vs_avg"]>=0.10 and v["count"]>=3],
                   key=lambda x: -x["lift_vs_avg"])

    rules = []
    if elite: rules.append(f"Elite props (+10% lift): {', '.join(p['prop'] for p in elite[:5])}")
    if by_group:
        best_g = max(by_group.items(), key=lambda x: x[1]["avg_engagement"])
        rules.append(f"Best prop category: '{best_g[0]}' ({best_g[1]['avg_engagement']:.0%})")

    out = {"total_unique_props": len(prop_count), "global_avg": round(global_avg,3),
           "top_props": top_props, "by_prop_group": by_group,
           "elite_props": elite, "best_by_sector": best_by_sector, "agency_rules": rules}

    LOGS.mkdir(exist_ok=True)
    (LOGS / "props_taxonomy.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Props taxonomy -- {len(prop_count)} unique props")
    print("Top 10 by frequency:")
    for prop, data in list(top_props.items())[:10]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {prop:<25}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nBy group:")
    for grp, data in sorted(by_group.items(), key=lambda x: -x[1]["avg_engagement"]):
        print(f"  {grp:<18}  {data['avg_engagement']:.0%}  n={data['count']}")
    for rule in rules: print(f"\n  > {rule}")
    print("  Output -> logs/props_taxonomy.json")

if __name__ == "__main__":
    main()
