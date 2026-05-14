# ADR-0001 — Files-First, Database Second

**Status:** Accepted
**Date:** 2026-05-13
**Decided by:** Mohamed
**Architect:** Mohamed + Claude (deep research)

---

## Context

`{PLATFORM_NAME}` requires durable, versionable, auditable knowledge: 88 chain definitions, 5+ sector baselines, 5+ Saudi occasions, 5 CD-brain methodologies, 80-field cultural specs, brand fingerprints, campaign archive, ~100 IG benchmarks, agent prompts, and routing rules.

The default move in any startup is to model this knowledge as database tables from day one. Tables are convenient: SQL queries, ORMs, dashboards. The problem with database-first knowledge is:

1. **Hidden mutation.** Every UPDATE statement silently rewrites history.
2. **Vendor lock-in.** Postgres-flavored types and constraints lock you to one DB.
3. **No human review.** Schema changes go through migrations, not Pull Requests.
4. **No diff-able history.** "Show me what changed in the F&B sector baseline last quarter" requires audit logs that nobody implements.
5. **No copy-paste portability.** Onboarding a new system means re-exporting the data.
6. **Trust depends on the database being reliable.** When the database goes down, the knowledge goes with it.

`{PLATFORM_NAME}` competes on **cultural authenticity as a moat**. The moat is only as defensible as the discipline behind it. A database-first approach makes the moat invisible — it's just rows in a table that anyone with credentials can modify.

---

## Decision

**The Git repository is the source of truth. The Postgres database is an index over the files.**

Specifically:

1. Every record type (chain, sector baseline, occasion, CD brain, cultural spec, agent prompt, etc.) lives as a file in this repo (`.json`, `.yaml`, or `.md`).
2. Files are organized in a strict folder hierarchy (16 numbered folders).
3. Every file validates against a JSON schema in `12_data_shapes/`.
4. Files are modified only via Pull Requests; direct pushes are blocked.
5. The Memory Controller (a deterministic process in the runtime layer) reads files and UPSERTs them into Postgres.
6. The Postgres database is rebuildable from the repo at any time. If the database is corrupted, dropped, or vendor-changed, the data survives.
7. Per-brand data (brand fingerprints, generation events, outcome events) lives in the database with RLS isolation — NOT in this repo. But the structure of those records is defined by schemas in this repo.

---

## Consequences

### Positive

- **Auditable history.** Every change is a commit. `git blame` answers "who decided F&B should use Najdi-leaning colloquial by default?"
- **Diff-able review.** Sector baseline changes get reviewed in GitHub PR with line-level diffs.
- **Vendor-portable.** If Supabase becomes unsuitable, the data ships to any Postgres-compatible system in hours.
- **Human-readable.** A new team member can clone the repo and understand the entire knowledge base by reading files.
- **Backup is free.** GitHub is the backup.
- **Validation gates.** CI rejects schema violations before they hit the DB.
- **Forks possible.** Pipeline-A vs Pipeline-B knowledge variations can be branches with merges as appropriate.

### Negative

- **Sync latency.** Changes to repo aren't reflected in DB until sync_to_supabase.py runs. Mitigated by running on every merge to main.
- **Two sources to keep in step.** Repo + DB. Discipline required to never write directly to DB.
- **Larger ops surface.** Need CI for schema validation, branch protection, deploy automation.
- **YAML/JSON files at scale.** ~250+ files is manageable; if it grows to 10,000+ we may need tooling beyond grep.

### Accepted trade-offs

- We accept higher operational complexity for higher data integrity.
- We accept sync latency for vendor-portability.
- We accept that some operations (like real-time content tagging) require database, not files — those happen in the runtime layer, never here.

---

## Alternatives Considered

### A1 — Database-first, with periodic exports

The mainstream choice. Postgres tables for everything, periodic `pg_dump` for backup.

**Rejected because:** export ≠ source of truth. Audit story is weak. Schema changes don't go through PR review.

### A2 — Headless CMS (Strapi, Sanity, Contentful)

A managed CMS would give us forms, role-based access, and a hosted database.

**Rejected because:** vendor lock-in. Saudi data residency unclear. Schema versioning is the CMS's job, not ours, and that's a loss of control we can't afford.

### A3 — Mixed: some files, some DB

Put "stable" data (chains, schemas) in files, put "evolving" data (patterns, brand fingerprints) in DB.

**Rejected because:** the line between "stable" and "evolving" moves. Once it moves, we'd be migrating between systems. Cleaner to put schemas in files (universal) and instances in DB (per-brand) with no mixing of categories within a record type.

---

## How This Manifests

- This repo IS the source of truth for the knowledge layer
- A separate repo (`ogz-runtime`, future) is the source of truth for the application logic
- A separate repo (`ogz-brand-studio`, future) is the source of truth for the client UI
- The Postgres database is a read-and-write-via-controlled-path system, never a source of truth itself

---

## Reversibility

This decision is **moderately reversible.** If we abandon files-first:
- Easy: export the repo content to DB rows (one-time script)
- Hard: rebuild the audit trail (Git history is lost as a primary source)
- Hard: rebuild the validation gates (CI → DB triggers is non-trivial)

We expect to live with this decision for the lifetime of `{PLATFORM_NAME}` v1 (years).
