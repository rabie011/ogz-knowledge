# BUILD_PLAN.md — Days 2-5

**Goal:** complete the seed knowledge base in 4 more working days. Each day stands alone — finish it before starting the next.

---

## Day 1 — DONE ✓

- Folder skeleton (16 numbered + 23 TF directories)
- Root files: README, CONVENTIONS, CHANGELOG, .gitignore, CLAUDE.md, BUILD_PLAN.md
- 14 v1 schemas in `12_data_shapes/`
- 88 chain JSONs across TF01-TF23 + INDEX.json
- `scripts/validate.py` and `scripts/generate_chains.py`

---

## Day 2 — Sector + Occasion + Saudi Rules

### Task 2.1 — Sector Baselines (5 files)

**Folder:** `05_sector_defaults/`
**Schema:** `12_data_shapes/sector_baseline_v1.schema.json`
**Format:** YAML (per CONVENTIONS.md §5)

**5 files to produce:**
1. `f_and_b.yaml` — Food & Beverage
2. `retail.yaml` — Retail
3. `beauty.yaml` — Beauty
4. `real_estate.yaml` — Real Estate
5. `healthcare_wellness.yaml` — Healthcare & Wellness

**Per-file content:**
- Inherit the sector_baseline_v1 schema
- `default_voice`: register, formality, dialect, MSA tolerance, codeswitching tolerance
- `default_visual`: primary palette (hex), secondary accents, lighting default, composition, texture
- `default_cinematography`: lens, depth of field, camera height, motion grammar
- `default_cultural_spec`: pre-fill ~70 of 80 cultural fields based on sector typicality (use research corpus + Saudi market knowledge)
- `default_eligible_chains`: scored 0-1 list of which of the 88 chains best suit this sector (read INDEX.json + chain eligibility filters)
- `default_occasions_priority`: which occasions matter most for this sector
- `default_kpis_focus`: footfall, online sales, brand lift, etc.
- `forbidden_topics_sector_specific`: anything off-limits for this sector
- `default_cd_brain_routing_bias`: per-CD-brain weight 0-1

**Source material:**
- `OGz_OpenClaw_Prompt_Requirements.xlsx` — sheet: "Sector Baselines" (if present)
- Research corpus knowledge of Saudi sector patterns
- Existing chains' `eligibility_filters.sectors_allowed` for cross-reference

