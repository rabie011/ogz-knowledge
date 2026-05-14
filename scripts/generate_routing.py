#!/usr/bin/env python3
"""
Day 4 / Task 4.2 — Generate 6 routing YAMLs in 01_how_to_decide/.

These are short config files read by the CEO agent at routing time. No formal schema;
provenance enforced.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import yaml

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "01_how_to_decide"
OUT.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
INDEX = json.load(open(REPO / "02_what_to_build" / "INDEX.json"))


def provenance(source: str, scope: str = "universal") -> dict:
    return {"source": source, "date_added": NOW, "confirmer": "Mohamed",
            "confidence": "experimental", "scope": scope}


def write_yaml(filename: str, data: dict, note: str) -> None:
    path = OUT / filename
    header = (f"# {filename}\n# {note}\n# Confidence: {data['provenance']['confidence']}\n"
              f"# Scope: {data['provenance']['scope']}\n\n---\n")
    path.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
    print(f"✓ {path.relative_to(REPO)}")


# Index chains by family for sector_to_chains
def chains_by_sector():
    by_sector = defaultdict(list)
    for ch in INDEX["chains"]:
        for s in ch.get("sectors_allowed", []):
            by_sector[s].append({
                "chain_ulid": ch["chain_ulid"],
                "chain_id_short": ch["chain_id_short"],
                "name_en": ch["name_en"],
                "family": ch["family"],
                "cost_estimate_usd": ch.get("cost_estimate_usd", 0),
            })
    return by_sector


# 1) intent → chain family
def intent_to_family():
    return {
        "schema_version": 1,
        "title": "Brief intent → chain-family mapping",
        "description": ("CEO agent uses this to narrow chain selection from the 23 TF families "
                        "down to a candidate subset before per-chain scoring. Multi-intent briefs "
                        "union the candidate sets."),
        "intents": {
            "product_hero_launch": {
                "primary_families": ["TF01", "TF02", "TF06", "TF21"],
                "secondary_families": ["TF03", "TF11", "TF22"],
                "notes": "Static and motion product reveals; TF01 silhouette/hero, TF02 dynamic splash, TF06 studio reveal, TF21 launch motion.",
            },
            "lifestyle_storytelling": {
                "primary_families": ["TF04", "TF13", "TF23"],
                "secondary_families": ["TF05", "TF09"],
                "notes": "Environmental scenes (TF04, TF13) + Saudi cultural lifestyle scenes (TF23).",
            },
            "occasion_ramadan": {
                "primary_families": ["TF16", "TF22"],
                "secondary_families": ["TF04", "TF23"],
                "notes": "TF16 Iftar/occasion-specific, TF22 occasion motion. Sector overrides apply.",
            },
            "occasion_eid_or_national": {
                "primary_families": ["TF16", "TF22", "TF23"],
                "secondary_families": ["TF04"],
                "notes": "Occasion greeting + cultural lifestyle scenes. Heritage tier elevates TF23.",
            },
            "promotion_offer": {
                "primary_families": ["TF15", "TF21"],
                "secondary_families": ["TF01"],
                "notes": "Discount/offer chains; tone-aligned per brand DNA (no aggressive sales for premium brands).",
            },
            "brand_announcement_milestone": {
                "primary_families": ["TF21", "TF22"],
                "secondary_families": ["TF06", "TF16"],
                "notes": "Manifesto + announcement chains. CEO routes to human-gate for first-ever campaigns.",
            },
            "behind_the_scenes_authenticity": {
                "primary_families": ["TF13", "TF23"],
                "secondary_families": ["TF04", "TF09"],
                "notes": "BTS + cultural scenes. Authenticity Detective brain often wins on these.",
            },
            "crisis_response": {
                "primary_families": [],
                "secondary_families": [],
                "notes": "ALWAYS routes to human gate. CEO classifies and holds; no automatic chain.",
                "force_human_gate": True,
            },
            "evergreen_brand_voice": {
                "primary_families": ["TF01", "TF04", "TF23"],
                "secondary_families": ["TF06", "TF11", "TF13"],
                "notes": "Default rotation when no specific intent or occasion drives the brief.",
            },
        },
        "provenance": provenance(
            source="research_corpus_synthesis + chain_INDEX.json + agent_prompts/CEO",
        ),
    }


# 2) sector → chains (with scores from existing sector baselines)
def sector_to_chains():
    return {
        "schema_version": 1,
        "title": "Sector → recommended-chain scoring",
        "description": ("Per-sector chain eligibility derived from chain `sectors_allowed` and "
                        "sector-baseline `default_eligible_chains`. CEO scoring multiplies these "
                        "with brand fingerprint cd_routing_weights and brain.sector_affinity."),
        "sectors": {
            "f_and_b": {"baseline_file": "05_sector_defaults/f_and_b.yaml", "see": "default_eligible_chains in sector baseline"},
            "retail": {"baseline_file": "05_sector_defaults/retail.yaml", "see": "default_eligible_chains in sector baseline"},
            "beauty": {"baseline_file": "05_sector_defaults/beauty.yaml", "see": "default_eligible_chains in sector baseline"},
            "real_estate": {"baseline_file": "05_sector_defaults/real_estate.yaml", "see": "default_eligible_chains in sector baseline"},
            "healthcare_wellness": {"baseline_file": "05_sector_defaults/healthcare_wellness.yaml", "see": "default_eligible_chains in sector baseline"},
        },
        "scoring_rules": [
            "Each chain has `sectors_allowed` (wildcard '*' or specific sector slugs) — chains with non-matching `sectors_allowed` are excluded.",
            "Eligible chains are scored by the sector baseline's `default_eligible_chains` (0–1).",
            "Brand can override sector-baseline weights at onboarding; per-brand overrides win.",
            "Cost: `cost_estimate_usd` factors into Starter-tier filtering (CEO cost-gate may exclude expensive chains for Starter).",
        ],
        "provenance": provenance(
            source="02_what_to_build/INDEX.json + 05_sector_defaults/*.yaml",
        ),
    }


# 3) occasion → chain triggers
def occasion_triggers():
    return {
        "schema_version": 1,
        "title": "Occasion auto-triggers — which chains fire when",
        "description": ("CEO agent reads this when an occasion is active. Each occasion may "
                        "elevate certain chains AND force-include others regardless of brand "
                        "preference (e.g. occasion greeting for the 5 major occasions)."),
        "occasions": {
            "ramadan": {
                "force_include_chains": ["tf16_01", "tf22_01"],
                "boost_chains": {"tf04_02": 1.30, "tf23_09": 1.25, "tf16_02": 1.20, "tf22_04": 1.20, "tf12_03": 1.15},
                "demote_chains_below": 0.40,
                "demote_reason": "Aggressive promotional chains discouraged in weeks 1-2",
                "demote_chain_ids": ["tf15_*"],
                "active_window_days_before": 21,
                "active_window_days_after": 0,
            },
            "eid_al_fitr": {
                "force_include_chains": ["tf16_02"],
                "boost_chains": {"tf22_04": 1.20, "tf22_05": 1.15, "tf21_02": 1.15, "tf23_09": 1.15, "tf04_03": 1.10},
                "active_window_days_before": 14,
                "active_window_days_after": 3,
            },
            "eid_al_adha": {
                "force_include_chains": ["tf16_02"],
                "boost_chains": {"tf22_04": 1.15, "tf04_02": 1.15, "tf23_09": 1.10, "tf23_10": 1.15},
                "blackout_sectors": ["entertainment"],
                "active_window_days_before": 14,
                "active_window_days_after": 4,
            },
            "saudi_national_day": {
                "force_include_chains": ["tf16_02", "tf22_04"],
                "boost_chains": {"tf23_10": 1.30, "tf23_08": 1.20, "tf21_02": 1.15, "tf22_05": 1.15},
                "active_window_days_before": 21,
                "active_window_days_after": 1,
            },
            "saudi_founding_day": {
                "force_include_chains": ["tf16_02", "tf22_04"],
                "boost_chains": {"tf23_10": 1.35, "tf04_05": 1.20, "tf06_03": 1.15},
                "active_window_days_before": 14,
                "active_window_days_after": 1,
            },
        },
        "provenance": provenance(
            source="06_saudi_calendar/*.yaml + chain INDEX",
        ),
    }


# 4) compliance gates
def compliance_gates():
    return {
        "schema_version": 1,
        "title": "Compliance gates — which checks run per chain × sector × brand",
        "description": ("CCO and CEO agents read this to decide which gates evaluate each piece "
                        "of generated content. Gates compose: a chain × sector × brand combination "
                        "may trigger multiple gates."),
        "gates": {
            "universal_forbidden_lists": {
                "applies_to": "all chains, all sectors, all brands",
                "checks": ["gestures", "props", "behaviors", "visuals"],
                "source_files": [
                    "15_cultural_specs/forbidden_lists/universal_gestures_forbidden.yaml",
                    "15_cultural_specs/forbidden_lists/universal_props_forbidden.yaml",
                    "15_cultural_specs/forbidden_lists/universal_behaviors_forbidden.yaml",
                    "15_cultural_specs/forbidden_lists/universal_visuals_forbidden.yaml",
                ],
                "violation_outcome": "HARD_BLOCK; score floored to 0",
            },
            "arabic_quality": {
                "applies_to": "every caption-bearing chain",
                "checks": ["dialect_match", "translation_smell", "ligature_correctness", "register"],
                "source_files": ["04_saudi_rules/arabic_text_rules.yaml"],
                "violation_outcome": "Score reduced; severe issues flag for human review",
            },
            "gender_rules": {
                "applies_to": "all chains depicting humans",
                "checks": ["mixed_gender_rule_per_brand", "modesty_threshold", "cross_gender_distance"],
                "source_files": ["04_saudi_rules/gender_rules.yaml", "15_cultural_specs/sector_defaults/*.yaml"],
                "violation_outcome": "soft_flag → human review; hard violation → HARD_BLOCK",
            },
            "occasion_alignment": {
                "applies_to": "content scheduled during occasion active windows",
                "checks": ["content_dos compliance", "content_donts violations", "anti_pattern_warnings"],
                "source_files": ["06_saudi_calendar/*.yaml"],
                "violation_outcome": "soft_flag with rewrite suggestion",
            },
            "sector_specific_compliance": {
                "applies_to": "by sector",
                "by_sector": {
                    "healthcare_wellness": "SFDA / MoH health-claim verification; no patient identifiers; PDPL strict",
                    "real_estate": "no guaranteed-return language; no unverifiable comparisons; no race/nationality-targeted pricing",
                    "f_and_b": "no alcohol/pork; no misleading health claims; halal-status accuracy",
                    "retail": "no false pricing claims; no exaggerated discount language; competitor-name exclusion",
                    "beauty": "no medical/treatment claims; no skin-tone hierarchy; no weight-loss timelines",
                },
                "violation_outcome": "STRONG_WARN to HARD_BLOCK depending on severity",
            },
            "saudi_flag_rule": {
                "applies_to": "any content using Saudi flag",
                "checks": ["upright orientation", "no overlay on faces or disposables", "respect of shahada"],
                "violation_outcome": "HARD_BLOCK",
            },
        },
        "provenance": provenance(
            source="research_corpus_synthesis + 04_saudi_rules + 15_cultural_specs + agent prompts",
        ),
    }


# 5) quality tier map
def quality_tier_map():
    return {
        "schema_version": 1,
        "title": "Pricing tier → access map",
        "description": ("Tier-based access to chains, frequency, human review, and quality "
                        "floors. CEO checks this at routing time."),
        "tiers": {
            "starter": {
                "monthly_posts_default": 8,
                "chains_allowed_count_max": 12,
                "chains_allowed_quality_filter": "quality_tiers_allowed contains 'starter'",
                "chains_excluded_pattern_filter": "cost_estimate_usd > 0.07 (cost-gate)",
                "human_review": "first-ever campaign only; subsequent auto-approve if confidence ≥ 75",
                "watermark_required_below_confidence": 75,
                "cultural_advisor_review": "spot-check 1 in 20 posts",
                "confidence_floor_min": 0.6,
                "monthly_price_sar_default": 2500,
                "characterization": "Self-service automated content for Saudi SMEs",
            },
            "growth": {
                "monthly_posts_default": 20,
                "chains_allowed_count_max": 25,
                "chains_allowed_quality_filter": "quality_tiers_allowed contains 'growth' OR 'starter'",
                "human_review": "first campaign + monthly hero post; otherwise auto-approve if confidence ≥ 75",
                "watermark_required_below_confidence": 75,
                "cultural_advisor_review": "all hero content + religious occasion content",
                "confidence_floor_min": 0.65,
                "strategist_involved": True,
                "characterization": "Managed services for growing Saudi brands",
            },
            "enterprise": {
                "monthly_posts_default": 40,
                "chains_allowed_count_max": "all 88",
                "chains_allowed_quality_filter": "all",
                "human_review": "all hero content; auto-approve only standard cadence",
                "watermark_required_below_confidence": 50,
                "cultural_advisor_review": "all content; CD lead involved in monthly planning",
                "confidence_floor_min": 0.7,
                "strategist_involved": True,
                "cd_lead_involved": True,
                "characterization": "AI-C-Suite managed services for larger Saudi brands and government",
            },
        },
        "provenance": provenance(
            source="research_corpus/OGzAI_Business_Model_V5_Final.docx + agent prompts",
        ),
    }


# 6) conflict resolution
def conflict_rules():
    return {
        "schema_version": 1,
        "title": "Conflict resolution — when rules contradict, who wins",
        "description": ("Deterministic precedence ordering when two or more rules point in "
                        "different directions. CEO and CCO apply these in order."),
        "precedence_order": [
            {"level": 1, "name": "universal_forbidden_lists", "rationale": "Hard-blocks are non-negotiable. No brand or sector override."},
            {"level": 2, "name": "saudi_compliance_rules", "rationale": "Saudi law and regulatory rules supersede brand preference."},
            {"level": 3, "name": "brand_explicit_rejection", "rationale": "Brand has explicitly forbidden a tone/visual/topic at onboarding or via correction — respect it."},
            {"level": 4, "name": "cultural_advisor_verdict", "rationale": "Human cultural reviewer's call beats automated heuristics."},
            {"level": 5, "name": "brand_fingerprint", "rationale": "Brand's chosen voice/visual/tone wins over sector default."},
            {"level": 6, "name": "occasion_active_overrides", "rationale": "Active occasion guidance overrides standard sector default."},
            {"level": 7, "name": "sector_baseline", "rationale": "Sector default is the fallback when no brand or occasion specific guidance applies."},
            {"level": 8, "name": "cd_brain_methodology", "rationale": "Within remaining latitude, the assigned CD brain's preferred constructions win."},
            {"level": 9, "name": "platform_default", "rationale": "Last-resort fallback to platform-wide defaults."},
        ],
        "conflict_examples": [
            {
                "scenario": "Brand fingerprint says 'modern-permissive modesty' but occasion is Ramadan with strict register",
                "resolution": "Occasion override (level 6) wins for that period. Revert to brand default after occasion window closes.",
            },
            {
                "scenario": "CD brain suggests humor; brand's tone_anti_attribute_ids excludes humor",
                "resolution": "Brand explicit rejection (level 3) wins. CD brain works within remaining latitude.",
            },
            {
                "scenario": "Healthcare sector compliance vs. Paradox Hunter (CD-05) contrarian register",
                "resolution": "Sector compliance (level 5) + sector_safety_lock excludes CD-05 from healthcare routing entirely (set in cd_brain_router_rules.yaml).",
            },
            {
                "scenario": "Cultural Advisor approves a brave-route caption; CCO scored it 55 (soft hold)",
                "resolution": "Cultural Advisor verdict (level 4) overrides CCO score; content publishes with verdict logged.",
            },
        ],
        "provenance": provenance(
            source="research_corpus_synthesis + ADRs + agent prompts",
        ),
    }


def main() -> int:
    write_yaml("intent_to_family.yaml", intent_to_family(), "Brief intent → candidate chain families.")
    write_yaml("sector_to_chains.yaml", sector_to_chains(), "Per-sector chain eligibility (refers to sector baselines).")
    write_yaml("occasion_triggers.yaml", occasion_triggers(), "Occasion auto-triggers and chain boosts/demotions.")
    write_yaml("compliance_gates.yaml", compliance_gates(), "Which compliance checks run per chain × sector × brand.")
    write_yaml("quality_tier_map.yaml", quality_tier_map(), "Pricing tier → chain access + human review level.")
    write_yaml("conflict_rules.yaml", conflict_rules(), "Precedence ordering when rules conflict.")
    print(f"\nWrote 6 routing YAMLs to {OUT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
