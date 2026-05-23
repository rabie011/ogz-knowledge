#!/usr/bin/env python3
"""
build_engagement_signals.py
Per-feature probability table: P(high_engagement | feature_value).
Output: logs/engagement_signal_table.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

ENG_MAP = {"high": 1, "very_high": 1, "above_average": 1, "medium": 0, "low": 0, "below_average": 0}

def verdict(rate, n):
    if n < 3:
        return "insufficient_data"
    if rate >= 0.80:
        return "strong_positive"
    if rate >= 0.60:
        return "positive"
    if rate >= 0.40:
        return "neutral"
    if rate >= 0.20:
        return "weak"
    return "avoid"

def main():
    signals = defaultdict(lambda: {"count": 0, "high_count": 0})

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        qa = data.get("quality_assessment", {})
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        is_high = ENG_MAP.get(eng_raw, -1)
        if is_high == -1:
            continue

        def track(key, val):
            if not val:
                return
            k = f"{key}::{str(val).lower().strip()}"
            signals[k]["count"] += 1
            signals[k]["high_count"] += is_high

        # Pattern signals
        for pm in data.get("pattern_matches", []):
            slug = pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
            if slug:
                track("pattern", slug)

        # Voice signals
        vo = data.get("voice_observations", {})
        track("dialect", vo.get("dialect_detected"))
        track("register", vo.get("register"))
        track("tone", vo.get("tone"))

        # Visual signals
        vv = data.get("visual_observations", {})
        track("setting", vv.get("setting"))
        track("media_type", (data.get("content_ref") or {}).get("content_type"))

        # Cultural signals
        cn = data.get("cultural_notes", {})
        track("occasion", cn.get("occasion_relevance"))
        track("heritage_vs_modern", cn.get("heritage_vs_modern"))
        hosp_count = len(cn.get("hospitality_cues", []) or [])
        if hosp_count == 0:
            track("hospitality_level", "none")
        elif hosp_count <= 2:
            track("hospitality_level", "low")
        elif hosp_count <= 4:
            track("hospitality_level", "medium")
        else:
            track("hospitality_level", "high")

        # Quality signals
        track("production_quality", qa.get("production_quality"))
        track("brand_consistency", qa.get("brand_consistency_with_account"))

        # Sector
        track("sector", data.get("sector"))

    # Build output table
    rows = []
    for key, data in signals.items():
        n = data["count"]
        h = data["high_count"]
        rate = round(h / n, 3) if n else 0
        signal_type, signal_value = key.split("::", 1)
        rows.append({
            "signal_type": signal_type,
            "signal_value": signal_value,
            "obs_count": n,
            "high_engagement_count": h,
            "high_engagement_rate": rate,
            "verdict": verdict(rate, n),
            "insight": f"{h}/{n} obs with high engagement ({int(rate*100)}%)"
        })

    # Sort: verdict priority, then rate, then count
    verdict_order = {"strong_positive": 0, "positive": 1, "neutral": 2, "weak": 3, "avoid": 4, "insufficient_data": 5}
    rows.sort(key=lambda x: (verdict_order.get(x["verdict"], 5), -x["high_engagement_rate"], -x["obs_count"]))

    # Summary groupings
    by_type = defaultdict(list)
    for r in rows:
        if r["verdict"] != "insufficient_data":
            by_type[r["signal_type"]].append(r)

    top_positive = [r for r in rows if r["verdict"] in ("strong_positive", "positive") and r["obs_count"] >= 3]
    to_avoid = [r for r in rows if r["verdict"] == "avoid" and r["obs_count"] >= 3]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "how_to_read": "high_engagement_rate = fraction of obs with this feature that scored high engagement. verdict: strong_positive (80%+), positive (60-80%), neutral (40-60%), weak (20-40%), avoid (<20%). Min 3 obs required for verdict.",
        "signal_types_covered": list(by_type.keys()),
        "top_positive_signals": top_positive[:20],
        "signals_to_avoid": to_avoid[:10],
        "all_signals": rows
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "engagement_signal_table.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Total signals analysed: {len(rows)}")
    print(f"Strong positive: {len([r for r in rows if r['verdict'] == 'strong_positive'])}")
    print(f"To avoid: {len([r for r in rows if r['verdict'] == 'avoid'])}")
    print(f"\nTop 10 strongest engagement signals:")
    for r in top_positive[:10]:
        print(f"  [{r['signal_type']}] {r['signal_value']}: {r['high_engagement_rate']*100:.0f}% high eng (n={r['obs_count']}) — {r['verdict']}")
    print(f"\nSignals to avoid:")
    for r in to_avoid[:5]:
        print(f"  [{r['signal_type']}] {r['signal_value']}: {r['high_engagement_rate']*100:.0f}% high eng (n={r['obs_count']})")
    print(f"\nOutput: logs/engagement_signal_table.json")

if __name__ == "__main__":
    main()
