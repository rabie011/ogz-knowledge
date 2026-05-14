# Pipeline A — Operational Flow

**Tier:** Starter
**Audience:** Saudi SMEs, self-service
**Monthly content:** 8 posts
**Price point:** SAR 2,500/month
**Onboarding time:** under 4 minutes

## End-to-end flow

1. **Signup + payment** — Stripe customer + initial subscription
2. **15-question intake** (`14_brand_fingerprint/enhanced_onboarding/15_question_critical_starter.md`)
3. **Auto-extraction** — Apify (Instagram) + website + Google Business scrapers
4. **COO `build_branddna`** — maps form + extractions to 10 critical BrandDNA fields with confidence states
5. **Brand snapshot card** — client confirms or corrects fields (triggers revision flow)
6. **First calendar generation** — CEO routes → COO compiles CaptionContext → DeepSeek generates 8 captions → CCO Arabic QC → COO confidence score
7. **Gate routing** — clean (score ≥75) / watermarked (50-74) / hold (<50)
8. **Delivery** — Resend email + calendar dashboard

## Gates and auto-triggers

- **Confidence floor**: 0.6. Below this: paused, prompted to complete missing fields.
- **Auto-route to human gate**: first-ever output, healthcare sector, government sector, dialect_unconfirmed_hero content.
- **Watermark required**: confidence_mode `Cautious` or `Minimal`.

## What happens when something fails

| Failure | Auto-response |
|---|---|
| Apify scrape times out | Mark Instagram fields `inferred_low`; continue with form data only |
| BrandDNA `dialect_confirmed: false` | Surface dialect-confirm prompt; hold hero content |
| CCO returns `HARD_BLOCK` on any post | Auto-regenerate; if 2nd attempt also fails, route to human review |
| Cost ceiling breached for the month | Pause generation; surface upgrade prompt |
