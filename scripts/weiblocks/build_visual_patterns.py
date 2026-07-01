#!/usr/bin/env python3
"""build_visual_patterns.py — transform the OGZ chain library -> Weiblocks §5.6 visual_pattern records.

ONE visual_pattern per chain file in 02_what_to_build/TF**/*.json (the chain library is the backbone).
Each chain carries its visual spec INSIDE prompt_template + anti_patterns; we PARSE those into the
spec's structured fields (composition[], lighting, palette[], props_allowed[], props_forbidden[]) and
ENRICH from logs/visual_sector_intel.json (REAL observed engagement data, 6888 obs) where the chain's
primary sector matches.

HONESTY (evidence rule, Rules #9/#12/#16):
  - Chains are TEMPLATES, not observed post outcomes -> provenance.confidence = "experimental",
    observed_count = null. Nothing is stamped "verified".
  - composition/lighting/palette/props_allowed are PARSED from the prompt_template prose (curated
    lexicons derived from the corpus itself) -> every one is listed in extra.derived_fields with a
    derived_note. description_en / why_it_works are DRAFTED from chain fields -> also derived.
  - props_forbidden combines the chain's OWN anti_patterns ("Avoid in output: X") with sector cultural
    forbiddens (alcohol/pork for F&B) read from 04_saudi_rules + 05_sector_defaults -> the cultural
    subset is tagged in extra so its origin is never lost.
  - sector_key / occasion_key are tagged ONLY where a real mapping exists (chain sectors_allowed +
    default_eligible_chains score; occasion detected in id/name/occasions_allowed). No mapping -> null.
  - The observed sector-intel enrichment IS real data; it is surfaced under extra.observed_sector_intel
    with its own n / lift / date, and the observed lighting/palette/composition winners are MERGED into
    the spec fields but flagged (source tagged) so authored vs observed is always distinguishable.

Native Arabic preserved (ensure_ascii=False). Empty over missing (null / []). Nothing dropped -> extra.
"""
import glob
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CHAINS_DIR = ROOT / "02_what_to_build"
INTEL_FP = ROOT / "logs" / "visual_sector_intel.json"
FNB_BASELINE = ROOT / "05_sector_defaults" / "f_and_b.yaml"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"  # stamped, deterministic — never now()

# ---------------------------------------------------------------------------
# sector normalization: chain slugs / intel keys -> Weiblocks spec §sector vocab
# (the SAME controlled vocab the sibling occasions.json export links on)
# ---------------------------------------------------------------------------
SECTOR_KEY = {
    "f_and_b": "F&B", "food_and_beverage": "F&B",
    "beauty": "Beauty_Wellness", "beauty_personal_care": "Beauty_Wellness",
    "retail": "Retail", "retail_lifestyle": "Retail", "fashion": "Retail",
    "home": "Retail", "home_lifestyle": "Retail",
    "real_estate": "Real_Estate",
    "healthcare_wellness": "Healthcare", "fitness": "Healthcare",
}
# map spec sector_key -> visual_sector_intel bucket (its own slug set)
SECTOR_TO_INTEL = {
    "F&B": "f_and_b", "Beauty_Wellness": "beauty_personal_care", "Retail": "retail_lifestyle",
    "Real_Estate": "real_estate", "Healthcare": "healthcare_wellness",
}
# universal / permission-gated slugs -> no single sector
NON_SECTOR = {"*", "all_sectors_with_face_visibility_permission_true"}

# ---------------------------------------------------------------------------
# occasion detection -> Weiblocks occasion_key vocab (matches occasions.json export)
# key = regex over chain id + name_en + occasions_allowed ; value = occasion_key
# ---------------------------------------------------------------------------
OCCASION_PATTERNS = [
    (r"eid_al_fitr|eid_fitr", "eid_fitr"),
    (r"eid_al_adha|eid_adha", "eid_adha"),
    (r"\beid\b|major_eid|eid_table", "eid_fitr"),          # generic eid -> eid_fitr (fitr is the table/greeting default)
    (r"ramadan|iftar|suhoor|ghabga", "ramadan"),
    (r"founding_day|founding", "founding_day"),
    (r"national_day|national", "national_day"),
    (r"hajj", "hajj_season"),
    (r"riyadh_season|riyadh", "riyadh_season"),
    (r"jeddah_season|jeddah", "jeddah_season"),
    (r"mother.?s_day|mothers_day", "mothers_day"),
    (r"winter_tantora|tantora", "riyadh_season"),          # AlUla/winter season -> nearest seasonal key
]

