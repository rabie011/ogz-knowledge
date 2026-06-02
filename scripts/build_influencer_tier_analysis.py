#!/usr/bin/env python3
"""
build_influencer_tier_analysis.py
Analyse content performance by account follower tier (nano/micro/mid/macro/mega).
Answers: which tier produces the highest engagement? Which sectors benefit most
from micro vs macro accounts? What content pillars work best per tier?

Output: logs/influencer_tier_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS  = BASE / "11_who_to_learn_from" / "observations"
ACCS = BASE / "11_who_to_learn_from" / "accounts"
LOGS = BASE / "logs"

TIER_ORDER = ["nano", "micro", "mid", "macro", "mega"]

def main():
    # Build handle → follower_tier map from account profiles
    tier_map = {}
    for f in ACCS.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            h = d.get("instagram_handle","").lstrip("@") or d.get("handle","")
            t = d.get("follower_tier","")
            if h and t: tier_map[h] = t
        except: pass

    # Aggregate obs by tier
    stats = defaultdict(lambda: {
        "total": 0, "high": 0, "medium": 0, "low": 0,
        "by_sector": defaultdict(lambda: {"total":0,"high":0}),
        "by_pillar": defaultdict(lambda: {"total":0,"high":0}),
        "by_format": defaultdict(lambda: {"total":0,"high":0}),
        "by_emotion": defaultdict(lambda: {"total":0,"high":0}),
    })

    for f in OBS.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            handle = d.get("account_handle_normalized","")
            tier = tier_map.get(handle)
            if not tier: continue
            ep = d.get("quality_assessment",{}).get("engagement_potential","") or \
                 d.get("engagement_potential","")
            sector  = d.get("sector","unknown")
            pillar  = d.get("content_pillar","unknown") or "unknown"
            fmt     = d.get("content_ref",{}).get("content_type","unknown")
            emotion = d.get("emotion_primary","unknown") or "unknown"
            s = stats[tier]
            s["total"] += 1
            if ep == "high":
                s["high"] += 1
                s["by_sector"][sector]["high"] += 1
                s["by_pillar"][pillar]["high"] += 1
                s["by_format"][fmt]["high"] += 1
                s["by_emotion"][emotion]["high"] += 1
            elif ep == "medium": s["medium"] += 1
            elif ep == "low":    s["low"] += 1
            s["by_sector"][sector]["total"] += 1
            s["by_pillar"][pillar]["total"] += 1
            s["by_format"][fmt]["total"] += 1
            s["by_emotion"][emotion]["total"] += 1
        except: pass

    def top_n(bucket, n=5, min_total=5):
        return sorted(
            [{"value":k,"total":v["total"],
              "high_rate":round(v["high"]/v["total"],3) if v["total"]>0 else 0}
             for k,v in bucket.items() if v["total"]>=min_total],
            key=lambda x: -x["high_rate"])[:n]

    output = {"schema_version":1, "tiers":{}, "tier_comparison":[], "key_findings":[]}

    for tier in TIER_ORDER:
        if tier not in stats: continue
        s = stats[tier]
        total = s["total"]
        if total == 0: continue
        high_rate = round(s["high"]/total, 3)
        output["tiers"][tier] = {
            "total_obs": total,
            "high_engagement_rate": high_rate,
            "medium_engagement_rate": round(s["medium"]/total,3),
            "low_engagement_rate": round(s["low"]/total,3),
            "best_sectors": top_n(s["by_sector"]),
            "best_pillars": top_n(s["by_pillar"]),
            "best_formats": top_n(s["by_format"]),
            "best_emotions": top_n(s["by_emotion"]),
        }

    output["tier_comparison"] = sorted(
        [{"tier":tier,"total_obs":d["total_obs"],"high_rate":d["high_engagement_rate"]}
         for tier,d in output["tiers"].items()],
        key=lambda x:-x["high_rate"])

    # Key findings
    if output["tier_comparison"]:
        top = output["tier_comparison"][0]
        output["key_findings"].append(
            f"{top['tier'].upper()} tier has highest engagement rate ({top['high_rate']:.0%}) — n={top['total_obs']}")

    out = LOGS / "influencer_tier_analysis.json"
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Influencer tier analysis written: {out}")
    print("Tier comparison (high ER):")
    for row in output["tier_comparison"]:
        print(f"  {row['tier']:8} n={row['total_obs']:4}  high_rate={row['high_rate']:.1%}")

if __name__ == "__main__":
    main()
