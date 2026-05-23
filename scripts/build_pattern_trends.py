#!/usr/bin/env python3
"""
build_pattern_trends.py
Temporal trend analysis for patterns using capture_date on 374/474 obs.
Which patterns are rising, stable, or declining in engagement over time?
Output: logs/pattern_trend_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def parse_date(s):
    if not s: return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try: return datetime.strptime(str(s)[:19], fmt[:len(str(s)[:10]) + (9 if 'T' in str(s) else 0)])
        except: pass
    try: return datetime.fromisoformat(str(s)[:10])
    except: return None


def to_quarter(dt):
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{q}"


def to_half(dt):
    h = 1 if dt.month <= 6 else 2
    return f"{dt.year}-H{h}"


def load_pattern_names():
    names = {}
    for pf in PATTERNS.rglob("*.json"):
        try:
            p = json.loads(pf.read_text())
            if p.get("pattern_slug"):
                names[p["pattern_slug"]] = p.get("pattern_name", p["pattern_slug"])
        except: pass
    return names


def trend_direction(rates_ordered):
    """Simple linear trend from list of (period, rate) tuples sorted by period."""
    if len(rates_ordered) < 2: return "insufficient_data"
    first_half = [r for _, r in rates_ordered[:len(rates_ordered)//2 + 1]]
    second_half= [r for _, r in rates_ordered[len(rates_ordered)//2:]]
    avg_first  = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    delta = avg_second - avg_first
    if delta >  0.10: return "rising"
    if delta < -0.10: return "declining"
    return "stable"


def main():
    pattern_names = load_pattern_names()

    # Per pattern × quarter
    pat_quarter = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Overall corpus × quarter
    corpus_quarter = defaultdict(lambda: {"count":0,"high":0})
    # Per quarter obs count (for coverage)
    quarter_obs = defaultdict(int)

    total = 0
    dated = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cr      = data.get("content_ref",{}) or {}
        raw_date= cr.get("capture_date") or cr.get("post_date")
        dt      = parse_date(raw_date)
        if not dt: continue

        dated  += 1
        quarter = to_quarter(dt)
        quarter_obs[quarter] += 1

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        corpus_quarter[quarter]["count"] += 1
        corpus_quarter[quarter]["high"]  += is_high

        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if not slug: continue
            pat_quarter[slug][quarter]["count"] += 1
            pat_quarter[slug][quarter]["high"]  += is_high

    # Sort quarters chronologically
    all_quarters = sorted(corpus_quarter.keys())

    # Corpus trend
    corpus_trend = []
    for q in all_quarters:
        d = corpus_quarter[q]
        n = d["count"]
        corpus_trend.append({
            "period": q,
            "obs_count": n,
            "high_engagement_rate": round(d["high"]/n, 3) if n else 0,
        })

    # Pattern trend profiles (min 10 total dated obs for the pattern)
    pattern_trends = []
    for slug, quarters in pat_quarter.items():
        total_dated = sum(d["count"] for d in quarters.values())
        if total_dated < 5: continue

        per_period = []
        for q in all_quarters:
            d = quarters.get(q, {"count":0,"high":0})
            n = d["count"]
            if n > 0:
                per_period.append({
                    "period": q,
                    "count": n,
                    "high_eng_rate": round(d["high"]/n, 3),
                })

        if len(per_period) < 2: continue

        # Early vs late half engagement
        rates_ordered = [(p["period"], p["high_eng_rate"]) for p in per_period]
        direction     = trend_direction(rates_ordered)

        all_rates  = [p["high_eng_rate"] for p in per_period]
        overall    = round(sum(d["high"] for d in quarters.values()) /
                           sum(d["count"] for d in quarters.values()), 3)
        volatility = round(max(all_rates) - min(all_rates), 3)

        pattern_trends.append({
            "slug": slug,
            "name": pattern_names.get(slug, slug),
            "total_dated_obs": total_dated,
            "periods_active": len(per_period),
            "overall_high_eng_rate": overall,
            "trend_direction": direction,
            "volatility": volatility,
            "peak_period": per_period[all_rates.index(max(all_rates))]["period"],
            "peak_rate": max(all_rates),
            "per_period": per_period,
        })

    # Sort buckets
    rising   = sorted([p for p in pattern_trends if p["trend_direction"] == "rising"],
                      key=lambda x: -x["overall_high_eng_rate"])
    declining= sorted([p for p in pattern_trends if p["trend_direction"] == "declining"],
                      key=lambda x: -x["overall_high_eng_rate"])
    stable   = sorted([p for p in pattern_trends if p["trend_direction"] == "stable"],
                      key=lambda x: -x["overall_high_eng_rate"])

    # Key findings
    findings = []
    findings.append(f"{dated}/{total} obs have capture_date. {len(all_quarters)} quarters covered: {all_quarters[0]} → {all_quarters[-1]}.")
    if rising:
        r = rising[0]
        findings.append(f"Strongest rising pattern: '{r['slug']}' — engagement trending UP (overall {int(r['overall_high_eng_rate']*100)}%)")
    if declining:
        d = declining[0]
        findings.append(f"Steepest declining pattern: '{d['slug']}' — engagement trending DOWN (overall {int(d['overall_high_eng_rate']*100)}%)")

    # Check product_hero trend specifically
    ph = next((p for p in pattern_trends if p["slug"] == "product_hero"), None)
    if ph:
        findings.append(f"product_hero trend: {ph['trend_direction']} (peak {ph['peak_period']}, volatility {ph['volatility']})")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "dated_obs": dated,
        "quarters_covered": all_quarters,
        "corpus_engagement_trend": corpus_trend,
        "pattern_trend_summary": {
            "total_patterns_with_trend_data": len(pattern_trends),
            "rising_count": len(rising),
            "stable_count": len(stable),
            "declining_count": len(declining),
        },
        "rising_patterns": rising[:10],
        "stable_patterns": stable[:10],
        "declining_patterns": declining[:10],
        "all_pattern_trends": sorted(pattern_trends, key=lambda x: -x["overall_high_eng_rate"]),
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "pattern_trend_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Pattern trends: {dated}/{total} dated obs, {len(all_quarters)} quarters, {len(pattern_trends)} patterns tracked")
    print(f"\nCorpus engagement by quarter:")
    for q in corpus_trend:
        bar = "█" * int(q["high_engagement_rate"] * 20)
        print(f"  {q['period']}  {int(q['high_engagement_rate']*100):>3}%  {bar}  n={q['obs_count']}")
    print(f"\nRising patterns ({len(rising)}):")
    for p in rising[:5]:
        print(f"  ↑  {p['slug']:<40} {int(p['overall_high_eng_rate']*100):>3}%  peak={p['peak_period']}")
    print(f"\nDeclining patterns ({len(declining)}):")
    for p in declining[:5]:
        print(f"  ↓  {p['slug']:<40} {int(p['overall_high_eng_rate']*100):>3}%  peak={p['peak_period']}")
    print(f"\nOutput: logs/pattern_trend_analysis.json")


if __name__ == "__main__":
    main()
