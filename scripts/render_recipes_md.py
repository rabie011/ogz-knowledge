#!/usr/bin/env python3
"""Render the pattern-card library as a human playbook (June 12 — the team reads
markdown, not JSON). Regenerate any time: python3 scripts/render_recipes_md.py"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent


def main():
    p = json.loads((BASE / "data/pattern_cards_v1.json").read_text())
    lines = [
        "# OGZ CAPTION RECIPES — the writers' menu",
        f"*Generated {datetime.now().isoformat(timespec='minutes')} from data/pattern_cards_v1.json — edit THERE, not here.*",
        "",
        "Every recipe is an applicable MOVE (like the 94 visual chains). Nothing enters",
        "production prompts before Mohamed ratifies it. A ratified recipe is a PLAYER:",
        "his rejections can bench it like a mind.",
        "",
    ]
    def order(c):
        s = str(c.get("status", ""))
        return (0 if s.startswith("RATIFIED") else 1 if "REVISED" in s else 2,
                -(c.get("rating_provisional") or 0))
    for c in sorted(p["survivors"], key=order):
        s = str(c.get("status", ""))
        badge = "✅ RATIFIED" if s.startswith("RATIFIED") else ("🔁 REVISED — awaiting re-approval" if "REVISED" in s else "⏳ awaiting Mohamed")
        lines += [
            f"## {c['slug']}  ·  {badge}  ·  Rabie {c.get('rating_provisional','?')}/5",
            f"**The move:** {c['move']}",
            f"**Skeleton:** {c['skeleton']}",
            f"**When:** {c['when']}",
            f"**Real example:** {c.get('example_real','—')}",
            f"**Fresh example:** {c.get('example_fresh','—')}",
            f"**How it dies:** {c['anti']}",
            f"**Sectors:** {c.get('sector_flavor','universal')}",
            "",
        ]
    lines += ["---", f"Killed in judging: {len(p.get('killed', []))} (reasons in the JSON). "
              f"Round-2 additions: {', '.join(p.get('round2', {}).get('added', []))}."]
    out = BASE / "20_cd_brains" / "CAPTION_RECIPES.md"
    out.write_text("\n".join(lines))
    print(f"✓ {out.relative_to(BASE)} — {len(p['survivors'])} recipes rendered")


if __name__ == "__main__":
    main()
