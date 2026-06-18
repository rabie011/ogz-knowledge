#!/usr/bin/env python3
"""CAMPAIGN DETECTION (June 18) — Mohamed's insight: the best agency doesn't post standalone posts,
it runs CAMPAIGNS (connected posts forming one arc). We modeled only the post-unit; this finds the
unit ABOVE it. Connective tissue = a recurring hashtag that marks a SUBSET of posts (a campaign),
not the always-on brand tag / tagline (on ~every post). Groups the connected posts into arcs with
their sequence, date span, and real engagement. Zero-key, deterministic.
Usage: python3 scripts/detect_campaigns.py --handle dunkindonutsksa
"""
import argparse, json, re
from collections import defaultdict
from datetime import datetime as dt
from pathlib import Path

B = Path(__file__).parent.parent
TAG = re.compile(r"#[\w؀-ۿ]+")


def detect(handle):
    f = next(B.glob(f"11_who_to_learn_from/_inbox/*{handle}*/*_full_extraction.json"), None) \
        or next(B.glob(f"11_who_to_learn_from/_inbox/@{handle}/*_full_extraction.json"), None)
    d = json.loads(f.read_text())
    posts = [p for p in d.get("posts", []) if p.get("date") or p.get("timestamp")]
    n = len(posts)
    # tag frequency → campaign tags are recurring (>=2) but NOT near-universal (brand/tagline >40%)
    freq = defaultdict(list)
    for p in posts:
        for t in set(TAG.findall(p.get("caption") or "")):
            freq[t].append(p)
    universal = {t for t, ps in freq.items() if len(ps) > 0.30 * n}   # brand tag + tagline (always-on)
    campaigns = []
    for t, ps in freq.items():
        if t in universal or len(ps) < 2:
            continue
        ps = sorted(ps, key=lambda p: str(p.get("date") or p.get("timestamp")))
        dates = [str(p.get("date") or p.get("timestamp"))[:10] for p in ps]
        span = (dt.fromisoformat(dates[-1]) - dt.fromisoformat(dates[0])).days
        likes = [p.get("likes", 0) for p in ps]
        campaigns.append({
            "campaign_tag": t, "posts": len(ps), "arc_days": span,
            "start": dates[0], "end": dates[-1],
            "avg_likes": round(sum(likes) / len(likes)),
            "n_videos": sum(1 for p in ps if p.get("is_video")),
            "shortcodes": [p.get("shortcode") for p in ps],
            "opener_caption": (ps[0].get("caption") or "")[:120],
        })
    campaigns.sort(key=lambda c: c["posts"], reverse=True)
    in_campaign = len({sc for c in campaigns for sc in c["shortcodes"]})
    out = {"handle": handle, "n_posts": n, "universal_tags": sorted(universal),
           "n_campaigns": len(campaigns), "posts_in_campaigns": in_campaign,
           "pct_campaign_driven": round(in_campaign / n * 100), "campaigns": campaigns}
    op = f.parent / "campaigns.json"
    op.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"  {n} posts → {len(campaigns)} campaigns · {in_campaign} posts ({out['pct_campaign_driven']}%) are campaign-driven")
    print(f"  always-on (brand/tagline): {', '.join(sorted(universal))}")
    for c in campaigns[:8]:
        print(f"   • {c['campaign_tag']:28} {c['posts']:>2} posts · {c['arc_days']:>3}d arc · {c['avg_likes']:>5} avg likes · {c['n_videos']} vids")
    print(f"  ✅ → {op.relative_to(B)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--handle", default="dunkindonutsksa")
    detect(ap.parse_args().handle)
