#!/usr/bin/env python3
"""
extract_account_browser_api.py
Extract full account data using Instagram's internal web API via the logged-in
Chrome browser session. Replicates the original browser_v1_api_full method.

For each account:
  1. Calls Instagram's /api/v1/feed/user/{user_id}/  (paginated)
  2. Gets all posts with real engagement data + captions + media URLs
  3. Downloads media files while CDN URLs are valid
  4. Writes {handle}_full_extraction.json (same format as original)
  5. Runs preprocess_inbox to create extraction_queue + account_summary

Usage:
  python3 scripts/extract_account_browser_api.py --handle kyajy --sector beauty
  python3 scripts/extract_account_browser_api.py --all-priority
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import browser_cookie3

BASE     = Path(__file__).resolve().parent.parent
INBOX    = BASE / "11_who_to_learn_from" / "_inbox"
ACC_ROOT = BASE / "11_who_to_learn_from" / "accounts"
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

SLEEP_BETWEEN_PAGES  = 3   # seconds between API pages
SLEEP_BETWEEN_ACCTS  = 30  # seconds between accounts
MAX_POSTS_PER_ACCT   = 100 # cap to avoid huge downloads
DOWNLOAD_MEDIA       = True

# Priority accounts — ordered by follower count
PRIORITY_BEAUTY = [
    ("kyajy",            "OGZ-BEAUTY-Reference-003",  "beauty"),
    ("fitnesstimesa",    "OGZ-BEAUTY-Reference-004",  "beauty"),
    ("laze",             "OGZ-BEAUTY-Reference-006",  "beauty"),
    ("qabonah",          "OGZ-BEAUTY-Reference-010",  "beauty"),
    ("baseandboon",      "OGZ-BEAUTY-Reference-016",  "beauty"),
]
PRIORITY_RETAIL = [
    ("lanb_boutique",    "OGZ-RETAIL-Reference-003",  "retail"),
    ("bayaboutique",     "OGZ-RETAIL-Reference-004",  "retail"),
    ("vella.sa",         "OGZ-RETAIL-Reference-005",  "retail"),
    ("lyafie_jewelry",   "OGZ-RETAIL-Reference-007",  "retail"),
    ("kids_ksa",         "OGZ-RETAIL-Reference-008",  "retail"),
]
PRIORITY_FNB = [
    ("zzahut_sa",        "OGZ-F-AND-B-Reference-012", "f_and_b"),
    ("fe.najd",          "OGZ-F-AND-B-Reference-013", "f_and_b"),
    ("donalds_sa",       "OGZ-F-AND-B-Reference-014", "f_and_b"),
    ("lsaif.gallery",    "OGZ-F-AND-B-Reference-015", "f_and_b"),
    ("kheel_mall_riyadh","OGZ-F-AND-B-Reference-016", "f_and_b"),
]

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ulid_off = 0

def make_ulid() -> str:
    global _ulid_off
    t = int(time.time() * 1000) + _ulid_off
    _ulid_off += 1
    t_part = ""
    v = t
    for _ in range(10):
        t_part = CROCKFORD[v & 0x1F] + t_part
        v >>= 5
    r = random.getrandbits(80)
    r_part = ""
    for _ in range(16):
        r_part = CROCKFORD[r & 0x1F] + r_part
        r >>= 5
    return t_part + r_part


def _get_cookies() -> dict:
    """Get Instagram session cookies from Chrome."""
    for profile in ["Profile 1", "Profile 2", "Default", "Profile 3", "Profile 4"]:
        db = Path.home() / f"Library/Application Support/Google/Chrome/{profile}/Cookies"
        if not db.exists():
            continue
        try:
            cj = browser_cookie3.chrome(cookie_file=str(db), domain_name=".instagram.com")
            cookies = {c.name: c.value for c in cj}
            if cookies.get("sessionid"):
                print(f"  ✅ Session found in Chrome {profile}")
                return cookies
        except Exception:
            continue
    raise RuntimeError("No Instagram sessionid found in Chrome. Make sure you're logged in.")


def _make_headers(cookies: dict) -> dict:
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items() if k in (
        "sessionid", "ds_user_id", "csrftoken", "ig_did", "mid", "ig_nrcb"
    ))
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Cookie": cookie_str,
        "X-CSRFToken": cookies.get("csrftoken", ""),
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/",
        "Origin": "https://www.instagram.com",
    }


def _api_get(url: str, headers: dict) -> dict | None:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"    API error: {e}")
        return None


def _get_user_id(handle: str, headers: dict) -> str | None:
    """Get numeric user ID from handle."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={handle}"
    data = _api_get(url, headers)
    if data:
        uid = (data.get("data", {}).get("user", {}) or {}).get("id")
        if uid:
            return str(uid)
    # Fallback: scrape profile page
    url2 = f"https://www.instagram.com/{handle}/?__a=1&__d=dis"
    data2 = _api_get(url2, headers)
    if data2:
        uid = (data2.get("graphql", {}).get("user", {}) or {}).get("id")
        if uid:
            return str(uid)
    return None


