#!/usr/bin/env python3
"""
creative_pipeline.py — End-to-end: Intelligence → Concept → Prompt → Storyboard

Takes a brand + sector + occasion and produces:
  1. Intelligence context (what works)
  2. Creative concept (the idea)
  3. Ready-to-use fal.ai prompts (the execution)
  4. Storyboard (the sequence)
  5. Arabic captions (the voice)

Usage:
  python3 scripts/creative_pipeline.py --brand AlBaik --sector f_and_b --occasion ramadan
  python3 scripts/creative_pipeline.py --brand ROSHN --sector real_estate --occasion national_day --product "luxury villa"
"""
import json, argparse, glob, os, sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
CHAINS = BASE / "02_what_to_build"
INTEL = BASE / "11_who_to_learn_from" / "intelligence_layer.json"

def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if not os.environ.get(k):
                    os.environ[k] = v
_load_env()


# --- Thin-Brain v4.2 key map (B057c fork ruled A=REWIRE, 2026-06-22) ---
# The v3.0 slim (commit f80d27e4) dropped sector_playbooks / occasion_rules /
# universal_rules / emotion_rules / campaign_arcs. This reader used to .get()
# those dead keys → silently empty → generic fallback (Rule #6 severed wire,
# flagged by intel_consumer_health). It now sources the SAME fields consumers
# expect from the LIVE keys: sector_facts, occasion_calendar, visual_intelligence,
# and logs/pattern_engagement_evidence.json.
PATTERN_EVIDENCE = BASE / "logs" / "pattern_engagement_evidence.json"
_SECTOR_ALIAS = {
    "food": "f_and_b", "f&b": "f_and_b", "fnb": "f_and_b", "f_and_b": "f_and_b",
    "restaurant": "f_and_b", "cafe": "f_and_b", "beverage": "f_and_b",
    "retail": "retail_lifestyle", "retail_lifestyle": "retail_lifestyle",
    "fashion": "fashion", "beauty": "beauty_personal_care",
    "beauty_personal_care": "beauty_personal_care",
    "fitness": "healthcare_wellness", "wellness": "healthcare_wellness",
    "healthcare": "healthcare_wellness", "healthcare_wellness": "healthcare_wellness",
    "real_estate": "real_estate", "realestate": "real_estate",
}


def _norm_sector(sector):
    s = (sector or "").lower().strip()
    return _SECTOR_ALIAS.get(s, s)


def load_intelligence(sector, occasion):
    """Load intelligence for this sector + occasion (Thin-Brain v4.2 live keys)."""
    intel = json.loads(INTEL.read_text())
    sec = _norm_sector(sector)

    # must_use ← real per-sector engagement patterns (high-engagement share %).
    # Require MIN_PATTERN_N observations so n=1 flukes at 100% don't outrank the
    # true signal (Rule #9 — a high_share_pct on a tiny sample is noise, not fact).
    MIN_PATTERN_N = 30
    must_use = []
    if PATTERN_EVIDENCE.exists():
        pe = json.loads(PATTERN_EVIDENCE.read_text())
        rows = []
        for name, rec in pe.items():
            if name.startswith("_") or not isinstance(rec, dict):
                continue
            bys = (rec.get("by_sector") or {}).get(sec)
            if bys and bys.get("high_share_pct") and (bys.get("n") or 0) >= MIN_PATTERN_N:
                rows.append({"pattern": name, "engagement": bys["high_share_pct"], "n": bys["n"]})
        rows.sort(key=lambda r: r["engagement"], reverse=True)
        must_use = rows[:5]

    # visual_dna ← visual_intelligence winning-visual entries (real GPT-4o vision)
    vi = intel.get("visual_intelligence", {})
    top_share = must_use[0]["engagement"] if must_use else 0
    visual_dna = []
    for _k, v in vi.items():
        if isinstance(v, dict) and (v.get("lighting") or v.get("setting")):
            visual_dna.append({
                "lighting": v.get("lighting", "natural"),
                "setting": v.get("setting", "studio"),
                "high_pct": top_share,
            })
    visual_dna = visual_dna[:3]

    # never_use ← cultural guardrails (forbidden props / behaviors / visuals)
    cg = intel.get("cultural_guardrails", {})
    never_use = []
    for fk in ("forbidden_props", "forbidden_behaviors", "forbidden_visuals", "forbidden_gestures"):
        never_use.extend(cg.get(fk, []) or [])
    never_use = never_use[:5]

    # obs_count ← real sector observation count
    obs_count = (intel.get("sector_facts", {}).get(sec, {}) or {}).get("obs_count", 0)

    aq = intel.get("arabic_quality_rules")
    return {
        "must_use": must_use,
        "never_use": never_use,
        "visual_dna": visual_dna,
        "winning_formulas": [],   # v3.0 dropped; no live equivalent (honest empty)
        "universal": aq[:3] if isinstance(aq, list) else [],
        "occasion": intel.get("occasion_calendar", {}).get(occasion, {}),
        "emotion": {},            # v3.0 dropped; no live equivalent
        "campaign_arc": {},       # v3.0 dropped; no live equivalent
        "obs_count": obs_count,
    }


