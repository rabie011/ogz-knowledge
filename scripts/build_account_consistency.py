#!/usr/bin/env python3
"""
build_account_consistency.py
Two unmined account-level questions:
  1. Engagement consistency — which accounts reliably hit high engagement vs. volatile ones?
  2. Seasonal content ratio — does posting more occasion-specific content lift overall performance?
Output: logs/account_consistency.json
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


def stdev(values):
    if len(values) < 2: return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean)**2 for v in values) / len(values)
    return math.sqrt(variance)


def main():
    accounts = defaultdict(lambda: {
        "sector": None,
        "eng_scores": [],
        "occasions": [],
        "patterns_per_post": [],
        "media_types": Counter(),
        "post_dates": [],
    })

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        account = data.get("account_handle_normalized","unknown")
        sector  = data.get("sector","unknown") or "unknown"

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)

        cn  = data.get("cultural_notes",{}) or {}
        occ = str(cn.get("occasion_relevance","") or "evergreen").lower().strip() or "evergreen"

        cr  = data.get("content_ref",{}) or {}
        mt  = str(cr.get("content_type","") or "").lower()
        date= cr.get("capture_date") or cr.get("post_date")

        slugs = [pm.get("pattern_slug","") if isinstance(pm,dict) else pm
                 for pm in data.get("pattern_matches",[]) if pm]
        slugs = [s for s in slugs if s]

        accounts[account]["sector"]  = sector
        accounts[account]["eng_scores"].append(eng)
        accounts[account]["occasions"].append(occ)
        accounts[account]["patterns_per_post"].append(len(slugs))
        if mt: accounts[account]["media_types"][mt] += 1
        if date: accounts[account]["post_dates"].append(str(date)[:10])

    # Build profiles
    profiles = []
    for acc, info in accounts.items():
        eng_scores = info["eng_scores"]
        n = len(eng_scores)
        if n < 3: continue

        mean_eng  = sum(eng_scores) / n
        high_rate = sum(1 for e in eng_scores if e >= 0.75) / n
        sd        = stdev(eng_scores)
        # Consistency = inverse of coefficient of variation (lower variance = more consistent)
        cv = sd / mean_eng if mean_eng > 0 else 1.0
        consistency_score = round(max(0, 1.0 - cv), 3)  # 1.0 = perfectly consistent

        # Seasonal ratio
        n_evergreen = sum(1 for o in info["occasions"] if o == "evergreen")
        seasonal_ratio = round(1 - n_evergreen / n, 3)

        # Avg patterns per post
        avg_patterns = round(sum(info["patterns_per_post"]) / n, 2)

        # Dominant media type
        dominant_media = info["media_types"].most_common(1)[0][0] if info["media_types"] else None

        profiles.append({
            "account": acc,
            "sector": info["sector"],
            "obs_count": n,
            "avg_engagement": round(mean_eng, 3),
            "high_engagement_rate": round(high_rate, 3),
            "engagement_stdev": round(sd, 3),
            "consistency_score": consistency_score,
            "consistency_grade": (
                "A" if consistency_score >= 0.70 else
                "B" if consistency_score >= 0.50 else
                "C" if consistency_score >= 0.30 else "D"
            ),
            "seasonal_content_ratio": seasonal_ratio,
            "avg_patterns_per_post": avg_patterns,
            "dominant_media_type": dominant_media,
        })

    # Sort variants
    by_consistency = sorted(profiles, key=lambda x: -x["consistency_score"])
    by_high_rate   = sorted(profiles, key=lambda x: -x["high_engagement_rate"])
    by_seasonal    = sorted(profiles, key=lambda x: -x["seasonal_content_ratio"])

    # Correlation: seasonal_ratio vs high_engagement_rate
    if len(profiles) >= 3:
        seasonal_rates = [(p["seasonal_content_ratio"], p["high_engagement_rate"]) for p in profiles]
        mean_s = sum(s for s,_ in seasonal_rates) / len(seasonal_rates)
        mean_e = sum(e for _,e in seasonal_rates) / len(seasonal_rates)
        cov = sum((s-mean_s)*(e-mean_e) for s,e in seasonal_rates) / len(seasonal_rates)
        sd_s = stdev([s for s,_ in seasonal_rates])
        sd_e = stdev([e for _,e in seasonal_rates])
        seasonal_correlation = round(cov / (sd_s * sd_e), 3) if sd_s > 0 and sd_e > 0 else 0
    else:
        seasonal_correlation = None

    # Consistency vs performance: are consistent accounts also high performers?
    consistency_performance = [
        {
            "account": p["account"],
            "consistency_score": p["consistency_score"],
            "high_engagement_rate": p["high_engagement_rate"],
            "consistency_grade": p["consistency_grade"],
        }
        for p in by_consistency
    ]

    findings = []
    if by_consistency:
        most = by_consistency[0]
        least = by_consistency[-1]
        findings.append(
            f"Most consistent: {most['account'][:40]} (score={most['consistency_score']}, "
            f"{int(most['high_engagement_rate']*100)}% high eng)"
        )
        findings.append(
            f"Most volatile: {least['account'][:40]} (score={least['consistency_score']}, "
            f"{int(least['high_engagement_rate']*100)}% high eng)"
        )
    if seasonal_correlation is not None:
        direction = "positive" if seasonal_correlation > 0.1 else "negative" if seasonal_correlation < -0.1 else "neutral"
        findings.append(
            f"Seasonal content ratio correlation with engagement: {seasonal_correlation} ({direction}). "
            + ("More seasonal = better performance." if seasonal_correlation > 0.1 else
               "No clear relationship between seasonal ratio and engagement." if abs(seasonal_correlation) <= 0.1
               else "Surprising: more seasonal content correlates with LOWER engagement — check evergreen quality.")
        )
    if by_seasonal:
        most_seasonal = by_seasonal[0]
        findings.append(
            f"Most occasion-driven account: {most_seasonal['account'][:40]} "
            f"({int(most_seasonal['seasonal_content_ratio']*100)}% seasonal, "
            f"{int(most_seasonal['high_engagement_rate']*100)}% eng)"
        )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "account_count": len(profiles),
        "seasonal_ratio_vs_engagement_correlation": seasonal_correlation,
        "by_consistency": by_consistency,
        "by_seasonal_ratio": by_seasonal,
        "by_high_engagement": by_high_rate,
        "consistency_vs_performance": consistency_performance,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "account_consistency.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Account consistency: {len(profiles)} accounts, {total} obs")
    print(f"\nEngagement consistency ranking:")
    print(f"  {'Account':<38} {'Consist':>8}  {'Grade':<6}  {'HighEng':>8}  {'Seasonal':>9}")
    print("  " + "─"*82)
    for p in by_consistency:
        print(f"  {p['account'][:36]:<38} {p['consistency_score']:>8.3f}  [{p['consistency_grade']}]    "
              f"{int(p['high_engagement_rate']*100):>7}%  {int(p['seasonal_content_ratio']*100):>8}%")
    if seasonal_correlation is not None:
        print(f"\nSeasonal ratio ↔ engagement correlation: {seasonal_correlation}")
    print(f"\nOutput: logs/account_consistency.json")

if __name__ == "__main__":
    main()
