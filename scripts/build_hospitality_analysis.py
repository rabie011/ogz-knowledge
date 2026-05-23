#!/usr/bin/env python3
"""
build_hospitality_analysis.py
How does Saudi cultural density (hospitality cue count) correlate with engagement?
Buckets: 0 cues, 1, 2, 3, 4+ — cross with engagement, sector, occasion, heritage_vs_modern.
Output: logs/hospitality_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def bucket(n):
    if n == 0: return "0"
    if n == 1: return "1"
    if n == 2: return "2"
    if n == 3: return "3"
    return "4+"


def main():
    # Cue-count buckets
    buckets = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Cue type frequency and engagement
    cue_types = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Sector × cue-count
    sector_bucket = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Heritage_vs_modern × cue-count
    hvm_bucket = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Occasion × cue-count
    occ_bucket = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Per-account hospitality avg
    accounts = defaultdict(lambda: {"cue_counts":[],"eng_scores":[]})

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cn      = data.get("cultural_notes",{}) or {}
        cues    = cn.get("hospitality_cues") or []
        n_cues  = len(cues)
        bkt     = bucket(n_cues)
        hvm     = str(cn.get("heritage_vs_modern") or "unknown").lower()[:20]
        occ     = str(cn.get("occasion_relevance") or "evergreen").lower().strip() or "evergreen"
        sector  = data.get("sector","unknown") or "unknown"
        account = data.get("account_handle_normalized","unknown")

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        buckets[bkt]["count"] += 1
        buckets[bkt]["high"]  += is_high
        buckets[bkt]["sum"]   += eng

        for cue in cues:
            if isinstance(cue, str) and cue.strip():
                ct = cue.strip().lower()
                cue_types[ct]["count"] += 1
                cue_types[ct]["high"]  += is_high
                cue_types[ct]["sum"]   += eng

        sector_bucket[sector][bkt]["count"] += 1
        sector_bucket[sector][bkt]["high"]  += is_high
        hvm_bucket[hvm][bkt]["count"]       += 1
        hvm_bucket[hvm][bkt]["high"]        += is_high
        occ_bucket[occ][bkt]["count"]       += 1
        occ_bucket[occ][bkt]["high"]        += is_high

        accounts[account]["cue_counts"].append(n_cues)
        accounts[account]["eng_scores"].append(eng)

    # Build bucket table
    bucket_table = []
    for bkt in ["0","1","2","3","4+"]:
        d = buckets[bkt]
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        bucket_table.append({
            "hospitality_cues": bkt,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement_score": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })

    # Top cue types by frequency
    top_cue_types = []
    for ct, d in sorted(cue_types.items(), key=lambda x: -x[1]["count"])[:20]:
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        top_cue_types.append({
            "cue_type": ct,
            "frequency": n,
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })

    # Sector breakdown
    sector_table = {}
    for sec, bkts in sector_bucket.items():
        rows = []
        for bkt in ["0","1","2","3","4+"]:
            d = bkts.get(bkt, {"count":0,"high":0})
            n = d["count"]
            if n == 0: continue
            rows.append({
                "hospitality_cues": bkt,
                "count": n,
                "high_eng_rate": round(d["high"]/n, 3) if n else 0,
            })
        sector_table[sec] = rows

    # Per-account hospitality signature
    account_rows = []
    for acc, info in accounts.items():
        counts = info["cue_counts"]
        engs   = info["eng_scores"]
        avg_cues = round(sum(counts)/len(counts), 2) if counts else 0
        avg_eng  = round(sum(engs)/len(engs), 3) if engs else 0
        high_rate = round(sum(1 for e in engs if e >= 0.75)/len(engs), 3) if engs else 0
        account_rows.append({
            "account": acc,
            "avg_hospitality_cues_per_post": avg_cues,
            "avg_engagement": avg_eng,
            "high_engagement_rate": high_rate,
            "obs_count": len(counts),
        })
    account_rows.sort(key=lambda x: -x["avg_hospitality_cues_per_post"])

    # Key findings
    findings = []
    peak = max(bucket_table, key=lambda x: x["high_engagement_rate"]) if bucket_table else None
    zero = next((b for b in bucket_table if b["hospitality_cues"] == "0"), None)
    if peak and zero:
        gap = round(peak["high_engagement_rate"] - zero["high_engagement_rate"], 3)
        findings.append(
            f"Peak engagement at {peak['hospitality_cues']} hospitality cues: "
            f"{int(peak['high_engagement_rate']*100)}% vs {int(zero['high_engagement_rate']*100)}% for zero cues "
            f"({int(gap*100)}pp gap)"
        )
    if top_cue_types:
        best_cue = max(top_cue_types, key=lambda x: x["high_engagement_rate"])
        findings.append(
            f"Highest-engagement cue type: '{best_cue['cue_type']}' "
            f"({int(best_cue['high_engagement_rate']*100)}% high eng, n={best_cue['frequency']})"
        )
    if account_rows:
        top_acc = account_rows[0]
        findings.append(
            f"Highest hospitality density account: {top_acc['account'][:40]} "
            f"({top_acc['avg_hospitality_cues_per_post']} avg cues, {int(top_acc['high_engagement_rate']*100)}% high eng)"
        )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "hospitality_cue_bucket_engagement": bucket_table,
        "top_cue_types_by_frequency": top_cue_types,
        "sector_hospitality_breakdown": sector_table,
        "account_hospitality_signatures": account_rows,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "hospitality_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Hospitality analysis: {total} obs")
    print(f"\nCue count → engagement:")
    print(f"  {'Cues':<8} {'HighEng':>8}  {'Lift':>7}  {'n':>5}")
    print("  " + "─"*36)
    for b in bucket_table:
        lift = f"+{int(b['lift_vs_baseline']*100)}%" if b['lift_vs_baseline'] >= 0 else f"{int(b['lift_vs_baseline']*100)}%"
        print(f"  {b['hospitality_cues']:<8} {int(b['high_engagement_rate']*100):>7}%  {lift:>7}  {b['obs_count']:>5}")
    print(f"\nTop cue types:")
    for ct in top_cue_types[:8]:
        print(f"  {ct['cue_type']:<40} {int(ct['high_engagement_rate']*100):>3}%  n={ct['frequency']}")
    print(f"\nOutput: logs/hospitality_analysis.json")


if __name__ == "__main__":
    main()
