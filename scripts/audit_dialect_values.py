#!/usr/bin/env python3
"""
audit_dialect_values.py
Print all unique dialect_detected values + frequency across all 474 obs JSON files.
"""
import json
import os
from collections import Counter

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")

counter = Counter()
total = 0

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
            except Exception as e:
                print(f"ERROR reading {fpath}: {e}")
                continue
        total += 1
        dialect = d.get("voice_observations", {}).get("dialect_detected", "__MISSING__")
        counter[str(dialect)] += 1

print(f"Total obs scanned: {total}")
print(f"\nUnique dialect values ({len(counter)}):\n")
for val, count in sorted(counter.items(), key=lambda x: -x[1]):
    print(f"  {count:4d}  {val}")
