#!/usr/bin/env python3
"""Occasion FACTS — replaces the poetic occasion_tension (de-poison L1.1, June 11).

Source: 06_saudi_calendar/*.yaml (already rich: content_focus_themes, content_dos,
day variations — validated cultural data). Extracted by CODE, not generated — zero
poison risk. The 4 everyday post-types get hand-authored behavioral facts inline
(they are post types, not calendar occasions — correctly NOT added to the calendar).

Doctrine note: only POSITIVE facts (themes/dos) flow into prompts; content_donts
stay in the facts file for the judge/filter side, never inside a generation prompt.

Output: data/occasion_facts.json
"""
import json
from pathlib import Path

import yaml

BASE = Path(__file__).parent.parent
OUT = BASE / "data" / "occasion_facts.json"

EVERYDAY = {
    "new_product": {
        "name_ar": "إطلاق منتج جديد",
        "themes": ["novelty and first-taste excitement", "clear product name and what's new about it",
                    "availability: where/when/how to order", "early-adopter pride (be the first)"],
        "dos": ["lead with the news itself — the product IS the story",
                 "state availability plainly (app, branch, date)",
                 "invite trial with the brand's own CTA style"],
        "donts": ["no philosophical framing — it's news, not poetry"],
    },
    "weekly_offer": {
        "name_ar": "عرض الأسبوع",
        "themes": ["deal clarity: what, how much, until when", "urgency that respects the reader",
                    "repeat-visit habit building"],
        "dos": ["numbers explicit (price/percentage)", "deadline visible", "one offer per post"],
        "donts": ["no fake scarcity"],
    },
    "new_branch": {
        "name_ar": "افتتاح فرع جديد",
        "themes": ["neighborhood pride — the brand came TO YOU", "exact location, landmarks",
                    "opening-day energy and welcome"],
        "dos": ["name the district/street like a local", "welcome phrasing in the brand's voice",
                 "invite the neighborhood specifically"],
        "donts": [],
    },
    "daily_post": {
        "name_ar": "منشور يومي عادي",
        "themes": ["ordinary-day relevance (mood, weather, time of day)", "community feeling",
                    "light engagement (a smile, a question, a moment)"],
        "dos": ["small and warm beats big and loud", "today-specific feeling"],
        "donts": ["no occasion pretending"],
    },
}


def main():
    facts = {}
    for f in sorted((BASE / "06_saudi_calendar").glob("*.yaml")):
        d = yaml.safe_load(f.read_text().split("---", 1)[-1])
        if not isinstance(d, dict) or "occasion_slug" not in d:
            continue
        slug = d["occasion_slug"]
        sig = d.get("cultural_significance", {}) or {}
        facts[slug] = {
            "name_ar": d.get("name_ar", slug),
            "name_en": d.get("name_en", slug),
            "themes": d.get("content_focus_themes", [])[:6],
            "dos": d.get("content_dos", [])[:6],
            "donts": d.get("content_donts", []),          # judge/filter side ONLY
            "commercial_note": sig.get("commercial_activity", ""),
            "family_centrality": sig.get("family_centrality", ""),
            "source": f"06_saudi_calendar/{f.name}",
        }
    for slug, d in EVERYDAY.items():
        facts[slug] = {**d, "name_en": slug, "commercial_note": "", "family_centrality": "",
                        "source": "build_occasion_facts.py inline (post-type, not calendar)"}
    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"✓ occasion_facts.json: {len(facts)} occasions ({len(facts)-len(EVERYDAY)} from calendar + {len(EVERYDAY)} everyday)")


if __name__ == "__main__":
    main()
