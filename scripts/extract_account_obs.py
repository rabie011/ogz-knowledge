#!/usr/bin/env python3
"""
extract_account_obs.py
Download posts from an Instagram account via Apify, classify them with
Claude Batch API (Haiku 4.5), and write observation JSON files.

Requires:
  - APIFY_TOKEN in ~/.abraham_env
  - ANTHROPIC_API_KEY in ~/.abraham_env
  - pip install apify-client anthropic python-ulid

Usage:
  python3 scripts/extract_account_obs.py --handle barnscoffee --sector f_and_b
  python3 scripts/extract_account_obs.py --handle jarir --sector retail --limit 50
  python3 scripts/extract_account_obs.py --handle barnscoffee --sector f_and_b --dry-run
"""
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from ulid import ULID

# ── Load env ───────────────────────────────────────────────────────────────────
def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if not os.environ.get(k):
                    os.environ[k] = v

_load_env()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent.parent
OBS_ROOT   = BASE / "11_who_to_learn_from" / "observations"
ACCTS_ROOT = BASE / "11_who_to_learn_from" / "accounts"
ACCOUNTS_INDEX = BASE / "11_who_to_learn_from" / "accounts_index.json"
TARGET_ACCOUNTS_FILE = BASE / "11_who_to_learn_from" / "target_accounts.json"

# ── Sector folder mapping ──────────────────────────────────────────────────────
SECTOR_FOLDER = {
    "f_and_b":              "f_and_b",
    "food_and_beverage":    "f_and_b",
    "beauty":               "beauty",
    "beauty_personal_care": "beauty",
    "retail":               "retail",
    "retail_lifestyle":     "retail",
    "real_estate":          "real_estate",
}

# ── Apify actor ────────────────────────────────────────────────────────────────
APIFY_ACTOR = "apify/instagram-post-scraper"

# ── Classification prompt ──────────────────────────────────────────────────────
CLASSIFY_SYSTEM = """You are a Saudi Instagram content analyst. Classify posts for a Saudi content intelligence database.
Return ONLY valid JSON — no explanation, no markdown."""

def _classify_prompt(caption: str, content_type: str, capture_date: str,
                     sector: str, likes: int, comments: int) -> str:
    engagement_signal = "high" if (likes + comments) > 500 else "medium" if (likes + comments) > 100 else "low"
    return f"""Classify this Saudi Instagram post:

Caption (first 500 chars): "{caption[:500] if caption else ''}"
Type: {content_type} | Date: {capture_date} | Sector: {sector}
Likes: {likes} | Comments: {comments} | Rough engagement signal: {engagement_signal}

Return ONLY this JSON (all fields required, exact enum values):
{{
  "engagement_potential": "high" or "medium" or "low",
  "production_quality": "professional" or "semi_professional" or "ugc" or "low",
  "overall_compliance": "clean" or "soft_flagged" or "hard_blocked",
  "occasion": null or "ramadan" or "national_day" or "eid_al_fitr" or "eid_al_adha" or "founding_day" or "seasonal" or "general",
  "language": "arabic" or "english" or "bilingual" or "none",
  "tone": "celebratory" or "informative" or "casual" or "professional" or "urgent" or "playful",
  "heritage_vs_modern": "heritage" or "modern" or "blended" or "neutral",
  "composition_style": "product_hero_closeup" or "lifestyle_integrated" or "editorial" or "overhead_spread" or "face_forward" or "text_dominant",
  "visual_complexity": "simple" or "moderate" or "complex",
  "human_presence": "none" or "partial" or "full",
  "pattern_slugs": [],
  "compliance_flags": []
}}"""


