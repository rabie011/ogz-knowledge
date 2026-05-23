#!/usr/bin/env python3
"""
enrich_missing_fields.py
Back-fill 4 low-coverage fields across existing observations.
Only fills NULL/MISSING values — never overwrites analyst data.

Fields:
  1. cultural_notes.occasion_relevance  (57.8%) → pattern-slug inference, default evergreen
  2. cultural_notes.heritage_vs_modern  (76.8%) → pattern+setting+tone signal scoring
  3. voice_observations.dialect_detected (69.0%) → account dominant dialect from brand_dna
  4. cultural_notes.hospitality_cues    (43.2%) → props+setting cue list inference

  capture_date: SKIPPED — post dates cannot be inferred from obs content alone.

Enrichment sources tracked in logs/enrichment_report.json (not written to obs files).
Output: modifies obs in-place + logs/enrichment_report.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE      = Path(__file__).parent.parent
OBS_ROOT  = BASE / "11_who_to_learn_from" / "observations"
LOGS      = BASE / "logs"
BRAND_DNA = LOGS / "brand_dna"

# ── Occasion inference map ───────────────────────────────────────────────────
PATTERN_OCCASION = {
    "eid_occasion_greeting":           "eid_al_fitr",
    "eid_al_adha_occasion":            "eid_al_adha",
    "eid_celebration_visual":          "eid_al_fitr",
    "ramadan_iftar_warmth":            "ramadan",
    "ramadan_iftar_table":             "ramadan",
    "ramadan_countdown":               "ramadan",
    "ramadan_atmosphere":              "ramadan",
    "ramadan_occasion":                "ramadan",
    "national_day_pride":              "national_day",
    "national_day_modernity_heritage": "national_day",
    "saudi_national_day_visual":       "national_day",
    "founding_day_dirayyah_heritage":  "founding_day",
    "founding_day_visual":             "founding_day",
    "national_sports_day_occasion":    "national_sports_day",
    "football_occasion_tie_in":        "national_sports_day",
    "sports_passion_peg":              "national_sports_day",
    "winter_comfort_cozy":             "winter_seasonal",
    "winter_seasonal_launch":          "winter_seasonal",
    "seasonal_summer_heat":            "summer_campaign",
    "summer_occasion":                 "summer_campaign",
    "world_coffee_day":                "world_coffee_day",
    "world_food_heritage_day":         "world_food_heritage_day",
    "graduation_season":               "graduation_season",
    "mother_day_tribute":              "mothers_day",
    "valentines_occasion":             "valentines_day",
    "vision_2030_moment":              "vision_2030_moment",
    "hajj_season_content":             "hajj",
}

# ── Heritage/modern signal sets ───────────────────────────────────────────────
HERITAGE_PATS = {
    "heritage_storytelling_hook", "cultural_object_hero", "community_pride_statement",
    "founding_day_dirayyah_heritage", "saudi_dining_ritual", "nostalgia_cultural_reference",
    "national_day_modernity_heritage", "ramadan_iftar_warmth", "ramadan_iftar_table",
    "traditional_craftsmanship_focus", "arabic_calligraphy_integration",
    "dallah_qahwa_ritual", "eid_occasion_greeting", "behind_the_craft",
    "hand_in_motion_pour_or_place", "interior_architectural_framing",
}
MODERN_PATS = {
    "educational_explainer", "lifestyle_embed", "trend_riding", "price_offer_graphic",
    "csr_brand_story", "interactive_question_post", "influencer_takeover_post",
    "carousel_swipe_mechanic", "product_launch_countdown", "lifestyle_environment_integration",
}
HERITAGE_SETTINGS  = {"heritage_setting"}
MODERN_SETTINGS    = {"studio", "editorial_lifestyle"}
BLENDED_SETTINGS   = {"restaurant_indoor", "restaurant_outdoor", "tabletop_food",
                       "outdoor_nature", "retail_urban"}
HERITAGE_TONES     = {"nostalgic", "storytelling", "warm"}
MODERN_TONES       = {"aspirational", "informative", "educational", "transactional"}

# ── Prop → hospitality cue map ────────────────────────────────────────────────
PROP_CUE_MAP = [
    (["qahwa","dallah","coffee pot","arabic coffee","قهوة","دلة","dalah"],
     "traditional_coffee_service"),
    (["dates","tamr","تمر","date"],
     "date_offering"),
    (["incense","bakhoor","oud","بخور","عود","bukhoor"],
     "incense_bakhoor"),
    (["chai","tea","شاي","كرك","karak"],
     "tea_service"),
    (["abundant","spread","feast","مائدة","وليمة","platter"],
     "abundant_food_spread"),
    (["golden teapot","silver tray","golden tray","مباخر"],
     "premium_presentation"),
    (["rose water","ماء الورد","rosewater"],
     "rosewater_offering"),
    (["poolside","luxury pool","luxury setting"],
     "poolside_luxury_setting"),
    (["sahlab","suhoor","سحور","صاحب"],
     "suhoor_gathering"),
]


def load_account_dialects() -> dict:
    """dominant dialect per account from brand_dna profiles."""
    result = {}
    if not BRAND_DNA.exists():
        return result
    for f in BRAND_DNA.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            acc  = d.get("account","")
            dial = d.get("dominant_dialect","")
            if acc and dial and dial not in ("", "unknown", "None", "null"):
                result[acc] = dial
        except: pass
    return result


def get_slugs(data: dict) -> set:
    slugs = set()
    for pm in (data.get("pattern_matches") or []):
        s = pm.get("pattern_slug","") if isinstance(pm, dict) else pm
        if s: slugs.add(s)
    return slugs


def is_empty(v) -> bool:
    """True if value is None, empty string, or the string 'null'/'None'."""
    if v is None: return True
    if isinstance(v, str) and v.strip().lower() in ("", "null", "none", "unknown"): return True
    return False


# ── Field inference functions ─────────────────────────────────────────────────

def infer_occasion(data: dict) -> tuple:
    cn  = data.get("cultural_notes") or {}
    if not is_empty(cn.get("occasion_relevance")):
        return None, None  # already set
    slugs = get_slugs(data)
    for slug in slugs:
        occ = PATTERN_OCCASION.get(slug)
        if occ:
            return occ, f"pattern:{slug}"
    return "evergreen", "default:no_occasion_pattern"


def infer_heritage(data: dict) -> tuple:
    cn = data.get("cultural_notes") or {}
    if not is_empty(cn.get("heritage_vs_modern")):
        return None, None
    slugs   = get_slugs(data)
    vv      = data.get("visual_observations") or {}
    vo      = data.get("voice_observations") or {}
    setting = vv.get("setting","")
    tone    = str(vo.get("tone","") or "").lower()
    hosp    = len(cn.get("hospitality_cues") or [])

    h = 0; m = 0
    h += 3 * len(slugs & HERITAGE_PATS)
    m += 3 * len(slugs & MODERN_PATS)
    if setting in HERITAGE_SETTINGS:  h += 2
    if setting in MODERN_SETTINGS:    m += 2
    if setting in BLENDED_SETTINGS:   h += 1; m += 1
    if tone in HERITAGE_TONES:        h += 1
    if tone in MODERN_TONES:          m += 1
    if hosp >= 2:                     h += 1

    if h == 0 and m == 0:
        return "modern", "default:no_signals"
    if h >= m + 2:
        return "heritage", f"signals:h={h},m={m}"
    if m >= h + 2:
        return "modern",  f"signals:h={h},m={m}"
    return "blended",     f"signals:h={h},m={m}"


def infer_dialect(data: dict, account_dialects: dict) -> tuple:
    vo = data.get("voice_observations") or {}
    if not is_empty(vo.get("dialect_detected")):
        return None, None
    acc  = data.get("account_handle_normalized","")
    dial = account_dialects.get(acc)
    if dial:
        return dial, f"account_dominant"
    return "gulf_arabic", "default:saudi_sector"


def infer_hospitality(data: dict) -> tuple:
    cn = data.get("cultural_notes") or {}
    if cn.get("hospitality_cues") is not None:  # already set (even [])
        return None, None
    vv     = data.get("visual_observations") or {}
    props  = vv.get("props_visible") or []
    if isinstance(props, dict):
        props = list(props.keys()) + [str(v) for v in props.values() if v]
    props_str = " ".join(str(p).lower() for p in props if p)
    setting   = (vv.get("setting") or "").lower()

    cues = []
    for kws, cue in PROP_CUE_MAP:
        if any(k in props_str for k in kws) and cue not in cues:
            cues.append(cue)
    if setting == "heritage_setting" and "heritage_environment" not in cues:
        cues.append("heritage_environment")

    src = "props_and_setting" if cues else "assessed_none"
    return cues, src


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    account_dialects = load_account_dialects()
    print(f"Loaded dialect profiles for {len(account_dialects)} accounts")

    stats = defaultdict(int)
    occasion_sources = Counter()
    heritage_sources = Counter()
    dialect_sources  = Counter()
    hosp_sources     = Counter()
    log_entries      = []

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        stats["total"] += 1
        changes = {}

        # Ensure dicts exist
        if not isinstance(data.get("cultural_notes"), dict):
            data["cultural_notes"] = {}
        if not isinstance(data.get("voice_observations"), dict):
            data["voice_observations"] = {}

        # 1. Occasion
        occ_v, occ_s = infer_occasion(data)
        if occ_v is not None:
            data["cultural_notes"]["occasion_relevance"] = occ_v
            stats["occasion_filled"] += 1
            occasion_sources[occ_s] += 1
            changes["occasion_relevance"] = {"value": occ_v, "source": occ_s}

        # 2. Heritage/modern
        hvm_v, hvm_s = infer_heritage(data)
        if hvm_v is not None:
            data["cultural_notes"]["heritage_vs_modern"] = hvm_v
            stats["heritage_filled"] += 1
            heritage_sources[hvm_s[:30]] += 1
            changes["heritage_vs_modern"] = {"value": hvm_v, "source": hvm_s}

        # 3. Dialect
        dial_v, dial_s = infer_dialect(data, account_dialects)
        if dial_v is not None:
            data["voice_observations"]["dialect_detected"] = dial_v
            stats["dialect_filled"] += 1
            dialect_sources[dial_s] += 1
            changes["dialect_detected"] = {"value": dial_v, "source": dial_s}

        # 4. Hospitality cues
        hosp_v, hosp_s = infer_hospitality(data)
        if hosp_v is not None:
            data["cultural_notes"]["hospitality_cues"] = hosp_v
            stats["hospitality_filled"] += 1
            hosp_sources[hosp_s] += 1
            changes["hospitality_cues"] = {"count": len(hosp_v), "cues": hosp_v, "source": hosp_s}

        if changes:
            stats["files_modified"] += 1
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            log_entries.append({
                "file": obs_file.name,
                "account": data.get("account_handle_normalized","?"),
                "changes": changes,
            })

    # ── Print results ─────────────────────────────────────────────────────────
    print(f"\nEnrichment complete")
    print(f"  Total obs processed  : {stats['total']}")
    print(f"  Files modified       : {stats['files_modified']}")
    print(f"\n  Field fills:")
    print(f"    occasion_relevance   : +{stats['occasion_filled']} obs")
    print(f"    heritage_vs_modern   : +{stats['heritage_filled']} obs")
    print(f"    dialect_detected     : +{stats['dialect_filled']} obs")
    print(f"    hospitality_cues     : +{stats['hospitality_filled']} obs")
    print(f"\n  capture_date         : SKIPPED (not inferrable without external data)")

    print(f"\n  Occasion sources:")
    for src, cnt in occasion_sources.most_common(8):
        print(f"    {cnt:>4}  {src}")

    print(f"\n  Heritage/modern sources:")
    for src, cnt in heritage_sources.most_common(8):
        print(f"    {cnt:>4}  {src}")

    print(f"\n  Dialect sources:")
    for src, cnt in dialect_sources.most_common():
        print(f"    {cnt:>4}  {src}")

    # Expected coverage after enrichment
    print(f"\n  Expected field coverage after enrichment:")
    t = stats["total"]
    for field, filled, prev_pct in [
        ("occasion_relevance",  stats["occasion_filled"],  57.8),
        ("heritage_vs_modern",  stats["heritage_filled"],  76.8),
        ("dialect_detected",    stats["dialect_filled"],   69.0),
        ("hospitality_cues",    stats["hospitality_filled"], 43.2),
    ]:
        prev_n = int(prev_pct / 100 * t)
        new_n  = prev_n + filled
        new_pct = round(new_n / t * 100, 1)
        print(f"    {field:<28} {prev_pct:>5}% → {new_pct:>5}%  (+{filled})")

    # Save report
    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "stats": dict(stats),
        "occasion_sources": dict(occasion_sources),
        "heritage_sources": dict(heritage_sources),
        "dialect_sources": dict(dialect_sources),
        "hospitality_sources": dict(hosp_sources),
        "capture_date_note": "Skipped — post dates cannot be inferred from obs content. Requires Instagram API or manual lookup.",
        "enrichment_log": log_entries[:100],
    }
    LOGS.mkdir(exist_ok=True)
    (LOGS / "enrichment_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nOutput: logs/enrichment_report.json")


if __name__ == "__main__":
    main()
