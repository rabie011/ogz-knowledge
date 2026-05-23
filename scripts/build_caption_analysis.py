#!/usr/bin/env python3
"""
build_caption_analysis.py
Analyse caption features vs engagement:
  - CTA presence (does having a call-to-action help or hurt?)
  - Caption length (word count buckets vs engagement)
  - Bilingual vs Arabic-only vs Visual-only captions
  - Hashtag density vs engagement
  - Question-as-caption hook vs statement
Output: logs/caption_analysis.json
"""
import json, re
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}

# CTA signal words (Arabic + English)
CTA_KEYWORDS = [
    "اطلب", "اطلبي", "احجز", "احجزي", "زور", "زوري", "اضغط", "اضغطي",
    "شارك", "شاركي", "علّق", "علّقي", "اتبع", "اتبعي", "تابع", "تابعي",
    "order", "book", "visit", "click", "share", "comment", "follow",
    "link in bio", "لينك في البايو", "order now", "اطلب الآن",
    "احجز الآن", "تسوق الآن", "shop now",
]

# Bilingual signal: Arabic + Latin chars
ARABIC_RANGE = re.compile(r'[؀-ۿ]')
LATIN_RANGE  = re.compile(r'[a-zA-Z]{3,}')   # 3+ consecutive latin chars = English word


def caption_features(text: str) -> dict:
    if not text or not text.strip():
        return {
            "has_cta": False,
            "word_count": 0,
            "length_bucket": "empty",
            "is_bilingual": False,
            "is_arabic_only": False,
            "has_hashtags": False,
            "hashtag_count": 0,
            "opens_with_question": False,
            "has_emoji": False,
            "arabic_char_ratio": 0.0,
        }

    text_lower = text.lower()

    # CTA detection
    has_cta = any(kw in text_lower for kw in CTA_KEYWORDS)

    # Word count (rough — split on whitespace)
    words = text.split()
    word_count = len(words)
    if word_count == 0:
        length_bucket = "empty"
    elif word_count <= 5:
        length_bucket = "micro"      # 1-5 words
    elif word_count <= 15:
        length_bucket = "short"      # 6-15
    elif word_count <= 40:
        length_bucket = "medium"     # 16-40
    elif word_count <= 80:
        length_bucket = "long"       # 41-80
    else:
        length_bucket = "very_long"  # 80+

    # Language mix
    has_arabic = bool(ARABIC_RANGE.search(text))
    has_latin  = bool(LATIN_RANGE.search(text))
    is_bilingual = has_arabic and has_latin
    is_arabic_only = has_arabic and not has_latin

    # Arabic character ratio
    arabic_chars = len(ARABIC_RANGE.findall(text))
    total_chars  = max(1, len(text.replace(" ", "")))
    arabic_ratio = round(arabic_chars / total_chars, 3)

    # Hashtags
    hashtags = re.findall(r'#\w+', text)
    has_hashtags  = bool(hashtags)
    hashtag_count = len(hashtags)

    # Question hook (first 20 chars)
    opens_with_question = text.strip()[:40].count("?") > 0 or text.strip()[:40].count("؟") > 0

    # Emoji (Unicode emoji range)
    has_emoji = bool(re.search(
        r'[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U0001FA00-\U0001FA9F]', text
    ))

    return {
        "has_cta": has_cta,
        "word_count": word_count,
        "length_bucket": length_bucket,
        "is_bilingual": is_bilingual,
        "is_arabic_only": is_arabic_only,
        "has_hashtags": has_hashtags,
        "hashtag_count": min(hashtag_count, 30),
        "opens_with_question": opens_with_question,
        "has_emoji": has_emoji,
        "arabic_char_ratio": arabic_ratio,
    }


def agg(label):
    return {"label": label, "count": 0, "high_count": 0, "eng_sum": 0.0}


def record(bucket, is_high, eng):
    bucket["count"]      += 1
    bucket["high_count"] += is_high
    bucket["eng_sum"]    += eng


def summarise(bucket):
    n = bucket["count"]
    if n == 0:
        return {"count": 0, "high_engagement_rate": 0, "avg_engagement": 0, "verdict": "no_data"}
    rate = round(bucket["high_count"] / n, 3)
    avg  = round(bucket["eng_sum"] / n, 3)
    verdict = (
        "strong_positive" if rate >= 0.70 else
        "positive"        if rate >= 0.55 else
        "neutral"         if rate >= 0.40 else
        "weak"            if rate >= 0.25 else
        "avoid"
    )
    return {"count": n, "high_engagement_rate": rate, "avg_engagement": avg, "verdict": verdict}


