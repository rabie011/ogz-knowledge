# CLAUDE.md — Briefing Pack for Claude Code

**Read this first. Then read `BUILD_PLAN.md`. Then start work.**

## Verification Rule — MANDATORY
Before claiming ANY data quality work is done, run:
```
python3 scripts/verify_ship_ready.py
```
Exit code must be 0. If any check fails, fix it before committing.
This script checks field completeness thresholds, ghost accounts, pattern integrity, chain coverage, embeddings, and DB schema. Do NOT mark work complete based on what you think you did — verify with the script.

This file tells you everything you need to know to continue building `ogz-knowledge` on Mohamed's machine. The repo skeleton, schemas, and the 88 chain library are already built. You'll execute Days 2-5 of the build plan.

---

## What You're Building

`ogz-knowledge` — the **system-agnostic, file-first knowledge base** for `{PLATFORM_NAME}`, a Saudi creative intelligence platform built by OGZ Studios LLC, Riyadh.

The platform is **fal.ai-powered**, **Arabic-first**, and **Saudi-native**. It serves two pipelines:
- **Pipeline A (Starter):** self-service automated content for Saudi SMEs
- **Pipeline B (Growth/Enterprise):** AI-C-Suite managed services for larger brands

This repo is **the knowledge that powers both pipelines.** It's NOT the runtime, NOT the brand-specific data, NOT the client UI. It's the seed knowledge that gets synced to the runtime Postgres database, read by all agents, and evolved through use.

---

## The Owner

- **Mohamed** — system architect; the person who will direct you
- **Alhareth** — CEO, OGZ Studios
- Communication: Mohamed writes in brief English, sometimes with typos. Read carefully. When uncertain, ask one tight question and proceed with stated assumption.

---

## The Locked Decisions (Do Not Re-litigate)

These were decided across multiple deep-strategy sessions before you got the keys. Take them as ground truth:

1. **Repo name:** `ogz-knowledge`
2. **Platform name:** `{PLATFORM_NAME}` placeholder throughout. Will be find-replaced when Mohamed picks a name (likely Amira or Firaasa).
3. **Source of truth:** files in this Git repo + object storage. Postgres is an index OVER files, never the other way around.
4. **IDs:** ULIDs (26-char Crockford base32). Deterministic where possible.
5. **Provenance:** every record carries 5 fields — source, date_added, confirmer, confidence, scope.
6. **Append-only event logs.** No updates. Corrections happen as new events.
7. **Quarantine, not delete.** 90-day soft retention.
8. **One write path:** the Memory Controller (in the separate runtime repo). This repo is edited only via PR.
9. **Brand isolation:** Row-Level Security in DB + filesystem scoping in object storage.
10. **The 5 CD brain methodologies from the research corpus** are seed brains. Marked `status: seed_v1`, `confidence: experimental`. They evolve through use, not invention.
11. **Cultural authenticity is the moat.** The 80-field Cultural Spec + Saudi forbidden lists are non-negotiable.
12. **Honest staged maturity:** Stage 0 deterministic → Stage 1 shadow → Stage 2 selective → Stage 3 managed.

If you find yourself debating any of these, stop. Ask Mohamed. Don't redesign.

---

## What's Already Built (Day 1, Already Shipped)

