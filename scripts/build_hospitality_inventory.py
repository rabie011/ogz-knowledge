#!/usr/bin/env python3
"""
build_hospitality_inventory.py
Extract all cultural_notes.hospitality_cues from observations into
logs/hospitality_cues_inventory.json
Each entry: cue + account + sector + heritage_vs_modern + shortcode + ulid
"""
import json
import os

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/hospitality_cues_inventory.json")

def extract_handle(d):
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    return d.get("account_handle_normalized", "")

def extract_shortcode(d):
    src = d.get("content_ref", {}).get("source_url", "")
    parts = src.rstrip("/").split("/")
    return parts[-1] if parts else ""

entries = []
total_obs = 0
obs_with_cues = 0

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
        ulid = d.get("observation_ulid", fname.replace(".json",""))
        handle = extract_handle(d)
        shortcode = extract_shortcode(d)
        sector_val = d.get("sector", sector)
        cn = d.get("cultural_notes", {})
        heritage = cn.get("heritage_vs_modern", None)
        occasion = cn.get("occasion_relevance", None)
        cues = cn.get("hospitality_cues", [])

        if not cues:
            continue

        obs_with_cues += 1
        for cue in cues:
            if not cue or not isinstance(cue, str):
                continue
            cue = cue.strip()
            if not cue:
                continue
            entries.append({
                "cue": cue,
                "account": handle,
                "sector": sector_val,
                "heritage_vs_modern": heritage,
                "occasion": occasion if occasion not in (None, "none", "None", "null") else None,
                "shortcode": shortcode,
                "observation_ulid": ulid
            })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"Total obs scanned:      {total_obs}")
print(f"Obs with hosp. cues:    {obs_with_cues}")
print(f"Total cue entries:      {len(entries)}")
print(f"Written to: {OUT_PATH}")
