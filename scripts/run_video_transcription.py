#!/usr/bin/env python3
"""
run_video_transcription.py
Download Instagram videos and transcribe with Whisper.

For each video obs with source_url and no voiceover_text:
  1. Download video via instaloader (--load-cookies chrome)
  2. Run Whisper (small model, auto-detect Arabic/English)
  3. Store result in voice_observations.voiceover_text + audio_strategy
  4. Delete the mp4 to save disk space

Fields written per obs (only if currently null):
  voice_observations.voiceover_text           ← full transcript (or "" if silent/music)
  voice_observations.audio_strategy.has_voiceover     ← bool
  voice_observations.audio_strategy.voiceover_language ← "arabic"|"english"|"none"
  voice_observations.audio_strategy.music_type         ← "voiceover"|"music_only"|"silent"

Safe to re-run: skips obs where voiceover_text is not null.

Usage:
  python3 scripts/run_video_transcription.py              # full run
  python3 scripts/run_video_transcription.py --dry-run    # plan only
  python3 scripts/run_video_transcription.py --batch 50   # process N videos
"""
import json, os, re, subprocess, sys, tempfile, time
from collections import defaultdict
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
LOGS        = BASE / "logs"
INSTALOADER = "/opt/homebrew/bin/instaloader"
COOKIE_FILE = BASE / "logs" / ".instagram_cookies.txt"
SLEEP_DL    = 4    # seconds between instaloader calls
VIDEO_TYPES = {"video", "reel", "video_reel"}
MAX_FILE_MB = 24   # OpenAI Whisper API limit is 25 MB

# ── OpenAI Whisper API client ─────────────────────────────────────────────────
try:
    from openai import OpenAI as _OpenAI
    _oa_client = _OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    USE_OPENAI_WHISPER = bool(os.environ.get("OPENAI_API_KEY"))
except ImportError:
    _oa_client = None
    USE_OPENAI_WHISPER = False


def _shortcode(url: str):
    m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
    return m.group(1) if m else None


def _download_video(shortcode: str, work_dir: Path) -> Path | None:
    """Download a single Instagram post video. Returns mp4 path or None."""
    cmd = [
        INSTALOADER,
        "--cookiefile", str(COOKIE_FILE),
        "--no-pictures",
        "--no-profile-pic",
        "--no-compress-json",
        "--",
        f"-{shortcode}",
    ]
    try:
        subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=30)
    except Exception:
        return None

    post_dir = work_dir / f"-{shortcode}"
    if not post_dir.exists():
        return None

    mp4s = sorted(post_dir.glob("*.mp4"))
    return mp4s[0] if mp4s else None


