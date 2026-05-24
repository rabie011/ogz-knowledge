#!/usr/bin/env python3
"""
build_posting_frequency_analysis.py
Analyze posting cadence, seasonality, and temporal patterns.
Uses capture_date (85% fill = 548/648 obs).

Answers:
  - How often do top-performing accounts post vs weak ones?
  - Which months/quarters show highest engagement?
  - Do accounts post more around occasions?
  - What is the optimal posts-per-week cadence?

Output: logs/posting_frequency_analysis.json
"""
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _lift(avg, baseline): return round(avg - baseline, 3) if avg is not None and baseline is not None else None

MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}


def _parse_date(s):
    if not s: return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d"):
        try: return datetime.strptime(s[:10], fmt)
        except: pass
    return None


def main():
    all_obs = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]
    corpus_engs = [_eng(d) for d in all_obs if _eng(d) is not None]
    corpus_baseline = _avg(corpus_engs)

    # ── Parse dates ──
    dated = []
    for d in all_obs:
        cr = d.get("content_ref") or {}
        dt = _parse_date(cr.get("capture_date",""))
        e  = _eng(d)
        if dt and e is not None:
            dated.append({
                "dt": dt,
                "eng": e,
                "account": d.get("account_handle_normalized",""),
                "sector": d.get("sector",""),
                "occasion": d.get("occasion",""),
                "content_type": cr.get("content_type",""),
            })

    N_dated = len(dated)

    # ── Month × engagement ──
    month_data = defaultdict(list)
    for item in dated:
        month_data[item["dt"].month].append(item["eng"])

    by_month = []
    for m in range(1, 13):
        engs = month_data.get(m, [])
        if len(engs) >= 3:
            avg = _avg(engs)
            by_month.append({
                "month": m,
                "month_name": MONTH_NAMES[m],
                "count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })

    # ── Quarter × engagement ──
    q_data = defaultdict(list)
    for item in dated:
        q = (item["dt"].month - 1) // 3 + 1
        q_data[q].append(item["eng"])

    by_quarter = []
    for q in [1,2,3,4]:
        engs = q_data.get(q,[])
        if engs:
            avg = _avg(engs)
            by_quarter.append({
                "quarter": f"Q{q}",
                "count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })

    # ── Day of week × engagement (from content_ref.day_of_week) ──
    DOW_ORDER = ["sunday","monday","tuesday","wednesday","thursday","friday","saturday"]
    dow_data = defaultdict(list)
    for d in all_obs:
        dow = (d.get("content_ref") or {}).get("day_of_week","")
        e = _eng(d)
        if dow and e is not None:
            dow_data[dow.lower()].append(e)

    by_dow = []
    for day in DOW_ORDER:
        engs = dow_data.get(day,[])
        if engs:
            avg = _avg(engs)
            by_dow.append({
                "day": day,
                "count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })
    by_dow_sorted = sorted(by_dow, key=lambda x: -(x["avg_engagement"] or 0))

    # ── Account posting cadence ──
    acc_dates = defaultdict(list)
    for item in dated:
        acc_dates[item["account"]].append((item["dt"], item["eng"]))

    acc_cadence = []
    for acc, items in sorted(acc_dates.items()):
        if len(items) < 5: continue
        items_sorted = sorted(items, key=lambda x: x[0])
        dates = [x[0] for x in items_sorted]
        engs  = [x[1] for x in items_sorted]

        # Calculate gaps between posts
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_gap  = _avg(gaps)
        avg_eng  = _avg(engs)

        # Posts per week estimate
        if len(dates) >= 2:
            span_days = (dates[-1] - dates[0]).days
            ppw = round(len(dates) / (span_days / 7), 2) if span_days > 0 else None
        else:
            ppw = None

        acc_cadence.append({
            "account": acc,
            "total_posts": len(items),
            "date_range": f"{dates[0].strftime('%Y-%m')}" + f"→{dates[-1].strftime('%Y-%m')}",
            "avg_gap_days": _avg(gaps),
            "min_gap_days": min(gaps) if gaps else None,
            "max_gap_days": max(gaps) if gaps else None,
            "posts_per_week": ppw,
            "avg_engagement": avg_eng,
        })

    # Sort by avg_engagement
    acc_cadence_sorted = sorted(acc_cadence, key=lambda x: -(x["avg_engagement"] or 0))

    # ── Cadence × engagement correlation ──
    # Bin accounts by posts_per_week
    ppw_bins = defaultdict(list)
    for acc in acc_cadence:
        ppw = acc.get("posts_per_week")
        avg = acc.get("avg_engagement")
        if ppw and avg:
            if ppw < 1:   bin_ = "under_1_per_week"
            elif ppw < 2: bin_ = "1_per_week"
            elif ppw < 4: bin_ = "2_3_per_week"
            elif ppw < 7: bin_ = "4_6_per_week"
            else:         bin_ = "daily_plus"
            ppw_bins[bin_].append(avg)

    cadence_vs_eng = []
    for bin_ in ["under_1_per_week","1_per_week","2_3_per_week","4_6_per_week","daily_plus"]:
        engs = ppw_bins.get(bin_,[])
        if engs:
            avg = _avg(engs)
            cadence_vs_eng.append({
                "cadence": bin_,
                "account_count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })

    # ── Occasion posting surge — how many posts per occasion? ──
    occasion_vol = Counter(item["occasion"] for item in dated if item["occasion"])
    occasion_eng = defaultdict(list)
    for item in dated:
        if item["occasion"]:
            occasion_eng[item["occasion"]].append(item["eng"])

    by_occasion_volume = []
    for occ, count in occasion_vol.most_common():
        engs = occasion_eng[occ]
        avg  = _avg(engs)
        by_occasion_volume.append({
            "occasion": occ,
            "post_count": count,
            "pct_of_dated": round(count/N_dated,3),
            "avg_engagement": avg,
            "lift_vs_corpus": _lift(avg, corpus_baseline),
        })

    # ── Year over year (if multi-year data) ──
    year_data = defaultdict(list)
    for item in dated:
        year_data[item["dt"].year].append(item["eng"])

    by_year = [
        {"year": yr, "count": len(engs), "avg_engagement": _avg(engs),
         "lift_vs_corpus": _lift(_avg(engs), corpus_baseline)}
        for yr, engs in sorted(year_data.items()) if len(engs) >= 5
    ]

    # ── Sector × cadence ──
    sector_dates = defaultdict(list)
    for item in dated:
        sector_dates[item["sector"]].append((item["dt"], item["eng"]))

    sector_cadence = []
    for sec, items in sector_dates.items():
        if not sec: continue
        items_sorted = sorted(items, key=lambda x: x[0])
        dates = [x[0] for x in items_sorted]
        engs  = [x[1] for x in items_sorted]
        span_days = (dates[-1] - dates[0]).days if len(dates) >= 2 else 0
        ppw = round(len(dates)/(span_days/7),2) if span_days > 0 else None
        sector_cadence.append({
            "sector": sec,
            "total_posts": len(items),
            "posts_per_week": ppw,
            "avg_engagement": _avg(engs),
        })

    # ── Consistency score: accounts that post most days win? ──
    # Find the optimal gap_days range
    gap_bucket_eng = defaultdict(list)
    for item in dated:
        acc = item["account"]
        acc_items = sorted(acc_dates.get(acc,[]), key=lambda x: x[0])
        dates_acc = [x[0] for x in acc_items]
        gaps = [(dates_acc[i+1]-dates_acc[i]).days for i in range(len(dates_acc)-1)]
        if gaps:
            ag = _avg(gaps)
            if ag is not None:
                bucket = "1_3_days" if ag <= 3 else "4_7_days" if ag <= 7 else "8_14_days" if ag <= 14 else "15_plus_days"
                gap_bucket_eng[bucket].append(item["eng"])

    gap_vs_eng = []
    for bucket in ["1_3_days","4_7_days","8_14_days","15_plus_days"]:
        engs = gap_bucket_eng.get(bucket,[])
        if engs:
            avg = _avg(engs)
            gap_vs_eng.append({
                "avg_gap_bucket": bucket,
                "obs_count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })

    out = {
        "meta": {
            "schema_version": 1,
            "total_obs": len(all_obs),
            "dated_obs": N_dated,
            "date_coverage_pct": round(N_dated/len(all_obs),3),
            "corpus_baseline": corpus_baseline,
        },
        "by_month":             by_month,
        "by_quarter":           by_quarter,
        "by_day_of_week":       by_dow_sorted,
        "by_year":              by_year,
        "by_occasion_volume":   by_occasion_volume,
        "cadence_vs_engagement":cadence_vs_eng,
        "gap_days_vs_engagement":gap_vs_eng,
        "sector_cadence":       sector_cadence,
        "account_cadence":      acc_cadence_sorted,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "posting_frequency_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    # ── Print summary ──
    W = 68
    print(f"\n{'═'*W}")
    print(f"  POSTING FREQUENCY ANALYSIS")
    print(f"  {N_dated} dated obs  ·  {round(N_dated/len(all_obs)*100)}% coverage")
    print(f"{'═'*W}\n")

    print(f"  DAY OF WEEK × ENGAGEMENT (best → worst)")
    for r in by_dow_sorted:
        bar = "█" * int(r["avg_engagement"] * 20)
        lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
        print(f"    {r['day']:<12}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}")

    if by_month:
        best_month = max(by_month, key=lambda x: x["avg_engagement"])
        worst_month= min(by_month, key=lambda x: x["avg_engagement"])
        print(f"\n  MONTHLY SEASONALITY")
        for r in by_month:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            flag = " ★" if r == best_month else " ⚠" if r == worst_month else ""
            print(f"    {r['month_name']:<6}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}{flag}")

    if by_quarter:
        print(f"\n  QUARTERLY TREND")
        for r in sorted(by_quarter, key=lambda x: -(x["avg_engagement"] or 0)):
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['quarter']}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}")

    if cadence_vs_eng:
        print(f"\n  POSTING CADENCE × ENGAGEMENT")
        for r in sorted(cadence_vs_eng, key=lambda x: -(x["avg_engagement"] or 0)):
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['cadence']:<22}  {r['avg_engagement']:.0%}  ({lift_str})  {r['account_count']} accounts")

    if gap_vs_eng:
        print(f"\n  GAP BETWEEN POSTS × ENGAGEMENT")
        for r in sorted(gap_vs_eng, key=lambda x: -(x["avg_engagement"] or 0)):
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['avg_gap_bucket']:<22}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['obs_count']}")

    print(f"\n  Output → logs/posting_frequency_analysis.json\n")


if __name__ == "__main__":
    main()
