#!/usr/bin/env python3
"""
generate_schema_gap_report.py
Formal gap report: what data dimensions are MISSING from the current
observation schema that would unlock agency-grade creative intelligence.
Categorised by: field gaps / structural gaps / strategic gaps.
Each gap has: business_rationale, agency_impact, collection_method, priority.
Output: logs/schema_gap_report.json + printed summary
"""
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
LOGS = BASE / "logs"

# ── Gap definitions ────────────────────────────────────────────────────────────

FIELD_GAPS = [
    # Fields in schema but never analyzed — now being closed
    {
        "field": "characters_visible",
        "status": "in_schema_just_mined",
        "coverage_pct": 91,
        "agency_value": "Casting direction — human presence, gender, traditional dress vs casual",
        "analytics_built": "human_element_analysis.json",
    },
    {
        "field": "color_palette_dominant",
        "status": "in_schema_just_mined",
        "coverage_pct": 100,
        "agency_value": "Art direction color guidance — warm heritage vs cool modern palettes",
        "analytics_built": "color_palette_analysis.json",
    },
    {
        "field": "text_overlays",
        "status": "in_schema_just_mined",
        "coverage_pct": 84,
        "agency_value": "Post-production text strategy — Arabic vs English overlay, content type",
        "analytics_built": "text_overlay_analysis.json",
    },
    {
        "field": "regional_orientation_detected",
        "status": "in_schema_low_coverage",
        "coverage_pct": 90,
        "agency_value": "Geo-targeting strategy — Riyadh vs Jeddah vs general Saudi",
        "analytics_built": None,
        "next_step": "Build regional_signals.py",
    },
    {
        "field": "cultural_notes.free_notes",
        "status": "in_schema_unstructured",
        "coverage_pct": 77,
        "agency_value": "Analyst qualitative insights — rich context for creative rationale",
        "analytics_built": None,
        "next_step": "Mine for recurring themes using keyword extraction",
    },
]

