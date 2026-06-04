#!/usr/bin/env python3
"""
reprocess_from_raw.py — Regenerate observations from raw Apify archive.

If we need to:
  - Add fields we didn't extract originally
  - Fix classification with a better model
  - Recalculate engagement from real metrics
  - Recover from data corruption

This script reads _raw_archive/ and rebuilds observations WITHOUT re-extracting.

Usage:
  python3 scripts/reprocess_from_raw.py --handle albaik --sector f_and_b
  python3 scripts/reprocess_from_raw.py --all
  python3 scripts/reprocess_from_raw.py --handle albaik --metrics-only  # just update metrics, keep AI classification
"""
import json, argparse, glob, os, sys, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
RAW_DIR = BASE / "11_who_to_learn_from" / "_raw_archive"
OBS_DIR = BASE / "11_who_to_learn_from" / "observations"

sys.path.insert(0, str(BASE / "scripts"))
from lib.engagement import calculate_engagement, tier_from_total


def load_raw_posts(handle: str) -> list[dict]:
    """Load all raw Apify posts for a handle from the archive."""
    handle_dir = RAW_DIR / handle
    if not handle_dir.exists():
        print(f"  No raw archive for @{handle}")
        return []

    posts = []
    for jsonl in sorted(handle_dir.glob("**/*_apify_raw.jsonl")):
        with open(jsonl) as f:
            for line in f:
                if line.strip():
                    posts.append(json.loads(line))

    print(f"  Loaded {len(posts)} raw posts from archive for @{handle}")
    return posts


def update_obs_metrics(handle: str, sector: str, raw_posts: list[dict]):
    """Update existing observations with real metrics from raw archive."""
    # Build lookup: shortcode → raw post
    raw_by_shortcode = {}
    for post in raw_posts:
        sc = post.get("shortCode") or post.get("shortcode") or ""
        if sc:
            raw_by_shortcode[sc] = post

    # Find existing obs for this handle
    updated = 0
    not_found = 0

    sector_folders = {
        "f_and_b": "f_and_b", "beauty_personal_care": "beauty",
        "retail_lifestyle": "retail", "fashion": "retail",
        "real_estate": "real_estate", "healthcare_wellness": "healthcare_wellness",
    }
    folder = sector_folders.get(sector, sector)

    for obs_path in sorted(OBS_DIR.glob(f"{folder}/*.json")):
        obs = json.loads(obs_path.read_text())

        # Check if this obs belongs to our handle
        obs_handle = obs.get("account_handle_normalized", "").lstrip("@")
        if obs_handle.lower() != handle.lower():
            continue

        # Find matching raw post by source_url shortcode
        source_url = obs.get("content_ref", {}).get("source_url", "")
        shortcode = ""
        if "/p/" in source_url:
            shortcode = source_url.split("/p/")[1].strip("/").split("/")[0]
        elif obs.get("content_ref", {}).get("filename", ""):
            shortcode = obs["content_ref"]["filename"].replace(".jpg", "").replace(".mp4", "")

        raw = raw_by_shortcode.get(shortcode)
        if not raw:
            not_found += 1
            continue

        # Extract real metrics
        likes = int(raw.get("likesCount") or raw.get("likes") or 0)
        comments = int(raw.get("commentsCount") or raw.get("comments") or 0)
        followers = int(raw.get("ownerFollowerCount") or raw.get("followersCount") or 0)

        # Calculate engagement
        eng = calculate_engagement(likes, comments, followers)

        # Update content_ref with real metrics
        cr = obs.get("content_ref", {})
        cr["likes_count"] = likes
        cr["comments_count"] = comments
        cr["engagement_total"] = likes + comments
        cr["followers_at_capture"] = followers
        cr["engagement_rate"] = eng["rate"]
        obs["content_ref"] = cr

        # Update engagement_potential from real metrics (not AI guess)
        obs["quality_assessment"]["engagement_potential"] = eng["tier"]
        obs["quality_assessment"]["engagement_method"] = eng["method"]

        # Update provenance
        obs["provenance"]["last_verified_at"] = datetime.now().isoformat()
        obs["provenance"]["metrics_source"] = "apify_raw_archive"

        # Save
        obs_path.write_text(json.dumps(obs, indent=2, ensure_ascii=False))
        updated += 1

    return updated, not_found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", help="Account handle to reprocess")
    parser.add_argument("--sector", help="Sector of the account")
    parser.add_argument("--all", action="store_true", help="Reprocess all handles in raw archive")
    parser.add_argument("--metrics-only", action="store_true", help="Only update metrics, keep AI classification")
    args = parser.parse_args()

    if args.all:
        handles = [d.name for d in RAW_DIR.iterdir() if d.is_dir()]
        if not handles:
            print("No raw archives found. Extract first with: python3 scripts/extract_account_obs.py")
            return
        print(f"Reprocessing {len(handles)} handles from raw archive...")
        total_updated = 0
        total_missing = 0
        for handle in sorted(handles):
            # Guess sector from existing obs
            sector = "f_and_b"  # default
            for obs_path in OBS_DIR.glob("*/*.json"):
                obs = json.loads(obs_path.read_text())
                if obs.get("account_handle_normalized", "").lstrip("@").lower() == handle.lower():
                    sector = obs.get("sector", "f_and_b")
                    break

            raw_posts = load_raw_posts(handle)
            if raw_posts:
                updated, missing = update_obs_metrics(handle, sector, raw_posts)
                total_updated += updated
                total_missing += missing
                print(f"  @{handle}: {updated} updated, {missing} not matched")

        print(f"\nTotal: {total_updated} obs updated, {total_missing} not matched")

    elif args.handle:
        if not args.sector:
            print("--sector required with --handle")
            return
        raw_posts = load_raw_posts(args.handle)
        if raw_posts:
            updated, missing = update_obs_metrics(args.handle, args.sector, raw_posts)
            print(f"\n✅ @{args.handle}: {updated} obs updated, {missing} not matched")
    else:
        print("Usage: --handle X --sector Y | --all")


if __name__ == "__main__":
    main()
