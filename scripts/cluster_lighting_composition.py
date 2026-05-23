#!/usr/bin/env python3
"""
cluster_lighting_composition.py
Normalize freeform visual_observations.lighting (435 unique)
and visual_observations.composition_style (408 unique) into canonical values.

Canonical Lightings (9):
  warm_studio       — warm studio, warm golden, warm product spotlight
  cold_studio       — clean white/bright studio, studio artificial, studio flat
  flat_graphic      — flat digital, no photographic, pure graphic, 2D digital
  natural_daylight  — natural daylight, outdoor, sunlit, golden hour
  dramatic_moody    — dramatic, dark, high contrast, moody, low key
  warm_ambient      — warm bright, warm indoor, soft warm, candle glow
  ambient_neutral   — neutral ambient, available light, natural indoor
  branded_bright    — bright branded, branded colors, vibrant flat
  mixed_lighting    — mixed, combination, complex lighting setup

Canonical Compositions (9):
  product_hero_closeup  — close-up product hero, isolated product
  overhead_spread       — overhead tabletop, flat lay, bird's eye
  lifestyle_integrated  — lifestyle environment integration, in-scene product
  architectural_frame   — architectural framing, interior architecture
  portrait_face         — portrait, face close-up, centered person shot
  graphic_text          — graphic, text-heavy, digital layout, quote card
  before_after          — before/after, transformation reveal
  multi_product         — carousel shade range, multi-product, product family
  documentary_candid    — documentary, event, candid, BTS, UGC-style
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high": 1.0, "very_high": 1.0, "above_average": 0.75,
           "medium": 0.5, "low": 0.0, "below_average": 0.25}

# ── Lighting rules ───────────────────────────────────────────────────────────
LIGHTING_RULES = [
    ("flat_graphic", lambda v: any(k in v for k in (
        "flat digital", "no photographic", "digital", "graphic", "flat graph",
        "2d", "animation", "illustration", "green gold white",
    ))),
    ("dramatic_moody", lambda v: any(k in v for k in (
        "dramatic", "dark", "moody", "low key", "low-key", "high contrast",
        "noir", "shadow", "chiaroscuro", "cinematic shadow",
    ))),
    ("warm_studio", lambda v: any(k in v for k in (
        "warm studio", "warm golden", "warm product spotlight", "warm_studio",
        "warm professional", "gold studio", "golden studio",
    ))),
    ("cold_studio", lambda v: any(k in v for k in (
        "clean white studio", "clean bright studio", "studio flat white",
        "studio artificial", "studio controlled", "cool studio", "white studio",
        "clean studio", "clinical studio", "neutral studio", "studio white",
        "bright studio", "cool white", "studio_", "studio soft",
    ))),
    ("warm_ambient", lambda v: any(k in v for k in (
        "warm bright", "warm indoor", "soft warm", "candle", "lantern",
        "amber", "firelight", "candlelight", "soft golden",
        "warm natural", "warm glow", "warm interior", "warm overhead",
        "warm soft", "warm light", "warm_", "warm,",
    ))),
    ("natural_daylight", lambda v: any(k in v for k in (
        "natural", "daylight", "sunlit", "sunlight", "outdoor light",
        "golden hour", "dusk", "dawn", "overcast", "sun",
        "window light", "available light outdoor",
    ))),
    ("branded_bright", lambda v: any(k in v for k in (
        "bright branded", "branded", "bright clean", "bright flat",
        "vibrant", "neon", "colored light", "red background",
        "green background", "bold color",
    ))),
    ("ambient_neutral", lambda v: any(k in v for k in (
        "ambient", "neutral", "available light", "natural indoor",
        "soft indoor", "diffuse", "flat bright", "clean bright",
        "bright graphic", "clean graphic", "flat bright",
    ))),
    ("mixed_lighting", lambda v: True),  # fallback
]

# ── Composition rules ─────────────────────────────────────────────────────────
COMPOSITION_RULES = [
    ("before_after", lambda v: any(k in v for k in (
        "before", "after", "transformation", "reveal", "comparison",
    ))),
    ("portrait_face", lambda v: any(k in v for k in (
        "portrait", "face close", "centered portrait", "headshot",
        "close-up on person", "person close", "model close",
    ))),
    ("overhead_spread", lambda v: any(k in v for k in (
        "overhead", "over head", "flat lay", "flat-lay", "bird", "top down",
        "top-down", "birds eye", "bird's eye", "overhead_tabletop",
    ))),
    ("graphic_text", lambda v: any(k in v for k in (
        "graphic", "text", "quote", "typograph", "digital layout",
        "minimal text", "seasonal_campaign_graphic", "graphic design",
        "text overlay", "info card", "announcement",
    ))),
    ("multi_product", lambda v: any(k in v for k in (
        "shade range", "product family", "product lineup", "multi",
        "range", "bundle", "collection", "products on", "several product",
        "product grouping",
    ))),
    ("documentary_candid", lambda v: any(k in v for k in (
        "documentary", "candid", "bts", "behind the scenes", "ugc",
        "event", "street", "reportage", "real life", "authentic",
        "influencer", "creator", "get-ready", "grwm",
    ))),
    ("lifestyle_integrated", lambda v: any(k in v for k in (
        "lifestyle", "environment", "in-scene", "in scene", "context",
        "setting integration", "lifestyle_environment", "natural context",
        "in use", "in situ",
    ))),
    ("architectural_frame", lambda v: any(k in v for k in (
        "architectural", "architecture", "arch", "frame", "framing",
        "doorway", "window frame", "arched",
    ))),
    ("product_hero_closeup", lambda v: True),  # fallback
]


def match_rule(raw, rules):
    v = raw.lower().strip()
    for canonical, rule in rules:
        if rule(v):
            return canonical
    return rules[-1][0]


def main():
    # First pass: collect raw values
    lighting_before    = Counter()
    composition_before = Counter()

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue
        vo = data.get("visual_observations", {}) or {}
        l = vo.get("lighting")
        c = vo.get("composition_style")
        if l and isinstance(l, str):
            lighting_before[l.strip()] += 1
        if c and isinstance(c, str):
            composition_before[c.strip()] += 1

    # Second pass: update in-place
    lighting_after    = Counter()
    composition_after = Counter()
    lighting_mapping    = defaultdict(lambda: defaultdict(int))
    composition_mapping = defaultdict(lambda: defaultdict(int))
    updated = 0
    total   = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            text = obs_file.read_text()
            data = json.loads(text)
        except Exception:
            continue

        total += 1
        changed = False
        vo = data.get("visual_observations", {}) or {}

        raw_l = vo.get("lighting")
        if raw_l and isinstance(raw_l, str) and raw_l.strip():
            can_l = match_rule(raw_l, LIGHTING_RULES)
            lighting_mapping[raw_l.strip()][can_l] += 1
            if raw_l != can_l:
                vo["lighting"] = can_l
                changed = True
            lighting_after[can_l] += 1

        raw_c = vo.get("composition_style")
        if raw_c and isinstance(raw_c, str) and raw_c.strip():
            can_c = match_rule(raw_c, COMPOSITION_RULES)
            composition_mapping[raw_c.strip()][can_c] += 1
            if raw_c != can_c:
                vo["composition_style"] = can_c
                changed = True
            composition_after[can_c] += 1

        if changed:
            data["visual_observations"] = vo
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            updated += 1

    # Engagement per canonical lighting and composition
    setting_eng = defaultdict(lambda: {"count": 0, "high": 0})
    comp_eng    = defaultdict(lambda: {"count": 0, "high": 0})

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue
        vo  = data.get("visual_observations", {}) or {}
        qa  = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        lighting    = vo.get("lighting")
        composition = vo.get("composition_style")

        if lighting:
            setting_eng[lighting]["count"] += 1
            setting_eng[lighting]["high"]  += is_high
        if composition:
            comp_eng[composition]["count"] += 1
            comp_eng[composition]["high"]  += is_high

    def eng_table(counter_dict, count_dict):
        rows = []
        for val, n in count_dict.most_common():
            h = counter_dict[val]["high"]
            rate = round(h / n, 3) if n else 0
            rows.append({
                "value": val, "count": n,
                "high_engagement_rate": rate,
                "verdict": (
                    "strong_positive" if rate >= 0.70 and n >= 5 else
                    "positive"        if rate >= 0.55 and n >= 5 else
                    "neutral"         if rate >= 0.40 else
                    "weak"            if rate >= 0.25 else
                    "avoid"
                ) if n >= 3 else "insufficient_data"
            })
        rows.sort(key=lambda x: -x["high_engagement_rate"])
        return rows

    log = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "obs_updated": updated,
        "lighting": {
            "before_unique_count": len(lighting_before),
            "canonical_values": [r[0] for r in LIGHTING_RULES],
            "after_distribution": dict(sorted(lighting_after.items(), key=lambda x: -x[1])),
            "engagement_table": eng_table(setting_eng, lighting_after),
        },
        "composition": {
            "before_unique_count": len(composition_before),
            "canonical_values": [r[0] for r in COMPOSITION_RULES],
            "after_distribution": dict(sorted(composition_after.items(), key=lambda x: -x[1])),
            "engagement_table": eng_table(comp_eng, composition_after),
        },
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "lighting_composition_normalization.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2)
    )

    print(f"Scanned {total} | Updated {updated}")
    print(f"\nLighting: {len(lighting_before)} unique → {len(lighting_after)} canonical")
    for k, v in sorted(lighting_after.items(), key=lambda x: -x[1]):
        print(f"  {k:<22} {v:3d}")

    print(f"\nComposition: {len(composition_before)} unique → {len(composition_after)} canonical")
    for k, v in sorted(composition_after.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {v:3d}")

    print(f"\nLighting engagement ranking:")
    for r in log["lighting"]["engagement_table"]:
        if r["count"] >= 5:
            print(f"  {r['value']:<22} n={r['count']:3d} | "
                  f"high_eng={int(r['high_engagement_rate']*100):3d}% | {r['verdict']}")

    print(f"\nComposition engagement ranking:")
    for r in log["composition"]["engagement_table"]:
        if r["count"] >= 5:
            print(f"  {r['value']:<25} n={r['count']:3d} | "
                  f"high_eng={int(r['high_engagement_rate']*100):3d}% | {r['verdict']}")

    print(f"\nOutput: logs/lighting_composition_normalization.json")


if __name__ == "__main__":
    main()