STRUCTURAL_GAPS = [
    {
        "gap": "caption_text",
        "description": "Actual Arabic and English caption copy is not captured in any field",
        "agency_impact": "CRITICAL — cannot analyze: Arabic copywriting formulas that work, "
                         "caption length vs engagement, emoji usage, hashtag strategy, "
                         "question vs statement opens, branded phrase patterns",
        "what_unlocks": [
            "Which Arabic sentence structures drive highest engagement",
            "Optimal caption length (short punchy vs long story)",
            "Hashtag count and type (branded vs trending vs category)",
            "Emoji frequency and positioning",
            "Question-open captions vs statement-open captions",
            "Brand voice consistency scoring (NLP-based)",
        ],
        "collection_method": "Add caption_text field to observation_v1 schema. "
                             "Extract from Instagram API or manual copy-paste during observation.",
        "priority": "P0 — highest impact gap",
        "estimated_extraction_effort": "10-15 min per account re-extraction pass",
    },
    {
        "gap": "video_duration_seconds",
        "description": "For 159 video observations, no duration data exists",
        "agency_impact": "HIGH — cannot answer: is 15s better than 60s? Is Reels length optimal?",
        "what_unlocks": [
            "Optimal video length per sector (F&B vs Beauty)",
            "Optimal video length per occasion",
            "Short-form (≤15s) vs mid-form (15-60s) vs long-form (60s+) engagement",
            "Reels vs IGTV performance comparison",
        ],
        "collection_method": "Add video_duration_seconds to content_ref. "
                             "Extract from Instagram API metadata or manual file inspection.",
        "priority": "P1 — high impact for video production decisions",
        "estimated_extraction_effort": "Can be batch-extracted from Instagram API for all video obs",
    },
    {
        "gap": "has_voiceover_or_music",
        "description": "Audio strategy for video content not captured",
        "agency_impact": "HIGH — no ability to advise on sound design for videos",
        "what_unlocks": [
            "Voiceover (Arabic vs English vs none) vs engagement",
            "Music (trending sound vs original vs silence) vs engagement",
            "ASMR/sensory sound in food content",
            "Subtitles present vs absent",
        ],
        "collection_method": "Add audio_strategy field: {has_voiceover, voiceover_language, "
                             "music_type, has_subtitles} to visual_observations for video obs only.",
        "priority": "P1 — critical for video content direction",
        "estimated_extraction_effort": "Manual review of video obs (~159 records)",
    },
    {
        "gap": "actual_engagement_metrics",
        "description": "No real engagement numbers — only analyst estimate of engagement_potential",
        "agency_impact": "CRITICAL — all engagement rates are analyst-estimated, not measured. "
                         "Cannot do: ROI analysis, benchmark against industry averages, "
                         "save/share/comment ratio, reach vs impressions",
        "what_unlocks": [
            "True engagement rate (likes+comments+saves / reach)",
            "Save rate (best proxy for content value)",
            "Share rate (virality signal)",
            "Comment sentiment analysis",
            "Reach vs followers (organic amplification)",
            "Story completion rate for video content",
        ],
        "collection_method": "Instagram Graph API (requires business account access from client). "
                             "Add engagement_metrics: {likes, comments, saves, shares, reach, impressions} "
                             "to quality_assessment or new analytics section.",
        "priority": "P0 — transforms all engagement analysis from estimated to measured",
        "estimated_extraction_effort": "Requires Instagram API credentials from each account owner",
    },
    {
        "gap": "hashtag_strategy",
        "description": "No hashtag count, types, or strategy captured",
        "agency_impact": "MEDIUM — hashtags affect discoverability, not directly engagement",
        "what_unlocks": [
            "Branded hashtag vs trending hashtag usage",
            "Optimal hashtag count (0 vs 5 vs 30)",
            "Arabic vs English hashtags",
            "Location-based hashtag strategy",
        ],
        "collection_method": "Add hashtag_data: {count, has_branded, has_location, "
                             "language} to voice_observations. Extract from caption text.",
        "priority": "P2 — medium impact, needs caption_text first",
        "estimated_extraction_effort": "Derived from caption_text once captured",
    },
    {
        "gap": "aspect_ratio",
        "description": "Whether content is square (1:1), portrait (4:5 or 9:16), or landscape (16:9)",
        "agency_impact": "MEDIUM — affects how the creative is produced and experienced",
        "what_unlocks": [
            "Feed post vs Reels vs Stories performance comparison",
            "Vertical video vs square vs landscape engagement",
            "Mobile-first vs desktop framing decisions",
        ],
        "collection_method": "Add aspect_ratio to content_ref. Detectable from file metadata.",
        "priority": "P2 — medium impact",
        "estimated_extraction_effort": "Automated from image/video file metadata",
    },
    {
        "gap": "color_grade_temperature",
        "description": "Post-production color grading style not captured (warm orange/teal grade vs natural vs desaturated)",
        "agency_impact": "MEDIUM — color grade is a significant visual identity signal",
        "what_unlocks": [
            "Warm grade vs cool grade vs natural vs moody",
            "Color grading consistency per brand",
            "Grade preference per occasion (Ramadan = warm? National Day = cool?)",
        ],
        "collection_method": "Add color_grade to visual_observations: "
                             "{warm/cool/natural/moody/high_contrast/desaturated}",
        "priority": "P2 — visual identity enhancement",
        "estimated_extraction_effort": "Manual observation during extraction (~2 min per obs)",
    },
    {
        "gap": "product_to_context_ratio",
        "description": "What fraction of the frame is the hero product vs environment/props",
        "agency_impact": "MEDIUM — product prominence vs lifestyle context is a key creative decision",
        "what_unlocks": [
            "100% product vs 50/50 product+context vs context-led content",
            "When to let the food/product be the hero vs embed it in lifestyle",
            "Macro/extreme closeup vs environmental shot performance",
        ],
        "collection_method": "Add product_frame_ratio to visual_observations: "
                             "{product_dominant/balanced/context_dominant}",
        "priority": "P2",
        "estimated_extraction_effort": "Quick visual judgement during extraction",
    },
    {
        "gap": "budget_tier",
        "description": "Production budget level not captured (studio shoot vs iPhone, hero production vs UGC)",
        "agency_impact": "HIGH — critical for ROI analysis: does premium production pay off?",
        "what_unlocks": [
            "High production vs lo-fi content engagement comparison",
            "When authenticity beats polish",
            "Budget allocation advice for clients",
        ],
        "collection_method": "Add production_tier: {studio_hero/semi_professional/ugc_style/graphic_only} "
                             "— extends existing production_quality field.",
        "priority": "P1 — directly impacts agency pricing and client recommendations",
        "estimated_extraction_effort": "Can be inferred from existing production_quality field (already captured)",
    },
    {
        "gap": "posting_time_and_day",
        "description": "Time-of-day and day-of-week not captured (capture_date is date only, no time)",
        "agency_impact": "HIGH — posting timing significantly affects organic reach",
        "what_unlocks": [
            "Best time of day per sector (F&B = lunchtime/iftar?)",
            "Best day of week (Thu/Fri for Saudi social media?)",
            "Ramadan timing (post-iftar spike)",
            "Content calendar optimization",
        ],
        "collection_method": "Extend capture_date to full ISO timestamp. "
                             "Extract from Instagram API post metadata.",
        "priority": "P1 — high impact for scheduling strategy",
        "estimated_extraction_effort": "Requires Instagram API access for timestamp data",
    },
]