```
ogz-knowledge/
├── README.md                        ← navigation
├── CONVENTIONS.md                   ← 12 universal rules
├── CHANGELOG.md                     ← versioning
├── .gitignore
├── scripts/
│   ├── validate.py                  ← schema validator (USE THIS)
│   └── generate_chains.py           ← the chain generator (reference)
├── 12_data_shapes/                  ← 14 v1 schemas, all validated
│   ├── provenance_mixin_v1.schema.json
│   ├── chain_v1.schema.json
│   ├── sector_baseline_v1.schema.json
│   ├── occasion_v1.schema.json
│   ├── cd_brain_v1.schema.json
│   ├── cultural_spec_v1.schema.json  ← 80 fields
│   ├── brand_fingerprint_v1.schema.json
│   ├── campaign_archive_v1.schema.json
│   ├── benchmark_account_v1.schema.json
│   ├── generation_event_v1.schema.json
│   ├── outcome_event_v1.schema.json
│   ├── account_pattern_v1.schema.json
│   ├── frame_v1.schema.json
│   └── motion_v1.schema.json
├── 02_what_to_build/                ← 88 chains across 23 families
│   ├── INDEX.json                   ← chain discovery index
│   ├── TF01/  (3 chains)
│   ├── TF02/  (5 chains)
│   ├── TF03/  (4 chains)
│   ├── ... through TF23 (10 chains)
└── (16 other folders, mostly empty — your job to fill)
```

---

## How to Operate

### Before writing code or files

1. **Read `CONVENTIONS.md`** — every file in this repo follows these rules.
2. **Skim `12_data_shapes/`** — these schemas are the contracts. Every record you produce must validate.
3. **Read `BUILD_PLAN.md`** — the day-by-day task list with embedded specs.
4. **Run `python3 scripts/validate.py <record.json> <schema.json>`** before committing any new record.

### Tools available

- **Python 3.11+** with `jsonschema`, `referencing`, `python-docx`, `pyyaml`, `openpyxl`
- **`scripts/validate.py`** — JSON schema validator handling draft 2020-12 + cross-file $ref
- The original research corpus is in `/mnt/user-data/uploads/` (or wherever Mohamed mounted it)

### Source materials (in /mnt/user-data/uploads/ on the original session — Mohamed will mount these)

| File | Use for |
|---|---|
| `OGz_2_0_ChainLibrary_v2_Complete.docx` | 88 chains (DONE) |
| `OGz_Saudi_Instagram_Benchmarks.xlsx` | 100 benchmark accounts (Day 4) |
| `OGz_OpenClaw_Prompt_Requirements.xlsx` | Sector baselines + occasion details (Day 2) |
| `OGzStudios_CEO_Prompt_v1.md` | CEO agent prompt (Day 3) |
| `OGzStudios_COO_Prompt_v1.md` | COO agent prompt (Day 3) |
| `OGzStudios_CCO_Prompt_v1.md` | CCO agent prompt (Day 3) |
| `cd_01_firaasa_architect.md` through `cd_05_paradox_hunter.md` | CD brain methodologies (Day 3) |
| `ogz_campaign_archive.md` | 38 campaign anonymized records (Day 5) |
| `ogz_org_and_kpis.md` | Org context (Day 5) |
| `OGzAI_BrandDNA_Schema_V3_FINAL.docx` | Reference for brand fingerprint structure |
| `CCO_Environment_v2.docx` | Reference for CCO operational spec |
| `OGzAI_Master_Architecture_v4_FINAL.docx` | The big picture architecture |

### Operating principles

**Be deterministic where possible.** Use the chain generator (`scripts/generate_chains.py`) as a reference pattern: parse source → map to schema → validate → write.

**Validate before commit.** A schema failure caught after commit costs 10x more than one caught before. Every record must validate.

**Never duplicate the chain library trick.** When you produce 100 benchmark accounts or 38 campaign records, write a generator script (like `scripts/generate_chains.py`) rather than producing each by hand. Save the generator script in `scripts/` for reproducibility.

**Save your generators.** Every batch operation lives forever in `scripts/`. Mohamed should be able to regenerate the repo from source data + scripts + corpus.

**Ask before redesigning.** If a schema feels wrong, document the friction in `00_start_here/decisions/` as a draft ADR and ping Mohamed. Don't silently change schemas.

**Maintain CONFIDENCE discipline.** Everything you produce from research corpus is `confidence: experimental` until a human validates. Don't claim `confirmed` without authority.

---

## When to Ask Mohamed vs Just Do It

