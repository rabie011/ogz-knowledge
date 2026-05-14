#!/usr/bin/env python3
"""
Day 4 / Task 4.1 — Generate Brand Fingerprint specs (~12 files).

Each file is a markdown spec that explains a layer of the 6-layer fingerprint,
how data flows in from onboarding, how it's used at generation time, and example
values per sector.

No formal schema validation on these markdown docs; provenance is in front-matter.
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "14_brand_fingerprint"

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

FRONT = lambda title, scope="universal": f"""---
title: "{title}"
schema_version: 1
created_at: "{NOW}"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "{NOW}"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "{scope}"
---

"""


def write(rel_path: str, content: str):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"✓ {path.relative_to(REPO)}")


# ───────────────────────────────────────────────────────────────────────────
# Layer specs (5)
# ───────────────────────────────────────────────────────────────────────────

L1_STRATEGY = FRONT("Layer 1 — Strategy") + """# Layer 1 — Strategy

**What the schema requires:** `primary_cd_brain`, `cd_routing_weights` (5 values summing to 1.0).
**Optional:** `secondary_cd_brain`, `contrarian_belief`, `single_word_positioning`.

## Purpose

Layer 1 is the strategic posture of the brand — which CD methodology(s) lead its creative output, what it believes that 90% of competitors don't, and the single-word positioning that anchors all downstream layers.

This layer drives the CD-Brain Router. Without it, the router refuses and surfaces a setup error. Brands must complete L1 onboarding before content routing runs.

## Field details

### `primary_cd_brain`
- Enum: `cd_01` / `cd_02` / `cd_03` / `cd_04` / `cd_05`
- Brand's lead methodology. Wins all router ties.
- Picked at onboarding via question framing — not directly named; inferred from the brand's answers about cultural posture, voice register, and competitive frame.

### `cd_routing_weights`
- Five 0–1 values summing to 1.0.
- Determines how the deterministic router scores each brain per brief.
- Example for a heritage-anchored F&B brand: `cd_01: 0.20, cd_02: 0.10, cd_03: 0.30, cd_04: 0.30, cd_05: 0.10`.
- Example for a fintech challenger: `cd_01: 0.20, cd_02: 0.25, cd_03: 0.15, cd_04: 0.05, cd_05: 0.35`.

### `contrarian_belief` (optional but recommended)
- Free-text. The thing this brand believes that 90% of its category competitors do not.
- Example: "A coffee brand believing that the *atmosphere* matters more than the cup."
- Used by Firaasa Architect (CD-01) routing to elevate this brain when present.

### `single_word_positioning`
- Enum: `Authentic` / `Innovative` / `Heritage` / `Disruptive` / `Refined`
- The one word that, if removed, the brand would not be itself.

## How data flows in

1. Onboarding Q1–Q15 (Pipeline A) or Q1–Q60 (Pipeline B) collects the raw signals.
2. COO `build_branddna` maps the answers to `cd_routing_weights` using a deterministic rubric (see `enhanced_onboarding/pipeline_a_intake_flow.md`).
3. `primary_cd_brain` = argmax of the weights, unless explicitly chosen by client.
4. `contrarian_belief` comes from Q10 (Pipeline A) or Q14 (Pipeline B) — never inferred.

## How it's used at generation time

For each brief:
1. CD-Brain Router computes per-brain scores using L1 weights × brain.sector_affinity × occasion factor.
2. Primary brain (and possibly secondary via Two-CD Diagnostic) is selected.
3. The CD brain's methodology — diagnostic question, signature technique, voice register — flows into the CaptionContext that DeepSeek reads.

## Example values per sector

| Sector | Common L1 lead | Typical weights pattern |
|---|---|---|
| F&B (heritage Najdi café) | cd_03 + cd_04 | Authenticity + Heritage skew |
| F&B (modern QSR chain) | cd_02 + cd_05 | Metaphor + Paradox skew |
| Retail (luxury) | cd_01 + cd_04 | Firaasa + Heritage skew |
| Retail (Vision-2030 modern) | cd_02 + cd_05 | Metaphor + Paradox skew |
| Beauty (heritage perfume) | cd_03 + cd_04 | Authenticity + Heritage skew |
| Real Estate (mega-development) | cd_01 + cd_04 | Firaasa + Heritage skew |
| Healthcare | cd_01 + cd_03 | Firaasa + Authenticity skew (paradox excluded by sector lock) |