SECTOR_GAPS = [
    {
        "gap": "retail_sector_underrepresentation",
        "description": "Only 25 obs from Retail (5.3% of corpus) — too thin for reliable insights",
        "agency_impact": "CRITICAL for Retail clients — all retail-sector analytics are unreliable",
        "what_unlocks": [
            "Reliable retail-specific engagement patterns",
            "Retail × occasion matrix with statistical confidence",
            "Retail brand archetype differentiation",
        ],
        "collection_method": "Extract 3-5 additional Saudi retail accounts: "
                             "@alsaif.gallery, @nakheel_mall_riyadh, @jarir, @extra.ksa",
        "target": "100+ retail obs (from 25)",
        "priority": "P0 — block for retail client engagements",
    },
    {
        "gap": "beauty_sector_underrepresentation",
        "description": "Only 50 obs from Beauty (10.5%) — better than retail but still thin",
        "agency_impact": "HIGH — beauty-specific insights unreliable below n=100",
        "collection_method": "Extract 2-3 more Saudi beauty accounts: @elyazya.ksa, @eyhhsa, @nora.alqahtani",
        "target": "120+ beauty obs (from 50)",
        "priority": "P1",
    },
    {
        "gap": "tiktok_platform_gap",
        "description": "All 474 obs are Instagram — zero TikTok intelligence",
        "agency_impact": "HIGH — TikTok is increasingly dominant for F&B and beauty in Saudi",
        "what_unlocks": [
            "TikTok vs Instagram content strategy comparison",
            "Vertical video performance benchmarks",
            "Sound-on vs sound-off engagement in Saudi market",
            "Gen-Z vs Millennial content preference signals",
        ],
        "collection_method": "Add TikTok observation track to extraction pipeline. "
                             "New schema field: platform (already exists, add TikTok obs).",
        "priority": "P1 — missing an entire platform",
    },
]

STRATEGIC_GAPS = [
    {
        "gap": "competitive_share_of_voice",
        "description": "No data on posting frequency, reach, or follower size per account",
        "agency_impact": "Cannot benchmark: who owns what % of content mindshare",
        "collection_method": "Scrape follower count + posting frequency per account monthly",
        "priority": "P2",
    },
    {
        "gap": "ab_testing_framework",
        "description": "No controlled experiments — all insights are correlational, not causal",
        "agency_impact": "Cannot prove causality: 'carousels get more engagement' may be confounded",
        "collection_method": "Design A/B content experiments with real clients",
        "priority": "P2 — requires client partnerships",
    },
    {
        "gap": "audience_demographic_data",
        "description": "No data on who consumes this content (age, gender, location of audience)",
        "agency_impact": "Cannot do audience-content fit analysis",
        "collection_method": "Instagram Insights API (requires account owner access)",
        "priority": "P1 — fundamental for media planning",
    },
    {
        "gap": "trending_sound_usage",
        "description": "Trending audio on Instagram/TikTok not tracked",
        "agency_impact": "Missing a key viral lever — trending sounds amplify organic reach",
        "collection_method": "Add audio_strategy field to video obs",
        "priority": "P2",
    },
]


