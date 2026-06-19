#!/usr/bin/env python3
"""
build_production_brief_engine.py  v2
OGZ Production Brief Generator — wired to all 25+ analytics logs.

Usage:
  python3 scripts/build_production_brief_engine.py \
    --sector food_and_beverage --occasion ramadan --goal brand_building
  python3 scripts/build_production_brief_engine.py --interactive

Output: full production brief to stdout + logs/production_briefs/{ts}.json
"""
import json, argparse, os, re
from pathlib import Path
from datetime import datetime

BASE        = Path(__file__).parent.parent
LOGS        = BASE / "logs"
CHAINS_BASE = BASE / "02_what_to_build"
INTEL_PATH  = BASE / "11_who_to_learn_from" / "intelligence_layer.json"

# ── Load intelligence layer (the holy book) ──────────────────────────────────
INTELLIGENCE = {}
if INTEL_PATH.exists():
    INTELLIGENCE = json.loads(INTEL_PATH.read_text())

# ── PRIMARY distilled-rules keys this engine reads from the intelligence layer ──
# Thin-Brain-v3.0 (commit f80d27e4) dropped these; until B057c is resolved (strip vs
# rewire) the engine silently read them as empty. Rule #6 + #8: every brief now CARRIES
# an honest health flag so downstream produce/judge can SEE it ran on degraded primary
# intel — no silent empties masquerading as guidance. This declares the state; it does
# NOT decide the fork (no strip, no rewire).
PRIMARY_INTEL_KEYS = [
    "sector_playbooks", "universal_rules", "anti_patterns", "occasion_rules",
    "visual_rules", "caption_rules", "format_rules",
]


def intel_health(intel: dict | None = None) -> dict:
    """Audit the PRIMARY intel keys this engine depends on.

    A key is 'missing' if absent OR falsy ({} / [] / None / "") — an empty value is a
    severed wire dressed as data. Pure + side-effect-free so callers and tests share it.
    Returns: {degraded: bool, missing_keys: [...], present_keys: [...], checked: [...]}.
    """
    if intel is None:
        intel = INTELLIGENCE
    missing, present = [], []
    for k in PRIMARY_INTEL_KEYS:
        (present if intel.get(k) else missing).append(k)
    return {
        "degraded": bool(missing),
        "missing_keys": missing,
        "present_keys": present,
        "checked": list(PRIMARY_INTEL_KEYS),
    }


class IntelDegeneracyError(RuntimeError):
    """Raised by assert_intel_complete when PRIMARY intel is degraded (Rule #8 strict mode)."""


def assert_intel_complete(intel: dict | None = None) -> dict:
    """Strict guard (Rule #8 — refuse, don't warn). Opt-in for callers that must HALT
    rather than run degraded. The live daemon stays on the soft path (it tags the brief
    degraded and continues) so we don't decide the raise-vs-degrade half of the fork."""
    h = intel_health(intel)
    if h["degraded"]:
        raise IntelDegeneracyError(
            "PRIMARY intel degraded — empty/missing keys: " + ", ".join(h["missing_keys"])
        )
    return h

# ── Load env (same approach as fill_missing_patterns.py) ──────────────────────
def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if not os.environ.get(k):
                    os.environ[k] = v
_load_env()


# ── Chain library helpers ──────────────────────────────────────────────────────
def _load_all_chains() -> list[dict]:
    """Load every chain JSON from 02_what_to_build/TF*/ folders."""
    chains = []
    for tf_dir in sorted(CHAINS_BASE.glob("TF*")):
        if not tf_dir.is_dir():
            continue
        for f in sorted(tf_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text())
                if d.get("chain_id_short"):
                    chains.append(d)
            except Exception:
                pass
    return chains


def _recommend_chains(sector: str, occasion: str, goal: str, quality_tier: str = "growth") -> list[dict]:
    """Return top 3 chains matching sector/occasion/goal eligibility, sorted by cost."""
    sk = SECTOR_KEY_MAP.get(sector, sector)
    chains = _load_all_chains()
    candidates = []
    for c in chains:
        ef = c.get("eligibility_filters") or {}
        sa = ef.get("sectors_allowed") or []
        oa = ef.get("occasions_allowed") or []
        qa = ef.get("quality_tiers_allowed") or []
        sectors_ok  = not sa or "*" in sa or sk in sa
        occ_ok      = not oa or "*" in oa or occasion in oa or "evergreen" in oa
        tier_ok     = not qa or "*" in qa or quality_tier in qa
        if sectors_ok and occ_ok and tier_ok:
            candidates.append(c)
    # Sort by cost ascending (cheapest first = most accessible)
    candidates.sort(key=lambda c: (c.get("cost_estimate_usd") or 99))
    return [
        {
            "chain_id":  c["chain_id_short"],
            "name_en":   c["name_en"],
            "name_ar":   c.get("name_ar", ""),
            "purpose":   (c.get("purpose") or "")[:120],
            "output_type": c.get("output_type", "image"),
            "cost_usd":  c.get("cost_estimate_usd"),
            "family":    c.get("family", ""),
        }
        for c in candidates[:3]
    ]


