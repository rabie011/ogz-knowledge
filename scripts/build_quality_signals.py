#!/usr/bin/env python3
"""
build_quality_signals.py
Mine quality_assessment fields never analyzed for engagement:
  - production_quality (professional / semi_professional / amateur)
  - brand_consistency_with_account (strong / moderate / weak)
  - heritage_vs_modern × sector × engagement
Cross all three dimensions and find which combinations win.
Output: logs/quality_signals.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

PROD_ORDER   = ["professional","semi_professional","amateur"]
BRAND_ORDER  = ["strong","moderate","weak"]
HVM_BUCKETS  = {
    "heritage":     ["heritage","traditional","classic","historic"],
    "modern":       ["modern","contemporary","minimal","western"],
    "blended":      ["blend","balanced","fusion","mix"],
}


def classify_hvm(raw):
    if not raw: return "unclassified"
    v = str(raw).lower()
    for label, kws in HVM_BUCKETS.items():
        if any(k in v for k in kws): return label
    return "unclassified"


def main():
    prod_data  = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    brand_data = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    hvm_data   = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    combo_data = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})  # prod × brand
    hvm_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))  # hvm × sector

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        prod  = str(qa.get("production_quality","") or "").lower().strip()
        brand = str(qa.get("brand_consistency_with_account","") or "").lower().strip()
        cn    = data.get("cultural_notes",{}) or {}
        hvm   = classify_hvm(cn.get("heritage_vs_modern"))
        sector= data.get("sector","unknown") or "unknown"

        if prod:
            prod_data[prod]["count"] += 1
            prod_data[prod]["high"]  += is_high
            prod_data[prod]["sum"]   += eng
        if brand:
            brand_data[brand]["count"] += 1
            brand_data[brand]["high"]  += is_high
            brand_data[brand]["sum"]   += eng
        hvm_data[hvm]["count"] += 1
        hvm_data[hvm]["high"]  += is_high
        hvm_data[hvm]["sum"]   += eng
        hvm_sector[hvm][sector]["count"] += 1
        hvm_sector[hvm][sector]["high"]  += is_high

        if prod and brand:
            key = f"{prod}::{brand}"
            combo_data[key]["count"] += 1
            combo_data[key]["high"]  += is_high
            combo_data[key]["sum"]   += eng
            combo_data[key]["prod"]   = prod
            combo_data[key]["brand"]  = brand

    def make_table(d, order=None):
        rows = []
        keys = order if order else sorted(d.keys())
        for k in keys:
            if k not in d: continue
            n = d[k]["count"]
            if n == 0: continue
            rate = round(d[k]["high"]/n, 3)
            rows.append({
                "value": k, "obs_count": n,
                "high_engagement_rate": rate,
                "avg_engagement": round(d[k]["sum"]/n, 3),
                "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            })
        return rows

    prod_table  = make_table(prod_data,  PROD_ORDER)
    brand_table = make_table(brand_data, BRAND_ORDER)
    hvm_table   = make_table(hvm_data)
    hvm_table.sort(key=lambda x: -x["high_engagement_rate"])

    combo_table = []
    for key, d in combo_data.items():
        n = d["count"]
        if n < 2: continue
        rate = round(d["high"]/n, 3)
        combo_table.append({
            "production_quality": d["prod"],
            "brand_consistency":  d["brand"],
            "obs_count": n,
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    combo_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    hvm_sector_table = {}
    for hvm, sectors in hvm_sector.items():
        hvm_sector_table[hvm] = {
            sec: {
                "count": d["count"],
                "high_eng_rate": round(d["high"]/d["count"],3) if d["count"] else 0,
            }
            for sec, d in sectors.items()
        }

    findings = []
    if prod_table:
        best = prod_table[0]; worst = prod_table[-1]
        findings.append(f"Production: {best['value']} = {int(best['high_engagement_rate']*100)}% vs {worst['value']} = {int(worst['high_engagement_rate']*100)}% ({int((best['high_engagement_rate']-worst['high_engagement_rate'])*100)}pp gap)")
    if brand_table:
        best = brand_table[0]; worst = brand_table[-1]
        findings.append(f"Brand consistency: {best['value']} = {int(best['high_engagement_rate']*100)}% vs {worst['value']} = {int(worst['high_engagement_rate']*100)}%")
    if hvm_table:
        best = hvm_table[0]
        findings.append(f"Heritage framing: {best['value']} = {int(best['high_engagement_rate']*100)}% (n={best['obs_count']})")
    if combo_table:
        t = combo_table[0]
        findings.append(f"Best quality combo: {t['production_quality']} + {t['brand_consistency']} = {int(t['high_engagement_rate']*100)}% (n={t['obs_count']})")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "production_quality_engagement": prod_table,
        "brand_consistency_engagement": brand_table,
        "heritage_vs_modern_engagement": hvm_table,
        "production_x_brand_combos": combo_table,
        "heritage_vs_modern_by_sector": hvm_sector_table,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "quality_signals.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Quality signals: {total} obs")
    print(f"\nProduction quality → engagement:")
    for r in prod_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['value']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['obs_count']}")
    print(f"\nBrand consistency → engagement:")
    for r in brand_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['value']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['obs_count']}")
    print(f"\nHeritage vs Modern → engagement:")
    for r in hvm_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['value']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['obs_count']}")
    print(f"\nProduction × brand combos:")
    for r in combo_table[:6]:
        print(f"  {r['production_quality']:<20} × {r['brand_consistency']:<10} {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nOutput: logs/quality_signals.json")

if __name__ == "__main__":
    main()
