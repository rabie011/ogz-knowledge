# CHANGELOG

All notable changes to `ogz-knowledge` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This repository uses semantic versioning at the **knowledge-base level**:
- **Major** (X.0.0): breaking schema changes; migration required
- **Minor** (1.X.0): new entities, new fields (additive), new chains/sectors/occasions
- **Patch** (1.0.X): content updates, fixes, typo corrections

> **Status note (2026-05-14):** v1.0.0 is staged in 5 day-cuts. Each tag (`v1.0.0-day1` through `v1.0.0-day5`) ships only the work physically complete at that point. Earlier `CHANGELOG.md` revisions listed all 5 days as shipped under v1.0.0 on 2026-05-13 — that was aspirational. This version reflects ground truth.

---

## [Unreleased — Day 3 onward]

### Planned — Day 3 (Agents + CD Brains + Cultural Specs)
- `10_agent_brains/`: 3 system prompts (CEO, COO, CCO) + CD-brain router rules
- `20_cd_brains/`: 5 CD-brain methodologies restructured from research corpus + router
- `15_cultural_specs/`: 8 sector-default cultural specs + 4 forbidden lists + advisor playbook

### Planned — Day 4 (Brand Fingerprint + Routing + Benchmarks)
- `14_brand_fingerprint/`: 6-layer specs + intake forms + distinctiveness scoring
- `01_how_to_decide/`: 6 routing YAMLs
- `11_who_to_learn_from/`: ~100 benchmark accounts + ~300 patterns

### Planned — Day 5 (Archive + Org + Database + Ops)
- `21_campaign_archive/`: 38 anonymized campaign records
- `22_org_context/`: 5 org/KPI/BD/comm/ops YAMLs
- `13_database/migrations/`: 4 SQL files (initial schema, RLS, mat views, indexes)
- `09_how_to_run/`: 6 ops runbooks
- `16_character_library/` stub
- `sync_to_supabase.py` stub

### Planned for v1.1.0 (post-seed)
- Cultural Advisor validation of all sector-default cultural specs
- Expanded forbidden lists with VLM-classifier-ready visual references
- Sub-BrandDNA derivation rules formalized
- Pattern library expansion (target 500 patterns from 100 benchmark accounts)

### Planned for v1.2.0
- 6 craft-role agent prompts (Copywriter, Art Director, Cinematographer, Producer, Editor, Strategist)
- Stage 2 routing logic
- Cross-brand pattern anonymization rules

---

## [v1.0.0-day2] — 2026-05-14 — Sectors + Occasions + Saudi Rules

### Added

**Sector Baselines (`05_sector_defaults/`)** — 5 YAML files, each validates against `sector_baseline_v1.schema.json`:
- `f_and_b.yaml` — Food & Beverage
- `retail.yaml` — Retail
- `beauty.yaml` — Beauty & Personal Care
- `real_estate.yaml` — Real Estate (extrapolated; flagged `confidence: experimental`)
- `healthcare_wellness.yaml` — Healthcare & Wellness (extrapolated; flagged `confidence: experimental`)

**Saudi Occasions (`06_saudi_calendar/`)** — 5 YAML files, each validates against `occasion_v1.schema.json`:
- `ramadan.yaml` — 3-phase variation (first 10 / middle 10 / last 10)
- `eid_al_fitr.yaml` — Day 1 vs Days 2–3 variation
- `eid_al_adha.yaml` — Hajj-aligned
- `saudi_national_day.yaml` — September 23
- `saudi_founding_day.yaml` — February 22

**Saudi Rules (`04_saudi_rules/`)** — 5 short config YAMLs:
- `compliance_levels.yaml` — hard_block / soft_flag / advisory tiers
- `saudi_visual_rules.yaml` — color semantics, motif rules, photography conventions
- `arabic_text_rules.yaml` — RTL, dialect markers, MSA usage rules
- `gender_rules.yaml` — same/mixed-gender depiction rules per sector context
- `occasion_calendar_index.yaml` — Hijri + Gregorian quick lookup

**Generator scripts (`scripts/`)** — saved for reproducibility:
- `generate_sector_baselines.py`
- `generate_occasions.py`
- `generate_saudi_rules.py`
- `validate_all.py` extended with YAML support + new folder→schema mappings

**Fixes**
- `scripts/validate.py` — hardcoded `/home/claude/...` SCHEMA_DIR path replaced with portable `Path(__file__).resolve().parent.parent`
- `CHANGELOG.md` corrected: earlier revisions listed full Days 1–5 content under v1.0.0 shipped 2026-05-13. Only Day 1 actually shipped then. This version reflects ground truth.
- `.gitignore` — `.venv/` excluded (Python project venv)

### Notes

- All Day 2 content marked `confidence: experimental`. Real Estate and Healthcare/Wellness sector baselines are extrapolated from research corpus (source xlsx covered F&B/Retail/Beauty only) — these need Cultural Advisor validation before any production use.
- Saudi Rules YAMLs are short config files without dedicated schemas; they are read directly by agents and the compliance gate evaluator.

---

## [v1.0.0-day1] — 2026-05-13 — Foundation + Schemas + 88 Chains

### Added

**Foundation**
- `README.md` describing the repo's purpose and navigation
- `CONVENTIONS.md` defining 12 universal rules
- `.gitignore`
- `00_start_here/AGENT_MANIFEST.md`
- 4 initial ADRs in `00_start_here/decisions/`:
  - `ADR-0001-files-first.md`
  - `ADR-0002-ulids.md`
  - `ADR-0003-supabase.md`
  - `ADR-0004-fal-primary.md`

**Schemas (`12_data_shapes/`)** — 14 v1 schemas
- `provenance_mixin_v1.schema.json` (5-field universal mixin)
- `chain_v1.schema.json`
- `frame_v1.schema.json`
- `motion_v1.schema.json`
- `sector_baseline_v1.schema.json`
- `occasion_v1.schema.json`
- `cultural_spec_v1.schema.json` (80 fields)
- `brand_fingerprint_v1.schema.json`
- `cd_brain_v1.schema.json`
- `campaign_archive_v1.schema.json`
- `benchmark_account_v1.schema.json`
- `generation_event_v1.schema.json`
- `outcome_event_v1.schema.json`
- `account_pattern_v1.schema.json`

**Chains (`02_what_to_build/`)** — 88 chain JSON files across 23 families (TF01–TF23) + per-family `.negative_prompt.txt` sidecars + `INDEX.json`

**Scripts (`scripts/`)**
- `validate.py` — single-file JSON schema validator with cross-file $ref support
- `validate_all.py` — repo-wide validation runner
- `generate_chains.py` — chain library generator (reference pattern for future generators)
- `repo_manifest.py` — file inventory tool

### Notes

All v1.0.0 content is marked `confidence: experimental` until validated through production use. The seed knowledge base is research-derived and structured; real brand operation will refine it over Months 1–6.

---
