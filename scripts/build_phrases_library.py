#!/usr/bin/env python3
"""
build_phrases_library.py
Extract all notable_phrases from observations into logs/notable_phrases_library.json
Each entry: phrase + account handle + sector + tone + occasion + shortcode + ulid
"""
import json
import os

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")
OUT_PATH  = os.path.expanduser("~/Desktop/ogz-knowledge/logs/notable_phrases_library.json")

def extract_handle(d):
    """Best-effort account handle from obs JSON."""
    # provenance.source often contains the handle
    source = d.get("provenance", {}).get("source", "")
    for part in source.split(";"):
        part = part.strip()
        if part.startswith("benchmark:@") or part.startswith("benchmark:"):
            return part.replace("benchmark:@","").replace("benchmark:","").strip()
    # Fall back to account_handle_normalized minus OGZ- prefix cleanup
    normalized = d.get("account_handle_normalized", "")
    return normalized

def extract_shortcode(d):
    src = d.get("content_ref", {}).get("source_url", "")
    # https://www.instagram.com/p/SHORTCODE/
    parts = src.rstrip("/").split("/")
    return parts[-1] if parts else ""

entries = []
total_obs = 0
obs_with_phrases = 0

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
        vo = d.get("voice_observations", {})
        tone = vo.get("tone", None)
        occasion = d.get("cultural_notes", {}).get("occasion_relevance", None)
        phrases = vo.get("notable_phrases", [])

        if not phrases:
            continue

        obs_with_phrases += 1
        for phrase in phrases:
            if not phrase or not isinstance(phrase, str):
                continue
            phrase = phrase.strip()
            if not phrase:
                continue
            entries.append({
                "phrase": phrase,
                "account": handle,
                "sector": sector_val,
                "tone": tone,
                "occasion": occasion if occasion not in (None, "none", "None", "null") else None,
                "shortcode": shortcode,
                "observation_ulid": ulid
            })

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"Total obs scanned:      {total_obs}")
print(f"Obs with phrases:       {obs_with_phrases}")
print(f"Total phrase entries:   {len(entries)}")
print(f"Written to: {OUT_PATH}")
