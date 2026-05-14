# ADR-0002 — ULIDs as Universal Identifiers

**Status:** Accepted
**Date:** 2026-05-13
**Decided by:** Mohamed

---

## Context

Every record in the knowledge base needs a unique identifier. The ID must be:
- Stable (referenceable across files, DB, object storage, API)
- Sortable (so we can order records chronologically without a separate timestamp column)
- Mintable anywhere (in files, in scripts, in the runtime, by clients) without coordination
- Compact enough for filenames

The standard options are:
- **Postgres serial / autoincrement** — requires DB connection to mint
- **UUIDv4** — random, not sortable, ugly in filenames
- **UUIDv7** — newer, sortable, but still hex-uglier
- **Snowflake IDs** — vendor-flavored (Twitter, etc.)
- **ULIDs** — 26-char Crockford base32, timestamp-encoded, lexicographically sortable

## Decision

**Use ULIDs (Universally Unique Lexicographically Sortable Identifiers) for all record identifiers.**

Format: 26 characters, Crockford base32 alphabet (`0123456789ABCDEFGHJKMNPQRSTVWXYZ`).

Example: `01HXZQQR4M2PVQ4VZG9YT3WQBB`

The first 10 characters encode the millisecond Unix timestamp; the last 16 are random.

## Implementation

- **Python:** `python-ulid` library
- **JS/TS:** `ulid` package (npm)
- **PostgreSQL:** stored as TEXT, indexed; could use BYTEA for compaction (not needed at our scale)
- **Deterministic ULIDs:** for seed records, derived from `sha256(canonical_string)` mapped to Crockford base32; ensures repo regeneration produces the same IDs
- **Random ULIDs:** for runtime events; uses standard ULID generation

## Consequences

### Positive
- Records sort chronologically without separate ORDER BY timestamp
- Filenames sort meaningfully (`01HXZQQR...` files cluster by creation time)
- IDs can be minted in scripts, files, and runtime without DB coordination
- 26 chars fits in any column, filename, URL path
- Crockford base32 has no ambiguous characters (no I/L/O confusion)

### Negative
- 26 chars > 8-byte int (size)
- Most ORMs don't have first-class ULID support; treated as strings
- Slight performance penalty on indexed lookups vs ints (negligible at our scale)

## Reversibility

Migrating away from ULIDs would require updating every record + every reference. High cost. Don't migrate.