def main():
    # Dimension buckets
    cta_yes   = agg("cta_present")
    cta_no    = agg("cta_absent")

    length_buckets = {k: agg(k) for k in ["empty", "micro", "short", "medium", "long", "very_long"]}

    bilingual  = agg("bilingual")
    arabic_only= agg("arabic_only")
    latin_mix  = agg("other_language_mix")

    hash_yes   = agg("hashtags_present")
    hash_no    = agg("hashtags_absent")
    hash_dense = agg("hashtags_5plus")

    question   = agg("opens_with_question")
    statement  = agg("statement_opening")

    emoji_yes  = agg("emoji_present")
    emoji_no   = agg("emoji_absent")

    # Caption vs visual_only
    has_caption_text  = agg("has_caption_text")
    visual_only_reg   = agg("visual_only_register")

    total = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        qa       = data.get("quality_assessment", {}) or {}
        eng_raw  = str(qa.get("engagement_potential", "") or "").lower()
        eng      = ENG_MAP.get(eng_raw, 0.5)
        is_high  = 1 if eng >= 0.75 else 0

        # Caption text — stored in voice_observations.notable_phrases or content_ref.caption
        cr       = data.get("content_ref", {}) or {}
        caption  = cr.get("caption", "") or ""
        if not caption:
            # Try voice observations for any text signal
            vo = data.get("voice_observations", {}) or {}
            register = str(vo.get("register", "") or "").lower()
            if "visual_only" in register or "visual" in register:
                record(visual_only_reg, is_high, eng)
                continue  # skip text analysis for visual-only

        record(has_caption_text, is_high, eng)
        feats = caption_features(caption)

        # CTA
        record(cta_yes if feats["has_cta"] else cta_no, is_high, eng)

        # Length
        lb = feats["length_bucket"]
        record(length_buckets.get(lb, length_buckets["medium"]), is_high, eng)

        # Language
        if feats["is_bilingual"]:
            record(bilingual, is_high, eng)
        elif feats["is_arabic_only"]:
            record(arabic_only, is_high, eng)
        else:
            record(latin_mix, is_high, eng)

        # Hashtags
        record(hash_yes if feats["has_hashtags"] else hash_no, is_high, eng)
        if feats["hashtag_count"] >= 5:
            record(hash_dense, is_high, eng)

        # Question hook
        record(question if feats["opens_with_question"] else statement, is_high, eng)

        # Emoji
        record(emoji_yes if feats["has_emoji"] else emoji_no, is_high, eng)

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "note": "Caption text is sparse in this corpus — many obs were extracted without full caption text. Results reflect relative patterns within the subset that has caption data.",
        "cta_vs_no_cta": {
            "cta_present": summarise(cta_yes),
            "cta_absent":  summarise(cta_no),
        },
        "caption_length": {k: summarise(v) for k, v in length_buckets.items()},
        "language_mix": {
            "bilingual_ar_en":  summarise(bilingual),
            "arabic_only":      summarise(arabic_only),
            "other_lang":       summarise(latin_mix),
        },
        "hashtag_usage": {
            "hashtags_present": summarise(hash_yes),
            "hashtags_absent":  summarise(hash_no),
            "hashtag_5plus":    summarise(hash_dense),
        },
        "opening_hook": {
            "question_hook":    summarise(question),
            "statement_hook":   summarise(statement),
        },
        "emoji_usage": {
            "emoji_present": summarise(emoji_yes),
            "emoji_absent":  summarise(emoji_no),
        },
        "has_caption_vs_visual_only": {
            "has_caption_text": summarise(has_caption_text),
            "visual_only":      summarise(visual_only_reg),
        },
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "caption_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Caption analysis across {total} observations")
    print(f"\nCTA effect:")
    print(f"  CTA present: {out['cta_vs_no_cta']['cta_present']}")
    print(f"  CTA absent:  {out['cta_vs_no_cta']['cta_absent']}")
    print(f"\nCaption length effect:")
    for bucket, stats in out["caption_length"].items():
        if stats["count"] > 0:
            print(f"  {bucket:<12} n={stats['count']:3d} | high_eng={int(stats['high_engagement_rate']*100)}% | {stats['verdict']}")
    print(f"\nLanguage mix effect:")
    for lang, stats in out["language_mix"].items():
        if stats["count"] > 0:
            print(f"  {lang:<20} n={stats['count']:3d} | high_eng={int(stats['high_engagement_rate']*100)}%")
    print(f"\nOpening hook effect:")
    for hook, stats in out["opening_hook"].items():
        if stats["count"] > 0:
            print(f"  {hook:<20} n={stats['count']:3d} | high_eng={int(stats['high_engagement_rate']*100)}%")
    print(f"\nOutput: logs/caption_analysis.json")


if __name__ == "__main__":
    main()
