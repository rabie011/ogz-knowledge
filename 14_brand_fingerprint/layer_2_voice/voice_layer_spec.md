---
title: "Layer 2 — Voice"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 2 — Voice

**What the schema requires:** none individually required, but typical fingerprints fill: `voice_triangle`, `three_love_lines`, `three_hate_lines`, `dialect`, `msa_tolerance`, `emoji_density`, `hashtag_style`, `codeswitch_tolerance`, `anti_vocabulary`.

## Purpose

Layer 2 is the audible identity of the brand — register, dialect, the things it loves to say and refuses to say, its emoji and hashtag posture, its tolerance for English mixing.

This is what the CCO agent reads when scoring whether a generated Arabic caption "sounds like" this brand.

## The Voice Triangle

Three 0–1 axes that locate the brand on a map:

| Axis | 0 (one extreme) | 1 (other extreme) |
|---|---|---|
| `formal_colloquial` | full classical/MSA | pure Saudi colloquial |
| `warm_cold` | impersonal corporate | warm conversational |
| `confident_humble` | humble service-mode | confident challenger |

A premium heritage perfume brand might sit at `(0.7, 0.5, 0.4)` — leaning classical, balanced warmth, slightly humble.
A fintech challenger might sit at `(0.2, 0.5, 0.85)` — leaning colloquial, balanced warmth, highly confident.

## The Three Love Lines

Three sample lines the brand WOULD say. These are the calibration anchors for CCO Arabic QC. When CCO sees a generated caption, it asks: "does this sound like one of the three love lines, or one of the three hate lines, or neither?"

Examples (composed for illustration):
- F&B heritage Najdi café:
  - "حدّك تجلس مع كوبك، نحن نتعب على القهوة عشانك"
  - "نص اللذة في الجلسة، ونصها في ريحة القهوة"
  - "كل يوم نشوي على نار هادية. ولأنه أنت تستحق، ما نستعجل"
- Fintech challenger:
  - "غلطان. توّنا مابدينا"
  - "أسرع طريقة لتدفع، أو ترسل، أو تأخذ"
  - "ليش الطريقة الصعبة لما الموجود أحسن؟"

## The Three Hate Lines

Three things the brand WOULD NEVER say. These are the negative calibration anchors for CCO.

Examples:
- F&B heritage Najdi café:
  - "خصم 50%! العرض ينتهي اليوم!"
  - "البودي بست في الرياض"
  - "خصم محدود — اطلب الآن!"
- Fintech challenger:
  - "نعمل دائماً من أجل عملائنا الكرام"
  - "تجربة سلسة، خدمة متميزة، حلول مبتكرة"
  - "نسعى لتقديم أفضل الخدمات"

## Other fields

- `dialect`: Najdi / Hejazi / Eastern / Southern / Khaleeji-neutral / MSA / mixed (see `04_saudi_rules/arabic_text_rules.yaml`)
- `msa_tolerance`: none / low / moderate / high
- `emoji_density`: zero / sparse / moderate / heavy
- `hashtag_style`: no-hashtags / brand-only / topical / heavy-trending
- `codeswitch_tolerance`: none / low / moderate / high (how much English mixing the brand allows in Arabic captions)
- `anti_vocabulary`: list of specific words the brand refuses (e.g., "حصري", "اكتشف سحر", "innovative", "cutting-edge")

## How data flows in

- Voice triangle: Q3-Q5 of Pipeline A intake (3 ladder questions).
- Love/hate lines: Q10 + Q13 of Pipeline A intake (with examples shown to the client).
- Dialect: Q7 of Pipeline A intake (the most important question; auto-flag if `inferred_low`).
- Anti-vocabulary: Q13 + corpus scrape of brand's existing posts (extract recurring forbidden phrases).

## How it's used at generation time

- COO `compile_caption_context` reads Layer 2 → puts the dialect, top tone descriptors, and anti-vocabulary into Layer 1 of the CaptionContext.
- CCO scores against love/hate lines as calibration; brand-specific. A line scoring near a "love" line gets high marks; near "hate" line gets penalty.

## Voice examples per sector

See companion file `voice_examples_per_sector.yaml` for the curated examples table.
