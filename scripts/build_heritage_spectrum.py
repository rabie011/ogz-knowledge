#!/usr/bin/env python3
"""
build_heritage_spectrum.py
Map each account's distribution across heritage_vs_modern values.
Sort accounts by % heritage. Output: logs/heritage_modern_spectrum.json
"""
import json
import os
from collections import defaultdict, Counter

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/heritage_modern_spectrum.json")

def extract_handle(d):
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    return d.get("account_handle_normalized", "unknown")

accounts = defaultdict(lambda: {
    "sector": None,
    "counter": Counter(),
    "total": 0
})

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

        handle = extract_handle(d)
        sec = d.get("sector", sector)
        hm = d.get("cultural_notes", {}).get("heritage_vs_modern", None)

        acc = accounts[handle]
        acc["sector"] = sec
        acc["total"] += 1
        if hm and str(hm).lower() not in ("none", "null", ""):
            acc["counter"][str(hm)] += 1

# Build output sorted by % heritage
results = []
for handle, data in accounts.items():
    total = data["total"]
    c = data["counter"]
    heritage_pct = round(c.get("heritage", 0) / total * 100, 1) if total else 0
    blended_pct  = round(c.get("blended",  0) / total * 100, 1) if total else 0
    modern_pct   = round(c.get("modern",   0) / total * 100, 1) if total else 0
    neutral_pct  = round(c.get("neutral",  0) / total * 100, 1) if total else 0

    results.append({
        "account": handle,
        "sector": data["sector"],
        "obs_count": total,
        "pct_heritage": heritage_pct,
        "pct_blended": blended_pct,
        "pct_modern": modern_pct,
        "pct_neutral": neutral_pct,
        "raw_counts": {
            "heritage": c.get("heritage", 0),
            "blended":  c.get("blended", 0),
            "modern":   c.get("modern", 0),
            "neutral":  c.get("neutral", 0),
        }
    })

# Sort: most heritage-leaning first
results.sort(key=lambda x: -x["pct_heritage"])

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Accounts mapped: {len(results)}")
print(f"Written to: {OUT_PATH}")
print()
print(f"{'Account':<35} {'Sector':<10} {'Obs':>4}  Heritage  Blended  Modern  Neutral")
print("-" * 90)
for r in results:
    print(f"{r['account']:<35} {r['sector']:<10} {r['obs_count']:>4}    "
          f"{r['pct_heritage']:>5.1f}%   {r['pct_blended']:>5.1f}%  "
          f"{r['pct_modern']:>5.1f}%  {r['pct_neutral']:>5.1f}%")