## Anti-patterns

- Picking `cd_05` (Paradox Hunter) for healthcare brands — excluded by the router's sector safety lock regardless of weight.
- Setting all 5 weights to 0.20 — produces no signal; router defaults to alphabetical tie-break (cd_01 wins everything). Bad signal.
- Skipping `contrarian_belief` — losing the strongest single input the Firaasa Architect uses.

## Updates

Weights evolve through real client outcomes. The Learning Agent (Sundays 02:00 Riyadh) proposes weight updates based on engagement data; Mohamed or strategist approves before merge.
"""

L2_VOICE = FRONT("Layer 2 — Voice") + """# Layer 2 — Voice

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
"""

L2_VOICE_EXAMPLES = FRONT("Voice examples per sector") + """# Voice Examples per Sector

Curated calibration examples. Each sector × register combination gets 3 love-lines and 3 hate-lines that the CCO can use as starting calibrations when a brand has insufficient onboarding data.

## F&B — Warm-conversational (Najdi default)

**Love (3):**
- "صباحك قهوة. اليوم خاص"
- "حدّك تجلس، نحن نتعب لك"
- "نص اللذة في الجلسة، النص الثاني عندنا"

**Hate (3):**
- "خصم 50% — لفترة محدودة!"
- "أفضل قهوة في الرياض"
- "اطلب الآن ولا تفوت الفرصة"

## Retail — Practical-direct (mixed Najdi/MSA)

**Love (3):**
- "ما نقولك لازم تشتري. نقولك جربه"
- "هذي الموديل اللي يدوم"
- "الجودة، بدون كلام كثير"

**Hate (3):**
- "حصرياً عبر متجرنا"
- "اكتشف سحر تصميمنا الفاخر"
- "بأسعار لا تقاوم!"

## Beauty — Nurturing-confident (Najdi default, modesty-high)

**Love (3):**
- "البساطة في الاهتمام"
- "ما هو من المكوّنات الباهظة. من الاستمرار"
- "هذا الزيت، من أمي"

**Hate (3):**
- "أحدث صيحات الجمال"
- "تخلصي من العيوب بكبسة زر"
- "للنساء الجريئات"

## Real Estate — Aspirational-trustworthy (mixed dialect, MSA-tolerant)

**Love (3):**
- "بيت تكبر فيه العائلة، بيت تكبر فيه الذكريات"
- "هذي المساحة بنيناها على فكرة بسيطة: العائلة أولاً"
- "نصمم على راحتك، ما نصمم لإعجاب الكاميرا"

**Hate (3):**
- "استثمار مضمون العائد"
- "أرقى المشاريع في المملكة"
- "فرصة لن تتكرر — احجز الآن"

## Healthcare/Wellness — Calm-reassuring (MSA with dialect layer)

**Love (3):**
- "نشرح بهدوء. ونعطيك وقتك"
- "ما عندنا وعود سريعة. عندنا متابعة طويلة"
- "هذي العيادة بنيناها لك، مش لنا"

**Hate (3):**
- "نتائج فورية!"
- "العيادة الأولى في الرياض"
- "تخلصي من المشكلة بزيارة واحدة"

## Notes

These are seed v1 — calibrated to feel right per sector and verify CCO doesn't drift. They are NOT examples to copy. They are examples to compare against. Real brand love-lines come from each brand's onboarding.
"""

L3_VISUAL = FRONT("Layer 3 — Visual Identity") + """# Layer 3 — Visual Identity

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
"""

L3_COLOR_EXT = FRONT("Color extension rules") + """# Color Extension Rules

The brand's primary and secondary colors must extend into neutrals (greys, off-whites, near-blacks) that read as "part of the same brand family" even when used 80% of the time without the primary present.

## Rules per primary-color family

