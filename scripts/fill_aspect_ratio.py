#!/usr/bin/env python3
"""
fill_aspect_ratio.py
Extract width × height from local image/video files and write
content_ref.aspect_ratio to matched observation JSON files.

Canonical values (matching schema description):
  square_1x1       — ratio ≈ 1.0  (1080×1080)
  portrait_4x5     — ratio ≈ 0.8  (1080×1350)
  vertical_9x16    — ratio ≈ 0.56 (1080×1920)
  landscape_16x9   — ratio ≈ 1.78 (1920×1080)
  landscape_4x3    — ratio ≈ 1.33 (1440×1080)

Safe to re-run: skips obs where aspect_ratio is already set.

Output: logs/aspect_ratio_report.json
"""
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
FFPROBE     = "/opt/homebrew/bin/ffprobe"
IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS  = {".mp4", ".mov"}


def _ratio_to_label(w: int, h: int) -> str:
    if h == 0:
        return "unknown"
    r = w / h
    if r < 0.65:   return "vertical_9x16"
    if r < 0.90:   return "portrait_4x5"
    if r < 1.15:   return "square_1x1"
    if r < 1.55:   return "landscape_4x3"
    return "landscape_16x9"


def _dims_from_image(path: Path):
    if not PIL_OK:
        return None, None
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except Exception:
        return None, None


def _dims_from_video(path: Path):
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json",
             "-show_streams", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        for s in data.get("streams", []):
            w = s.get("width")
            h = s.get("height")
            if w and h:
                return int(w), int(h)
    except Exception:
        pass
    return None, None


def _shortcode_from_stem(stem: str) -> str:
    """Extract shortcode: last segment after last underscore if long suffix."""
    if "_" in stem:
        parts = stem.split("_")
        last = parts[-1]
        # If the last part looks like a shortcode (≥8 chars, alphanumeric+-)
        if len(last) >= 8 and re.match(r"^[A-Za-z0-9_\-]+$", last):
            return last
    return stem


def _build_file_index() -> dict:
    """Map shortcode → best local file (prefer full image over thumb)."""
    index = {}
    for path in INBOX.rglob("*"):
        ext = path.suffix.lower()
        if ext not in IMAGE_EXTS | VIDEO_EXTS:
            continue
        if "_thumb" in path.stem:
            continue  # skip thumbnails
        sc = _shortcode_from_stem(path.stem)
        # Prefer images over _N suffix files (carousel) — keep first hit
        if sc not in index:
            index[sc] = path
    return index


def _build_obs_index() -> dict:
    """Map shortcode → obs_file for all obs."""
    obs_idx = {}
    for obs_file in OBS_ROOT.rglob("*.json"):
        d = json.loads(obs_file.read_text())
        cr  = d.get("content_ref") or {}
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        if m:
            obs_idx[m.group(1)] = obs_file
        else:
            # fallback: try filename field
            fname = cr.get("filename", "")
            if fname:
                sc = _shortcode_from_stem(Path(fname).stem)
                obs_idx[sc] = obs_file
    return obs_idx


def main():
    print("Building indexes...", flush=True)
    file_index = _build_file_index()
    obs_index  = _build_obs_index()

    print(f"Local files (non-thumb): {len(file_index)}")
    print(f"Obs with shortcode:      {len(obs_index)}")
    print()

    updated      = 0
    skipped      = 0
    no_file      = 0
    errors       = 0
    ratio_dist   = Counter()
    results      = []

    for shortcode, obs_file in sorted(obs_index.items()):
        d  = json.loads(obs_file.read_text())
        cr = d.get("content_ref") or {}

        # Skip if already set
        if cr.get("aspect_ratio"):
            skipped += 1
            ratio_dist[cr["aspect_ratio"]] += 1
            continue

        local_file = file_index.get(shortcode)
        if not local_file:
            no_file += 1
            continue

        ext = local_file.suffix.lower()
        if ext in IMAGE_EXTS:
            w, h = _dims_from_image(local_file)
        else:
            w, h = _dims_from_video(local_file)

        if not w or not h:
            errors += 1
            continue

        label = _ratio_to_label(w, h)
        cr["aspect_ratio"] = label
        d["content_ref"]   = cr
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))

        ratio_dist[label] += 1
        updated += 1
        results.append({
            "shortcode": shortcode,
            "file": str(local_file.relative_to(BASE)),
            "dims": f"{w}x{h}",
            "aspect_ratio": label,
        })

        if updated % 50 == 0:
            print(f"  ...{updated} updated", flush=True)

    # ── save report ───────────────────────────────────────────────────
    LOGS.mkdir(exist_ok=True)
    report = {
        "obs_with_shortcode": len(obs_index),
        "local_files_found": len(file_index),
        "updated": updated,
        "skipped_already_set": skipped,
        "no_local_file": no_file,
        "errors": errors,
        "aspect_ratio_distribution": dict(ratio_dist.most_common()),
        "sample_results": results[:20],
    }
    (LOGS / "aspect_ratio_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("ASPECT RATIO FILL COMPLETE")
    print(f"  Updated      : {updated}")
    print(f"  Already set  : {skipped}")
    print(f"  No local file: {no_file}")
    print(f"  Errors       : {errors}")
    print()
    print("  Aspect ratio distribution:")
    for label, cnt in ratio_dist.most_common():
        print(f"    {label:<20} {cnt:>4}")
    print()
    print("  Output → logs/aspect_ratio_report.json")


if __name__ == "__main__":
    main()
