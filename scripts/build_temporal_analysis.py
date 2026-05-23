#!/usr/bin/env python3
"""
build_temporal_analysis.py
Correlate posting day-of-week and month with engagement across 374 dated observations.
Output: logs/temporal_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def agg():
    return {"count": 0, "high_count": 0, "eng_sum": 0.0}


def record(bucket, is_high, eng):
    bucket["count"]      += 1
    bucket["high_count"] += is_high
    bucket["eng_sum"]    += eng


def summarise(bucket, label=""):
    n = bucket["count"]
    if n == 0:
        return {"label": label, "count": 0, "high_engagement_rate": 0.0, "avg_engagement": 0.0, "verdict": "no_data"}
    rate = round(bucket["high_count"] / n, 3)
    avg  = round(bucket["eng_sum"] / n, 3)
    verdict = (
        "strong_positive" if rate >= 0.70 else
        "positive"        if rate >= 0.55 else
        "neutral"         if rate >= 0.40 else
        "weak"            if rate >= 0.25 else
        "avoid"
    )
    return {"label": label, "count": n, "high_engagement_rate": rate, "avg_engagement": avg, "verdict": verdict}


def main():
    dow_buckets   = {d: agg() for d in DAYS}
    month_buckets = {m: agg() for m in MONTHS}
    # Weekend vs weekday
    weekday_bucket = agg()
    weekend_bucket = agg()
    # Quarter
    quarter_buckets = {f"Q{i}": agg() for i in range(1, 5)}
    # Sector × day
    sector_dow = defaultdict(lambda: {d: agg() for d in DAYS})

    total = 0
    dated = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        cr = data.get("content_ref", {}) or {}
        dt_str = cr.get("capture_date")
        if not dt_str:
            continue

        try:
            dt = datetime.strptime(str(dt_str), "%Y-%m-%d")
        except Exception:
            continue

        dated += 1
        qa     = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector", "unknown") or "unknown"

        day   = dt.strftime("%A")
        month = dt.strftime("%B")
        q     = f"Q{(dt.month - 1) // 3 + 1}"

        record(dow_buckets[day], is_high, eng)
        record(month_buckets[month], is_high, eng)
        record(sector_dow[sector][day], is_high, eng)

        if dt.weekday() < 5:  # Mon–Fri
            record(weekday_bucket, is_high, eng)
        else:
            record(weekend_bucket, is_high, eng)

        record(quarter_buckets[q], is_high, eng)

    # Rank days
    dow_results = [
        {**summarise(dow_buckets[d], d), "day": d}
        for d in DAYS
    ]
    dow_results_sorted = sorted(dow_results, key=lambda x: -x["high_engagement_rate"])

    month_results = [
        {**summarise(month_buckets[m], m), "month": m}
        for m in MONTHS
        if month_buckets[m]["count"] > 0
    ]
    month_results_sorted = sorted(month_results, key=lambda x: -x["high_engagement_rate"])

    # Sector × day highlights
    sector_day_insights = {}
    for sector, day_data in sorted(sector_dow.items()):
        ranked = sorted(
            [{"day": d, **summarise(day_data[d], d)} for d in DAYS if day_data[d]["count"] > 0],
            key=lambda x: -x["high_engagement_rate"]
        )
        sector_day_insights[sector] = {
            "best_day": ranked[0]["day"] if ranked else None,
            "best_day_high_eng_rate": ranked[0]["high_engagement_rate"] if ranked else 0,
            "worst_day": ranked[-1]["day"] if ranked else None,
            "day_ranking": ranked
        }

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "obs_with_dates": dated,
        "day_of_week_analysis": {
            "ranked_best_to_worst": dow_results_sorted,
            "weekday_vs_weekend": {
                "weekday": summarise(weekday_bucket, "weekday"),
                "weekend": summarise(weekend_bucket, "weekend")
            }
        },
        "month_analysis": {
            "ranked_best_to_worst": month_results_sorted,
        },
        "quarter_analysis": {
            q: summarise(quarter_buckets[q], q)
            for q in sorted(quarter_buckets)
            if quarter_buckets[q]["count"] > 0
        },
        "sector_by_day_of_week": sector_day_insights,
        "key_findings": []  # populated below
    }

    # Auto-generate findings
    best_day  = dow_results_sorted[0]
    worst_day = dow_results_sorted[-1]
    out["key_findings"] = [
        f"Best day to post: {best_day['day']} ({int(best_day['high_engagement_rate']*100)}% high eng, n={best_day['count']})",
        f"Worst day to post: {worst_day['day']} ({int(worst_day['high_engagement_rate']*100)}% high eng, n={worst_day['count']})",
        f"Weekday vs Weekend: weekday={int(summarise(weekday_bucket)['high_engagement_rate']*100)}% vs weekend={int(summarise(weekend_bucket)['high_engagement_rate']*100)}%",
    ]
    if month_results_sorted:
        best_month = month_results_sorted[0]
        out["key_findings"].append(
            f"Best month: {best_month['month']} ({int(best_month['high_engagement_rate']*100)}% high eng, n={best_month['count']})"
        )

    LOGS.mkdir(exist_ok=True)
    (LOGS / "temporal_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Temporal analysis: {dated}/{total} obs with dates")
    print(f"\nDay of week ranking (best → worst):")
    for r in dow_results_sorted:
        bar = "█" * int(r["high_engagement_rate"] * 20)
        print(f"  {r['day']:<12} n={r['count']:2d} | {int(r['high_engagement_rate']*100):3d}% | {bar}")
    print(f"\nWeekday: {summarise(weekday_bucket)['high_engagement_rate']*100:.0f}% | "
          f"Weekend: {summarise(weekend_bucket)['high_engagement_rate']*100:.0f}%")
    if month_results_sorted:
        print(f"\nTop months:")
        for r in month_results_sorted[:5]:
            print(f"  {r['month']:<12} n={r['count']:2d} | {int(r['high_engagement_rate']*100)}%")
    print(f"\nOutput: logs/temporal_analysis.json")


if __name__ == "__main__":
    main()
