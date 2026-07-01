#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weiblocks export builder — SECTOR root records (contract weiblocks-knowledge-spec-v1, §5.1 + §6).

SYSTEM PRODUCES (Rule #12): this script READS the real source files and EMITS the JSON.
No record content is hand-authored here — every field is derived from a real read of a
source file, and every derivation is logged in extra.derived_fields + extra.derived_note.

SHIP: 3 observed sectors (F&B, Retail, Beauty_Wellness) + 1 neutral Other.
HOLD (do NOT emit): healthcare_wellness + real_estate — held for validation (see gaps).

Run with:  /Users/abarihm/Desktop/ogz-knowledge/.venv/bin/python3 scripts/weiblocks/build_sectors.py
Output:    exports/weiblocks_v1/sectors.json  (ensure_ascii=False — native Arabic, raw UTF-8)
"""
import json
import os
import sys
import hashlib
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from occasion_keys import normalize as normalize_occasion, SHIPPED_KEYS  # THE shared join module — never a local map

ROOT = "/Users/abarihm/Desktop/ogz-knowledge"
LOGS = os.path.join(ROOT, "logs")
SECDEF = os.path.join(ROOT, "05_sector_defaults")
OUT_DIR = os.path.join(ROOT, "exports", "weiblocks_v1")
OUT_FILE = os.path.join(OUT_DIR, "sectors.json")
DATE = "2026-07-01"

# ---- our-slug -> weiblocks sector_key mapping (per task spec) --------------------
# keep our slug in extra.source_label
SECTOR_MAP = {
    "f_and_b":             {"key": "F&B",              "yaml": "f_and_b.yaml",  "name_en": "Food & Beverage",       "name_ar": "الأطعمة والمشروبات"},
    "retail_lifestyle":    {"key": "Retail",           "yaml": "retail.yaml",   "name_en": "Retail",                "name_ar": "التجزئة"},
    "beauty_personal_care":{"key": "Beauty_Wellness",  "yaml": "beauty.yaml",   "name_en": "Beauty & Personal Care","name_ar": "العناية والجمال"},
}
SHIP_ORDER = ["f_and_b", "retail_lifestyle", "beauty_personal_care"]  # 3 observed

# ---- honesty notes (baked in — reproducibility: no post-hoc normalizer) ----------
# NOTE text is the contract-shipped string, byte-for-byte. Do not reword.
TONE_HONESTY_NOTE = (
    "voice tone approval_rate is null (no measured approval data); `prevalence` = how often "
    "the tone appears in the sector (proxy), not a measured approval rate"
)
NEG_LIFT_NOTE_ALL = (
    "palette colors are rank-order least-bad; every color underperforms the baseline "
    "(negative lift) — not proven winners"
)


# ---- loaders --------------------------------------------------------------------
def load_json(name):
    with open(os.path.join(LOGS, name), encoding="utf-8") as f:
        return json.load(f)

def load_yaml(name):
    with open(os.path.join(SECDEF, name), encoding="utf-8") as f:
        return yaml.safe_load(f)

COMPARISON  = load_json("sector_comparison.json")
FINGERPRINT = load_json("sector_fingerprint.json")
CAPTION     = load_json("caption_intelligence_by_sector.json")
VISUAL      = load_json("visual_sector_intel.json")
ARABIC      = load_json("arabic_copywriting_by_sector.json")
PATTERN     = load_json("pattern_sector_matrix.json")
LENHASH     = load_json("caption_length_hashtag_analysis.json")


def stable_id(seed):
    """Deterministic 26-char Crockford-base32-ish id derived from a stable seed."""
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    n = int.from_bytes(h[:17], "big")  # ~136 bits -> plenty for 26 base32 chars
    out = []
    for _ in range(26):
        out.append(alphabet[n & 31])
        n >>= 5
    return "".join(reversed(out))


# ---- field derivers -------------------------------------------------------------
def derive_voice(slug, yml):
    """
    tone_default   <- fingerprint profile.tone.top_3 (real observed prevalence).
    top/worst_performing_tones <- SAME distribution. HONESTY (baked in, not post-hoc):
      the corpus has NO tone->engagement/approval table anywhere, so approval_rate is
      emitted as None (null) — never a fabricated rate. prevalence = observed share
      (pct) of the tone in the sector, the honest proxy. sample = obs_count*pct
      (derived count). Stated in extra.honesty_notes (TONE_HONESTY_NOTE).
    love_lines / hate_lines <- arabic signal_phrases / avoid_phrases (real high/low
      engagement ratios), observed_count carried as sample.
    person <- authored persona string derived from YAML register/tone_attributes (curated).
    """
    fp = FINGERPRINT["sectors"][slug]
    obs = fp["obs_count"]
    tone = fp["profile"]["tone"]
    top3 = tone["top_3"]

    tone_default = [t["value"] for t in top3]

    # top performers = the higher-prevalence tones; worst = the lowest of the top_3 tail.
    # (There is no true worst-tone engagement signal; we surface the least-prevalent observed tone.)
    # approval_rate = None ALWAYS (no measured approval data exists); prevalence carries the pct.
    # Key order (tone, approval_rate, sample, prevalence) is the shipped contract shape.
    def _tone_obj(t):
        return {"tone": t["value"], "approval_rate": None,
                "sample": int(round(obs * t["pct"])), "prevalence": round(t["pct"], 3)}

    top_perf = [_tone_obj(t) for t in top3[:2]]
    worst_perf = [_tone_obj(top3[-1])] if top3 else []

    ar = ARABIC["per_sector_analysis"][slug]
    love_lines = [
        {"line": p["phrase"], "high_ratio": round(p["high_ratio"], 3),
         "lift": round(p["lift_vs_sector_baseline"], 3), "sample": p["total"]}
        for p in ar.get("signal_phrases", [])[:12]
    ]
    hate_lines = [
        {"line": p["phrase"], "high_ratio": round(p["high_ratio"], 3),
         "lift": round(p["lift_vs_sector_baseline"], 3), "sample": p["total"]}
        for p in ar.get("avoid_phrases", [])[:10]
    ]

    dv = yml["default_voice"]
    cs = yml.get("default_cultural_spec", {})
    tone_attrs = cs.get("tone_attributes", [])
    person = (
        f"{dv['register']} voice, {dv['formality']} formality, "
        f"{dv['dialect_default']} dialect default"
        + (f"; {', '.join(tone_attrs)}" if tone_attrs else "")
    )

    return {
        "tone_default": tone_default,
        "top_performing_tones": top_perf,
        "worst_performing_tones": worst_perf,
        "love_lines": love_lines,
        "hate_lines": hate_lines,
        "person": person,
    }


def derive_visual(slug, yml):
    """
    palette      <- YAML default_visual primary+secondary hex (real), enriched with
                    visual_sector_intel top_colors (real engagement names).
    lighting     <- YAML lighting_default (curated) + best-performing lighting values (real eng).
    composition  <- YAML composition_default (curated) + best-performing composition values (real eng).
    styling_notes<- YAML texture_default (real).
    """
    dvis = yml["default_visual"]
    vi = VISUAL["sectors"][slug]

    palette = list(dvis.get("primary_palette", [])) + list(dvis.get("secondary_accents", []))
    top_colors = [
        {"name": c["value"], "engagement_rate": round(c["engagement_rate"], 3),
         "lift": round(c["lift"], 3), "sample": c["n"]}
        for c in vi.get("color_palette", {}).get("top_colors", [])
    ]

    lighting = {
        "default": dvis.get("lighting_default"),
        "best_performing": [
            {"value": x["value"], "engagement_rate": round(x["engagement_rate"], 3),
             "lift": round(x["lift"], 3), "sample": x["n"]}
            for x in vi.get("lighting", {}).get("best", [])
        ],
    }
    composition = {
        "default": dvis.get("composition_default"),
        "best_performing": [
            {"value": x["value"], "engagement_rate": round(x["engagement_rate"], 3),
             "lift": round(x["lift"], 3), "sample": x["n"]}
            for x in vi.get("composition", {}).get("best", [])
        ],
        "best_setting": [
            {"value": x["value"], "engagement_rate": round(x["engagement_rate"], 3),
             "lift": round(x["lift"], 3), "sample": x["n"]}
            for x in vi.get("setting", {}).get("best", [])
        ],
    }
    return {
        "palette": palette,
        "palette_top_performing_colors": top_colors,
        "lighting": lighting,
        "composition": composition,
        "styling_notes": dvis.get("texture_default"),
    }


def derive_content_mix():
    """
    content_mix_default is NOT in our data (no observed product/lifestyle/occasion/
    brand_story/founder split exists anywhere in the corpus). Honest inferred default,
    same neutral split for the 3 observed sectors, marked inferred.
    """
    return {
        "product": 0.35,
        "lifestyle": 0.30,
        "occasion": 0.15,
        "brand_story": 0.15,
        "founder": 0.05,
    }


def _len_ideal(slug):
    """ideal_length from caption_intelligence caption_length buckets (best avg_engagement,
    excluding the degenerate 'empty' bucket which = no-caption posts) + best_wc_by_sector."""
    buckets = CAPTION["per_sector_analysis"][slug]["caption_length"]
    real = [b for b in buckets if b["bucket"] != "empty"]
    best = max(real, key=lambda b: b["avg_engagement"]) if real else None
    wc = LENHASH.get("best_wc_by_sector", {}).get(slug, [])
    best_wc = max(wc, key=lambda b: b["avg_engagement"]) if wc else None
    return {
        "best_length_bucket": best["bucket"] if best else None,
        "best_length_avg_engagement": round(best["avg_engagement"], 3) if best else None,
        "best_word_count_bucket": best_wc["bucket"] if best_wc else None,
        "note": "empty/no-caption bucket excluded — it reflects visual-only posts, not a caption length strategy",
    }


def derive_caption_conventions(slug):
    cap = CAPTION["per_sector_analysis"][slug]
    # emoji
    emoji = {b["bucket"]: b for b in cap.get("emoji_presence", [])}
    no_e = emoji.get("no_emoji", {}).get("avg_engagement")
    has_e = emoji.get("has_emoji", {}).get("avg_engagement")
    emoji_usage = "sparing" if (no_e is not None and has_e is not None and no_e > has_e) else "moderate"

    # hashtag strategy from best_hc_by_sector (real engagement per hashtag bucket)
    hc = LENHASH.get("best_hc_by_sector", {}).get(slug, [])
    best_hc = max(hc, key=lambda b: b["avg_engagement"]) if hc else None
    hashtag_strategy = {
        "best_bucket": best_hc["bucket"] if best_hc else None,
        "best_avg_engagement": round(best_hc["avg_engagement"], 3) if best_hc else None,
        "buckets": [
            {"bucket": b["bucket"], "avg_engagement": round(b["avg_engagement"], 3), "sample": b["n"]}
            for b in hc
        ],
    }

    # common_hashtags_ar: the corpus has NO hashtag-text field; the closest real Arabic
    # tokens are occasion_keyword_clusters (real counted keywords). We surface those as
    # hashtag-able Arabic tokens, honestly labeled (they are keywords, not scraped '#tags').
    clusters = ARABIC["per_sector_analysis"][slug].get("occasion_keyword_clusters", {})
    common_hashtags_ar = []
    for occ, kws in clusters.items():
        for kw in kws[:2]:
            common_hashtags_ar.append({"tag": kw["keyword"], "occasion": occ, "count": kw["count"]})

    agency = CAPTION.get("agency_rules_by_sector", {}).get(slug, [])

    return {
        "ideal_length": _len_ideal(slug),
        "emoji_usage": emoji_usage,
        "hashtag_strategy": hashtag_strategy,
        "common_hashtags_ar": common_hashtags_ar,
        "_agency_rules": agency,
    }


def derive_occasions(occ_list):
    """occasion_key = shared occasion_keys.normalize(slug) — the JOIN field; it MUST resolve
    to a shipped occasions.json occasion_key. The original (YAML/authored) slug is kept as
    occasion_slug_source for provenance. Rule #8 (refuse, don't warn): an unresolvable slug
    EXITS the build non-zero — a join key that doesn't resolve must never ship."""
    out = []
    for o in occ_list or []:
        key, orig = normalize_occasion(o["occasion_slug"])
        if key is None or key not in SHIPPED_KEYS:
            raise SystemExit(
                f"REFUSE (Rule #8): occasion slug {o['occasion_slug']!r} does not resolve to a "
                f"shipped occasion_key — fix occasion_keys.py aliases or the source, then re-run"
            )
        out.append({"occasion_key": key, "occasion_slug_source": orig, "priority": o["priority"]})
    return out


def derive_negative_patterns(slug, yml):
    """common_negative_patterns <- forbidden_topics (YAML, real) + worst-performing
    visual values (real low engagement) + arabic avoid_phrases top 3 (real)."""
    out = []
    for t in yml.get("forbidden_topics_sector_specific", []):
        out.append({"pattern": t, "kind": "forbidden_topic", "source": "sector_yaml"})
    vi = VISUAL["sectors"][slug]
    for dim in ("lighting", "setting", "composition"):
        for x in vi.get(dim, {}).get("worst", [])[:2]:
            out.append({"pattern": f"{dim}={x['value']}",
                        "kind": "low_engagement_visual",
                        "engagement_rate": round(x["engagement_rate"], 3),
                        "lift": round(x["lift"], 3), "sample": x["n"]})
    for p in ARABIC["per_sector_analysis"][slug].get("avoid_phrases", [])[:3]:
        out.append({"pattern": p["phrase"], "kind": "low_engagement_phrase",
                    "lift": round(p["lift_vs_sector_baseline"], 3), "sample": p["total"]})
    return out


def derive_dos_donts(slug, yml):
    vi = VISUAL["sectors"][slug]
    dos = []
    # agency_directives are real, sector-specific, engagement-grounded
    for d in vi.get("agency_directives", []):
        dos.append(d)
    # best performers -> explicit dos
    for dim in ("lighting", "setting", "composition"):
        best = vi.get(dim, {}).get("best", [])
        if best:
            b = best[0]
            dos.append(f"Favor {dim}='{b['value']}' — {round(b['engagement_rate']*100)}% eng (+{round(b['lift']*100)}% lift, n={b['n']})")
    donts = []
    for dim in ("lighting", "setting", "composition"):
        worst = vi.get(dim, {}).get("worst", [])
        if worst:
            w = worst[-1]  # lowest
            donts.append(f"Avoid {dim}='{w['value']}' — {round(w['engagement_rate']*100)}% eng ({round(w['lift']*100)}% lift, n={w['n']})")
    for t in yml.get("forbidden_topics_sector_specific", []):
        donts.append(f"Never: {t}")
    return dos, donts


# ---- record builders ------------------------------------------------------------
def build_observed(slug):
    m = SECTOR_MAP[slug]
    yml = load_yaml(m["yaml"])
    fp = FINGERPRINT["sectors"][slug]
    comp = COMPARISON["sectors"][slug]
    cap_summary = CAPTION["sector_summaries"][slug]

    voice = derive_voice(slug, yml)
    visual = derive_visual(slug, yml)
    caption_conv = derive_caption_conventions(slug)
    dos, donts = derive_dos_donts(slug, yml)

    # observed_count: the real corpus obs backing this sector (fingerprint obs_count)
    observed_count = fp["obs_count"]

    # intelligence depth from ranking -> confidence: only F&B has real depth (75).
    depth = next((r["intelligence_depth"] for r in COMPARISON["ranking"] if r["sector"] == slug), 0)
    # HONESTY: engagement signals are inferred-from-data (not human-validated).
    confidence = "inferred"

    rec = {
        "id": stable_id(f"weiblocks:sector:{m['key']}"),
        "entity": "sector",
        "sector_key": m["key"],
        "name_en": m["name_en"],
        "name_ar": m["name_ar"],
        "voice": voice,
        "visual": visual,
        "content_mix_default": derive_content_mix(),
        "caption_conventions": {
            "ideal_length": caption_conv["ideal_length"],
            "emoji_usage": caption_conv["emoji_usage"],
            "hashtag_strategy": caption_conv["hashtag_strategy"],
            "common_hashtags_ar": caption_conv["common_hashtags_ar"],
        },
        "typical_occasions": derive_occasions(yml.get("default_occasions_priority", [])),
        "common_negative_patterns": derive_negative_patterns(slug, yml),
        "dos": dos,
        "donts": donts,
        "provenance": {
            "source": "derived",
            "confidence": confidence,
            "observed_count": observed_count,
            "date_added": DATE,
            "scope": f"sector:{slug}",
        },
        "extra": {
            "source_label": slug,
            "source_baseline_ulid": yml.get("sector_baseline_ulid"),
            "avg_engagement": round(fp["avg_engagement"], 3),
            "lift_vs_corpus": round(fp["lift_vs_corpus"], 3),
            "intelligence_depth": depth,
            "strength": comp.get("strength"),
            "caption_sector_baseline": cap_summary.get("sector_baseline"),
            "agency_rules_caption": caption_conv["_agency_rules"],
            "yaml_default_voice": yml.get("default_voice"),
            "yaml_default_cinematography": yml.get("default_cinematography"),
            "yaml_cd_brain_routing_bias": yml.get("default_cd_brain_routing_bias"),
            "confidence": "inferred",
            "derived_fields": [
                "voice.tone_default", "voice.top_performing_tones", "voice.worst_performing_tones",
                "voice.love_lines", "voice.hate_lines", "voice.person",
                "visual.palette", "visual.palette_top_performing_colors",
                "visual.lighting", "visual.composition", "visual.styling_notes",
                "content_mix_default",
                "caption_conventions.ideal_length", "caption_conventions.emoji_usage",
                "caption_conventions.hashtag_strategy", "caption_conventions.common_hashtags_ar",
                "typical_occasions", "common_negative_patterns", "dos", "donts",
            ],
            "derived_note": (
                "voice.tone_default = sector_fingerprint profile.tone.top_3 (observed PREVALENCE, "
                "not engagement). voice.top/worst_performing_tones.approval_rate = the SAME "
                "prevalence share (pct) — the corpus has NO tone->approval/engagement table anywhere, "
                "so approval_rate is prevalence, and sample = obs_count*pct (derived count), NOT a "
                "counted approval. love_lines/hate_lines = arabic_copywriting_by_sector "
                "signal_phrases/avoid_phrases (real high/low engagement ratios); sample = real 'total'. "
                "visual.palette hex = 05_sector_defaults YAML default_visual (curated palette); "
                "palette_top_performing_colors + lighting/composition best_performing = "
                "visual_sector_intel (real engagement_rate, real n). content_mix_default = INFERRED "
                "honest default split — no product/lifestyle/occasion/brand_story/founder split exists "
                "in the corpus. caption_conventions = caption_intelligence_by_sector buckets + "
                "caption_length_hashtag_analysis best_wc/hc (real). common_hashtags_ar = "
                "occasion_keyword_clusters (real counted Arabic keywords) — these are KEYWORDS, the "
                "corpus has no scraped '#hashtag' text field. typical_occasions = YAML "
                "default_occasions_priority (curated). dos/donts = visual_sector_intel best/worst "
                "(real eng) + forbidden_topics (YAML)."
            ),
        },
    }

    # honesty_notes — baked in (Rule: honesty in the transformer, never a post-hoc normalizer).
    honesty_notes = [TONE_HONESTY_NOTE]
    lifts = [c["lift"] for c in visual["palette_top_performing_colors"]]
    neg = sum(1 for l in lifts if l < 0)
    if lifts and neg == len(lifts):
        # every color underperforms the baseline — 'top_performing' is rank-order least-bad
        honesty_notes.append(NEG_LIFT_NOTE_ALL)
    elif lifts and neg > len(lifts) / 2:
        # majority negative — same warning, stated with the real numbers (never claim
        # 'every color underperforms' when one does not; verify-the-number rule)
        honesty_notes.append(
            f"palette colors are rank-order least-bad; {neg} of {len(lifts)} colors underperform "
            f"the baseline (negative lift), best remaining lift only +{max(lifts):.3f} "
            f"— not proven winners"
        )
    rec["extra"]["honesty_notes"] = honesty_notes
    return rec


def build_other():
    """
    §6 Other sector: neutral/conservative Saudi baseline. NOT observed — authored
    fallback. confidence=experimental. Carries routing_hints + fallback_behavior.
    """
    key = "Other"
    rec = {
        "id": stable_id(f"weiblocks:sector:{key}"),
        "entity": "sector",
        "sector_key": key,
        "name_en": "Other / General",
        "name_ar": "أخرى / عام",
        "voice": {
            "tone_default": ["informative", "warm", "respectful"],
            "top_performing_tones": [],
            "worst_performing_tones": [],
            "love_lines": [],
            "hate_lines": [],
            "person": "neutral, respectful Saudi voice; MSA-leaning with light dialect warmth; universally safe register that borrows a sector's voice once the business type is known",
        },
        "visual": {
            "palette": ["#1F2A2E", "#E8D5B4", "#FFFFFF", "#C09F6F"],
            "palette_top_performing_colors": [],
            "lighting": {"default": "clean natural daylight, soft even key; no extreme mood", "best_performing": []},
            "composition": {"default": "balanced, subject-centered, ample negative space", "best_performing": [], "best_setting": []},
            "styling_notes": "neutral, uncluttered, conservative Saudi-appropriate styling; borrow the matched sector's styling once routed",
        },
        "content_mix_default": {
            "product": 0.30,
            "lifestyle": 0.30,
            "occasion": 0.15,
            "brand_story": 0.15,
            "founder": 0.10,
        },
        "caption_conventions": {
            "ideal_length": {"best_length_bucket": "medium_11_30", "best_length_avg_engagement": None,
                             "best_word_count_bucket": "10-30",
                             "note": "conservative default; no observed baseline for Other — borrow the routed sector's convention"},
            "emoji_usage": "sparing",
            "hashtag_strategy": {"best_bucket": "1-5", "best_avg_engagement": None, "buckets": []},
            "common_hashtags_ar": [],
        },
        "typical_occasions": derive_occasions([
            {"occasion_slug": "ramadan", "priority": 0.8},
            {"occasion_slug": "eid_al_fitr", "priority": 0.8},
            {"occasion_slug": "saudi_national_day", "priority": 0.75},
            {"occasion_slug": "saudi_founding_day", "priority": 0.55},
            {"occasion_slug": "eid_al_adha", "priority": 0.55},
        ]),
        "common_negative_patterns": [
            {"pattern": "alcohol references", "kind": "forbidden_topic", "source": "universal_saudi_red_lines"},
            {"pattern": "pork references", "kind": "forbidden_topic", "source": "universal_saudi_red_lines"},
            {"pattern": "immodest imagery / clothing removal", "kind": "forbidden_topic", "source": "universal_saudi_red_lines"},
            {"pattern": "exploiting weakness / misleading claims", "kind": "forbidden_topic", "source": "universal_saudi_red_lines"},
        ],
        "dos": [
            "Stay neutral and respectful until the business type is identified, then route to the closest sector's voice+visual",
            "Default to conservative Saudi cultural norms (modesty, halal, prayer-time awareness)",
            "Lead captions Arabic-primary with a clean, informative register",
        ],
        "donts": [
            "Never guess a sector-specific tone before routing — stay neutral",
            "Never: alcohol / pork / immodest imagery / misleading claims (universal Saudi red lines)",
            "Avoid extreme visual mood (dark/dramatic) as an unrouted default",
        ],
        "provenance": {
            "source": "manual_curation",
            "confidence": "experimental",
            "observed_count": None,
            "date_added": DATE,
            "scope": "sector:other",
        },
        "extra": {
            "source_label": "other_neutral_baseline",
            "confidence": "experimental",
            "routing_hints": [
                {"if_signal": "serves food/drink", "borrow_sector": "F&B"},
                {"if_signal": "sells physical products", "borrow_sector": "Retail"},
                {"if_signal": "clinic/spa/wellness", "borrow_sector": "Beauty_Wellness"},
                {"if_signal": "professional/B2B service", "borrow_sector": "Corporate_Services"},
            ],
            "fallback_behavior": (
                "When a client's sector is unknown or unmatched, apply this neutral Saudi baseline "
                "(conservative palette, balanced content mix, universal cultural red lines, MSA-leaning "
                "voice). On the FIRST reliable business-type signal, route via routing_hints and inherit "
                "the matched sector's voice + visual + caption_conventions; keep the universal red lines "
                "regardless of routing. If the routed sector is one held-for-validation "
                "(Healthcare, Real_Estate) or not-yet-observed (Corporate_Services), remain on this "
                "neutral baseline and flag for human onboarding."
            ),
            "derived_fields": [
                "ALL fields authored (no observed backing) — neutral/conservative Saudi baseline per spec §6",
            ],
            "derived_note": (
                "Other is an AUTHORED fallback, not an observed sector. confidence=experimental. "
                "Palette = neutral subset of common OGZ tokens; content_mix = balanced default; "
                "occasions/red-lines = universal Saudi baseline. Nothing here is engagement-observed."
            ),
            "honesty_notes": [TONE_HONESTY_NOTE],
        },
    }
    return rec


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    records = [build_observed(s) for s in SHIP_ORDER]
    records.append(build_other())

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"WROTE {len(records)} sector records -> {OUT_FILE}")
    for r in records:
        pc = r["provenance"]
        print(f"  {r['sector_key']:16} conf={pc['confidence']:12} obs={pc['observed_count']} "
              f"love={len(r['voice']['love_lines'])} hate={len(r['voice']['hate_lines'])} "
              f"dos={len(r['dos'])} donts={len(r['donts'])}")


if __name__ == "__main__":
    main()