# ── Apify extraction ───────────────────────────────────────────────────────────
def extract_via_apify(handle: str, limit: int) -> list[dict]:
    """Pull posts from Apify Instagram scraper. Returns raw Apify post dicts."""
    apify_token = os.environ.get("APIFY_TOKEN", "")
    if not apify_token:
        raise RuntimeError(
            "APIFY_TOKEN not set. Create a free Apify account at apify.com → "
            "Settings → API tokens → add to ~/.abraham_env as APIFY_TOKEN"
        )

    try:
        from apify_client import ApifyClient
    except ImportError:
        raise RuntimeError(
            "apify-client not installed. Run: pip install apify-client"
        )

    print(f"  Calling Apify for @{handle} (limit={limit})...", flush=True)
    client = ApifyClient(apify_token)
    run = client.actor(APIFY_ACTOR).call(
        run_input={
            "username": [handle],
            "resultsLimit": limit,
            "addParentData": False,
        }
    )
    posts = list(client.dataset(run.default_dataset_id).iterate_items())
    print(f"  Apify returned {len(posts)} posts", flush=True)
    return posts


# ── Map Apify post → raw obs fields ───────────────────────────────────────────
def _map_apify_post(post: dict, handle: str, sector: str) -> dict:
    """Convert Apify post dict to partial obs dict before classification."""
    short_code  = post.get("shortCode") or post.get("id", "")
    post_type   = post.get("type", "")  # Image | Video | Sidecar
    timestamp   = post.get("timestamp") or post.get("takenAt", "")
    caption_raw = post.get("caption") or post.get("captionText") or ""
    likes       = int(post.get("likesCount") or post.get("likes") or 0)
    comments    = int(post.get("commentsCount") or post.get("comments") or 0)
    display_url = post.get("displayUrl") or post.get("imageUrl") or ""

    # content_type mapping
    ct_map = {"Image": "image", "Video": "video", "Sidecar": "carousel_slide"}
    content_type = ct_map.get(post_type, "image")

    # Normalise date to YYYY-MM-DD
    if timestamp:
        try:
            if isinstance(timestamp, int):
                capture_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            else:
                capture_date = str(timestamp)[:10]
        except Exception:
            capture_date = "2026-01-01"
    else:
        capture_date = "2026-01-01"

    # Derive filename from URL or shortCode
    filename = f"{short_code}.jpg" if not display_url else display_url.split("?")[0].split("/")[-1]

    word_count = len(caption_raw.split()) if caption_raw else 0
    hashtag_count = len(re.findall(r"#\w+", caption_raw))
    has_emoji = bool(re.search(r"[\U00010000-\U0010ffff\U00002600-\U000027BF]", caption_raw))

    return {
        "short_code":    short_code,
        "content_type":  content_type,
        "capture_date":  capture_date,
        "caption_text":  caption_raw,
        "word_count":    word_count,
        "hashtag_count": hashtag_count,
        "has_emoji":     has_emoji,
        "likes":         likes,
        "comments":      comments,
        "display_url":   display_url,
        "filename":      filename,
        "sector":        sector,
        "handle":        handle,
        "source_url":    f"https://www.instagram.com/p/{short_code}/",
    }


# ── Claude Batch classification ────────────────────────────────────────────────
def classify_batch(raw_posts: list[dict], client: anthropic.Anthropic) -> dict[str, dict]:
    """Submit batch classification job. Returns {short_code: classification_dict}."""
    requests = []
    for p in raw_posts:
        requests.append({
            "custom_id": p["short_code"],
            "params": {
                "model": "claude-haiku-4-5",
                "max_tokens": 500,
                "system": CLASSIFY_SYSTEM,
                "messages": [{"role": "user", "content": _classify_prompt(
                    p["caption_text"], p["content_type"], p["capture_date"],
                    p["sector"], p["likes"], p["comments"],
                )}],
            },
        })

    print(f"  Submitting {len(requests)} posts to Claude Batch API...", flush=True)
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"  Batch ID: {batch_id}", flush=True)

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(
            f"  Status: {status} | "
            f"succeeded={counts.succeeded} errored={counts.errored} processing={counts.processing}",
            flush=True,
        )
        if status == "ended":
            break
        time.sleep(10)

    results = {}
    for result in client.messages.batches.results(batch_id):
        sc = result.custom_id
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            try:
                results[sc] = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"  ⚠ JSON parse error for {sc}: {e}")
        else:
            print(f"  ✗ {sc}: {result.result.type}")

    return results


