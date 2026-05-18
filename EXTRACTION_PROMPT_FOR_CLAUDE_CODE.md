# Extraction Prompt for Claude Code

Read `CLAUDE.md` before starting. This document tells you how to extract observations from content.

## Input

You receive content items (images, video screenshots) from either:
- `11_who_to_learn_from/_calibration_set/content/` (calibration mode)
- `11_who_to_learn_from/_inbox/@handle/` (real extraction mode)

For each item, produce one observation record conforming to `12_data_shapes/observation_v1.schema.json`.

## Before you start

1. Read `12_data_shapes/observation_v1.schema.json` — this is your output format
2. Read all 4 forbidden lists in `15_cultural_specs/forbidden_lists/`:
   - `universal_gestures_forbidden.yaml`
   - `universal_props_forbidden.yaml`
   - `universal_behaviors_forbidden.yaml`
   - `universal_visuals_forbidden.yaml`
3. Read the pattern library index at `11_who_to_learn_from/patterns/`
4. Read the picks file for the sector you are extracting from `source_library/my_picks/`

## Extraction steps (per content item)

### a. Generate IDs
- Generate a ULID for `observation_ulid`
- Look up the parent account in `my_picks/` or `accounts/` to get `account_ulid` and `account_handle_normalized`
- Set `sector` from the picks file

### b. Content reference
- Set `content_ref.filename` to the source filename
- Set `platform` and `content_type` from the picks file or from what you observe

### c. Visual observations
Look at the content and record:
- `composition_style` — describe the composition (e.g. "overhead tabletop spread", "close-up macro texture")
- `lighting` — natural, studio, golden hour, flat, etc.
- `color_palette_dominant` — the 2-4 dominant colors
- `props_visible` — list every prop you can identify
- `setting` — where the content was shot
- `characters_visible` — count, gender presentation, wardrobe, gestures
- `text_overlays` — any text visible in the content, with language
- `notable_visual_elements` — anything else worth noting

### d. Voice observations
If there is a caption, text overlay, or audio transcript:
- `language` — arabic, english, bilingual, or none
- `dialect_detected` — Najdi, Hejazi, MSA, Gulf, or null if unclear
- `register` — formal, casual, poetic, etc.
- `tone` — warm, authoritative, playful, etc.
- `notable_phrases` — short distinctive phrases (not full quotes)
- `call_to_action_present` — true/false

### e. Compliance check — HIGHEST PRIORITY

This is the most important step. Cross-reference the content against EVERY entry in ALL 4 forbidden lists.

For each forbidden list entry:
1. Read the `name`, `description`, and `detection_hints`
2. Check if the content violates this entry
3. If **confident** it violates: add to `hard_blocks_triggered` with the entry's `id`, `name`, `severity`, and a description of what you observed
4. If **uncertain** but suspicious: add to `soft_flags` with a description

Set `overall_compliance`:
- `"clean"` — no hard blocks, no soft flags
- `"soft_flagged"` — no hard blocks, but one or more soft flags
- `"hard_blocked"` — one or more hard blocks triggered

**Never skip this step. Never rush it. Check every forbidden list entry.**

### f. Cultural notes
- `regional_orientation_detected` — Najdi, Hejazi, Eastern, general Saudi, or null
- `occasion_relevance` — Ramadan, Eid, National Day, etc., or null
- `hospitality_cues` — any hospitality signals (qahwa, dates, incense, etc.)
- `heritage_vs_modern` — heritage, modern, blended, or neutral
- `free_notes` — anything culturally notable not captured above

### g. Pattern matches
Check the content against the 40 patterns in `11_who_to_learn_from/patterns/`. For each match:
- `pattern_slug` — the pattern filename without extension
- `confidence` — strong, moderate, or weak
- `notes` — why you think it matches (or null)

### h. Quality assessment
- `production_quality` — professional, semi_professional, ugc, or low
- `brand_consistency_with_account` — strong, moderate, or weak (compared to the account's other content)
- `engagement_potential` — high, medium, or low

### i. Provenance
- `source`: `"benchmark:@{handle}; content:{filename}"`
- `date_added`: current UTC timestamp (ISO 8601)
- `confirmer`: `"claude_code_extraction"`
- `confidence`: `"inferred"`
- `scope`: `"sector:{sector_slug}"`

## Output

Save each observation as a JSON file:
- Filename: `{observation_ulid}.json`
- Pretty-printed, 2-space indent, UTF-8
- Calibration mode: save to `_calibration_set/claude_extractions/`
- Real extraction mode: save to `observations/{sector}/`

## The item_02 rule

If you are processing a calibration set and item_02 does NOT trigger `hard_blocks_triggered` containing an entry with `entry_name: "left_hand_serving"`:

**STOP IMMEDIATELY.**

Tell Mohamed. Do not continue extraction. The pipeline is unreliable until this is fixed.

## After extraction

Run validation:
```bash
python3 scripts/validate_all.py
```

Print a summary: how many items extracted, how many hard blocks found, how many patterns matched.
