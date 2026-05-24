#!/usr/bin/env python3
"""
extract_new_accounts.py
Download + extract observations for new accounts not yet in the corpus.

For each target account (read from accounts/ directory):
  1. Download posts via instaloader (up to --count images)
  2. Move media to _inbox/@{handle}/media/
  3. Extract pass1 metadata from instaloader JSON
  4. Call Claude API (haiku) with vision to generate observation_v1 records
  5. Save to observations/{sector}/

Priority: accounts with largest follower_count_bucket first.

Safe to re-run: skips accounts that already have >= MIN_OBS_ALREADY observations,
  and skips images already extracted for a partial account.

Usage:
  python3 scripts/extract_new_accounts.py
  python3 scripts/extract_new_accounts.py --sector beauty
  python3 scripts/extract_new_accounts.py --sector retail --count 15
  python3 scripts/extract_new_accounts.py --max-accounts 5
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE        = Path(__file__).resolve().parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
ACC_ROOT    = BASE / "11_who_to_learn_from" / "accounts"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
INSTALOADER = "/opt/homebrew/bin/instaloader"
SLEEP_BETWEEN_DOWNLOADS = 10   # seconds between posts in same account
SLEEP_BETWEEN_ACCOUNTS  = 30   # seconds between accounts
MIN_OBS_ALREADY = 5            # skip account if it already has this many obs

# Follower bucket → priority score (higher = download first)
BUCKET_PRIORITY = {
    ">1m": 6, "500k-1m": 5, "100k-500k": 4, "50k-100k": 3,
    "10k-50k": 2, "<10k": 1,
}

# ── EXTRACTION SYSTEM PROMPT ─────────────────────────────────────────────────
EXTRACTION_SYSTEM = """You are an expert visual analyst for OGZ Studios, a Saudi Arabian creative agency.
Your job: analyze a Saudi brand Instagram image and return a structured JSON observation record.

## Forbidden list (memorize — check every image):

### HARD BLOCKS (severe violations):
- left_hand_serving: Left hand used as PRIMARY serving hand (food/drink/gifts)
- sole_of_foot_visible: Soles of feet/shoes directed at a person
- shoes_on_seating: Shoes on seating surfaces/majlis cushions
- alcohol_product: Any alcohol bottle, wine glass, beer imagery
- pork_product: Bacon, ham, pork imagery
- gambling_imagery: Casino chips, slot machines, playing cards in gambling context
- eating_during_ramadan_daylight: Eating/drinking in Ramadan daytime
- cross_gender_physical_contact_non_mahram: Handshake/embrace between unrelated opposite genders
- prayer_as_commercial_backdrop: Prayer used as promotional set-dressing
- saudi_flag_misuse: Saudi flag on disposable items, upside-down, overlaid on faces
- kaaba_or_mecca_as_backdrop: Kaaba/Hajj imagery as brand backdrop

### MODERATE violations:
- western_palm_up_beckon: Curling finger "come here" gesture
- pointing_finger_at_person: Index finger pointed directly at a person
- thumbs_up_to_elder_or_religious: Thumbs up at religious/elder figures
- ok_circle_gesture: Western "OK" circle hand gesture
- other_faith_religious_symbols: Cross, Star of David, Buddha as decoration
- smoking_family_context: Smoking in family-context content

## 40 patterns (match if present):
Visual: overhead_tabletop_spread, product_hero_close_up, pattern_repeat_flatlay, steam_and_texture_macro, architectural_framing, cultural_object_hero, lifestyle_environment_integration, behind_the_scenes_production, duo_product_comparison, storytelling_sequence_grid
Voice: arabic_casual_mood_trigger, bilingual_brand_voice, heritage_storytelling_hook, curiosity_gap_question, community_pride_statement, urgency_without_pressure, user_generated_amplification, occasion_specific_greeting, poetic_phrasing_najdi, call_to_action_soft_invite
Content: product_launch_reveal, seasonal_campaign_graphic, event_collab_announcement, giveaway_contest_post, behind_scenes_reel_teaser, educational_ingredient_spotlight, brand_milestone_post, menu_expansion_announcement, cultural_moment_tie_in, influencer_takeover_post
Occasion: national_day_93_94, ramadan_iftar_warmth, eid_premium_gift, expo_2030_pride, women_empowerment_day, global_event_saudi_lens, world_food_heritage_day, winter_comfort_cozy, founding_day_celebration, seasonal_summer_heat

