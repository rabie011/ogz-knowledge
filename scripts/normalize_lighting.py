#!/usr/bin/env python3
"""
normalize_lighting.py
Collapse messy lighting strings → 6 canonical clusters.
Canonical: warm_studio | natural_daylight | dramatic_moody | flat_graphic | cold_studio | mixed_ambient
Updates lighting field in-place across all 648 obs.
"""
import json, re
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

# Map: (substring patterns) → canonical
RULES = [
    # warm first (most common ambiguous)
    (["warm studio",  "warm_studio",  "warm bright",   "warm artificial"], "warm_studio"),
    (["warm ambient", "warm_ambient", "ambient warm"],                      "warm_studio"),
    (["natural",      "daylight",     "sunlight",      "golden hour"],      "natural_daylight"),
    (["dramatic",     "moody",        "low key",       "low-key",
      "high contrast","chiaroscuro"],                                        "dramatic_moody"),
    (["flat",         "graphic",      "digital",       "animated",
      "illustrated",  "2d"],                                                 "flat_graphic"),
    (["cold studio",  "cold_studio",  "cool studio",   "studio artificial",
      "studio controlled", "studio",  "cold",          "bright",
      "branded_bright","branded bright","white bg"],                         "cold_studio"),
    (["mixed",        "ambient neutral","ambient_neutral","ambient"],        "mixed_ambient"),
]

def classify(raw: str) -> str:
    r = raw.lower().strip()
    for patterns, canonical in RULES:
        for p in patterns:
            if p in r:
                return canonical
    return raw  # keep as-is if no match


def main():
    from collections import Counter
    changes = Counter()
    updated = unchanged = 0

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        vo = d.get("visual_observations", {})
        raw = vo.get("lighting", "")
        if not raw:
            continue
        norm = classify(raw)
        if norm != raw:
            vo["lighting"] = norm
            d["visual_observations"] = vo
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            changes[norm] += 1
            updated += 1
        else:
            unchanged += 1

    print(f"Lighting normalized: {updated} updated  |  {unchanged} already canonical")
    print("Result distribution:")
    for k, v in changes.most_common():
        print(f"  {k:<20} {v}")

    LOGS.mkdir(exist_ok=True)
    (LOGS / "normalize_lighting_report.json").write_text(
        json.dumps({"updated": updated, "unchanged": unchanged,
                    "changes": dict(changes)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
