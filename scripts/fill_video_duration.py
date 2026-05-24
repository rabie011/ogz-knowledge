#!/usr/bin/env python3
"""
fill_video_duration.py
Fill content_ref.video_duration_seconds for video/reel obs that are missing it,
using ffprobe on local mp4 files.

Safe to re-run: skips obs where video_duration_seconds is already set.
Output: logs/fill_video_duration_report.json
"""
import json
import re
import subprocess
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
FFPROBE     = "/opt/homebrew/bin/ffprobe"
VIDEO_TYPES = {"video", "reel"}


def _get_duration(mp4: Path) -> int | None:
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json",
             "-show_streams", str(mp4)],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(result.stdout)
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                dur = s.get("duration")
                if dur:
                    return int(float(dur))
    except Exception:
        pass
    return None


def _build_mp4_index() -> dict:
    """Map shortcode → mp4 path."""
    index = {}
    for p in INBOX.rglob("*.mp4"):
        stem = p.stem
        # Handle account_shortcode naming
        if "_" in stem:
            parts = stem.split("_")
            last = parts[-1]
            if len(last) >= 8 and re.match(r"^[A-Za-z0-9_\-]+$", last):
                stem = last
        if stem not in index:
            index[stem] = p
    return index


def main():
    mp4_index = _build_mp4_index()

    updated  = 0
    skipped  = 0
    no_file  = 0
    errors   = 0
    results  = []

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        d  = json.loads(obs_file.read_text())
        cr = d.get("content_ref") or {}
        ct = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue
        if cr.get("video_duration_seconds") is not None:
            skipped += 1
            continue

        # Find matching mp4
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        sc  = m.group(1) if m else None
        mp4 = mp4_index.get(sc) if sc else None

        if not mp4:
            no_file += 1
            continue

        dur = _get_duration(mp4)
        if dur is None:
            errors += 1
            continue

        cr["video_duration_seconds"] = dur
        d["content_ref"] = cr
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        results.append({"shortcode": sc, "duration_s": dur, "file": obs_file.name})

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_video_duration_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_local_file": no_file, "errors": errors,
                    "results": results}, ensure_ascii=False, indent=2)
    )

    print("=" * 50)
    print("VIDEO DURATION FILL COMPLETE")
    print(f"  Updated      : {updated}")
    print(f"  Already set  : {skipped}")
    print(f"  No local mp4 : {no_file}")
    print(f"  Errors       : {errors}")


if __name__ == "__main__":
    main()
