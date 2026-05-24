#!/usr/bin/env python3
"""
build_competitive_gap.py
For each account: which high-engagement patterns do same-sector competitors use
that this account does NOT? The differentiation gap = what this account is missing.
Also: unique patterns (only this account uses them), and the overlap score.
Output: logs/competitive_gap.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
MIN_ENG_THRESHOLD = 0.75   # patterns must be "high engagement" in competitor to count as a gap
MIN_COMPETITOR_USES = 2    # pattern must appear at least 2x in competitor corpus to matter


def main():
    # Collect per-account data
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "patterns": Counter(),       # slug → count for this account
        "pattern_eng": defaultdict(list),  # slug → list of eng scores
    })

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        acc    = data.get("account_handle_normalized","unknown")
        sector = data.get("sector","unknown") or "unknown"
        qa     = data.get("quality_assessment",{}) or {}
        eng_raw= str(qa.get("engagement_potential","") or "").lower()
        eng    = ENG_MAP.get(eng_raw, 0.5)

        slugs = [pm.get("pattern_slug","") if isinstance(pm,dict) else pm
                 for pm in data.get("pattern_matches",[]) if pm]
        slugs = [s for s in slugs if s]

        accounts[acc]["sector"]     = sector
        accounts[acc]["obs_count"] += 1
        for s in slugs:
            accounts[acc]["patterns"][s]   += 1
            accounts[acc]["pattern_eng"][s].append(eng)

    # Sector → {pattern → {total_uses, high_eng_rate, accounts_using}}
    sector_patterns = defaultdict(lambda: defaultdict(lambda: {"uses":0,"high":0,"accounts":set()}))
    for acc, info in accounts.items():
        sector = info["sector"]
        for slug, cnt in info["patterns"].items():
            engs = info["pattern_eng"][slug]
            high = sum(1 for e in engs if e >= 0.75)
            sector_patterns[sector][slug]["uses"]     += cnt
            sector_patterns[sector][slug]["high"]     += high
            sector_patterns[sector][slug]["accounts"].add(acc)

    # Compute engagement rate per sector-level pattern
    sector_pattern_rates = {}
    for sector, pats in sector_patterns.items():
        sector_pattern_rates[sector] = {}
        for slug, d in pats.items():
            uses = d["uses"]
            rate = round(d["high"]/uses, 3) if uses else 0
            sector_pattern_rates[sector][slug] = {
                "uses": uses,
                "high_eng_rate": rate,
                "account_count": len(d["accounts"]),
                "accounts": list(d["accounts"]),
            }

    # Build gap report per account
    gap_reports = []
    for acc, info in sorted(accounts.items(), key=lambda x: -x[1]["obs_count"]):
        n = info["obs_count"]
        if n < 3: continue
        sector = info["sector"]
        my_patterns = set(info["patterns"].keys())
        sector_pats = sector_pattern_rates.get(sector, {})

        # Competitor patterns = sector patterns NOT from this account alone
        # High-value gaps: patterns others use with high engagement, this account doesn't
        gaps = []
        for slug, sp in sector_pats.items():
            if slug in my_patterns: continue
            # Must be used by at least 1 other account with min uses
            other_accounts = [a for a in sp["accounts"] if a != acc]
            if not other_accounts: continue
            if sp["uses"] < MIN_COMPETITOR_USES: continue
            if sp["high_eng_rate"] >= MIN_ENG_THRESHOLD:
                gaps.append({
                    "pattern": slug,
                    "competitor_high_eng_rate": sp["high_eng_rate"],
                    "competitor_uses": sp["uses"],
                    "used_by_accounts": other_accounts[:3],
                    "priority": "high" if sp["high_eng_rate"] >= 0.85 else "medium",
                })
        gaps.sort(key=lambda x: -x["competitor_high_eng_rate"])

        # Unique patterns: only this account uses them
        unique_pats = []
        for slug in my_patterns:
            sp = sector_pats.get(slug, {})
            accs = sp.get("accounts", [acc])
            if len(accs) == 1 and acc in accs:
                rate_list = info["pattern_eng"][slug]
                own_rate = round(sum(1 for e in rate_list if e >= 0.75)/len(rate_list), 3) if rate_list else 0
                unique_pats.append({
                    "pattern": slug,
                    "own_uses": info["patterns"][slug],
                    "own_high_eng_rate": own_rate,
                })
        unique_pats.sort(key=lambda x: -x["own_high_eng_rate"])

        # Overlap score: % of sector top-patterns (n≥2) this account already uses
        sector_top = [s for s, d in sector_pats.items() if d["uses"] >= MIN_COMPETITOR_USES]
        overlap = round(len(my_patterns & set(sector_top)) / len(sector_top), 3) if sector_top else 0

        # Own pattern performance
        own_perf = []
        for slug, cnt in info["patterns"].most_common():
            engs = info["pattern_eng"][slug]
            rate = round(sum(1 for e in engs if e >= 0.75)/len(engs), 3) if engs else 0
            own_perf.append({"pattern": slug, "uses": cnt, "own_high_eng_rate": rate})
        own_perf.sort(key=lambda x: -x["own_high_eng_rate"])

        gap_reports.append({
            "account": acc,
            "sector": sector,
            "obs_count": n,
            "pattern_repertoire_size": len(my_patterns),
            "sector_pattern_overlap_score": overlap,
            "high_value_gaps": gaps[:10],     # top 10 missing high-eng patterns
            "unique_to_this_account": unique_pats[:5],
            "own_pattern_performance": own_perf[:10],
            "strategic_summary": _strategic_summary(acc, gaps, unique_pats, overlap),
        })

    gap_reports.sort(key=lambda x: -x["obs_count"])

    # Sector-level pattern leaderboard
    sector_leaders = {}
    for sector, pats in sector_pattern_rates.items():
        ranked = sorted(pats.items(), key=lambda x: -x[1]["high_eng_rate"])
        sector_leaders[sector] = [
            {"pattern": s, **d}
            for s, d in ranked
            if d["uses"] >= MIN_COMPETITOR_USES
        ][:20]

    findings = []
    for report in gap_reports[:5]:
        if report["high_value_gaps"]:
            top_gap = report["high_value_gaps"][0]
            findings.append(
                f"{report['account']}: biggest gap = '{top_gap['pattern']}' "
                f"({int(top_gap['competitor_high_eng_rate']*100)}% eng, used by {', '.join(top_gap['used_by_accounts'][:2])})"
            )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": 0.54,
        "total_obs": total,
        "account_gap_reports": gap_reports,
        "sector_pattern_leaderboard": sector_leaders,
        "key_findings": findings,
        "how_to_use": (
            "high_value_gaps = patterns competitors use with high engagement that this account hasn't tried. "
            "unique_to_this_account = this brand's differentiation moat. "
            "sector_pattern_overlap_score = how much of the sector playbook this account already covers (1.0 = full overlap). "
            "Use high_value_gaps for creative brief expansion. Use unique patterns for brand positioning."
        ),
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "competitive_gap.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Competitive gap analysis: {len(gap_reports)} accounts, {total} obs")
    print(f"\n  {'Account':<38} {'Sector':<12} {'Gaps':>5}  {'Unique':>6}  {'Overlap':>8}")
    print("  " + "─"*80)
    for r in gap_reports:
        print(f"  {r['account'][:36]:<38} {r['sector']:<12} {len(r['high_value_gaps']):>5}  "
              f"{len(r['unique_to_this_account']):>6}  {int(r['sector_pattern_overlap_score']*100):>7}%")
    print(f"\nKey findings:")
    for f in findings:
        print(f"  ▸ {f}")
    print(f"\nOutput: logs/competitive_gap.json")


def _strategic_summary(acc, gaps, unique_pats, overlap):
    parts = []
    if gaps:
        parts.append(f"Missing {len(gaps)} high-engagement competitor patterns. Priority: {gaps[0]['pattern']}.")
    if unique_pats:
        parts.append(f"Owns {len(unique_pats)} unique patterns — differentiation moat.")
    if overlap >= 0.8:
        parts.append("High sector alignment — limited differentiation risk.")
    elif overlap < 0.4:
        parts.append("Low sector overlap — either highly differentiated or underexploring proven patterns.")
    return " ".join(parts) if parts else "Insufficient data for strategic summary."


if __name__ == "__main__":
    main()
