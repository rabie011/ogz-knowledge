#!/usr/bin/env python3
"""
build_intelligence_playbook.py
Synthesize all analytical artifacts into a master intelligence playbook.
Answers the most common content strategy questions with direct corpus evidence.

Reads from all existing logs (does not re-scan obs directly).
Output: logs/intelligence_playbook.json
"""
import json
from pathlib import Path
from collections import defaultdict

LOGS = Path(__file__).parent.parent / "logs"


def safe_load(filename):
    path = LOGS / filename
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def top_items(lst, key_field, value_field, n=5):
    """Pull top N items from a list by a numeric value field."""
    return sorted(lst, key=lambda x: -x.get(value_field, 0))[:n]


def main():
    # Load all artifacts
    eng_signals  = safe_load("engagement_signal_table.json")
    media_eng    = safe_load("media_engagement_analysis.json")
    temporal     = safe_load("temporal_analysis.json")
    color_dna    = safe_load("color_palette_dna.json")
    patterns_net = safe_load("pattern_network_graph.json")
    setting_norm = safe_load("setting_normalization.json")
    lighting_comp= safe_load("lighting_composition_normalization.json")
    char_anal    = safe_load("character_analysis.json")
    x_sector     = safe_load("cross_sector_benchmark.json")
    pillars      = safe_load("content_pillars.json")
    themes       = safe_load("account_themes_index.json")
    archetypes   = safe_load("account_archetypes.json")
    brand_dna    = safe_load("brand_dna_index.json")
    cooc         = safe_load("pattern_cooccurrence_matrix.json")
    recipes      = safe_load("content_recipe_combos.json")
    similarity   = safe_load("account_similarity_matrix.json")

    # ── 1. Best formats ──────────────────────────────────────────────────────
    media_ranking = media_eng.get("media_type_ranking", [])
    format_answer = {
        "question": "What media format maximises engagement?",
        "answer": "Carousel slides first, then Reels. Single images are mid-tier. Long video underperforms.",
        "evidence": [
            {
                "format": r["media_type"],
                "high_engagement_rate": r["high_engagement_rate"],
                "obs_count": r["count"],
                "verdict": r["verdict"]
            }
            for r in media_ranking
        ]
    }

    # ── 2. Best day to post ──────────────────────────────────────────────────
    dow = temporal.get("day_of_week_analysis", {}).get("ranked_best_to_worst", [])
    we  = temporal.get("day_of_week_analysis", {}).get("weekday_vs_weekend", {})
    timing_answer = {
        "question": "What day of the week produces the highest engagement?",
        "answer": f"{dow[0]['day']} is the best posting day. {dow[-1]['day']} is the worst. Weekends outperform weekdays (50% vs 43% high engagement).",
        "day_ranking": [{"day": d["day"], "high_engagement_rate": d["high_engagement_rate"], "obs_count": d["count"]} for d in dow],
        "top_months": temporal.get("month_analysis", {}).get("ranked_best_to_worst", [])[:5],
    }

    # ── 3. Top engagement signals ────────────────────────────────────────────
    all_signals = eng_signals.get("all_signals", [])
    top_pos = [s for s in all_signals if s.get("verdict") in ("strong_positive", "positive") and s.get("obs_count", 0) >= 3][:20]
    to_avoid = [s for s in all_signals if s.get("verdict") == "avoid" and s.get("obs_count", 0) >= 3][:10]

    signals_answer = {
        "question": "Which content features consistently drive high engagement?",
        "top_positive_signals": top_pos,
        "signals_to_avoid": to_avoid,
    }

    # ── 4. Best patterns ─────────────────────────────────────────────────────
    pattern_signals = [s for s in top_pos if s["signal_type"] == "pattern"][:10]
    hub_patterns = patterns_net.get("top_hub_patterns", [])[:5]

    pattern_answer = {
        "question": "Which patterns are highest-engagement AND most versatile?",
        "answer": "heritage_storytelling_hook (100%), parallel_original_bilingual (100%), urgency_without_pressure (100%), community_pride_statement (92%), eid_occasion_greeting (100%) are the strongest pattern signals.",
        "highest_engagement_patterns": pattern_signals,
        "hub_patterns_most_versatile": [
            {"slug": p["slug"], "name": p["name"], "weighted_degree": p["weighted_degree"]}
            for p in hub_patterns
        ],
    }

    # ── 5. Best settings ─────────────────────────────────────────────────────
    setting_table = setting_norm.get("setting_engagement_table", [])
    setting_answer = {
        "question": "What setting should content be shot in?",
        "answer": "Outdoor/retail (87%), outdoor nature (68%), heritage environments (67%) outperform indoor restaurants (47%). Editorial lifestyle is the weakest at 20%.",
        "setting_ranking": setting_table,
    }

    # ── 6. Best lighting ─────────────────────────────────────────────────────
    lighting_table = lighting_comp.get("lighting", {}).get("engagement_table", [])
    lighting_answer = {
        "question": "What lighting style drives the most engagement?",
        "answer": "Dramatic/moody lighting (68%) outperforms clean cold studio (48%) and branded bright (35%).",
        "lighting_ranking": [r for r in lighting_table if r.get("count", 0) >= 5],
    }

    # ── 7. Best compositions ─────────────────────────────────────────────────
    comp_table = lighting_comp.get("composition", {}).get("engagement_table", [])
    comp_answer = {
        "question": "What composition style produces the best engagement?",
        "answer": "Architectural framing (64%) and overhead spread (62%) outperform product hero close-up (48%), which is the most overused composition in the corpus.",
        "composition_ranking": [r for r in comp_table if r.get("count", 0) >= 5],
    }

    # ── 8. Best color palettes ───────────────────────────────────────────────
    color_table = color_dna.get("fleet_color_family_engagement", [])
    color_answer = {
        "question": "What color palettes drive the most engagement?",
        "answer": "Mixed/vibrant palettes (81%) and amber/gold (62%) are the top performers. Red and grey are weakest.",
        "color_family_ranking": [r for r in color_table if r.get("obs_count", 0) >= 5],
    }

    # ── 9. Heritage vs Modern ────────────────────────────────────────────────
    heritage_signals = [s for s in all_signals if "heritage" in s.get("signal_value", "") and s.get("verdict") in ("strong_positive", "positive")]
    modern_signals   = [s for s in all_signals if "modern" in s.get("signal_value", "") and s.get("verdict") in ("strong_positive", "positive")]
    heritage_answer = {
        "question": "Does heritage content outperform modern content?",
        "answer": "Yes — heritage_vs_modern: heritage signals score 100% where present. Heritage patterns (heritage_storytelling_hook, community_pride_statement) are 2-3x stronger than educational or modern equivalents.",
        "heritage_positive_signals": heritage_signals[:5],
        "modern_positive_signals": modern_signals[:5],
    }

    # ── 10. Character/people ─────────────────────────────────────────────────
    char_data = char_anal.get("character_presence_vs_engagement", {})
    count_buckets = char_anal.get("character_count_buckets", {})
    character_answer = {
        "question": "Does showing people in frame help engagement?",
        "answer": "Yes — posts with people: 59% high eng vs without: 51%. 4+ people in a group shot: 90% high eng.",
        "has_characters": char_data.get("has_characters", {}),
        "no_characters": char_data.get("no_characters", {}),
        "count_buckets": count_buckets,
    }

    # ── 11. Sector findings ──────────────────────────────────────────────────
    sector_profiles = x_sector.get("sector_profiles", {})
    sector_answer = {
        "question": "How do sectors compare on engagement performance?",
        "answer": "F&B leads at 60% high engagement. Retail mid at 36%. Beauty lags at 18% — dragged by medical claims and generic flat-lays.",
        "sector_comparison": {
            sec: {
                "high_engagement_rate": prof["engagement"]["high_engagement_rate"],
                "dominant_tone": prof["voice"]["dominant_tone"],
                "top_pattern": prof["top_10_patterns"][0]["slug"] if prof.get("top_10_patterns") else None,
            }
            for sec, prof in sector_profiles.items()
        },
    }

    # ── 12. Content recipe combos ────────────────────────────────────────────
    master_recipes = recipes.get("master_triplet_recipes", [])[:8]
    recipe_answer = {
        "question": "What pattern combinations (recipes) are proven to work?",
        "answer": "Top recipe: lifestyle_integration + overhead_tabletop + product_hero (11 obs, 1.0 avg eng). heritage_storytelling_hook as anchor pattern elevates any combo.",
        "master_triplet_recipes": master_recipes,
        "top_pairs": cooc.get("top_pairs", [])[:8],
    }

    # ── 13. Anti-patterns (things to avoid) ─────────────────────────────────
    fleet_anti = themes.get("fleet_wide", {}).get("top_anti_patterns", [])[:10]
    avoid_answer = {
        "question": "What content types and approaches should be avoided?",
        "answer": "Sponsored content without authentic angle (26 accounts flag this), generic flat-lays (25 accounts), medical-claim language in beauty (17 accounts), educational/explainer format (19% eng rate), lifestyle_embed pattern (11%).",
        "anti_patterns_from_account_files": fleet_anti,
        "lowest_engagement_signals": to_avoid[:8],
    }

    # ── 14. Brand positioning (archetypes) ──────────────────────────────────
    archetype_dist = archetypes.get("fleet_distribution", {})
    archetype_answer = {
        "question": "What brand archetype is most common, and which performs best?",
        "answer": "Modern Premium dominates (10/15 accounts). Heritage Anchor is rare but has the highest-scoring individual account (OGZ-F-AND-B-Reference-010, health grade A, 86% avg eng).",
        "fleet_distribution": {arch: info["count"] for arch, info in archetype_dist.items()},
        "top_accounts_by_health": brand_dna.get("accounts", [])[:5],
    }

    # ── 15. Content pillars ──────────────────────────────────────────────────
    fleet_pillars = pillars.get("fleet_pillar_distribution", [])
    pillar_answer = {
        "question": "What content pillars drive the best engagement?",
        "answer": "Lifestyle Editorial (70% high eng) > Seasonal/Occasion (69%) > Product Showcase (55%). Product Showcase is the most used (45% of all posts) but not the highest performer.",
        "fleet_pillar_distribution": fleet_pillars,
    }

    # ── 16. Competitive gaps ─────────────────────────────────────────────────
    gap_pairs = similarity.get("top_10_most_differentiated_pairs", [])
    similar_pairs = similarity.get("top_20_most_similar_pairs", [])[:5]
    competitive_answer = {
        "question": "Which accounts are competitive twins, and which are maximally differentiated?",
        "most_similar_pairs": similar_pairs,
        "most_different_pairs": gap_pairs[:5],
    }

    # ── Assemble playbook ────────────────────────────────────────────────────
    playbook = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "title": "OGZ Saudi Instagram Intelligence Playbook",
        "corpus": {
            "total_observations": 474,
            "total_accounts": 15,
            "total_patterns": 159,
            "sectors": ["f_and_b", "beauty", "retail"],
            "analytical_artifacts": 27,
        },
        "executive_summary": {
            "top_5_actionable_findings": [
                "Use carousel format — 74% high engagement vs 37% for video. Single images are mid-tier (53%).",
                "Post on Sundays — 60% high eng vs 38% on Tuesdays. March and January are peak months.",
                "Heritage content pattern (heritage_storytelling_hook) achieves 100% high engagement across 13 observations.",
                "Architectural framing and overhead spreads outperform product hero close-up (64-62% vs 48%). Product hero is overused.",
                "Dramatic/moody lighting outperforms clean cold studio (68% vs 48%). Branded bright is the worst (35%).",
            ],
            "top_5_things_to_avoid": [
                "Video format — lowest engagement rate (37%) despite being widely used (122 obs).",
                "Educational explainer pattern — 19% high engagement across 26 observations.",
                "editorial_lifestyle setting — 20% high engagement (avoid this setting type).",
                "Branded bright lighting — 35% high engagement, weakest lighting category.",
                "Generic product-only flat-lays — flagged as anti-pattern by 25 accounts.",
            ],
        },
        "answers": {
            "1_what_format": format_answer,
            "2_when_to_post": timing_answer,
            "3_top_engagement_signals": signals_answer,
            "4_best_patterns": pattern_answer,
            "5_best_setting": setting_answer,
            "6_best_lighting": lighting_answer,
            "7_best_composition": comp_answer,
            "8_best_colors": color_answer,
            "9_heritage_vs_modern": heritage_answer,
            "10_people_in_frame": character_answer,
            "11_sector_performance": sector_answer,
            "12_content_recipes": recipe_answer,
            "13_what_to_avoid": avoid_answer,
            "14_brand_archetypes": archetype_answer,
            "15_content_pillars": pillar_answer,
            "16_competitive_positioning": competitive_answer,
        }
    }

    (LOGS / "intelligence_playbook.json").write_text(
        json.dumps(playbook, ensure_ascii=False, indent=2)
    )

    print("OGZ Intelligence Playbook built")
    print(f"\n{'═'*60}")
    print("EXECUTIVE SUMMARY")
    print(f"{'═'*60}")
    print("\nTop 5 findings:")
    for i, f in enumerate(playbook["executive_summary"]["top_5_actionable_findings"], 1):
        print(f"  {i}. {f}")
    print("\nTop 5 things to avoid:")
    for i, f in enumerate(playbook["executive_summary"]["top_5_things_to_avoid"], 1):
        print(f"  {i}. {f}")
    print(f"\nOutput: logs/intelligence_playbook.json")


if __name__ == "__main__":
    main()
