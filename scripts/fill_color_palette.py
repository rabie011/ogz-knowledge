#!/usr/bin/env python3
"""
fill_color_palette.py
Extract dominant color palette from local images using PIL.
Fills visual_observations.color_palette per obs.

For each obs with a local image:
  - Extract top-3 dominant colors (RGB → named family)
  - Classify warm / cool / neutral
  - Detect if palette is monochrome / duotone / rich

Output: logs/fill_color_palette_report.json
"""
import json
import re
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

IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".webp"}
SKIP_SUFFIX = "_thumb"

# ── Color family mapping ─────────────────────────────────────────────
def _rgb_to_family(r, g, b) -> str:
    """Map RGB to a named color family."""
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    # Greyscale
    if delta < 25:
        if max_c < 60:   return "black"
        if max_c > 200:  return "white"
        return "grey"

    # Hue
    if max_c == r:
        hue = 60 * ((g - b) / delta % 6)
    elif max_c == g:
        hue = 60 * ((b - r) / delta + 2)
    else:
        hue = 60 * ((r - g) / delta + 4)
    if hue < 0: hue += 360

    sat = delta / max_c if max_c else 0

    if sat < 0.15:   return "grey"
    if hue < 15:     return "red"
    if hue < 40:     return "orange"
    if hue < 70:     return "yellow"
    if hue < 150:    return "green"
    if hue < 195:    return "teal"
    if hue < 250:    return "blue"
    if hue < 290:    return "purple"
    if hue < 330:    return "pink"
    return "red"


WARM_FAMILIES  = {"red", "orange", "yellow", "pink"}
COOL_FAMILIES  = {"blue", "teal", "green", "purple"}
NEUTRAL_FAMILIES = {"white", "grey", "black"}


def _warmth(families: list[str]) -> str:
    warm = sum(1 for f in families if f in WARM_FAMILIES)
    cool = sum(1 for f in families if f in COOL_FAMILIES)
    if warm > cool: return "warm"
    if cool > warm: return "cool"
    return "neutral"


def _palette_type(families: list[str]) -> str:
    unique = set(families) - NEUTRAL_FAMILIES
    if len(unique) == 0: return "monochrome_neutral"
    if len(unique) == 1: return "monochrome"
    if len(unique) == 2: return "duotone"
    return "rich"


def _dominant_colors(img_path: Path, n=3) -> list[str]:
    """Extract top-n dominant color families from image."""
    try:
        with Image.open(img_path) as img:
            # Resize for speed
            img = img.convert("RGB").resize((80, 80))
            pixels = list(img.getdata())
            families = [_rgb_to_family(r, g, b) for r, g, b in pixels]
            top = [fam for fam, _ in Counter(families).most_common(n)]
            return top
    except Exception:
        return []


def _build_file_index() -> dict:
    """shortcode → image path (prefer full image over thumb)."""
    index = {}
    for p in INBOX.rglob("*"):
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        if SKIP_SUFFIX in p.stem:
            continue
        # For carousels (_1.jpg, _2.jpg) use slide 1
        stem = p.stem
        m = re.match(r'^(.+)_(\d+)$', stem)
        if m:
            sc = m.group(1)
            slide = int(m.group(2))
            if slide != 1:
                continue
            stem = sc
        # Standard shortcode extraction
        if "_" in stem:
            last = stem.split("_")[-1]
            if len(last) >= 8 and re.match(r"^[A-Za-z0-9_\-]+$", last):
                stem = last
        if stem not in index:
            index[stem] = p
    return index


def _build_obs_index() -> dict:
    """shortcode → obs_file"""
    idx = {}
    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        url = (d.get("content_ref") or {}).get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        if m:
            idx[m.group(1)] = f
    return idx


def main():
    if not PIL_OK:
        print("PIL not installed — run: pip install Pillow")
        return

    print("Building indexes…", flush=True)
    file_index = _build_file_index()
    obs_index  = _build_obs_index()
    print(f"Image files (slide-1 or solo): {len(file_index)}")
    print(f"Obs with shortcode:            {len(obs_index)}")
    print()

    updated   = 0
    skipped   = 0
    no_file   = 0
    errors    = 0
    results   = []
    family_dist = Counter()

    for sc, obs_file in sorted(obs_index.items()):
        d  = json.loads(obs_file.read_text())
        vo = d.get("visual_observations") or {}

        if vo.get("color_palette"):
            skipped += 1
            continue

        img = file_index.get(sc)
        if not img:
            no_file += 1
            continue

        families = _dominant_colors(img)
        if not families:
            errors += 1
            continue

        palette = {
            "dominant_colors":  families,
            "warmth":           _warmth(families),
            "palette_type":     _palette_type(families),
            "primary_family":   families[0] if families else None,
        }

        vo["color_palette"] = palette
        d["visual_observations"] = vo
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        family_dist[families[0]] += 1
        results.append({"shortcode": sc, "palette": palette, "file": img.name})

        if updated % 50 == 0:
            print(f"  …{updated} updated", flush=True)

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_color_palette_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_file": no_file, "errors": errors,
                    "primary_color_distribution": dict(family_dist.most_common()),
                    "sample": results[:20]},
                   ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("COLOR PALETTE FILL COMPLETE")
    print(f"  Updated  : {updated}")
    print(f"  Skipped  : {skipped}")
    print(f"  No file  : {no_file}")
    print(f"  Errors   : {errors}")
    print()
    print("  Primary color distribution:")
    for fam, c in family_dist.most_common():
        print(f"    {fam:<15} {c}")
    print()
    print("  Output → logs/fill_color_palette_report.json")


if __name__ == "__main__":
    main()
