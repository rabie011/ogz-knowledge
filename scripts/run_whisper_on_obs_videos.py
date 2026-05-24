#!/usr/bin/env python3
"""
run_whisper_on_obs_videos.py
Run Whisper on the ~35 video obs that have a local mp4 but no voiceover_text.

Fills:
  voice_observations.voiceover_text
  voice_observations.audio_strategy.has_voiceover
  voice_observations.audio_strategy.voiceover_language
  voice_observations.audio_strategy.music_type  (inferred: silence if wc < 3)

Uses: /opt/homebrew/bin/whisper with --model small --language Arabic
Safe to re-run: skips obs where voiceover_text is already set.

Output: logs/whisper_obs_run_report.json
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
WHISPER     = "/opt/homebrew/bin/whisper"
VIDEO_TYPES = {"video", "reel"}


def _build_mp4_index() -> dict:
    index = {}
    for p in INBOX.rglob("*.mp4"):
        stem = p.stem
        if "_" in stem:
            last = stem.split("_")[-1]
            if len(last) >= 8 and re.match(r"^[A-Za-z0-9_\-]+$", last):
                stem = last
        if stem not in index:
            index[stem] = p
    return index


def _run_whisper(mp4: Path) -> dict:
    """Run Whisper on mp4, return {text, language, word_count}."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [WHISPER, str(mp4),
             "--model", "small",
             "--output_format", "json",
             "--output_dir", tmpdir,
             "--fp16", "False"],
            capture_output=True, text=True, timeout=180,
        )
        out_file = Path(tmpdir) / (mp4.stem + ".json")
        if out_file.exists():
            data = json.loads(out_file.read_text())
            text = data.get("text", "").strip()
            lang = data.get("language", "")
            wc   = len(text.split()) if text else 0
            return {"text": text, "language": lang, "word_count": wc}
    return {"text": "", "language": "", "word_count": 0}


def main():
    mp4_index = _build_mp4_index()
    print(f"Local mp4s indexed: {len(mp4_index)}")

    # Find obs that need Whisper
    targets = []
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        d  = json.loads(obs_file.read_text())
        cr = d.get("content_ref") or {}
        vo = d.get("voice_observations") or {}
        ct = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue
        if vo.get("voiceover_text") is not None:
            continue
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        sc  = m.group(1) if m else None
        mp4 = mp4_index.get(sc) if sc else None
        if mp4:
            targets.append((obs_file, mp4, sc))

    print(f"Obs needing Whisper with local mp4: {len(targets)}")
    print()

    updated = 0
    errors  = 0
    results = []

    for i, (obs_file, mp4, sc) in enumerate(targets, 1):
        print(f"[{i:>2}/{len(targets)}] {sc:<25}", end="  ", flush=True)
        try:
            w   = _run_whisper(mp4)
            text = w["text"]
            lang = w["language"]
            wc   = w["word_count"]
            print(f"{lang}  {wc}w  {text[:40]!r}")

            d  = json.loads(obs_file.read_text())
            vo = d.setdefault("voice_observations", {})
            vo["voiceover_text"] = text

            audio = vo.setdefault("audio_strategy", {})
            if audio.get("has_voiceover") is None:
                audio["has_voiceover"] = wc > 3
            if wc > 3 and not audio.get("voiceover_language"):
                lang_map = {"ar": "arabic", "en": "english",
                            "fr": "french", "und": None}
                mapped = lang_map.get(lang, lang if lang else None)
                if mapped:
                    audio["voiceover_language"] = mapped
            if audio.get("music_type") is None:
                audio["music_type"] = "silence" if wc < 3 else "original_score"

            d["voice_observations"] = vo
            obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            updated += 1
            results.append({"shortcode": sc, "language": lang,
                            "word_count": wc, "text_preview": text[:80]})

        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    LOGS.mkdir(exist_ok=True)
    (LOGS / "whisper_obs_run_report.json").write_text(
        json.dumps({"total_targets": len(targets), "updated": updated,
                    "errors": errors, "results": results},
                   ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("WHISPER OBS RUN COMPLETE")
    print(f"  Updated : {updated}")
    print(f"  Errors  : {errors}")
    print(f"  Output  → logs/whisper_obs_run_report.json")


if __name__ == "__main__":
    main()
