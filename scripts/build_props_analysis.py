#!/usr/bin/env python3
"""
build_props_analysis.py
Mine props_visible from visual_observations — completely unmined dimension.
Which props (coffee cups, trays, vessels, hands) appear in high-engagement posts?
Output: logs/props_analysis.json
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

# Prop taxonomy — map raw strings to canonical categories
PROP_CATEGORIES = [
    ("coffee_vessel",    ["cup","mug","qahwa","dallah","espresso","coffee pot","thermos","karak"]),
    ("food_prop",        ["plate","dish","bowl","tray","platter","food","dessert","cake","bread","dates"]),
    ("drink_vessel",     ["glass","juice","smoothie","laban","water","bottle","can","drink"]),
    ("hand_motion",      ["hand","pour","hold","grip","finger","reach","touch"]),
    ("traditional_item", ["incense","oud","bakhoor","sadu","bisht","thobe","kandura","abaya","headband","misba"]),
    ("floral_natural",   ["flower","rose","plant","leaf","herb","mint","greenery","botanical"]),
    ("packaging",        ["bag","box","packaging","wrapper","label","branded","sleeve","logo"]),
    ("table_surface",    ["table","marble","wood","surface","counter","fabric","cloth","linen","stone"]),
    ("device_tech",      ["phone","camera","screen","laptop","tech"]),
    ("lifestyle_item",   ["book","sunglasses","watch","accessory","ring","jewel"]),
]


def classify_prop(s: str):
    v = s.lower()
    for cat, kws in PROP_CATEGORIES:
        if any(k in v for k in kws):
            return cat
    return "other"


def normalize_prop(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip().lower())


def main():
    # Raw prop tracking
    raw_props = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter(),"accounts":set()})
    # Category tracking
    cat_props = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter()})
    # Prop co-occurrence with setting
    prop_setting = defaultdict(lambda: defaultdict(int))

    total = 0
    obs_with_props = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv  = data.get("visual_observations",{}) or {}
        props_raw = vv.get("props_visible") or []
        # props_visible can be list or dict — handle both
        if isinstance(props_raw, dict):
            props_list = list(props_raw.keys()) + [str(v) for v in props_raw.values() if v]
        elif isinstance(props_raw, list):
            props_list = [str(p) for p in props_raw if p]
        else:
            props_list = [str(props_raw)] if props_raw else []

        if not props_list: continue
        obs_with_props += 1

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector","unknown") or "unknown"
        account = data.get("account_handle_normalized","unknown")
        setting = vv.get("setting","unknown") or "unknown"

        for prop_str in props_list:
            if not prop_str or not prop_str.strip(): continue
            key = normalize_prop(prop_str)
            if len(key) < 2: continue
            cat = classify_prop(key)

            raw_props[key]["count"]  += 1
            raw_props[key]["high"]   += is_high
            raw_props[key]["sum"]    += eng
            raw_props[key]["sectors"][sector] += 1
            raw_props[key]["accounts"].add(account)

            cat_props[cat]["count"]  += 1
            cat_props[cat]["high"]   += is_high
            cat_props[cat]["sum"]    += eng
            cat_props[cat]["sectors"][sector] += 1

            prop_setting[cat][setting] += 1

    # Category table
    cat_table = []
    for cat, d in sorted(cat_props.items(), key=lambda x: -x[1]["count"]):
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        cat_table.append({
            "category": cat,
            "frequency": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "top_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    cat_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["frequency"]))

    # Top raw props (2+ uses)
    raw_table = []
    for prop, d in raw_props.items():
        n = d["count"]
        if n < 2: continue
        rate = round(d["high"]/n, 3)
        raw_table.append({
            "prop": prop,
            "frequency": n,
            "account_count": len(d["accounts"]),
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "dominant_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    raw_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["frequency"]))

    # Prop × setting synergy
    prop_setting_table = {
        cat: dict(Counter(settings).most_common(3))
        for cat, settings in prop_setting.items()
    }

    findings = []
    findings.append(f"{obs_with_props}/{total} observations have props_visible data.")
    if cat_table:
        best = cat_table[0]
        findings.append(f"Best prop category: '{best['category']}' {int(best['high_engagement_rate']*100)}% high eng (n={best['frequency']})")
        worst = min(cat_table, key=lambda x: x["high_engagement_rate"])
        findings.append(f"Worst prop category: '{worst['category']}' {int(worst['high_engagement_rate']*100)}% (n={worst['frequency']})")
    if raw_table:
        best_raw = raw_table[0]
        findings.append(f"Top individual prop: '{best_raw['prop']}' {int(best_raw['high_engagement_rate']*100)}% (n={best_raw['frequency']})")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_props": obs_with_props,
        "prop_category_engagement": cat_table,
        "top_raw_props": raw_table[:30],
        "prop_setting_cooccurrence": prop_setting_table,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "props_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Props analysis: {obs_with_props}/{total} obs have props")
    print(f"\nProp category → engagement:")
    print(f"  {'Category':<22} {'HighEng':>8}  {'Lift':>7}  {'n':>5}  Top sector")
    print("  " + "─"*65)
    for c in cat_table:
        lift = f"+{int(c['lift_vs_baseline']*100)}%" if c['lift_vs_baseline']>=0 else f"{int(c['lift_vs_baseline']*100)}%"
        print(f"  {c['category']:<22} {int(c['high_engagement_rate']*100):>7}%  {lift:>7}  {c['frequency']:>5}  {c['top_sector'] or '—'}")
    if raw_table:
        print(f"\nTop individual props (n≥2):")
        for r in raw_table[:10]:
            print(f"  {r['prop']:<40} {int(r['high_engagement_rate']*100):>3}%  n={r['frequency']}")
    print(f"\nOutput: logs/props_analysis.json")

if __name__ == "__main__":
    main()