| Primary family | Allowed warm neutrals | Allowed cool neutrals | Forbidden neutrals |
|---|---|---|---|
| Reds / Oranges (warm) | warm beige, cream, soft tan, charcoal-warm | none (cool grey reads off-brand) | pure white, ice grey |
| Greens (cool) | none (warm beige reads off-brand) | soft sage, mint-white, slate-grey | cream, warm beige |
| Blues (cool) | none | soft sky-grey, sand-grey-cool, slate | cream, warm tan |
| Purples / Magentas | warm beige (low saturation) | soft mauve-grey | bright white, cool blue-grey |
| Yellows / Golds (warm) | warm beige, cream, off-white | none | cool grey, ice |
| Browns / Earth-tones | warm beige, cream, tan, charcoal-warm | none | cool grey, bright white |
| Pinks / Coral | warm cream, soft tan, gold | none | cool grey, slate |

## Rules per brand register

- **Heritage register**: neutrals lean warm (cream, beige, off-white). Cool neutrals read modern, disrupting heritage feel.
- **Modern / Vision-2030 register**: neutrals can be cool (slate, sand-grey, ice-cream). Warm neutrals read traditional.
- **Premium register**: high-contrast neutrals — deep charcoal + crisp cream. Avoid mid-tone greys (read corporate).
- **Energetic / youth register**: tinted neutrals (lavender-tinted grey, peach-tinted cream). Pure neutrals read corporate.

## Usage percentages

Typical fingerprint:
- Primary brand color: 25-35% of visual frame
- Secondary color: 10-15%
- Neutrals (3 shades): 50-60%
- Accent (sparingly): <5%

## How CCO checks

When CCO scores a brand's generated content, palette discipline is one of the inputs (not as strict as forbidden gestures, but contributes to the score). Visible 5+ color palette = score deduction.
"""

L4_CINE = FRONT("Layer 4 — Cinematography") + """# Layer 4 — Cinematography

**Schema fields:** `lighting_style`, `lighting_direction`, `key_fill_ratio`, `focal_length`, `depth_of_field`, `camera_height`, `camera_angle`, `sensor_look`, `motion_grammar`, `signature_camera_move`, `color_grade_lock`, `first_frame_category`, `last_frame_category`.

## Purpose

Layer 4 is the lens grammar of the brand. It governs video generation in particular but also informs static photography for hero shots.

This layer is where craft credibility lives. A brand can have great strategy (L1), great voice (L2), great visual identity (L3) — but if every video feels like stock B-roll, the brand's craft signature is missing.

## Lighting

- **Lighting style**: golden-hour-natural / soft-diffused-studio / hard-key-cinematic / window-side-natural / overhead-product-studio
- **Lighting direction**: side / back / overhead / front (front kills depth — avoid for hero)
- **Key/fill ratio**: 4:1 (high contrast, drama) / 2:1 (balanced) / 1:1 (flat, soft)

## Lens grammar

- **Focal length**: 35mm / 50mm / 85mm / 100mm macro / 16-35mm wide / 24-70mm zoom
- **Depth of field**: shallow (subject sharp, BG creamy) / medium / deep (everything sharp)
- **Sensor look**: cinematic-S35 / digital-clean / film-emulation / smartphone-realistic

## Composition motion

- **Camera height**: ground / waist / eye-level / overhead-tabletop
- **Camera angle**: dead-on / slight-elevation / dutch (avoid unless youth-edgy brand)
- **Motion grammar**: handheld / gimbal-smooth / push-in / pull-out / dolly-side / static-locked
- **Signature camera move**: the ONE move that says "this brand" (e.g., "slow gimbal push toward product" or "static-locked with subject motion blur").

## Cut + grade

- **Color grade lock**: golden-warm / cool-cinematic / neutral-clean / vintage-film / contrasty-bold
- **First frame category**: face / hands / product / environment / typography (what the video opens on every time)
- **Last frame category**: same options — what it closes on

## Per-CD-brain biases

| CD Brain | Lighting preference | Motion preference |
|---|---|---|
| Firaasa | golden-warm cinematic | static-locked with breathing-room |
| Metaphor | soft-diffused with one motion-blur layer | the still-figure-motion-blur signature |
| Authenticity | window-side natural | handheld (subtle) |
| Heritage | golden-warm with hard-key on heritage objects | unhurried push-in |
| Paradox | hard-key cinematic | quick punctuated cuts; product-as-mechanism reveal |

