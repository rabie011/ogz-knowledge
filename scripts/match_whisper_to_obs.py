#!/usr/bin/env python3
"""
match_whisper_to_obs.py
Recover 669 unmatched Whisper transcriptions → write voiceover_text to obs.

whisper_unmatched.json has entries like:
  {"file": "11_who_to_learn_from/_inbox/@barnscoffee/media/ABC123.mp4",
   "shortcode": "ABC123", "language": "ar", "word_count": 12, "text": "..."}

obs files have content_ref.source_url like:
  "https://www.instagram.com/p/ABC123/"

This script matches shortcode → obs and writes voiceover_text.
Safe to re-run: skips obs where voiceover_text already set.
"""
import json
import re
from pathlib import Path

BASE         = Path(__file__).resolve().parent.parent
OBS_ROOT     = BASE / "11_who_to_learn_from" / "observations"
LOGS         = BASE / "logs"
UNMATCHED_F  = LOGS / "whisper_unmatched.json"


def _build_shortcode_index() -> dict:
    """Map shortcode → obs_file path from source_url fields."""
    index = {}
    for f in OBS_ROOT.rglob("*.json"):
        try:
            data = json.loads(f.read_text())
            url = (data.get("content_ref") or {}).get("source_url", "")
            m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
            if m:
                index[m.group(1)] = f
        except Exception:
            pass
    return index


def main():
    if not UNMATCHED_F.exists():
        print("No whisper_unmatched.json found — nothing to do.")
        return

    unmatched = json.loads(UNMATCHED_F.read_text())
    print(f"Whisper unmatched entries: {len(unmatched)}")

    index = _build_shortcode_index()
    print(f"Obs with source_url shortcodes: {len(index)}")

    matched    = 0
    written    = 0
    skipped    = 0
    no_match   = 0
    still_unmatched = []

    for entry in unmatched:
        sc   = entry.get("shortcode", "")
        text = entry.get("text", "").strip()
        lang = entry.get("language", "")
        wc   = entry.get("word_count", 0)

        obs_file = index.get(sc)
        if not obs_file:
            no_match += 1
            still_unmatched.append(entry)
            continue

        matched += 1

        # Check if already filled
        data = json.loads(obs_file.read_text())
        vo   = data.setdefault("voice_observations", {})
        if vo.get("voiceover_text") is not None:
            skipped += 1
            continue

        # Write voiceover_text
        vo["voiceover_text"] = text

        # Update has_voiceover and language if missing
        audio = vo.setdefault("audio_strategy", {})
        if audio.get("has_voiceover") is None:
            audio["has_voiceover"] = wc > 3
        if wc > 3 and not audio.get("voiceover_language"):
            lang_map = {"ar": "arabic", "en": "english", "fr": "french"}
            audio["voiceover_language"] = lang_map.get(lang, lang)

        obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        written += 1
        print(f"  ✓ {sc}  {lang}  {wc}w → {obs_file.name}")

    # Update unmatched file with only truly unmatched entries
    UNMATCHED_F.write_text(json.dumps(still_unmatched, ensure_ascii=False, indent=2))

    print()
    print("=" * 55)
    print("WHISPER MATCH COMPLETE")
    print(f"  Total unmatched entries : {len(unmatched)}")
    print(f"  Matched to obs          : {matched}")
    print(f"  Written (new)           : {written}")
    print(f"  Skipped (already set)   : {skipped}")
    print(f"  No shortcode match      : {no_match}")
    print(f"  Still unmatched         : {len(still_unmatched)}")


if __name__ == "__main__":
    main()
