---
title: "Pipeline A — 15-Question Critical Starter"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Pipeline A — 15-Question Critical Starter Intake

The minimum form to onboard a Saudi SME to the platform's Starter tier. Covers the 10 critical BrandDNA Lite fields plus 5 confidence-establishing questions.

Target completion time: under 4 minutes.

## The 15 questions

### Identity (Q1-Q3)
1. **Brand name (Arabic)** — `brand_name_ar` — required. Auto-validated for proper Arabic letterforms.
2. **Brand name (English)** — `brand_name_en` — required.
3. **Business sector** — `sector` — dropdown. F&B / Retail / Beauty / Real Estate / Healthcare / Other. Maps to `05_sector_defaults/<sector>.yaml`.

### Cultural anchor (Q4-Q7)
4. **City / primary market** — `city_primary` — Riyadh / Jeddah / Dammam / Khobar / Madinah / Makkah / other. Drives regional cultural spec selection.
5. **Instagram handle** — `@handle` — used for auto-extraction (Apify scraper). Optional but high-value.
6. **Website URL** — optional — used for richer brand voice extraction.
7. **Arabic dialect** — `arabic_dialect` — **MOST IMPORTANT FIELD.** Najdi / Hejazi / Eastern / Southern / Khaleeji-neutral / MSA. Auto-flag if `inferred_low`.

### Strategic positioning (Q8-Q10)
8. **Price positioning** — `price_position` — Budget / Mid-market / Premium / Luxury.
9. **Primary audience description** — `primary_audience` — free text or multi-select.
10. **What makes your brand different?** — `brand_differentiator` — free text, min 20 chars. **Cannot be inferred.** If empty or under 20 chars, marked `missing`.

### Operational (Q11-Q13)
11. **Brand maturity** — `brand_maturity` — New (<1yr) / Growing (1-3yr) / Established (3-7yr) / Legacy (7+yr).
12. **Primary content goal** — `primary_kpi_type` — Engagement / Conversion / Brand awareness / Lead gen / Customer support.
13. **What tone should your brand NEVER use?** — `tone_anti_attribute_ids` — multi-select from curated list. Critical for QC. **Cannot be inferred from scrapers.** If empty, mark `missing`.

### Calendar (Q14-Q15)
14. **Competitor Instagram handles** — up to 3 handles — optional, used for competitive gap analysis.
15. **Ramadan content importance** — `ramadan_relevance` — Critical / High / Medium / Low / Not relevant. Drives content calendar prioritization.

## Confidence-scoring mapping per field

See `pipeline_a_intake_flow.md` for the full source-hierarchy rules.

Field → confidence state at COO `build_branddna`:
- `arabic_dialect`: explicitly_confirmed if form (Q7) answered; inferred_high if form + IG analysis agree.
- `brand_differentiator`: explicitly_confirmed if Q10 has ≥20 chars; otherwise missing.
- `tone_anti_attribute_ids`: explicitly_confirmed if Q13 has selections; otherwise missing.
- All other 7 fields: explicitly_confirmed at form level; inferred_high if corroborated by IG/website scrape.

## What the form does NOT cover (deferred to chat)

Fields filled later through conversational onboarding (Phase 3 per the platform design):
- Three love-lines / hate-lines (L2)
- Reference brand anchors (L5)
- Signature ritual (L6)
- Detailed CD routing weights (L1) — inferred from Q3 + Q7 + Q10 + Q13

## Validation gates

- Q3 not Other-text — must select from curated sector list (or "Other" with sub-text routing to human review).
- Q7 not unconfirmed for hero content — if `arabic_dialect: inferred_low`, hero posts (high-budget chains) are auto-routed to human review.
- Q10 minimum 20 characters — system rejects under-20 with "Tell us more — this drives every piece of content."
