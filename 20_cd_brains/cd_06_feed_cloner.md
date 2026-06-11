---
cd_brain_ulid: 01KTVDT0X8CXTNEVK2463V7D1W
cd_brain_slug: cd_06_feed_cloner
name_internal: The Feed Cloner
name_external: Brand-Feed Continuation Director
schema_version: 1
caption_generation_status: ACTIVE — the caption methodology of record (2026-06-11)
diagnostic_question: If this brand's real admin posted tomorrow, what would the post actually say?
signature_technique:
  name: Feed Continuation
  description: The brand's real top-engagement posts become few-shot message pairs; the model continues the feed in its own measured voice — never a house style, never a technique applied from outside.
  failure_mode: >-
    Producing the AVERAGE of the feed — competent-flat imitation with no idea
    inside. The cure is angle-first briefs (truth packs + approved angles)
    feeding this brain — it renders ideas, it does not invent them.
best_fits:
  - any brand with >=20 real captions in the archive (DNA v2/v3 buildable)
  - everyday post types (announcement, offer, question, moment, greeting)
less_good_fits:
  - brands with visual-only feeds (thin captions — excluded honestly)
  - campaign-concept ideation (use CD diagnostic questions at the ANGLE stage instead)
provenance:
  source: founder audit June 10-11, 2026 (568 rejected captions -> doctrine)
  date_added: '2026-06-11'
  confirmer: Mohamed (ADR-2026-06-11 draft)
  confidence: experimental
  scope: universal
voice_register:
  register_descriptor: Whatever THIS brand's feed actually sounds like — measured, not invented.
  arabic_register: The brand's own measured dialect and length distribution. Never a house style.
---

# The Feed Cloner — methodology

Born from the June 10-11 founder audit: 568 technique-driven captions rejected; root causes =
rhetoric-teaching prompts, a judge rewarding the em-dash aphorism, and poetic brief seeds.

## Method (THE DOCTRINE, operational)
1. **The feed is the spec.** Few-shot = the brand's real top-engagement posts as message pairs
   (brief → caption). The model continues a feed; it never "applies a technique."
2. **DNA before generation.** No caption without brand DNA v2+ (voice, measured openers,
   signature phrases, emoji style, length distribution, pattern usage). Builders:
   scripts/build_brand_dna_v2.py / _v3.py.
3. **Positive-only prompts.** Banned structures live in scripts/caption_filter.py (post-gen),
   never in prompt text (pink-elephant: mentioning plants it).
4. **Structure menu, not rhetoric menu.** Post TYPES (announcement / audience question /
   real-life moment / occasion greeting / story when the brand uses it) — selected from the
   brand's own pattern fingerprint.
5. **Occasion FACTS, not tensions.** data/occasion_facts.json (extracted from the validated
   calendar) grounds the occasion. The poetic occasion_tension field is deprecated.
6. **The judge is DNA-aligned.** scripts/scorer_v2.py: brand-opener match, signature presence,
   fit to the brand's own length band, filter pass. Zero structural taste.
7. **The founder's ratings are ground truth.** GOLD set feeds back into few-shot; the judge
   recalibrates against ratings, never against itself.

## Evolution
Seed v1. Evolves through cross-compare ratings — see logs/cross_preferences.json.
