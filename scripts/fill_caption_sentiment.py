#!/usr/bin/env python3
"""
fill_caption_sentiment.py
Classify caption sentiment (positive / negative / neutral) for obs
with caption_text, using keyword lexicon — no API needed.

Writes: voice_observations.caption_sentiment
  "positive" | "negative" | "neutral" | "question"

Output: logs/fill_caption_sentiment_report.json
"""
import json
import re
from collections import Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"

# ── Lexicons ─────────────────────────────────────────────────────────
POSITIVE_AR = [
    "رائع", "ممتاز", "لذيذ", "جميل", "مميز", "حلو", "روعة", "رائحة",
    "أفضل", "جديد", "خاص", "طازج", "احتفال", "فرح", "سعادة", "نجاح",
    "محبوب", "استثنائي", "إبداع", "أصيل", "شهي", "مذاق", "يستحق",
    "تجربة", "نكهة", "جودة", "طعم", "عرض", "هدية", "مفاجأة", "جديد",
    "ترقية", "يحب", "ناعم", "إشراقة", "جميل", "حلاوة", "سعيد",
]
POSITIVE_EN = [
    "love", "amazing", "best", "fresh", "new", "special", "delicious",
    "great", "perfect", "beautiful", "wonderful", "excellent", "enjoy",
    "happy", "celebrate", "glowing", "smooth", "soft", "gorgeous",
]
NEGATIVE_AR = [
    "سيء", "مشكلة", "خطأ", "صعب", "مؤلم", "ضعيف", "تعبان",
    "مرفوض", "فاشل", "انتهى", "أزمة", "قلق",
]
NEGATIVE_EN = [
    "bad", "problem", "fail", "wrong", "terrible", "awful", "disappoint",
]
QUESTION_PATTERNS = [
    re.compile(r'[؟?]'),
    re.compile(r'\b(كيف|هل|ماذا|متى|أين|لماذا|من|ما)\b'),
    re.compile(r'\b(how|what|when|where|why|who|which)\b', re.I),
]


def _classify(text: str) -> str:
    if not text:
        return "neutral"
    t = text.lower()

    # Question check first
    for pat in QUESTION_PATTERNS:
        if pat.search(t):
            return "question"

    pos = sum(1 for w in POSITIVE_AR + POSITIVE_EN if w in t)
    neg = sum(1 for w in NEGATIVE_AR + NEGATIVE_EN if w in t)

    if pos > neg and pos >= 1: return "positive"
    if neg > pos and neg >= 1: return "negative"
    return "neutral"


def _ensure_schema_field():
    schema = json.loads(SCHEMA_PATH.read_text())
    vo_props = schema["properties"]["voice_observations"]["properties"]
    if "caption_sentiment" not in vo_props:
        vo_props["caption_sentiment"] = {
            "type": ["string", "null"],
            "enum": ["positive", "negative", "neutral", "question", None],
            "description": "Lexicon-based sentiment of caption text"
        }
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added caption_sentiment")


def main():
    _ensure_schema_field()

    updated  = 0
    skipped  = 0
    no_cap   = 0
    dist     = Counter()

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        d  = json.loads(obs_file.read_text())
        vo = d.get("voice_observations") or {}

        caption = vo.get("caption_text")
        if not caption:
            no_cap += 1
            continue
        if vo.get("caption_sentiment") is not None:
            skipped += 1
            continue

        sentiment = _classify(caption)
        vo["caption_sentiment"] = sentiment
        d["voice_observations"] = vo
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        dist[sentiment] += 1

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_caption_sentiment_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_caption": no_cap,
                    "sentiment_distribution": dict(dist.most_common())},
                   ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("CAPTION SENTIMENT FILL COMPLETE")
    print(f"  Updated    : {updated}")
    print(f"  Skipped    : {skipped}")
    print(f"  No caption : {no_cap}")
    print()
    print("  Distribution:")
    for s, c in dist.most_common():
        print(f"    {s:<12} {c:>3}  {'█' * c}")
    print()
    print("  Output → logs/fill_caption_sentiment_report.json")


if __name__ == "__main__":
    main()
