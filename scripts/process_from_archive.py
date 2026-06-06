#!/usr/bin/env python3
"""
process_from_archive.py — Convert existing raw archive into obs files.
No Apify. No new extractions. Uses data already on disk.

Reads _raw_archive/{handle}/*_apify_raw.jsonl
Classifies with OpenAI gpt-4o-mini (fast, cheap — ~$0.001/post)
Writes obs files to observations/{sector}/

Usage:
    python3 scripts/process_from_archive.py --handle bathandbodyworksarabia --sector beauty_personal_care
    python3 scripts/process_from_archive.py --all-unprocessed   # process all brands missing obs
    python3 scripts/process_from_archive.py --all-partial       # top up brands with fewer obs than raw posts

Mohamed can verify with:
    python3 scripts/process_from_archive.py --status
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO    = Path(__file__).resolve().parent.parent
RAW_DIR = REPO / "11_who_to_learn_from" / "_raw_archive"
OBS_DIR = REPO / "11_who_to_learn_from" / "observations"

sys.path.insert(0, str(REPO / "scripts"))
from lib.normalize_gpt import normalize_obs_fields
from lib.engagement import calculate_engagement, tier_from_total

SECTOR_FOLDER = {
    "f_and_b":                "f_and_b",
    "beauty_personal_care":   "beauty",
    "retail_lifestyle":       "retail",
    "fashion":                "retail",
    "real_estate":            "real_estate",
    "healthcare_wellness":    "healthcare_wellness",
}

# Brand → sector mapping for --all-unprocessed
BRAND_SECTORS = {
    "bathandbodyworksarabia": "beauty_personal_care",
    "lcwaikiki":              "fashion",
    "ajmalperfumes":          "beauty_personal_care",
    "namshi":                 "fashion",
    "myfitness.sa":           "healthcare_wellness",
    "zara":                   "fashion",
    "fitnessfirstme":         "healthcare_wellness",
    "kyancafe":               "f_and_b",
    "hmksa":                  "fashion",
    # add more as needed
}


# ─────────────────────────────────────────────────────────────
# Load env
# ─────────────────────────────────────────────────────────────
def load_env():
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip('"\'')
    return env


# ─────────────────────────────────────────────────────────────
# Load raw posts from archive
# ─────────────────────────────────────────────────────────────
def load_raw_posts(handle: str) -> list[dict]:
    handle_dir = RAW_DIR / handle
    if not handle_dir.exists():
        return []
    posts = []
    for jsonl in sorted(handle_dir.rglob("*_apify_raw.jsonl")):
        for line in jsonl.read_text().splitlines():
            if line.strip():
                try:
                    posts.append(json.loads(line))
                except Exception:
                    pass
    return posts


# ─────────────────────────────────────────────────────────────
# Get existing obs source URLs (dedup)
# ─────────────────────────────────────────────────────────────
def get_existing_urls(handle: str) -> set[str]:
    urls = set()
    for f in OBS_DIR.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized", "").lower() == handle.lower():
                url = d.get("content_ref", {}).get("source_url", "")
                if url:
                    urls.add(url)
        except Exception:
            pass
    return urls


# ─────────────────────────────────────────────────────────────
# Classify a batch of posts with OpenAI
# ─────────────────────────────────────────────────────────────
CLASSIFY_PROMPT = """Classify this Instagram post. Reply with JSON only, no markdown.

Caption: {caption}
Likes: {likes} | Content type: {content_type} | Sector: {sector}