# ── Write observation JSON ─────────────────────────────────────────────────────
def _get_or_create_account_ulid(handle: str) -> str:
    """Look up account ULID: checks accounts_index.json first, then existing accounts/ JSON files."""
    # 1. Check fast-path index
    index = {}
    if ACCOUNTS_INDEX.exists():
        try:
            index = json.loads(ACCOUNTS_INDEX.read_text())
        except Exception:
            pass
    if handle in index:
        return index[handle]

    # 2. Search existing account JSON files for a matching handle
    accounts_dir = BASE / "11_who_to_learn_from" / "accounts"
    for acct_file in accounts_dir.rglob("*.json"):
        try:
            d = json.loads(acct_file.read_text())
            # Match on account_handle_normalized (e.g. "kuduksa") or handle field
            handle_norm = d.get("account_handle_normalized", "")
            handle_raw  = d.get("handle", "")
            if handle in (handle_norm, handle_raw, handle_norm.lower(), handle_raw.lower()):
                existing_ulid = d.get("account_ulid", "")
                if existing_ulid:
                    index[handle] = existing_ulid
                    ACCOUNTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
                    ACCOUNTS_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
                    return existing_ulid
        except Exception:
            continue

    # 3. Create new ULID
    new_ulid = str(ULID())
    index[handle] = new_ulid
    ACCOUNTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    return new_ulid


def write_observation(raw: dict, cls: dict, account_ulid: str) -> Path:
    """Build and write a complete observation_v1 JSON file."""
    sector_folder = SECTOR_FOLDER.get(raw["sector"], raw["sector"])
    obs_dir = OBS_ROOT / sector_folder
    obs_dir.mkdir(parents=True, exist_ok=True)

    obs_ulid = str(ULID())
    handle = raw["handle"]

    # Determine language
    lang = cls.get("language", "arabic")
    valid_langs = {"arabic", "english", "bilingual", "none"}
    if lang not in valid_langs:
        lang = "arabic"

    # Compliance
    compliance = cls.get("overall_compliance", "clean")
    if compliance not in {"clean", "soft_flagged", "hard_blocked"}:
        compliance = "clean"

    # Engagement
    eng = cls.get("engagement_potential", "medium")
    if eng not in {"high", "medium", "low"}:
        eng = "medium"

    # Production quality
    pq = cls.get("production_quality", "semi_professional")
    if pq not in {"professional", "semi_professional", "ugc", "low"}:
        pq = "semi_professional"

    # Pattern matches
    pattern_matches = [
        {"pattern_slug": slug, "confidence": "moderate"}
        for slug in (cls.get("pattern_slugs") or [])
        if isinstance(slug, str) and slug.strip()
    ]

    # human_presence: schema expects boolean/null
    hp_raw = cls.get("human_presence", "none")
    if hp_raw in ("full", "partial"):
        human_presence = True
    elif hp_raw == "none":
        human_presence = False
    else:
        human_presence = None

    obs = {
        "observation_ulid": obs_ulid,
        "schema_version": 1,
        "account_handle_normalized": handle,
        "account_ulid": account_ulid,
        "sector": raw["sector"],
        "content_ref": {
            "filename": raw["filename"],
            "platform": "instagram",
            "content_type": raw["content_type"],
            "capture_date": raw["capture_date"],
            "source_url": raw["source_url"],
        },
        "visual_observations": {
            "composition_style": cls.get("composition_style", ""),
            "lighting": "",
            "color_palette_dominant": [],
            "visual_complexity": cls.get("visual_complexity", "moderate"),
            "human_presence": human_presence,
            "setting": "",
        },
        "voice_observations": {
            "caption_text": raw["caption_text"],
            "language": lang,
            "caption_word_count": raw["word_count"],
            "hashtag_count": raw["hashtag_count"],
            "has_emoji": raw["has_emoji"],
            "tone": cls.get("tone", "informative"),
        },
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags": [
                {"flag_type": f, "description": f.replace("_", " ")} if isinstance(f, str)
                else f
                for f in (cls.get("compliance_flags") or [])
            ],
            "overall_compliance": compliance,
        },
        "cultural_notes": {
            "occasion_relevance": cls.get("occasion") or None,
            "hospitality_cues": [],
            "heritage_vs_modern": cls.get("heritage_vs_modern", "neutral") if cls.get("heritage_vs_modern") in ("heritage", "modern", "blended", "neutral") else "neutral",
            "free_notes": "",
        },
        "pattern_matches": pattern_matches,
        "quality_assessment": {
            "engagement_potential": eng,
            "production_quality": pq,
        },
        "provenance": {
            "source": "apify_instagram_scraper",
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confirmer": "claude_haiku_batch_classification",
            "confidence": "inferred",
            "scope": f"brand:{re.sub(r'[^a-z0-9_]', '_', handle.lower())}",
        },
    }

    out = obs_dir / f"{obs_ulid}.json"
    out.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
    return out


