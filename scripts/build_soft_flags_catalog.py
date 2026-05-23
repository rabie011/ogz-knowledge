#!/usr/bin/env python3
"""
build_soft_flags_catalog.py
Compile all soft_flags from compliance_check across all obs.
Output: logs/soft_flags_catalog.json
"""
import json
import os
from collections import defaultdict, Counter

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/soft_flags_catalog.json")

def extract_handle(d):
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    return d.get("account_handle_normalized", "unknown")

def extract_shortcode(d):
    src = d.get("content_ref", {}).get("source_url", "")
    parts = src.rstrip("/").split("/")
    return parts[-1] if parts else ""

# Accumulate by flag_type
by_type = defaultdict(lambda: {
    "count": 0,
    "examples": [],
    "accounts": Counter(),
    "sectors": Counter(),
})

total_obs = 0
flagged_obs = 0
total_flags = 0

for sector in sorted(os.listdir(OBS_ROOT)):
    sector_path = os.path.join(OBS_ROOT, sector)
    if not os.path.isdir(sector_path):
        continue
    for fname in sorted(os.listdir(sector_path)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(sector_path, fname)
        with open(fpath) as f:
            try:
                d = json.load(f)
            except Exception:
                continue

        total_obs += 1
        flags = d.get("compliance_check", {}).get("soft_flags", [])
        if not flags:
            continue

        has_flag = False
        handle = extract_handle(d)
        shortcode = extract_shortcode(d)
        sec = d.get("sector", sector)
        ulid = d.get("observation_ulid", fname.replace(".json",""))

        for flag in flags:
            if not flag:
                continue
            # Flags should be {flag_type, description} objects
            if isinstance(flag, dict):
                flag_type = flag.get("flag_type", "unknown")
                description = flag.get("description", "")
            elif isinstance(flag, str):
                flag_type = flag
                description = ""
            else:
                continue

            ft = by_type[flag_type]
            ft["count"] += 1
            ft["accounts"][handle] += 1
            ft["sectors"][sec] += 1
            if len(ft["examples"]) < 5:
                ft["examples"].append({
                    "description": description,
                    "account": handle,
                    "shortcode": shortcode,
                    "observation_ulid": ulid
                })
            total_flags += 1
            has_flag = True

        if has_flag:
            flagged_obs += 1

# Build output
results = []
for flag_type, data in sorted(by_type.items(), key=lambda x: -x[1]["count"]):
    results.append({
        "flag_type": flag_type,
        "total_occurrences": data["count"],
        "affected_accounts": dict(data["accounts"].most_common()),
        "by_sector": dict(data["sectors"].most_common()),
        "examples": data["examples"]
    })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Total obs scanned:      {total_obs}")
print(f"Obs with soft flags:    {flagged_obs}")
print(f"Total flag instances:   {total_flags}")
print(f"Unique flag types:      {len(results)}")
print(f"Written to: {OUT_PATH}")
if results:
    print()
    print("Flag types by frequency:")
    for r in results:
        print(f"  {r['total_occurrences']:4d}  {r['flag_type']}")
