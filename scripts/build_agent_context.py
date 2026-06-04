#!/usr/bin/env python3
"""
build_agent_context.py — Thin brain context for LLM prompts.

Provides REAL context (not commands):
  - Cultural guardrails (what to avoid)
  - Real metrics (actual likes, clickable URLs)
  - Brand voice (tone, dialect, hashtags)
  - Occasion context (what's happening culturally)

Does NOT provide:
  - Engagement scores (were wrong)
  - "Always/Never" pattern rules (blocked good patterns)
  - Emotion prescriptions (failed for individual brands)

Usage:
  python3 scripts/build_agent_context.py --brand albaik --occasion ramadan
  python3 scripts/build_agent_context.py --brand pizzahutsaudi --occasion evergreen
"""
import json, argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
INTEL_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"


def build_context(brand_handle: str, occasion: str = "evergreen") -> str:
    """Build a thin context block for LLM prompts."""
    intel = json.loads(INTEL_PATH.read_text())

    lines = []

    # 1. Brand identity (if we have it)
    brand = intel.get("brand_profiles", {}).get(brand_handle, {})
    if brand:
        lines.append(f"## BRAND: @{brand_handle}")
        lines.append(f"Voice: {brand.get('voice', '')}")
        lines.append(f"Tone: {', '.join(brand.get('tone', []))}")
        lines.append(f"Arabic style: {brand.get('arabic_style', '')}")
        if brand.get("signature_phrases"):
            lines.append(f"Hashtags: {', '.join(brand['signature_phrases'])}")
        lines.append("")

    # 2. Real metrics (if we have them)
    metrics = intel.get("real_metrics", {}).get(brand_handle, {})
    if metrics and metrics.get("verified"):
        lines.append(f"## REAL ENGAGEMENT (verified from Instagram)")
        lines.append(f"Average: {metrics['avg_likes']:,} likes per post")
        lines.append(f"Best post: {metrics['max_likes']:,} likes")
        lines.append(f"Based on {metrics['obs_count']} real posts")
        lines.append("")

    # 3. Reference examples (top posts with URLs)
    examples = intel.get("reference_examples", {}).get(brand_handle, [])
    if examples:
        lines.append("## TOP POSTS (click to verify)")
        for e in examples[:3]:
            lines.append(f"- {e['likes']:,} likes | {e['content_type']} | {e['url']}")
            if e.get("caption_preview"):
                lines.append(f"  \"{e['caption_preview']}\"")
        lines.append("")

    # 4. Occasion context
    occ = intel.get("occasion_calendar", {}).get(occasion, {})
    if occ:
        lines.append(f"## OCCASION: {occasion}")
        lines.append(f"{occ.get('content_approach', '')}")
        lines.append("")

    # 5. Cultural guardrails (always include)
    cg = intel.get("cultural_guardrails", {})
    sacred = cg.get("sacred_occasions", {}).get(occasion, "")
    lines.append("## CULTURAL RULES (hard blocks)")
    lines.append(f"Forbidden: {', '.join(cg.get('forbidden_behaviors', []))}")
    if sacred:
        lines.append(f"⚠️ {occasion}: {sacred}")
    modesty = cg.get("modesty_rules", {})
    sector = brand.get("sector", "")
    sector_modesty = modesty.get(f"{sector}_sector", modesty.get("default", ""))
    if sector_modesty:
        lines.append(f"Modesty: {sector_modesty}")
    lines.append("")

    # 6. Honest gaps
    gaps = intel.get("honest_gaps", [])
    if gaps:
        sector_gaps = [g for g in gaps if sector in g.lower()] if sector else []
        if sector_gaps:
            lines.append("## ⚠️ DATA LIMITATIONS")
            for g in sector_gaps[:2]:
                lines.append(f"- {g}")
            lines.append("")

    context = "\n".join(lines)
    tokens = int(len(context.split()) * 1.3)

    return context, tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True)
    parser.add_argument("--occasion", default="evergreen")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ctx, tokens = build_context(args.brand, args.occasion)
    if args.json:
        print(json.dumps({"context_block": ctx, "token_count": tokens}))
    else:
        print(ctx)
        print(f"\n--- {tokens} tokens ---")


if __name__ == "__main__":
    main()
