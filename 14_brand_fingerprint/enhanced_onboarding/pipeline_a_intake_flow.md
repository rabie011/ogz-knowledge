---
title: "Pipeline A — Operational Intake Flow"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Pipeline A — Operational Intake Flow

End-to-end operational sequence for Starter tier onboarding.

## Step-by-step

### Step 0: Client signs up + pays
- Platform UI: `/signup`
- Stripe creates customer + initial subscription
- Status: `pending_intake`

### Step 1: 15-question form (Q1-Q15)
- Client fills form. Form posts to `n8n-A01` webhook.
- Estimated time: 2-4 minutes.
- Form auto-saves drafts every 30s.

### Step 2: Auto-extraction
- `n8n-A02` triggers Apify Instagram scraper (Q5 handle) + website scraper (Q6 URL) + Google Business scraper (auto-derived from brand name).
- Result: `instagram_extraction`, `website_extraction`, `google_business_extraction`.
- Timeout: 5 min per source.

### Step 3: COO `build_branddna`
- COO reads form + extractions + sector baseline.
- Produces field nominations with confidence states per the source hierarchy.
- Marks `dialect_confirmed: true/false`.
- Computes `completeness_score`.
- Memory Controller writes to BrandDNA (RLS-isolated).

### Step 4: Brand snapshot card
- Client sees their brand profile.
- Confidence states surface visually (green / amber / red).
- Client can confirm or correct any field (triggers `N8N-A04` revision flow).

### Step 5: First calendar generation
- CEO routes: `pipeline: A`, `request_type: calendar_scheduled` or `calendar_ondemand`.
- COO compiles CaptionContext.
- DeepSeek generates 8 posts (Starter monthly volume).
- CCO Arabic QC.
- COO confidence score per post.
- Gate routing: clean / watermarked / hold.

### Step 6: Email delivery
- Resend: "Your [Month] content calendar is ready! 🎉"
- Calendar dashboard live in platform.

## Confidence-state source hierarchy

```
explicitly_confirmed  → form answer (highest)
inferred_high         → form + scraper agree
inferred_medium       → single scraper signal OR form without corroboration
inferred_low          → weak/conflicting signals
missing               → no signal — sector baseline fallback
```

## Watermark policy

- Post score 75+ → `clean` → publishes normally
- Post score 50-74 → `watermark_required` → publishes with "Beta AI draft" translucent overlay
- Post score <50 → `hold` → routes to Production Copilot queue

## Auto-flag triggers (route to human gate)

1. `arabic_dialect` confidence is `inferred_low` AND post is hero content
2. `brand_differentiator` field is missing
3. `tone_anti_attribute_ids` field is missing
4. First-ever client output (always human-reviewed)
5. Sector is Healthcare or Government (always human-reviewed)

## Confidence floor

Starter tier confidence floor: `0.6`. If overall confidence is below 0.6, calendar generation is paused; client is prompted to complete missing fields.
