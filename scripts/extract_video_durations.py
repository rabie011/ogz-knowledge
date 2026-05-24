#!/usr/bin/env python3
"""
extract_video_durations.py
Fill video_duration_seconds for all obs that have a local video file
downloaded in 11_who_to_learn_from/_inbox/.

Uses ffprobe — zero network calls, instant.
Safe to re-run: never overwrites existing non-null values.

Usage:
  python3 scripts/extract_video_durations.py
"""
import json
import re
import subprocess
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
INBOX    = BASE / "11_who_to_learn_from" / "_inbox"
FFPROBE  = "/opt/homebrew/bin/ffprobe"
VIDEO_TYPES = {"video", "reel"}


def _duration_ffprobe(video_path: Path) -> float | None:
    """Return duration in seconds via ffprobe, or None."""
    cmd = [
        FFPROBE, "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data   = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                dur = stream.get("duration")
                if dur:
                    return round(float(dur), 1)
    except Exception:
        pass
    return None


def main():
    # Build index: shortcode → video path (from _inbox)
    video_index: dict[str, Path] = {}
    for mp4 in INBOX.rglob("*.mp4"):
        stem = mp4.stem
        # Handle old_partial naming: reel01_DYco4DoDiF6 → DYco4DoDiF6
        if "_" in stem and len(stem.split("_")[-1]) > 8:
            stem = stem.split("_")[-1]
        video_index[stem] = mp4

    print(f"Videos indexed: {len(video_index)}")
    print()

    filled   = 0
    skipped  = 0
    no_match = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        data = json.loads(obs_file.read_text())
        cr   = data.get("content_ref") or {}
        ct   = str(cr.get("content_type") or "").lower()

        if ct not in VIDEO_TYPES:
            continue

        # Already filled?
        if cr.get("video_duration_seconds") is not None:
            skipped += 1
            continue

        # Match to local file
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
        if not m:
            no_match += 1
            continue

        sc       = m.group(1)
        vid_path = video_index.get(sc)

        if vid_path is None:
            no_match += 1
            continue

        dur = _duration_ffprobe(vid_path)
        if dur is None:
            print(f"  {sc:<25} ffprobe failed")
            no_match += 1
            continue

        cr["video_duration_seconds"] = int(dur)
        obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        filled += 1
        print(f"  {sc:<25} {int(dur)}s  ✓")

    print()
    print("=" * 50)
    print("DURATION EXTRACTION COMPLETE")
    print(f"  Filled        : {filled}")
    print(f"  Already set   : {skipped}")
    print(f"  No local file : {no_match}")


if __name__ == "__main__":
    main()
