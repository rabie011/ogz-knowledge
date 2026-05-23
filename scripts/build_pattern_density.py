#!/usr/bin/env python3
"""
build_pattern_density.py
Does stacking more patterns per post help or hurt engagement?
Buckets: 0, 1, 2, 3, 4, 5+ patterns per observation.
Also: per-account pattern repertoire diversity score.
Output: logs/pattern_density.json
"""
import json
import math
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def main():
    density_buckets = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    exact_counts    = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    sector_density  = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    account_data    = defaultdict(lambda: {"obs":[],"all_patterns":Counter()})

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
        sector  = data.get("sector","unknown") or "unknown"
        account = data.get("account_handle_normalized","unknown")

        slugs = []
        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: slugs.append(slug)

        n_patterns = len(slugs)
        if n_patterns == 0:   bkt = "0"
        elif n_patterns == 1: bkt = "1"
        elif n_patterns == 2: bkt = "2"
        elif n_patterns == 3: bkt = "3"
        elif n_patterns == 4: bkt = "4"
        else:                 bkt = "5+"

        density_buckets[bkt]["count"] += 1
        density_buckets[bkt]["high"]  += is_high
        density_buckets[bkt]["sum"]   += eng

        exact_counts[n_patterns]["count"] += 1
        exact_counts[n_patterns]["high"]  += is_high
        exact_counts[n_patterns]["sum"]   += eng

        sector_density[sector][bkt]["count"] += 1
        sector_density[sector][bkt]["high"]  += is_high

        account_data[account]["obs"].append({"n_patterns":n_patterns,"eng":eng,"is_high":is_high})
        for s in slugs:
            account_data[account]["all_patterns"][s] += 1

    # Bucket table
    bucket_table = []
    for bkt in ["0","1","2","3","4","5+"]:
        d = density_buckets[bkt]
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        bucket_table.append({
            "patterns_per_post": bkt,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })

    # Exact count table (up to 8)
    exact_table = []
    for n_pat in sorted(exact_counts.keys()):
        if n_pat > 8: continue
        d = exact_counts[n_pat]
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        exact_table.append({
            "exact_pattern_count": n_pat,
            "obs_count": n,
            "high_engagement_rate": rate,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })

    # Per-account diversity
    account_profiles = []
    for acc, info in account_data.items():
        obs_list = info["obs"]
        n = len(obs_list)
        if n == 0: continue
        avg_patterns = round(sum(o["n_patterns"] for o in obs_list)/n, 2)
        unique_patterns = len(info["all_patterns"])
        avg_eng = round(sum(o["eng"] for o in obs_list)/n, 3)
        high_rate = round(sum(o["is_high"] for o in obs_list)/n, 3)
        # Shannon entropy of pattern usage = diversity score
        total_pattern_uses = sum(info["all_patterns"].values())
        if total_pattern_uses > 0:
            entropy = -sum(
                (c/total_pattern_uses) * math.log2(c/total_pattern_uses)
                for c in info["all_patterns"].values() if c > 0
            )
        else:
            entropy = 0.0
        account_profiles.append({
            "account": acc,
            "obs_count": n,
            "avg_patterns_per_post": avg_patterns,
            "unique_patterns_used": unique_patterns,
            "pattern_diversity_entropy": round(entropy, 3),
            "avg_engagement": avg_eng,
            "high_engagement_rate": high_rate,
        })
    account_profiles.sort(key=lambda x: -x["pattern_diversity_entropy"])

    # Sector density breakdown
    sector_table = {}
    for sec, bkts in sector_density.items():
        rows = []
        for bkt in ["0","1","2","3","4","5+"]:
            d = bkts.get(bkt, {"count":0,"high":0})
            n = d["count"]
            if n == 0: continue
            rows.append({"patterns_per_post":bkt,"count":n,
                          "high_eng_rate":round(d["high"]/n,3) if n else 0})
        sector_table[sec] = rows

    # Key findings
    findings = []
    peak_bkt = max(bucket_table, key=lambda x: x["high_engagement_rate"])
    zero_bkt = next((b for b in bucket_table if b["patterns_per_post"]=="0"), None)
    findings.append(
        f"Sweet spot: {peak_bkt['patterns_per_post']} patterns per post = "
        f"{int(peak_bkt['high_engagement_rate']*100)}% high eng (n={peak_bkt['obs_count']})"
    )
    if zero_bkt:
        findings.append(
            f"Zero-pattern posts: {int(zero_bkt['high_engagement_rate']*100)}% — "
            f"{'above' if zero_bkt['high_engagement_rate'] > CORPUS_BASELINE else 'below'} baseline"
        )
    if account_profiles:
        most_diverse = account_profiles[0]
        findings.append(
            f"Most diverse account: {most_diverse['account'][:40]} "
            f"(entropy={most_diverse['pattern_diversity_entropy']}, {most_diverse['unique_patterns_used']} unique patterns)"
        )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "density_bucket_engagement": bucket_table,
        "exact_count_engagement": exact_table,
        "sector_density_breakdown": sector_table,
        "account_diversity_profiles": account_profiles,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "pattern_density.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Pattern density: {total} obs")
    print(f"\nPatterns per post → engagement:")
    print(f"  {'N patterns':<14} {'HighEng':>8}  {'Lift':>7}  {'n':>5}")
    print("  " + "─"*44)
    for b in bucket_table:
        lift = f"+{int(b['lift_vs_baseline']*100)}%" if b['lift_vs_baseline']>=0 else f"{int(b['lift_vs_baseline']*100)}%"
        bar = "█" * int(b["high_engagement_rate"] * 15)
        print(f"  {b['patterns_per_post']:<14} {int(b['high_engagement_rate']*100):>7}%  {lift:>7}  {b['obs_count']:>5}  {bar}")
    print(f"\nAccount pattern diversity (top 5 by entropy):")
    for a in account_profiles[:5]:
        print(f"  {a['account'][:38]:<40} entropy={a['pattern_diversity_entropy']}  "
              f"{a['unique_patterns_used']} unique  {int(a['high_engagement_rate']*100)}% eng")
    print(f"\nOutput: logs/pattern_density.json")

if __name__ == "__main__":
    main()
