#!/usr/bin/env python3
"""
build_wardrobe_gender_analysis.py
Gender presentation + wardrobe × engagement.
Key for Beauty sector: who appears, what they wear, how it performs.
Output: logs/wardrobe_gender_analysis.json
"""
import json, re
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""),None)

def _normalize_gender(raw: str) -> str:
    r = raw.lower().strip()
    if any(w in r for w in ["female","woman","women","فتاة","امرأة"]): return "female"
    if any(w in r for w in ["male","man","men","رجل"]): return "male"
    if any(w in r for w in ["mixed","both","group","family"]): return "mixed"
    if any(w in r for w in ["none","no human","no character","0"]): return "none"
    return "unknown"

def main():
    gender_eng   = defaultdict(list)
    wardrobe_kw  = Counter()
    wardrobe_eng = defaultdict(list)
    sector_gender= defaultdict(lambda: defaultdict(list))
    no_human_eng = []

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        cv  = d.get("visual_observations",{}).get("characters_visible",{})
        e   = _eng(d)
        if e is None: continue
        sec = d.get("sector","")

        count = cv.get("count", 0) or 0
        if count == 0:
            no_human_eng.append(e)
            gender_eng["none"].append(e)
            if sec: sector_gender[sec]["none"].append(e)
            continue

        gender_raw = cv.get("gender_presentation","")
        if gender_raw:
            g = _normalize_gender(gender_raw)
            gender_eng[g].append(e)
            if sec: sector_gender[sec][g].append(e)

        wardrobe = cv.get("wardrobe_notes","")
        if wardrobe:
            # Extract keywords
            for kw in ["abaya","thobe","casual","formal","traditional","modern","branded",
                       "hijab","modest","sportswear","uniform","luxury"]:
                if kw in wardrobe.lower():
                    wardrobe_kw[kw] += 1
                    wardrobe_eng[kw].append(e)

    global_avg = sum(v for vals in gender_eng.values() for v in vals) / max(sum(len(v) for v in gender_eng.values()),1)

    by_gender = {}
    for g, vals in sorted(gender_eng.items(), key=lambda x: -len(x[1])):
        avg = round(sum(vals)/len(vals),3)
        by_gender[g] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg,3),
        }

    by_wardrobe = {}
    for kw, vals in sorted(wardrobe_eng.items(), key=lambda x: -sum(x[1])/max(len(x[1]),1)):
        avg = round(sum(vals)/len(vals),3)
        by_wardrobe[kw] = {
            "count": len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg,3),
        }

    best_by_sector = {}
    for sec, genders in sector_gender.items():
        ranked = sorted(genders.items(), key=lambda x: sum(x[1])/max(len(x[1]),1), reverse=True)
        best_by_sector[sec] = [
            {"gender": k, "avg_engagement": round(sum(v)/len(v),3), "n": len(v)}
            for k,v in ranked[:3]
        ]

    rules = []
    if by_gender:
        best_g = max(by_gender.items(), key=lambda x: x[1]["avg_engagement"])
        rules.append(f"Best gender presentation: '{best_g[0]}' ({best_g[1]['avg_engagement']:.0%})")
    if by_wardrobe:
        best_w = max(by_wardrobe.items(), key=lambda x: x[1]["avg_engagement"])
        rules.append(f"Best wardrobe style: '{best_w[0]}' ({best_w[1]['avg_engagement']:.0%})")

    out = {
        "total_obs": sum(len(v) for v in gender_eng.values()),
        "global_avg": round(global_avg,3),
        "by_gender": by_gender,
        "by_wardrobe_keyword": by_wardrobe,
        "best_by_sector": best_by_sector,
        "agency_rules": rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "wardrobe_gender_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Wardrobe/gender × engagement — {out['total_obs']} obs")
    print("Gender breakdown:")
    for g, data in by_gender.items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {g:<12}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nWardrobe keywords:")
    for kw, data in list(by_wardrobe.items())[:8]:
        print(f"  {kw:<15}  {data['avg_engagement']:.0%}  n={data['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/wardrobe_gender_analysis.json")

if __name__ == "__main__":
    main()