**Just do it (don't ask):**
- Following the spec in `BUILD_PLAN.md` for any day
- Creating files that match an existing schema
- Writing helper scripts in `scripts/`
- Validating outputs
- Fixing typos or small inconsistencies you find

**Ask Mohamed (one tight question):**
- Schema design changes
- New top-level folders not in the plan
- Ambiguity in the source corpus that affects multiple records
- Trade-offs that affect more than one Day's work
- Anything cultural/Saudi-specific that the research doesn't clearly resolve

**Never do without permission:**
- Change anything in `12_data_shapes/` (schemas are frozen at v1)
- Delete or rename existing files
- Push to git without local validation passing
- Add new top-level folders beyond what's in the existing structure

---

## The 5 CD Brains — How to Handle Them

The 5 CD methodologies are **already in the research corpus** as markdown files (in `/mnt/user-data/uploads/`):
- `cd_01_firaasa_architect.md`
- `cd_02_metaphor_architect.md`
- `cd_03_authenticity_detective.md`
- `cd_04_heritage_decoder.md`
- `cd_05_paradox_hunter.md`

**Your job (Day 3):** restructure these into the `cd_brain_v1.schema.json` format. Front-matter YAML + markdown body. Keep the methodology content intact; just structure it consistently.

These are seed methodologies marked `status: seed_v1`, `confidence: experimental`. They are NOT immutable doctrine. They evolve through real client work.

---

## Cultural Specs — The Moat

`15_cultural_specs/` is the **deepest layer** of the system. The 80 fields capture what "Saudi-native" actually means in operational terms. This is what differentiates `{PLATFORM_NAME}` from any foreign tool that translates English content to Arabic.

When building sector defaults (Day 3), the rule of thumb:
- **~70 of 80 fields:** sector-default-derivable (e.g., F&B almost always has gulf-coffee props, dates-on-table behaviors)
- **~10 of 80 fields:** must be brand-overridden at onboarding (e.g., specific dialect, modesty threshold, mixed-gender rule)

If the research corpus is unclear on a cultural field, mark it `confidence: experimental` and flag it for Cultural Advisor review.

---

## Output Quality Bar

For every file you produce:

- [ ] Validates against its schema
- [ ] Has a complete provenance block (5 fields)
- [ ] Uses ULIDs for any IDs
- [ ] Follows file naming conventions in `CONVENTIONS.md`
- [ ] Is in the correct folder per the structure
- [ ] Cross-references are by ULID, not by name
- [ ] Has appropriate confidence level
- [ ] Scope is correctly set

If any of these fails, fix it before moving on.

---

## Definition of Done for Each Day

See `BUILD_PLAN.md` for specifics, but at minimum:

- Every produced file validates
- `scripts/validate.py` exits 0 across the new files
- `CHANGELOG.md` updated with new files added
- Any generator script saved to `scripts/`
- Folder README.md updated where applicable

---

## When You're Stuck

1. **Check `BUILD_PLAN.md`** — the specific day's tasks have embedded specs
2. **Check `CONVENTIONS.md`** — most "which way should I do X?" questions are answered here
3. **Check the schemas in `12_data_shapes/`** — the field names and types are authoritative
4. **Check the corpus files** — Mohamed has them mounted
5. **Ask Mohamed.** One tight question. Continue working on something else meanwhile.

---

## Notes for Future Sessions

- This repo will be public-internal eventually (visible to OGZ partners, employees). Write all comments and READMEs as if a new team member will read them tomorrow.
- The `{PLATFORM_NAME}` placeholder will be find-replaced. Don't hardcode any name.
- When the runtime sync_to_supabase.py is built (separate repo), it will read this repo's files. So filename stability matters more than internal IDs.
- The `13_database/` SQL migrations you write must match the schemas exactly — they are the database manifestation of the file-level schemas.

---

## Last Word

This repo is the company's most important asset. It's the difference between `{PLATFORM_NAME}` being just another fal.ai wrapper and being a defensible Saudi creative intelligence platform.

Build it like it matters. Because it does.

---

*— Claude (the previous session), May 13, 2026, Riyadh*
