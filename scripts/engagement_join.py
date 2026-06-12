#!/usr/bin/env python3
"""DATA RE-LAYERING — LAYER 3: REAL ENGAGEMENT JOIN (June 12 go-build).
The eyeballed engagement_potential enum carries no signal (measured: high/low tiers
differ by 0.5pp on every axis we care about) — RETIRED as authority. This joins
MEASURED likes/comments from Apify (instagram-post-scraper, the same actor the intake
already uses) onto the obs quality index.

MONEY DISCIPLINE (Mohamed's law): sample-first. --sample N (default 120) proves the
pipe + measures cost per post; the FULL run (~5.5k clean obs) only goes after the
sample's cost lands on a portal card for Mohamed's go.

Engagement enters the ranking as a TIE-BREAKER only (brainstorm ruling: laws >
Mohamed's taste > measured engagement > extractor opinion).

Output: data/engagement_join.json {ulid: {likes, comments, fetched}} + a cost line.
"""
import argparse
import glob
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def collect_urls(sample_n: int):
    B = base()
    qi = json.loads((B / "data/obs_quality_index.json").read_text())["index"]
    rows = []
    for f in glob.glob(str(B / "11_who_to_learn_from/observations/*/*.json")):
        try:
            o = json.loads(Path(f).read_text())
        except Exception:
            continue
        ulid = o.get("observation_ulid") or Path(f).stem
        if qi.get(ulid, {}).get("tier") != "clean":
            continue
        url = (o.get("content_ref") or {}).get("source_url") or ""
        if "instagram.com/p/" in url or "instagram.com/reel" in url:
            rows.append((ulid, url))
    random.seed(20260612)
    random.shuffle(rows)
    return rows[:sample_n], len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=120)
    a = ap.parse_args()
    B = base()
    out_f = B / "data/engagement_join.json"
    existing = json.loads(out_f.read_text()) if out_f.exists() else {"joined": {}}
    urls, total_clean = collect_urls(a.sample)
    urls = [(u, l) for u, l in urls if u not in existing["joined"]]
    print(f"clean obs with IG urls: {total_clean} · fetching sample: {len(urls)}")
    if not urls:
        print("nothing new to fetch")
        return
    from apify_client import ApifyClient
    client = ApifyClient(env("APIFY_TOKEN"))
    run = client.actor("apify/instagram-post-scraper").call(
        run_input={"directUrls": [u for _, u in urls], "resultsLimit": len(urls)})
    ds = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId", "")
    by_url = {}
    for item in client.dataset(ds).iterate_items():
        u = (item.get("url") or item.get("inputUrl") or "").rstrip("/")
        by_url[u] = {"likes": item.get("likesCount"), "comments": item.get("commentsCount"),
                     "video_views": item.get("videoViewCount"), "ts": item.get("timestamp")}
    hits = 0
    for ulid, u in urls:
        m = by_url.get(u.rstrip("/"))
        if m and m.get("likes") is not None:
            existing["joined"][ulid] = {**m, "fetched": now_iso()}
            hits += 1
    existing["generated"] = now_iso()
    existing["coverage_note"] = f"sample run: {hits}/{len(urls)} resolved"
    out_f.write_text(json.dumps(existing, ensure_ascii=False))
    # cost evidence (money discipline: numbers, not feelings)
    usage = run.get("usageTotalUsd") or run.get("usage", {}).get("TOTAL_USD") if isinstance(run.get("usage"), dict) else run.get("usageTotalUsd")
    print(f"resolved: {hits}/{len(urls)} · run usage USD: {usage} · "
          f"full-run estimate ({total_clean} posts): ~${(usage or 0) * total_clean / max(len(urls),1):.2f}")


if __name__ == "__main__":
    main()
