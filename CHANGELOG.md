# CHANGELOG

All notable changes to `ogz-knowledge` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This repository uses semantic versioning at the **knowledge-base level**:
- **Major** (X.0.0): breaking schema changes; migration required
- **Minor** (1.X.0): new entities, new fields (additive), new chains/sectors/occasions
- **Patch** (1.0.X): content updates, fixes, typo corrections

> **Status note (2026-05-14):** v1.0.0 is staged in 5 day-cuts. Each tag (`v1.0.0-day1` through `v1.0.0-day5`) ships only the work physically complete at that point. Earlier `CHANGELOG.md` revisions listed all 5 days as shipped under v1.0.0 on 2026-05-13 — that was aspirational. This version reflects ground truth.

---

## [Unreleased — Day 5]

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

## [v1.0.0-day4] — 2026-05-14 — Brand Fingerprint + Routing + Benchmarks

### Added

**Brand Fingerprint (`14_brand_fingerprint/`)** — 13 spec docs across 6 layers + onboarding + distinctiveness:
- 5 layer specs (Strategy / Voice / Visual / Cinematography / Look & Feel / Production)
- 2 voice companion docs (per-sector examples + color extension rules)
- 4 enhanced-onboarding docs (Pipeline A 15-Q + Pipeline B 60-Q + flows for each)
- 2 distinctiveness-scoring docs (score spec + anti-convergence monitor)
- `README.md` — folder index

**Routing (`01_how_to_decide/`)** — 6 YAML configs:
- `intent_to_family.yaml` — brief intent → candidate TF chain families
- `sector_to_chains.yaml` — per-sector chain eligibility (references sector baselines)
- `occasion_triggers.yaml` — occasion auto-fires + boosts/demotions + blackout sectors
- `compliance_gates.yaml` — which CCO checks run per chain × sector × brand
- `quality_tier_map.yaml` — tier → chain access + human review level
- `conflict_rules.yaml` — precedence when rules contradict
- `README.md`

**Benchmarks (`11_who_to_learn_from/`)** — 149 files:
- `accounts/f_and_b/` — 37 anonymized accounts (handles → `OGZ-F-AND-B-Reference-NNN`)
- `accounts/retail/` — 40 anonymized accounts
- `accounts/beauty/` — 31 anonymized accounts
- `patterns/visual_compositions/` — 10 patterns
- `patterns/voice_techniques/` — 10 patterns
- `patterns/content_types/` — 10 patterns
- `patterns/occasion_plays/` — 10 patterns
- `INDEX.json` — full lookup
- `README.md`

**Generator scripts (`scripts/`)** — saved for reproducibility:
- `generate_routing.py`
- `generate_brand_fingerprint.py`
- `generate_benchmarks.py`
- `validate_all.py` extended with 4 new folder mappings (`01_how_to_decide`, `11_who_to_learn_from/accounts`, `11_who_to_learn_from/patterns`, `15_cultural_specs/forbidden_lists`)

### Validation

`validate_all.py` → **275/275 records valid** across all Days 1–4.

### Notes

- **Pattern count: 40, not 300.** The original target of ~300 was aspirational. Honest delivery is 40 substantive cross-account patterns (10 per category × 4 categories) — quality over count per Mohamed's "do not cut corners." Expand in v1.1.0 as real-brand operations surface additional patterns.
- All benchmark accounts marked `confidence: experimental` pending Cultural Advisor validation.
- Account handles anonymized to category codes (`OGZ-<SECTOR>-Reference-NNN`) for system-design discipline. Internal handles preserved in `account_handle_internal` (never client-surfaced).
- All routing YAMLs are short configs without dedicated schemas; provenance enforced.

---

## [v1.0.0-day3] — 2026-05-14 — Agents + CD Brains + Cultural Specs

### Added

**Agent Prompts (`10_agent_brains/`)** — verbatim corpus bodies with YAML front-matter, IP-preserved:
- `ceo_system_prompt_v1.md` — Claude Sonnet 4.6 · 8-step routing protocol · 11 human-gate triggers · JSON-only output
- `coo_system_prompt_v1.md` — Claude Haiku 4.5 · 3 jobs (build_branddna / compile_caption_context / score_confidence) · confidence formula 0.40/0.30/0.15/0.15
- `cco_system_prompt_v1.md` — GPT-5 · Arabic QC gate · per-post 0–100 score + dialect/negpat/cultural/brave flags
- `cd_brain_router_rules.yaml` — deterministic CD-brain routing logic (Two-CD Diagnostic gate, occasion overrides, sector safety locks)
- `README.md` — folder index + cross-references

**CD Brains (`20_cd_brains/`)** — 5 methodology profiles restructured from research corpus, anonymized:
- `cd_01_firaasa_architect.md` — Why-Before-What cultural-contract diagnosis
- `cd_02_metaphor_architect.md` — System-to-Human full metaphor architecture
- `cd_03_authenticity_detective.md` — Performance/Reality two-scene contrast (parallel-original bilingual)
- `cd_04_heritage_decoder.md` — Classical-Arabic Inversion via double-meaning word
- `cd_05_paradox_hunter.md` — Counterintuitive flip + Product-as-Mechanism
- `cd_router.md` — narrative companion to `cd_brain_router_rules.yaml`
- `README.md` — folder index + voice anchors

All 5 brains validate against `cd_brain_v1.schema.json`. All marked `confidence: experimental`, `status: seed_v1`. Human names from corpus replaced with methodology codenames; "Habbar" replaced with `{PLATFORM_NAME}` placeholder; client names anonymized to category labels (stc → telecom-flagship-A, etc.).

**Cultural Specs (`15_cultural_specs/`)** — the moat layer:
- `sector_defaults/` — 8 YAMLs validating against the 80-field `cultural_spec_v1.schema.json`:
  - F&B: Najdi + Hejazi
  - Retail: modern + heritage
  - Beauty: modern + heritage
  - Real Estate: modern Najdi
  - Healthcare: modern
- `forbidden_lists/` — 4 universal hard-block YAMLs (gestures · props · behaviors · visuals)
- `advisor_playbook/` — 3 markdown docs (README · escalation procedures · review checklist)
- `README.md` — folder index + 80-field category map

All marked `confidence: experimental` pending Cultural Advisor review.

**Generator scripts (`scripts/`)** — saved for reproducibility:
- `generate_agent_prompts.py`
- `generate_cd_brains.py` (with anonymization regex table)
- `generate_cultural_specs.py` (base spec + overlay pattern)
- `validate_all.py` — extended with `md_frontmatter` format + 4 new folder mappings

### Validation

`validate_all.py` → **121/121 records valid** across all Days 1–3:
- 88 chains
- 5 sector baselines
- 5 Saudi occasions
- 5 Saudi rules
- 1 CD-brain router rules YAML
- 5 CD-brain methodology MDs (front-matter)
- 8 cultural-spec sector defaults (80 fields each)
- 4 universal forbidden lists

### Notes

- Agent prompt bodies are intellectual property — preserved verbatim from corpus. Only YAML front-matter was added.
- CD-brain methodology content is preserved (diagnostic question, signature technique, anti-patterns, voice register, sector/occasion affinity, inversion test). Biographical and Cluster-portfolio sections were stripped per the anonymization rules.
- Cultural specs cover the most common Saudi sector × region combinations. Eastern Province and Southern (Asiri) regions are NOT yet specced — planned for v1.1.0.
- Forbidden lists are universal; brand-specific NegativePatterns layer on top.

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