def select_chains(sector, occasion, intel=None, count=3):
    """Select best production chains matching intelligence visual recommendations."""
    # Get visual preferences from intelligence
    preferred_keywords = set()
    if intel and intel.get("visual_dna"):
        for v in intel["visual_dna"]:
            for word in (v.get("lighting", "") + " " + v.get("setting", "")).lower().split():
                if len(word) > 3:
                    preferred_keywords.add(word)
    # Always prefer these over UGC
    preferred_keywords.update({"studio", "dramatic", "moody", "hero", "premium", "product", "spotlight"})

    candidates = []
    for f in sorted(CHAINS.glob("TF*/tf*.json")):
        d = json.loads(f.read_text())
        ef = d.get("eligibility_filters", {})
        sa = ef.get("sectors_allowed", [])
        oa = ef.get("occasions_allowed", [])

        sector_ok = not sa or "*" in sa or sector in sa or any(s in sector for s in sa)
        occasion_ok = not oa or "*" in oa or occasion in oa or "evergreen" in oa

        if sector_ok and occasion_ok and d.get("prompt_template"):
            # Score by visual match (higher = better match to intelligence)
            prompt_lower = d.get("prompt_template", "").lower()
            visual_score = sum(1 for kw in preferred_keywords if kw in prompt_lower)
            # Penalize UGC/real-person chains when we have AI generation options
            model = d.get("models_used", [{}])[0].get("provider", "")
            if model == "other":
                visual_score -= 5
            d["_visual_score"] = visual_score
            candidates.append(d)

    # Sort by visual match (desc), then cost (asc)
    candidates.sort(key=lambda c: (-c.get("_visual_score", 0), c.get("cost_estimate_usd", 99)))
    return candidates[:count]


