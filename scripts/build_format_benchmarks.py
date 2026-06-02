#!/usr/bin/env python3
"""
build_format_benchmarks.py
Format-segmented engagement benchmarks — separates image/video/carousel/reel.
Pooling all formats produces misleading averages (Reels avg 1.23% ER vs images 0.70%).

Output: logs/format_benchmarks.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS  = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

FORMAT_ALIASES = {
    "image":          "image",
    "carousel_slide": "carousel",
    "video":          "video",
    "reel":           "reel",
}

def main():
    stats = defaultdict(lambda: {
        "total": 0, "high_eng": 0, "medium_eng": 0, "low_eng": 0,
        "by_sector": defaultdict(lambda: {"total":0,"high":0}),
        "by_occasion": defaultdict(lambda: {"total":0,"high":0}),
        "by_emotion": defaultdict(lambda: {"total":0,"high":0}),
        "by_pillar": defaultdict(lambda: {"total":0,"high":0}),
        "by_dow": defaultdict(lambda: {"total":0,"high":0}),
    })

    for f in OBS.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            ct = d.get("content_ref",{}).get("content_type","")
            fmt = FORMAT_ALIASES.get(ct)
            if not fmt: continue
            ep = d.get("quality_assessment",{}).get("engagement_potential","") or \
                 d.get("engagement_potential","")
            sector  = d.get("sector","unknown")
            occasion = d.get("occasion","") or "evergreen"
            emotion = d.get("emotion_primary","") or "unknown"
            pillar  = d.get("content_pillar","") or "unknown"
            dow     = d.get("content_ref",{}).get("day_of_week","") or "unknown"

            s = stats[fmt]
            s["total"] += 1
            if ep == "high":
                s["high_eng"] += 1
                s["by_sector"][sector]["high"] += 1
                s["by_occasion"][occasion]["high"] += 1
                s["by_emotion"][emotion]["high"] += 1
                s["by_pillar"][pillar]["high"] += 1
                s["by_dow"][dow]["high"] += 1
            elif ep == "medium": s["medium_eng"] += 1
            elif ep == "low":    s["low_eng"] += 1

            s["by_sector"][sector]["total"] += 1
            s["by_occasion"][occasion]["total"] += 1
            s["by_emotion"][emotion]["total"] += 1
            s["by_pillar"][pillar]["total"] += 1
            s["by_dow"][dow]["total"] += 1
        except: pass

    # Build output with engagement rates per format
    output = {"schema_version": 1, "formats": {}, "cross_format_comparison": []}

    for fmt, s in sorted(stats.items()):
        total = s["total"]
        if total == 0: continue
        high_rate = round(s["high_eng"] / total, 3)

        def top_n(bucket, n=5, min_total=5):
            return sorted(
                [{"value": k, "total": v["total"],
                  "high_rate": round(v["high"]/v["total"],3) if v["total"]>0 else 0}
                 for k,v in bucket.items() if v["total"] >= min_total],
                key=lambda x: -x["high_rate"]
            )[:n]

        output["formats"][fmt] = {
            "total_obs": total,
            "high_engagement_rate": high_rate,
            "medium_engagement_rate": round(s["medium_eng"]/total, 3),
            "low_engagement_rate": round(s["low_eng"]/total, 3),
            "best_sectors":   top_n(s["by_sector"]),
            "best_occasions": top_n(s["by_occasion"]),
            "best_emotions":  top_n(s["by_emotion"]),
            "best_pillars":   top_n(s["by_pillar"]),
            "best_posting_days": top_n(s["by_dow"]),
        }

    # Cross-format comparison
    output["cross_format_comparison"] = sorted(
        [{"format": fmt, "total_obs": d["total_obs"],
          "high_engagement_rate": d["high_engagement_rate"]}
         for fmt, d in output["formats"].items()],
        key=lambda x: -x["high_engagement_rate"]
    )

    output["note"] = "Engagement rates segmented by content format. Never compare across formats — Reels, images, and carousels have different baseline rates and should be benchmarked separately."

    out_path = LOGS / "format_benchmarks.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Format benchmarks written: {out_path}")
    print("Cross-format ER comparison:")
    for row in output["cross_format_comparison"]:
        print(f"  {row['format']:15} n={row['total_obs']:4}  high_rate={row['high_engagement_rate']:.1%}")

if __name__ == "__main__":
    main()