def main():
    # Count totals
    p0_count = sum(1 for g in STRUCTURAL_GAPS if g.get("priority","").startswith("P0"))
    p0_count += sum(1 for g in SECTOR_GAPS if g.get("priority","").startswith("P0"))

    now_closed = [f for f in FIELD_GAPS if f.get("status","").startswith("in_schema_just_mined")]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "summary": {
            "fields_just_mined_this_session": len(now_closed),
            "structural_gaps_identified": len(STRUCTURAL_GAPS),
            "sector_gaps_identified": len(SECTOR_GAPS),
            "strategic_gaps_identified": len(STRATEGIC_GAPS),
            "p0_gaps": p0_count,
            "highest_impact_next_action": "Add caption_text field + extract for all 474 obs — unlocks entire copywriting intelligence layer",
            "second_highest_impact": "Connect Instagram Graph API for real engagement metrics — converts all analysis from estimated to measured",
        },
        "field_gaps": FIELD_GAPS,
        "structural_gaps": STRUCTURAL_GAPS,
        "sector_gaps": SECTOR_GAPS,
        "strategic_gaps": STRATEGIC_GAPS,
        "recommended_phase_4": {
            "title": "Phase 4 — Data Enrichment & Schema Expansion",
            "steps": [
                "P0: Add caption_text to schema — manual re-extraction for all 474 obs (1-2 day effort)",
                "P0: Expand Retail to 100+ obs — extract @alsaif.gallery + @jarir + 2 more",
                "P1: Connect Instagram API for real metrics — requires account owner cooperation",
                "P1: Add video_duration + audio_strategy to schema for 159 video obs",
                "P1: Expand Beauty to 120+ obs — extract 2-3 more accounts",
                "P1: Add TikTok observation track — parallel schema, same extraction method",
                "P2: Add aspect_ratio + color_grade to visual_observations",
                "P2: Add hashtag_data to voice_observations (derivable from caption_text)",
            ],
        },
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "schema_gap_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print("=" * 70)
    print("  OGZ KNOWLEDGE BASE — SCHEMA GAP REPORT")
    print("=" * 70)

    print(f"\n  ✅ FIELDS JUST MINED THIS SESSION ({len(now_closed)} fields):")
    for f in now_closed:
        print(f"     {f['field']:<40} → {f['analytics_built']}")

    print(f"\n  🔴 STRUCTURAL GAPS — data we don't capture at all ({len(STRUCTURAL_GAPS)} gaps):")
    print(f"  {'Gap':<34} {'Priority':<6}  Agency Impact")
    print("  " + "─" * 80)
    for g in sorted(STRUCTURAL_GAPS, key=lambda x: x.get("priority","P9")):
        impact_short = g["agency_impact"][:55]
        print(f"  {g['gap']:<34} {g.get('priority','?'):<6}  {impact_short}")

    print(f"\n  🟠 SECTOR GAPS — corpus too thin to trust ({len(SECTOR_GAPS)} gaps):")
    for g in SECTOR_GAPS:
        print(f"  {g['gap']:<40} {g.get('priority','?')}  → {g.get('target','?')}")

    print(f"\n  🟡 STRATEGIC GAPS — require new methodology ({len(STRATEGIC_GAPS)} gaps):")
    for g in STRATEGIC_GAPS:
        print(f"  {g['gap']:<40} {g.get('priority','?')}")

    print(f"\n  ★ HIGHEST VALUE NEXT ACTIONS:")
    print(f"  1. [P0] Add 'caption_text' to schema — unlocks entire copy intelligence layer")
    print(f"  2. [P0] Expand Retail to 100+ obs — @alsaif.gallery + @jarir + 2 more")
    print(f"  3. [P1] Instagram API for real metrics — convert estimated → measured engagement")
    print(f"  4. [P1] Add video_duration + audio_strategy for 159 video obs")
    print(f"  5. [P1] Add TikTok observation track — parallel to Instagram")

    print(f"\nOutput: logs/schema_gap_report.json")


if __name__ == "__main__":
    main()
