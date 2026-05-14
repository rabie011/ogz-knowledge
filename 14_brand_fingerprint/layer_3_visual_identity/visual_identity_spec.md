---
title: "Layer 3 — Visual Identity"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 3 — Visual Identity

**What the schema covers:** `primary_color` (hex, philosophy, extension rule, usage_pct, temperature_lock, saturation_lock, forbidden_pairings), `secondary_color`, `typography`, `composition`, `logo_behavior`, `seed_range`, `reference_locks`.

## Purpose

Layer 3 is the visible identity — the palette, type, composition rules, logo behavior, and reference locks that constrain image generation.

This is what fal.ai sees through the COO's compiled CaptionContext. The COO doesn't pass raw Arabic into image prompts (Arabic is applied post-generation by Sharp/Canvas), but it passes color palette, typography choices, and composition cues.

## Primary color

Each brand has one primary color that anchors the visual identity. Fields:

- `hex`: `#RRGGBB`
- `philosophy`: why this color (one sentence). E.g., "Hejazi coastal blue — invitation, openness, the sea you can see from the café"
- `extension_rule`: how the color extends into neutrals (e.g., "warm beige for backgrounds; soft cream for body text on color blocks")
- `usage_pct`: typical share of the visual frame (e.g., 30%)
- `temperature_lock`: "warm" / "cool" / "neutral"
- `saturation_lock`: "low (40-60)" / "moderate (60-80)" / "high (80-100)"
- `forbidden_pairings`: colors that don't go with this primary

## Secondary color + accents

Secondary is the second-most-visible color in the brand's frame. Accents (1-3) are the punctuation marks.

## Typography

- Arabic font: family + weight + tracking + line-height rules
- English font: family + weight + tracking + line-height rules
- Pairing rule: equal optical weight always (per `04_saudi_rules/arabic_text_rules.yaml`)
- Anti-vocabulary applies to type style too (e.g., no "decorative" or "calligraphic" if the brand register is modern)

## Composition

- Grid style: 8-point baseline / 12-column / Fibonacci / free
- Negative-space ratio: ≥40% / 30-40% / <30%
- Subject placement: center / rule-of-thirds / off-edge
- Crop discipline: full-frame / tight / breathing-room

## Logo behavior

- Placement: top-left always / bottom-right always / contextual
- Sizing: small (8-12% of frame width) / medium (12-18%) / large (>18%)
- Color rule: always white / always brand-primary / contextual
- Clear space: 1.5x logo height minimum

## Seed range

A 2-integer range for image-generation seed locking. The brand's content uses seeds within this range for consistency across posts.

## Reference locks

Up to 5 reference images the brand has confirmed represent its visual identity. fal.ai uses these as control-net or img-to-img references for tight brand fidelity.

## How data flows in

- Color: Q11 of Pipeline A (color picker + brand-logo color extraction).
- Typography: Q12 (brand has a typeface? pick from curated list / upload custom).
- Composition: inferred from Instagram scrape; CCO confirms or flags.
- Logo behavior: standard defaults at onboarding; brand can override later.

## How it's used at generation time

- COO compiles palette + typography rules into prompt scaffolding.
- fal.ai receives palette HEX values, style tokens, and reference image URIs.
- Sharp/Canvas applies brand color to caption text post-generation.

## Anti-patterns

- 5+ color palette: dilutes brand recognition. Cap at 3 (primary + secondary + 1 accent).
- High-saturation primary + high-saturation secondary: kills the eye. One should be moderate or neutral.
- Logo over face: never. Universal forbidden.

## Companion file

See `color_extension_rules.yaml` for the brand-color-to-neutrals extension matrix.