## How data flows in

- Onboarding Q11-Q12 (Pipeline A) or Q23-Q28 (Pipeline B): style references + grade samples.
- Instagram scrape: COO infers brand's existing cinematography from posted videos.
- CCO refines after each video — actual outputs are checked against L4 lock; drift triggers re-tune.

## How it's used at generation time

- COO passes L4 fields into fal.ai video chain prompts as control parameters.
- Signature camera move is locked: every brand video uses it at the hero moment.
- Color grade lock controls the post-generation grading pass.

## Anti-patterns

- Mixing handheld AND gimbal-smooth in the same video: reads inconsistent. Pick one or stage explicitly.
- Dutch angle unless brand is edgy-youth: looks amateur.
- Overhead-product-studio for lifestyle: kills the warmth.
"""

L5_LOOK = FRONT("Layer 5 — Look & Feel") + """# Layer 5 — Look & Feel

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
"""

L6_PROD = FRONT("Layer 6 — Production Signature") + """# Layer 6 — Production Signature

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
"""


# ───────────────────────────────────────────────────────────────────────────
# Enhanced onboarding (4 files)
# ───────────────────────────────────────────────────────────────────────────

ONB_15Q = FRONT("Pipeline A — 15-Question Critical Starter") + """# Pipeline A — 15-Question Critical Starter Intake

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
"""

ONB_60Q = FRONT("Pipeline B — 60-Question Full Intake") + """# Pipeline B — 60-Question Full Intake

The complete onboarding form for Growth and Enterprise tiers. Covers all 6 layers fully + strategist involvement points + extensive references.

Target completion time: 25-40 minutes across 2 sessions (with strategist guidance).

## Section structure

### Section 1: Identity + sector (Q1-Q8) — covers L0 basics + Pipeline A Q1-Q3
1. Legal brand name + trade name
2. Year founded
3. Sector + sub-sector
4. Cities of operation
5. Number of branches / employees / users
6. Languages served
7. Saudi vs. regional vs. international scope
8. Commercial / NGO / Government

### Section 2: Layer 1 — Strategy (Q9-Q18)
9. What does your brand do that 90% of competitors do NOT?
10. Single-word positioning (Authentic / Innovative / Heritage / Disruptive / Refined)
11. Primary CD methodology preference (or "let the system decide")
12. CD routing weights — 5-slider input
13. The contrarian belief (free text, min 50 chars)
14. Brand's biggest strategic challenge in 2026
15. Brand's stated KPIs (3 priority)
16. Quality tier choice (Growth / Enterprise)
17. Monthly content volume target
18. Brand maturity self-assessment

### Section 3: Layer 2 — Voice (Q19-Q28)
19. Voice triangle — formal_colloquial slider
20. Voice triangle — warm_cold slider
21. Voice triangle — confident_humble slider
22. Three love-lines — paste 3 examples of writing the brand would do
23. Three hate-lines — paste 3 examples the brand would NEVER do
24. Arabic dialect (with regional auto-suggest)
25. MSA tolerance
26. Emoji density preference
27. Hashtag style
28. Codeswitch tolerance (English mixing into Arabic)

### Section 4: Layer 3 — Visual Identity (Q29-Q38)
29. Primary brand color (color picker + hex override)
30. Color philosophy — why this color (one sentence)
31. Secondary color
32. Accent colors (up to 3)
33. Arabic typeface
34. English typeface
35. Logo placement preference
36. Logo sizing preference
37. Reference visual locks — upload up to 5 reference images
38. Negative-space preference

### Section 5: Layer 4 — Cinematography (Q39-Q46)
39. Lighting style preference
40. Lighting direction preference
41. Lens / focal length preference
42. Depth of field preference
43. Camera height preference
44. Motion grammar preference
45. Signature camera move — describe one move that should always appear
46. Color grade lock

### Section 6: Layer 5 — Look & Feel (Q47-Q53)
47. Mood lexicon — 10-20 words (chip-input with suggestions)
48. Reference brand anchors — up to 5 brands (with what-similarly / what-differently)
49. Audience emotional state lock — one sentence
50. Saudi cultural dimension
51. Taboo proximity
52. Tradition vs. modernity balance %
53. Regional specificity

