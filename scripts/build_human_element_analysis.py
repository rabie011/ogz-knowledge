#!/usr/bin/env python3
"""
build_human_element_analysis.py
Mine characters_visible — count, gender, wardrobe — never analyzed.
Critical agency questions:
  - Does human presence in frame lift engagement?
  - Does traditional Saudi dress vs casual matter?
  - Single person vs group — which performs better?
  - Gender in frame — does it affect outcomes?
Output: logs/human_element_analysis.json
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

TRADITIONAL_KEYWORDS = [
    "thobe","shmagh","ghitra","bisht","abaya","niqab","kandura",
    "embroidered","traditional","saudi dress","najdi","heritage",
    "تراث","عباية","ثوب","شماغ"
]
CASUAL_KEYWORDS = ["casual","jeans","shirt","t-shirt","hoodie","western","streetwear","modern"]


def classify_wardrobe(notes: str) -> str:
    if not notes or not notes.strip():
        return "unknown"
    n = notes.lower()
    if any(k in n for k in TRADITIONAL_KEYWORDS):
        return "traditional_saudi"
    if any(k in n for k in CASUAL_KEYWORDS):
        return "casual_modern"
    return "other"


def main():
    # Buckets
    has_human  = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    by_count   = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    by_gender  = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    by_wardrobe= defaultdict(lambda: {"count":0,"high":0,"sum":0.0})

    # Cross-dims
    gender_sector   = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    wardrobe_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    count_sector    = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    obs_with_chars = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv  = data.get("visual_observations",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector","unknown") or "unknown"

        cv = vv.get("characters_visible")

        # Has human vs no human
        has_person = isinstance(cv, dict) and int(cv.get("count",0) or 0) > 0
        label = "has_human" if has_person else "no_human"
        has_human[label]["count"]  += 1
        has_human[label]["high"]   += is_high
        has_human[label]["sum"]    += eng

        if not has_person:
            continue

        obs_with_chars += 1
        count = min(int(cv.get("count",1) or 1), 5)  # cap at 5+ for grouping
        count_label = str(count) if count < 5 else "5+"
        gender  = str(cv.get("gender_presentation","") or "").lower().strip() or "unknown"
        wardrobe_notes = str(cv.get("wardrobe_notes","") or cv.get("wardrobe","") or "")
        wardrobe = classify_wardrobe(wardrobe_notes)

        # Normalize gender
        if "female" in gender and "male" in gender:
            gender = "mixed"
        elif "male" in gender:
            gender = "male"
        elif "female" in gender:
            gender = "female"
        elif "hand" in gender:
            gender = "hand_only"
        else:
            gender = "unknown"

        by_count[count_label]["count"]   += 1
        by_count[count_label]["high"]    += is_high
        by_count[count_label]["sum"]     += eng

        by_gender[gender]["count"]  += 1
        by_gender[gender]["high"]   += is_high
        by_gender[gender]["sum"]    += eng

        by_wardrobe[wardrobe]["count"] += 1
        by_wardrobe[wardrobe]["high"]  += is_high
        by_wardrobe[wardrobe]["sum"]   += eng

        gender_sector[gender][sector]["count"]   += 1
        gender_sector[gender][sector]["high"]    += is_high
        wardrobe_sector[wardrobe][sector]["count"] += 1
        wardrobe_sector[wardrobe][sector]["high"]  += is_high
        count_sector[count_label][sector]["count"] += 1
        count_sector[count_label][sector]["high"]  += is_high

    def make_table(d, label_key="value"):
        rows = []
        for label, data in d.items():
            n = data["count"]
            if n == 0: continue
            rate = round(data["high"]/n, 3)
            rows.append({
                label_key: label,
                "obs_count": n,
                "high_engagement_rate": rate,
                "avg_engagement": round(data["sum"]/n, 3),
                "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            })
        rows.sort(key=lambda x: -x["high_engagement_rate"])
        return rows

    human_presence_table = make_table(has_human, "human_presence")
    count_table    = make_table(by_count, "people_count")
    gender_table   = make_table(by_gender, "gender")
    wardrobe_table = make_table(by_wardrobe, "wardrobe_style")

    # Cross-tabs
    gender_sector_rows = []
    for gender, sectors in gender_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n,3) if n else 0
            if n >= 2:
                gender_sector_rows.append({
                    "gender": gender, "sector": sector, "count": n,
                    "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
                })
    gender_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    wardrobe_sector_rows = []
    for wardrobe, sectors in wardrobe_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n,3) if n else 0
            if n >= 2:
                wardrobe_sector_rows.append({
                    "wardrobe": wardrobe, "sector": sector, "count": n,
                    "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
                })
    wardrobe_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Key findings
    findings = []
    # Human presence effect
    human = next((r for r in human_presence_table if r["human_presence"]=="has_human"), None)
    no_human = next((r for r in human_presence_table if r["human_presence"]=="no_human"), None)
    if human and no_human:
        diff = human["high_engagement_rate"] - no_human["high_engagement_rate"]
        dir_str = "HELPS" if diff > 0.05 else "HURTS" if diff < -0.05 else "NEUTRAL"
        findings.append(
            f"Human presence {dir_str} engagement: "
            f"with_person={int(human['high_engagement_rate']*100)}% vs no_person={int(no_human['high_engagement_rate']*100)}% "
            f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
        )
    if wardrobe_table:
        best = wardrobe_table[0]
        findings.append(
            f"Best wardrobe style: '{best['wardrobe_style']}' = {int(best['high_engagement_rate']*100)}% high eng "
            f"(n={best['obs_count']}, +{int(best['lift_vs_baseline']*100)}pp)"
        )
    if count_table:
        best_count = count_table[0]
        findings.append(
            f"Best group size: {best_count['people_count']} person(s) = {int(best_count['high_engagement_rate']*100)}% high eng (n={best_count['obs_count']})"
        )
    if gender_table:
        best_gen = gender_table[0]
        findings.append(
            f"Best gender in frame: '{best_gen['gender']}' = {int(best_gen['high_engagement_rate']*100)}% (n={best_gen['obs_count']})"
        )

    # Agency rules
    agency_rules = []
    if human and no_human:
        diff = human["high_engagement_rate"] - no_human["high_engagement_rate"]
        if diff > 0.05:
            agency_rules.append("Include a human in the frame — it lifts engagement")
        elif diff < -0.05:
            agency_rules.append("Product-only shots outperform human shots in this corpus — let the food/product hero")
        else:
            agency_rules.append("Human presence is neutral — decide based on brand story, not engagement heuristic")
    trad = next((r for r in wardrobe_table if r["wardrobe_style"]=="traditional_saudi"), None)
    if trad and trad["lift_vs_baseline"] > 0.10:
        agency_rules.append(f"Traditional Saudi dress in frame = +{int(trad['lift_vs_baseline']*100)}pp lift — cast accordingly for heritage content")
    best_count = count_table[0] if count_table else None
    if best_count:
        agency_rules.append(f"Optimal group size: {best_count['people_count']} person(s) in frame")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_human_presence": obs_with_chars,
        "human_presence_table": human_presence_table,
        "people_count_table": count_table,
        "gender_table": gender_table,
        "wardrobe_style_table": wardrobe_table,
        "gender_by_sector": gender_sector_rows,
        "wardrobe_by_sector": wardrobe_sector_rows,
        "agency_rules": agency_rules,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "human_element_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Human element analysis: {obs_with_chars}/{total} obs have human presence")
    print(f"\nHuman presence → engagement:")
    for r in human_presence_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['human_presence']:<16} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['obs_count']}")
    print(f"\nWardrobe style → engagement:")
    for r in wardrobe_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['wardrobe_style']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['obs_count']}")
    print(f"\nGroup size → engagement:")
    for r in count_table:
        print(f"  {r['people_count']:<8} people  {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/human_element_analysis.json")


if __name__ == "__main__":
    main()
