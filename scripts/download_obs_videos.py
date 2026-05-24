#!/usr/bin/env python3
"""
download_obs_videos.py
Download video files for all video/reel obs that have a source_url
but no local video file in 11_who_to_learn_from/_inbox/.

Uses instaloader to download actual .mp4 files.
Organises files as: _inbox/@{handle}/media/{shortcode}.mp4

Safe to re-run: skips obs whose shortcode already exists locally.

Usage:
  python3 scripts/download_obs_videos.py
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
INSTALOADER = "/opt/homebrew/bin/instaloader"
SLEEP_SEC   = 8          # between downloads — gentle on Instagram
VIDEO_TYPES = {"video", "reel"}

# Account handle map (normalised ID → Instagram handle)
ACCOUNT_HANDLES = {
    "OGZ-F-AND-B-Reference-002": "barnscoffee",
    "OGZ-F-AND-B-Reference-003": "hawasweets",
    "OGZ-F-AND-B-Reference-004": "matbakhkousa",
    "OGZ-F-AND-B-Reference-005": "altazaj_fakieh",
    "OGZ-F-AND-B-Reference-006": "dx33QjaDUqf",
    "OGZ-F-AND-B-Reference-007": "kuduksa",
    "OGZ-F-AND-B-Reference-008": "albaik",
    "OGZ-F-AND-B-Reference-009": "shawarmersa",
    "OGZ-F-AND-B-Reference-010": "aseeb.najd",
    "OGZ-F-AND-B-Reference-011": "alromansiahksa",
    "OGZ-F-AND-B-Reference-038": "pizzahutsaudi",
    "OGZ-F-AND-B-Reference-039": "mcdonaldsksa",
    "OGZ-RETAIL-Reference-001":  "aldeebajofficial",
    "OGZ-BEAUTY-Reference-001":  "asteribeautysa",
    "OGZ-BEAUTY-Reference-002":  "prettynature.official",
}


def _existing_shortcodes() -> set:
    """Return set of shortcodes already in _inbox."""
    codes = set()
    for mp4 in INBOX.rglob("*.mp4"):
        stem = mp4.stem
        if "_" in stem and len(stem.split("_")[-1]) > 8:
            stem = stem.split("_")[-1]
        codes.add(stem)
    return codes


def _download(shortcode: str, dest_dir: Path) -> Path | None:
    """Download video via instaloader. Returns path to .mp4 or None."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = dest_dir / f"_tmp_{shortcode}"
    tmp_dir.mkdir(exist_ok=True)

    cmd = [
        INSTALOADER,
        "--no-pictures",
        "--no-compress-json",
        "--no-profile-pic",
        f"--filename-pattern={{shortcode}}",
        "--", f"-{shortcode}",
    ]
    try:
        subprocess.run(
            cmd, cwd=str(tmp_dir),
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        return None

    # Find the downloaded mp4
    mp4_files = list(tmp_dir.rglob("*.mp4"))
    if not mp4_files:
        # Clean up empty tmp dir
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    # Move to final location
    src = mp4_files[0]
    dst = dest_dir / f"{shortcode}.mp4"
    src.rename(dst)

    # Remove tmp
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return dst


def main():
    existing = _existing_shortcodes()
    print(f"Already downloaded: {len(existing)} videos")

    # Collect all video obs that need downloading
    queue = []
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        data = json.loads(obs_file.read_text())
        cr   = data.get("content_ref") or {}
        ct   = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue

        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
        if not m:
            continue

        sc = m.group(1)
        if sc in existing:
            continue

        acct   = data.get("account_handle_normalized", "unknown")
        handle = ACCOUNT_HANDLES.get(acct, acct.lower())
        queue.append({"sc": sc, "handle": handle, "obs": obs_file, "data": data})

    print(f"Videos to download: {len(queue)}")
    print()

    downloaded = 0
    failed     = 0

    for i, item in enumerate(queue, 1):
        sc     = item["sc"]
        handle = item["handle"]
        dest   = INBOX / f"@{handle}" / "media"

        print(f"[{i:>3}/{len(queue)}] @{handle}/{sc}", end="  ", flush=True)
        mp4_path = _download(sc, dest)

        if mp4_path:
            # Write duration back to obs immediately
            data = json.loads(item["obs"].read_text())
            cr   = data.get("content_ref") or {}
            if cr.get("video_duration_seconds") is None:
                try:
                    import subprocess as sp2
                    r = sp2.run(
                        ["/opt/homebrew/bin/ffprobe", "-v", "quiet",
                         "-print_format", "json", "-show_streams", str(mp4_path)],
                        capture_output=True, text=True, timeout=15,
                    )
                    d = json.loads(r.stdout)
                    for s in d.get("streams", []):
                        if s.get("codec_type") == "video":
                            dur = s.get("duration")
                            if dur:
                                cr["video_duration_seconds"] = int(float(dur))
                                break
                    item["obs"].write_text(json.dumps(data, ensure_ascii=False, indent=2))
                except Exception:
                    pass

            size_mb = round(mp4_path.stat().st_size / 1024 / 1024, 1)
            print(f"✓  {size_mb}MB")
            downloaded += 1
        else:
            print("FAILED")
            failed += 1

        if i < len(queue):
            time.sleep(SLEEP_SEC)

    print()
    print("=" * 50)
    print("VIDEO DOWNLOAD COMPLETE")
    print(f"  Downloaded : {downloaded}")
    print(f"  Failed     : {failed}")
    print(f"  Total _inbox: {len(existing) + downloaded} videos")


if __name__ == "__main__":
    main()
