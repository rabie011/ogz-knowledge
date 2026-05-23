#!/usr/bin/env python3
"""
audit_missing_patterns.py
List all pattern slugs referenced in obs but not defined in the pattern library.
Sorted by frequency. Helps plan which patterns to write next.
"""
import json
import os
from collections import Counter

OBS_ROOT     = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
PATTERNS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/patterns")

# Collect defined pattern slugs
defined = set()
for subcat in os.listdir(PATTERNS_ROOT):
    subcat_path = os.path.join(PATTERNS_ROOT, subcat)
    if not os.path.isdir(subcat_path):
        continue
    for fname in os.listdir(subcat_path):
        if fname.endswith(".json"):
            slug = fname.replace(".json", "")
            defined.add(slug)
            # Also read the file to get slug from inside (in case filename differs)
            try:
                with open(os.path.join(subcat_path, fname)) as f:
                    d = json.load(f)
                    if "slug" in d:
                        defined.add(d["slug"])
            except Exception:
                pass

# Collect referenced slugs from obs
referenced = Counter()
for sector in os.listdir(OBS_ROOT):
    sector_path = os.path.join(OBS_ROOT, sector)
    if not os.path.isdir(sector_path):
        continue
    for fname in os.listdir(sector_path):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(sector_path, fname)
        with open(fpath) as f:
            try:
                d = json.load(f)
            except Exception:
                continue
        for pm in d.get("pattern_matches", []):
            slug = pm.get("pattern_slug") or pm.get("pattern")
            if slug:
                referenced[str(slug).strip()] += 1

missing = {slug: count for slug, count in referenced.items() if slug not in defined}
in_library_unused = defined - set(referenced.keys())

print(f"Defined in library:      {len(defined)}")
print(f"Referenced in obs:       {len(referenced)}")
print(f"Missing from library:    {len(missing)}")
print(f"Defined but never used:  {len(in_library_unused)}")
print()
print("Never-used library patterns:")
for slug in sorted(in_library_unused):
    print(f"  {slug}")

print()
print(f"Missing patterns (sorted by usage count):")
print(f"{'Count':>6}  Slug")
print("-" * 60)
for slug, count in sorted(missing.items(), key=lambda x: -x[1]):
    print(f"  {count:4d}  {slug}")