JSON fields:
- composition_style: one of product_hero_closeup|lifestyle_integrated|editorial|text_dominant|overhead_spread
- lighting: one of natural|warm_studio|flat_bright|dramatic_moody|golden_hour|studio
- setting: one of restaurant|retail_store|studio|outdoor|home|office|other
- visual_complexity: one of minimal|simple|moderate|complex
- human_presence: one of full|partial|none
- tone: one of celebratory|urgent|informative|aspirational|warm|playful|proud|humorous
- language: one of arabic|english|bilingual|none
- occasion: one of evergreen|ramadan|eid_al_fitr|eid_al_adha|national_day|founding_day|riyadh_season|jeddah_season|hajj_season|white_friday|singles_day|null
- heritage_vs_modern: one of heritage|modern|blended|neutral
- engagement_potential: one of high|medium|low
- production_quality: one of professional|semi_professional|ugc|low
- overall_compliance: one of clean|soft_flagged|hard_blocked
- pattern_slugs: list of 0-2 short slug strings describing content pattern"""


def classify_posts(posts: list[dict], sector: str, api_key: str) -> list[dict | None]:
    """Classify a list of posts. Returns list of classification dicts (or None on error)."""
    import openai
    client = openai.OpenAI(api_key=api_key)
    results = []
    for post in posts:
        caption  = (post.get("caption_text") or "")[:400]
        likes    = post.get("likes", 0)
        ctype    = post.get("content_type", "image")
        prompt   = CLASSIFY_PROMPT.format(caption=caption, likes=likes, content_type=ctype, sector=sector)
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0,
            )
            raw_text = resp.choices[0].message.content.strip()
            # Strip markdown if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"```[a-z]*\n?", "", raw_text).strip("` ")
            cls = json.loads(raw_text)
            results.append(cls)
        except Exception as e:
            results.append(None)
    return results


# ─────────────────────────────────────────────────────────────
# Write one obs file
# ─────────────────────────────────────────────────────────────
def write_obs(post: dict, cls: dict, sector: str, account_ulid: str) -> Path | None:
    from ulid import ULID

    sector_folder = SECTOR_FOLDER.get(sector, sector)
    out_dir = OBS_DIR / sector_folder
    out_dir.mkdir(parents=True, exist_ok=True)

    handle     = post["handle"]
    obs_ulid   = str(ULID())
    source_url = post.get("source_url", "")
    likes      = post.get("likes", 0)
    comments   = post.get("comments", 0)

    # Validate/clean GPT fields
    lang = cls.get("language", "arabic") if cls else "arabic"
    if lang not in {"arabic", "english", "bilingual", "none"}: lang = "arabic"
    compliance = cls.get("overall_compliance", "clean") if cls else "clean"
    if compliance not in {"clean", "soft_flagged", "hard_blocked"}: compliance = "clean"
    eng = cls.get("engagement_potential", "medium") if cls else "medium"
    if eng not in {"high", "medium", "low"}: eng = "medium"
    pq = cls.get("production_quality", "semi_professional") if cls else "semi_professional"
    if pq not in {"professional", "semi_professional", "ugc", "low"}: pq = "semi_professional"
    hvmod = cls.get("heritage_vs_modern", "neutral") if cls else "neutral"
    if hvmod not in {"heritage", "modern", "blended", "neutral"}: hvmod = "neutral"

    caption_text = post.get("caption_text", "")
    word_count   = len(caption_text.split()) if caption_text else 0
    hashtag_count = len(re.findall(r'#\S+', caption_text))
    has_emoji    = bool(re.search(r'[\U0001F300-\U0001FFFF]', caption_text))

    occasion_raw = (cls.get("occasion") if cls else None) or post.get("occasion")
    VALID_OCCASIONS = {"evergreen","ramadan","eid_al_fitr","eid_al_adha","national_day",
                       "founding_day","riyadh_season","jeddah_season","hajj_season",
                       "white_friday","singles_day"}
    occasion = occasion_raw if occasion_raw in VALID_OCCASIONS else "evergreen"

    obs = {
        "observation_ulid":            obs_ulid,
        "schema_version":              1,
        "account_handle_normalized":   handle,
        "account_ulid":                account_ulid,
        "sector":                      sector,
        "occasion":                    occasion,
        "content_ref": {
            "filename":               post.get("filename", f"{post.get('shortcode','')}.jpg"),
            "platform":               "instagram",
            "content_type":           post.get("content_type", "image"),
            "capture_date":           post.get("capture_date", ""),
            "source_url":             source_url,
            "display_url":            post.get("display_url", ""),
            "video_url":              post.get("video_url", ""),
            "likes_count":            likes,
            "comments_count":         comments,
            "engagement_total":       likes + comments,
        },
        "visual_observations": {
            "composition_style":      (cls.get("composition_style","") if cls else ""),
            "lighting":               (cls.get("lighting","") if cls else ""),
            "setting":                (cls.get("setting","") if cls else ""),
            "visual_complexity":      (cls.get("visual_complexity","moderate") if cls else "moderate"),
            "human_presence":         (True if cls and cls.get("human_presence") in ("full","partial")
                                       else False if cls and cls.get("human_presence") == "none"
                                       else None),
        },
        "voice_observations": {
            "caption_text":    caption_text,
            "language":        lang,
            "caption_word_count": word_count,
            "hashtag_count":   hashtag_count,
            "has_emoji":       has_emoji,
            "tone":            (cls.get("tone","informative") if cls else "informative"),
        },
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags":            [],
            "overall_compliance":    compliance,
        },
        "cultural_notes": {
            "occasion_relevance": occasion,
            "hospitality_cues":   [],
            "heritage_vs_modern": hvmod,
            "free_notes":         "",
        },
        "pattern_matches": [],
        "quality_assessment": {
            "engagement_potential":       eng,
            "production_quality":         pq,
            "engagement_method":          "apify_raw_archive",
        },
        "provenance": {
            "source":    f"apify_raw_archive:@{handle}",
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confirmer": "process_from_archive.py+gpt4omini",
            "confidence": "inferred",
            "scope":      f"brand:{re.sub(r'[^a-z0-9_]','_', handle.lower())}",
        },
    }

    # Normalize enums
    try:
        normalize_obs_fields(obs)
    except Exception:
        pass

    # Content hash dedup
    caption_head = caption_text[:100]
    content_hash = hashlib.md5(f"{source_url}|{obs['content_ref']['content_type']}|{caption_head}".encode()).hexdigest()
    hash_file = out_dir / ".content_hashes"
    seen = set(hash_file.read_text().strip().split("\n")) if hash_file.exists() else set()
    if content_hash in seen:
        return None
    seen.add(content_hash)
    hash_file.write_text("\n".join(seen))

    out = out_dir / f"{obs_ulid}.json"
    out.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
    return out


# ─────────────────────────────────────────────────────────────
# Process one brand
# ─────────────────────────────────────────────────────────────
def process_brand(handle: str, sector: str, api_key: str, limit: int = 200) -> int:
    from ulid import ULID

    print(f"\n@{handle} ({sector})")
    raw_posts = load_raw_posts(handle)
    if not raw_posts:
        print(f"  No raw archive found")
        return 0

    existing_urls = get_existing_urls(handle)
    print(f"  Raw archive: {len(raw_posts)} posts | Existing obs: {len(existing_urls)}")

    # Filter to new posts only
    new_posts = []
    for post in raw_posts:
        sc  = post.get("shortCode") or post.get("shortcode") or ""
        url = f"https://www.instagram.com/p/{sc}/"
        if url in existing_urls or not sc:
            continue
        caption = str(post.get("caption") or "")
        likes    = int(post.get("likesCount") or post.get("likes_count") or 0)
        comments = int(post.get("commentsCount") or post.get("comments_count") or 0)

        raw_type = post.get("type", "Image")
        TYPE_MAP = {"GraphImage":"image","GraphVideo":"video","GraphSidecar":"carousel_slide",
                    "Image":"image","Video":"video","Sidecar":"carousel_slide"}
        content_type = TYPE_MAP.get(raw_type, "image")
        day_map = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        ts = post.get("timestamp","")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(str(ts)[:19]) if ts else _dt.now()
            capture_date = dt.strftime("%Y-%m-%d")
        except Exception:
            capture_date = str(ts)[:10] if ts else ""

        new_posts.append({
            "handle":       handle,
            "sector":       sector,
            "source_url":   url,
            "filename":     f"{sc}.jpg",
            "content_type": content_type,
            "capture_date": capture_date,
            "caption_text": caption,
            "likes":        likes,
            "comments":     comments,
            "display_url":  post.get("displayUrl",""),
            "video_url":    post.get("videoUrl",""),
        })
        if len(new_posts) >= limit:
            break

    if not new_posts:
        print(f"  All posts already processed")
        return 0

    print(f"  Processing {len(new_posts)} new posts with OpenAI...", flush=True)
    account_ulid = str(ULID())
    classifications = classify_posts(new_posts, sector, api_key)

    written = 0
    for post, cls in zip(new_posts, classifications):
        out = write_obs(post, cls or {}, sector, account_ulid)
        if out:
            written += 1

    print(f"  ✅ Wrote {written} new obs files")
    return written


# ─────────────────────────────────────────────────────────────
# Status report
# ─────────────────────────────────────────────────────────────
def status_report():
    obs_by_brand = defaultdict(int)
    for f in OBS_DIR.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            h = d.get("account_handle_normalized","")
            if h: obs_by_brand[h] += 1
        except Exception:
            pass

    raw_brands = {}
    for jsonl in RAW_DIR.rglob("*_apify_raw.jsonl"):
        brand = jsonl.parts[-3]
        posts = len([l for l in jsonl.read_text().splitlines() if l.strip()])
        raw_brands[brand] = max(raw_brands.get(brand, 0), posts)

    print(f"\n{'Brand':<30} {'Raw':>6} {'Obs':>6} {'Gap':>6}")
    print("─"*50)
    for brand in sorted(raw_brands, key=lambda b: -(raw_brands[b] - obs_by_brand.get(b,0))):
        raw = raw_brands[brand]
        obs = obs_by_brand.get(brand, 0)
        gap = raw - obs
        if raw > 10:
            flag = " ← process" if gap > 20 and obs == 0 else (" ← top up" if gap > 50 else "")
            print(f"  {brand:<28} {raw:>6} {obs:>6} {gap:>6}{flag}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle", help="Single brand handle")
    parser.add_argument("--sector", help="Sector for single brand")
    parser.add_argument("--all-unprocessed", action="store_true", help="Process all brands with 0 obs")
    parser.add_argument("--all-partial",     action="store_true", help="Top up brands with partial obs")
    parser.add_argument("--status",          action="store_true", help="Show status report only")
    args = parser.parse_args()

    if args.status:
        status_report()
        return

    env = load_env()
    api_key = env.get("OPENAI_API_KEY","")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in ~/.abraham_env")
        sys.exit(1)

    total_written = 0

    if args.handle:
        if not args.sector:
            sector = BRAND_SECTORS.get(args.handle.lower())
            if not sector:
                print(f"❌ --sector required for @{args.handle}")
                sys.exit(1)
        else:
            sector = args.sector
        total_written += process_brand(args.handle.lower(), sector, api_key)

    elif args.all_unprocessed:
        obs_by_brand = defaultdict(int)
        for f in OBS_DIR.rglob("*.json"):
            try:
                d = json.loads(f.read_text())
                h = d.get("account_handle_normalized","")
                if h: obs_by_brand[h] += 1
            except Exception:
                pass
        for jsonl in sorted(RAW_DIR.rglob("*_apify_raw.jsonl")):
            brand = jsonl.parts[-3]
            if obs_by_brand.get(brand, 0) == 0 and brand in BRAND_SECTORS:
                sector = BRAND_SECTORS[brand]
                posts = len([l for l in jsonl.read_text().splitlines() if l.strip()])
                if posts > 10:
                    total_written += process_brand(brand, sector, api_key)

    elif args.all_partial:
        obs_by_brand = defaultdict(int)
        for f in OBS_DIR.rglob("*.json"):
            try:
                d = json.loads(f.read_text())
                h = d.get("account_handle_normalized","")
                if h: obs_by_brand[h] += 1
            except Exception:
                pass
        for jsonl in sorted(RAW_DIR.rglob("*_apify_raw.jsonl")):
            brand = jsonl.parts[-3]
            if brand not in BRAND_SECTORS:
                continue
            raw_count = len([l for l in jsonl.read_text().splitlines() if l.strip()])
            obs_count = obs_by_brand.get(brand, 0)
            if raw_count > 10 and obs_count > 0 and obs_count < raw_count * 0.6:
                sector = BRAND_SECTORS[brand]
                total_written += process_brand(brand, sector, api_key)

    else:
        parser.print_help()
        print("\nRun --status to see what's available")
        return

    print(f"\n{'='*50}")
    print(f"Total obs written: {total_written}")
    if total_written > 0:
        print(f"Next: python3 scripts/expand_template_library.py")
        print(f"      python3 scripts/verify_ship_ready.py")


if __name__ == "__main__":
    main()