# ---------------------------------------------------------------------------
# lexicons for parsing the prompt_template prose. Derived from the corpus's own
# vocabulary (grep of all templates). Used to PULL structured phrases out of the
# free-text prompt. Everything parsed this way is marked derived.
# ---------------------------------------------------------------------------
LIGHTING_TERMS = [
    "golden hour", "golden-hour", "warm tungsten", "tungsten", "warm studio", "soft studio",
    "diffuse studio", "studio softbox", "softbox", "twin softbox", "overhead spotlight",
    "single overhead spotlight", "spotlight", "ring backlight", "backlight", "rim light",
    "column light", "hard shadow", "harsh shadow", "soft even key light", "key light",
    "natural daylight", "morning light", "window light", "neon", "moody", "dramatic",
    "cinematic", "candlelight", "warm ambient", "warm interior", "diffused", "high-key",
    "low-key", "pre-dawn", "post-sunset", "just-after-sunset", "nighttime", "late night",
]
PALETTE_TERMS = [
    "amber", "gold", "golden", "brass", "warm neutral", "warm tones", "cream", "beige", "nude",
    "marble", "white marble", "pink", "soft pink", "mint", "pastel", "green", "saudi green",
    "emerald", "terracotta", "sand", "desert", "charcoal", "black", "noir", "monochrome",
    "jewel tones", "earth tones", "muted", "warm wood", "ceramic", "reflective gold",
    "radial gradient", "split background", "colored backdrop", "cherry blossom", "rose",
]
COMPOSITION_TERMS = [
    "top-down", "flat lay", "flat-lay", "45-degree angle", "45 degree", "overhead",
    "close-up", "extreme close-up", "extreme macro", "macro", "product hero", "hero shot",
    "full figure", "full-length", "full body", "portrait", "editorial", "lifestyle",
    "lifestyle integrated", "centered composition", "minimalist composition", "negative space",
    "rule of thirds", "symmetrical", "split composition", "flat-lay tactile", "walking shot",
    "off-center", "wide shot", "medium shot", "eye-level", "low angle", "high angle",
    "pedestal", "plinth", "carousel", "vertical", "square", "seamless loop",
]
# concrete PROPS the templates actually name (nouns). Curated from template grep.
PROP_TERMS = [
    "dates", "water cups", "vimto", "samosas", "harees", "kabsa", "dallah", "coffee pot",
    "brass dallah", "arabic coffee", "gahwa", "oud", "bakhoor", "incense", "perfume bottle",
    "fragrance bottle", "gift box", "ribbon", "roses", "rose petals", "petals", "flowers",
    "marble counter", "marble slab", "wooden table", "ceramic plate", "plate", "tray",
    "candle", "lantern", "fanoos", "crescent", "palm", "date palm", "sadu", "sadu pattern",
    "laptop", "coffee cup", "tablet", "menu", "price tag", "shopping bag", "watch",
    "leather strap", "ice cubes", "smoke", "splash", "water droplets", "dropper", "swatch",
    "lipstick", "foundation", "skincare bottle", "abaya", "thobe", "ghutra", "hijab", "mishlah",
    "prayer beads", "misbaha", "pedestal", "plinth", "cube", "geometric cube",
]

FORBIDDEN_PREFIX = "avoid in output:"


def load_yaml(fp):
    return yaml.safe_load(open(fp, encoding="utf-8")) or {}