def _generate_sample_captions(brief_context: dict) -> list[str]:
    """Call Claude Haiku to generate 2 sample Arabic captions based on brief spec."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        cap = brief_context.get("caption_spec", {})
        voice = brief_context.get("voice_spec", {})
        inp = brief_context.get("input", {})
        sector  = inp.get("sector", "")
        occ     = inp.get("occasion", "evergreen").replace("_", " ")
        goal    = inp.get("content_goal", "brand_building").replace("_", " ")
        wc      = cap.get("word_count_target", "medium_11_30")
        opener  = cap.get("opener_formula", "heritage_occasion_opener")
        tone    = voice.get("tone", "warm")
        phrases = cap.get("arabic_signal_phrases", [])
        phrase_hint = f"Include signal phrases like: {', '.join(phrases[:3])}" if phrases else ""
        wc_map  = {
            "very_long_75plus": "75+ words",
            "long_31_75": "40-60 words",
            "medium_11_30": "15-25 words",
            "short_1_10": "5-10 words",
        }
        wc_label = wc_map.get(wc, "25-40 words")

        prompt = f"""Write 2 distinct Instagram captions in Arabic for a Saudi {sector} brand.
Context: occasion={occ} | goal={goal} | tone={tone} | opener style={opener}
Length: {wc_label} each
{phrase_hint}
Rules: Saudi dialect acceptable, authentic warm tone, no price mentions, no hard sell.
Return ONLY a JSON array of 2 strings: ["caption1", "caption2"]"""

        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        result = json.loads(text)
        if isinstance(result, list) and len(result) >= 1:
            return result[:2]
    except Exception:
        pass
    return []

SECTOR_ALIASES = {
    "fb":"food_and_beverage","f&b":"food_and_beverage","food":"food_and_beverage",
    "food_and_beverage":"food_and_beverage","beauty":"beauty_personal_care",
    "personal_care":"beauty_personal_care","retail":"retail_lifestyle",
    "lifestyle":"retail_lifestyle",
}
SECTOR_KEY_MAP = {
    "food_and_beverage":"f_and_b","beauty_personal_care":"beauty","retail_lifestyle":"retail",
}
GOAL_DESC = {
    "brand_building":   "Build emotional brand equity — no hard sell",
    "product_launch":   "Introduce a new product or menu item",
    "occasion_content": "Celebrate a cultural or seasonal moment",
    "offer_promotion":  "Drive immediate purchase with price or offer",
    "awareness":        "Reach new audiences, build recognition",
    "community":        "Foster loyalty with existing customers",
}

def _load(name): 
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}

def _avg_eng(eng_dict, key):
    return (eng_dict.get(key) or {}).get("avg_engagement")

def _best_key(eng_dict, min_n=3):
    """Return key with highest avg_engagement, n >= min_n."""
    candidates = [(k,v) for k,v in (eng_dict or {}).items()
                  if isinstance(v,dict) and (v.get("count") or 0) >= min_n]
    if not candidates: candidates = [(k,v) for k,v in (eng_dict or {}).items() if isinstance(v,dict)]
    if not candidates: return None
    return max(candidates, key=lambda x:(x[1].get("avg_engagement") or 0))[0]

def _top_n(eng_dict, n=3, min_count=2):
    """Return top n keys by avg_engagement."""
    candidates = [(k,v) for k,v in (eng_dict or {}).items()
                  if isinstance(v,dict) and (v.get("count") or 0) >= min_count]
    candidates.sort(key=lambda x:-(x[1].get("avg_engagement") or 0))
    return [k for k,_ in candidates[:n]]


def generate_brief(sector, occasion, goal, account=None):
    sk = SECTOR_KEY_MAP.get(sector, sector)

    # ── Load intelligence layer (PRIMARY — distilled rules) ──
    intel_playbook = INTELLIGENCE.get("sector_playbooks", {}).get(sector, {})
    intel_must_use = intel_playbook.get("must_use", [])
    intel_never_use = intel_playbook.get("never_use", [])
    intel_formulas = intel_playbook.get("winning_formulas", [])
    intel_visual_dna = intel_playbook.get("visual_dna", [])
    intel_universal = INTELLIGENCE.get("universal_rules", [])
    intel_anti = INTELLIGENCE.get("anti_patterns", [])
    intel_occasion = {r["occasion"]: r for r in INTELLIGENCE.get("occasion_rules", [])}
    intel_visual = INTELLIGENCE.get("visual_rules", [])
    intel_caption = INTELLIGENCE.get("caption_rules", [])
    intel_format = INTELLIGENCE.get("format_rules", [])
    intel_occ_verdict = intel_occasion.get(occasion, {}).get("verdict", "use_selectively")

    # ── Load all analytics logs (SECONDARY — raw detail) ──
    opp      = _load("occasion_playbook.json")
    vdt      = _load("visual_decision_tree.json")
    ct_an    = _load("content_type_analysis.json")
    tone_reg = _load("tone_register_analysis.json")
    cult_sig = _load("cultural_signal_analysis.json")
    pat_eng  = _load("pattern_engagement.json")
    light_an = _load("lighting_analysis.json")
    set_an   = _load("setting_analysis.json")
    comp_an  = _load("composition_analysis.json")
    css_an   = _load("composition_setting_synergy.json")
    dow_an   = _load("day_of_week_analysis.json")
    wg_an    = _load("wardrobe_gender_analysis.json")
    hosp_an  = _load("hospitality_intelligence.json")
    vc_an    = _load("visual_complexity_analysis.json")
    cap_lh   = _load("caption_length_hashtag_analysis.json")
    cap_sec  = _load("caption_intelligence_by_sector.json")
    ar_sec   = _load("arabic_copywriting_by_sector.json")
    cap_corp = _load("caption_intelligence.json")
    ar_corp  = _load("arabic_copywriting.json")
    hash_an  = _load("hashtag_strategy.json")
    fmt_occ  = _load("format_occasion_matrix.json")
    gap      = _load("competitive_gap.json") if account else {}
    # Phase 4 — deep intelligence layer
    npi      = _load("notable_phrases_intelligence.json")
    evw      = _load("elite_vs_weak_dna.json")
    toi      = _load("text_overlay_intelligence.json")
    sfp      = _load("sector_fingerprint.json")
    osf      = _load("occasion_sector_format_matrix.json")

    # Sector slices (preferred over corpus)
    _cap_sl  = ((cap_sec.get("per_sector_analysis") or {}).get(sk) or {})
    _ar_sl   = ((ar_sec.get("per_sector_analysis")  or {}).get(sk) or {})
    _sec_base= (cap_sec.get("sector_baselines") or {}).get(sk)

    # ── Occasion playbook entry ──
    pb_entry = next((e for e in (opp.get("playbook") or [])
                     if e.get("occasion","").lower() == occasion.lower()), None)

    # ── Visual decision tree node ──
    vdt_node = ((vdt.get("sector_occasion_decision_tree") or {}).get(sk) or {}).get(occasion)

    # ── FORMAT ──
    # Best format overall then slice by occasion
    best_ct_overall = _best_key(ct_an.get("by_content_type") or {})
    best_ct_for_occ = ((ct_an.get("best_by_occasion") or {}).get(occasion) or [{}])[0].get("content_type")
    best_ct_for_sec = ((ct_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("content_type")
    best_fmt_occ    = ((fmt_occ.get("best_format_per_occasion") or {}).get(occasion) or {}).get("format")
    recommended_format = best_ct_for_occ or best_fmt_occ or best_ct_for_sec or best_ct_overall

    # Best aspect ratio
    best_ar = _best_key(ct_an.get("by_aspect_ratio") or {})
    # Best combo
    combos = ct_an.get("combo_matrix") or []
    best_combo = combos[0] if combos else {}

    # ── SETTING ──
    best_set_overall = _best_key(set_an.get("by_setting") or {})
    best_set_for_sec = ((set_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("setting")
    best_set_for_occ = ((set_an.get("best_by_occasion") or {}).get(occasion) or [{}])[0].get("setting")
    recommended_setting = best_set_for_occ or best_set_for_sec or best_set_overall
    # Fallback to VDT/playbook
    if not recommended_setting:
        recommended_setting = ((vdt_node or {}).get("recommended_production") or {}).get("setting") \
                           or (pb_entry or {}).get("overall_recipe",{}).get("setting")

    # ── LIGHTING ──
    best_lit_overall = _best_key(light_an.get("by_lighting") or {}, min_n=5)
    best_lit_for_sec = ((light_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("lighting")
    recommended_lighting = best_lit_for_sec or best_lit_overall
    if not recommended_lighting:
        recommended_lighting = ((vdt_node or {}).get("recommended_production") or {}).get("lighting") \
                             or (pb_entry or {}).get("overall_recipe",{}).get("lighting")

    # ── COMPOSITION ──
    best_comp_overall = _best_key(comp_an.get("by_composition") or {}, min_n=10)
    best_comp_for_sec = ((comp_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("composition")
    best_comp_for_occ = ((comp_an.get("best_by_occasion") or {}).get(occasion) or [{}])[0].get("composition")
    recommended_comp  = best_comp_for_occ or best_comp_for_sec or best_comp_overall
    if not recommended_comp:
        recommended_comp = ((vdt_node or {}).get("recommended_production") or {}).get("composition") \
                        or (pb_entry or {}).get("overall_recipe",{}).get("composition")

    # ── VISUAL COMPLEXITY ──
    best_vc_for_sec = ((vc_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("complexity")
    best_vc_overall = _best_key(vc_an.get("by_complexity") or {})
    recommended_vc  = best_vc_for_sec or best_vc_overall

    # ── Best composition × setting combo ──
    css_combos = css_an.get("all_combos_ranked") or []
    best_css_for_sec = ((css_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("combo","")

    # ── HUMAN ELEMENT ──
    wg_rules = wg_an.get("agency_rules") or []
    best_gender = (wg_an.get("by_gender") or {})
    best_gender_key = _best_key(best_gender, min_n=5)

    # ── TONE + REGISTER ──
    best_tone_overall = _best_key(tone_reg.get("by_tone") or {}, min_n=3)
    best_reg_overall  = _best_key(tone_reg.get("by_register") or {}, min_n=5)
    best_tone_for_sec = ((tone_reg.get("best_tone_by_sector") or {}).get(sector) or [{}])[0].get("tone")
    best_reg_for_sec  = ((tone_reg.get("best_reg_by_sector") or {}).get(sector) or [{}])[0].get("register")
    best_tone_for_occ = ((tone_reg.get("best_tone_by_occasion") or {}).get(occasion) or [{}])[0].get("tone")
    recommended_tone  = best_tone_for_occ or best_tone_for_sec or best_tone_overall
    recommended_reg   = best_reg_for_sec  or best_reg_overall
    # VDT fallback
    if not recommended_tone: recommended_tone = ((vdt_node or {}).get("recommended_production") or {}).get("tone") or (pb_entry or {}).get("overall_recipe",{}).get("tone")
    if not recommended_reg:  recommended_reg  = ((vdt_node or {}).get("recommended_production") or {}).get("register") or (pb_entry or {}).get("overall_recipe",{}).get("register")

    # ── HERITAGE SIGNAL ──
    hvm_overall  = cult_sig.get("by_heritage_vs_modern") or {}
    best_hvm_for_sec = ((cult_sig.get("hvm_by_sector") or {}).get(sector) or [{}])[0].get("hvm")
    best_hvm_for_occ = ((cult_sig.get("hvm_by_occasion") or {}).get(occasion) or [{}])[0].get("hvm")
    heritage_uplift  = cult_sig.get("heritage_uplift_vs_modern")
    recommended_hvm  = best_hvm_for_occ or best_hvm_for_sec or _best_key(hvm_overall, min_n=20)
    if not recommended_hvm: recommended_hvm = (pb_entry or {}).get("overall_recipe",{}).get("heritage_vs_modern")

    # ── DIALECT ──
    dial_by_sec = ((cult_sig.get("dialect_by_sector") or {}).get(sector) or [{}])[0].get("dialect")
    dial_by_occ = ((cult_sig.get("dialect_by_occasion") or {}).get(occasion) or [{}])[0].get("dialect")
    recommended_dialect = dial_by_occ or dial_by_sec

    # ── CAPTION: length + hashtags + emoji + opener ──
    # Word count — prefer new caption_intelligence.json (high_engagement_rate ranked)
    _wc_new_rows = sorted(
        cap_corp.get("caption_length_table") or [],
        key=lambda r: -(r.get("high_engagement_rate") or 0)
    )
    # sector slice from old file as fallback
    _wc_sec_rows = (cap_lh.get("best_wc_by_sector") or {}).get(sector) or []
    best_wc_for_sec  = next((r["bucket"] for r in _wc_sec_rows if r.get("n",0) >= 10), None)
    best_wc_new      = (_wc_new_rows[0]["caption_length_bucket"] if _wc_new_rows else None)
    best_wc_overall  = best_wc_new or _best_key(cap_lh.get("by_word_count") or {})
    # New corpus data takes priority over old sector slice
    recommended_wc   = best_wc_new or best_wc_for_sec or best_wc_overall

    # Hashtag count — prefer hashtag_strategy.json (high_engagement_rate ranked)
    _hc_new_rows = sorted(
        hash_an.get("hashtag_count_table") or [],
        key=lambda r: -(r.get("high_engagement_rate") or 0)
    )
    _hc_sec_rows = (cap_lh.get("best_hc_by_sector") or {}).get(sector) or []
    best_hc_for_sec  = next((r["bucket"] for r in _hc_sec_rows if r.get("n",0) >= 10), None)
    best_hc_new      = (_hc_new_rows[0]["hashtag_count"] if _hc_new_rows else None)
    best_hc_overall  = best_hc_new or _best_key(cap_lh.get("by_hashtag_count") or {})
    # New corpus data takes priority over old sector slice
    recommended_hc   = best_hc_new or best_hc_for_sec or best_hc_overall

    # Emoji — prefer new emoji_presence_table
    _em_new = sorted(
        cap_corp.get("emoji_presence_table") or [],
        key=lambda r: -(r.get("high_engagement_rate") or 0)
    )
    if _em_new:
        use_emoji = _em_new[0].get("emoji_presence","") == "has_emoji"
    else:
        em_data = cap_lh.get("by_emoji") or {}
        emoji_yes = (em_data.get("True") or {}).get("avg_engagement") or 0
        emoji_no  = (em_data.get("False") or {}).get("avg_engagement") or 1
        use_emoji = emoji_yes >= emoji_no

    # Opener formula — prefer arabic_copywriting opener_formula_table
    _op_new_rows = sorted(
        ar_corp.get("opener_formula_table") or [],
        key=lambda r: -(r.get("high_engagement_rate") or 0)
    )
    best_op_new     = (_op_new_rows[0]["formula"] if _op_new_rows else None)
    best_op_overall = best_op_new or _best_key(cap_lh.get("by_opener_formula") or {})

    # Sentiment — fallback to old file
    best_sent = _best_key(cap_lh.get("by_sentiment") or {})

    # Arabic signal phrases (sector slice preferred)
    ar_phrases = [p["phrase"] for p in (
        _ar_sl.get("signal_phrases") or _ar_sl.get("signal_phrases_high_eng") or
        ar_corp.get("signal_phrases_high_eng") or []
    )[:5]]

    # ── HASHTAG STRATEGY ──
    hash_top = (hash_an.get("top_hashtags") or {})
    hash_rules= hash_an.get("agency_rules") or []

    # ── HOSPITALITY CUES ──
    hosp_group_best = _best_key(hosp_an.get("by_cue_group") or {}, min_n=5)
    hosp_sec_cues   = [(c["cue"],c["avg_engagement"]) for c in ((hosp_an.get("best_by_sector") or {}).get(sector) or [{}])[:3] if c.get("cue")]
    hosp_occ_cues   = [(c["cue"],c["avg_engagement"]) for c in ((hosp_an.get("best_by_occasion") or {}).get(occasion) or [{}])[:3] if c.get("cue")]
    hosp_target     = max(2, (pb_entry or {}).get("overall_recipe",{}).get("avg_hospitality_cues",2) or 2)

    # ── PATTERNS ──
    elite_patterns = [p["pattern"] for p in (pat_eng.get("elite_patterns") or [])[:8]]
    avoid_patterns = [p["pattern"] for p in (pat_eng.get("avoid_patterns") or [])[:5]]
    occ_patterns   = [(p["pattern"],p["avg_engagement"]) for p in ((pat_eng.get("best_by_occasion") or {}).get(occasion) or [])[:4]]
    sec_patterns   = [(p["pattern"],p["avg_engagement"]) for p in ((pat_eng.get("best_by_sector") or {}).get(sector) or [])[:4]]
    # Playbook override if has specific patterns
    pb_patterns    = ((pb_entry or {}).get("elite_recipe") or {}).get("top_patterns") or (pb_entry or {}).get("top_patterns") or []

    # ── POSTING DAY ──
    best_day_overall = (dow_an.get("ranked_days") or ["—"])[0]
    best_day_for_sec = ((dow_an.get("best_by_sector") or {}).get(sector) or {}).get("best_day")
    best_day_for_occ = ((dow_an.get("best_by_occasion") or {}).get(occasion) or {}).get("best_day")
    recommended_day  = best_day_for_occ or best_day_for_sec or best_day_overall

    # ── OCCASION × SECTOR × FORMAT (most precise format source) ──
    osf_lookup = {e["occasion"] + "__" + e["sector"]: e for e in (osf.get("best_format_table") or [])}
    osf_best   = osf_lookup.get(f"{occasion}__{sk}") or {}
    if osf_best.get("best_format"):
        recommended_format = osf_best["best_format"]  # override with 3-way precision

    # ── NOTABLE PHRASES ──
    npi_elite       = [p["phrase"] for p in (npi.get("elite_phrases") or [])[:6]]
    npi_by_sector   = [p["phrase"] for p in (npi.get("best_by_sector") or {}).get(sk, [])[:5]]
    npi_by_occasion = [p["phrase"] for p in (npi.get("best_by_occasion") or {}).get(occasion, [])[:4]]
    npi_best_cat    = (list((npi.get("by_category") or {}).items()) or [("sensory_food", {})])[0][0]
    npi_avoid       = [p["phrase"] for p in (npi.get("avoid_phrases") or [])[:3]]

    # ── ELITE vs WEAK DNA ──
    evw_do    = [(r["dimension"], r["value"], r["elite_advantage"])
                 for r in (evw.get("top_elite_advantages") or [])[:5]]
    evw_avoid = [(r["dimension"], r["value"], abs(r["elite_advantage"]))
                 for r in (evw.get("top_weak_tendencies") or [])[:4]]

    # ── TEXT OVERLAY guidance ──
    toi_lang_ranked  = [(k,v) for k,v in (toi.get("by_language") or {}).items() if (v.get("count") or 0) >= 10]
    toi_best_lang_global = toi_lang_ranked[0][0] if toi_lang_ranked else "english"
    # Sector slice: pick first language with n >= 10
    sec_langs = [e for e in ((toi.get("best_lang_by_sector") or {}).get(sk) or []) if (e.get("n") or 0) >= 10]
    toi_best_lang_sec    = sec_langs[0].get("lang") if sec_langs else None
    toi_best_lang        = toi_best_lang_sec or toi_best_lang_global
    toi_type_ranked  = list((toi.get("by_overlay_type") or {}).items())
    toi_best_type    = toi_type_ranked[0][0] if toi_type_ranked else "brand_identity"
    toi_overlay_lift = toi.get("overlay_presence_lift")

    # ── SECTOR FINGERPRINT ──
    sfp_sectors  = sfp.get("sectors") or {}
    sfp_sec_data = sfp_sectors.get(sk) or {}
    sfp_profile  = sfp_sec_data.get("profile") or {}
    sfp_lift     = sfp_sec_data.get("lift_vs_corpus")

    # ── COMPETITOR GAPS ──
    account_gaps = []
    if account and gap:
        for report in (gap.get("account_gap_reports") or []):
            if report.get("account","").lower() == account.lower():
                account_gaps = report.get("high_value_gaps",[])[:5]
                break

    # ── PREDICTION ──
    rates = []
    if pb_entry: rates.append(pb_entry.get("high_engagement_rate",0))
    if vdt_node: rates.append(vdt_node.get("occasion_high_eng_rate",0))
    pred_rate  = round(sum(rates)/len(rates),3) if rates else 0.59
    pred_grade = "A" if pred_rate>=0.75 else "B" if pred_rate>=0.60 else "C" if pred_rate>=0.45 else "D"
    pred_conf  = "high" if min(pb_entry.get("obs_count",0) if pb_entry else 0,
                               vdt_node.get("obs_count",0) if vdt_node else 0) >= 8 else "medium"

    brief = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "2.0",
        "input": {"sector":sector,"occasion":occasion,"content_goal":goal,"account":account},
        "intel_health": intel_health(INTELLIGENCE),
        "predicted_engagement": {
            "predicted_high_eng_rate": pred_rate,
            "grade": pred_grade,
            "confidence": pred_conf,
        },
        "production_spec": {
            "format":             recommended_format,
            "aspect_ratio":       best_ar,
            "best_format_combo":  f"{best_combo.get('content_type','—')} + {best_combo.get('aspect_ratio','—')} ({best_combo.get('avg_engagement',0):.0%})" if best_combo else None,
            "setting":            recommended_setting,
            "lighting":           recommended_lighting,
            "composition":        recommended_comp,
            "visual_complexity":  recommended_vc,
            "best_visual_combo":  best_css_for_sec or (css_combos[0].get("combo") if css_combos else None),
            "human_presence":     "recommended" if (best_gender_key not in ["none","—"]) else "optional",
            "gender_direction":   best_gender_key,
        },
        "voice_spec": {
            "tone":               recommended_tone,
            "register":           recommended_reg,
            "heritage_framing":   recommended_hvm,
            "heritage_uplift":    f"+{heritage_uplift:.0%} vs modern" if heritage_uplift else None,
            "dialect":            recommended_dialect,
            "language":           (pb_entry or {}).get("overall_recipe",{}).get("language"),
        },
        "caption_spec": {
            "word_count_target":  recommended_wc,
            "hashtag_count":      recommended_hc,
            "use_emoji":          use_emoji,
            "opener_formula":     best_op_overall,
            "sentiment":          best_sent,
            "arabic_signal_phrases": ar_phrases,
            "sector_baseline":    _sec_base,
        },
        "cultural_spec": {
            "hospitality_group":      hosp_group_best,
            "hospitality_cue_target": hosp_target,
            "hospitality_cues_sector": [c[0] for c in hosp_sec_cues],
            "hospitality_cues_occasion": [c[0] for c in hosp_occ_cues],
        },
        "posting_spec": {
            "best_day":    recommended_day,
            "best_day_for_occasion": best_day_for_occ,
            "best_day_for_sector":   best_day_for_sec,
        },
        "content_patterns": {
            "occasion_patterns": [p for p,_ in occ_patterns],
            "sector_patterns":   [p for p,_ in sec_patterns],
            "playbook_patterns": pb_patterns[:5],
            "elite_corpus":      elite_patterns[:5],
            "avoid":             avoid_patterns[:3],
        },
        "competitive_gaps": account_gaps or None,
        "recommended_chains": _recommend_chains(sector, occasion, goal),
        "sample_captions": [],  # filled below after brief is assembled
        "elite_production_rules": {
            "do_more":   [{"dimension": d, "value": v, "elite_advantage": round(a, 3)} for d, v, a in evw_do],
            "do_less":   [{"dimension": d, "value": v, "diff": round(a, 3)} for d, v, a in evw_avoid],
        },
        "overlay_spec": {
            "overlay_presence_lift":  toi_overlay_lift,
            "verdict":    "skip" if (toi_overlay_lift or 0) < 0 else "add",
            "best_language":   toi_best_lang,
            "best_overlay_type": toi_best_type,
            "worst_overlay_type": toi_type_ranked[-1][0] if toi_type_ranked else None,
        },
        "notable_phrases": {
            "best_category":      npi_best_cat,
            "elite_phrases":      npi_elite[:4],
            "sector_phrases":     npi_by_sector[:4],
            "occasion_phrases":   npi_by_occasion[:3],
            "avoid_phrases":      npi_avoid,
        },
        "sector_dna": {
            "sector_avg_engagement": sfp_sec_data.get("avg_engagement"),
            "lift_vs_corpus":        sfp_lift,
            "dominant_composition":  (sfp_profile.get("composition") or {}).get("dominant"),
            "dominant_setting":      (sfp_profile.get("setting") or {}).get("dominant"),
            "dominant_tone":         (sfp_profile.get("tone") or {}).get("dominant"),
            "dominant_heritage":     (sfp_profile.get("heritage_framing") or {}).get("dominant"),
        },
        "data_sources": {
            "occasion_obs":    (pb_entry or {}).get("obs_count",0),
            "sector_occ_obs":  (vdt_node or {}).get("obs_count",0),
            "total_corpus":    intel_playbook.get("obs_count", 648),
        },
        "intelligence_layer": {
            "must_use_patterns": [p["pattern"] for p in intel_must_use[:5]],
            "never_use_patterns": [p["pattern"] for p in intel_never_use[:5]],
            "winning_formulas": [{
                "formula": f"{f['content_type']} + {f['pattern']} + {f['occasion']}",
                "engagement": f.get("high_pct", 0),
            } for f in intel_formulas[:3]],
            "visual_dna": [{
                "combo": f"{v['lighting']} + {v['setting']}",
                "engagement": v.get("high_pct", 0),
            } for v in intel_visual_dna[:3]],
            "occasion_verdict": intel_occ_verdict,
            "universal_rules": [r["pattern"] for r in intel_universal[:3]],
            "format_ranking": [f"{f['content_type']} ({f['engagement']}%)" for f in intel_format],
        },
    }

    # Fill sample captions after brief is assembled (needs caption_spec context)
    brief["sample_captions"] = _generate_sample_captions(brief)

    return brief


def print_brief(brief):
    inp  = brief["input"]
    prod = brief["production_spec"]
    voice= brief["voice_spec"]
    cap  = brief["caption_spec"]
    cult = brief["cultural_spec"]
    post = brief["posting_spec"]
    pats = brief["content_patterns"]
    pred = brief["predicted_engagement"]
    elr  = brief.get("elite_production_rules") or {}
    ov   = brief.get("overlay_spec") or {}
    nph  = brief.get("notable_phrases") or {}
    dna  = brief.get("sector_dna") or {}

    W = 68
    print(f"\n{'═'*W}")
    print(f"  OGZ PRODUCTION BRIEF  v{brief.get('version','2.0')}")
    print(f"  {inp['sector'].upper()} × {inp['occasion'].replace('_',' ').upper()} × {inp['content_goal'].replace('_',' ').upper()}")
    if inp.get("account"): print(f"  Account: @{inp['account']}")
    print(f"{'═'*W}\n")

    grade = pred.get("grade","?")
    rate  = int((pred.get("predicted_high_eng_rate",0))*100)
    bl    = f"  (sector baseline={int(cap['sector_baseline']*100)}%)" if cap.get("sector_baseline") else ""
    print(f"  PREDICTED ENGAGEMENT  →  Grade {grade}  ({rate}% high eng)  [{pred.get('confidence','?')} conf]{bl}")
    print(f"  {'─'*64}\n")

    print(f"  ── PRODUCTION ────────────────────────────────────────────────")
    print(f"  Format:       {prod.get('format') or '—'}  ({prod.get('aspect_ratio') or '—'})")
    print(f"  Best combo:   {prod.get('best_format_combo') or '—'}")
    print(f"  Setting:      {prod.get('setting') or '—'}")
    print(f"  Lighting:     {prod.get('lighting') or '—'}")
    print(f"  Composition:  {prod.get('composition') or '—'}")
    print(f"  Visual depth: {prod.get('visual_complexity') or '—'}  (props + chars + overlays)")
    print(f"  Best visual:  {prod.get('best_visual_combo') or '—'}")
    print(f"  Human:        {prod.get('human_presence') or '—'}  ({prod.get('gender_direction') or '—'})")

    print(f"\n  ── VOICE ─────────────────────────────────────────────────────")
    print(f"  Tone:         {voice.get('tone') or '—'}")
    print(f"  Register:     {voice.get('register') or '—'}")
    heritage = voice.get('heritage_framing') or '—'
    uplift   = voice.get('heritage_uplift') or ''
    print(f"  Framing:      {heritage}  {uplift}")
    if voice.get("dialect"): print(f"  Dialect:      {voice['dialect']}")
    if voice.get("language"): print(f"  Language:     {voice['language']}")

    # ── bucket → human label maps ──────────────────────────────
    WC_LABEL = {
        "very_long_75plus": "75+ words (long-form)",
        "long_31_75":       "31-75 words",
        "medium_11_30":     "11-30 words",
        "short_1_10":       "1-10 words",
        "30-60 words":      "30-60 words",   # old format passthrough
    }
    HC_LABEL = {
        "1_5":    "1-5 hashtags",
        "6_15":   "6-15 hashtags",
        "16plus": "16+ hashtags (avoid)",
        "0":      "none",
    }
    print(f"\n  ── CAPTION ───────────────────────────────────────────────────")
    wc_raw = cap.get('word_count_target') or '—'
    print(f"  Length:       {WC_LABEL.get(wc_raw, wc_raw)}")
    hc_val = cap.get('hashtag_count')
    hc_display = HC_LABEL.get(hc_val, ("none" if hc_val == "0" else (hc_val or '—')))
    print(f"  Hashtags:     {hc_display}")
    print(f"  Emoji:        {'YES' if cap.get('use_emoji') else 'NO'}")
    print(f"  Opener:       {cap.get('opener_formula') or '—'}")
    print(f"  Sentiment:    {cap.get('sentiment') or '—'}")
    if cap.get("arabic_signal_phrases"):
        print(f"  Arabic cues:  {' / '.join(cap['arabic_signal_phrases'])}")

    print(f"\n  ── CULTURAL ──────────────────────────────────────────────────")
    print(f"  Hospitality:  {cult.get('hospitality_group') or '—'} group  ({cult.get('hospitality_cue_target',2)}+ cues)")
    if cult.get("hospitality_cues_occasion"):
        print(f"  Occ. cues:    {', '.join(cult['hospitality_cues_occasion'])}")
    if cult.get("hospitality_cues_sector"):
        print(f"  Sec. cues:    {', '.join(cult['hospitality_cues_sector'])}")

    print(f"\n  ── POSTING ───────────────────────────────────────────────────")
    print(f"  Best day:     {(post.get('best_day') or '—').title()}")
    if post.get("best_day_for_occasion"):
        print(f"  For occasion: {post['best_day_for_occasion'].title()}")

    print(f"\n  ── PATTERNS ──────────────────────────────────────────────────")
    all_rec = list(dict.fromkeys(
        (pats.get("playbook_patterns") or []) +
        (pats.get("occasion_patterns") or []) +
        (pats.get("sector_patterns") or []) +
        (pats.get("elite_corpus") or [])
    ))[:6]
    for p in all_rec: print(f"    ✓ {p}")
    if pats.get("avoid"):
        print(f"  AVOID:")
        for p in pats["avoid"]: print(f"    ✗ {p}")

    if brief.get("competitive_gaps"):
        print(f"\n  ── GAPS (@{inp.get('account')}) ──────────────────────────────────────")
        for g in brief["competitive_gaps"][:3]:
            print(f"    [{g['priority'].upper()}] {g['pattern']} — {int(g.get('competitor_high_eng_rate',0)*100)}%")

    # ── RECOMMENDED CHAINS ──
    chains = brief.get("recommended_chains") or []
    if chains:
        print(f"\n  ── RECOMMENDED CHAINS ────────────────────────────────────────")
        for c in chains:
            cost_str = f"  ~${c['cost_usd']:.2f}" if c.get("cost_usd") else ""
            ar = f" / {c['name_ar']}" if c.get("name_ar") else ""
            print(f"    [{c['chain_id']}] {c['name_en']}{ar}{cost_str}")
            if c.get("purpose"):
                print(f"           {c['purpose'][:80]}")

    # ── SAMPLE ARABIC CAPTIONS ──
    captions = brief.get("sample_captions") or []
    if captions:
        print(f"\n  ── SAMPLE ARABIC CAPTIONS ────────────────────────────────────")
        for i, cap in enumerate(captions, 1):
            print(f"  [{i}] {cap}")

    # ── ELITE PRODUCTION RULES ──
    if elr.get("do_more"):
        print(f"\n  ── ELITE RULES ───────────────────────────────────────────────")
        for r in (elr.get("do_more") or [])[:4]:
            pct = int((r.get("elite_advantage") or 0) * 100)
            print(f"    ✓ DO: {r['dimension']} → {r['value']}  (+{pct}pp vs weak)")
        for r in (elr.get("do_less") or [])[:3]:
            pct = int((r.get("diff") or 0) * 100)
            print(f"    ✗ AVOID: {r['dimension']} → {r['value']}  (-{pct}pp vs elite)")

    # ── OVERLAY SPEC ──
    if ov:
        lift_str = f"lift {ov.get('overlay_presence_lift',0):+.2f}" if ov.get("overlay_presence_lift") is not None else ""
        verdict  = ov.get("verdict","?").upper()
        print(f"\n  ── OVERLAY ───────────────────────────────────────────────────")
        print(f"  Overlay verdict: {verdict}  {lift_str}")
        print(f"  Best language:   {ov.get('best_language') or '—'}  |  Best type: {ov.get('best_overlay_type') or '—'}")
        if ov.get("worst_overlay_type"):
            print(f"  Avoid type:      {ov.get('worst_overlay_type')}")

    # ── NOTABLE PHRASES ──
    phrases = (nph.get("occasion_phrases") or nph.get("sector_phrases") or nph.get("elite_phrases") or [])[:4]
    avoid_ph = nph.get("avoid_phrases") or []
    if phrases or nph.get("best_category"):
        print(f"\n  ── NOTABLE PHRASES ───────────────────────────────────────────")
        if nph.get("best_category"):
            print(f"  Best category:   {nph['best_category']}")
        if phrases:
            print(f"  Use:  {' / '.join(phrases)}")
        if avoid_ph:
            print(f"  Avoid: {' / '.join(avoid_ph)}")

    # ── SECTOR DNA ──
    if dna.get("sector_avg_engagement") is not None:
        lift = dna.get("lift_vs_corpus") or 0
        lift_str = f"+{lift:.2f}" if lift >= 0 else f"{lift:.2f}"
        print(f"\n  ── SECTOR DNA ────────────────────────────────────────────────")
        print(f"  Sector avg: {int((dna['sector_avg_engagement'])*100)}%  (lift {lift_str} vs corpus)")
        dom = []
        if dna.get("dominant_composition"): dom.append(f"comp: {dna['dominant_composition']}")
        if dna.get("dominant_setting"):     dom.append(f"setting: {dna['dominant_setting']}")
        if dna.get("dominant_tone"):        dom.append(f"tone: {dna['dominant_tone']}")
        if dna.get("dominant_heritage"):    dom.append(f"hvm: {dna['dominant_heritage']}")
        if dom: print(f"  DNA:  {' | '.join(dom)}")

    print(f"\n{'═'*W}\n")


def main():
    parser = argparse.ArgumentParser(description="OGZ Production Brief Generator v2")
    parser.add_argument("--sector",      type=str)
    parser.add_argument("--occasion",    type=str)
    parser.add_argument("--goal",        type=str, default="brand_building")
    parser.add_argument("--account",     type=str, default=None)
    parser.add_argument("--save",        action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or not args.sector:
        print("\nOGZ Brief Generator v2 — Interactive")
        print("─"*40)
        print("Sectors: food_and_beverage | beauty_personal_care | retail_lifestyle")
        sector  = SECTOR_ALIASES.get(input("Sector: ").strip().lower(), input("Sector: ").strip().lower())
        print("Occasions: ramadan | national_day | eid_al_fitr | founding_day | evergreen ...")
        occasion = input("Occasion: ").strip().lower().replace(" ","_")
        print("Goals: brand_building | product_launch | offer_promotion | community | awareness")
        goal    = input("Goal [brand_building]: ").strip().lower() or "brand_building"
        account = input("Account (optional): ").strip().lower() or None
    else:
        sector  = SECTOR_ALIASES.get(args.sector.lower(), args.sector.lower())
        occasion= args.occasion.lower().replace(" ","_")
        goal    = args.goal.lower()
        account = args.account

    brief = generate_brief(sector, occasion, goal, account)
    print_brief(brief)

    if args.save or (args.interactive and input("Save? [y/N]: ").lower() == "y"):
        d = LOGS / "production_briefs"
        d.mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fn = f"brief_{sector}_{occasion}_{goal}_{ts}.json"
        (d/fn).write_text(json.dumps(brief, ensure_ascii=False, indent=2))
        print(f"Saved: logs/production_briefs/{fn}")

if __name__ == "__main__":
    main()
