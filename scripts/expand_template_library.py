#!/usr/bin/env python3
"""
expand_template_library.py — Add all 1,676 unused Arabic obs to template library.

Adds them as tier "unverified" — real Saudi Instagram captions, source URL clickable,
just no engagement ranking yet (extracted without Apify metrics).

This takes us from 1,383 to ~3,059 templates.
Real estate: 0 real templates → 111 real unverified.

Usage:
    python3 scripts/expand_template_library.py
    python3 scripts/expand_template_library.py --verify
"""
from __future__ import annotations
import argparse, glob, json, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO     = Path(__file__).resolve().parent.parent
OBS_DIR  = REPO / "11_who_to_learn_from" / "observations"
TLIB_PATH = REPO / "11_who_to_learn_from" / "template_library.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    tlib = json.loads(TLIB_PATH.read_text())
    templates = tlib.get("templates", [])

    if args.verify:
        by_tier = defaultdict(int)
        by_occ  = defaultdict(int)
        for t in templates:
            by_tier[t.get("tier","?")] += 1
            by_occ[t.get("occasion","?")] += 1
        print(f"Total templates: {len(templates)}")
        print("\nBy tier:")
        for tier in ["gold","silver","bronze","unverified","generated"]:
            print(f"  {tier:<12} {by_tier[tier]}")
        print("\nBy occasion (real_estate shown):")
        for occ in sorted(by_occ):
            mark = " ←" if occ == "real_estate" else ""
            print(f"  {occ:<25} {by_occ[occ]}{mark}")
        return

    # Build set of URLs already in library
    existing_urls = {t.get("original_url","") for t in templates if t.get("original_url")}
    before = len(templates)

    added = 0
    skipped_dup = 0
    skipped_no_arabic = 0

    for f in glob.glob(str(OBS_DIR / "**" / "*.json"), recursive=True):
        try:
            d = json.loads(Path(f).read_text())
        except Exception:
            continue

        cap  = d.get("voice_observations", {}).get("caption_text", "") or ""
        url  = d.get("content_ref", {}).get("source_url", "") or ""
        likes = d.get("content_ref", {}).get("likes_count") or d.get("likes_count") or 0

        # Skip if already in library
        if url and url in existing_urls:
            skipped_dup += 1
            continue

        # Skip if no Arabic
        if not re.search(r"[؀-ۿ]", cap) or len(cap) < 15:
            skipped_no_arabic += 1
            continue

        # Already-tiered obs (has real likes) are already in library — skip
        if likes >= 1000 or likes >= 100 or likes > 0:
            # These should already be in library — double-check
            if url and url in existing_urls:
                skipped_dup += 1
                continue

        sector   = d.get("sector", "")
        occasion = d.get("occasion") or "evergreen"
        handle   = d.get("account_handle_normalized", "")
        ctype    = d.get("content_ref", {}).get("content_type", "image")

        template = {
            "caption":        cap,
            "tier":           "unverified",
            "sector":         sector,
            "occasion":       occasion,
            "content_type":   ctype,
            "tone":           "authentic",
            "brand_source":   handle,
            "original_likes": likes,
            "original_url":   url,
            "note":           "Real Saudi Instagram caption — engagement not yet verified"
        }
        templates.append(template)
        if url:
            existing_urls.add(url)
        added += 1

    after = len(templates)

    # Write back
    tlib["templates"] = templates
    tlib.setdefault("meta", {})["updated_at"] = datetime.now(timezone.utc).isoformat()
    tlib["meta"]["total"] = after
    TLIB_PATH.write_text(json.dumps(tlib, ensure_ascii=False, indent=2))

    # Summary
    by_tier = defaultdict(int)
    by_occ  = defaultdict(lambda: defaultdict(int))
    for t in templates:
        by_tier[t.get("tier","?")] += 1
        by_occ[t.get("occasion","?")][t.get("tier","?")] += 1

    print(f"Templates: {before} → {after} (+{added} unverified added)")
    print(f"Skipped (duplicates): {skipped_dup}")
    print()
    print("By tier:")
    for tier in ["gold","silver","bronze","unverified","generated"]:
        print(f"  {tier:<12} {by_tier[tier]}")
    print()
    print("Coverage by occasion (gold + unverified):")
    for occ in sorted(by_occ):
        d = by_occ[occ]
        real = d.get("gold",0) + d.get("silver",0) + d.get("bronze",0)
        unv  = d.get("unverified",0)
        gen  = d.get("generated",0)
        print(f"  {occ:<25} real={real:>4}  unverified={unv:>4}  generated={gen:>3}")

    print(f"\n✅ Done. Verify: python3 scripts/expand_template_library.py --verify")


if __name__ == "__main__":
    main()
