---
title: "Layer 6 — Production Signature"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 6 — Production Signature

**Schema fields:** `talent_profile`, `location_profile`, `prop_signature`, `wardrobe_palette`, `signature_ritual`.

## Purpose

Layer 6 is the recurring production details that make the brand feel itself. The specific recurring talent archetype, the specific location aesthetic, the signature props, the wardrobe register, and the one ritual the brand repeats across content.

This is the layer that, when done right, makes a brand's content instantly recognizable from a thumbnail.

## Talent profile

- `archetype`: "the calm host" / "the curious explorer" / "the dedicated craftsperson" / "the generous matriarch" / "the focused young professional"
- `age_range`: typical age window
- `regional_look`: Najdi-classical / Hejazi-coastal / general-Saudi
- `consistency_model`: same-person-always / rotating-core-cast (2-4 people) / archetypal-character (different faces, same archetype)
- `directing_style`: lightly-directed-real / scripted-natural / scripted-stylized

## Location profile

- `primary_setting`: cafe-interior / home-majlis / boutique-floor / clinical-room / architectural-exterior
- `region_aesthetic`: Najdi / Hejazi / modern-Riyadh
- `time-of-day`: morning-golden / afternoon-warm / evening-cool / artificial-clean
- `recurring_specific_location`: if any (e.g., "always the same café table by the window")

## Prop signature

- `hero_prop`: the ONE recurring prop that appears in most pieces (e.g., "the brand's signature dallah" or "the brand's specific notebook")
- `secondary_props`: 3-5 recurring secondary objects
- `forbidden_props`: brand-specific exclusions on top of universal forbidden list

## Wardrobe palette

A small array of color × texture references for talent wardrobe. Should harmonize with the primary brand color.

## Signature ritual

The ONE recurring action the talent performs across content that becomes a brand signature.

Examples:
- F&B heritage café: "every video, the host pours the coffee with the right hand and the cup is placed by the elder first"
- Beauty heritage perfume: "every video, the bottle is lifted slowly, then the wrist is dabbed and inhaled"
- Real estate Vision-2030: "every video, the camera walks through the doorway and pauses one beat before the reveal"

This isn't a marketing gesture. It's a craft commitment that becomes a thumbnail signature.

## How data flows in

- Onboarding Q15 (Pipeline A) or Q50-Q60 (Pipeline B): production discipline questions.
- Brand's existing content: COO extracts recurring talent archetype, locations, props from a scraped sample.
- Cultural Advisor: reviews proposed production signature for cultural compliance before finalizing.

## How it's used at generation time

- For image-generation chains: prop signature + wardrobe palette inform reference-image construction.
- For video chains: signature ritual is baked into the script structure (every video has the ritual moment).
- COO refuses to publish a hero piece without the brand's signature ritual at the hero moment.

## Anti-patterns

- Generic talent archetype ("relatable" / "modern" / "premium") — no signal. Use specific archetype words.
- 10+ secondary props: dilutes recognition. Cap at 5.
- Signature ritual that is too elaborate: should be subtle and repeatable in 2-3 seconds.

## Updates

L6 evolves slowly. A change here is a significant brand shift; PR + Cultural Advisor sign-off + Mohamed required.