## Output format (return ONLY valid JSON, no markdown):
{
  "composition_style": "string",
  "lighting": "string",
  "color_palette_dominant": ["color1", "color2"],
  "props_visible": ["prop1"],
  "setting": "string",
  "characters": {
    "count": 0,
    "gender_presentation": null,
    "wardrobe_notes": null,
    "gesture_notes": null
  },
  "text_overlays": [{"language": "arabic", "content_summary": "summary"}],
  "notable_visual_elements": ["element1"],
  "voice": {
    "language": "arabic",
    "dialect_detected": null,
    "register": "casual",
    "tone": "warm",
    "notable_phrases": [],
    "call_to_action_present": false
  },
  "compliance": {
    "hard_blocks": [],
    "soft_flags": []
  },
  "cultural_notes": {
    "regional_orientation": "Najdi | Hejazi | Eastern | general_saudi | null",
    "occasion_relevance": null,
    "hospitality_cues": [],
    "heritage_vs_modern": "heritage | modern | blended | neutral",
    "free_notes": null
  },
  "pattern_matches": [
    {"pattern_slug": "overhead_tabletop_spread", "confidence": "strong", "notes": "why"}
  ],
  "production_quality": "professional | semi_professional | ugc | low",
  "brand_consistency": "strong | moderate | weak",
  "engagement_potential": "high | medium | low"
}"""

EXTRACTION_USER = """Account: @{handle} — {sector} brand in Saudi Arabia
Description: {description}
Watch for: {what_to_watch}
Filename: {filename}
Caption (if available): {caption}

