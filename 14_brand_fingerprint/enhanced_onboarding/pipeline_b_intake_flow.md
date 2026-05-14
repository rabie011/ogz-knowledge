---
title: "Pipeline B — Operational Intake Flow"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Pipeline B — Operational Intake Flow

End-to-end operational sequence for Growth and Enterprise tier onboarding. Includes strategist involvement at 3 checkpoints.

## Step-by-step

### Step 0: Sales qualification
- BD lead qualifies brand: sector fit, monthly content volume need, willingness for managed services.
- Discovery call (60 min): scopes the engagement.
- Contract signed; Stripe Growth ($X/mo) or Enterprise ($Y/mo) subscription activated.

### Step 1: Strategist assigned
- Strategist (human) is assigned to the brand. They are the brand's primary contact during onboarding.

### Step 2: Section 1-2 form (Q1-Q18)
- Identity + sector + Layer 1 Strategy questions.
- Strategist preview-call before final submission: 30 min, validate cd_routing_weights + contrarian belief.

### Step 3: Section 3-4 form (Q19-Q38)
- Voice + Visual Identity questions.
- No strategist call here; brand fills independently.
- Auto-extraction (Apify, website, Google Business) runs in parallel.

### Step 4: Section 5 form (Q39-Q46)
- Cinematography questions.
- No strategist call here.

### Step 5: Section 6-7 form (Q47-Q60)
- Look & Feel + Production Signature.
- **Strategist call**: 30 min, validate mood lexicon + reference brand anchors + signature ritual.

### Step 6: Cultural Advisor review
- Cultural Advisor (Pipeline B always involves Cultural Advisor) reviews the complete cultural spec implied by the fingerprint.
- Sector × region default is loaded as the baseline; brand overrides are captured.
- Cultural Advisor signs off before activation.

### Step 7: COO `build_branddna` (extended)
- All Pipeline B fields are `explicitly_confirmed`.
- COO builds the full 6-layer fingerprint.
- Memory Controller writes (RLS-isolated).

### Step 8: Strategist final review
- 60-min call: strategist walks through the complete fingerprint + first month's content plan.
- Brand approves or requests revisions.
- Status: `active`.

### Step 9: Monthly calendar generation
- Growth tier: 20 posts/month.
- Enterprise tier: 40+ posts/month + extra custom executions.
- All hero content routed through human review at CD-lead level.

## Confidence floor

- Growth tier: 0.65
- Enterprise tier: 0.7

## Distinct from Pipeline A

- Strategist is present (vs. self-service)
- Cultural Advisor approval required at activation
- Two-CD Diagnostic routing more frequently fires (richer brand fingerprint = more pronounced weights)
- Hero content always human-reviewed