# ── Quota helpers ──────────────────────────────────────────────────────────────
DEFAULT_QUOTA = {"image": 50, "video": 50, "carousel": 25}

def _ct_to_quota_key(content_type: str) -> str:
    """Map content_type → quota bucket key."""
    if content_type in ("video", "reel"):
        return "video"
    if content_type == "carousel_slide":
        return "carousel"
    return "image"  # image, story, unknown → image bucket


def count_existing_by_type(handle: str) -> dict:
    """Count existing obs for this handle, bucketed by quota key."""
    counts = {"image": 0, "video": 0, "carousel": 0}
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized", "").lower() != handle.lower():
                continue
            ct = d.get("content_ref", {}).get("content_type", "")
            key = _ct_to_quota_key(ct)
            counts[key] += 1
        except Exception:
            pass
    return counts


def _load_quota_for_handle(handle: str) -> dict:
    """Load per-account quota from target_accounts.json, or return default."""
    try:
        data = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        for a in data.get("accounts", []):
            if a.get("handle", "").lower() == handle.lower():
                return a.get("quota", DEFAULT_QUOTA)
    except Exception:
        pass
    return DEFAULT_QUOTA


# ── Update target_accounts.json status ────────────────────────────────────────
def _update_target_status(handle: str, written_by_type: dict, quota: dict):
    if not TARGET_ACCOUNTS_FILE.exists():
        return
    try:
        data = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        for acct in data.get("accounts", []):
            if acct.get("handle", "").lower() != handle.lower():
                continue
            # Recount current totals from disk (includes newly written)
            current = count_existing_by_type(handle)
            total = sum(current.values())
            acct["obs_count_actual"] = total
            acct["obs_by_type"] = current
            # Done only if every type meets its quota
            quota_met = all(current.get(k, 0) >= v for k, v in quota.items())
            acct["status"] = "done" if quota_met else "partial"
            break
        data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        TARGET_ACCOUNTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  ⚠ Could not update target_accounts.json: {e}")