**Generator strategy:** write `scripts/generate_sector_baselines.py` that produces all 5 YAMLs. Source the data inline in the script (it's only 5 sectors).

**Validation:** each YAML loaded as JSON-equivalent must validate against `sector_baseline_v1.schema.json`. Write a validation helper that handles YAML→JSON conversion before validation.

**Provenance:** `source: "internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#sector_baselines"`, `confirmer: "Mohamed"`, `confidence: "experimental"`, `scope: "sector:<slug>"`

---

### Task 2.2 — Saudi Occasions (5 files)

**Folder:** `06_saudi_calendar/`
**Schema:** `12_data_shapes/occasion_v1.schema.json`
**Format:** YAML

**5 files to produce:**
1. `ramadan.yaml` — Holy month (Hijri, varies)
2. `eid_al_fitr.yaml` — End of Ramadan
3. `eid_al_adha.yaml` — Hajj-aligned
4. `saudi_national_day.yaml` — September 23
5. `saudi_founding_day.yaml` — February 22

**Per-file content:**
- `date_recurrence`: type (hijri/gregorian/hybrid), Hijri month + days OR Gregorian month + day, duration_days
- `cultural_significance`: religious weight, family centrality, hospitality intensity, commercial activity, patriotic weight, heritage weight
- `content_focus_themes`: 5-10 specific themes
- `content_dos`: minimum 5 (e.g., "show iftar gathering with family of multiple generations")
- `content_donts`: minimum 5 (e.g., "do NOT show food during fasting hours")
- `day_specific_variations`: Ramadan has 3 phases (early, middle, last 10 days); Eid has Day 1 vs Days 2-3
- `recommended_chains`: pull from chain INDEX.json (TF16, TF22 V01/V04 for Ramadan, etc.)
- `anti_pattern_warnings`: minimum 3 culturally specific failure modes
- `preparation_lead_days`: 14 for Ramadan, 7 for Eids, 21 for National/Founding

**Source material:**
- `OGz_OpenClaw_Prompt_Requirements.xlsx` — sheet: "Saudi Occasions" (if present)
- Research corpus (mentioned in chains' SAUDI ADAPTATION sections)
- General Saudi cultural knowledge

**Provenance:** same pattern as sectors.

---

### Task 2.3 — Saudi Rules (5 files)

**Folder:** `04_saudi_rules/`
**Format:** YAML

**5 files to produce:**

1. **`compliance_levels.yaml`** — defines the 3 enforcement tiers
   ```yaml
   levels:
     hard_block:
       description: "System refuses to generate; not negotiable"
       examples: ["face-only women branded for traditional brands when face_visibility_permission=false", "left-hand serving food"]
     soft_flag:
       description: "Flagged for human review; can be released with override"
       examples: ["mixed-gender groups in non-family context", "shorts in branded content"]
     advisory:
       description: "Informational note; no enforcement"
       examples: ["palette deviation from sector default", "non-standard typography"]
   ```

2. **`saudi_visual_rules.yaml`** — visual compliance rules (colors that mean things, motifs that don't transplant)

3. **`arabic_text_rules.yaml`** — Arabic text rules: rendering, RTL, ligature handling, dialect markers, no English words in Arabic typography unless brand-locked

4. **`gender_rules.yaml`** — gender compliance rules: same-gender groups OK, mixed family OK, mixed-strangers context-dependent, depiction defaults by sector

5. **`occasion_calendar_index.yaml`** — quick-lookup index of occasions by date (Gregorian + Hijri)

**Generator strategy:** these are short config files. Write `scripts/generate_saudi_rules.py` if needed, or just produce them directly.

---

### Day 2 Acceptance Criteria

- 15 new files (5 sectors + 5 occasions + 5 rules)
- All YAML valid (yamllint passes)
- All sector/occasion YAMLs validate against their schemas
- `scripts/generate_sector_baselines.py` saved
- `scripts/generate_occasions.py` saved
- CHANGELOG.md updated

---

## Day 3 — Agents + CD Brains + Cultural Specs

### Task 3.1 — Agent System Prompts (4 files)

**Folder:** `10_agent_brains/`
**Format:** markdown with YAML front-matter

**4 files to produce:**

1. **`ceo_system_prompt_v1.md`** — based on `/mnt/user-data/uploads/OGzStudios_CEO_Prompt_v1.md`
2. **`coo_system_prompt_v1.md`** — based on `OGzStudios_COO_Prompt_v1.md`
3. **`cco_system_prompt_v1.md`** — based on `OGzStudios_CCO_Prompt_v1.md`
4. **`cd_brain_router_rules.yaml`** — routing logic for which CD brain to apply per brief

**Front-matter for each prompt:**
```yaml
---
agent_role: "CEO" | "COO" | "CCO"
schema_version: 1
prompt_version: 1
model_recommended: "claude-sonnet-4-6"  # or per OGzAI architecture v4
created_at: "2026-05-..."
provenance:
  source: "internal_research_corpus/OGzStudios_CEO_Prompt_v1.md"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---
```

**Body:** the full system prompt as markdown. Don't paraphrase — preserve the original wording where possible. Mark `{PLATFORM_NAME}` placeholders consistently.

**Validation:** ensure each prompt loads cleanly and the front-matter parses as valid YAML.

---

### Task 3.2 — CD Brains (6 files: 5 brains + 1 router)

**Folder:** `20_cd_brains/`
**Schema:** `cd_brain_v1.schema.json` (front-matter)
**Format:** markdown with YAML front-matter

**5 brain files:**
1. `cd_01_firaasa_architect.md` — based on `/mnt/user-data/uploads/cd_01_firaasa_architect.md`
2. `cd_02_metaphor_architect.md` — based on `cd_02_metaphor_architect.md`
3. `cd_03_authenticity_detective.md` — based on `cd_03_authenticity_detective.md`
4. `cd_04_heritage_decoder.md` — based on `cd_04_heritage_decoder.md`
5. `cd_05_paradox_hunter.md` — based on `cd_05_paradox_hunter.md`

**Per-file content:**
- Complete front-matter matching `cd_brain_v1.schema.json` (diagnostic_question, voice_register, signature_technique, best_fits, less_good_fits, sector_affinity, occasion_affinity, sub_branddna_hooks, inversion_test_definition)
- Body: the full methodology in markdown — preserve the source corpus content
- Mark `confidence: experimental` — they're seed v1

6. **`cd_router.md`** — explains the router logic: how a brief gets matched to one or two CD brains, the `cd_routing_weights` derivation, the Two-CD Diagnostic gate.

**Validation:** parse the YAML front-matter of each .md file and validate against `cd_brain_v1.schema.json`.

---

### Task 3.3 — Cultural Specs (13 files)

**Folder:** `15_cultural_specs/`
**Schema:** `cultural_spec_v1.schema.json` (80 fields)
**Format:** YAML

**3 sub-folders to fill:**

**`sector_defaults/` (8 files)** — per-sector cultural defaults with regional variants:
1. `f_and_b_najdi.yaml`
2. `f_and_b_hejazi.yaml`
3. `retail_modern.yaml`
4. `retail_heritage.yaml`
5. `beauty_modern.yaml`
6. `beauty_heritage.yaml`
7. `real_estate_modern_najdi.yaml`
8. `healthcare_modern.yaml`

Each fills the 80-field schema with sector + region appropriate defaults.

**`forbidden_lists/` (4 files)** — universal hard-blocks:
1. `universal_gestures_forbidden.yaml` — left-hand-serving, beckoning-finger-up-palm-up, etc.
2. `universal_props_forbidden.yaml` — pork products, alcohol bottles (unless approved), inappropriate imagery
3. `universal_behaviors_forbidden.yaml` — touching in cross-gender contexts, eating-during-Ramadan-daylight-hours scenes, etc.
4. `universal_visuals_forbidden.yaml` — certain religious symbols out of context, certain political imagery

**`advisor_playbook/` (3 files):**
1. `README.md` — what the Cultural Advisor does
2. `escalation_procedures.md` — when to escalate, to whom, expected SLA
3. `review_checklist.md` — checklist the advisor uses on each major deliverable

**Source material:**
- Research corpus (creative intelligence, campaign archive)
- Saudi market knowledge
- Cross-reference chain `cultural_constraints` to see which gestures/props get used

**Provenance:** each cultural spec gets `confidence: experimental` unless explicitly Cultural Advisor confirmed.

---

### Day 3 Acceptance Criteria

- 4 agent prompt files (3 .md + 1 .yaml)
- 6 CD brain files (5 brains + 1 router)
- 13 cultural spec files (8 sector defaults + 4 forbidden lists + 3 advisor)
- All validate against schemas where applicable
- `20_cd_brains/README.md` added
- `15_cultural_specs/README.md` added
- `10_agent_brains/README.md` added
- CHANGELOG.md updated

---

## Day 4 — Brand Fingerprint + Routing + Benchmarks

### Task 4.1 — Brand Fingerprint (~10 files)

**Folder:** `14_brand_fingerprint/`

**Sub-structures to fill:**

**`layer_2_voice/`** — Voice triangle, 3 love lines, 3 hate lines, dialect, MSA tolerance, emoji density spec.
- `voice_layer_spec.md`
- `voice_examples_per_sector.yaml`

**`layer_3_visual_identity/`** — primary color, secondary, typography, composition, logo behavior, seed range, reference locks.
- `visual_identity_spec.md`
- `color_extension_rules.yaml`

**`layer_4_cinematography/`** — lighting, focal length, depth of field, camera height/angle, motion grammar, signature camera move.
- `cinematography_spec.md`

**`layer_5_look_and_feel/`** — mood lexicon, reference brand anchors, audience emotional state lock.
- `look_and_feel_spec.md`

**`layer_6_production_signature/`** — talent profile, location profile, prop signature, wardrobe palette, signature ritual.
- `production_signature_spec.md`

**`enhanced_onboarding/` (4 files):**
1. `15_question_critical_starter.md` — the Pipeline A intake form (15 questions cover the 10 critical BrandDNA fields)
2. `60_question_full_intake.md` — the Pipeline B intake form
3. `pipeline_a_intake_flow.md` — operational flow: question → field → confidence
4. `pipeline_b_intake_flow.md` — operational flow with strategist involvement

**`distinctiveness_scoring/` (2 files):**
1. `brand_fingerprint_score_spec.md` — math + implementation spec for distinctiveness score (1.0 - avg_cosine_similarity)
2. `anti_convergence_monitor.md` — operational spec for monitoring brand drift toward sector mean

---

### Task 4.2 — Routing (`01_how_to_decide/`)

**6 files:**

1. `intent_to_family.yaml` — maps brief intents (launch, announcement, occasion, etc.) to chain families
2. `sector_to_chains.yaml` — maps sectors to recommended chains (cross-reference with INDEX.json)
3. `occasion_triggers.yaml` — which occasions auto-trigger which chains (e.g., Ramadan auto-fires V01 from TF22)
4. `compliance_gates.yaml` — which gates run for which chain × sector × brand combinations
5. `quality_tier_map.yaml` — what each tier (Starter/Growth/Enterprise) gets access to
6. `conflict_rules.yaml` — when 2 rules contradict, how to resolve

---

### Task 4.3 — Benchmarks (~100 IG accounts + ~300 patterns)

**Folder:** `11_who_to_learn_from/`

**Source:** `/mnt/user-data/uploads/OGz_Saudi_Instagram_Benchmarks.xlsx`

**Files to produce:**

**`accounts/` (~100 files)** — one JSON per account, organized by sector subfolder:
- `accounts/f_and_b/account_001.json` through `account_~40.json`
- `accounts/retail/account_001.json` through `account_~30.json`
- `accounts/beauty/account_001.json` through `account_~30.json`

Each file validates against `benchmark_account_v1.schema.json`. Account handles anonymized using `account_handle_normalized` (e.g., `OGZ-FB-Reference-001`); the actual handle goes in `account_handle_internal` (which won't be exposed in client-facing surfaces).

**`patterns/` (~300 files)** — patterns extracted from the accounts:
- Each validates against `account_pattern_v1.schema.json`
- Group patterns by category: `patterns/visual_compositions/`, `patterns/voice_techniques/`, `patterns/content_types/`, etc.

**Generator strategy:** write `scripts/generate_benchmarks.py` that reads the Excel file, anonymizes account handles, extracts patterns, validates everything, and writes ~400 files in one pass.

**INDEX.json:** at `11_who_to_learn_from/INDEX.json` — full lookup of all accounts + all patterns.

---

### Day 4 Acceptance Criteria

- ~10 brand fingerprint files
- 6 routing YAMLs in `01_how_to_decide/`
- ~100 benchmark account JSONs + INDEX.json
- ~300 pattern JSONs organized into subcategories
- All validates
- Generator scripts saved
- CHANGELOG.md updated

---

## Day 5 — Archive + Org + Database + Wiring

### Task 5.1 — Campaign Archive (38 files)

**Folder:** `21_campaign_archive/`
**Source:** `/mnt/user-data/uploads/ogz_campaign_archive.md`

**Files:**
- `campaigns/` — 38 anonymized JSONs, one per campaign
- `INDEX.json` — lookup by sector, year, CD brain used

Each campaign validates against `campaign_archive_v1.schema.json`. Anonymize client names with codes (`OGZ-CAMPAIGN-001`, etc.).

**Generator:** `scripts/generate_campaign_archive.py`.

---

### Task 5.2 — Org Context (5 files)

**Folder:** `22_org_context/`
**Source:** `/mnt/user-data/uploads/ogz_org_and_kpis.md` + `ogz_bd_pipeline.md`

**5 files:**
1. `org_structure.yaml` — 4-cluster org as described in research (anonymized)
2. `kpi_definitions.yaml` — KPIs OGZ tracks internally
3. `bd_pipeline_status.yaml` — BD pipeline stages, qualification criteria
4. `communication_rules.yaml` — internal comm rituals
5. `operational_rituals.yaml` — Sunday Learning Cycle, weekly reviews, etc.

---

### Task 5.3 — Database Migrations (4 files)

**Folder:** `13_database/migrations/`
**Format:** SQL (Postgres dialect, Supabase-compatible)

**4 files:**

1. **`0001_initial_schema.sql`** — Postgres tables for every schema in `12_data_shapes/`:
   - `chains`, `sector_baselines`, `occasions`, `cd_brains`, `cultural_specs`, `brand_fingerprints`, `campaign_archive`, `benchmark_accounts`, `account_patterns`, `frames`, `motions`
   - Plus runtime tables: `brands`, `briefs`, `generation_events`, `outcome_events`
   - All have ULID primary keys, JSONB columns for nested data, provenance fields, created_at/updated_at
   - Foreign keys where appropriate

2. **`0002_rls_policies.sql`** — Row Level Security:
   - Public schema tables (chains, sector_baselines, occasions, cd_brains, cultural_specs, benchmark_accounts, account_patterns, campaign_archive, frames, motions) → read-only for authenticated users
   - Brand-scoped tables (brand_fingerprints, briefs, generation_events, outcome_events) → RLS by brand_ulid; users can only see their own brand's records

3. **`0003_materialized_views.sql`** — pre-computed views:
   - `brand_eligible_chains_view` — per-brand filtered chain list
   - `brand_distinctiveness_view` — current distinctiveness score per brand
   - `sector_chain_recommendation_view` — sector → top-scored chains

4. **`0004_indexes.sql`** — indexes for:
   - All ULID foreign keys
   - JSONB GIN indexes on commonly-queried fields
   - Vector indexes (pgvector) on embedding columns when introduced
   - Date range indexes on event tables

---

### Task 5.4 — Operations (`09_how_to_run/`) (6 files)

1. `pipeline_a_flow.md` — Pipeline A operational flow (Starter, self-service)
2. `pipeline_b_flow.md` — Pipeline B operational flow (Growth/Enterprise, managed)
3. `decision_authority.yaml` — who decides what (client / strategist / system distributions)
4. `data_consent_policy.md` — PDPL-aligned consent and data handling
5. `data_residency_policy.md` — KSA residency requirements
6. `breach_response.md` — 72-hour PDPL breach notification runbook

---

### Task 5.5 — ADRs (4 files)

**Folder:** `00_start_here/decisions/`

Each ADR follows the standard format: Context, Decision, Consequences, Status.

1. `ADR-0001-files-first.md` — why files-first, not database-first
2. `ADR-0002-ulids.md` — why ULIDs, not UUIDs or serial IDs
3. `ADR-0003-supabase.md` — why Supabase as runtime DB
4. `ADR-0004-fal-primary.md` — why fal.ai as primary model provider

---

### Task 5.6 — Character Library Stub

**Folder:** `16_character_library/`

This folder structure stubs the visual content reference library. The actual visual content (image references) lives in object storage with LFS pointers, not in Git. For Day 5, just produce:

1. `README.md` — explains what this library is, how characters are organized
2. Subfolder structure: `faces/`, `wardrobe/`, `architecture/`, `props/`, `gestures/`, `rituals/` — each with a placeholder `.gitkeep` and a `MANIFEST.md` describing what goes in it

---

### Task 5.7 — `sync_to_supabase.py` Stub

**Folder:** repo root or `scripts/`

A starter Python script that, when run, will:
1. Read every record file in `02_what_to_build/`, `05_sector_defaults/`, `06_saudi_calendar/`, `15_cultural_specs/`, `20_cd_brains/`, `11_who_to_learn_from/`, `21_campaign_archive/`
2. Validate against schemas
3. UPSERT into the Supabase Postgres tables via the corresponding SQL schema
4. Write a manifest of what was synced

For Day 5, ship as a stub with comprehensive comments and a working `--dry-run` mode. The real implementation is Week 2 work in the runtime repo.

---

### Day 5 Acceptance Criteria

- 38 campaign archive JSONs + INDEX.json
- 5 org context YAMLs
- 4 SQL migration files
- 6 operations files
- 4 ADRs in `00_start_here/decisions/`
- Character library stub structure
- `sync_to_supabase.py` stub
- ALL files in the entire repo validate against schemas
- CHANGELOG.md finalized for v1.0.0
- Generate a final manifest: `python3 scripts/repo_manifest.py` produces total file counts per folder
- Tag the commit `v1.0.0-seed-week1`

---

## After Day 5

The repo is **done for v1.0.0 seed.** Next steps (NOT in this 5-day plan):

- Week 2: Runtime repo (`ogz-runtime`) implements the sync, the agents, the fal.ai integration
- Week 3: Brand Studio frontend (`ogz-brand-studio`) implements the client UI
- Months 1-6: Real brands onboard; the seed knowledge evolves through use
- Year 1: Stage 1 → Stage 2 agent transitions

---

## Definition of Repo Done

```bash
# These commands all exit 0:
python3 scripts/validate_all.py             # validates everything in one shot
yamllint -c .yamllint.yaml .                # all YAML clean
git status                                  # no uncommitted changes
git log --oneline | head -20                # clean commit history
git tag                                     # shows v1.0.0-seed-week1
find . -type f -name "*.json" | wc -l       # ~250+ JSON files
find . -type f -name "*.yaml" | wc -l       # ~30+ YAML files
find . -type f -name "*.md" | wc -l         # ~40+ markdown files
```

---

## Closing Note

This plan is detailed because the first week sets the standard. If `ogz-knowledge` ships clean, every downstream system inherits that discipline. If it ships messy, every downstream system inherits the mess.

Take the time. Validate everything. Save your scripts. Update the CHANGELOG.

When in doubt, ask Mohamed.

**Now go.**
