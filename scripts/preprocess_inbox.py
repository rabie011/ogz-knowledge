#!/usr/bin/env python3
"""
Phase 0: Preprocess raw Instagram extractions into working structure.

For each pilot account:
  1. Read _inbox/@{handle}/{handle}_full_extraction.json
  2. Select 25 posts (top 15 engagement + 5 recent + 5 random)
  3. Map media files on disk to selected posts
  4. Write extraction_queue.json, captions.txt, account_summary.json

Usage:
  python3 scripts/preprocess_inbox.py
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = REPO_ROOT / "11_who_to_learn_from" / "_inbox"

PILOT_ACCOUNTS = ["barnscoffee", "aseeb.najd", "riyadhfood", "altazaj_fakieh"]

ACCOUNT_REFS = {
    "barnscoffee": {
        "normalized": "OGZ-F-AND-B-Reference-002",
        "ulid": "01KRKHS8R8SNJ8VJ56WKSQTS28",
    },
    "aseeb.najd": {
        "normalized": "OGZ-F-AND-B-Reference-010",
        "ulid": "01KRKHS8R9HB73WWWGKXVDMC3A",
    },
    "riyadhfood": {
        "normalized": "OGZ-F-AND-B-Reference-004",
        "ulid": "01KRKHS8R8SNJ8VJ56WKSQTS2E",
    },
    "altazaj_fakieh": {
        "normalized": "OGZ-F-AND-B-Reference-005",
        "ulid": "01KRKHS8R8SNJ8VJ56WKSQTS2H",
    },
}

SAMPLE_SIZE = 25
TOP_ENGAGEMENT = 15
RECENT = 5
RANDOM_FILL = 5


def find_media_files(media_dir: Path, shortcode: str) -> list[str]:
    """Find all media files on disk matching a shortcode."""
    if not media_dir.exists():
        return []
    matches = []
    for f in media_dir.iterdir():
        if f.stem == shortcode or f.stem.startswith(shortcode + "_"):
            matches.append(f.name)
    return sorted(matches)


def select_posts(posts: list[dict], n: int = SAMPLE_SIZE) -> list[dict]:
    """Select n posts: top by engagement + most recent + random fill."""
    if len(posts) <= n:
        return posts

    selected_codes = set()
    selected = []

    by_engagement = sorted(
        posts, key=lambda p: p.get("likes", 0) + p.get("comments_count", 0), reverse=True
    )
    for p in by_engagement:
        if len(selected) >= TOP_ENGAGEMENT:
            break
        selected.append(p)
        selected_codes.add(p["shortcode"])

    by_date = sorted(posts, key=lambda p: p.get("timestamp", 0), reverse=True)
    for p in by_date:
        if p["shortcode"] in selected_codes:
            continue
        if len(selected) >= TOP_ENGAGEMENT + RECENT:
            break
        selected.append(p)
        selected_codes.add(p["shortcode"])

    remaining = [p for p in posts if p["shortcode"] not in selected_codes]
    random.seed(42)
    random.shuffle(remaining)
    for p in remaining:
        if len(selected) >= n:
            break
        selected.append(p)
        selected_codes.add(p["shortcode"])

    return selected


def content_type_from_post(post: dict) -> str:
    mt = post.get("media_type")
    pt = post.get("product_type", "")
    if post.get("is_carousel") or mt == 8:
        return "carousel_slide"
    if pt == "clips":
        return "reel"
    if post.get("is_video") or mt == 2:
        return "video"
    return "image"


def process_account(handle: str) -> dict | None:
    """Process one account. Returns summary dict or None on error."""
    inbox = INBOX_DIR / f"@{handle}"
    extraction_path = inbox / f"{handle}_full_extraction.json"

    if not extraction_path.exists():
        print(f"  SKIP: {extraction_path} not found")
        return None

    data = json.loads(extraction_path.read_text(encoding="utf-8"))
    profile = data.get("profile", {})
    posts = data.get("posts", [])
    comments = data.get("comments", {})
    summary = data.get("summary", {})

    if not posts:
        print(f"  SKIP: no posts in extraction")
        return None

    media_dir = inbox / "media"
    ref = ACCOUNT_REFS.get(handle, {})

    selected = select_posts(posts)
    queue_posts = []
    for post in selected:
        sc = post["shortcode"]
        media_files = find_media_files(media_dir, sc)
        engagement = post.get("likes", 0) + post.get("comments_count", 0)
        queue_posts.append({
            "shortcode": sc,
            "id": post.get("id"),
            "content_type": content_type_from_post(post),
            "timestamp": post.get("timestamp"),
            "date": post.get("date"),
            "caption": post.get("caption", ""),
            "likes": post.get("likes", 0),
            "comments_count": post.get("comments_count", 0),
            "play_count": post.get("play_count"),
            "view_count": post.get("view_count"),
            "engagement_score": engagement,
            "location": post.get("location"),
            "product_type": post.get("product_type"),
            "tagged_users": post.get("tagged_users", []),
            "is_paid_partnership": post.get("is_paid_partnership", False),
            "media_files_on_disk": media_files,
            "has_media": len(media_files) > 0,
            "pass1_status": "pending",
            "pass2_status": "pending",
        })

    queue = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "handle": handle,
        "account_handle_normalized": ref.get("normalized", f"OGZ-F-AND-B-{handle}"),
        "account_ulid": ref.get("ulid", ""),
        "sector": "f_and_b",
        "total_posts_in_extraction": len(posts),
        "selected_count": len(queue_posts),
        "selection_method": f"top_{TOP_ENGAGEMENT}_engagement + {RECENT}_recent + {RANDOM_FILL}_random",
        "posts": queue_posts,
    }
    queue_path = inbox / "extraction_queue.json"
    queue_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

    captions = []
    for i, post in enumerate(posts, 1):
        cap = post.get("caption", "").strip()
        if cap:
            date_str = post.get("date", "unknown")[:10]
            captions.append(f"--- [{i}/{len(posts)}] {post['shortcode']} ({date_str}) ---\n{cap}\n")
    captions_path = inbox / "captions.txt"
    captions_path.write_text("\n".join(captions), encoding="utf-8")

    followers = profile.get("followers", 0)
    total_likes = sum(p.get("likes", 0) for p in posts)
    total_comments = sum(p.get("comments_count", 0) for p in posts)
    total_plays = sum(p.get("play_count", 0) or 0 for p in posts)
    videos = [p for p in posts if p.get("is_video") or p.get("media_type") == 2]
    images = [p for p in posts if not p.get("is_video") and not p.get("is_carousel") and p.get("media_type") != 8]
    carousels = [p for p in posts if p.get("is_carousel") or p.get("media_type") == 8]
    reels = [p for p in posts if p.get("product_type") == "clips"]
    locations = [p.get("location") for p in posts if p.get("location")]
    tagged = [p for p in posts if p.get("tagged_users")]
    paid = [p for p in posts if p.get("is_paid_partnership")]

    acct_summary = {
        "handle": handle,
        "account_handle_normalized": ref.get("normalized"),
        "account_ulid": ref.get("ulid"),
        "sector": "f_and_b",
        "profile": {
            "username": profile.get("username"),
            "full_name": profile.get("full_name"),
            "biography": profile.get("biography"),
            "followers": followers,
            "following": profile.get("following"),
            "post_count": profile.get("post_count"),
            "is_verified": profile.get("is_verified"),
            "is_business": profile.get("is_business"),
            "category": profile.get("category"),
        },
        "content_stats": {
            "extracted_posts": len(posts),
            "images": len(images),
            "videos": len(videos),
            "carousels": len(carousels),
            "reels": len(reels),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_plays": total_plays,
            "avg_likes": round(total_likes / len(posts)) if posts else 0,
            "avg_comments": round(total_comments / len(posts)) if posts else 0,
            "avg_engagement_rate": round((total_likes + total_comments) / (len(posts) * max(followers, 1)) * 100, 2),
            "posts_with_location": len(locations),
            "posts_with_tags": len(tagged),
            "paid_partnerships": len(paid),
            "date_range": {
                "oldest": posts[-1].get("date", "")[:10] if posts else "",
                "newest": posts[0].get("date", "")[:10] if posts else "",
            },
        },
        "comments_extracted": {
            "posts_with_comments": len(comments),
            "total_comments": sum(
                c.get("extracted", 0) if isinstance(c, dict) else len(c)
                for c in comments.values()
            ),
        },
        "media_on_disk": {
            "total_files": len(list(media_dir.iterdir())) if media_dir.exists() else 0,
        },
        "selected_for_visual_analysis": len(queue_posts),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = inbox / "account_summary.json"
    summary_path.write_text(json.dumps(acct_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "handle": handle,
        "posts": len(posts),
        "selected": len(queue_posts),
        "captions_chars": sum(len(c) for c in captions),
        "media_matched": sum(1 for p in queue_posts if p["has_media"]),
    }


def main() -> int:
    print("Phase 0: Preprocessing inbox for 4-account pilot\n")

    results = []
    for handle in PILOT_ACCOUNTS:
        print(f"Processing @{handle}...")
        result = process_account(handle)
        if result:
            results.append(result)
            print(f"  {result['posts']} posts total, {result['selected']} selected, "
                  f"{result['media_matched']}/{result['selected']} have media on disk")
        print()

    print(f"\nDone: {len(results)}/{len(PILOT_ACCOUNTS)} accounts processed")
    total_selected = sum(r["selected"] for r in results)
    total_with_media = sum(r["media_matched"] for r in results)
    print(f"Total posts selected: {total_selected}")
    print(f"Posts with media on disk: {total_with_media}/{total_selected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
