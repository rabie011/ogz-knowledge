#!/usr/bin/env python3
"""Canonical index for the 1,002 content_type pattern files (L3.8, June 11).
The library's slugs fragment by alias (food_* / f_and_b_* / food_beverage_*) — the
same disease meta-pattern F documented for sectors. NO files move or rename:
this builds an INDEX with canonical prefixes + duplicate-candidate groups.
Output: 11_who_to_learn_from/patterns/content_types/_CANONICAL_INDEX.json
"""
import json, glob, re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent.parent
DIR = BASE / "11_who_to_learn_from/patterns/content_types"

# canonical prefix aliases (extends 12_data_shapes/sector_aliases.json philosophy)
PREFIX_ALIASES = {
    "food": "f_and_b", "food_beverage": "f_and_b", "fnb": "f_and_b",
    "beauty_personal_care": "beauty", "retail_lifestyle": "retail",
    "ecommerce": "retail", "healthcare": "health", "wellness": "health",
}


def canon(slug: str) -> str:
    for alias, target in sorted(PREFIX_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if slug.startswith(alias + "_"):
            return target + slug[len(alias):]
    return slug


def main():
    files = sorted(glob.glob(str(DIR / "*.json")))
    files = [f for f in files if not f.endswith("_CANONICAL_INDEX.json")]
    groups = defaultdict(list)
    for f in files:
        slug = Path(f).stem
        groups[canon(slug)].append(slug)
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    # near-duplicate candidates: same canonical stem after stripping generic tails
    stem_groups = defaultdict(list)
    for c in groups:
        stem = re.sub(r"_(caption|content|post|pattern)s?$", "", c)
        stem_groups[stem].append(c)
    near = {k: v for k, v in stem_groups.items() if len(v) > 1}
    out = {
        "_meta": {"built": "2026-06-11", "files": len(files),
                   "canonical_groups": len(groups),
                   "alias_merge_groups": len(dupes),
                   "near_duplicate_stems": len(near),
                   "rule": "READ via canonical slug; alias slugs resolve here; no files were moved"},
        "prefix_aliases": PREFIX_ALIASES,
        "alias_merges": dupes,
        "near_duplicate_candidates": dict(sorted(near.items(), key=lambda kv: -len(kv[1]))[:60]),
    }
    (DIR / "_CANONICAL_INDEX.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"✓ {len(files)} files → {len(groups)} canonical · alias-merges: {len(dupes)} · near-dupe stems: {len(near)}")


if __name__ == "__main__":
    main()