def _transcribe(mp4_path: Path) -> dict:
    """
    Transcribe mp4 audio. Uses OpenAI Whisper API if key available,
    falls back to local Whisper CLI otherwise.
    Returns dict with: text, language, word_count, has_voiceover, music_type
    """
    _EMPTY = {"text": "", "language": "none", "word_count": 0,
              "has_voiceover": False, "music_type": "unknown"}

    # ── OpenAI Whisper API (preferred) ────────────────────────────────────────
    if USE_OPENAI_WHISPER and _oa_client:
        file_mb = mp4_path.stat().st_size / 1024 / 1024
        if file_mb > MAX_FILE_MB:
            print(f"    ⚠ {mp4_path.name} is {file_mb:.1f} MB — skipping (API limit 25 MB)")
            return _EMPTY
        try:
            with open(mp4_path, "rb") as fh:
                resp = _oa_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=fh,
                    response_format="verbose_json",
                    language=None,   # auto-detect Arabic/English
                )
            text     = (resp.text or "").strip()
            language = resp.language or "none"
        except Exception as e:
            print(f"    ⚠ OpenAI Whisper API error: {e}")
            return _EMPTY

    # ── Local Whisper CLI (fallback) ──────────────────────────────────────────
    else:
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [
                "/opt/homebrew/bin/whisper",
                str(mp4_path),
                "--model", "small",
                "--output_format", "json",
                "--output_dir", tmp,
                "--fp16", "False",
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired:
                return _EMPTY

            json_files = sorted(Path(tmp).glob("*.json"))
            if not json_files:
                return _EMPTY
            try:
                data = json.loads(json_files[0].read_text())
            except Exception:
                return _EMPTY

        text     = data.get("text", "").strip()
        language = data.get("language", "none")

    # ── Classify audio strategy (shared) ─────────────────────────────────────
    wc = len(text.split()) if text else 0

    if wc < 3:
        music_type    = "music_only" if wc == 0 else "silent"
        has_voiceover = False
        text = ""  # discard noise
    else:
        music_type    = "voiceover"
        has_voiceover = True

    lang_label = "arabic"  if language in ("ar", "arabic")  else \
                 "english" if language in ("en", "english") else \
                 language  if language else "none"

    return {
        "text":          text,
        "language":      lang_label,
        "word_count":    wc,
        "has_voiceover": has_voiceover,
        "music_type":    music_type,
    }


def main():
    dry_run   = "--dry-run" in sys.argv
    batch_arg = next((sys.argv[i+1] for i,a in enumerate(sys.argv) if a == "--batch"), None)
    batch_max = int(batch_arg) if batch_arg else None

    if dry_run:
        print("DRY RUN — no files will be written\n")

    # ── 1. Find video obs needing transcription ────────────────────────────────
    to_process = []
    for f in sorted(OBS_ROOT.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue

        ct  = d.get("content_ref", {}).get("content_type", "")
        if not any(v in ct for v in VIDEO_TYPES):
            continue

        voc = d.get("voice_observations") or {}
        if voc.get("voiceover_text") is not None:
            continue  # already done

        url = d.get("content_ref", {}).get("source_url", "")
        if "instagram.com/p/" not in url:
            continue

        sc = _shortcode(url)
        if not sc:
            continue

        to_process.append((f, d, sc))

    if batch_max:
        to_process = to_process[:batch_max]

    n       = len(to_process)
    eta_min = round(n * (SLEEP_DL + 15) / 60, 1)

    print(f"Videos to transcribe : {n}  (≈{eta_min} min)")
    if dry_run or n == 0:
        if n == 0: print("Nothing to do.")
        return

    print()

    stats  = defaultdict(int)
    errors = []

    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)

        for i, (obs_file, data, sc) in enumerate(to_process, 1):
            pct    = round(i / n * 100)
            handle = data.get("account_handle_normalized", "?")
            print(f"[{i:>4}/{n}  {pct:>3}%]  @{handle[:20]:20}  {sc:<26}", end="  ", flush=True)

            # ── Download ───────────────────────────────────────────────────────
            mp4 = _download_video(sc, work_dir)
            if mp4 is None:
                print("FAILED (no mp4)")
                stats["dl_failed"] += 1
                errors.append({"shortcode": sc, "error": "no_mp4", "file": obs_file.name})
                time.sleep(SLEEP_DL)
                continue

            # ── Transcribe ─────────────────────────────────────────────────────
            result = _transcribe(mp4)

            # ── Clean up mp4 immediately ───────────────────────────────────────
            try:
                mp4.unlink()
            except Exception:
                pass

            # ── Write to obs ───────────────────────────────────────────────────
            voc = data["voice_observations"] or {}
            voc["voiceover_text"] = result["text"]

            audio = voc.get("audio_strategy") or {}
            audio["has_voiceover"]       = result["has_voiceover"]
            audio["voiceover_language"]  = result["language"]
            audio["music_type"]          = result["music_type"]
            voc["audio_strategy"] = audio
            data["voice_observations"]   = voc

            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            stats["written"] += 1

            if result["has_voiceover"]:
                stats["has_voiceover"] += 1
                label = f"✓ {result['word_count']}w [{result['language']}]"
            else:
                stats["music_only"] += 1
                label = f"♫ {result['music_type']}"

            print(f"OK  {label}", flush=True)

            if i < n:
                time.sleep(SLEEP_DL)

    # ── Summary ────────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("TRANSCRIPTION COMPLETE")
    print(f"  Written          : {stats['written']}")
    print(f"  Has voiceover    : {stats['has_voiceover']}")
    print(f"  Music/silent     : {stats['music_only']}")
    print(f"  Download failed  : {stats['dl_failed']}")

    if errors:
        LOGS.mkdir(exist_ok=True)
        err_path = LOGS / "transcription_errors.json"
        err_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2))
        print(f"  Error log        : logs/transcription_errors.json")
        for e in errors[:5]:
            print(f"    {e['shortcode']} → {e['error']}")
        if len(errors) > 5:
            print(f"    ... +{len(errors)-5} more")

    print()
    print("Next step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
