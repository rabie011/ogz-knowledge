---
title: "Anti-Convergence Monitor"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Anti-Convergence Monitor

Operational spec for detecting and addressing brand drift toward the sector mean over time.

## What drift looks like

Over months of operation, a brand's actual published content can drift away from its onboarded fingerprint:
- The brand picks the same chain repeatedly because it engages best, narrowing its visual range
- CCO scores tone-conservative outputs higher, slowly muting the brand's contrarian voice
- The CD-Brain Router increasingly picks the same brain because the sector-affinity heuristic dominates
- Production signature ritual slips away as different talent rotates in

Result: distinctiveness score declines over 3-6 months, and the brand's content starts to look like its sector peers.

## How the monitor works

### Daily signal
- Each post published is vectorized (caption + image embedding).
- Cosine similarity to brand's onboarded fingerprint vector is computed.
- If similarity > 0.92, flag as "drifting-near-mean" (post is generic for the brand).
- If similarity < 0.65, flag as "outlier" (post is off-brand).

### Weekly aggregation
- Sunday 02:00 Riyadh: Learning Agent reviews the past 7 days of published posts per brand.
- Computes 7-day moving average of similarity-to-fingerprint.
- Compares to 4-week moving average.

### Alert triggers
- **Yellow alert:** 7-day average ≥ 0.05 above 4-week average. Notify strategist + brand: "Your content has been more conventional this week."
- **Red alert:** 7-day average ≥ 0.10 above 4-week average for 2+ consecutive weeks. Auto-route next 3 posts through Cultural Advisor for rebalancing.
- **Critical alert:** brand's distinctiveness score has dropped below 0.30 from previous threshold. Trigger fingerprint review.

### Response actions

| Alert | Auto-action | Human action |
|---|---|---|
| Yellow | Surface advisory in dashboard | Optional: strategist outreach |
| Red | Route next 3 hero posts to Cultural Advisor | Strategist call to brand within 5 business days |
| Critical | Pause auto-generation for hero content | Cultural Advisor + Mohamed jointly review fingerprint |

## What the monitor does NOT do

- It doesn't force brands to be more distinctive than they want.
- It doesn't override brand explicit rejections.
- It surfaces the drift; the brand decides whether to act.

## Implementation

- Embeddings + cosine: pgvector in Postgres.
- Aggregation: daily materialized view `brand_drift_signals_view`.
- Alerts: Learning Agent (Sundays); inline dashboard for daily signals.
- Cross-references: `brand_fingerprint_score_spec.md`, `13_database/migrations/0003_materialized_views.sql`.
