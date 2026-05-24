#!/usr/bin/env python3
"""
build_master_signal_table.py
Consolidate EVERY signal we've ever measured into one ranked reference table.
Shows: dimension | value | avg_engagement | lift | n | confidence

The OGZ intelligence cheat sheet — every variable ranked by impact.
Output: logs/master_signal_table.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _conf(n):
    if n >= 50: return "high"
    if n >= 15: return "medium"
    if n >= 5:  return "low"
    return "very_low"

def main():
    obs_files = list(OBS_ROOT.rglob("*.json"))

    # Collect every (dimension, value) → engagement list
    dim_eng = defaultdict(list)

    for f in obs_files:
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        cr  = d.get("content_ref", {})
        vis = d.get("visual_observations", {})
        vo  = d.get("voice_observations", {})
        cn  = d.get("cultural_notes", {})
        qa  = d.get("quality_assessment", {})
        cp  = vis.get("color_palette") or {}

        def _add(dim, val):
            if val and str(val).strip() and str(val).strip().lower() not in ["none","null","—",""]:
                dim_eng[(dim, str(val).strip())].append(e)

        # Content ref
        _add("content_type",        cr.get("content_type"))
        _add("platform",            cr.get("platform"))
        _add("aspect_ratio",        cr.get("aspect_ratio"))
        _add("editing_pace",        cr.get("editing_pace"))
        _add("day_of_week",         cr.get("day_of_week"))

        # Video duration bucket
        vd = cr.get("video_duration_seconds")
        if vd is not None:
            b = "<15s" if vd<15 else "15-30s" if vd<30 else "30-60s" if vd<60 else "60-120s" if vd<120 else "120s+"
            _add("video_duration", b)

        # Visual
        _add("composition_style",   vis.get("composition_style"))
        _add("setting",             vis.get("setting"))
        _add("lighting",            vis.get("lighting"))
        _add("visual_complexity",   vis.get("visual_complexity"))
        _add("human_presence",      vis.get("human_presence"))

        # Color
        _add("color_warmth",        cp.get("warmth"))
        _add("color_primary",       cp.get("primary_family"))
        _add("color_palette_type",  cp.get("palette_type"))

        # Characters
        cv = vis.get("characters_visible") or {}
        count = cv.get("count")
        if count is not None:
            _add("character_count", "0" if count==0 else "1" if count==1 else "2-3" if count<=3 else "4+")
        _add("gender_presentation",  cv.get("gender_presentation","")[:20] if cv.get("gender_presentation") else None)

        # Voice / caption
        _add("voice_language",       vo.get("language"))
        _add("dialect",              vo.get("dialect_detected"))
        _add("register",             vo.get("register","")[:30] if vo.get("register") else None)
        _add("tone",                 vo.get("tone","")[:30] if vo.get("tone") else None)
        _add("cta_present",          vo.get("call_to_action_present"))
        _add("caption_sentiment",    vo.get("caption_sentiment"))
        _add("opener_formula",       vo.get("opener_formula"))
        _add("has_emoji",            vo.get("has_emoji"))

        # Caption length bucket
        wc = vo.get("caption_word_count")
        if wc is not None:
            _add("caption_length", "<10w" if wc<10 else "10-30w" if wc<30 else "30-60w" if wc<60 else "60w+")

        # Hashtag bucket
        hc = vo.get("hashtag_count")
        if hc is not None:
            _add("hashtag_count", "0" if hc==0 else "1-5" if hc<=5 else "6-15" if hc<=15 else "16+")

        # Cultural
        _add("heritage_vs_modern",   cn.get("heritage_vs_modern"))
        _add("sector",               d.get("sector"))
        _add("occasion",             d.get("occasion") or "evergreen")

        # Quality
        _add("production_quality",   qa.get("production_quality"))
        _add("brand_consistency",    qa.get("brand_consistency_with_account"))

    # Compute global baseline
    all_vals = [v for vals in dim_eng.values() for v in vals]
    global_avg = _avg(all_vals) or 0.65

    # Build signal table
    signals = []
    for (dim, val), vals in dim_eng.items():
        avg  = _avg(vals) or 0
        lift = round(avg - global_avg, 3)
        signals.append({
            "dimension":   dim,
            "value":       val,
            "count":       len(vals),
            "avg_engagement": avg,
            "lift_vs_avg": lift,
            "high_rate":   round(sum(1 for v in vals if v >= 0.75) / len(vals), 3),
            "confidence":  _conf(len(vals)),
        })

    # Sort by absolute lift × confidence weight
    CONF_W = {"high":1.0,"medium":0.8,"low":0.6,"very_low":0.3}
    signals.sort(key=lambda x: abs(x["lift_vs_avg"]) * CONF_W.get(x["confidence"],0.3), reverse=True)

    # Top boosters (lift ≥ +0.10, n ≥ 5)
    boosters = [s for s in signals if s["lift_vs_avg"] >= 0.10 and s["count"] >= 5]
    boosters.sort(key=lambda x: -x["lift_vs_avg"])

    # Top killers (lift ≤ -0.10, n ≥ 5)
    killers = [s for s in signals if s["lift_vs_avg"] <= -0.10 and s["count"] >= 5]
    killers.sort(key=lambda x: x["lift_vs_avg"])

    # Group by dimension
    by_dim = defaultdict(list)
    for s in signals:
        by_dim[s["dimension"]].append(s)

    # Dimension-level summary: best value, avg lift range
    dim_summary = {}
    for dim, rows in sorted(by_dim.items()):
        if not rows: continue
        best  = max(rows, key=lambda x: x["avg_engagement"])
        worst = min(rows, key=lambda x: x["avg_engagement"])
        spread = round(best["avg_engagement"] - worst["avg_engagement"], 3)
        dim_summary[dim] = {
            "best_value":     best["value"],
            "best_eng":       best["avg_engagement"],
            "worst_value":    worst["value"],
            "worst_eng":      worst["avg_engagement"],
            "spread":         spread,
            "n_values":       len(rows),
        }

    # Top dimensions by spread (most impactful to get right)
    top_dims = sorted(dim_summary.items(), key=lambda x: -x[1]["spread"])

    out = {
        "generated_at":   __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_obs":      len(obs_files),
        "global_avg":     round(global_avg, 3),
        "total_signals":  len(signals),
        "top_boosters":   boosters[:30],
        "top_killers":    killers[:20],
        "by_dimension":   {dim: rows for dim, rows in by_dim.items()},
        "dimension_summary": dict(top_dims),
        "top_dimensions_by_impact": [
            {"dimension": dim, **data} for dim, data in top_dims[:20]
        ],
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "master_signal_table.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Master signal table — {len(signals)} signals across {len(by_dim)} dimensions\n")
    print(f"Global baseline: {global_avg:.0%}\n")
    print(f"{'Dimension':<22} {'Best value':<28} {'Eng':>4}  {'Spread':>6}")
    print("─" * 68)
    for dim, data in top_dims[:20]:
        print(f"  {dim:<20}  {data['best_value']:<26}  {data['best_eng']:.0%}  ±{data['spread']:.2f}")
    print(f"\nTop 15 boosters (lift ≥ +10%, n≥5):")
    for s in boosters[:15]:
        print(f"  {s['dimension']:<22}  {s['value']:<25}  {s['avg_engagement']:.0%}  +{s['lift_vs_avg']:.2f}  n={s['count']}")
    print(f"\nTop 10 killers (lift ≤ -10%, n≥5):")
    for s in killers[:10]:
        print(f"  {s['dimension']:<22}  {s['value']:<25}  {s['avg_engagement']:.0%}  {s['lift_vs_avg']:.2f}  n={s['count']}")
    print(f"\n  Output → logs/master_signal_table.json")

if __name__ == "__main__":
    main()