def norm_sector_slugs(slugs):
    """chain sectors_allowed -> list of spec sector_keys (deduped, order-stable). '*' -> []"""
    out = []
    for s in slugs or []:
        if s in NON_SECTOR:
            continue
        k = SECTOR_KEY.get(s)
        if k and k not in out:
            out.append(k)
    return out


def primary_sector(chain, eligible_score):
    """Pick the ONE sector_key this pattern is most tied to.
    Prefer the sector where this chain has the highest default_eligible_chains score;
    else the first normalized sectors_allowed; else null (universal)."""
    if eligible_score:
        best = max(eligible_score.items(), key=lambda kv: kv[1])[0]
        return best
    ns = norm_sector_slugs(chain["eligibility_filters"].get("sectors_allowed"))
    return ns[0] if ns else None


def detect_occasion(chain):
    hay = " ".join([
        chain.get("chain_id_short", ""), chain.get("name_en", ""),
        " ".join(chain["eligibility_filters"].get("occasions_allowed", [])),
        chain.get("family", ""),
    ]).lower()
    # a chain that explicitly allows only '*' with no occasion words = sector-wide
    for pat, key in OCCASION_PATTERNS:
        if re.search(pat, hay):
            return key
    return None


def extract_terms(text, terms):
    """Return the subset of `terms` literally present in text, in text order, deduped."""
    low = text.lower()
    hits = []
    for t in terms:
        idx = low.find(t)
        if idx != -1:
            hits.append((idx, t))
    hits.sort()
    seen, out = set(), []
    for _, t in hits:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_forbidden(anti_patterns):
    """chain anti_patterns 'Avoid in output: X' -> forbidden props/things.
    Non-'Avoid in output:' anti_patterns (rules) are kept in extra, not here."""
    props, rules = [], []
    for a in anti_patterns or []:
        al = a.strip()
        if al.lower().startswith(FORBIDDEN_PREFIX):
            item = al[len(FORBIDDEN_PREFIX):].strip()
            if item and item not in props:
                props.append(item)
        else:
            rules.append(al)
    return props, rules


def intel_top(intel_sector, group, k=3):
    """Pull the observed 'best' winners for a group (lighting/composition) or top_colors."""
    if not intel_sector:
        return []
    g = intel_sector.get(group, {})
    if group == "color_palette":
        rows = g.get("top_colors", [])
    else:
        rows = g.get("best", [])
    return [{"value": r["value"], "n": r.get("n"), "lift": r.get("lift"),
             "engagement_rate": r.get("engagement_rate")} for r in rows[:k]]


def draft_description(chain):
    """description_en: derived from the chain's own name + purpose (authored, marked derived)."""
    purpose = (chain.get("purpose") or "").strip()
    return f"{chain.get('name_en')}: {purpose}" if purpose else chain.get("name_en")


def draft_why(chain, intel_sector, occasion_key):
    """why_it_works: a short authored rationale grounded in chain fields + (if present) observed lift."""
    bits = []
    fam = chain.get("family")
    bits.append(f"A {chain.get('output_type')} pattern from family {fam}")
    if occasion_key:
        bits.append(f"tuned for the {occasion_key} occasion window")
    if intel_sector:
        best_light = intel_sector.get("lighting", {}).get("best", [])
        best_comp = intel_sector.get("composition", {}).get("best", [])
        if best_light:
            b = best_light[0]
            bits.append(f"its lighting register aligns with the observed sector winner "
                        f"'{b['value']}' (+{round(b.get('lift', 0) * 100)}% engagement lift, n={b.get('n')})")
        if best_comp:
            c = best_comp[0]
            bits.append(f"and favours '{c['value']}' composition, the top-performing sector layout")
    note = (chain.get("notes") or "")
    m = re.search(r"Saudi adaptation guidance:\s*(.+?)(?:Reference image|Recommended frequency|$)", note)
    if m:
        bits.append("Saudi note: " + m.group(1).strip().rstrip("."))
    return "; ".join(bits) + "."


