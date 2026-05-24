#!/usr/bin/env python3
"""
build_pattern_engagement.py
Cross 1507 pattern_matches × confidence × engagement × sector × occasion.
Which of the 127 creative patterns actually drive engagement in Saudi content?
Output: logs/pattern_engagement.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""), None)

def main():
    pattern_eng     = defaultdict(list)
    pattern_conf    = defaultdict(Counter)   # pattern → {strong/moderate/weak: count}
    sec_pattern     = defaultdict(lambda: defaultdict(list))
    occ_pattern     = defaultdict(lambda: defaultdict(list))
    pattern_count   = Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        sec = d.get("sector", "")
        occ = d.get("occasion", "") or "evergreen"

        for pm in d.get("pattern_matches", []):
            slug = pm.get("pattern_slug", "")
            conf = pm.get("confidence", "")
            if not slug: continue

            pattern_eng[slug].append(e)
            pattern_count[slug] += 1
            pattern_conf[slug][conf] += 1
            if sec: sec_pattern[sec][slug].append(e)
            if occ: occ_pattern[occ][slug].append(e)

    global_avg = sum(v for vals in pattern_eng.values() for v in vals) / max(
        sum(len(v) for v in pattern_eng.values()), 1)

    # Build per-pattern stats
    by_pattern = {}
    for slug, vals in pattern_eng.items():
        avg = round(sum(vals) / len(vals), 3)
        by_pattern[slug] = {
            "count":           len(vals),
            "avg_engagement":  avg,
            "lift_vs_avg":     round(avg - global_avg, 3),
            "high_rate":       round(sum(1 for v in vals if v >= 0.75) / len(vals), 3),
            "confidence_dist": dict(pattern_conf[slug]),
        }

    # Elite: ≥+0.10 lift, n ≥ 5
    elite = sorted(
        [{"pattern": k, **v} for k, v in by_pattern.items()
         if v["lift_vs_avg"] >= 0.10 and v["count"] >= 5],
        key=lambda x: -x["lift_vs_avg"]
    )

    # Avoid: ≤-0.10 lift, n ≥ 5
    avoid = sorted(
        [{"pattern": k, **v} for k, v in by_pattern.items()
         if v["lift_vs_avg"] <= -0.10 and v["count"] >= 5],
        key=lambda x: x["lift_vs_avg"]
    )

    # Best pattern per sector
    best_by_sector = {}
    for sec, patterns in sec_pattern.items():
        ranked = sorted(
            patterns.items(),
            key=lambda x: (sum(x[1]) / max(len(x[1]), 1), len(x[1])),
            reverse=True
        )
        best_by_sector[sec] = [
            {"pattern": k, "avg_engagement": round(sum(v)/len(v), 3), "n": len(v)}
            for k, v in ranked[:5] if len(v) >= 3
        ]

    # Best pattern per key occasion
    best_by_occasion = {}
    for occ, patterns in occ_pattern.items():
        total = sum(len(v) for v in patterns.values())
        if total < 5: continue
        ranked = sorted(
            patterns.items(),
            key=lambda x: sum(x[1]) / max(len(x[1]), 1),
            reverse=True
        )
        best_by_occasion[occ] = [
            {"pattern": k, "avg_engagement": round(sum(v)/len(v), 3), "n": len(v)}
            for k, v in ranked[:3] if len(v) >= 2
        ]

    # Full ranked list
    ranked_all = sorted(by_pattern.items(), key=lambda x: -x[1]["avg_engagement"])

    rules = []
    if elite:
        rules.append(f"Elite patterns: {', '.join(p['pattern'] for p in elite[:5])}")
    if avoid:
        rules.append(f"Avoid patterns: {', '.join(p['pattern'] for p in avoid[:3])}")

    out = {
        "total_pattern_instances": sum(pattern_count.values()),
        "unique_patterns":         len(by_pattern),
        "global_avg_engagement":   round(global_avg, 3),
        "elite_patterns":          elite,
        "avoid_patterns":          avoid,
        "all_patterns_ranked":     [
            {"pattern": k, **v} for k, v in ranked_all
        ],
        "best_by_sector":          best_by_sector,
        "best_by_occasion":        best_by_occasion,
        "agency_rules":            rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "pattern_engagement.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Pattern engagement — {len(by_pattern)} patterns, {sum(pattern_count.values())} instances")
    print(f"Global avg: {global_avg:.0%}\n")
    print(f"{'Pattern':<40} {'Eng':>5}  {'Lift':>6}  n")
    print("-" * 60)
    for item in out["all_patterns_ranked"][:20]:
        lift = f"+{item['lift_vs_avg']:.2f}" if item["lift_vs_avg"] >= 0 else f"{item['lift_vs_avg']:.2f}"
        print(f"  {item['pattern']:<38} {item['avg_engagement']:.0%}  {lift:>6}  {item['count']}")
    print(f"\n  ▸ Elite ({len(elite)}): {', '.join(p['pattern'] for p in elite[:6])}")
    print(f"  ▸ Avoid ({len(avoid)}): {', '.join(p['pattern'] for p in avoid[:3])}")
    print("  Output → logs/pattern_engagement.json")

if __name__ == "__main__":
    main()
