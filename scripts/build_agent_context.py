#!/usr/bin/env python3
"""
build_agent_context.py — Generate intelligence context blocks for agent prompts.

The intelligence layer distilled into prompt-ready context that every agent
reads before thinking. Each block is 500-800 tokens — fits any model's budget.

Usage:
  python3 scripts/build_agent_context.py --sector f_and_b --occasion ramadan --role ceo
  python3 scripts/build_agent_context.py --sector beauty_personal_care --role cco
  python3 scripts/build_agent_context.py --all-roles --sector f_and_b --occasion evergreen

Roles: ceo, cco, coo, cd_router, brief_engine, scorer
"""
import json, argparse, os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
INTEL_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"


def load_intelligence() -> dict:
    if not INTEL_PATH.exists():
        raise FileNotFoundError(f"Intelligence layer not found at {INTEL_PATH}")
    with open(INTEL_PATH) as f:
        return json.load(f)


def build_context(sector: str, occasion: str = "evergreen", role: str = "ceo") -> str:
    """Build a prompt-ready intelligence context block for a specific agent role."""
    intel = load_intelligence()
    playbook = intel.get("sector_playbooks", {}).get(sector, {})
    obs_count = playbook.get("obs_count", 0)

    lines = [
        f"## INTELLIGENCE CONTEXT (from {intel['meta'].get('generated_from', 'benchmark observations')})",
        "",
        f"SECTOR: {sector} ({obs_count} obs)",
        "",
    ]

    if role in ("ceo", "brief_engine", "scorer"):
        # Must-use patterns
        must_use = playbook.get("must_use", [])
        if must_use:
            lines.append("### MUST USE (highest engagement patterns):")
            for p in must_use[:8]:
                lines.append(f"- {p['pattern']} as {p['as']} = {p['engagement']}% high ({p['obs']} obs)")
            lines.append("")

        # Winning formulas
        formulas = playbook.get("winning_formulas", [])
        if formulas:
            lines.append("### WINNING FORMULAS:")
            for f in formulas[:5]:
                lines.append(f"- {f['content_type']} + {f['pattern']} + {f['occasion']} = {f['high_pct']}%")
            lines.append("")

        # Universal rules
        for r in intel.get("universal_rules", [])[:5]:
            lines.append(f"ALWAYS: {r['pattern']} ({r['engagement']}% high)")
        lines.append("")

        # Format rules
        for f in intel.get("format_rules", []):
            lines.append(f"FORMAT: {f['content_type']} = {f['engagement']}% high ({f['obs']} obs)")
        lines.append("")

    if role in ("ceo", "coo", "brief_engine"):
        # Visual rules
        visual = playbook.get("visual_dna", [])
        if visual:
            lines.append("### VISUAL DIRECTION:")
            for v in visual[:3]:
                lines.append(f"- {v['lighting']} + {v['setting']} = {v['high_pct']}% high")
            lines.append("")

        # Global visual rules
        preferred = [r for r in intel.get("visual_rules", []) if r.get("type") == "preferred"]
        avoid = [r for r in intel.get("visual_rules", []) if r.get("type") == "avoid"]
        if preferred:
            lines.append("BEST VISUAL COMBOS (global):")
            for v in preferred[:3]:
                lines.append(f"- {v['lighting']} + {v['setting']} = {v['engagement']}%")
        if avoid:
            lines.append("AVOID:")
            for v in avoid[:3]:
                lines.append(f"- {v['lighting']} + {v['setting']} = {v['engagement']}%")
        lines.append("")

    if role in ("cco", "brief_engine"):
        # Caption rules
        for cr in intel.get("caption_rules", []):
            if cr.get("type") == "language":
                lines.append(f"CAPTION: {cr['rule']}")
            elif cr.get("type") == "length":
                ranking = cr.get("ranking", [])
                if ranking:
                    best = ranking[0]
                    lines.append(f"CAPTION LENGTH: {best['length']} performs best ({best['high_pct']}% high)")
        lines.append("")

    if role in ("ceo", "coo", "brief_engine"):
        # Occasion rules
        occ_rules = intel.get("occasion_rules", [])
        current = [r for r in occ_rules if r["occasion"] == occasion]
        if current:
            r = current[0]
            lines.append(f"OCCASION: {r['occasion']} = {r['engagement']}% high — {r['verdict'].upper()}")
        else:
            lines.append(f"OCCASION: {occasion} — no specific data, use evergreen patterns")
        lines.append("")

    if role in ("ceo", "brief_engine"):
        # Anti-patterns (never use)
        never = playbook.get("never_use", [])
        if never:
            lines.append("### NEVER USE (consistently low engagement):")
            for p in never[:5]:
                lines.append(f"- {p['pattern']} as {p['as']} = {p['engagement']}% high")
            lines.append("")

    if role == "cd_router":
        # Cross-sector transfers
        transfers = intel.get("cross_sector_transfers", [])
        relevant = [t for t in transfers if t.get("strong_in") == sector or t.get("weak_in") == sector]
        if relevant:
            lines.append("### CROSS-SECTOR INTELLIGENCE:")
            for t in relevant[:5]:
                lines.append(f"- {t['pattern']}: {t['strong_pct']}% in {t['strong_in']} → {t['weak_pct']}% in {t['weak_in']}")
            lines.append("")

    context = "\n".join(lines)
    token_estimate = len(context.split()) * 1.3

    return context, int(token_estimate), obs_count


def build_all_roles(sector: str, occasion: str = "evergreen") -> dict:
    """Build context blocks for all agent roles."""
    roles = ["ceo", "cco", "coo", "cd_router", "brief_engine", "scorer"]
    results = {}
    for role in roles:
        ctx, tokens, obs = build_context(sector, occasion, role)
        results[role] = {"context": ctx, "tokens": tokens, "obs_backing": obs}
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", required=True)
    parser.add_argument("--occasion", default="evergreen")
    parser.add_argument("--role", default="ceo", choices=["ceo", "cco", "coo", "cd_router", "brief_engine", "scorer"])
    parser.add_argument("--all-roles", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.all_roles:
        results = build_all_roles(args.sector, args.occasion)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for role, data in results.items():
                print(f"\n{'═' * 50}")
                print(f"  ROLE: {role.upper()} ({data['tokens']} tokens)")
                print(f"{'═' * 50}")
                print(data["context"])
    else:
        ctx, tokens, obs = build_context(args.sector, args.occasion, args.role)
        if args.json:
            print(json.dumps({"context_block": ctx, "token_count": tokens, "obs_backing": obs}))
        else:
            print(ctx)
            print(f"\n--- {tokens} tokens | backed by {obs} observations ---")


if __name__ == "__main__":
    main()
