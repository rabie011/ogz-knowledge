# Data Residency Policy

## Stance

`{PLATFORM_NAME}` is a Saudi-native platform. Data residency posture reflects that.

## Primary region

- **Supabase Postgres**: `me-central-1` (Bahrain) — closest to Saudi with full Supabase regional support.
- **Object storage (R2/S3)**: KSA region where available; Bahrain fallback.
- **fal.ai**: regional endpoint where available; global with KSA data residency clauses negotiated.

## Backup

- Daily encrypted backup to KSA-based backup region.
- 90-day backup retention; quarterly snapshots for 1 year.

## What stays in KSA (mandatory)

- Customer identifying information
- Brand fingerprint and brand-specific generated content
- Outcome events with engagement data
- OAuth tokens (encrypted at rest)

## What can be processed regionally

- Generic chain definitions (universal, no brand-specific data)
- Universal forbidden lists
- Public benchmark account references

## Compliance posture

- PDPL aligned (Personal Data Protection Law of KSA)
- ISO 27001 target for 2026 Q4
- SOC 2 Type II target for 2027

## Breach response

See `breach_response.md`.
