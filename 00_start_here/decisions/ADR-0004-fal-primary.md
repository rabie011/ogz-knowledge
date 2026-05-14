# ADR-0004 — fal.ai as Primary Model Provider

**Status:** Accepted
**Date:** 2026-05-13
**Decided by:** Mohamed

---

## Context

`{PLATFORM_NAME}` generates images and video. The model landscape in 2026:
- **FLUX (Black Forest Labs)** — text-to-image leader
- **Kling 2.1** — text-to-video premium
- **Veo 3 (Google)** — text-to-video competitor
- **Wan (Alibaba)** — image/video, Chinese strength
- **Replicate** — model aggregator, slower
- **fal.ai** — model aggregator, sub-second latency, 200+ models
- **OpenAI DALL-E 3** — limited Arabic, expensive
- **Custom self-hosted (ComfyUI, A1111)** — full control, high ops cost

Requirements:
1. Sub-30-second total latency for image; sub-3-minute for video (Pipeline A needs fast)
2. Multiple model families accessible through one API (avoid 5 SDKs)
3. LoRA support (per-brand custom training crucial for character consistency)
4. Reasonable cost per call (Pipeline A economics: ~$0.05 / image gen acceptable)
5. Saudi-friendly: no provider that blocks Arabic content or imposes US-flavored content policy heavily

## Decision

**fal.ai is the primary model provider for the 88 chains in the v1 chain library.**

Secondary providers (for fallback or special cases):
- Direct FLUX API (if fal.ai outage; pricier)
- Replicate (for models not on fal.ai)
- OpenAI (for chains that need GPT-Image-2 or similar OpenAI-specific output)

## Implementation

- All chain JSONs in `02_what_to_build/` declare their primary model with `provider: "fal"`
- Chain prompts use fal.ai's API conventions
- LoRA models trained per-brand uploaded to fal.ai for inference
- Cost budgets tracked per-brand per-month against fal.ai usage
- Latency budgets: chains declare `latency_estimate_seconds`; runtime alerts if 95th percentile exceeds 2x

## Consequences

### Positive
- One SDK, one API, 200+ models
- Sub-second to sub-minute latency depending on model
- LoRA inference supported natively (critical for brand fingerprint character locks)
- Active model catalog — new models added quickly
- Cost is competitive (~$0.04-1.80/gen depending on model)

### Negative
- Vendor dependency on fal.ai
- fal.ai outage = `{PLATFORM_NAME}` outage (until fallback engages)
- Pricing changes from fal.ai propagate directly to our economics
- Content policy: fal.ai applies their own policy in addition to our cultural compliance — possible conflicts with Saudi-specific content

### Accepted trade-offs
- Vendor dependency accepted; chain JSONs declare provider so swapping is a config change
- Outage risk mitigated by fallback providers (Replicate as backup, OpenAI for some chains)
- Content policy: we route Saudi-sensitive content through fal.ai with brand-side compliance metadata; escalate when fal.ai's policy conflicts with our brand requirements

## Mitigation Plan

If fal.ai becomes unsuitable:
1. Chain JSONs are provider-tagged: bulk-rewrite from `fal` → another provider is a script
2. LoRA weights stored in our own object storage; portable to any inference provider
3. The runtime's fal.ai client is one module — swap to Replicate, ComfyUI, or self-hosted in a sprint

Expected primary lifetime: 12-24 months. fal.ai's velocity is the main reason; if a model family becomes their exclusive offering, we benefit. If they slow down, we move.
