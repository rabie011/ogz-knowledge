#!/usr/bin/env python3
"""
Day 2 / Task 2.3 — Generate 5 Saudi rules YAML files.

These are short config files without dedicated v1 schemas — they are read by
agents and the compliance gate evaluator. Each file carries a provenance block
following CONVENTIONS.md §3.

Idempotent overwrite; no ULIDs needed at this layer (no record-level identity).
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "04_saudi_rules"
OUT_DIR.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance(source_ref: str, scope: str = "universal") -> dict:
    return {
        "source": source_ref,
        "date_added": NOW,
        "confirmer": "Mohamed",
        "confidence": "experimental",
        "scope": scope,
    }


# ───────────────────────────────────────────────────────────────────────────
# compliance_levels.yaml
# ───────────────────────────────────────────────────────────────────────────
def compliance_levels():
    return {
        "schema_version": 1,
        "title": "Saudi compliance enforcement levels",
        "description": "Three-tier enforcement model used by the CCO agent and compliance gates. Every rule, forbidden item, or cultural caution belongs to one of these levels.",
        "levels": {
            "hard_block": {
                "description": "System refuses to generate or publish. Not negotiable. No override path without a documented exception process plus dual approval.",
                "agent_behavior": "Generate an alternative draft and log the deflection. Notify the user that the request was reshaped, with a brief reason.",
                "examples": [
                    "alcohol product imagery or naming in promotional context",
                    "pork product imagery or naming in promotional context",
                    "gambling content (lotteries, betting, casino imagery)",
                    "graphic religious-imagery used as commercial backdrop (Kaaba, Mecca crowds for non-Hajj brand)",
                    "left-hand-serving-food in any framed scene (universal cultural rule)",
                    "depiction of fasting violation during Ramadan daylight hours",
                    "graphic slaughter imagery on Eid Al-Adha",
                    "Saudi flag misuse (upside-down, on disposable items, overlay on faces)",
                    "depiction of identifiable patients without consent (healthcare sector)",
                ],
            },
            "soft_flag": {
                "description": "Flagged for human review before publication. Can be released with explicit override by a human reviewer (brand owner or compliance reviewer).",
                "agent_behavior": "Generate as requested but route to human review queue. Include the flag reason in the side panel.",
                "examples": [
                    "mixed-gender groups in non-family non-public context",
                    "shorts, sleeveless tops, or revealing wardrobe in branded content",
                    "promotional content during Ramadan weeks 1-2 with discount-heavy language",
                    "comparison with competitors by name (regulator-sensitive in some sectors)",
                    "before/after imagery in beauty/healthcare (potential treatment-claim implication)",
                    "use of religious terminology in commercial context outside designated occasions",
                ],
            },
            "advisory": {
                "description": "Informational note attached to the output. No enforcement. Surfaces in the side panel as 'consider this'.",
                "agent_behavior": "Publish normally. Surface the advisory note in the side panel and in the next-week insights.",
                "examples": [
                    "palette deviates from sector default (may be intentional brand choice)",
                    "non-standard typography pairing",
                    "Arabic copy uses MSA where dialect would typically perform better for the audience",
                    "post timing falls within a non-optimal engagement window per benchmark data",
                    "the same chain has been used twice in the same week",
                ],
            },
        },
        "escalation": {
            "hard_block_override": "Requires written approval from Mohamed AND a Cultural Advisor. Logged as an exception event in the audit trail.",
            "soft_flag_release": "Single human reviewer (brand owner or compliance reviewer). Logged.",
            "advisory_acknowledge": "No formal action; tracked in metrics for pattern detection.",
        },
        "provenance": provenance(
            source_ref="CONVENTIONS.md§11 + research_corpus/CCO_Environment_v2.docx + Saudi_cultural_norms",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# saudi_visual_rules.yaml
# ───────────────────────────────────────────────────────────────────────────
def saudi_visual_rules():
    return {
        "schema_version": 1,
        "title": "Saudi visual compliance rules",
        "description": "Color, motif, and composition rules specific to Saudi visual context. Enforced by the COO agent at generation time and the CCO agent at QC time.",
        "color_semantics": {
            "saudi_green_official": {
                "hex": "#006C35",
                "rule": "Reserved for National Day, Founding Day, and explicitly patriotic content. Do not use as a generic accent. When used, full strength — never tinted or pastel-softened.",
            },
            "religious_palette": {
                "rule": "Avoid deep gold + green combinations that read as religious-flag imagery in non-religious commercial context.",
            },
            "color_combinations_to_avoid": [
                "any combination that visually evokes a foreign nation's flag in patriotic content",
                "red-on-green in iftar context (reads as Christmas-style; foreign palette)",
                "pure black-on-pure-white with no warmth in F&B context (reads as funerary)",
            ],
        },
        "motif_rules": {
            "approved_when_authentic": [
                "Najdi mud-brick architecture (Dir'iyah, At-Turaif, traditional homes)",
                "Hijazi rawasheen (latticed wooden windows)",
                "sadu weaving patterns (geometric, primary-color, woven texture)",
                "falcon (national symbol; use respectfully, never as background prop)",
                "palm tree and date palm in heritage contexts",
                "Arabic calligraphy when designed by a calligrapher (not auto-generated)",
                "thobe, ghutra, igal, mishlah for men; abaya, hijab in cultural framing for women",
            ],
            "do_not_use_without_brand_clearance": [
                "Kaaba imagery (reserved for Hajj-services brands or religious-content authority)",
                "Quranic verses overlaid on commercial imagery",
                "named historical figures (founders, royals) without official endorsement",
                "tribal markers (specific tribe symbols) — divisive in pan-Saudi context",
            ],
            "do_not_use": [
                "cheaply-rendered AI calligraphy that gibberishes the Arabic letterforms",
                "Saudi flag as decorative element on disposables, party items, or face overlays",
                "stock-feeling 'desert + camel + sunset' cliché unless intentionally subverted",
                "borrowed regional motifs falsely presented as Saudi (e.g., Emirati architecture, Egyptian symbols)",
            ],
        },
        "photography_conventions": {
            "lighting_register": "Saudi premium register favors warm natural daylight (golden hour) and clean diffuse studio. Avoid harsh-shadow editorial-fashion lighting for general SME content.",
            "modesty_default": "Talent fully covered unless brand has explicit face-visible permission at onboarding. Same-gender depiction preferred for personal-care contexts.",
            "regional_specificity": "Najdi, Hijazi, Eastern, and Southern visual contexts differ meaningfully (architecture, dress nuance, palette). Default per brand's stated region; never collapse to a generic 'Saudi'.",
            "talent_realism": "Real-talent lightly-directed is preferred over heavy posed studio work. Avoid stock-feeling smiles and over-rendered faces.",
        },
        "provenance": provenance(
            source_ref="research_corpus/CCO_Environment_v2.docx + Saudi_visual_culture_synthesis_2026",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# arabic_text_rules.yaml
# ───────────────────────────────────────────────────────────────────────────
def arabic_text_rules():
    return {
        "schema_version": 1,
        "title": "Arabic text rendering and writing rules",
        "description": "How the system writes, renders, and validates Arabic text. Applied at generation time (COO) and QC time (CCO).",
        "rendering": {
            "direction": "RTL by default for Arabic text blocks. Numerals: Indo-Arabic (٠١٢٣٤٥٦٧٨٩) preferred for native feel; Western Arabic (0123456789) acceptable in commercial-tech contexts.",
            "font_pairing": "Pair Arabic font with English Latin font at equal optical weight. Recommended: Neue Frutiger Arabic family with Modern Era (English). Never use machine-defaulted system fonts where licensing allows the brand pair.",
            "ligatures": "Use full Arabic ligatures (initial / medial / final / isolated). Never produce 'broken Arabic' where letters render as disconnected glyphs.",
            "diacritics": "Tashkeel (vowel diacritics) are optional. Use only when meaning would otherwise be ambiguous. Avoid over-vocalized text — it feels textbook-formal.",
        },
        "dialect_default": {
            "primary": "najdi (Riyadh-default for Saudi-domestic content)",
            "regional_overrides": {
                "hijazi": "for Jeddah, Makkah, Madinah, Western region brands",
                "eastern": "for Eastern Province brands (oil-sector cities)",
                "southern": "for Asir, Najran, Jazan brands",
            },
            "gulf_neutral": "khaleeji_neutral — for brands targeting GCC across borders",
        },
        "msa_usage": {
            "rule": "Modern Standard Arabic (MSA) is used only when context demands: government, religious occasions (Ramadan, Eid Al-Adha), official announcements, or brands that explicitly request MSA at onboarding.",
            "avoid_msa_for": [
                "casual social posts",
                "F&B and beauty content (sounds textbook-stiff)",
                "youth-targeted retail",
                "humor or warm-conversational content (MSA cannot do warmth)",
            ],
        },
        "codeswitching": {
            "rule": "Brand-controlled. Default tolerance per sector baseline.",
            "approved_patterns": [
                "Brand name in Latin script when registered that way (e.g., STC, Almarai)",
                "Tech/product terms with no native Arabic equivalent (e.g., podcast, Wi-Fi, app)",
                "Quoted English from an external source, kept in English for accuracy",
            ],
            "avoid": [
                "showing off bilingual capability where it interrupts flow",
                "translating words that have natural Arabic equivalents (e.g., 'time' → use الوقت, not 'time')",
                "more than 30% English in an Arabic-primary post",
            ],
        },
        "translation_smell": {
            "description": "Indicators that Arabic copy was machine-translated from English rather than written native. CCO flags these.",
            "indicators": [
                "English sentence structure preserved (verb-final or verb-first English patterns rendered awkwardly in Arabic)",
                "literal idiom translation ('break a leg' → كسر ساق)",
                "uniform tashkeel pattern that mimics translation-tool default",
                "stiff MSA where dialect would naturally flow",
                "absence of natural Arabic rhetorical devices (saj', repetition, parallel structure)",
                "inappropriate formal address (using حضرتك where dialect would say أنت)",
            ],
        },
        "writing_conventions": {
            "voice_anchor": "Arabic is a SIBLING to English, never a SUBTITLE. Each language carries its own resonance.",
            "headline_rule": "When English headline is bold/declarative, Arabic headline mirrors at equal weight — not smaller, not below.",
            "punctuation": "Arabic punctuation marks (؟ ، ؛) preferred. ASCII punctuation acceptable in mixed-script lines.",
            "emoji_rules": "One emoji maximum per caption, or none. Emoji never replaces an Arabic word that conveys the meaning.",
            "no_machine_translation": "Caption text must be authentically composed Arabic, not Google-translated English. CCO scores translation-smell as a quality dock.",
        },
        "provenance": provenance(
            source_ref="research_corpus/CCO_Environment_v2.docx + saudi_dialect_synthesis + bilingual_voice_principles",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# gender_rules.yaml
# ───────────────────────────────────────────────────────────────────────────
def gender_rules():
    return {
        "schema_version": 1,
        "title": "Gender depiction rules in Saudi visual content",
        "description": "Rules for how gender is depicted, mixed, or kept separate in generated content. Defaults are conservative; brand can unlock specific patterns at onboarding with explicit permission.",
        "default_posture": "conservative — when in doubt, choose the more modest framing",
        "patterns": {
            "same_gender_groups": {
                "rule": "Always allowed. Default visual register for personal-care, beauty, fitness, and wellness contexts.",
                "level": "allowed",
            },
            "mixed_family_groups": {
                "rule": "Allowed across all sectors. Multi-generational scenes (grandparents + parents + children) preferred for occasion content (Ramadan iftar, Eid family gatherings, National Day outings).",
                "level": "allowed",
            },
            "mixed_strangers_public_context": {
                "rule": "Allowed in clearly public-business contexts (café, retail floor, office reception, conference). Both genders fully covered; no proximity or implied intimacy.",
                "level": "allowed_with_framing",
            },
            "mixed_strangers_intimate_context": {
                "rule": "Soft-flagged. Requires brand-level permission. Default refusal: agent reshapes to same-gender or family framing.",
                "level": "soft_flag",
            },
            "single_woman_face_visible": {
                "rule": "Soft-flagged at default; brand can unlock at onboarding with explicit face-visible permission. When permission granted, no hierarchy implications (no woman-served-by-man visual framings).",
                "level": "soft_flag_brand_unlockable",
            },
            "single_man_face_visible": {
                "rule": "Generally allowed across sectors. Cultural framing per sector (e.g., F&B founder shots, retail floor staff).",
                "level": "allowed",
            },
            "cross_gender_physical_contact": {
                "rule": "Hard-blocked outside family-frame. Even in family-frame, depicts as warmth not intimacy.",
                "level": "hard_block_outside_family",
            },
            "shorts_sleeveless_revealing_wardrobe": {
                "rule": "Soft-flagged. Allowed only with brand permission and contextual justification (e.g., fitness sector with same-gender framing).",
                "level": "soft_flag",
            },
        },
        "sector_overrides": {
            "beauty": "Default modesty HIGH. Hands/product preferred; face-visible only with brand permission. Same-gender personal-care contexts.",
            "healthcare_wellness": "Same-gender depiction default for personal-care; mixed allowed in family/general-clinic context.",
            "f_and_b": "Mixed family context allowed; mixed strangers allowed in public dining context with full coverage.",
            "retail": "Both genders shoppable. Mixed allowed in public-retail context.",
            "real_estate": "Family scenes preferred. Mixed allowed in public-architecture context.",
            "fitness": "Same-gender default. Mixed only with explicit brand permission and same-gender preferred for personal/gym content.",
        },
        "regional_notes": {
            "najdi": "Slightly more conservative on mixed-stranger interaction than Hijazi context.",
            "hijazi": "Hijaz culture is slightly more relaxed on mixed-public context; default still respects modesty.",
            "eastern": "Mid-range; follow brand stated posture.",
        },
        "provenance": provenance(
            source_ref="research_corpus/CCO_Environment_v2.docx + Saudi_cultural_norms_2026 + Vision_2030_social_evolution",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# occasion_calendar_index.yaml — Hijri + Gregorian quick lookup (2027 reference year)
# ───────────────────────────────────────────────────────────────────────────
def occasion_calendar_index():
    return {
        "schema_version": 1,
        "title": "Saudi occasion calendar — quick lookup",
        "description": "Cross-reference of recurring occasions with Hijri and Gregorian dates. Reference year 2027 for Hijri-aligned events; verify annually via moon-sighting calendar before each cycle.",
        "reference_year_gregorian": 2027,
        "reference_year_hijri": "1448 — 1449",
        "occasions": [
            {
                "slug": "ramadan",
                "name_en": "Ramadan",
                "name_ar": "رمضان",
                "type": "hijri",
                "hijri_month": 9,
                "hijri_days": "1-30",
                "approx_gregorian_2027": "Feb 18 – Mar 19, 2027",
                "duration_days": 29,
                "lead_days_for_content": 21,
                "occasion_file": "06_saudi_calendar/ramadan.yaml",
            },
            {
                "slug": "eid_al_fitr",
                "name_en": "Eid Al-Fitr",
                "name_ar": "عيد الفطر",
                "type": "hijri",
                "hijri_month": 10,
                "hijri_days": "1-3",
                "approx_gregorian_2027": "Mar 20 – Mar 22, 2027",
                "duration_days": 3,
                "lead_days_for_content": 14,
                "occasion_file": "06_saudi_calendar/eid_al_fitr.yaml",
            },
            {
                "slug": "eid_al_adha",
                "name_en": "Eid Al-Adha",
                "name_ar": "عيد الأضحى",
                "type": "hijri",
                "hijri_month": 12,
                "hijri_days": "10-13",
                "approx_gregorian_2027": "May 26 – May 29, 2027",
                "duration_days": 4,
                "lead_days_for_content": 14,
                "occasion_file": "06_saudi_calendar/eid_al_adha.yaml",
            },
            {
                "slug": "saudi_national_day",
                "name_en": "Saudi National Day",
                "name_ar": "اليوم الوطني السعودي",
                "type": "gregorian",
                "gregorian_month": 9,
                "gregorian_day": 23,
                "approx_gregorian_2027": "Sep 23, 2027",
                "duration_days": 1,
                "lead_days_for_content": 21,
                "occasion_file": "06_saudi_calendar/saudi_national_day.yaml",
            },
            {
                "slug": "saudi_founding_day",
                "name_en": "Saudi Founding Day",
                "name_ar": "يوم التأسيس",
                "type": "gregorian",
                "gregorian_month": 2,
                "gregorian_day": 22,
                "approx_gregorian_2027": "Feb 22, 2027",
                "duration_days": 1,
                "lead_days_for_content": 14,
                "occasion_file": "06_saudi_calendar/saudi_founding_day.yaml",
            },
        ],
        "auto_quiet_periods": {
            "ramadan_iftar_window_AST": "18:00-18:30 (auto-quiet for promo posts, configurable per brand)",
            "ramadan_taraweeh_window_AST": "20:30-22:00 (advisory only; some brands post during this window)",
            "friday_prayer_window_AST": "12:00-13:30 (auto-quiet for promo posts on Fridays)",
        },
        "notes": [
            "Hijri dates derive from official moon-sighting; verify against Saudi Supreme Court announcement each cycle before scheduling.",
            "Gregorian dates for fixed national days are stable: Sep 23 (National), Feb 22 (Founding).",
            "Lead times shown are recommended content-preparation windows, not posting windows.",
        ],
        "provenance": provenance(
            source_ref="internal_research_corpus/Saudi_calendar_synthesis_2027 + occasion_files",
        ),
    }


def write_yaml(data: dict, path: Path, schema_note: str) -> None:
    header = f"# {path.name}\n# {schema_note}\n# Confidence: {data['provenance']['confidence']}\n# Scope: {data['provenance']['scope']}\n\n---\n"
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    path.write_text(header + body)


def main() -> int:
    items = [
        ("compliance_levels.yaml", compliance_levels(), "Short config — no formal schema. Read by CCO agent + compliance gate evaluator."),
        ("saudi_visual_rules.yaml", saudi_visual_rules(), "Short config — read by COO (generation) + CCO (QC)."),
        ("arabic_text_rules.yaml", arabic_text_rules(), "Short config — read by COO + CCO. Arabic-text quality + dialect routing."),
        ("gender_rules.yaml", gender_rules(), "Short config — depiction rules. Defaults conservative, brand-unlockable at onboarding."),
        ("occasion_calendar_index.yaml", occasion_calendar_index(), "Cross-reference index over occasion YAMLs in 06_saudi_calendar/. Used by CEO routing."),
    ]
    for filename, data, note in items:
        path = OUT_DIR / filename
        write_yaml(data, path, note)
        print(f"✓ {path.relative_to(REPO)}")
    print(f"\nWrote {len(items)} Saudi rules to {OUT_DIR.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