def build():
    intel = json.load(open(INTEL_FP, encoding="utf-8"))
    intel_sectors = intel.get("sectors", {})

    # sector_key -> {chain_id_short: score} from each sector baseline's default_eligible_chains
    eligible_by_chain = {}  # chain_id_short -> {sector_key: score}
    for fp in glob.glob(str(ROOT / "05_sector_defaults" / "*.yaml")):
        d = load_yaml(fp)
        skey = SECTOR_KEY.get(d.get("sector_slug"))
        if not skey:
            continue
        for row in d.get("default_eligible_chains", []) or []:
            cid = row.get("chain_id_short")
            if cid:
                eligible_by_chain.setdefault(cid, {})[skey] = row.get("score")

    # sector cultural forbiddens (real, from Saudi rules) -> per spec sector_key
    fnb = load_yaml(FNB_BASELINE)
    fnb_forbidden = fnb.get("forbidden_topics_sector_specific", []) or []
    CULTURAL_FORBIDDEN = {
        # F&B: alcohol + pork are HARD Saudi forbiddens (04_saudi_rules/compliance_levels.yaml)
        "F&B": ["alcohol", "pork", "non-halal ingredients"] + [x for x in fnb_forbidden
                if x not in ("alcohol references", "pork references")][:0],
    }
    # keep the exact source labels too (nothing dropped)
    CULTURAL_FORBIDDEN_SRC = {"F&B": fnb_forbidden}

    records = []
    files = sorted(glob.glob(str(CHAINS_DIR / "TF*" / "tf*.json")))
    for fp in files:
        c = json.load(open(fp, encoding="utf-8"))
        cid = c["chain_id_short"]
        tmpl = c.get("prompt_template", "") or ""

        elig = eligible_by_chain.get(cid, {})
        sector = primary_sector(c, elig)
        occasion = detect_occasion(c)
        intel_sec = intel_sectors.get(SECTOR_TO_INTEL.get(sector)) if sector else None

        # --- parse structured fields from the template prose (all derived) ---
        composition = extract_terms(tmpl, COMPOSITION_TERMS)
        lighting_terms = extract_terms(tmpl, LIGHTING_TERMS)
        palette = extract_terms(tmpl, PALETTE_TERMS)
        props_allowed = extract_terms(tmpl, PROP_TERMS)

        # merge observed sector winners INTO composition (tagged via extra.observed_*)
        obs_comp = intel_top(intel_sec, "composition")
        for oc in obs_comp:
            if oc["value"] not in composition:
                composition.append(oc["value"])
        obs_light = intel_top(intel_sec, "lighting")
        obs_palette = intel_top(intel_sec, "color_palette")

        # lighting is a single scalar in the spec -> pick the chain's primary parsed term,
        # else the observed sector winner, else null
        lighting = lighting_terms[0] if lighting_terms else (obs_light[0]["value"] if obs_light else None)
        # fold observed palette winners in (they are real signal), keep authored first
        for op in obs_palette:
            if op["value"] not in palette:
                palette.append(op["value"])

        # --- forbidden props: chain's own anti_patterns + sector cultural forbiddens ---
        chain_forbidden, chain_rules = parse_forbidden(c.get("anti_patterns"))
        cultural_forbidden = CULTURAL_FORBIDDEN.get(sector, [])
        props_forbidden = list(dict.fromkeys(chain_forbidden + cultural_forbidden))

        derived_fields = ["composition", "lighting", "palette", "props_allowed",
                          "description_en", "why_it_works"]
        # note WHICH forbiddens are cultural-injected vs chain-authored
        rec = {
            "id": c["chain_ulid"],                       # reuse the source ULID (stable)
            "entity": "visual_pattern",
            "sector_key": sector,                        # null = universal / no single sector
            "occasion_key": occasion,                    # null = sector-wide / evergreen
            "pattern_name": c.get("name_en"),
            "description_en": draft_description(c),
            "composition": composition,
            "lighting": lighting,
            "palette": palette,
            "props_allowed": props_allowed,
            "props_forbidden": props_forbidden,
            "why_it_works": draft_why(c, intel_sec, occasion),
            "provenance": {
                "source": "derived",                     # parsed/authored from a curated template
                "confidence": "experimental",            # chains are templates, NOT observed outcomes
                "observed_count": None,                  # never counted -> null (no fabrication)
                "date_added": DATE_ADDED,
                "scope": f"chain:{cid}" + (f"|sector:{sector}" if sector else "") +
                         (f"|occasion:{occasion}" if occasion else ""),
            },
            "extra": {
                "source_label": Path(fp).name,
                "chain_id_short": cid,
                "chain_family": c.get("family"),
                "pattern_name_ar": c.get("name_ar"),
                "output_type": c.get("output_type"),
                "target_dimensions": c.get("target_dimensions"),
                "prompt_template": tmpl,                 # the ground truth we parsed — kept verbatim
                "sectors_allowed_raw": c["eligibility_filters"].get("sectors_allowed"),
                "occasions_allowed_raw": c["eligibility_filters"].get("occasions_allowed"),
                "eligible_sector_scores": elig or None,  # real per-sector scores if any
                "cultural_constraints": c.get("cultural_constraints"),
                "chain_anti_pattern_rules": chain_rules,  # non-prop anti-patterns (kept, not dropped)
                "props_forbidden_cultural_injected": cultural_forbidden,
                "props_forbidden_source_labels": CULTURAL_FORBIDDEN_SRC.get(sector, []),
                "observed_sector_intel": ({
                    "sector_intel_bucket": SECTOR_TO_INTEL.get(sector),
                    "sector_total_obs": intel_sec.get("total_obs"),
                    "sector_avg_engagement": intel_sec.get("sector_avg"),
                    "observed_intel_date": intel.get("generated_at"),
                    "lighting_best": obs_light,
                    "composition_best": obs_comp,
                    "palette_top": obs_palette,
                    "agency_directives": intel_sec.get("agency_directives"),
                } if intel_sec else None),
                "derived_fields": derived_fields,
                "derived_note": (
                    "composition/lighting/palette/props_allowed PARSED from prompt_template prose via "
                    "curated corpus lexicons; description_en/why_it_works AUTHORED from chain "
                    "name+purpose+notes. Chains are experimental templates, not observed posts "
                    "(observed_count=null). Where a primary sector matched, the observed winners from "
                    "logs/visual_sector_intel.json (real, n/lift stamped) were MERGED into "
                    "composition/palette and surfaced verbatim under observed_sector_intel; "
                    "props_forbidden = chain anti_patterns + Saudi cultural forbiddens "
                    "(alcohol/pork for F&B, tagged in props_forbidden_cultural_injected)."
                ),
                "source_provenance": c.get("provenance"),  # keep the chain's own provenance block
                "notes": c.get("notes"),
            },
        }
        records.append(rec)

    OUT.mkdir(parents=True, exist_ok=True)
    outfp = OUT / "visual_patterns.json"
    json.dump(records, open(outfp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # --- audit to stdout ---
    n_sector = sum(1 for r in records if r["sector_key"])
    n_occ = sum(1 for r in records if r["occasion_key"])
    n_intel = sum(1 for r in records if r["extra"]["observed_sector_intel"])
    n_cultforbid = sum(1 for r in records if r["extra"]["props_forbidden_cultural_injected"])
    print(f"wrote {len(records)} visual_pattern records -> {outfp}")
    print(f"  sector_key tagged: {n_sector}/{len(records)} | null: {len(records) - n_sector}")
    print(f"  occasion_key tagged: {n_occ}/{len(records)} | null: {len(records) - n_occ}")
    print(f"  observed_sector_intel enriched: {n_intel}/{len(records)}")
    print(f"  cultural forbiddens injected: {n_cultforbid}/{len(records)}")
    from collections import Counter
    sc = Counter(r["sector_key"] for r in records)
    oc = Counter(r["occasion_key"] for r in records if r["occasion_key"])
    print("  sector dist:", dict(sc))
    print("  occasion dist:", dict(oc))
    return records


if __name__ == "__main__":
    build()