### Section 7: Layer 6 — Production Signature (Q54-Q60)
54. Talent archetype
55. Talent consistency model
56. Primary location aesthetic
57. Hero prop description
58. Secondary props (up to 5)
59. Wardrobe palette
60. Signature ritual — one sentence describing the recurring action

## Strategist involvement

A strategist (human) joins the brand at:
- Section 2 (Layer 1 Strategy) — 30-min call to validate cd_routing_weights and contrarian belief
- Section 6 (Layer 5 Look & Feel) — 30-min call to validate mood lexicon + reference brand anchors
- Final review — 60-min call to validate the complete fingerprint before activation

## Confidence scoring

Every Pipeline B field is `explicitly_confirmed` after strategist review. The fingerprint is sealed when the final-review call concludes.
"""

ONB_FLOW_A = FRONT("Pipeline A — Operational Intake Flow") + """# Pipeline A — Operational Intake Flow

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
"""

ONB_FLOW_B = FRONT("Pipeline B — Operational Intake Flow") + """# Pipeline B — Operational Intake Flow

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
"""


# ───────────────────────────────────────────────────────────────────────────
# Distinctiveness scoring (2 files)
# ───────────────────────────────────────────────────────────────────────────

DIST_SCORE = FRONT("Brand Fingerprint Distinctiveness Score Spec") + """# Brand Fingerprint Distinctiveness Score

A single 0-1 score per brand measuring how distinct that brand's fingerprint is from its sector mean. Higher = more distinctive; lower = more sector-conventional.

## Formula

```
distinctiveness_score = 1.0 - avg_cosine_similarity_to_sector_peers
```

Where:
- The brand's fingerprint is vectorized (concatenating numeric fields + embedding categorical fields).
- We compute cosine similarity to every other brand in the same sector.
- We average across those similarities.
- Subtract from 1.0.

## Vectorization

- L1 numeric fields: `cd_routing_weights` (5 dim) + voice triangle (3 dim) = 8 dim
- L3 numeric: primary_color hex → HSL (3 dim) + usage_pct (1 dim) = 4 dim
- L5 numeric: tradition_modernity_balance (1 dim) + each cultural_resonance field tokenized = ~5 dim
- Categorical fields: embedded via OpenAI embeddings text-embedding-3-small (1536 dim per field)
- Mood lexicon: embedded as concatenated text (1536 dim)
- Reference brand anchors: not vectorized (internal-only, not used for distinctiveness)

Total vector dimension: ~3000 (numeric + embeddings).

## Thresholds

- **< 0.30** — Urgent. Brand is highly conventional for its sector. Surface alert to brand: "Your fingerprint is very similar to other brands in your sector. Consider strengthening your contrarian belief or unique reference locks."
- **0.30 – 0.60** — Acceptable. Brand is distinguishable but not differentiated. Surface as advisory.
- **> 0.60** — Excellent. Brand has a clearly distinct posture in its sector.

## Computation cadence

- Initial: computed when brand fingerprint is sealed (post-onboarding).
- Updated: monthly batch (Sunday 02:00 Riyadh) when any fingerprint changes are merged.
- Surface: `current_score`, `sector_average`, `last_computed` in the brand's `distinctiveness` block.

## Implementation

- Backend (runtime, not this repo): Postgres + pgvector for similarity computation.
- The materialized view `brand_distinctiveness_view` exposes current scores per brand for dashboard reads.
- See `13_database/migrations/0003_materialized_views.sql` for view definition.

## How the score is used

- **Brand dashboard:** surfaced to brand as a single number ("Your distinctiveness: 0.42 — sector median 0.38").
- **CD-Brain Router (indirect):** if score drops below 0.30, the router applies a "distinctiveness boost" — slight bias toward less-frequently-routed brains for this brand's briefs.
- **Anti-convergence monitor (companion file):** triggers proactive alerts.

## What it does NOT do

- It's not a quality score. A brand can have low distinctiveness and high content quality.
- It's not a similarity-to-best-performer score. It measures distance from the sector mean, not distance from sector leader.
- It's not a brand-strength score. It's a brand-individuality score.
"""

ANTI_CONV = FRONT("Anti-Convergence Monitor") + """# Anti-Convergence Monitor

