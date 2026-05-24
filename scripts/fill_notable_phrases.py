#!/usr/bin/env python3
"""
fill_notable_phrases.py
Extract notable_phrases from existing caption_text for obs that have
captions but no notable_phrases.

No AI required — uses text parsing:
  - Removes hashtags, emoji, phone/time/location markers
  - Extracts 1-3 key Arabic/English phrases (3+ word sequences)
  - Takes the first meaningful line(s) as the core phrase

Safe to re-run: skips obs that already have notable_phrases filled.
Output: logs/fill_notable_phrases_report.json
"""
import json
import re
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

# Arabic Unicode range
AR_RE = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿ]+')

# Things to strip before phrase extraction
STRIP_PATTERNS = [
    re.compile(r'#\S+'),                    # hashtags
    re.compile(r'https?://\S+'),            # URLs
    re.compile(r'@\w+'),                    # mentions
    re.compile(r'\b9\d{8,}\b'),             # phone numbers
    re.compile(r'\b\d{1,2}:\d{2}[اعماً ]*(?:م|ص|صباحاً|مساءً)?\b', re.IGNORECASE),  # times
    re.compile(r'📍.*'),                    # location markers
    re.compile(r'[📞📱☎️🕔🕑🕒🕓🕕🕖🕗🕘🕙🕚🕛].*'),  # phone/time emoji lines
    re.compile(r'للحجوزات.*', re.DOTALL),   # booking info block
    re.compile(r'للتواصل.*', re.DOTALL),    # contact info block
    re.compile(r'للطلب.*', re.DOTALL),      # order info block
    re.compile(r'\b(يوجد|الموقع|العنوان|فرع|التواصل)\b.*', re.IGNORECASE),
]

# Emoji pattern
EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def _clean(text: str) -> str:
    for pattern in STRIP_PATTERNS:
        text = pattern.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_phrases(text: str) -> list[str]:
    """Extract 1-3 notable phrases from cleaned caption text."""
    cleaned = _clean(text)
    if not cleaned:
        return []

    phrases = []

    # Split into lines, filter blank
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]

    for line in lines:
        # Skip lines that are just punctuation or very short
        words = line.split()
        if len(words) < 2:
            continue
        # Must contain Arabic or English words (not just numbers/symbols)
        if not re.search(r'[a-zA-Z؀-ۿ]', line):
            continue
        # Skip lines that are mainly numbers
        if sum(c.isdigit() for c in line) > len(line) * 0.5:
            continue
        # Clean trailing punctuation slightly
        line = line.strip('.،,؟?!…')
        if len(line) > 5:
            phrases.append(line)
        if len(phrases) >= 3:
            break

    # Deduplicate while preserving order
    seen = set()
    result = []
    for p in phrases:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            result.append(p)

    return result[:3]


def main():
    updated  = 0
    skipped  = 0
    no_cap   = 0
    empty    = 0

    results  = []

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        d  = json.loads(obs_file.read_text())
        vo = d.get("voice_observations") or {}

        caption = vo.get("caption_text")
        if not caption:
            no_cap += 1
            continue

        existing = vo.get("notable_phrases")
        if existing:  # list with items
            skipped += 1
            continue

        phrases = _extract_phrases(caption)
        if not phrases:
            empty += 1
            continue

        vo["notable_phrases"] = phrases
        d["voice_observations"] = vo
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        results.append({
            "file": obs_file.name,
            "phrases": phrases,
            "caption_preview": caption[:60],
        })

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_notable_phrases_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_caption": no_cap, "empty_after_clean": empty,
                    "results": results}, ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("NOTABLE PHRASES FILL COMPLETE")
    print(f"  Updated        : {updated}")
    print(f"  Already set    : {skipped}")
    print(f"  No caption     : {no_cap}")
    print(f"  Empty after clean: {empty}")
    print()
    print("  Sample phrases extracted:")
    for r in results[:6]:
        print(f"    {r['phrases']}")
    print()
    print("  Output → logs/fill_notable_phrases_report.json")


if __name__ == "__main__":
    main()