Analyze this image and return the JSON observation. Return ONLY the JSON."""

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ulid_offset = 0

def make_ulid() -> str:
    global _ulid_offset
    t = int(time.time() * 1000) + _ulid_offset
    _ulid_offset += 1
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


# ── ACCOUNT DISCOVERY ─────────────────────────────────────────────────────────

def _obs_count_for_account(handle_norm: str) -> int:
    count = 0
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized") == handle_norm:
                count += 1
        except Exception:
            pass
    return count


def _existing_filenames_for_account(handle_norm: str, sector: str) -> set[str]:
    used = set()
    obs_dir = OBS_ROOT / sector
    if not obs_dir.exists():
        return used
    for f in obs_dir.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized") == handle_norm:
                fn = d.get("content_ref", {}).get("filename", "")
                if fn:
                    used.add(fn)
                    used.add(fn.rsplit(".", 1)[0].rstrip("_0123456789"))
        except Exception:
            pass
    return used


def load_accounts(sector_filter: str | None = None) -> list[dict]:
    """Load all unextracted accounts, sorted by priority."""
    accounts = []
    sectors = ["beauty", "retail", "f_and_b"] if not sector_filter else [sector_filter]

    for sector in sectors:
        sector_dir = ACC_ROOT / sector
        if not sector_dir.exists():
            continue
        for acc_file in sorted(sector_dir.glob("*.json")):
            try:
                data = json.loads(acc_file.read_text())
            except Exception:
                continue

            handle = data.get("account_handle_internal", "").strip()
            norm   = data.get("account_handle_normalized", "")
            bucket = data.get("profile", {}).get("follower_count_bucket", "<10k")

            # Skip blanks, dashes, or obviously bad handles
            if not handle or handle in ("---", "-", "_", "") or len(handle) < 3:
                continue

            obs_count = _obs_count_for_account(norm)
            if obs_count >= MIN_OBS_ALREADY:
                continue  # already extracted enough

            # Build description from account data
            high_themes  = data.get("high_engagement_themes", [])
            vis_traits   = data.get("distinctive_visual_traits", [])
            voice_traits = data.get("distinctive_voice_traits", [])
            patterns     = [p.get("pattern_name","") for p in data.get("content_patterns_observed", [])]

            description = f"{sector} brand, {bucket} followers"
            if high_themes:
                description += f". High-eng themes: {', '.join(high_themes[:2])}"

            what_to_watch = []
            if vis_traits:
                what_to_watch.append(f"Visual: {', '.join(vis_traits[:2])}")
            if voice_traits:
                what_to_watch.append(f"Voice: {', '.join(voice_traits[:1])}")
            if patterns:
                what_to_watch.append(f"Patterns: {', '.join(patterns[:2])}")
            what_to_watch_str = " | ".join(what_to_watch) or "Saudi cultural authenticity, brand consistency"

            accounts.append({
                "handle": handle,
                "handle_norm": norm,
                "account_ulid": data.get("account_ulid", make_ulid()),
                "sector": sector.replace("_", "-"),  # f_and_b → f-and-b for obs
                "sector_dir": sector,
                "description": description,
                "what_to_watch": what_to_watch_str,
                "bucket": bucket,
                "priority": BUCKET_PRIORITY.get(bucket, 1),
                "obs_count": obs_count,
            })

    # Sort by priority (descending), then handle alphabetically
    accounts.sort(key=lambda a: (-a["priority"], a["handle"]))
    return accounts


# ── INSTALOADER DOWNLOAD ──────────────────────────────────────────────────────

def _download_account(handle: str, count: int) -> Path | None:
    """Download account posts via instaloader. Returns media dir or None."""
    media_dir = INBOX / f"@{handle}" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # Check already downloaded
    existing = list(media_dir.glob("*.jpg")) + list(media_dir.glob("*.mp4"))
    if len(existing) >= count:
        print(f"    Already have {len(existing)} files in media/, skipping download")
        return media_dir

    tmp_dir = INBOX / f"@{handle}" / "_download_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        INSTALOADER,
        "--no-profile-pic",
        "--no-stories",
        "--no-compress-json",
        "--no-captions",            # captions in JSON already
        f"--count={count}",
        f"--filename-pattern={{shortcode}}",
        "--", handle,
    ]

    print(f"    Downloading @{handle} (up to {count} posts)...")
    try:
        result = subprocess.run(
            cmd, cwd=str(tmp_dir),
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0 and "404" in result.stderr:
            print(f"    ⚠  404 — account may be private or deleted")
            # Create a SKIPPED marker
            (INBOX / f"@{handle}" / "SKIPPED.json").write_text(
                json.dumps({"reason": "404_or_private", "handle": handle}, indent=2)
            )
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return None
    except subprocess.TimeoutExpired:
        print(f"    ⚠  Download timed out for @{handle}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    # Move media files to media_dir, move JSON to pass1_dir
    pass1_dir = INBOX / f"@{handle}" / "pass1"
    pass1_dir.mkdir(exist_ok=True)

    moved_images = 0
    handle_subdir = tmp_dir / handle  # instaloader creates a subdir with the handle name
    search_dir = handle_subdir if handle_subdir.exists() else tmp_dir

    for f in search_dir.rglob("*"):
        if f.suffix in (".jpg", ".webp", ".png"):
            dst = media_dir / f.name
            if not dst.exists():
                shutil.move(str(f), str(dst))
                moved_images += 1
        elif f.suffix == ".json" and not f.name.startswith("_"):
            dst = pass1_dir / f.name
            if not dst.exists():
                shutil.move(str(f), str(dst))
        elif f.suffix == ".mp4":
            dst = media_dir / f.name
            if not dst.exists():
                shutil.move(str(f), str(dst))

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"    Downloaded {moved_images} images to media/")
    return media_dir if moved_images > 0 else None


# ── CAPTION EXTRACTION ────────────────────────────────────────────────────────

def _load_captions(handle: str) -> dict[str, str]:
    """Load captions from pass1 JSON files (instaloader metadata)."""
    captions = {}
    pass1_dir = INBOX / f"@{handle}" / "pass1"
    if not pass1_dir.exists():
        return captions
    for jf in pass1_dir.glob("*.json"):
        try:
            d = json.loads(jf.read_text())
            # Instaloader puts caption in 'edge_media_to_caption' or 'caption'
            cap = (
                d.get("caption") or
                (d.get("edge_media_to_caption", {}).get("edges", [{}])[0]
                 .get("node", {}).get("text", "")) or ""
            )
            captions[jf.stem] = cap.strip()
        except Exception:
            pass
    return captions


# ── CLAUDE EXTRACTION ─────────────────────────────────────────────────────────

def _detect_media_type(path: Path) -> str:
    with open(path, "rb") as f:
        header = f.read(12)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"


def _load_image_b64(path: Path) -> tuple[str, str]:
    with open(path, "rb") as f:
        data = f.read()
    return base64.standard_b64encode(data).decode(), _detect_media_type(path)


def _extract_one(client, img_path: Path, account: dict, caption: str, obs_ulid: str) -> dict:
    handle   = account["handle"]
    filename = img_path.name
    sector   = account["sector_dir"]  # f_and_b, beauty, retail

    # Content type detection
    content_type = "image"
    if "_" in img_path.stem and img_path.stem.split("_")[-1].isdigit():
        content_type = "carousel_slide"
    elif img_path.suffix == ".mp4":
        content_type = "video"

    img_b64, media_type = _load_image_b64(img_path)

    user_msg = EXTRACTION_USER.format(
        handle=handle,
        sector=sector.replace("_", " "),
        description=account["description"],
        what_to_watch=account["what_to_watch"],
        filename=filename,
        caption=caption or "(no caption available)",
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=EXTRACTION_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                {"type": "text", "text": user_msg},
            ],
        }],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    ex = json.loads(raw)

    # ── normalise helpers ────────────────────────────────────────────────────
    _VALID_LANGS = {"arabic", "english", "bilingual", "none"}
    _VALID_CONF  = {"strong", "moderate", "weak"}

    def _norm_lang(v: str) -> str:
        v = v.lower()
        if any(x in v for x in ("none", "visual", "no_text", "no text", "silent")): return "none"
        if any(x in v for x in ("mixed", "bilingual", "both")): return "bilingual"
        if "english" in v: return "english"
        return "arabic"

    def _norm_conf(v: str) -> str:
        v = v.lower()
        if v in ("high", "strong"): return "strong"
        if v in ("low", "weak"):    return "weak"
        return "moderate"

    def _norm_qual(v: str) -> str:
        v = v.lower()
        if v in ("professional", "semi_professional", "ugc", "low"): return v
        if "professional" in v: return "professional"
        return "semi_professional"

    def _norm_eng(v: str) -> str:
        v = v.lower()
        if v in ("high", "medium", "low"): return v
        return "medium"

    def _norm_bc(v: str) -> str:
        v = v.lower()
        if v in ("strong", "moderate", "weak"): return v
        return "moderate"

    def _norm_hvm(v: str) -> str:
        v = v.lower()
        if v in ("heritage", "modern", "blended", "neutral"): return v
        return "neutral"

    chars = ex.get("characters", {})
    chars_out: dict = {"count": chars.get("count", 0)}
    for k in ("gender_presentation", "wardrobe_notes", "gesture_notes"):
        if chars.get(k): chars_out[k] = chars[k]

    voice = ex.get("voice", {})
    voice_out: dict = {}
    if voice.get("language"):
        lang = voice["language"]
        voice_out["language"] = lang if lang in _VALID_LANGS else _norm_lang(lang)
    for k in ("dialect_detected", "register", "tone", "notable_phrases", "call_to_action_present"):
        if k in voice and voice[k] is not None:
            voice_out[k] = voice[k]

    compliance = ex.get("compliance", {})
    hard_blocks = []
    for hb in compliance.get("hard_blocks", []):
        hard_blocks.append({
            "forbidden_list_id": hb.get("id", ""),
            "entry_name": hb.get("name", ""),
            "severity": hb.get("severity", "moderate"),
            "evidence_description": hb.get("evidence", "observed violation"),
        })
    soft_flags = []
    for sf in compliance.get("soft_flags", []):
        soft_flags.append({"flag_type": sf.get("flag_type", "cultural_sensitivity"), "description": sf.get("description", "")})

    overall = "hard_blocked" if hard_blocks else ("soft_flagged" if soft_flags else "clean")

    cn = ex.get("cultural_notes", {})
    cn_out: dict = {
        "heritage_vs_modern": _norm_hvm(cn.get("heritage_vs_modern", "neutral")),
    }
    for k in ("regional_orientation_detected", "occasion_relevance", "hospitality_cues", "free_notes"):
        val = cn.get(k if k != "regional_orientation_detected" else "regional_orientation")
        if val:
            cn_out[k] = val

    pattern_matches = []
    for pm in ex.get("pattern_matches", []):
        slug = pm.get("pattern_slug", "")
        if slug:
            conf = pm.get("confidence", "moderate")
            pattern_matches.append({
                "pattern_slug": slug,
                "confidence": conf if conf in _VALID_CONF else _norm_conf(conf),
                "notes": pm.get("notes"),
            })

    obs = {
        "observation_ulid": obs_ulid,
        "schema_version": 1,
        "account_handle_normalized": account["handle_norm"],
        "account_ulid": account["account_ulid"],
        "sector": sector,
        "content_ref": {
            "filename": filename,
            "platform": "instagram",
            "content_type": content_type,
        },
        "visual_observations": {
            "composition_style": ex.get("composition_style", "unspecified"),
            "color_palette_dominant": ex.get("color_palette_dominant", []),
            "props_visible": ex.get("props_visible", []),
            "characters_visible": chars_out,
            "text_overlays": ex.get("text_overlays", []),
            "notable_visual_elements": ex.get("notable_visual_elements", []),
        },
        "compliance_check": {
            "hard_blocks_triggered": hard_blocks,
            "soft_flags": soft_flags,
            "overall_compliance": overall,
        },
        "cultural_notes": cn_out,
        "pattern_matches": pattern_matches,
        "quality_assessment": {
            "production_quality": _norm_qual(ex.get("production_quality", "semi_professional")),
            "brand_consistency_with_account": _norm_bc(ex.get("brand_consistency", "moderate")),
            "engagement_potential": _norm_eng(ex.get("engagement_potential", "medium")),
        },
        "provenance": {
            "source": f"instagram:@{handle}:{img_path.stem}",
            "date_added": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": f"sector:{sector}",
        },
    }

    # optional fields
    if ex.get("lighting"):
        obs["visual_observations"]["lighting"] = ex["lighting"]
    if ex.get("setting"):
        obs["visual_observations"]["setting"] = ex["setting"]
    if voice_out:
        obs["voice_observations"] = voice_out

    return obs


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", choices=["beauty", "retail", "f_and_b"], default=None,
                        help="Restrict to one sector (default: all)")
    parser.add_argument("--count", type=int, default=20,
                        help="Posts per account to download (default 20)")
    parser.add_argument("--max-accounts", type=int, default=10,
                        help="Max accounts to process in this run (default 10)")
    parser.add_argument("--extract-count", type=int, default=15,
                        help="Images per account to pass through Claude (default 15)")
    args = parser.parse_args()

    # Load Anthropic API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        env_path = Path.home() / ".abraham_env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("ERROR: No ANTHROPIC_API_KEY found — set it or add to ~/.abraham_env")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    accounts = load_accounts(args.sector)
    print(f"\n{'='*60}")
    print(f"  NEW ACCOUNT EXTRACTOR")
    print(f"  Sector filter : {args.sector or 'all'}")
    print(f"  Accounts found: {len(accounts)} (not yet extracted)")
    print(f"  Max this run  : {args.max_accounts}")
    print(f"  Posts to DL   : {args.count} per account")
    print(f"  Extract count : {args.extract_count} images per account")
    print(f"{'='*60}\n")

    if not accounts:
        print("Nothing to do — all accounts already extracted.")
        return

    accounts_processed = 0
    total_obs_written  = 0
    results_log        = []

    for account in accounts[:args.max_accounts]:
        handle   = account["handle"]
        sector   = account["sector_dir"]
        norm     = account["handle_norm"]
        bucket   = account["bucket"]

        print(f"\n{'─'*55}")
        print(f"  Account : @{handle}")
        print(f"  Sector  : {sector}  [{bucket}]")
        print(f"  Norm    : {norm}")
        print(f"{'─'*55}")

        # Check for SKIPPED marker
        skip_marker = INBOX / f"@{handle}" / "SKIPPED.json"
        if skip_marker.exists():
            print(f"  ⏭  SKIPPED (marker file exists)")
            continue

        # ── Step 1: Download ─────────────────────────────────────────────────
        media_dir = _download_account(handle, args.count)
        if media_dir is None:
            print(f"  ❌ Download failed — skipping")
            results_log.append({"handle": handle, "status": "download_failed"})
            if accounts_processed > 0:
                time.sleep(SLEEP_BETWEEN_ACCOUNTS)
            continue

        # ── Step 2: Load captions ────────────────────────────────────────────
        captions = _load_captions(handle)
        print(f"  Captions loaded: {len(captions)}")

        # ── Step 3: Select images ────────────────────────────────────────────
        used = _existing_filenames_for_account(norm, sector)
        all_imgs = sorted([
            f for f in media_dir.glob("*.jpg")
            if "_thumb" not in f.name
            and f.name not in used
            and f.stem.rstrip("_0123456789") not in used
        ])

        if not all_imgs:
            print(f"  ⏭  No new images to extract (all already done)")
            results_log.append({"handle": handle, "status": "nothing_new"})
            continue

        random.seed(42)
        random.shuffle(all_imgs)
        selected = all_imgs[:args.extract_count]
        print(f"  Images available: {len(all_imgs)}, extracting: {len(selected)}")

        # ── Step 4: Extract with Claude ──────────────────────────────────────
        obs_dir = OBS_ROOT / sector
        obs_dir.mkdir(parents=True, exist_ok=True)

        success = 0
        errors  = 0

        for i, img_path in enumerate(selected, 1):
            stem    = img_path.stem.rstrip("_0123456789")
            caption = captions.get(stem, captions.get(img_path.stem, ""))

            print(f"  [{i:>2}/{len(selected)}] {img_path.name:<40}", end="  ", flush=True)

            try:
                obs_ulid = make_ulid()
                obs = _extract_one(client, img_path, account, caption, obs_ulid)

                out_path = obs_dir / f"{obs_ulid}.json"
                out_path.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
                print(f"✓  {obs['quality_assessment']['production_quality']}")
                success += 1
                total_obs_written += 1

                if i < len(selected):
                    time.sleep(SLEEP_BETWEEN_DOWNLOADS)

            except Exception as e:
                print(f"ERROR: {e}")
                errors += 1

        results_log.append({
            "handle": handle, "sector": sector, "norm": norm,
            "status": "done", "success": success, "errors": errors,
        })
        accounts_processed += 1

        print(f"\n  ✅ @{handle} done — {success} obs written, {errors} errors")

        if accounts_processed < args.max_accounts and account != accounts[min(args.max_accounts, len(accounts)) - 1]:
            print(f"  Sleeping {SLEEP_BETWEEN_ACCOUNTS}s before next account...")
            time.sleep(SLEEP_BETWEEN_ACCOUNTS)

    # ── Summary ──────────────────────────────────────────────────────────────
    LOGS.mkdir(exist_ok=True)
    (LOGS / "new_account_extraction.json").write_text(
        json.dumps({"results": results_log, "total_obs_written": total_obs_written}, ensure_ascii=False, indent=2)
    )

    print(f"\n{'='*60}")
    print(f"  NEW ACCOUNT EXTRACTION COMPLETE")
    print(f"  Accounts processed : {accounts_processed}")
    print(f"  Total obs written  : {total_obs_written}")
    print(f"  Log → logs/new_account_extraction.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