Operational spec for detecting and addressing brand drift toward the sector mean over time.

## What drift looks like

Over months of operation, a brand's actual published content can drift away from its onboarded fingerprint:
- The brand picks the same chain repeatedly because it engages best, narrowing its visual range
- CCO scores tone-conservative outputs higher, slowly muting the brand's contrarian voice
- The CD-Brain Router increasingly picks the same brain because the sector-affinity heuristic dominates
- Production signature ritual slips away as different talent rotates in

Result: distinctiveness score declines over 3-6 months, and the brand's content starts to look like its sector peers.

## How the monitor works

### Daily signal
- Each post published is vectorized (caption + image embedding).
- Cosine similarity to brand's onboarded fingerprint vector is computed.
- If similarity > 0.92, flag as "drifting-near-mean" (post is generic for the brand).
- If similarity < 0.65, flag as "outlier" (post is off-brand).

### Weekly aggregation
- Sunday 02:00 Riyadh: Learning Agent reviews the past 7 days of published posts per brand.
- Computes 7-day moving average of similarity-to-fingerprint.
- Compares to 4-week moving average.

### Alert triggers
- **Yellow alert:** 7-day average ≥ 0.05 above 4-week average. Notify strategist + brand: "Your content has been more conventional this week."
- **Red alert:** 7-day average ≥ 0.10 above 4-week average for 2+ consecutive weeks. Auto-route next 3 posts through Cultural Advisor for rebalancing.
- **Critical alert:** brand's distinctiveness score has dropped below 0.30 from previous threshold. Trigger fingerprint review.

### Response actions

| Alert | Auto-action | Human action |
|---|---|---|
| Yellow | Surface advisory in dashboard | Optional: strategist outreach |
| Red | Route next 3 hero posts to Cultural Advisor | Strategist call to brand within 5 business days |
| Critical | Pause auto-generation for hero content | Cultural Advisor + Mohamed jointly review fingerprint |

## What the monitor does NOT do

- It doesn't force brands to be more distinctive than they want.
- It doesn't override brand explicit rejections.
- It surfaces the drift; the brand decides whether to act.

## Implementation

- Embeddings + cosine: pgvector in Postgres.
- Aggregation: daily materialized view `brand_drift_signals_view`.
- Alerts: Learning Agent (Sundays); inline dashboard for daily signals.
- Cross-references: `brand_fingerprint_score_spec.md`, `13_database/migrations/0003_materialized_views.sql`.
"""


def main() -> int:
    print("═══ writing 5 layer specs ═══")
    write("layer_2_voice/voice_layer_spec.md", L2_VOICE)
    write("layer_2_voice/voice_examples_per_sector.md", L2_VOICE_EXAMPLES)
    write("layer_3_visual_identity/visual_identity_spec.md", L3_VISUAL)
    write("layer_3_visual_identity/color_extension_rules.md", L3_COLOR_EXT)
    write("layer_4_cinematography/cinematography_spec.md", L4_CINE)
    write("layer_5_look_and_feel/look_and_feel_spec.md", L5_LOOK)
    write("layer_6_production_signature/production_signature_spec.md", L6_PROD)
    # also Layer 1 (strategy) — it wasn't in the prompt explicitly but the schema needs it
    write("layer_1_strategy/strategy_layer_spec.md", L1_STRATEGY)

    print("\n═══ writing 4 enhanced-onboarding docs ═══")
    write("enhanced_onboarding/15_question_critical_starter.md", ONB_15Q)
    write("enhanced_onboarding/60_question_full_intake.md", ONB_60Q)
    write("enhanced_onboarding/pipeline_a_intake_flow.md", ONB_FLOW_A)
    write("enhanced_onboarding/pipeline_b_intake_flow.md", ONB_FLOW_B)

    print("\n═══ writing 2 distinctiveness-scoring docs ═══")
    write("distinctiveness_scoring/brand_fingerprint_score_spec.md", DIST_SCORE)
    write("distinctiveness_scoring/anti_convergence_monitor.md", ANTI_CONV)

    print(f"\nWrote 13 brand-fingerprint files to {ROOT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
