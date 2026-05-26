#!/usr/bin/env python3
"""
extract_account_obs.py
Download posts from an Instagram account via Apify (instagram-post-scraper),
classify them with OpenAI Batch API (GPT-4o-mini), and write observation JSON files.

Requires:
  - OPENAI_API_KEY in ~/.abraham_env
  - APIFY_TOKEN in ~/.abraham_env  (apify.com — ~$11/1000 posts)

Usage:
  python3 scripts/extract_account_obs.py --handle barnscoffee --sector f_and_b
  python3 scripts/extract_account_obs.py --handle niceonesa --sector beauty_personal_care
  python3 scripts/extract_account_obs.py --handle jarirbookstore --sector retail_lifestyle --dry-run

Cost per account (125 posts):
  Apify:        ~$1.38  (125 × $11.03/1000)
  OpenAI Batch: ~$0.009 (125 × 600 tokens × gpt-4o-mini batch pricing)
  Total:        ~$1.39 / account  |  95 accounts ≈ $132  |  $29 covers ~21 accounts
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import openai
from apify_client import ApifyClient
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
    "fashion":              "retail",       # fashion brands → retail obs folder
    "real_estate":          "real_estate",
    "telecom":              "retail",       # telecoms go into retail for now
    "banking_finance":      "retail",
    "automotive":           "retail",
    "hospitality":          "f_and_b",     # hotels/restaurants → f_and_b folder
    "government":           "retail",
}

# ── Instaloader config (fallback when Apify credit exhausted) ─────────────────
INSTALOADER_BIN  = str(BASE / ".venv/bin/instaloader")
if not Path(INSTALOADER_BIN).exists():
    INSTALOADER_BIN = "/opt/homebrew/bin/instaloader"
INSTALOADER_COOKIE_FILE = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Profile 1/Cookies"
)

# ── Apify config ──────────────────────────────────────────────────────────────
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


# ── Apify extraction ──────────────────────────────────────────────────────────
def extract_via_apify(
    handle: str,
    sector: str,
    needed: dict,        # REMAINING per-type counts {image: N, video: N, carousel: N}
    seen_urls: set,
) -> tuple[list[dict], bool]:
    """
    Pull posts from Apify instagram-post-scraper.
    needed = remaining quota per type (already subtracts existing obs).
    Requests sum(needed) * 2 to ensure a good type mix, then filters on our side.

    Returns:
        (raw_posts, profile_exhausted)
    """
    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        raise RuntimeError("APIFY_TOKEN not set in ~/.abraham_env")

    # Request enough posts to likely find the right type mix.
    # Use 5× or minimum 150 to handle skewed type distributions; cap at 300.
    total_needed = sum(needed.values())
    if total_needed == 0:
        return [], False
    results_limit = min(max(total_needed * 5, 150), 300)

    print(f"  Fetching @{handle} via Apify (limit={results_limit})...", flush=True)

    client = ApifyClient(token)
    run = client.actor(APIFY_ACTOR).call(run_input={
        "username": [handle],          # actor v0.99+ requires array
        "resultsLimit": results_limit,
    })

    TYPE_MAP = {
        "Image":   "image",
        "Video":   "video",
        "Sidecar": "carousel_slide",
    }

    remaining = dict(needed)  # mutable copy
    collected: list[dict] = []
    total_raw = 0
    profile_exhausted = False

    # run is a typed Run object in apify_client >= 1.0 — use attribute access
    dataset_id = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId", "")
    items = list(client.dataset(dataset_id).iterate_items())
    total_raw = len(items)
    print(f"  Apify returned {total_raw} raw posts", flush=True)

    if total_raw < results_limit:
        profile_exhausted = True  # got fewer than we asked for — profile is thin

    for item in items:
        if all(v <= 0 for v in remaining.values()):
            break

        # ── Shortcode & dedup ─────────────────────────────────────────────────
        short_code = item.get("shortCode") or item.get("id") or ""
        source_url = f"https://www.instagram.com/p/{short_code}/"
        if source_url in seen_urls or not short_code:
            continue

        # ── Content type ──────────────────────────────────────────────────────
        raw_type     = item.get("type", "Image")
        content_type = TYPE_MAP.get(raw_type, "image")
        quota_key    = _ct_to_quota_key(content_type)
        if remaining.get(quota_key, 0) <= 0:
            continue

        # ── Timestamp ─────────────────────────────────────────────────────────
        ts = item.get("timestamp") or ""
        try:
            capture_date = str(ts)[:10] if ts else datetime.now().strftime("%Y-%m-%d")
        except Exception:
            capture_date = datetime.now().strftime("%Y-%m-%d")

        # ── Caption ───────────────────────────────────────────────────────────
        caption_raw = str(item.get("caption") or "")

        # ── Engagement counts ─────────────────────────────────────────────────
        likes    = int(item.get("likesCount")    or item.get("likes")    or 0)
        comments = int(item.get("commentsCount") or item.get("comments") or 0)

        # ── Derived fields ────────────────────────────────────────────────────
        word_count    = len(caption_raw.split()) if caption_raw else 0
        hashtag_count = len(re.findall(r"#\w+", caption_raw))
        has_emoji     = bool(re.search(r"[\U00010000-\U0010ffff\U00002600-\U000027BF]", caption_raw))

        collected.append({
            "short_code":    short_code,
            "content_type":  content_type,
            "capture_date":  capture_date,
            "caption_text":  caption_raw,
            "word_count":    word_count,
            "hashtag_count": hashtag_count,
            "has_emoji":     has_emoji,
            "likes":         likes,
            "comments":      comments,
            "display_url":   item.get("displayUrl", ""),
            "filename":      f"{short_code}.jpg",
            "sector":        sector,
            "handle":        handle,
            "source_url":    source_url,
        })
        remaining[quota_key] -= 1

    print(
        f"  Collected {len(collected)} posts after quota filter "
        f"(raw={total_raw}, exhausted={profile_exhausted})",
        flush=True,
    )
    return collected, profile_exhausted


# ── Instaloader fallback extraction ──────────────────────────────────────────
def extract_via_instaloader(
    handle: str,
    sector: str,
    needed: dict,
    seen_urls: set,
) -> tuple[list[dict], bool]:
    """
    Fallback extractor using instaloader CLI + Chrome Profile 1 cookies.
    Used automatically when Apify token is missing or credit < $1.00.
    Same raw_posts output format as extract_via_apify().

    Rate: ~3s between posts. Scrapes up to 300 posts from public profile.
    Saves no files to disk — uses --no-pictures --no-videos --save-metadata
    in a tempdir, then parses JSON sidecar files.
    """
    import subprocess, tempfile, shutil

    total_needed = sum(needed.values())
    if total_needed == 0:
        return [], False

    results_limit = min(max(total_needed * 5, 150), 300)
    print(f"  Fetching @{handle} via instaloader (limit={results_limit})...", flush=True)

    TYPE_MAP = {
        "GraphImage":   "image",
        "GraphVideo":   "video",
        "GraphSidecar": "carousel_slide",
        "Image":        "image",
        "Video":        "video",
        "Sidecar":      "carousel_slide",
    }

    collected: list[dict] = []
    remaining  = dict(needed)
    total_raw  = 0
    profile_exhausted = False

    with tempfile.TemporaryDirectory(prefix="ogz_il_") as tmpdir:
        cmd = [
            INSTALOADER_BIN,
            "--cookiefile", INSTALOADER_COOKIE_FILE,
            "--no-pictures",
            "--no-videos",
            "--no-video-thumbnails",
            "--no-profile-pic",
            "--save-metadata",
            "--no-compress-json",
            "--count", str(results_limit),
            f"@{handle}",
        ]
        try:
            subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=300, cwd=tmpdir, check=False,
            )
        except subprocess.TimeoutExpired:
            print("  instaloader timed out after 300s", flush=True)
            return [], False
        except Exception as e:
            print(f"  instaloader failed: {e}", flush=True)
            return [], False

        # Collect all .json sidecar files — instaloader saves them as:
        #   handle/YYYY-MM-DD_HH-MM-SS_UTC_SHORTCODE.json
        json_files = sorted(Path(tmpdir).rglob("*.json"))
        total_raw  = len(json_files)
        profile_exhausted = total_raw < results_limit

        for jf in json_files:
            if all(v <= 0 for v in remaining.values()):
                break
            try:
                meta = json.loads(jf.read_text())
                node = meta.get("node", meta)  # top-level node, or flat dict

                short_code = (
                    node.get("shortcode")
                    or node.get("shortCode")
                    or jf.stem.rsplit("_", 1)[-1]   # last part of filename
                )
                if not short_code:
                    continue

                source_url = f"https://www.instagram.com/p/{short_code}/"
                if source_url in seen_urls:
                    continue

                typename     = node.get("__typename", "GraphImage")
                content_type = TYPE_MAP.get(typename, "image")
                quota_key    = _ct_to_quota_key(content_type)
                if remaining.get(quota_key, 0) <= 0:
                    continue

                # Timestamp (unix or ISO)
                ts = node.get("taken_at_timestamp") or node.get("timestamp", 0)
                try:
                    ts_int = int(ts)
                    capture_date = datetime.utcfromtimestamp(ts_int).strftime("%Y-%m-%d")
                except (TypeError, ValueError, OSError):
                    capture_date = str(ts)[:10] if ts else datetime.now().strftime("%Y-%m-%d")

                # Caption — two possible locations in instaloader JSON
                caption_raw = ""
                try:
                    caption_raw = (
                        node.get("edge_media_to_caption", {})
                            .get("edges", [{}])[0]
                            .get("node", {})
                            .get("text", "")
                        or node.get("caption_text", "")
                        or node.get("caption", "")
                        or ""
                    )
                except (IndexError, AttributeError):
                    pass
                caption_raw = str(caption_raw)

                # Engagement
                likes    = int(node.get("edge_media_preview_like", {}).get("count", 0)
                               or node.get("edge_liked_by", {}).get("count", 0)
                               or node.get("likesCount", 0) or 0)
                comments = int(node.get("edge_media_to_comment", {}).get("count", 0)
                               or node.get("commentsCount", 0) or 0)

                word_count    = len(caption_raw.split()) if caption_raw else 0
                hashtag_count = len(re.findall(r"#\w+", caption_raw))
                has_emoji     = bool(re.search(
                    r"[\U00010000-\U0010ffff\U00002600-\U000027BF]", caption_raw))

                display_url = node.get("display_url", "")

                collected.append({
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
                    "filename":      f"{short_code}.jpg",
                    "sector":        sector,
                    "handle":        handle,
                    "source_url":    source_url,
                })
                remaining[quota_key] -= 1
            except Exception:
                continue

    print(
        f"  Collected {len(collected)} posts via instaloader "
        f"(raw={total_raw}, exhausted={profile_exhausted})",
        flush=True,
    )
    return collected, profile_exhausted


# ── Apify balance check ────────────────────────────────────────────────────────
def _get_apify_credit() -> float:
    """Return remaining Apify prepaid credit in USD. Returns 999.0 on any error."""
    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        return 0.0
    try:
        import urllib.request
        url = f"https://api.apify.com/v2/users/me?token={token}"
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=8)
        d = json.loads(resp.read()).get("data", {})
        credit = d.get("availablePrepaidCredit")
        if credit is not None:
            return float(credit)
        return 999.0   # unknown — assume OK
    except Exception:
        return 999.0   # on error, let Apify fail naturally (avoids killing on transient)


# ── Smart dispatcher: Apify first, instaloader fallback ───────────────────────
def extract_posts(
    handle: str,
    sector: str,
    needed: dict,
    seen_urls: set,
) -> tuple[list[dict], bool]:
    """
    Try Apify. Auto-fall back to instaloader if:
      • APIFY_TOKEN not set
      • Apify credit < $1.00
      • Apify raises any exception
    """
    token = os.environ.get("APIFY_TOKEN", "")

    if not token:
        print("  APIFY_TOKEN not set — using instaloader fallback", flush=True)
        return extract_via_instaloader(handle, sector, needed, seen_urls)

    credit = _get_apify_credit()
    if credit < 1.0:
        print(f"  Apify credit low (${credit:.2f}) — switching to instaloader", flush=True)
        return extract_via_instaloader(handle, sector, needed, seen_urls)

    try:
        return extract_via_apify(handle, sector, needed, seen_urls)
    except Exception as e:
        print(f"  Apify error ({e}) — falling back to instaloader", flush=True)
        return extract_via_instaloader(handle, sector, needed, seen_urls)


# ── OpenAI Batch classification ───────────────────────────────────────────────
def classify_batch(raw_posts: list[dict]) -> dict[str, dict]:
    """
    Submit all posts to OpenAI Batch API (GPT-4o-mini) for classification.
    Returns {short_code: classification_dict}.
    Cost: ~$0.075/1000 input tokens + $0.30/1000 output tokens (batch pricing).
    """
    import tempfile, io

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in ~/.abraham_env")

    client = openai.OpenAI(api_key=api_key)

    # Build JSONL batch file in memory
    lines = []
    for p in raw_posts:
        lines.append(json.dumps({
            "custom_id": p["short_code"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "max_tokens": 400,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": CLASSIFY_SYSTEM},
                    {"role": "user",   "content": _classify_prompt(
                        p["caption_text"], p["content_type"], p["capture_date"],
                        p["sector"], p["likes"], p["comments"],
                    )},
                ],
                "response_format": {"type": "json_object"},
            },
        }))

    jsonl_bytes = "\n".join(lines).encode("utf-8")
    print(f"  Uploading {len(raw_posts)} posts to OpenAI Batch API...", flush=True)

    # Upload JSONL file
    batch_file = client.files.create(
        file=("batch.jsonl", io.BytesIO(jsonl_bytes), "application/jsonl"),
        purpose="batch",
    )

    # Create batch job
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch_id = batch.id
    print(f"  Batch ID: {batch_id}", flush=True)

    # Poll until complete
    while True:
        batch = client.batches.retrieve(batch_id)
        status = batch.status
        rc = batch.request_counts
        print(
            f"  Status: {status} | "
            f"completed={rc.completed} failed={rc.failed} total={rc.total}",
            flush=True,
        )
        if status == "completed":
            break
        if status in ("failed", "expired", "cancelled"):
            raise RuntimeError(f"OpenAI Batch failed with status: {status}")
        time.sleep(15)

    # Download results
    result_content = client.files.content(batch.output_file_id).read()
    results = {}
    for line in result_content.decode("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            sc   = row["custom_id"]
            body = row.get("response", {}).get("body", {})
            text = (body.get("choices") or [{}])[0].get("message", {}).get("content", "")
            text = re.sub(r"^```(?:json)?\s*", "", text.strip())
            text = re.sub(r"\s*```$", "", text)
            results[sc] = json.loads(text)
        except Exception as e:
            print(f"  ⚠ parse error for {row.get('custom_id','?')}: {e}")

    print(f"  ✓ Classified {len(results)}/{len(raw_posts)} posts", flush=True)
    return results


# ── Write observation JSON ─────────────────────────────────────────────────────
def _get_or_create_account_ulid(handle: str) -> str:
    """Look up account ULID: checks accounts_index.json first, then existing accounts/ JSON files."""
    index = {}
    if ACCOUNTS_INDEX.exists():
        try:
            index = json.loads(ACCOUNTS_INDEX.read_text())
        except Exception:
            pass
    if handle in index:
        return index[handle]

    accounts_dir = BASE / "11_who_to_learn_from" / "accounts"
    for acct_file in accounts_dir.rglob("*.json"):
        try:
            d = json.loads(acct_file.read_text())
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

    lang = cls.get("language", "arabic")
    if lang not in {"arabic", "english", "bilingual", "none"}:
        lang = "arabic"

    compliance = cls.get("overall_compliance", "clean")
    if compliance not in {"clean", "soft_flagged", "hard_blocked"}:
        compliance = "clean"

    eng = cls.get("engagement_potential", "medium")
    if eng not in {"high", "medium", "low"}:
        eng = "medium"

    pq = cls.get("production_quality", "semi_professional")
    if pq not in {"professional", "semi_professional", "ugc", "low"}:
        pq = "semi_professional"

    pattern_matches = [
        {"pattern_slug": slug.lower(), "confidence": "moderate"}
        for slug in (cls.get("pattern_slugs") or [])
        if isinstance(slug, str) and slug.strip()
    ]

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
            "heritage_vs_modern": (
                cls.get("heritage_vs_modern", "neutral")
                if cls.get("heritage_vs_modern") in ("heritage", "modern", "blended", "neutral")
                else "neutral"
            ),
            "free_notes": "",
        },
        "pattern_matches": pattern_matches,
        "quality_assessment": {
            "engagement_potential": eng,
            "production_quality": pq,
        },
        "provenance": {
            "source": "apify_instagram",
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confirmer": "gpt4omini_batch_classification",
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
    if content_type in ("video", "reel"):
        return "video"
    if content_type == "carousel_slide":
        return "carousel"
    return "image"


def count_existing_by_type(handle: str) -> dict:
    counts = {"image": 0, "video": 0, "carousel": 0}
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized", "").lower() != handle.lower():
                continue
            ct  = d.get("content_ref", {}).get("content_type", "")
            key = _ct_to_quota_key(ct)
            counts[key] += 1
        except Exception:
            pass
    return counts


def _load_quota_for_handle(handle: str) -> dict:
    try:
        data = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        for a in data.get("accounts", []):
            if a.get("handle", "").lower() == handle.lower():
                return a.get("quota", DEFAULT_QUOTA)
    except Exception:
        pass
    return DEFAULT_QUOTA


# ── Update target_accounts.json ────────────────────────────────────────────────
def _update_target_status(
    handle: str,
    written_by_type: dict,
    quota: dict,
    force_done: bool = False,
):
    if not TARGET_ACCOUNTS_FILE.exists():
        return
    try:
        data = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        for acct in data.get("accounts", []):
            if acct.get("handle", "").lower() != handle.lower():
                continue
            current  = count_existing_by_type(handle)
            total    = sum(current.values())
            acct["obs_count_actual"] = total
            acct["obs_by_type"]      = current
            quota_met = force_done or all(current.get(k, 0) >= v for k, v in quota.items())
            acct["status"] = "done" if quota_met else "partial"
            if force_done:
                acct["note"] = "Profile exhausted — best-effort quota accepted"
            break
        data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        TARGET_ACCOUNTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  ⚠ Could not update target_accounts.json: {e}")


# ── Dedup ──────────────────────────────────────────────────────────────────────
def _load_existing_source_urls(handle: str) -> set:
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
    parser = argparse.ArgumentParser(
        description="Extract Saudi Instagram account observations via Apify"
    )
    parser.add_argument("--handle",         required=True, help="Instagram handle (without @)")
    parser.add_argument("--sector",         required=True, help="Sector: f_and_b | beauty_personal_care | retail_lifestyle | real_estate")
    parser.add_argument("--quota-image",    type=int, default=None)
    parser.add_argument("--quota-video",    type=int, default=None)
    parser.add_argument("--quota-carousel", type=int, default=None)
    parser.add_argument("--dry-run",        action="store_true")
    args = parser.parse_args()

    handle  = args.handle.lower().lstrip("@")
    sector  = args.sector.lower()
    dry_run = args.dry_run

    quota = _load_quota_for_handle(handle)
    if args.quota_image    is not None: quota["image"]    = args.quota_image
    if args.quota_video    is not None: quota["video"]    = args.quota_video
    if args.quota_carousel is not None: quota["carousel"] = args.quota_carousel

    print(f"\n{'='*60}")
    print(f"  Extracting @{handle} | sector={sector}")
    print(f"  Quota: image={quota['image']}  video={quota['video']}  carousel={quota['carousel']}")
    print(f"{'='*60}\n")

    existing = count_existing_by_type(handle)
    needed   = {k: max(0, quota[k] - existing.get(k, 0)) for k in quota}
    print(f"  Existing: image={existing['image']}  video={existing['video']}  carousel={existing['carousel']}")
    print(f"  Needed:   image={needed['image']}  video={needed['video']}  carousel={needed['carousel']}")

    if sum(needed.values()) == 0:
        print(f"  ✅ @{handle} already meets quota — nothing to extract.")
        _update_target_status(handle, {}, quota)
        sys.exit(0)

    seen_urls = _load_existing_source_urls(handle)
    print(f"  Dedup: {len(seen_urls)} existing source URLs loaded")

    # Smart extractor: Apify primary, instaloader fallback (auto when credit < $1)
    raw_posts, profile_exhausted = extract_posts(handle, sector, needed, seen_urls)

    if dry_run:
        print("\nDRY RUN — sample of collected posts:")
        for p in raw_posts[:5]:
            key = _ct_to_quota_key(p["content_type"])
            print(f"  [{key}] {p['short_code']} | {p['content_type']} | {p['capture_date']} | {p['caption_text'][:50]!r}")
        return

    if not raw_posts:
        print("  No new posts found — profile exhausted, accepting best-effort.")
        _update_target_status(handle, {}, quota, force_done=True)
        sys.exit(0)

    classifications = classify_batch(raw_posts)
    print(f"  Classified {len(classifications)}/{len(raw_posts)} posts")

    account_ulid    = _get_or_create_account_ulid(handle)
    written_by_type = {"image": 0, "video": 0, "carousel": 0}
    quota_remaining = dict(needed)
    errors          = 0

    for raw in raw_posts:
        ct_key = _ct_to_quota_key(raw["content_type"])
        if quota_remaining.get(ct_key, 0) <= 0:
            continue
        sc  = raw["short_code"]
        cls = classifications.get(sc, {})
        try:
            write_observation(raw, cls, account_ulid)
            written_by_type[ct_key] += 1
            quota_remaining[ct_key] -= 1
        except Exception as e:
            print(f"  ✗ {sc}: {e}")
            errors += 1

        if all(v <= 0 for v in quota_remaining.values()):
            break

    _update_target_status(handle, written_by_type, quota, force_done=profile_exhausted)

    total_written = sum(written_by_type.values())
    print(f"\n{'='*60}")
    print(f"Extracted {total_written} observations  |  Errors: {errors}")
    print(f"  image={written_by_type['image']}  video={written_by_type['video']}  carousel={written_by_type['carousel']}")
    if profile_exhausted:
        print(f"  ℹ Profile exhausted — best-effort quota accepted")
    print(f"Account ULID: {account_ulid}")
    print(f"\nNext step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
