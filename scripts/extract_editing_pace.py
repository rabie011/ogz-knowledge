#!/usr/bin/env python3
"""
extract_editing_pace.py
Analyse editing pace (cuts per second, avg shot duration) for all
local video files using ffmpeg scene detection.

For obs-matched videos: writes to observation JSON.
  - content_ref.cut_count           (int — number of scene cuts)
  - content_ref.avg_shot_duration   (float — seconds per shot)
  - content_ref.editing_pace        (str — "slow" | "medium" | "fast" | "viral_fast")

Thresholds (based on common video editing norms):
  viral_fast : ≥ 4 cuts/sec  (< 0.25s per shot)
  fast       : ≥ 1 cut/sec   (< 1s per shot)
  medium     : ≥ 0.3 cut/sec (< 3s per shot)
  slow       : < 0.3 cut/sec (≥ 3s per shot — cinematic)

Safe to re-run: skips obs where cut_count is already set.

Usage:
  python3 scripts/extract_editing_pace.py
"""
import json
import re
import subprocess
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
FFMPEG      = "/opt/homebrew/bin/ffmpeg"
FFPROBE     = "/opt/homebrew/bin/ffprobe"
VIDEO_TYPES = {"video", "reel"}

# Scene change detection threshold (0.0–1.0)
# Lower = more sensitive (more cuts detected). 0.35 is a good balance.
SCDET_THRESHOLD = 0.35


def _get_duration(mp4: Path) -> float | None:
    """Get video duration in seconds via ffprobe."""
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
                    return float(dur)
    except Exception:
        pass
    return None


def _count_cuts(mp4: Path, duration: float) -> int:
    """Count scene changes using ffmpeg scdet filter."""
    try:
        result = subprocess.run(
            [FFMPEG, "-i", str(mp4),
             "-vf", f"scdet=threshold={SCDET_THRESHOLD}",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=120,
        )
        # Count lines with "lavfi.scd" in stderr (each = a detected cut)
        cuts = sum(1 for line in result.stderr.splitlines()
                   if "lavfi.scd" in line)
        return cuts
    except Exception:
        return 0


def _pace_label(cuts: int, duration: float) -> str:
    if duration <= 0:
        return "unknown"
    cps = cuts / duration  # cuts per second
    if cps >= 4:    return "viral_fast"
    if cps >= 1:    return "fast"
    if cps >= 0.3:  return "medium"
    return "slow"


def _load_obs_index() -> dict:
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


def main():
    obs_index = _load_obs_index()
    all_videos = sorted(INBOX.rglob("*.mp4"))

    print(f"Total local videos: {len(all_videos)}")
    print(f"Obs-matched shortcodes: {len(obs_index)}")
    print()

    updated      = 0
    skipped      = 0
    unmatched    = 0
    errors       = 0
    all_results  = []   # store for log

    for i, mp4 in enumerate(all_videos, 1):
        stem = mp4.stem
        if "_" in stem and len(stem.split("_")[-1]) > 8:
            stem = stem.split("_")[-1]

        obs_file = obs_index.get(stem)
        label    = f"@{mp4.parent.parent.name}/{stem}"

        # Skip if already processed
        if obs_file:
            data = json.loads(obs_file.read_text())
            cr   = data.get("content_ref") or {}
            if cr.get("cut_count") is not None:
                print(f"[{i:>3}/{len(all_videos)}] {label:<40} SKIP")
                skipped += 1
                continue

        print(f"[{i:>3}/{len(all_videos)}] {label:<40}", end="  ", flush=True)

        try:
            duration = _get_duration(mp4)
            if duration is None:
                print("ERROR (no duration)")
                errors += 1
                continue

            cuts  = _count_cuts(mp4, duration)
            pace  = _pace_label(cuts, duration)
            avg_s = round(duration / (cuts + 1), 2)   # +1 to avoid div/0

            print(f"{int(duration)}s  {cuts} cuts  {pace}")

            res = {
                "shortcode": stem,
                "duration_s": round(duration, 1),
                "cut_count": cuts,
                "avg_shot_duration": avg_s,
                "editing_pace": pace,
                "file": str(mp4.relative_to(BASE)),
            }
            all_results.append(res)

            if obs_file:
                data = json.loads(obs_file.read_text())
                cr   = data.setdefault("content_ref", {})
                cr["cut_count"]          = cuts
                cr["avg_shot_duration"]  = avg_s
                cr["editing_pace"]       = pace
                # Also fill duration if missing
                if cr.get("video_duration_seconds") is None:
                    cr["video_duration_seconds"] = int(duration)
                obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                updated += 1
            else:
                unmatched += 1

        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    # Save full results log
    LOGS.mkdir(exist_ok=True)
    (LOGS / "editing_pace_analysis.json").write_text(
        json.dumps({
            "total_videos": len(all_videos),
            "results": all_results,
        }, ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("EDITING PACE EXTRACTION COMPLETE")
    print(f"  Obs updated  : {updated}")
    print(f"  Skipped      : {skipped}")
    print(f"  Unmatched    : {unmatched}")
    print(f"  Errors       : {errors}")
    print(f"  Log → logs/editing_pace_analysis.json")

    # Quick summary
    if all_results:
        from collections import Counter
        pace_dist = Counter(r["editing_pace"] for r in all_results)
        print(f"\n  Pace distribution:")
        for pace, cnt in sorted(pace_dist.items(), key=lambda x: -x[1]):
            print(f"    {pace:<15} {cnt}")


if __name__ == "__main__":
    main()
