#!/usr/bin/env python3
"""
run_whisper_extraction.py
Run OpenAI Whisper on all local video files in _inbox/
to extract voiceover text, confirm has_voiceover, and detect language.

For obs-matched videos: writes results back to the observation JSON.
  - voice_observations.voiceover_text          (new field — spoken words)
  - voice_observations.audio_strategy.has_voiceover
  - voice_observations.audio_strategy.voiceover_language

For unmatched videos (crumblcookiespr, riyadhfood):
  writes to logs/whisper_unmatched.json for future reference.

Model: "small" — good Arabic accuracy, runs in ~20-40s per video on CPU.
       Change to "medium" for better accuracy (slower).

Safe to re-run: skips obs where voiceover_text is already filled.

Usage:
  python3 scripts/run_whisper_extraction.py
  python3 scripts/run_whisper_extraction.py --model medium   # better Arabic
"""
import json
import re
import sys
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
VIDEO_TYPES = {"video", "reel"}
MODEL_NAME  = "small"

# Parse --model arg
for i, arg in enumerate(sys.argv[1:]):
    if arg == "--model" and i + 1 < len(sys.argv) - 1:
        MODEL_NAME = sys.argv[i + 2]


def _load_obs_index() -> dict:
    """Build shortcode → obs_path index from all video obs with source_url."""
    index = {}
    for obs_file in OBS_ROOT.rglob("*.json"):
        data = json.loads(obs_file.read_text())
        cr   = data.get("content_ref") or {}
        ct   = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
        if m:
            index[m.group(1)] = obs_file
    return index


def _already_done(obs_file: Path) -> bool:
    data = json.loads(obs_file.read_text())
    vo   = data.get("voice_observations") or {}
    return vo.get("voiceover_text") is not None


def _write_whisper_result(obs_file: Path, result: dict):
    """Write whisper result into the observation JSON."""
    data     = json.loads(obs_file.read_text())
    vo       = data.setdefault("voice_observations", {})
    audio    = vo.setdefault("audio_strategy", {})

    text     = result.get("text", "").strip()
    language = result.get("language", "")
    segments = result.get("segments", [])

    # Determine if there's actual speech (not just noise/music)
    words_spoken = len(text.split()) > 3

    vo["voiceover_text"] = text if text else ""

    # Only update audio_strategy if not already confirmed
    if audio.get("has_voiceover") is None:
        audio["has_voiceover"] = words_spoken
    if words_spoken and not audio.get("voiceover_language"):
        lang_map = {"ar": "arabic", "en": "english", "fr": "french"}
        audio["voiceover_language"] = lang_map.get(language, language)

    obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    try:
        import whisper
    except ImportError:
        print("ERROR: whisper not installed. Run: pip install openai-whisper")
        sys.exit(1)

    print(f"Loading Whisper model: {MODEL_NAME}")
    model = whisper.load_model(MODEL_NAME)
    print(f"Model loaded. Processing videos...\n")

    obs_index = _load_obs_index()

    # Collect all local videos
    all_videos = sorted(INBOX.rglob("*.mp4"))
    print(f"Total local videos: {len(all_videos)}")
    print(f"Obs-matched shortcodes: {len(obs_index)}")
    print()

    matched_done   = 0
    matched_skip   = 0
    unmatched_done = 0
    errors         = 0
    unmatched_results = []

    for i, mp4 in enumerate(all_videos, 1):
        stem = mp4.stem
        if "_" in stem and len(stem.split("_")[-1]) > 8:
            stem = stem.split("_")[-1]

        obs_file = obs_index.get(stem)
        label    = f"@{mp4.parent.parent.name}/{stem}"

        # Skip if obs already has voiceover_text
        if obs_file and _already_done(obs_file):
            print(f"[{i:>3}/{len(all_videos)}] {label:<40} SKIP (done)")
            matched_skip += 1
            continue

        print(f"[{i:>3}/{len(all_videos)}] {label:<40} transcribing...", end="", flush=True)

        try:
            # Transcribe — hint Arabic for Saudi accounts
            hint_lang = None
            if "crumbl" not in str(mp4).lower():
                hint_lang = "ar"

            options = {}
            if hint_lang:
                options["language"] = hint_lang

            result = model.transcribe(str(mp4), **options)
            text   = result.get("text", "").strip()
            lang   = result.get("language", "?")
            wc     = len(text.split()) if text else 0

            if obs_file:
                _write_whisper_result(obs_file, result)
                matched_done += 1
                print(f"  ✓ {lang}  {wc}w")
            else:
                unmatched_results.append({
                    "file": str(mp4.relative_to(BASE)),
                    "shortcode": stem,
                    "language": lang,
                    "word_count": wc,
                    "text": text,
                })
                unmatched_done += 1
                print(f"  ✓ {lang}  {wc}w  [unmatched]")

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

    # Save unmatched results
    if unmatched_results:
        out_path = LOGS / "whisper_unmatched.json"
        LOGS.mkdir(exist_ok=True)
        out_path.write_text(json.dumps(unmatched_results, ensure_ascii=False, indent=2))
        print(f"\nUnmatched results saved → {out_path}")

    print()
    print("=" * 55)
    print("WHISPER EXTRACTION COMPLETE")
    print(f"  Obs matched + transcribed : {matched_done}")
    print(f"  Obs matched + skipped     : {matched_skip}")
    print(f"  Unmatched (no obs)        : {unmatched_done}")
    print(f"  Errors                    : {errors}")
    print()
    print("Next: python3 scripts/run_phase4_analysis.py")


if __name__ == "__main__":
    main()
