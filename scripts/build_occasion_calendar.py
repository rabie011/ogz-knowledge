#!/usr/bin/env python3
"""
build_occasion_calendar.py
Group observations by occasion_relevance and map to top patterns, phrases,
accounts, and engagement signals.
Output: logs/occasion_pattern_calendar.json
"""
import json
import os
from collections import defaultdict, Counter

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/occasion_pattern_calendar.json")

NULL_VALUES = {None, "none", "None", "null", "NULL", "", "n/a", "N/A"}

# Map engagement_potential string to numeric weight for averaging
ENG_WEIGHT = {"high": 1.0, "medium": 0.5, "low": 0.0}

def extract_handle(d):
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    return d.get("account_handle_normalized", "unknown")

# Accumulate per-occasion buckets
occasions = defaultdict(lambda: {
    "obs_count": 0,
    "pattern_counter": Counter(),
    "account_counter": Counter(),
    "heritage_counter": Counter(),
    "engagement_scores": [],
    "sample_phrases": [],
    "sectors": Counter(),
})

total_obs = 0
occasions_found = 0

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
        cn = d.get("cultural_notes", {})
        occasion = cn.get("occasion_relevance", None)

        if occasion in NULL_VALUES:
            continue
        occasion = str(occasion).strip()
        if not occasion or occasion in NULL_VALUES:
            continue

        occasions_found += 1
        occ = occasions[occasion]
        occ["obs_count"] += 1

        handle = extract_handle(d)
        occ["account_counter"][handle] += 1

        heritage = cn.get("heritage_vs_modern")
        if heritage:
            occ["heritage_counter"][str(heritage)] += 1

        occ["sectors"][d.get("sector", "unknown")] += 1

        eng = d.get("quality_assessment", {}).get("engagement_potential", None)
        if eng in ENG_WEIGHT:
            occ["engagement_scores"].append(ENG_WEIGHT[eng])

        for pm in d.get("pattern_matches", []):
            slug = pm.get("pattern_slug") or pm.get("pattern")
            if slug:
                occ["pattern_counter"][str(slug)] += 1

        phrases = d.get("voice_observations", {}).get("notable_phrases", [])
        for p in phrases:
            if isinstance(p, str) and p.strip():
                if len(occ["sample_phrases"]) < 5:
                    occ["sample_phrases"].append(p.strip())

# Build output
results = []
for occasion, data in sorted(occasions.items(), key=lambda x: -x[1]["obs_count"]):
    top_patterns = [slug for slug, _ in data["pattern_counter"].most_common(5)]
    top_accounts = [acc for acc, _ in data["account_counter"].most_common(3)]

    heritage_c = data["heritage_counter"]
    dominant_heritage = heritage_c.most_common(1)[0][0] if heritage_c else None

    eng_scores = data["engagement_scores"]
    if eng_scores:
        avg_eng = sum(eng_scores) / len(eng_scores)
        avg_eng_label = "high" if avg_eng >= 0.7 else ("medium" if avg_eng >= 0.35 else "low")
    else:
        avg_eng_label = None

    results.append({
        "occasion": occasion,
        "obs_count": data["obs_count"],
        "sectors": dict(data["sectors"]),
        "top_patterns": top_patterns,
        "avg_engagement_potential": avg_eng_label,
        "dominant_heritage_vs_modern": dominant_heritage,
        "top_accounts": top_accounts,
        "sample_phrases": data["sample_phrases"][:5]
    })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Total obs scanned:      {total_obs}")
print(f"Obs with occasion:      {occasions_found}")
print(f"Unique occasions:       {len(results)}")
print(f"Written to: {OUT_PATH}")
print()
print("Top 15 occasions by obs count:")
for r in results[:15]:
    print(f"  {r['obs_count']:4d}  {r['occasion']}")
