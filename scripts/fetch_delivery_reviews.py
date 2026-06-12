#!/usr/bin/env python3
"""MAPS-FIRST REVIEW FETCHER (B163, June 12 — FLANK-05).
B162 ruled: no official delivery-app review APIs; Google Maps reviews via Apify
are the clean path (credits on hand, ToS-clean). Reviews land in
clients/{handle}/raw/maps_reviews/ as raw surface — the audience mirror reads
the customer's UNPROMPTED voice (complaints the comments section never sees).
Money law: --cap reviews per run (default 50), measured numbers printed.

Usage: python3 scripts/fetch_delivery_reviews.py --handle albaik --query "البيك الرياض" [--cap 50]
"""
import argparse, datetime, json, os
from pathlib import Path

BASE = Path(__file__).parent.parent


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--cap", type=int, default=50)
    a = ap.parse_args()
    from apify_client import ApifyClient
    client = ApifyClient(env("APIFY_TOKEN"))
    print(f"fetching ≤{a.cap} Maps reviews for «{a.query}» …", flush=True)
    run = client.actor("compass/google-maps-reviews-scraper").call(run_input={
        "searchStringsArray": [a.query],
        "maxReviews": a.cap,
        "language": "ar",
        "reviewsSort": "newest",
    })
    ds_id = getattr(run, "default_dataset_id", None) or (run.get("defaultDatasetId") if isinstance(run, dict) else None)
    items = list(client.dataset(ds_id).iterate_items())
    out = BASE / "clients" / a.handle / "raw/maps_reviews" / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "reviews.jsonl", "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    texts = [it.get("text") or it.get("reviewText") or "" for it in items]
    usable = sum(1 for t in texts if t.strip())
    stars = [it.get("stars") or it.get("rating") for it in items if it.get("stars") or it.get("rating")]
    avg = sum(stars) / len(stars) if stars else 0
    print(f"MEASURED: {len(items)} reviews · {usable} with text · avg {avg:.1f}★ "
          f"→ {out}/reviews.jsonl")
    # honest provenance note in the manifest
    mf = BASE / "clients" / a.handle / "manifest.json"
    if mf.exists():
        m = json.loads(mf.read_text())
        m.setdefault("surfaces_extra", {})["maps_reviews"] = {
            "fetched": len(items), "usable_text": usable, "avg_stars": round(avg, 1),
            "date": datetime.date.today().isoformat(), "query": a.query}
        mf.write_text(json.dumps(m, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
