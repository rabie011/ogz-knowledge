#!/usr/bin/env python3
"""
build_video_pace_analysis.py
Analyse editing pace × engagement for Saudi social content.

Agency questions answered:
  - viral_fast vs fast vs medium vs slow × engagement lift
  - Editing pace × sector (F&B uses different pace than beauty)
  - Editing pace × occasion (Ramadan reels vs product launches)
  - Optimal cuts per second by sector
  - Do fast cuts always win? Or does slow = luxury signal?
  - Cut count × video duration × engagement

Output: logs/video_pace_analysis.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75,
    "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}

VIDEO_TYPES = {"video", "reel"}

SECTOR_KEY_MAP = {
    "food_and_beverage": "f_and_b",
    "beauty_personal_care": "beauty",
    "retail_lifestyle": "retail",
}


def _eng(obs) -> float | None:
    # Primary: quality_assessment.engagement_potential (all 648 obs use this)
    qa = obs.get("quality_assessment") or {}
    el = qa.get("engagement_potential")
    if not el:
        el = obs.get("engagement_level") or obs.get("engagement_estimate")
    if not el:
        voice = obs.get("voice_observations") or {}
        el = voice.get("engagement_level")
    if not el:
        return None
    return ENG_MAP.get(str(el).lower())


def _acc(bucket: dict, eng: float):
    bucket["count"] += 1
    bucket["sum"] += eng
    if eng >= 0.75:
        bucket["high"] += 1


def _rate(bucket: dict) -> float | None:
    if bucket["count"] == 0:
        return None
    return round(bucket["sum"] / bucket["count"], 3)


def _lift(rate: float | None, baseline: float) -> float | None:
    if rate is None:
        return None
    return round(rate - baseline, 3)


def main():
    # ── load all video obs with editing_pace filled ────────────────────
    by_pace          = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_pace_sector   = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0}))
    by_pace_occasion = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0}))
    by_cps_bucket    = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})

    total_video  = 0
    pace_filled  = 0
    all_engs     = []
    per_sector_engs = defaultdict(list)

    obs_details = []   # for detailed output

    for f in sorted(OBS_ROOT.rglob("*.json")):
        d = json.loads(f.read_text())
        cr  = d.get("content_ref") or {}
        ct  = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue
        total_video += 1

        eng = _eng(d)
        if eng is None:
            continue

        raw_sector = str(d.get("sector") or "").lower()
        sector_key = SECTOR_KEY_MAP.get(raw_sector, raw_sector)
        occasion   = str(d.get("occasion") or "evergreen").lower()
        pace       = cr.get("editing_pace")
        cut_count  = cr.get("cut_count")
        duration   = cr.get("video_duration_seconds")

        all_engs.append(eng)
        per_sector_engs[sector_key].append(eng)

        if not pace:
            continue
        pace_filled += 1

        _acc(by_pace[pace], eng)
        _acc(by_pace_sector[sector_key][pace], eng)
        _acc(by_pace_occasion[occasion][pace], eng)

        # cuts-per-second bucket
        if cut_count is not None and duration and duration > 0:
            cps = cut_count / duration
            if cps >= 4:    cps_b = "4plus_cps"
            elif cps >= 2:  cps_b = "2_4_cps"
            elif cps >= 1:  cps_b = "1_2_cps"
            elif cps >= 0.3: cps_b = "0.3_1_cps"
            else:           cps_b = "under_0.3_cps"
            _acc(by_cps_bucket[cps_b], eng)

        obs_details.append({
            "account": d.get("account_handle", ""),
            "sector":  sector_key,
            "occasion": occasion,
            "editing_pace": pace,
            "cut_count": cut_count,
            "duration_s": duration,
            "engagement": eng,
        })

    # ── corpus & sector baselines ─────────────────────────────────────
    corpus_baseline = round(sum(all_engs) / len(all_engs), 3) if all_engs else 0.54
    sector_baselines = {
        k: round(sum(v) / len(v), 3) for k, v in per_sector_engs.items() if v
    }

    # ── pace table ───────────────────────────────────────────────────
    pace_table = {}
    for pace, b in sorted(by_pace.items()):
        r = _rate(b)
        pace_table[pace] = {
            "count": b["count"],
            "avg_engagement": r,
            "high_eng_pct": round(b["high"] / b["count"] * 100, 1) if b["count"] else 0,
            "lift_vs_corpus": _lift(r, corpus_baseline),
        }

    # best pace overall
    best_pace = max(
        ((p, v["avg_engagement"]) for p, v in pace_table.items() if v["avg_engagement"] is not None),
        key=lambda x: x[1], default=(None, None)
    )

    # ── pace × sector ─────────────────────────────────────────────────
    pace_by_sector = {}
    for sector, paces in sorted(by_pace_sector.items()):
        baseline = sector_baselines.get(sector, corpus_baseline)
        pace_by_sector[sector] = {
            "baseline": baseline,
            "paces": {},
        }
        best = None
        best_eng = -1
        for pace, b in sorted(paces.items()):
            r = _rate(b)
            pace_by_sector[sector]["paces"][pace] = {
                "count": b["count"],
                "avg_engagement": r,
                "lift_vs_sector_baseline": _lift(r, baseline),
            }
            if r is not None and r > best_eng:
                best_eng = r
                best = pace
        pace_by_sector[sector]["best_pace"] = best

    # ── pace × occasion ──────────────────────────────────────────────
    pace_by_occasion = {}
    for occ, paces in sorted(by_pace_occasion.items()):
        pace_by_occasion[occ] = {}
        for pace, b in sorted(paces.items()):
            r = _rate(b)
            pace_by_occasion[occ][pace] = {
                "count": b["count"],
                "avg_engagement": r,
                "lift_vs_corpus": _lift(r, corpus_baseline),
            }

    # ── cuts-per-second bucket ────────────────────────────────────────
    cps_table = {}
    for cps_b, b in sorted(by_cps_bucket.items()):
        r = _rate(b)
        cps_table[cps_b] = {
            "count": b["count"],
            "avg_engagement": r,
            "lift_vs_corpus": _lift(r, corpus_baseline),
        }

    # ── cross-sector signals ──────────────────────────────────────────
    cross_sector_signals = []
    for pace in ["viral_fast", "fast", "medium", "slow"]:
        sectors_positive = []
        for sector, data in pace_by_sector.items():
            lift = (data["paces"].get(pace) or {}).get("lift_vs_sector_baseline")
            if lift is not None and lift > 0.05:
                sectors_positive.append(sector)
        if len(sectors_positive) >= 2:
            corpus_lift = (pace_table.get(pace) or {}).get("lift_vs_corpus")
            cross_sector_signals.append({
                "pace": pace,
                "positive_in_sectors": sectors_positive,
                "corpus_lift": corpus_lift,
            })

    # ── load global pace log (all 869 videos) ────────────────────────
    global_log = {}
    pace_log_path = LOGS / "editing_pace_analysis.json"
    if pace_log_path.exists():
        raw = json.loads(pace_log_path.read_text())
        results = raw.get("results", [])
        dist = Counter(r["editing_pace"] for r in results)
        total_results = len(results)
        global_log = {
            "total_videos_analysed": total_results,
            "pace_distribution": dict(dist),
            "pace_pct": {
                k: round(v / total_results * 100, 1)
                for k, v in dist.items()
            },
            "avg_cut_count": round(sum(r["cut_count"] for r in results) / total_results, 1) if results else 0,
            "avg_duration_s": round(sum(r["duration_s"] for r in results) / total_results, 1) if results else 0,
        }

    # ── agency summary ────────────────────────────────────────────────
    agency_summary = {
        "q_does_viral_fast_win": None,
        "q_slow_means_luxury": None,
        "q_best_pace_overall": best_pace[0],
        "key_insight": "",
    }
    if "viral_fast" in pace_table and "slow" in pace_table:
        vf_eng = pace_table["viral_fast"]["avg_engagement"]
        sl_eng = pace_table["slow"]["avg_engagement"]
        if vf_eng is not None and sl_eng is not None:
            agency_summary["q_does_viral_fast_win"] = vf_eng > sl_eng
            agency_summary["q_slow_means_luxury"] = sl_eng > corpus_baseline

    if best_pace[0]:
        lift_pp = round((best_pace[1] - corpus_baseline) * 100, 1)
        agency_summary["key_insight"] = (
            f"'{best_pace[0]}' editing pace averages highest engagement "
            f"({best_pace[1]:.2f} vs {corpus_baseline:.2f} baseline, +{lift_pp}pp lift)"
        )

    # ── output ────────────────────────────────────────────────────────
    out = {
        "meta": {
            "total_video_obs": total_video,
            "obs_with_pace": pace_filled,
            "pace_coverage_pct": round(pace_filled / total_video * 100, 1) if total_video else 0,
            "corpus_baseline": corpus_baseline,
            "sector_baselines": sector_baselines,
        },
        "pace_table": pace_table,
        "best_pace_overall": best_pace[0],
        "pace_by_sector": pace_by_sector,
        "pace_by_occasion": pace_by_occasion,
        "cuts_per_second_table": cps_table,
        "cross_sector_signals": cross_sector_signals,
        "global_video_stats": global_log,
        "agency_summary": agency_summary,
    }

    LOGS.mkdir(exist_ok=True)
    out_path = LOGS / "video_pace_analysis.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print("=" * 55)
    print("VIDEO PACE ANALYSIS COMPLETE")
    print(f"  Video obs total  : {total_video}")
    print(f"  Obs with pace    : {pace_filled}  ({out['meta']['pace_coverage_pct']}%)")
    print(f"  Corpus baseline  : {corpus_baseline:.2f}")
    print()
    print("  Pace table:")
    for pace, v in sorted(pace_table.items(), key=lambda x: -(x[1]["avg_engagement"] or 0)):
        lift = v["lift_vs_corpus"]
        sign = "+" if lift and lift > 0 else ""
        print(f"    {pace:<15} n={v['count']:<4}  eng={v['avg_engagement'] or 'n/a':<6}  lift={sign}{lift}")
    print()
    if cross_sector_signals:
        print("  Cross-sector signals:")
        for s in cross_sector_signals:
            print(f"    {s['pace']}: positive in {', '.join(s['positive_in_sectors'])}")
    print()
    print(f"  Key insight: {agency_summary['key_insight']}")
    print(f"  Output → logs/video_pace_analysis.json")


if __name__ == "__main__":
    main()
