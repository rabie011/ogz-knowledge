# Schema Evolution Rules

All schemas in this folder are versioned (`schema_version: 1`). These rules govern how schemas change.

## Rules

1. **Add before remove.** New field → dual-write phase → consumer migration → deprecation → removal. Never delete a field in the same version you add its replacement.

2. **Never reuse deleted field names.** Once a field name is removed from a schema, it must never be used again (even with a different type or meaning). Mark removed fields in a `_deprecated_fields` comment.

3. **Changing enum values = breaking change.** Adding a new value to an enum (e.g., adding `"reel"` to content_type) is a minor change. Renaming or removing an enum value is a MAJOR version bump.

4. **Semantic changes require a version bump.** If a field keeps the same name and type but changes meaning (e.g., `engagement_potential` changes from "relative to account" to "absolute benchmark"), that's a breaking change.

5. **All migrations live in `scripts/migrations/`.** Every v1→v2 transition must have a runnable script: `scripts/migrations/migrate_obs_v1_to_v2.py`. The script must be idempotent (safe to re-run).

6. **Validate compatibility before merge.** `guard_data_quality.py` checks that all obs have the expected `schema_version`. If a schema bump is in progress, both versions must validate during the transition period.

7. **One schema version per record type at a time.** Don't leave half the obs at v1 and half at v2 indefinitely. Complete migrations within one session.

## Version History

| Schema | Version | Date | Notes |
|--------|---------|------|-------|
| observation_v1 | 1 | 2026-05-14 | Initial schema — 80+ fields |
| chain_v1 | 1 | 2026-05-14 | Initial — 23 TF families |
| All others | 1 | 2026-05-14 | Initial versions |

## When to Bump

- Adding optional fields: NO bump (backward compatible)
- Adding required fields with default: minor bump consideration
- Removing fields: MAJOR bump + migration script
- Changing field type: MAJOR bump + migration script
- Adding enum values: NO bump (backward compatible)
- Removing/renaming enum values: MAJOR bump + migration script
