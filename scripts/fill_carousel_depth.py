#!/usr/bin/env python3
"""
fill_carousel_depth.py
Count carousel slides from numbered local image files and write
content_ref.carousel_slide_count to matched carousel obs.

File naming: SHORTCODE_1.jpg, SHORTCODE_2.jpg ... SHORTCODE_N.jpg

Also adds carousel_slide_count to schema if not present.
Output: logs/fill_carousel_depth_report.json
"""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

BASE      = Path(__file__).parent.parent
OBS_ROOT  = BASE / "11_who_to_learn_from" / "observations"
INBOX     = BASE / "11_who_to_learn_from" / "_inbox"
LOGS      = BASE / "logs"
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"


def _build_carousel_depth_index() -> dict:
    """Map shortcode → max slide number seen in _inbox."""
    depth = defaultdict(int)
    for p in INBOX.rglob("*"):
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        m = re.match(r'^(.+)_(\d+)$', p.stem)
        if m:
            sc    = m.group(1)
            slide = int(m.group(2))
            depth[sc] = max(depth[sc], slide)
    return dict(depth)


def _build_obs_index() -> dict:
    """Map shortcode → obs_file for carousel obs only."""
    idx = {}
    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        cr = d.get("content_ref") or {}
        ct = str(cr.get("content_type") or "").lower()
        if ct != "carousel_slide":
            continue
        url = cr.get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        if m:
            idx[m.group(1)] = f
    return idx


def _ensure_schema_field():
    """Add carousel_slide_count to content_ref schema if missing."""
    schema = json.loads(SCHEMA_PATH.read_text())
    cr_props = schema["properties"]["content_ref"]["properties"]
    if "carousel_slide_count" not in cr_props:
        cr_props["carousel_slide_count"] = {
            "type": ["integer", "null"],
            "description": "Number of slides in the carousel (from local file count)"
        }
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added carousel_slide_count")


def main():
    _ensure_schema_field()

    depth_index = _build_carousel_depth_index()
    obs_index   = _build_obs_index()

    print(f"Carousels with depth data in _inbox: {len(depth_index)}")
    print(f"Carousel obs with shortcode:         {len(obs_index)}")
    print()

    updated  = 0
    skipped  = 0
    no_depth = 0
    results  = []
    depth_dist = Counter()

    for sc, obs_file in sorted(obs_index.items()):
        d  = json.loads(obs_file.read_text())
        cr = d.get("content_ref") or {}

        if cr.get("carousel_slide_count") is not None:
            skipped += 1
            continue

        depth = depth_index.get(sc)
        if not depth:
            no_depth += 1
            continue

        cr["carousel_slide_count"] = depth
        d["content_ref"] = cr
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        depth_dist[depth] += 1
        results.append({"shortcode": sc, "slides": depth})

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_carousel_depth_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_depth_data": no_depth,
                    "depth_distribution": dict(sorted(depth_dist.items())),
                    "avg_slides": round(sum(d * c for d, c in depth_dist.items()) /
                                        max(sum(depth_dist.values()), 1), 1),
                    "sample": results[:20]},
                   ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("CAROUSEL DEPTH FILL COMPLETE")
    print(f"  Updated      : {updated}")
    print(f"  Already set  : {skipped}")
    print(f"  No depth data: {no_depth}")
    if depth_dist:
        avg = sum(d * c for d, c in depth_dist.items()) / sum(depth_dist.values())
        print(f"  Avg slides   : {avg:.1f}")
        print()
        print("  Depth distribution:")
        for d, c in sorted(depth_dist.items()):
            print(f"    {d:>2} slides: {c:>3}  {'█' * min(c, 40)}")
    print()
    print("  Output → logs/fill_carousel_depth_report.json")


if __name__ == "__main__":
    main()