def fill_prompt(template, brand, product, sector, cultural_constraints=""):
    """Fill a chain prompt template with brand details."""
    replacements = {
        "{product_descriptor}": product or f"{brand} product",
        "{brand_color}": "#000000",
        "{background_color}": "dark charcoal",
        "{background_tone}": "deep black",
        "{beverage_descriptor}": f"{brand} signature drink",
        "{glass_style}": "traditional Saudi glass",
        "{quality_tier}": "premium",
        "{cultural_constraints_injection}": cultural_constraints or "Saudi-appropriate, no alcohol, halal imagery, modest presentation",
        "{tone_descriptor}": "warm, dignified, inviting",
    }
    result = template
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def generate_concept(brand, sector, occasion, product, intel):
    """Use LLM to generate a creative concept from intelligence."""
    from scripts.lib.openai_client import make_client, load_openai_key
    api_key = os.environ.get("OPENAI_API_KEY") or load_openai_key()
    if not api_key:
        return _fallback_concept(brand, sector, occasion, intel)

    client = make_client(api_key)  # timeout=90 + max_retries=2 baked in (B258)

    must_use = "\n".join(f"- {p['pattern']} ({p['engagement']}% high)" for p in intel["must_use"][:3])
    visual = "\n".join(f"- {v['lighting']} + {v['setting']} = {v['high_pct']}%" for v in intel["visual_dna"][:2])
    emotion = intel.get("emotion", {}).get("emotion", "anticipation")
    arc = intel.get("campaign_arc", {})

    # Load Brand DNA if available
    brand_dna_section = ""
    brand_handle = brand.lower().replace(" ", "").replace("-", "")
    dna_path = BASE / "logs" / "brand_dna" / f"{brand_handle}_gpt.json"
    if dna_path.exists():
        dna = json.loads(dna_path.read_text())
        bv = dna.get("brand_voice", {})
        cf = dna.get("content_formula", {})
        sig = bv.get("signature_phrases", [])
        brand_dna_section = f"""
BRAND DNA (from {dna.get('obs_count', 0)} observations of @{brand_handle}):
- Voice: {bv.get('summary', 'N/A')}
- Tone: {', '.join(bv.get('tone_tags', []))}
- Language: {bv.get('language_style', 'arabic-first')}
- Arabic style: {bv.get('arabic_technique', 'gulf')}
- Signature phrases: {', '.join(sig[:3]) if sig else 'none'}
- Best format: {cf.get('best_performing_type', 'N/A')}
- Top patterns: {', '.join(cf.get('top_patterns', [])[:4])}
"""

    prompt = f"""You are a Saudi creative director. Generate a creative concept for:

Brand: {brand}
Sector: {sector}
Occasion: {occasion}
Product: {product or "brand experience"}

CRITICAL: The brand name is "{brand}" — use this EXACT name. Do NOT change, translate, or modify the brand name. The product is "{product or 'brand experience'}" — use this EXACT product description.
{brand_dna_section}
DATA-BACKED INTELLIGENCE (from 4315 benchmark observations):
Best patterns:
{must_use}

Best visual combos:
{visual}

Best emotion: {emotion}
Campaign arc: {arc.get('arc_description', 'Start with anticipation, build to pride, close with warmth')}

Generate a creative concept with:

1. CONCEPT NAME (Arabic + English, 5 words max — must include the brand name "{brand}" exactly as written)
2. CONCEPT DESCRIPTION (2 sentences — what's the idea? Reference the actual product: {product or 'brand experience'})
3. VISUAL WORLD (specific: lighting, colors, textures, mood — based on the data above)
4. STORYBOARD (5 frames for a carousel or video):
   Frame 1: [Opening hook — {emotion}]
   Frame 2: [Build tension]
   Frame 3: [Hero moment — show the actual product: {product or 'brand'}]
   Frame 4: [Cultural connection — heritage/community]
   Frame 5: [Close — call to action]
5. CAPTION (Arabic, Gulf dialect, {', '.join(intel.get('emotion', {}).get('emotion', 'inviting').split(',')[:1])} tone, 50-150 chars — reference the product by name)
6. MOOD REFERENCE (describe the look and feel in one sentence)

Be specific. This goes to a production team who needs to shoot tomorrow."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def _fallback_concept(brand, sector, occasion, intel):
    """Generate concept without LLM — from data alone."""
    mu = intel["must_use"][0] if intel["must_use"] else {"pattern": "product_hero", "engagement": 50}
    vis = intel["visual_dna"][0] if intel["visual_dna"] else {"lighting": "natural", "setting": "studio", "high_pct": 50}
    emotion = intel.get("emotion", {}).get("emotion", "anticipation")

    return f"""## Creative Concept (data-driven fallback)

1. CONCEPT: {brand} × {mu['pattern'].replace('_',' ').title()} ({occasion})
2. DESCRIPTION: Showcase {brand} through {mu['pattern'].replace('_',' ')} pattern ({mu['engagement']}% high engagement).
   Visual world anchored in {vis['lighting']} lighting with {vis['setting']} setting.
