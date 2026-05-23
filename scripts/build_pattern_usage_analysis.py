#!/usr/bin/env python3
"""
build_pattern_usage_analysis.py
Structured JSON breakdown of pattern usage across all obs.
Output: logs/pattern_usage_analysis.json
Also emits a quick summary to stdout.
"""
import json
import os
from collections import defaultdict, Counter

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/pattern_usage_analysis.json")

ENG_WEIGHT = {"high": 1.0, "medium": 0.5, "low": 0.0}
NULL_VALUES = {None, "none", "None", "null", "", "n/a"}

def extract_handle(d):
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    return d.get("account_handle_normalized", "unknown")

# Accumulate per-pattern
patterns = defaultdict(lambda: {
    "total_uses": 0,
    "by_sector": Counter(),
    "by_account": Counter(),
    "by_confidence": Counter(),
    "engagement_scores": [],
    "occasions": Counter(),
})

total_obs = 0

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
        handle = extract_handle(d)
        sec = d.get("sector", sector)
        eng = d.get("quality_assessment", {}).get("engagement_potential", None)
        eng_score = ENG_WEIGHT.get(eng)
        occasion = d.get("cultural_notes", {}).get("occasion_relevance", None)

        for pm in d.get("pattern_matches", []):
            slug = pm.get("pattern_slug") or pm.get("pattern")
            if not slug:
                continue
            slug = str(slug).strip()
            conf = pm.get("confidence", "unknown")

            p = patterns[slug]
            p["total_uses"] += 1
            p["by_sector"][sec] += 1
            p["by_account"][handle] += 1
            p["by_confidence"][str(conf)] += 1
            if eng_score is not None:
                p["engagement_scores"].append(eng_score)
            if occasion and occasion not in NULL_VALUES:
                p["occasions"][str(occasion)] += 1

# Build output
results = []
for slug, data in sorted(patterns.items(), key=lambda x: -x[1]["total_uses"]):
    eng_scores = data["engagement_scores"]
    avg_eng = round(sum(eng_scores) / len(eng_scores), 3) if eng_scores else None

    results.append({
        "pattern_slug": slug,
        "total_uses": data["total_uses"],
        "by_sector": dict(data["by_sector"].most_common()),
        "by_account": dict(data["by_account"].most_common(5)),
        "confidence_breakdown": dict(data["by_confidence"].most_common()),
        "avg_engagement_score": avg_eng,
        "top_occasions": [occ for occ, _ in data["occasions"].most_common(3)]
    })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Total obs scanned:   {total_obs}")
print(f"Unique pattern slugs:{len(results)}")
print(f"Written to: {OUT_PATH}")
print()
print("Top 20 patterns by usage:")
for r in results[:20]:
    print(f"  {r['total_uses']:4d}  {r['pattern_slug']:<45}  avg_eng={r['avg_engagement_score']}")
