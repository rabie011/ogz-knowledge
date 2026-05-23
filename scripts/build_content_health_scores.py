#!/usr/bin/env python3
"""
build_content_health_scores.py
Per-obs weighted health score. Per-account rolling average + trend.
Output: logs/content_health_scores.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

# Ordinal → numeric maps
ENGAGEMENT_MAP = {
    "high": 1.0, "medium": 0.5, "low": 0.0,
    "very_high": 1.0, "above_average": 0.75, "below_average": 0.25
}
PRODUCTION_MAP = {
    "professional": 1.0, "semi_professional": 0.7, "amateur": 0.3,
    "high": 1.0, "medium": 0.7, "low": 0.3
}
BRAND_MAP = {
    "strong": 1.0, "moderate": 0.6, "weak": 0.2,
    "high": 1.0, "medium": 0.6, "low": 0.2
}
COMPLIANCE_MAP = {
    "clean": 1.0, "soft_flags": 0.85, "hard_block": 0.0,
    "flagged": 0.7, "pass": 1.0
}

def safe_lookup(mapping, key, default=0.5):
    if key is None:
        return default
    return mapping.get(str(key).lower().strip(), default)

def score_obs(data):
    cc = data.get("compliance_check", {})
    qa = data.get("quality_assessment", {})
    cn = data.get("cultural_notes", {})

    # Compliance multiplier
    hard_blocks = cc.get("hard_blocks_triggered", [])
    soft_flags = cc.get("soft_flags", [])
    if hard_blocks:
        compliance_mult = 0.0
    elif soft_flags:
        compliance_mult = 0.85
    else:
        compliance_mult = 1.0

    # Engagement
    eng_raw = qa.get("engagement_potential") or qa.get("estimated_engagement_level")
    eng = safe_lookup(ENGAGEMENT_MAP, eng_raw)

    # Production quality
    prod_raw = qa.get("production_quality")
    prod = safe_lookup(PRODUCTION_MAP, prod_raw)

    # Brand consistency
    brand_raw = qa.get("brand_consistency_with_account")
    brand = safe_lookup(BRAND_MAP, brand_raw)

    # Cultural signal bonus
    hvm = cn.get("heritage_vs_modern")
    hosp = cn.get("hospitality_cues", [])
    cultural_bonus = 0.1 if (hvm and len(hosp) > 0) else 0.0

    # Weighted composite (before compliance)
    composite = (eng * 0.35) + (prod * 0.30) + (brand * 0.25) + (cultural_bonus * 0.10)

    # Apply compliance multiplier
    final_score = round(composite * compliance_mult, 4)

    return {
        "score": final_score,
        "components": {
            "compliance_multiplier": compliance_mult,
            "engagement_score": round(eng, 3),
            "production_score": round(prod, 3),
            "brand_consistency_score": round(brand, 3),
            "cultural_bonus": cultural_bonus
        },
        "grade": "A" if final_score >= 0.8 else "B" if final_score >= 0.65 else "C" if final_score >= 0.5 else "D"
    }

def main():
    all_obs_scores = []    # {account, shortcode, sector, score, grade, components, ...}
    account_scores = defaultdict(list)

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        shortcode = data.get("shortcode", obs_file.stem)
        sector = data.get("sector", "unknown")
        obs_ulid = data.get("observation_ulid", "")

        result = score_obs(data)
        entry = {
            "observation_ulid": obs_ulid,
            "account": account,
            "shortcode": shortcode,
            "sector": sector,
            "health_score": result["score"],
            "grade": result["grade"],
            "components": result["components"]
        }
        all_obs_scores.append(entry)
        account_scores[account].append(result["score"])

    # Sort all obs by score desc
    all_obs_scores.sort(key=lambda x: -x["health_score"])

    # Per-account summaries
    account_summaries = {}
    for account, scores in sorted(account_scores.items()):
        n = len(scores)
        avg = round(sum(scores) / n, 4)
        # Trend: compare first half vs second half
        half = n // 2
        if half >= 2:
            first_half_avg = sum(scores[:half]) / half
            second_half_avg = sum(scores[half:]) / (n - half)
            trend = round(second_half_avg - first_half_avg, 4)
            trend_label = "improving" if trend > 0.05 else "declining" if trend < -0.05 else "stable"
        else:
            trend = 0.0
            trend_label = "insufficient_data"

        a_grade = sum(1 for s in scores if s >= 0.8)
        b_grade = sum(1 for s in scores if 0.65 <= s < 0.8)
        c_grade = sum(1 for s in scores if 0.5 <= s < 0.65)
        d_grade = sum(1 for s in scores if s < 0.5)

        account_summaries[account] = {
            "account": account,
            "obs_count": n,
            "avg_health_score": avg,
            "overall_grade": "A" if avg >= 0.8 else "B" if avg >= 0.65 else "C" if avg >= 0.5 else "D",
            "trend_score": trend,
            "trend": trend_label,
            "grade_distribution": {"A": a_grade, "B": b_grade, "C": c_grade, "D": d_grade},
            "top_score": round(max(scores), 4),
            "bottom_score": round(min(scores), 4)
        }

    # Sort accounts by avg score
    account_summaries_sorted = dict(sorted(account_summaries.items(),
                                           key=lambda x: -x[1]["avg_health_score"]))

    # Fleet averages
    all_scores = [e["health_score"] for e in all_obs_scores]
    fleet_avg = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "scoring_weights": {
            "engagement_potential": 0.35,
            "production_quality": 0.30,
            "brand_consistency": 0.25,
            "cultural_bonus": 0.10,
            "compliance_multiplier": "applied_after_composite"
        },
        "fleet_stats": {
            "total_observations": len(all_obs_scores),
            "fleet_avg_health_score": fleet_avg,
            "grade_A_count": sum(1 for s in all_scores if s >= 0.8),
            "grade_B_count": sum(1 for s in all_scores if 0.65 <= s < 0.8),
            "grade_C_count": sum(1 for s in all_scores if 0.5 <= s < 0.65),
            "grade_D_count": sum(1 for s in all_scores if s < 0.5),
            "top_performers": [e["account"] for e in all_obs_scores[:5]],
            "bottom_performers": [e["account"] for e in all_obs_scores[-5:]]
        },
        "account_summaries": account_summaries_sorted,
        "observations_ranked": all_obs_scores
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "content_health_scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Scored {len(all_obs_scores)} observations across {len(account_summaries)} accounts")
    print(f"Fleet avg health score: {fleet_avg}")
    print(f"\nTop 5 accounts by avg health score:")
    for acc, s in list(account_summaries_sorted.items())[:5]:
        print(f"  {acc}: {s['avg_health_score']} ({s['overall_grade']}) — trend: {s['trend']}")
    print(f"Output: logs/content_health_scores.json")

if __name__ == "__main__":
    main()
