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
            "directUrls": [f"https://www.instagram.com/{handle}/"],
            "resultsType": "posts",
            "resultsLimit": limit,
            "addParentData": False,
        }
    )
    posts = list(client.dataset(run["defaultDatasetId"]).iterate_items())
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
    """Look up or create account ULID from accounts_index.json."""
    index = {}
    if ACCOUNTS_INDEX.exists():
        try:
            index = json.loads(ACCOUNTS_INDEX.read_text())
        except Exception:
            pass
    if handle in index:
        return index[handle]
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
        {"pattern_slug": slug, "confidence": "inferred"}
        for slug in (cls.get("pattern_slugs") or [])
        if isinstance(slug, str) and slug.strip()
    ]

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
            "lighting_quality": "",
            "color_palette_dominant": "",
            "visual_complexity": cls.get("visual_complexity", "moderate"),
            "human_presence": cls.get("human_presence", "none"),
            "brand_visibility": "present",
            "setting": "",
            "heritage_vs_modern": cls.get("heritage_vs_modern", "neutral"),
        },
        "voice_observations": {
            "caption_text": raw["caption_text"],
            "caption_language": lang,
            "word_count": raw["word_count"],
            "hashtag_count": raw["hashtag_count"],
            "has_emoji": raw["has_emoji"],
            "tone": cls.get("tone", "informative"),
        },
        "compliance_check": {
            "overall_compliance": compliance,
            "compliance_flags": cls.get("compliance_flags") or [],
            "reviewable_elements": [],
        },
        "cultural_notes": {
            "occasion": cls.get("occasion"),
            "hospitality_cues": [],
            "heritage_signals": [],
            "cultural_sensitivity": "standard",
        },
        "pattern_matches": pattern_matches,
        "quality_assessment": {
            "engagement_potential": eng,
            "production_quality": pq,
            "creative_risk_level": "moderate",
        },
        "provenance": {
            "source": "apify_instagram_scraper",
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confirmer": "claude_haiku_batch_classification",
            "confidence": "inferred",
            "scope": f"account:{handle}",
        },
    }

    out = obs_dir / f"{obs_ulid}.json"
    out.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
    return out


# ── Update target_accounts.json status ────────────────────────────────────────
def _update_target_status(handle: str, obs_count: int):
    if not TARGET_ACCOUNTS_FILE.exists():
        return
    try:
        data = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        for acct in data.get("accounts", []):
            if acct.get("handle") == handle:
                acct["obs_count_actual"] = obs_count
                if obs_count >= acct.get("target_obs", 50):
                    acct["status"] = "done"
                else:
                    acct["status"] = "partial"
                break
        data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        TARGET_ACCOUNTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  ⚠ Could not update target_accounts.json: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract Saudi Instagram account observations")
    parser.add_argument("--handle",  required=True, help="Instagram handle (without @)")
    parser.add_argument("--sector",  required=True, help="Sector: f_and_b | beauty | retail | real_estate")
    parser.add_argument("--limit",   type=int, default=50, help="Max posts to extract")
    parser.add_argument("--dry-run", action="store_true", help="Download only, no file writes")
    args = parser.parse_args()

    handle  = args.handle.lower().lstrip("@")
    sector  = args.sector.lower()
    limit   = args.limit
    dry_run = args.dry_run

    print(f"\n{'='*60}")
    print(f"  Extracting @{handle} | sector={sector} | limit={limit}")
    print(f"{'='*60}\n")

    # 1. Pull from Apify
    try:
        apify_posts = extract_via_apify(handle, limit)
    except RuntimeError as e:
        print(f"❌ Apify error: {e}")
        sys.exit(1)

    if not apify_posts:
        print("❌ No posts returned from Apify.")
        sys.exit(1)

    # 2. Map to raw obs dicts
    raw_posts = [_map_apify_post(p, handle, sector) for p in apify_posts]
    print(f"  Mapped {len(raw_posts)} posts to raw obs format")

    if dry_run:
        print("\nDRY RUN — sample of mapped posts:")
        for p in raw_posts[:3]:
            print(f"  {p['short_code']} | {p['content_type']} | {p['capture_date']} | caption={p['caption_text'][:60]!r}")
        return

    # 3. Classify via Claude Batch API
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    classifications = classify_batch(raw_posts, client)
    print(f"  Classified {len(classifications)}/{len(raw_posts)} posts")

    # 4. Write observation files
    account_ulid = _get_or_create_account_ulid(handle)
    written = 0
    errors  = 0

    for raw in raw_posts:
        sc = raw["short_code"]
        cls = classifications.get(sc, {})
        if not cls:
            print(f"  ⚠ No classification for {sc} — using defaults")
        try:
            out = write_observation(raw, cls, account_ulid)
            print(f"  ✅  {sc} → {out.relative_to(BASE)}")
            written += 1
        except Exception as e:
            print(f"  ✗ {sc}: {e}")
            errors += 1

    # 5. Update target_accounts.json
    _update_target_status(handle, written)

    print(f"\n{'='*60}")
    print(f"Extracted {written} observations  |  Errors: {errors}")
    print(f"Account ULID: {account_ulid}")
    print(f"\nNext step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
