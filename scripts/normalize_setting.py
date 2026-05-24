#!/usr/bin/env python3
"""
normalize_setting.py
Collapse messy setting strings → 10 canonical clusters.
Canonical: restaurant_indoor | restaurant_outdoor | studio | digital_graphic |
           outdoor_nature | heritage_setting | event_venue | tabletop_food |
           home_domestic | retail_urban
"""
import json
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

RULES = [
    (["restaurant_indoor", "restaurant indoor", "indoor restaurant",
      "café indoor",       "cafe indoor",       "indoor dining"],      "restaurant_indoor"),
    (["restaurant_outdoor","restaurant outdoor","outdoor restaurant",
      "outdoor dining",    "terrace"],                                  "restaurant_outdoor"),
    (["digital_graphic",   "digital graphic",   "graphic",    "animated",
      "illustrated",       "motion graphic",    "2d",         "rendered",
      "digital",           "cgi"],                                      "digital_graphic"),
    (["outdoor_nature",    "outdoor nature",    "outdoor park","natural outdoor",
      "beach",             "desert",            "garden",     "park",
      "mountain"],                                                       "outdoor_nature"),
    (["heritage",          "traditional",       "old town",   "souq",
      "old_town",          "historical",        "old city"],             "heritage_setting"),
    (["event_venue",       "event venue",       "stadium",    "arena",
      "conference",        "exhibition",        "venue",      "stage",
      "celebration"],                                                    "event_venue"),
    (["tabletop_food",     "tabletop food",     "tabletop",   "table top",
      "kitchen_prep",      "kitchen prep",      "kitchen",    "food prep",
      "prep station"],                                                   "tabletop_food"),
    (["home_domestic",     "home domestic",     "home ",      "apartment",
      "living room",       "bedroom",           "domestic"],            "home_domestic"),
    (["retail_urban",      "retail urban",      "urban",      "street",
      "city",              "storefront",        "retail"],              "retail_urban"),
    (["studio controlled", "studio solid",      "studio ",    "studio",
      "editorial",         "editorial_lifestyle","editorial lifestyle",
      "controlled",        "white bg",          "seamless"],            "studio"),
]

def classify(raw: str) -> str:
    r = raw.lower().strip()
    for patterns, canonical in RULES:
        for p in patterns:
            if p in r:
                return canonical
    return raw

def main():
    from collections import Counter
    changes = Counter()
    updated = unchanged = 0

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        vo = d.get("visual_observations", {})
        raw = vo.get("setting", "")
        if not raw:
            continue
        norm = classify(raw)
        if norm != raw:
            vo["setting"] = norm
            d["visual_observations"] = vo
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            changes[norm] += 1
            updated += 1
        else:
            unchanged += 1

    print(f"Setting normalized: {updated} updated  |  {unchanged} already canonical")
    print("Result distribution:")
    for k, v in changes.most_common():
        print(f"  {k:<22} {v}")

    LOGS.mkdir(exist_ok=True)
    (LOGS / "normalize_setting_report.json").write_text(
        json.dumps({"updated": updated, "unchanged": unchanged,
                    "changes": dict(changes)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