def _get_profile(handle: str, headers: dict) -> dict:
    """Get account profile data."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={handle}"
    data = _api_get(url, headers)
    if data:
        user = data.get("data", {}).get("user", {}) or {}
        return {
            "username":    user.get("username", handle),
            "full_name":   user.get("full_name", ""),
            "biography":   user.get("biography", ""),
            "followers":   user.get("edge_followed_by", {}).get("count", 0),
            "following":   user.get("edge_follow", {}).get("count", 0),
            "post_count":  user.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "is_verified": user.get("is_verified", False),
            "is_business": user.get("is_business_account", False),
            "category":    user.get("category_name", ""),
        }
    return {"username": handle}


def _fetch_posts(user_id: str, headers: dict, max_posts: int = MAX_POSTS_PER_ACCT) -> list[dict]:
    """Fetch posts using the feed API (paginated)."""
    posts = []
    cursor = None
    page = 1

    while len(posts) < max_posts:
        url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12"
        if cursor:
            url += f"&max_id={cursor}"

        print(f"    Page {page} ({len(posts)} posts so far)...", end=" ", flush=True)
        data = _api_get(url, headers)

        if not data:
            print("failed")
            break

        items = data.get("items", [])
        if not items:
            print("empty")
            break

        for item in items:
            post = _parse_post(item)
            if post:
                posts.append(post)

        print(f"{len(items)} posts")

        more = data.get("more_available", False)
        cursor = data.get("next_max_id")
        if not more or not cursor:
            break

        page += 1
        time.sleep(SLEEP_BETWEEN_PAGES)

    return posts[:max_posts]


def _parse_post(item: dict) -> dict | None:
    """Parse a single post item from the feed API."""
    sc = item.get("code") or item.get("shortcode", "")
    if not sc:
        return None

    caption_text = ""
    caption_node = item.get("caption")
    if caption_node:
        caption_text = caption_node.get("text", "") if isinstance(caption_node, dict) else str(caption_node)

    like_count = item.get("like_count", 0) or 0
    comment_count = item.get("comment_count", 0) or 0
    play_count = item.get("play_count") or item.get("view_count")

    media_type = item.get("media_type", 1)
    is_video = media_type == 2
    is_carousel = media_type == 8

    image_url  = None
    video_url  = None
    thumb_url  = None
    carousel_media = []

    if is_video:
        video_url = item.get("video_versions", [{}])[0].get("url") if item.get("video_versions") else None
        thumb_url = (item.get("image_versions2", {}).get("candidates", [{}])[0].get("url")
                     if item.get("image_versions2") else None)
    elif is_carousel:
        carousel_items = item.get("carousel_media", [])
        for ci in carousel_items:
            imgs = ci.get("image_versions2", {}).get("candidates", [{}])
            carousel_media.append({"image_url": imgs[0].get("url") if imgs else None})
        if carousel_items:
            imgs = carousel_items[0].get("image_versions2", {}).get("candidates", [{}])
            image_url = imgs[0].get("url") if imgs else None
    else:
        imgs = item.get("image_versions2", {}).get("candidates", [{}])
        image_url = imgs[0].get("url") if imgs else None

    ts = item.get("taken_at", 0)
    content_type = "video" if is_video else ("carousel" if is_carousel else "image")

    return {
        "shortcode":          sc,
        "id":                 str(item.get("pk", "")),
        "content_type":       content_type,
        "media_type":         media_type,
        "timestamp":          ts,
        "date":               datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None,
        "caption":            caption_text,
        "likes":              like_count,
        "comments_count":     comment_count,
        "play_count":         play_count,
        "view_count":         play_count,
        "engagement_score":   like_count + comment_count,
        "is_video":           is_video,
        "is_carousel":        is_carousel,
        "location":           (item.get("location") or {}).get("name"),
        "product_type":       item.get("product_type", "feed"),
        "media_count":        len(carousel_media) if is_carousel else 1,
        "tagged_users":       [u.get("user", {}).get("username", "") for u in item.get("usertags", {}).get("in", [])],
        "has_audio":          item.get("has_audio"),
        "is_paid_partnership":item.get("is_paid_partnership", False),
        "like_and_view_counts_disabled": item.get("like_and_view_counts_disabled", False),
        "accessibility_caption": item.get("accessibility_caption"),
        "dimensions":         {"width": item.get("original_width"), "height": item.get("original_height")},
        "image_url":          image_url,
        "video_url":          video_url,
        "thumbnail_url":      thumb_url,
        "carousel_media":     carousel_media,
    }


def _download_media(posts: list[dict], media_dir: Path, headers: dict) -> int:
    """Download images/thumbs for posts. Returns count downloaded."""
    media_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    dl_headers = {k: v for k, v in headers.items() if k not in ("X-CSRFToken", "X-Requested-With")}

    for post in posts:
        sc = post["shortcode"]
        urls_to_dl = []

        if post["is_video"] and post.get("thumbnail_url"):
            urls_to_dl.append((post["thumbnail_url"], f"{sc}_thumb.jpg"))
            if post.get("video_url"):
                urls_to_dl.append((post["video_url"], f"{sc}.mp4"))
        elif post["is_carousel"]:
            for i, cm in enumerate(post.get("carousel_media", [])):
                if cm.get("image_url"):
                    urls_to_dl.append((cm["image_url"], f"{sc}_{i+1}.jpg"))
            if not post.get("carousel_media") and post.get("image_url"):
                urls_to_dl.append((post["image_url"], f"{sc}.jpg"))
        elif post.get("image_url"):
            urls_to_dl.append((post["image_url"], f"{sc}.jpg"))

        for url, fname in urls_to_dl:
            dst = media_dir / fname
            if dst.exists():
                continue
            try:
                req = urllib.request.Request(url, headers=dl_headers)
                with urllib.request.urlopen(req, timeout=30) as r:
                    dst.write_bytes(r.read())
                downloaded += 1
            except Exception as e:
                pass  # CDN URL may have expired

    return downloaded


def extract_account(handle: str, handle_norm: str, sector: str, cookies: dict, max_posts: int = MAX_POSTS_PER_ACCT) -> bool:
    """Full extraction for one account. Returns True on success."""
    print(f"\n{'─'*55}")
    print(f"  @{handle}  [{sector}]  norm={handle_norm}")
    print(f"{'─'*55}")

    # Skip if already extracted
    inbox_dir   = INBOX / f"@{handle}"
    extract_f   = inbox_dir / f"{handle}_full_extraction.json"
    skip_f      = inbox_dir / "SKIPPED.json"

    if extract_f.exists():
        post_count = len(json.loads(extract_f.read_text()).get("posts", []))
        if post_count >= 10:
            print(f"  ⏭  Already extracted ({post_count} posts) — skipping")
            return True

    inbox_dir.mkdir(parents=True, exist_ok=True)
    headers = _make_headers(cookies)

    # 1. Get profile
    print(f"  Getting profile...", end=" ", flush=True)
    profile = _get_profile(handle, headers)
    followers = profile.get("followers", 0)
    print(f"  {followers:,} followers")

    if followers == 0:
        print(f"  ⚠  0 followers — account may be private/deleted")
        skip_f.write_text(json.dumps({"reason": "zero_followers", "handle": handle}, indent=2))
        return False

    # 2. Get user ID
    print(f"  Getting user ID...", end=" ", flush=True)
    user_id = _get_user_id(handle, headers)
    if not user_id:
        print(f"failed")
        skip_f.write_text(json.dumps({"reason": "user_id_not_found", "handle": handle}, indent=2))
        return False
    print(f"  uid={user_id}")

    # 3. Fetch posts
    print(f"  Fetching posts (max {MAX_POSTS_PER_ACCT}):")
    posts = _fetch_posts(user_id, headers, max_posts)
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print(f"  ⚠  No posts fetched")
        skip_f.write_text(json.dumps({"reason": "no_posts", "handle": handle}, indent=2))
        return False

    # 4. Download media
    if DOWNLOAD_MEDIA:
        media_dir = inbox_dir / "media"
        print(f"  Downloading media to media/...", end=" ", flush=True)
        dl_count = _download_media(posts, media_dir, headers)
        print(f"  {dl_count} files downloaded")

    # 5. Write full_extraction.json
    total_images = sum(1 for p in posts if not p["is_video"] and not p["is_carousel"])
    total_videos = sum(1 for p in posts if p["is_video"])
    total_carousels = sum(1 for p in posts if p["is_carousel"])

    extraction = {
        "extraction_date":   datetime.now(tz=timezone.utc).isoformat(),
        "extraction_method": "browser_v1_api_full",
        "account":           handle,
        "profile":           profile,
        "summary": {
            "total_posts":      len(posts),
            "images":           total_images,
            "videos":           total_videos,
            "carousels":        total_carousels,
            "avg_likes":        round(sum(p["likes"] for p in posts) / max(len(posts),1), 1),
            "avg_comments":     round(sum(p["comments_count"] for p in posts) / max(len(posts),1), 1),
        },
        "posts":     posts,
        "comments":  [],
        "media_manifest": {
            "total_files": len(posts),
            "note":        "CDN URLs valid at extraction time only"
        },
    }

    extract_f.write_text(json.dumps(extraction, ensure_ascii=False, indent=2))
    print(f"  ✅ Saved → {extract_f.name}  ({len(posts)} posts)")

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle",  help="Single account handle to extract")
    parser.add_argument("--norm",    help="Normalized ID (e.g. OGZ-BEAUTY-Reference-003)")
    parser.add_argument("--sector",  choices=["beauty", "retail", "f_and_b"], default="beauty")
    parser.add_argument("--all-priority", action="store_true", help="Extract all priority accounts")
    parser.add_argument("--all-beauty",   action="store_true")
    parser.add_argument("--all-retail",   action="store_true")
    parser.add_argument("--all-fnb",      action="store_true")
    parser.add_argument("--max", type=int, default=5, help="Max accounts when using --all-*")
    parser.add_argument("--max-posts", type=int, default=MAX_POSTS_PER_ACCT, dest="max_posts",
                        help="posts per account (default 100; raise to cover a longer window)")
    args = parser.parse_args()

    print("Loading Instagram session from Chrome...")
    try:
        cookies = _get_cookies()
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    accounts = []
    if args.handle:
        norm = args.norm or f"OGZ-{args.sector.upper().replace('_AND_','-AND-')}-Reference-????"
        accounts = [(args.handle, norm, args.sector)]
    elif args.all_priority:
        accounts = (PRIORITY_BEAUTY + PRIORITY_RETAIL + PRIORITY_FNB)[:args.max]
    elif args.all_beauty:
        accounts = PRIORITY_BEAUTY[:args.max]
    elif args.all_retail:
        accounts = PRIORITY_RETAIL[:args.max]
    elif args.all_fnb:
        accounts = PRIORITY_FNB[:args.max]
    else:
        # Default: all priority beauty first
        accounts = (PRIORITY_BEAUTY + PRIORITY_RETAIL + PRIORITY_FNB)[:args.max]

    print(f"\nAccounts to extract: {len(accounts)}")

    success = 0
    failed  = 0
    for i, (handle, norm, sector) in enumerate(accounts):
        ok = extract_account(handle, norm, sector, cookies, args.max_posts)
        if ok:
            success += 1
        else:
            failed += 1
        if i < len(accounts) - 1:
            print(f"\n  Sleeping {SLEEP_BETWEEN_ACCTS}s...")
            time.sleep(SLEEP_BETWEEN_ACCTS)

    print(f"\n{'='*55}")
    print(f"EXTRACTION COMPLETE")
    print(f"  Success: {success}")
    print(f"  Failed : {failed}")
    print(f"\nNext: python3 scripts/preprocess_inbox.py")
    print(f"Then: python3 scripts/batch_extract.py --account HANDLE --batch B1")


if __name__ == "__main__":
    main()
