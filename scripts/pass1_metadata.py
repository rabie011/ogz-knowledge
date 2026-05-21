#!/usr/bin/env python3
"""
Phase 0b: Pass 1 — Metadata extraction from JSON (no images needed).

Extracts Layer F (meta) + Layer G (caption) + engagement analysis for each
of the 25 selected posts per pilot account. Writes partial observation
records to _inbox/@{handle}/pass1/ (intermediate format, not observation_v1).

Observation_v1 records are assembled after Pass 2 (visual) is complete.

Usage:
  python3 scripts/pass1_metadata.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ulid import ULID

REPO_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = REPO_ROOT / "11_who_to_learn_from" / "_inbox"

PILOT_ACCOUNTS = ["barnscoffee", "aseeb.najd", "riyadhfood", "altazaj_fakieh"]

ARABIC_RANGE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
ENGLISH_RANGE = re.compile(r"[a-zA-Z]")
HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
MENTION_RE = re.compile(r"@(\w+)", re.UNICODE)
EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
    r"☀-⛿✀-➿⭐❤️]+"
)

NAJDI_MARKERS = [
    "ايش", "وش", "كذا", "حيل", "زين", "يبي", "يبغى", "ابي", "ذي", "ذا",
    "هذي", "عيال", "خشة", "مشب", "دحين", "الحين", "ذحين", "قهوة", "دلة",
    "بخور", "مجلس", "مشاوي", "كبسة", "مطبق", "قرصان", "جريش",
]
HEJAZI_MARKERS = [
    "كده", "بس", "لسه", "دي", "دا", "يلا", "اوكي", "حبيبي",
    "طيب", "شكرا", "يعطيك", "فول", "تميس", "سليقة", "مضبي",
]

CTA_PATTERNS_AR = [
    r"رابط\s*ال(بايو|لينك)",
    r"اطلب\s*(الان|الحين|من)",
    r"زور(وا|ونا)",
    r"سجل\s*(الان|الحين)",
    r"احجز",
    r"جرب(وا)?",
    r"تعال(وا)?",
    r"شارك(ونا)?",
    r"فعل\s*التنبيهات",
    r"اضغط",
    r"حمل",
    r"تابع(ونا)?",
]
CTA_PATTERNS_EN = [
    r"link\s*in\s*bio",
    r"order\s*now",
    r"visit\s*us",
    r"book\s*now",
    r"try\s*(it|our)",
    r"come\s*to",
    r"share\s*with",
    r"tap\s*(the|to)",
    r"download",
    r"follow\s*us",
    r"swipe\s*(up|left|right)",
    r"click\s*(the|here)",
    r"dm\s*(us|for)",
    r"comment\s*(below|your)",
    r"tag\s*(a\s*friend|someone)",
]


def detect_language(text: str) -> str:
    """Detect primary language of text."""
    if not text.strip():
        return "none"
    ar_count = len(ARABIC_RANGE.findall(text))
    en_count = len(ENGLISH_RANGE.findall(text))
    total = ar_count + en_count
    if total == 0:
        return "none"
    ar_ratio = ar_count / total
    if ar_ratio > 0.7:
        return "arabic"
    if ar_ratio < 0.3:
        return "english"
    return "bilingual"


def detect_dialect(text: str) -> str | None:
    """Detect Saudi dialect markers in Arabic text."""
    lower = text.lower()
    najdi_hits = sum(1 for m in NAJDI_MARKERS if m in lower)
    hejazi_hits = sum(1 for m in HEJAZI_MARKERS if m in lower)
    if najdi_hits >= 2 and najdi_hits > hejazi_hits:
        return "najdi"
    if hejazi_hits >= 2 and hejazi_hits > najdi_hits:
        return "hejazi"
    if najdi_hits >= 1 or hejazi_hits >= 1:
        return "saudi_colloquial"
    if ARABIC_RANGE.search(text):
        return "msa_or_undetected"
    return None


def detect_cta(text: str) -> bool:
    """Check if caption contains a call to action."""
    lower = text.lower()
    for pat in CTA_PATTERNS_AR + CTA_PATTERNS_EN:
        if re.search(pat, lower):
            return True
    return False


def extract_hashtags(text: str) -> list[dict]:
    """Extract hashtags with language detection."""
    tags = HASHTAG_RE.findall(text)
    result = []
    seen = set()
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in seen:
            continue
        seen.add(tag_lower)
        lang = detect_language(tag)
        result.append({"tag": tag, "language": lang})
    return result


def analyze_caption(caption: str) -> dict:
    """Full caption analysis — Layer G."""
    language = detect_language(caption)
    dialect = detect_dialect(caption)
    hashtags = extract_hashtags(caption)
    mentions = MENTION_RE.findall(caption)
    emojis = EMOJI_RE.findall(caption)
    has_cta = detect_cta(caption)

    words = re.findall(r"\S+", caption)
    lines = [l for l in caption.split("\n") if l.strip()]

    return {
        "language": language,
        "dialect_detected": dialect,
        "caption_length_chars": len(caption),
        "caption_length_words": len(words),
        "caption_lines": len(lines),
        "hashtags": hashtags,
        "hashtag_count": len(hashtags),
        "hashtag_languages": dict(Counter(h["language"] for h in hashtags)),
        "mentions": mentions,
        "mention_count": len(mentions),
        "emoji_count": len(emojis),
        "has_cta": has_cta,
        "has_caption": len(caption.strip()) > 0,
    }


def compute_engagement(post: dict, followers: int) -> dict:
    """Compute engagement metrics for a single post."""
    likes = post.get("likes", 0)
    comments = post.get("comments_count", 0)
    plays = post.get("play_count") or 0
    views = post.get("view_count") or 0
    total = likes + comments

    eng_rate = (total / max(followers, 1)) * 100 if followers else 0

    ts = post.get("timestamp", 0)
    hour = None
    dow = None
    if ts:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        hour = (dt.hour + 3) % 24  # Convert UTC to Riyadh (UTC+3)
        dow = dt.strftime("%A")

    return {
        "likes": likes,
        "comments": comments,
        "engagement_total": total,
        "engagement_rate_pct": round(eng_rate, 3),
        "play_count": plays if plays else None,
        "view_count": views if views else None,
        "post_hour_riyadh": hour,
        "post_day_of_week": dow,
    }


def extract_layer_f(post: dict) -> dict:
    """Extract Layer F (meta) from post JSON."""
    ct = "image"
    mt = post.get("media_type")
    pt = post.get("product_type", "")
    if post.get("is_carousel") or mt == 8:
        ct = "carousel"
    elif pt == "clips":
        ct = "reel"
    elif post.get("is_video") or mt == 2:
        ct = "video"

    return {
        "shortcode": post["shortcode"],
        "post_id": post.get("id"),
        "post_date": post.get("date"),
        "timestamp": post.get("timestamp"),
        "format": ct,
        "product_type": post.get("product_type"),
        "media_type": mt,
        "media_count": post.get("media_count", 1),
        "location": post.get("location"),
        "location_id": post.get("location_id"),
        "tagged_users": post.get("tagged_users", []),
        "is_paid_partnership": post.get("is_paid_partnership", False),
        "has_audio": post.get("has_audio"),
        "accessibility_caption": post.get("accessibility_caption"),
    }


def process_account(handle: str) -> dict | None:
    """Process one account's Pass 1 extraction."""
    inbox = INBOX_DIR / f"@{handle}"
    queue_path = inbox / "extraction_queue.json"

    if not queue_path.exists():
        print(f"  SKIP: no extraction_queue.json — run preprocess_inbox.py first")
        return None

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    summary_path = inbox / "account_summary.json"
    acct = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    followers = acct.get("profile", {}).get("followers", 0)

    pass1_dir = inbox / "pass1"
    pass1_dir.mkdir(exist_ok=True)

    posts = queue["posts"]
    all_engagements = []

    for post in posts:
        sc = post["shortcode"]
        caption = post.get("caption", "")

        layer_f = extract_layer_f(post)
        layer_g = analyze_caption(caption)
        engagement = compute_engagement(post, followers)
        all_engagements.append(engagement["engagement_total"])

        record = {
            "observation_ulid": str(ULID()),
            "pass": 1,
            "handle": handle,
            "account_handle_normalized": queue.get("account_handle_normalized"),
            "account_ulid": queue.get("account_ulid"),
            "sector": "f_and_b",
            "shortcode": sc,
            "layer_f": layer_f,
            "layer_g": layer_g,
            "engagement": engagement,
            "media_files": post.get("media_files_on_disk", []),
            "content_type": post.get("content_type", "image"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        out = pass1_dir / f"{sc}.json"
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    all_engagements.sort(reverse=True)
    for post in posts:
        sc = post["shortcode"]
        out = pass1_dir / f"{sc}.json"
        rec = json.loads(out.read_text(encoding="utf-8"))
        eng = rec["engagement"]["engagement_total"]
        rank = all_engagements.index(eng)
        pct = round((1 - rank / max(len(all_engagements) - 1, 1)) * 100, 1)
        rec["engagement"]["percentile_in_selection"] = pct
        out.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")

    for post in queue["posts"]:
        post["pass1_status"] = "done"
    queue_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

    langs = Counter()
    dialects = Counter()
    cta_count = 0
    for post in posts:
        sc = post["shortcode"]
        rec = json.loads((pass1_dir / f"{sc}.json").read_text(encoding="utf-8"))
        g = rec["layer_g"]
        langs[g["language"]] += 1
        if g["dialect_detected"]:
            dialects[g["dialect_detected"]] += 1
        if g["has_cta"]:
            cta_count += 1

    return {
        "handle": handle,
        "posts_processed": len(posts),
        "followers": followers,
        "languages": dict(langs),
        "dialects": dict(dialects),
        "cta_rate": f"{cta_count}/{len(posts)}",
        "avg_engagement_rate": round(
            sum(
                compute_engagement(p, followers)["engagement_rate_pct"]
                for p in posts
            )
            / len(posts),
            2,
        ),
    }


def main() -> int:
    print("Phase 0b: Pass 1 — Metadata extraction\n")

    results = []
    for handle in PILOT_ACCOUNTS:
        print(f"Processing @{handle}...")
        result = process_account(handle)
        if result:
            results.append(result)
            print(f"  {result['posts_processed']} posts → pass1/")
            print(f"  Languages: {result['languages']}")
            print(f"  Dialects: {result['dialects']}")
            print(f"  CTA rate: {result['cta_rate']}")
            print(f"  Avg engagement: {result['avg_engagement_rate']}%")
        print()

    total = sum(r["posts_processed"] for r in results)
    print(f"Done: {total} pass1 records across {len(results)} accounts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