3. VISUAL WORLD: {vis['lighting']} lighting, {vis['setting']} setting ({vis['high_pct']}% engagement proven)
4. STORYBOARD:
   Frame 1: Opening with {emotion} — tease the product/experience
   Frame 2: Build with visual detail — close-up texture, craftsmanship
   Frame 3: Hero reveal — full product shot in {vis['lighting']} lighting
   Frame 4: Cultural moment — heritage connection, Arabic text overlay
   Frame 5: Close — community/warmth, invitation to visit/try
5. EMOTION ARC: {emotion} → curiosity → pride → warmth → action
6. DATA CONFIDENCE: {mu['engagement']}% high engagement for this pattern, backed by {intel['obs_count']} observations"""


def run_pipeline(brand, sector, occasion, product=None):
    """Run the full creative pipeline."""
    print(f"\n{'═' * 60}")
    print(f"  CREATIVE PIPELINE: {brand} | {sector} | {occasion}")
    print(f"{'═' * 60}")

    # 1. Intelligence
    print("\n── 1. INTELLIGENCE LAYER")
    intel = load_intelligence(sector, occasion)
    print(f"  Sector: {sector} ({intel['obs_count']} obs)")
    print(f"  Must-use: {[p['pattern'] for p in intel['must_use'][:3]]}")
    print(f"  Emotion: {intel.get('emotion', {}).get('emotion', '?')}")
    if intel["visual_dna"]:
        print(f"  Visual: {intel['visual_dna'][0]['lighting']} + {intel['visual_dna'][0]['setting']}")
    print(f"  Occasion verdict: {intel.get('occasion', {}).get('verdict', '?')}")

    # 2. Creative Concept
    print("\n── 2. CREATIVE CONCEPT")
    concept = generate_concept(brand, sector, occasion, product, intel)
    print(concept)

    # 3. Production Chains (fal.ai prompts)
    print("\n── 3. PRODUCTION CHAINS (ready-to-use fal.ai prompts)")
    chains = select_chains(sector, occasion, intel=intel, count=3)
    for i, chain in enumerate(chains, 1):
        filled = fill_prompt(
            chain.get("prompt_template", ""),
            brand, product, sector,
        )
        models = chain.get("models_used", [{}])
        model = f"{models[0].get('provider', '?')}/{models[0].get('model_id', '?')}" if models else "?"
        print(f"\n  Chain {i}: {chain['name_en']} ({chain['chain_id_short']})")
        print(f"  Model: {model}")
        print(f"  Cost: ${chain.get('cost_estimate_usd', '?')}")
        print(f"  Output: {chain.get('output_type', '?')}")
        print(f"  Prompt:")
        print(f"  {filled[:300]}...")

    # 4. Storyboard Summary
    print(f"\n── 4. STORYBOARD SEQUENCE")
    arc = intel.get("campaign_arc", {})
    print(f"  Opening emotion: {arc.get('opening_emotion', 'anticipation')}")
    print(f"  Peak emotion: {arc.get('peak_emotion', 'pride')}")
    print(f"  Closing emotion: {arc.get('closing_emotion', 'warmth')}")
    print(f"  Arc: {arc.get('arc_description', 'anticipation → pride → warmth')}")

    # Save output
    output = {
        "brand": brand, "sector": sector, "occasion": occasion,
        "product": product, "intelligence": intel,
        "concept": concept, "chains": [c["chain_id_short"] for c in chains],
        "timestamp": datetime.now().isoformat(),
    }
    out_dir = BASE / "logs" / "creative_runs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{brand}_{occasion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    print(f"\n✅ Pipeline saved: {out_path}")

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True)
    parser.add_argument("--sector", required=True)
    parser.add_argument("--occasion", default="evergreen")
    parser.add_argument("--product", default=None)
    args = parser.parse_args()

    run_pipeline(args.brand, args.sector, args.occasion, args.product)


if __name__ == "__main__":
    main()