# ── Dedup: skip posts already in observations ──────────────────────────────────
def _load_existing_source_urls(handle: str) -> set:
    """Return set of source_urls already written for this handle."""
    urls = set()
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized", "").lower() != handle.lower():
                continue
            url = d.get("content_ref", {}).get("source_url", "")
            if url:
                urls.add(url)
        except Exception:
            pass
    return urls


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract Saudi Instagram account observations")
    parser.add_argument("--handle",  required=True, help="Instagram handle (without @)")
    parser.add_argument("--sector",  required=True, help="Sector: f_and_b | beauty | retail | real_estate")
    parser.add_argument("--quota-image",    type=int, default=None, help="Target image count (default: from target_accounts.json)")
    parser.add_argument("--quota-video",    type=int, default=None, help="Target video/reel count")
    parser.add_argument("--quota-carousel", type=int, default=None, help="Target carousel count")
    parser.add_argument("--dry-run", action="store_true", help="Download only, no file writes")
    args = parser.parse_args()

    handle  = args.handle.lower().lstrip("@")
    sector  = args.sector.lower()
    dry_run = args.dry_run

    # Load quota (CLI overrides file)
    quota = _load_quota_for_handle(handle)
    if args.quota_image    is not None: quota["image"]    = args.quota_image
    if args.quota_video    is not None: quota["video"]    = args.quota_video
    if args.quota_carousel is not None: quota["carousel"] = args.quota_carousel

    print(f"\n{'='*60}")
    print(f"  Extracting @{handle} | sector={sector}")
    print(f"  Quota: image={quota['image']}  video={quota['video']}  carousel={quota['carousel']}")
    print(f"{'='*60}\n")

    # 1. Count what we already have
    existing = count_existing_by_type(handle)
    needed = {k: max(0, quota[k] - existing.get(k, 0)) for k in quota}
    print(f"  Existing: image={existing['image']}  video={existing['video']}  carousel={existing['carousel']}")
    print(f"  Needed:   image={needed['image']}  video={needed['video']}  carousel={needed['carousel']}")

    if sum(needed.values()) == 0:
        print(f"  ✅ @{handle} already meets quota — nothing to extract.")
        _update_target_status(handle, {}, quota)
        sys.exit(0)

    # 2. Already-seen URLs (dedup)
    seen_urls = _load_existing_source_urls(handle)
    print(f"  Dedup: {len(seen_urls)} existing source URLs loaded")

    # 3. Pull from Apify — request 3× needed (buffer for type distribution)
    apify_limit = max(150, sum(needed.values()) * 3)
    try:
        apify_posts = extract_via_apify(handle, apify_limit)
    except RuntimeError as e:
        print(f"❌ Apify error: {e}")
        sys.exit(1)

    if not apify_posts:
        print("❌ No posts returned from Apify.")
        sys.exit(1)

    # 4. Map → raw obs, skip already seen
    raw_posts = []
    dupes = 0
    for p in apify_posts:
        raw = _map_apify_post(p, handle, sector)
        if raw["source_url"] in seen_urls:
            dupes += 1
            continue
        raw_posts.append(raw)

    print(f"  Mapped {len(raw_posts)} new posts ({dupes} dupes skipped)")

    if dry_run:
        print("\nDRY RUN — sample of new posts:")
        for p in raw_posts[:5]:
            key = _ct_to_quota_key(p["content_type"])
            print(f"  [{key}] {p['short_code']} | {p['content_type']} | {p['capture_date']} | {p['caption_text'][:50]!r}")
        return

    if not raw_posts:
        print("  No new posts after dedup.")
        _update_target_status(handle, {}, quota)
        sys.exit(0)

    # 5. Classify via Claude Batch API
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    classifications = classify_batch(raw_posts, client)
    print(f"  Classified {len(classifications)}/{len(raw_posts)} posts")

    # 6. Write — respect per-type quota
    account_ulid  = _get_or_create_account_ulid(handle)
    written_by_type = {"image": 0, "video": 0, "carousel": 0}
    quota_remaining = dict(needed)
    errors = 0

    for raw in raw_posts:
        ct_key = _ct_to_quota_key(raw["content_type"])
        if quota_remaining.get(ct_key, 0) <= 0:
            continue  # this type is full
        sc  = raw["short_code"]
        cls = classifications.get(sc, {})
        try:
            write_observation(raw, cls, account_ulid)
            written_by_type[ct_key] += 1
            quota_remaining[ct_key] -= 1
        except Exception as e:
            print(f"  ✗ {sc}: {e}")
            errors += 1

        # Stop early if all quotas met
        if all(v <= 0 for v in quota_remaining.values()):
            break

    # 7. Update target_accounts.json
    _update_target_status(handle, written_by_type, quota)

    total_written = sum(written_by_type.values())
    print(f"\n{'='*60}")
    print(f"Extracted {total_written} observations  |  Errors: {errors}")
    print(f"  image={written_by_type['image']}  video={written_by_type['video']}  carousel={written_by_type['carousel']}")
    print(f"Account ULID: {account_ulid}")
    print(f"\nNext step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
