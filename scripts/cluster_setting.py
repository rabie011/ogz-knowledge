#!/usr/bin/env python3
"""
cluster_setting.py
Normalize freeform visual_observations.setting (454 unique values)
into 12 canonical setting categories.

Canonical Settings:
  studio          — controlled studio, product photography, colored/white backgrounds
  restaurant_indoor — indoor dining room, cafe interior, restaurant inside
  restaurant_outdoor — terrace, rooftop, poolside, garden, outdoor seating
  tabletop_food   — food styling flat lay, overhead tabletop spread, tabletop surface
  heritage_setting — najdi, traditional, heritage-themed, diriyah, historic
  kitchen_prep    — kitchen, cooking environment, prep area
  retail_urban    — shops, malls, streets, urban commercial
  event_venue     — ceremony, stadium, arena, event space
  digital_graphic — pure digital, 3D rendered, graphic, animated, illustrated
  outdoor_nature  — nature, park, desert, landscape, exterior outdoor
  home_domestic   — home, bedroom, bathroom, domestic environment
  editorial_lifestyle — editorial campaign, lifestyle shoot, influencer setup

Output: logs/setting_normalization.json
Also updates all obs in-place.
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

SETTING_RULES = [
    # digital/graphic first — must beat studio (some values say "digital graphic")
    ("digital_graphic", lambda v: any(k in v for k in (
        "digital", "graphic", "3d rendered", "3d render", "illustrated",
        "animated", "rendered", "illustration", "cartoon", "motion graphic",
        "quiz graphic", "promotional graphic", "design layout", "graphic design",
        "designed background", "no physical setting", "virtual", "cgi",
    ))),
    # heritage settings — najdi/traditional/historic environments
    ("heritage_setting", lambda v: any(k in v for k in (
        "najdi", "heritage", "traditional", "historic", "diriyah", "at-turaif",
        "turaif", "arabic architecture", "islamic architecture", "old souk",
        "heritage fort", "heritage village", "traditional saudi",
        "al-bujairi", "cushion seating", "floor cushion", "najdi interior",
        "arabic graffiti", "ornate door", "arabian arch",
    ))),
    # kitchen/prep
    ("kitchen_prep", lambda v: any(k in v for k in (
        "kitchen", "cooking", "prep", "chef", "food preparation", "culinary",
        "bakery", "grill station", "open kitchen",
    ))),
    # tabletop food styling
    ("tabletop_food", lambda v: any(k in v for k in (
        "tabletop", "table top", "table surface", "overhead", "flat lay",
        "food styling", "plated", "styled table", "wooden tray", "marble surface",
        "styled spread", "food spread", "dining table from above",
        "ingredient", "ingredient hero", "product on tray",
    ))),
    # event venue
    ("event_venue", lambda v: any(k in v for k in (
        "event", "ceremony", "stadium", "arena", "venue", "award",
        "esports", "gaming center", "concert", "conference", "exhibition",
        "launch event", "grand opening", "opera", "theatre", "auditorium",
    ))),
    # outdoor nature
    ("outdoor_nature", lambda v: any(k in v for k in (
        "outdoor", "nature", "desert", "park", "landscape", "garden",
        "beach", "sea", "mountain", "forest", "waterfall",
        "pop-up", "pop up", "exterior", "open air",
    ))),
    # restaurant outdoor (before indoor — "outdoor pool" etc)
    ("restaurant_outdoor", lambda v: any(k in v for k in (
        "terrace", "rooftop", "poolside", "outdoor seating", "outdoor dining",
        "outdoor restaurant", "outdoor cafe", "wooden terrace",
        "garden seating", "outdoor table",
    ))),
    # restaurant indoor
    ("restaurant_indoor", lambda v: any(k in v for k in (
        "restaurant", "cafe", "dining room", "dining area", "dining hall",
        "dining table", "dining", "lounge", "bistro", "eatery",
        "main hall", "counter", "food court", "coffee shop",
        "curtained dining", "private dining",
    ))),
    # home/domestic
    ("home_domestic", lambda v: any(k in v for k in (
        "home", "domestic", "bedroom", "bathroom", "washroom", "living room",
        "vanity", "mirror", "influencer setup", "influencer setting",
        "everyday lifestyle", "natural influencer",
    ))),
    # retail/urban
    ("retail_urban", lambda v: any(k in v for k in (
        "retail", "mall", "shop", "store", "street", "urban", "city",
        "metro", "building", "construction", "warehouse", "underground",
        "parking", "commercial",
    ))),
    # editorial/lifestyle campaign shoots
    ("editorial_lifestyle", lambda v: any(k in v for k in (
        "editorial", "campaign", "lifestyle", "creator", "influencer",
        "beauty influencer", "brand ambassador", "photoshoot", "photo shoot",
        "behind the scenes", "bts", "asmr",
    ))),
    # studio — catch-all controlled studio
    ("studio",          lambda v: any(k in v for k in (
        "studio", "controlled", "product photography", "white background",
        "black background", "coloured background", "colored background",
        "solid background", "neutral background", "clean background",
        "product shot", "product hero", "product display", "product reveal",
        "product grouping", "product presentation", "product launch",
        "product specification", "product award", "pedestal", "podium",
        "white/neutral", "split colour", "gradient background",
        "sky aesthetic", "bubble", "water splash", "floating",
        "encased", "surreal", "composite",
        "grey textured", "cream background", "editorial beauty",
        "beauty close-up", "dark studio", "dramatic beauty",
        "clean beauty", "beauty application",
    ))),
    # default — anything remaining
    ("restaurant_indoor", lambda v: True),
]


def match_setting(raw: str) -> str:
    v = raw.lower().strip()
    for canonical, rule in SETTING_RULES:
        if rule(v):
            return canonical
    return "restaurant_indoor"


def main():
    before = Counter()
    after  = Counter()
    mapping = defaultdict(lambda: defaultdict(int))

    updated = 0
    total   = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            text = obs_file.read_text()
            data = json.loads(text)
        except Exception:
            continue

        total += 1
        vo  = data.get("visual_observations", {}) or {}
        raw = vo.get("setting")

        if not raw or not isinstance(raw, str) or not raw.strip():
            continue

        canonical = match_setting(raw)
        before[raw] += 1
        mapping[raw][canonical] += 1

        if raw != canonical:
            vo["setting"] = canonical
            data["visual_observations"] = vo
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            updated += 1

        after[canonical] += 1

    # Engagement correlation per canonical setting
    ENG_MAP = {"high": 1.0, "very_high": 1.0, "above_average": 0.75,
               "medium": 0.5, "low": 0.0, "below_average": 0.25}
    setting_eng = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue
        vo = data.get("visual_observations", {}) or {}
        setting = vo.get("setting")
        if not setting:
            continue
        qa = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        setting_eng[setting]["count"] += 1
        setting_eng[setting]["high"]  += is_high
        setting_eng[setting]["sum"]   += eng

    setting_table = []
    for setting, data in sorted(setting_eng.items(), key=lambda x: -x[1]["count"]):
        n = data["count"]
        rate = round(data["high"] / n, 3) if n else 0
        avg  = round(data["sum"] / n, 3) if n else 0
        setting_table.append({
            "setting": setting,
            "count": n,
            "high_engagement_rate": rate,
            "avg_engagement": avg,
            "verdict": (
                "strong_positive" if rate >= 0.70 and n >= 5 else
                "positive"        if rate >= 0.55 and n >= 5 else
                "neutral"         if rate >= 0.40 else
                "weak"            if rate >= 0.25 else
                "avoid"
            )
        })
    setting_table.sort(key=lambda x: -x["high_engagement_rate"])

    log = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "obs_updated": updated,
        "before_unique_count": len(before),
        "canonical_values": [
            "studio", "restaurant_indoor", "restaurant_outdoor", "tabletop_food",
            "heritage_setting", "kitchen_prep", "retail_urban", "event_venue",
            "digital_graphic", "outdoor_nature", "home_domestic", "editorial_lifestyle"
        ],
        "after_distribution": dict(sorted(after.items(), key=lambda x: -x[1])),
        "setting_engagement_table": setting_table,
        "mappings": {
            raw: dict(targets)
            for raw, targets in sorted(mapping.items(), key=lambda x: -sum(x[1].values()))
            if list(targets.keys()) != [raw]
        }
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "setting_normalization.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2)
    )

    print(f"Scanned {total} | Updated {updated} | {len(before)} unique → {len(after)} canonical")
    print(f"\nAfter distribution:")
    for k, v in sorted(after.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {v:3d}")
    print(f"\nSetting engagement ranking:")
    for r in setting_table:
        if r["count"] >= 5:
            print(f"  {r['setting']:<25} n={r['count']:3d} | "
                  f"high={int(r['high_engagement_rate']*100)}% | {r['verdict']}")
    print(f"\nOutput: logs/setting_normalization.json")


if __name__ == "__main__":
    main()
