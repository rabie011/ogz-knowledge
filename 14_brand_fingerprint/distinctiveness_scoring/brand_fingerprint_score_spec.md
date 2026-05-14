---
title: "Brand Fingerprint Distinctiveness Score Spec"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Brand Fingerprint Distinctiveness Score

A single 0-1 score per brand measuring how distinct that brand's fingerprint is from its sector mean. Higher = more distinctive; lower = more sector-conventional.

## Formula

```
distinctiveness_score = 1.0 - avg_cosine_similarity_to_sector_peers
```

Where:
- The brand's fingerprint is vectorized (concatenating numeric fields + embedding categorical fields).
- We compute cosine similarity to every other brand in the same sector.
- We average across those similarities.
- Subtract from 1.0.

## Vectorization

- L1 numeric fields: `cd_routing_weights` (5 dim) + voice triangle (3 dim) = 8 dim
- L3 numeric: primary_color hex → HSL (3 dim) + usage_pct (1 dim) = 4 dim
- L5 numeric: tradition_modernity_balance (1 dim) + each cultural_resonance field tokenized = ~5 dim
- Categorical fields: embedded via OpenAI embeddings text-embedding-3-small (1536 dim per field)
- Mood lexicon: embedded as concatenated text (1536 dim)
- Reference brand anchors: not vectorized (internal-only, not used for distinctiveness)

Total vector dimension: ~3000 (numeric + embeddings).

## Thresholds

- **< 0.30** — Urgent. Brand is highly conventional for its sector. Surface alert to brand: "Your fingerprint is very similar to other brands in your sector. Consider strengthening your contrarian belief or unique reference locks."
- **0.30 – 0.60** — Acceptable. Brand is distinguishable but not differentiated. Surface as advisory.
- **> 0.60** — Excellent. Brand has a clearly distinct posture in its sector.

## Computation cadence

- Initial: computed when brand fingerprint is sealed (post-onboarding).
- Updated: monthly batch (Sunday 02:00 Riyadh) when any fingerprint changes are merged.
- Surface: `current_score`, `sector_average`, `last_computed` in the brand's `distinctiveness` block.

## Implementation

- Backend (runtime, not this repo): Postgres + pgvector for similarity computation.
- The materialized view `brand_distinctiveness_view` exposes current scores per brand for dashboard reads.
- See `13_database/migrations/0003_materialized_views.sql` for view definition.

## How the score is used

- **Brand dashboard:** surfaced to brand as a single number ("Your distinctiveness: 0.42 — sector median 0.38").
- **CD-Brain Router (indirect):** if score drops below 0.30, the router applies a "distinctiveness boost" — slight bias toward less-frequently-routed brains for this brand's briefs.
- **Anti-convergence monitor (companion file):** triggers proactive alerts.

## What it does NOT do

- It's not a quality score. A brand can have low distinctiveness and high content quality.
- It's not a similarity-to-best-performer score. It measures distance from the sector mean, not distance from sector leader.
- It's not a brand-strength score. It's a brand-individuality score.
