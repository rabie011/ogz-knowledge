---
title: "Layer 5 — Look & Feel"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 5 — Look & Feel

**Schema fields:** `mood_lexicon` (10-20 words), `reference_brand_anchors`, `audience_emotional_state_lock`, `cultural_resonance`.

## Purpose

Layer 5 is the felt experience of the brand. Mood, reference anchors, the emotional state the audience should be in when they encounter the brand's content.

This is what binds the previous four layers into a coherent feeling. A brand can have right strategy + right voice + right palette + right cinematography and still feel "off" if the mood lexicon doesn't cohere.

## Mood lexicon

10-20 mood words that the brand IS. Not aspirational — describing the existing or intended feeling.

Examples:
- F&B heritage Najdi café: "warm, hospitable, unhurried, grounded, generous, present, quiet, story-bearing, reverent, family-rooted, dignified, attentive"
- Fintech challenger: "sharp, confident, contemporary, useful, clear, direct, modern, capable, ambitious, no-nonsense, sleek, immediate"
- Beauty heritage perfume: "intimate, layered, mysterious, refined, generational, sensory, slow, reflective, considered, ritual, treasured"

## Reference brand anchors

Up to 5 brands the audience already recognizes that share the felt-experience this brand wants to occupy. **Internal use only** — never client-facing.

For each anchor:
- brand_name
- what_this_brand_does_similarly
- what_this_brand_does_differently

This isn't aspirational ("we want to be like Apple"). It's calibrating: "this brand's audience feels the same way they feel about X — but with these specific differences."

## Audience emotional state lock

The emotional state the brand intends the audience to be in when they encounter content. One sentence.

Examples:
- "Calm anticipation — the audience knows the next post will reward them by being warmer than they expected."
- "Sharp interest — the audience expects to be surprised by something practical they didn't see coming."
- "Grounded recognition — the audience feels seen by content that names something they hadn't named themselves."

This lock is the qualitative anchor for all generation. CCO can flag content as "audience-state-mismatch" if generated content induces a different feeling.

## Cultural resonance

Object with sub-fields:
- `saudi_dimension`: which aspect of Saudi cultural register the brand resonates with (Najdi-pride / Hejazi-warmth / Vision-2030-ambition / generational-continuity / Khaleeji-confidence)
- `taboo_proximity`: how close the brand comfortably gets to cultural taboos (avoidant / respectful / playful-with-care / engaging)
- `tradition_modernity_balance`: percentage split (e.g., 60% modernity, 40% tradition)
- `regional_specificity`: how regionally-specific the brand is (pan-Saudi / region-locked / region-leading)

## How data flows in

- Onboarding Q14-Q15 (Pipeline A) or Q35-Q45 (Pipeline B): mood ladder + reference brand prompts.
- Instagram + competitive scrape: helps calibrate audience emotional state from real engagement patterns.

## How it's used at generation time

- Mood lexicon feeds into the CaptionContext as tone scaffolding.
- Reference brand anchors are INTERNAL — they shape COO's compiler choices but never appear in prompts.
- Audience emotional state lock is the CCO's qualitative check: does this generated piece induce the right feeling?

## Anti-patterns

- Mood lexicon with more than 20 words: dilutes signal; CCO can't calibrate.
- Mood lexicon with vague words ("good", "nice", "high-quality"): no signal. Use specific feeling-words.
- Reference brands within the same direct competitor set: confuses CCO; pick adjacent-category anchors instead.
