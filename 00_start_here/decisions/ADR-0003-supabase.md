# ADR-0003 — Supabase as Runtime Database

**Status:** Accepted
**Date:** 2026-05-13
**Decided by:** Mohamed

---

## Context

The runtime layer (separate repo) needs a database for:
- Per-brand fingerprints
- Brief intake and brand state
- Generation events (append-only log)
- Outcome events (append-only log)
- Materialized views (eligible-chains-per-brand, distinctiveness scores)
- Vector embeddings for retrieval-augmented generation

Requirements:
1. Postgres-compatible (we want SQL, pgvector, RLS)
2. Saudi data residency available
3. Auth + Row Level Security out of the box (multi-tenant safety)
4. Object storage for generated content
5. Minimal ops overhead at our team size

Options:
- **Self-hosted Postgres + auth0 + S3** — full control, high ops cost
- **AWS RDS + Cognito + S3** — common, expensive at small scale, no first-class RLS UX
- **Supabase** — Postgres + auth + RLS + storage in one product
- **Neon + custom auth + R2** — composable but more glue
- **PlanetScale** — MySQL-flavored, no pgvector

## Decision

**Use Supabase as the runtime database, auth provider, and object storage.**

For Saudi data residency, configure Supabase project in `me-central-1` (Bahrain) or wait for KSA-hosted regions when available. Implement local backup to KSA-resident storage as redundancy.

## Implementation

- Single Supabase project per environment (dev, staging, prod)
- Schema defined in `13_database/migrations/*.sql`
- Auth via Supabase Auth (email + magic link initially, SSO later)
- RLS enabled on all per-brand tables, with policies in `0002_rls_policies.sql`
- Object storage buckets:
  - `brand-assets` (RLS by brand_ulid)
  - `generated-content` (RLS by brand_ulid)
  - `lora-weights` (RLS by brand_ulid)
  - `character-library` (public read for reference content)
- pgvector extension for embeddings (1536-dim for OpenAI-compatible embeddings)

## Consequences

### Positive
- Postgres-compatible, so file-first portability stays intact
- RLS is enforced at the DB layer (defense in depth alongside file-level scoping)
- Auth handled; no NIH auth code
- Vector + relational + storage in one vendor
- Generous free tier; pay as we grow

### Negative
- Vendor dependency on Supabase
- Saudi data residency requires either Bahrain region OR self-hosted Supabase
- RLS policy mistakes are a top risk vector — must be carefully audited
- Storage egress costs at scale; need to monitor

### Accepted trade-offs
- We accept Supabase lock-in for v1 in exchange for operational simplicity
- We retain portability via files-first; migrating away is feasible if needed
- PDPL residency: hybrid (Bahrain for compute, KSA mirror for backup) until KSA regions exist

## Mitigation Plan

If Supabase becomes unsuitable:
1. Files-first architecture means knowledge survives
2. Postgres-compatible: dump/restore to self-hosted or another vendor
3. RLS policies portable (with adjustment)
4. Storage: migrate to S3-compatible (R2, B2, etc.)

Expected lock-in lifetime: 18-36 months minimum.
