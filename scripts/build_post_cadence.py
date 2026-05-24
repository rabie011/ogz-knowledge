#!/usr/bin/env python3
"""
build_post_cadence.py
Analyse posting frequency and cadence patterns from capture_date fields.

Per account:
  - Posts per week / month
  - Peak posting months
  - Gap between posts (min / avg / max days)
  - Posting acceleration: recent vs historical

Corpus-level:
  - Monthly volume
  - Day-of-week distribution (from dates)
  - Seasonal patterns

Output: logs/post_cadence_analysis.json
"""
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75, "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}

SAUDI_SEASONS = {
    1: "winter", 2: "winter", 3: "spring",
    4: "spring", 5: "pre_summer", 6: "summer",
    7: "summer", 8: "summer", 9: "autumn",
    10: "national_day_season", 11: "autumn", 12: "winter",
}


def _parse_date(s) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s)[:10])
    except Exception:
        return None


def main():
    by_account = defaultdict(list)  # account → [(date, engagement)]
    monthly    = Counter()
    weekday    = Counter()
    seasonal   = Counter()
    occ_timing = defaultdict(list)   # occasion → [month]

    total_with_date = 0

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        dt  = _parse_date((d.get("content_ref") or {}).get("capture_date"))
        qa  = d.get("quality_assessment") or {}
        eng = ENG_MAP.get(str(qa.get("engagement_potential") or "").lower(), 0.5)
        acc = d.get("account_handle_normalized", "?")
        occ = d.get("occasion") or "evergreen"

        if not dt:
            continue
        total_with_date += 1

        by_account[acc].append((dt, eng))
        monthly[dt.strftime("%Y-%m")] += 1
        weekday[dt.strftime("%A")] += 1
        seasonal[SAUDI_SEASONS.get(dt.month, "unknown")] += 1
        occ_timing[occ].append(dt.month)

    # ── Per-account cadence ─────────────────────────────────────────
    account_cadence = {}
    for acc, entries in sorted(by_account.items()):
        entries.sort(key=lambda x: x[0])
        dates = [e[0] for e in entries]
        engs  = [e[1] for e in entries]

        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_gap = round(sum(gaps) / len(gaps), 1) if gaps else None
        posts_per_month = round(len(entries) / max((dates[-1]-dates[0]).days / 30, 1), 1) if len(entries) > 1 else len(entries)

        # Recent (last 90 days) vs historical
        cutoff = max(dates) - timedelta(days=90)
        recent_count = sum(1 for d in dates if d >= cutoff)
        hist_count   = len(dates) - recent_count
        hist_months  = max((cutoff - dates[0]).days / 30, 1)
        recent_rate  = round(recent_count / 3, 1)  # posts/month
        hist_rate    = round(hist_count / hist_months, 1)

        # Peak months
        month_counts = Counter(d.strftime("%B") for d in dates)
        peak_month   = month_counts.most_common(1)[0][0] if month_counts else None

        account_cadence[acc] = {
            "total_obs": len(entries),
            "date_range": f"{dates[0].date()} → {dates[-1].date()}",
            "avg_gap_days": avg_gap,
            "posts_per_month": posts_per_month,
            "recent_rate_per_month": recent_rate,
            "historical_rate_per_month": hist_rate,
            "trending": "accelerating" if recent_rate > hist_rate * 1.2 else
                        "decelerating" if recent_rate < hist_rate * 0.8 else "stable",
            "peak_month": peak_month,
            "avg_engagement": round(sum(engs) / len(engs), 3),
        }

    # ── Occasion timing ─────────────────────────────────────────────
    occ_peak_months = {}
    for occ, months in occ_timing.items():
        month_counts = Counter(months)
        top = month_counts.most_common(2)
        occ_peak_months[occ] = {
            "peak_months": [datetime(2000, m, 1).strftime("%B") for m, _ in top],
            "total_posts": len(months),
        }

    # ── Output ──────────────────────────────────────────────────────
    out = {
        "meta": {
            "total_obs_with_date": total_with_date,
            "total_accounts": len(account_cadence),
        },
        "account_cadence": account_cadence,
        "corpus_monthly_volume": dict(sorted(monthly.items())),
        "weekday_distribution": dict(weekday.most_common()),
        "seasonal_distribution": dict(seasonal.most_common()),
        "occasion_peak_months": occ_peak_months,
        "key_findings": [],
    }

    # Findings
    fastest = min(account_cadence.items(), key=lambda x: x[1]["avg_gap_days"] or 999)
    slowest = max((a for a in account_cadence.items() if a[1]["avg_gap_days"]), key=lambda x: x[1]["avg_gap_days"])
    accel   = [a for a, v in account_cadence.items() if v["trending"] == "accelerating"]

    out["key_findings"] = [
        f"Fastest poster: {fastest[0]} ({fastest[1]['avg_gap_days']} days avg gap)",
        f"Slowest poster: {slowest[0]} ({slowest[1]['avg_gap_days']} days avg gap)",
        f"Accelerating accounts: {', '.join(accel) or 'none'}",
        f"Peak corpus month: {max(monthly, key=monthly.get)}",
        f"Most common posting day: {max(weekday, key=weekday.get)}",
    ]

    LOGS.mkdir(exist_ok=True)
    (LOGS / "post_cadence_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("POST CADENCE ANALYSIS COMPLETE")
    print(f"  Obs with date    : {total_with_date}/648")
    print(f"  Accounts analysed: {len(account_cadence)}")
    print()
    print("  Account cadence:")
    for acc, v in sorted(account_cadence.items(), key=lambda x: x[1]["posts_per_month"], reverse=True):
        trend = {"accelerating":"↑","decelerating":"↓","stable":"→"}[v["trending"]]
        print(f"    {acc:<40} {v['posts_per_month']:.1f}/mo  gap={v['avg_gap_days']}d  {trend}")
    print()
    print("  Key findings:")
    for f in out["key_findings"]:
        print(f"    ▸ {f}")
    print()
    print("  Output → logs/post_cadence_analysis.json")


if __name__ == "__main__":
    main()
