#!/usr/bin/env python3
"""
retry_failed_captions.py
Retry the 224 captions that failed in the first extraction run (rate-limited).

Uses 30s delay between requests instead of 4s — should avoid Instagram throttling.
Only retries shortcodes listed in logs/caption_extraction_errors.json.
Safe to re-run: skips obs where caption_text is already filled.

Usage:
  python3 scripts/retry_failed_captions.py
"""
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
LOGS        = BASE / "logs"
INSTALOADER = "/opt/homebrew/bin/instaloader"
SLEEP_SEC   = 30          # much gentler — 30s between requests
ERROR_LOG   = LOGS / "caption_extraction_errors.json"
RETRY_LOG   = LOGS / "caption_retry_run.log"

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002600-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    re.UNICODE,
)

_HASHTAG_RE  = re.compile(r"#[\w؀-ۿ]+")
VIDEO_TYPES  = {"video", "reel"}


def _has_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text))


def _fetch(shortcode: str, work_dir: Path) -> dict | None:
    """Run instaloader and return the post JSON dict, or None on failure."""
    cmd = [
        INSTALOADER,
        "--no-videos", "--no-pictures", "--no-profile-pic",
        "--no-compress-json",
        "--", f"-{shortcode}",
    ]
    try:
        subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None

    post_dir   = work_dir / f"-{shortcode}"
    json_files = sorted(post_dir.glob("*.json")) if post_dir.exists() else []
    if not json_files:
        return None
    try:
        return json.loads(json_files[-1].read_text())
    except Exception:
        return None


def _caption_from_post(post: dict) -> str | None:
    """Extract caption text from instaloader post JSON."""
    try:
        edges = post["node"]["edge_media_to_caption"]["edges"]
        if edges:
            return edges[0]["node"]["text"]
        return ""          # post exists but has no caption
    except (KeyError, IndexError, TypeError):
        return None


def _duration_from_post(post: dict) -> int | None:
    try:
        d = post["node"].get("video_duration")
        return int(d) if d is not None else None
    except (KeyError, TypeError):
        return None


def main():
    # Load failed shortcodes
    if not ERROR_LOG.exists():
        print("No error log found — nothing to retry.")
        return

    errors = json.loads(ERROR_LOG.read_text())
    print(f"Retry queue: {len(errors)} failed shortcodes")
    print(f"Delay between requests: {SLEEP_SEC}s")
    print(f"Estimated time: ~{len(errors)*SLEEP_SEC//60} minutes\n")

    # Build obs file index (shortcode → obs path)
    obs_index: dict[str, Path] = {}
    for entry in errors:
        fname = entry.get("file", "")
        if fname:
            # Search for the file
            matches = list(OBS_ROOT.rglob(fname))
            if matches:
                obs_index[entry["shortcode"]] = matches[0]

    written   = 0
    skipped   = 0
    failed    = 0
    still_failed: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)

        for i, entry in enumerate(errors, 1):
            sc   = entry["shortcode"]
            path = obs_index.get(sc)

            if path is None:
                print(f"[{i:>3}/{len(errors)}] {sc:<25} SKIP (file not found)")
                skipped += 1
                continue

            # Check if already filled
            data = json.loads(path.read_text())
            vo   = data.get("voice_observations") or {}
            if vo.get("caption_text") is not None:
                print(f"[{i:>3}/{len(errors)}] {sc:<25} SKIP (already filled)")
                skipped += 1
                continue

            # Fetch
            post = _fetch(sc, work_dir)
            caption = _caption_from_post(post) if post else None

            if caption is None:
                print(f"[{i:>3}/{len(errors)}] {sc:<25} FAILED")
                failed += 1
                still_failed.append(entry)
            else:
                # Derive fields
                wc = len(caption.split()) if caption else 0
                hc = len(_HASHTAG_RE.findall(caption))
                he = _has_emoji(caption)

                vo["caption_text"]       = caption
                vo["caption_word_count"] = wc
                vo["hashtag_count"]      = hc
                vo["has_emoji"]          = he

                # Duration for video obs
                cr = data.get("content_ref") or {}
                ct = str(cr.get("content_type") or "").lower()
                if ct in VIDEO_TYPES and cr.get("video_duration_seconds") is None:
                    dur = _duration_from_post(post)
                    if dur is not None:
                        cr["video_duration_seconds"] = dur

                path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                written += 1
                flag = f"{wc}w  {hc}#"
                print(f"[{i:>3}/{len(errors)}] {sc:<25} OK   {flag}")

            # Sleep between requests
            if i < len(errors):
                time.sleep(SLEEP_SEC)

    # Update error log with still-failed entries
    ERROR_LOG.write_text(json.dumps(still_failed, ensure_ascii=False, indent=2))

    print()
    print("=" * 50)
    print("RETRY COMPLETE")
    print(f"  Written    : {written}")
    print(f"  Skipped    : {skipped}")
    print(f"  Still fail : {failed}")
    print(f"  Error log  : {ERROR_LOG} ({len(still_failed)} remaining)")
    print()
    print("Next: python3 scripts/run_phase4_analysis.py")


if __name__ == "__main__":
    main()
