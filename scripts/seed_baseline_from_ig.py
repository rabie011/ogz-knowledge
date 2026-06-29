#!/usr/bin/env python3
"""seed_baseline_from_ig — warm perf_ingestor's COLD baseline from the brand's historical IG engagement.

DeepSeek's #1 bottleneck (June 29): the learning loop has 0 events while we already hold the brands' real
IG engagement (521 albaik posts, top 18k likes) — extracted but never fed back. This seeds it. Instagram
ONLY (Mohamed's scope). Each historical post → one baseline outcome_event so perf_ingestor._brand_history
has a real mean/std to z-score OUR produced posts against. Engagement-per-follower (likes + 3·comments) /
followers — consistent across image+video (we lack saves/shares/reach in the scrape). Marked _historical_seed
+ paid_boost flagged so a viral video doesn't corrupt the organic mean. Idempotent: clears prior seeds first.

  python3 scripts/seed_baseline_from_ig.py            # seed all 3 clients
"""
import glob
import json
import time
from pathlib import Path

B = Path(__file__).parent.parent
OUT = B / "data" / "outcome_events.jsonl"
BOOST_MULT = 5.0   # a post with >5× the median engagement = viral/boosted → flag, keep out of the mean


def _followers(handle):
    profs = sorted(glob.glob(f"{B}/clients/{handle}/raw/instagram/*/profile.json"))
    if not profs:
        return 0
    p = json.loads(Path(profs[-1]).read_text())
    return p.get("followersCount") or p.get("followers") or 0


def seed(handle):
    posts = sorted(glob.glob(f"{B}/clients/{handle}/raw/instagram/*/posts.jsonl"))
    if not posts:
        return 0
    followers = max(_followers(handle), 1)
    rows = [json.loads(l) for l in open(posts[-1]) if l.strip()]
    recs = []
    for i, r in enumerate(rows):
        likes = r.get("likesCount") or 0
        comments = r.get("commentsCount") or 0
        if not (likes or comments):
            continue
        er = (likes + 3 * comments) / followers
        recs.append({"likes": likes, "comments": comments, "er": er,
                     "post_id": f"{handle}__historical__{r.get('shortCode') or i}",
                     "caption": (r.get("caption") or "")[:200]})
    if not recs:
        return 0
    median = sorted(x["er"] for x in recs)[len(recs) // 2]
    out = []
    for x in recs:
        out.append({"ts": round(time.time(), 2), "brand": handle,
                    "engagement_rate": round(x["er"], 6),
                    "paid_boost": x["er"] > BOOST_MULT * median,
                    "_historical_seed": True, "likes": x["likes"], "comments": x["comments"],
                    "post_id": x["post_id"], "caption": x["caption"]})
    return out


def main():
    # idempotent: drop any prior _historical_seed rows, keep real produced events
    existing = []
    if OUT.exists():
        existing = [json.loads(l) for l in OUT.read_text().splitlines()
                    if l.strip() and not json.loads(l).get("_historical_seed")]
    seeded = []
    for h in ("albaik", "eatjurisha", "myfitness.sa"):
        rows = seed(h)
        if rows:
            seeded += rows
            org = sum(1 for r in rows if not r["paid_boost"])
            print(f"  {h}: seeded {len(rows)} baseline posts ({org} organic, {len(rows)-org} boosted-flagged)")
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in existing + seeded) + "\n")
    print(f"✅ learning loop warmed: {len(seeded)} historical events + {len(existing)} real events")


if __name__ == "__main__":
    main()
