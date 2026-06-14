# OpenClaw · Master Prompt Library v3.7 — COMPLETE
**The full library aligned to the locked v3.7 canonical architecture**
**Coverage:** COMPLETE — all 94 chains in this file: the 18 tested foundational chains (TF01, TF02, TF05, F-GROUND — verbatim validated text from the Baja live-testing series) + the 76 chains rebuilt to v3.7 (TF03–TF04, TF06–TF23)
**Architecture:** v3.7 locked canonical — 15-block image · 5-block video · native-video block order for TF22
**Alignment authority:** OpenClaw v3.7 Canon & Retrofit Spec — every chain audited against the 14-point failure ledger
**Date:** 2026-06-11 · OGZ Studios LLC · Confidential

---

## Library map

| Batch | Families | Chains | Count |
|---|---|---|---|
| Tested 18 (INCLUDED — first section) | TF01 Product Hero · TF02 Splash & Motion · TF05 Hand & Human Touch · F-GROUND Saudi Environment | U01, T01–T07, H01–H04, G01–G06 | 18 |
| Batch 1 | TF03 Spotlight & Dark Stage · TF04 Natural Environment · TF06 Studio Production · TF07 Pastel & Shadow Play | T08–T16, T21–T27 | 16 |
| Batch 2 | TF08 Cinematic Environment · TF09 Portrait & Model · TF10 Editorial Poster · TF11 Texture & Macro · TF12 Active Product Moment | T28–T46 | 19 |
| Batch 3 | TF13 Lifestyle Context · TF14 Premium Pedestal · TF15 Promotional & Text · TF16 Occasion & Cultural · TF17 Before/After | U04, U05, F02, T47–T53, U02, F04, R03, U03, F03, B01, B02 | 17 |
| Batch 4 | TF18 Product Flat Lay · TF19 On-Model Apparel · TF20 Premium Fragrance & Packaging · TF21 Service CTA | B03, B05, R01, R04, R02, R05, F05, B04, U06 | 9 |
| Batch 5 | TF22 Video (Native) · TF23 Saudi UGC Authentic | V01–V05, S01–S10 | 15 |

## Global rules in force on every chain (v3.7 canon)
One hard light source (declared system exceptions documented per chain) · color fields brand-derived from {brand.color_field_palette}, never borrowed from references (occasion chains are the documented inversion: occasion palette leads) · scale proportion-anchored via {product.dimensions} · material truth via {product.material_texture} · one hero companion maximum (collections and composed spreads are documented structural exceptions) · neighboring objects carry no readable text · TEXT OVERLAY conditional except on text-central families (TF10, TF15, TF21, U05, U03) where TEXT is core and carries the Arabic rule · CREATIVE VARIANCE DIRECTIVE on every chain · no fixed mm / f-stop / Kelvin commands anywhere · multi-subject risk notes binding (S03, S07, S09, F03).

## Open dependencies (unchanged from the Canon & Retrofit Spec)
Four schema fields with Mohamed Rabie → JSON rebuild per chain_v1.schema.json · Arabic deterministic overlay node (Pillow + arabic-reshaper + python-bidi) → TF10/TF15/TF21 production use · Cultural Spec 80 fields → {saudi.*} runtime fills · 18-chain live-testing completion → scaling gate.

---
---


<!-- ══════════ TESTED 18 · openclaw_master_prompts_v3_7_platform (verbatim, validated via Baja live testing 2026-05-27) ══════════ -->

# THE TESTED 18 · Platform System Prompts — F1 · F2 · F5 · F-GROUND
**Confidential · v3.7 · Product-agnostic · Built for the platform, filled by the agent at runtime**

These are the canonical, reusable master prompts validated through five rounds of live Baja visual testing. Every `{placeholder}` is filled by the agent from the BrandDNA / Brief / Cultural Spec libraries at generation time. The structural language stays constant; only the placeholder values change per product. This version consolidates every architecture decision from the v3.2 → v3.7 testing series.

---

## Section A · Recap of the prompt needs (what these prompts must do)

**1. Identity locked, everything else open.** The reference image teaches *what the product is* (silhouette, wordmark, label, colors, material). It must never dictate composition. The model is free — and instructed — to choose camera angle, framing, placement, and lighting. The brand identity is invariant; the creative interpretation is not.

**2. Real creative variance across generations.** Each chain must produce genuinely different compositions run-to-run, not the same shot with a lighting tweak. Every chain ends with a CREATIVE VARIANCE DIRECTIVE listing what to vary and what to hold constant.

**3. Integration, not placement-on-top.** The product is *photographed inside* the scene, not pasted onto it. One light source governs product and environment together. The product picks up ambient color cast from its surroundings; its contact shadow agrees with the scene's other shadows.

**4. Natural placement over forced hero-posing (environmental chains).** In real-world scenes the product is placed by gravity — it may lie flat, lean, tilt, or sit propped. "Brand-readable face toward camera" is a *possible outcome*, never a forced pose. The metaphor: imagine the product was set down or tossed into the scene and you photographed where it landed.

**5. Honest scale.** The product is rendered at its true real-world size relative to its environment and to any companion objects. No giant floating hero. Scale is anchored to a known reference object where one exists (e.g. product-to-cup ratio).

**6. Hero through proximity, not dead space.** Natural placement must not drift into vast empty frames. The camera comes close enough that the product reads as the clear focal subject — it occupies a meaningful share of the frame at a strong compositional point — while staying realistically scaled.

**7. Companion elements, derived and restrained.** Every product lives in a "world" of related objects (coffee → finjan/dallah/beans/dates; cold drink → ice/citrus/condensation; fragrance → botanicals/box). The agent derives these and integrates ONE hero companion per environmental scene with natural physics. Never a garnish-scatter of many small props.

**8. Editorial graphic punch — chiaroscuro + brand-derived color blocking.** Hard directional light, deep shadow that cuts across the frame, a saturated color FIELD that makes the product pop. CRITICAL: the color field is derived from the brand's *own* palette or its culturally-grounded context — never an accent color borrowed from a reference. Extract the *principle* (a field that makes the product pop), fill it with *the brand's* colors.

**9. True material texture.** The product must read as its real material — for flexible-film packaging: pliable, pillowed by contents, matte-vs-gloss finish contrast, crinkled seal edges, faint environmental reflection. Never rigid, never plastic-perfect CGI. (This block adapts per material type via `{product.material_finish}`.)

**10. Per-chain calibration.** The levers above are dialed differently per chain: full editorial punch on bold lifestyle/splash chains; warm tungsten chiaroscuro on heritage chains; soft natural light on intimate chains; palette discipline (not full color-block) on busy retail chains; clean even light on catalog/silhouette chains.

**11. Conditional Saudi + text blocks.** Saudi cultural direction is parameterized via `{saudi.*}` and appended only when context matches. Text overlay is appended only when `brief.text_request` fires.

**12. Platform-agnostic placeholders.** Written for the system, filled per product. No product baked in.

---

## Section B · Placeholder taxonomy (v3.7)

### Brand-level (from BrandDNA)

```
{brand.name}                        {brand.palette.primary}
{brand.region}                      {brand.palette.background_tone}
{brand.sector}                      {brand.color_field_palette}        ← NEW v3.7
{brand.tone_register}               {brand.aesthetic.capture_character}
{brand.quality_tier}                {brand.anti_attributes}
{brand.price_position}
{brand.modesty_register}
```

### Product-level (from BrandDNA)

```
{product.name}                      {product.label_text_arabic}
{product.identity_dna}              {product.label_text_latin}
{product.silhouette_description}    {product.dimensions}               ← NEW v3.7
{product.material_finish}           {product.material_texture}         ← NEW v3.7
                                    {product.companion_elements}       ← NEW v3.7
```

### Brief-level (from generation request)

```
{brief.occasion}    {brief.intent}    {brief.platform}
{brief.text_request.copy}    {brief.text_request.style}    {brief.text_request.zone}
```

### Saudi cultural (from Cultural Spec library)

```
{saudi.scene_context}      {saudi.apparel_context}      {saudi.material_context}
{saudi.color_palette_adjust}    {saudi.occasion_overlay}
```

### The four new v3.7 fields explained

- **`{brand.color_field_palette}`** — the brand-derived saturated colors usable as background/surface color-fields for chiaroscuro blocking. Derived from brand palette + culturally-grounded context. Explicitly excludes colors foreign to the brand.
- **`{product.dimensions}`** — real-world size + a scale-anchor object (e.g. "≈10cm tall; a serving cup is ≈5-6cm, so product is ~1.5-2× cup height").
- **`{product.material_texture}`** — detailed material-truth description for the product's specific substrate (flexible film, glass, rigid carton, metal tin, etc.).
- **`{product.companion_elements}`** — the product's "world" of related objects + the restraint rule (one hero companion per scene).

### Companion-element derivation logic (agent-side, any product)

Every product belongs to a category "world." Derive 1-3 related objects; integrate ONE hero companion per environmental scene with natural physics:

- Coffee/tea → serving cup, pot, beans, dates, cardamom, steam
- Cold beverage → ice, condensation, citrus, frosted glass, mint
- Fragrance → the box, scent-matched botanicals, a vanity surface
- Sweets/chocolate → cocoa dusting, the unwrapped piece, nuts
- Skincare → water droplets, the hero ingredient, a folded towel
- Packaged food → the prepared dish, raw hero ingredient, utensil

### Color-field derivation logic (agent-side, any product)

When a chain calls for color-blocking, the field color comes from `{brand.color_field_palette}` — never an accent borrowed from a reference image. Extract the *principle* (a saturated field that makes the product pop via contrast or harmony); fill it with the brand's own colors. Exclude any color the brand's identity does not own.

---

## Section C · The shared architecture blocks (how each chain is built)

Every image prompt uses this block order. The bracketed blocks adapt per chain; the principles are constant.

1. **[BRAND LOCK · identity invariant, composition open]** — teaches identity via `{product.identity_dna}`; states that angle/framing/placement/light are creative decisions; carries the INTEGRATION principle.
2. **[REALISM & CAPTURE CHARACTER]** — `{brand.aesthetic.capture_character}` + `{product.material_texture}` material-truth.
3. **[SCALE CALIBRATION]** — `{product.dimensions}` + relationship to environment/companions.
4. **[FRAMING & PROXIMITY]** — hero-through-closeness; share-of-frame target; no dead space.
5. **[COLOR & CONTRAST]** — brand-derived color-field blocking (calibrated per chain).
6. **[LIGHT & LENS]** — mood/intent, not fixed spec; chiaroscuro calibrated per chain.
7. **[NATURAL PLACEMENT]** *(environmental chains)* — gravity-placed orientation. *(Studio chains use a hero-framing line instead.)*
8. **[COMPANION ELEMENTS]** *(where relevant)* — one hero companion, restrained.
9. **[SCENE]** — the creative seed + the model's choice points.
10. **[SUBJECT]** — what's in frame + physical truth.
11. **[BRAND CONSTRAINTS]** — `{brand.anti_attributes}` + chain-specific limits.
12. **[OUTPUT]** — grade, resolution, exclusions.
13. **[SAUDI ADAPTATION — conditional]** — `{saudi.*}`, appended when context matches.
14. **[TEXT OVERLAY — conditional]** — appended only when `brief.text_request` fires.
15. **[CREATIVE VARIANCE DIRECTIVE]** — what to vary, what to hold constant.

Video prompts use: **[STARTING IMAGE HOLD]** → **[MOTION]** → **[WHAT STAYS STATIC]** → **[PACING & DURATION]** → **[OUTPUT]**.

---

# FAMILY F1 · TF01 — Product Hero (Clean)

*3 chains · U01, T01, T02 · Sectors: F&B, Retail, Beauty, Home, Fitness · Quality tier: universal*

---

## Chain U01 · Product Hero Static

```
FAMILY        TF01 · Product Hero (Clean)
SECTORS       F&B, Retail, Beauty, Home, Fitness
QUALITY TIER  universal
INTENT        launch, grow, harvest
REFERENCE     Recommended
FREQUENCY    3-5× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (limit 8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (limit 2,500 chars)
REF ACCOUNTS  @barnscoffee, @tiadress, @danatreasures
CULTURAL SPEC CS-22 photography angles, CS-24 women framing by tier
WHEN TO USE   Catalog backbone. E-commerce listings, marketplace grids, product pages — anywhere SKUs must look
              uniform and clean. Not a hero/marketing chain (use T01, T03, T07 for hero).
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — camera angle, framing, and lighting are creative decisions, not copies of the reference photo.
Identity DNA — preserved at any angle: {product.identity_dna}
INTEGRATION: The same studio light defines backdrop and product. The product picks up subtle ambient cast at its edges; its contact shadow flows onto the backdrop with the same direction and softness as any shadow in the frame.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio for catalog. Reads as captured on a medium-format digital back, high-end commercial grade. Material truth: {product.material_texture}. Imperfections are part of realism — genuine micro-reflectance, honest shadow-to-highlight temperature shift, true material behavior. Sharpness reads mechanical-optical, never algorithmically over-sharpened. No CGI-clean perfection, no plastic uniformity.

[SCALE CALIBRATION]
{product.dimensions}. As the sole catalog subject the product fills the frame at honest packaging scale — never distorted larger for emphasis.

[FRAMING & PROXIMITY]
Catalog hero proximity. Product occupies ~55% of frame height at a strong compositional point with deliberate negative space. Reads as a flagship catalog cover — confident, uncluttered.

[COLOR & CONTRAST · brand-derived]
Clean editorial palette anchored to {brand.palette.primary} against a {brand.palette.background_tone} backdrop. No colors foreign to the brand, no clinical pure white unless the brand owns it, no competing accents. {brand.anti_attributes}

[LIGHT & LENS · dimensional, mood not spec]
Premium catalog lighting — controlled, dimensional. Model chooses key direction, light quality (soft to semi-hard), fill ratio, and rim. Reveal the product's material truth and let {brand.palette.primary} read cleanly. Cleaner than the dramatic chains — the catalog needs full legibility — but never flat. Lens: model chooses macro intimacy to natural product perspective; depth from full-sharp to gentle falloff.

[SCENE · creative seed]
Present the product as the absolute hero of a clean premium frame — flagship catalog energy. Model chooses: camera angle (low-three-quarter, eye-level front, high-angle three-quarter, near-profile); placement (centered with negative space, rule-of-thirds, low-anchored); backdrop treatment (flat seamless, gradient falloff, subtle backlit glow) — all within the {brand.palette.background_tone} range.

[SUBJECT]
Single product as absolute subject, rendered to printed-catalog fidelity. No secondary elements.

[BRAND CONSTRAINTS]
Single product only, never duplicated, mirrored, or composited. No human elements — no hands, faces, limbs, silhouettes. Clean unbroken backdrop, no props. Colors true without oversaturation. No cartoon/illustration/stylized rendering. {brand.anti_attributes}

[OUTPUT]
8K photoreal commercial product photography. Editorial grade anchored to {brand.palette.primary}. No overlay text, no watermark, no logo other than the product's own. No human presence. No borders, frames, or UI.

[SAUDI ADAPTATION — conditional, agent appends if context matches]
{saudi.scene_context} — for catalog, adaptation is usually minimal. {saudi.color_palette_adjust} may warm the backdrop toward gold/sand/amber for fragrance/oud/luxury sectors. For Premium+ during {saudi.occasion_overlay}: subtle gold particle haze in the upper third.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, color contrasting against backdrop. Integrates as intentional design. If brief.text_request is absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Across generations, vary camera angle, placement, light direction, backdrop treatment, depth of field. Hold constant: brand-derived palette, clean catalog legibility, material texture. Each render a fresh catalog interpretation, never a fixed canonical shot.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
The starting image is immutable ground truth. Every frame preserves the product exactly: silhouette, proportions, label position, all label color values, every Arabic character ({product.label_text_arabic}) and Latin character ({product.label_text_latin}) character-perfect, logo marks, graphic elements, material finish. The product does not change shape, rotate, drift, or distort. Only the camera moves.

[MOTION]
Subtle gimbal-stabilized dolly slowly forward, ~8% closer over the full duration. Smooth mechanical pacing — no handheld shake, no wobble. Product stays centered. Natural light shifts 10-15% in directional warmth as the dolly progresses, suggesting a real photographic moment.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish, background tone — all locked. Capture character {brand.aesthetic.capture_character} preserved every frame — no synthetic grain, no rolling shutter, no fake shake.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts, no transitions.

[OUTPUT]
8K photoreal product cinematography. Silent — no audio. No text overlay, no watermark.
```

---

## Chain T01 · Floating Product Levitation

```
FAMILY        TF01 · Product Hero (Clean)
SECTORS       F&B, Retail, Beauty, Home, Fitness
QUALITY TIER  universal → premium
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee, @danatreasures
CULTURAL SPEC CS-19 incense/atmosphere, CS-22 photography angles
WHEN TO USE   Premium launch reveal. Hero shots, announcement posts, anything needing weightless prestige.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — float angle, framing, and lighting are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The product is suspended within the scene's atmospheric volume, not floating on a flat backdrop. The gradient wraps three-dimensionally; deeper tones cast subtle reflection onto the product's edges; atmospheric particles share the same light source.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, broadcast_cinematic grade. Material truth: {product.material_texture}. The product reads as physically present in space, not a 3D render composited onto a background. No CGI-clean perfection, no artificial floating glow.

[SCALE CALIBRATION]
{product.dimensions}. As the sole suspended subject it occupies ~60% of frame height at honest scale.

[FRAMING & PROXIMITY]
Premium hero proximity. Product ~60% of frame with strong negative space — intimate, not a vast empty void.

[COLOR & CONTRAST · brand-derived]
Deep {brand.palette.background_tone} gradient field, wrapping to darker edges. Anchored to {brand.palette.primary}. Color-field drawn from {brand.color_field_palette}. No colors foreign to the brand, no clinical tones.

[LIGHT & LENS · dramatic, mood not spec]
Cinematic premium light — singular, directional, with rich shadow falloff suggesting altitude. Model chooses key direction (upper angles for the float), rim placement (warm back-right, amber back-left, or top halo), atmospheric particles. The primary brand color catches a bright rim highlight. Deep rich shadow on the lower third for dimensional weight. Lens: portrait compression or near-macro; model chooses backdrop fall depth.

[SCENE · creative seed]
A premium gravity-defying reveal with luxury-launch prestige. Model chooses: float angle (vertical hover, forward tilt, three-quarter rotation, off-axis tilt); position (centered, off-center, slightly low); backdrop character (radial gradient, warm-dark wraparound, atmospheric haze, near-black void with localized pool).

[SUBJECT]
Single product defying gravity, part of the atmospheric volume. Full physical material truth.

[BRAND CONSTRAINTS]
Single product. No humans. No props. {brand.anti_attributes}

[OUTPUT]
8K photoreal commercial product photography. Editorial premium grade, rich blacks, controlled highlights. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional, agent appends if context matches]
{saudi.scene_context}. {saudi.color_palette_adjust} may warm the backdrop. Subtle gold/bukhoor-coded particles in the atmospheric volume permitted at premium register or during {saudi.occasion_overlay}.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary float angle, position, rim placement, particle density, backdrop gradient direction. Hold constant: brand-derived palette, dramatic single light, material texture. Each render a different premium moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. Only the camera and atmosphere move.

[MOTION]
Slow orbital drift around the suspended product, ~10-15 degrees over the duration, as if circling a weightless object. Atmospheric particles drift gently. The product rotates with the orbit only enough to stay naturally presented — it does not spin independently. Smooth, dreamlike pacing.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character {brand.aesthetic.capture_character} preserved every frame. No synthetic grain, no fake shake.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal product cinematography. Silent. No text overlay, no watermark.
```

---

## Chain T02 · Pure Product Silhouette *(LOCKED BY DESIGN)*

```
FAMILY        TF01 · Product Hero (Clean)
SECTORS       F&B, Retail, Beauty, Home, Fitness
QUALITY TIER  universal
INTENT        grow, harvest
REFERENCE     Recommended
FREQUENCY     as needed (catalog)
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @tiadress, @danatreasures
CULTURAL SPEC CS-22 photography angles
WHEN TO USE   Marketplace cutout. Product detail pages, comparison grids — anywhere uniform framing across SKUs
              matters more than creative variety. This chain is intentionally LOW-VARIANCE.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity AND composition locked by design]
The reference image teaches the {product.name} brand identity. This chain intentionally constrains composition — its purpose is uniform marketplace presentation where many SKUs must look identical in framing.
Identity DNA: {product.identity_dna}
INTEGRATION: The soft contact shadow flows from the product onto the backdrop seamlessly — the product sits ON the surface. Diffused light wraps the edges without a visual line between product and backdrop.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio, photoreal. Material truth: {product.material_texture}. (Texture is the one element that carries full v3.7 detail here; everything else stays marketplace-clean.)

[SCALE CALIBRATION]
{product.dimensions}. Occupies 60% of frame height — marketplace standard.

[FRAMING & PROXIMITY — LOCKED]
Product centered, front-facing, perfectly squared to camera, 60% frame height, symmetric negative space. Locked for marketplace uniformity.

[COLOR & CONTRAST — LOCKED]
Single clean field — warm-tinted off-white (#F8F5F0), not clinical pure white. Product colors true. No gradient, no environmental color, no foreign accents.

[LIGHT & LENS — even, LOCKED]
Even diffused upper-front softbox at neutral 5000K, minimizing harsh shadow on the product while preserving a soft contact shadow falling lower-right. 50% low-front fill. 85mm-equivalent, deep depth. Camera eye-level, perfectly squared. Functional, not dramatic.

[SCENE]
Pure silhouette — locked. Product centered on warm off-white, single soft elongated contact shadow lower-right at low opacity, generous symmetric negative space.

[SUBJECT]
Single product, isolated silhouette. Label text readable, edges crisp, colors accurate.

[BRAND CONSTRAINTS]
Single product. No humans. No props. Single off-white tone, no gradient. {brand.anti_attributes}

[OUTPUT]
8K photoreal e-commerce product photography. Clean warm-neutral grade. No overlay text, no watermark, no borders.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} may shift the backdrop fractionally warmer (toward #F5F0E8). Otherwise culturally neutral by design.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Intentionally low-variance. Only contact-shadow direction/softness varies subtly. Framing, light, and orientation stay consistent — marketplace uniformity is the brief.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. Only the camera moves.

[MOTION]
Minimal, locked-off feel: an almost imperceptible slow push-in (~5% over duration) on a perfectly squared product. No rotation. The clean even light holds steady. The restraint reinforces the marketplace-clean register.

[WHAT STAYS STATIC]
Everything except the subtle push: silhouette, label, color, logo, material, backdrop, even lighting — all locked. Capture character clean_studio preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal e-commerce cinematography. Silent. No text overlay, no watermark.
```

---
# FAMILY F2 · TF02 — Splash & Motion

*5 chains · T03, T04, T05, T06, T07 · Sectors: F&B, Beverage, Beauty · Quality tier: universal → premium*

---

## Chain T03 · Splash Ring Around Product

```
FAMILY        TF02 · Splash & Motion
SECTORS       F&B, Beverage, Beauty
QUALITY TIER  universal → premium
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     2-4× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-21 food/beverage cultural rules
WHEN TO USE   Dynamic hero for any pourable/drinkable/liquid-relevant product. High-energy launch and grow posts.
              The splash medium is derived from the product (water for cold drinks; brewed liquid for hot drinks; etc.).
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — splash composition, product angle, and light are creative choices.
Identity DNA: {product.identity_dna}
INTEGRATION: The product and the splash share one high-speed strobe event. Droplets cast colored reflection onto the product's nearest edges; the atmospheric haze between droplets and product shares the light volume; any suspended companion sits in the same focus plane.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed flash, photoreal. Material truth: {product.material_texture}. Droplets vary chaotically — some spherical, some elongating, some mid-deformation; authentic refraction and surface tension. No cartoon water, no over-stylized symmetric splash.

[SCALE CALIBRATION]
{product.dimensions}. Render any suspended companions (beans, fruit, garnish) at honest small scale relative to the product — accents, not oversized.

[FRAMING & PROXIMITY]
Hero proximity — product ~30-40% of frame at the centre of the splash ring, tight enough that the ring reaches the frame edges.

[COLOR & CONTRAST · brand-derived]
Deep {brand.palette.background_tone} radial field. Anchored to {brand.palette.primary}. The splash liquid's colour is derived from the product (cold/clear vs hot/amber vs the product's own liquid). Field colours from {brand.color_field_palette}. No colours foreign to the brand.

[LIGHT & LENS · dramatic, mood not spec]
Hard high-speed strobe energy. Model chooses key direction (side rake or top halo), rim placement and warmth matched to the product (warm rim for hot products, cool for cold), atmospheric haze. Deep radial backdrop fading toward black. The primary brand colour catches the strobe. Lens: macro for splash texture; aperture deep enough that ring and product stay crisp.

[SCENE · creative seed]
The product caught at its moment of action — a ring of its derived liquid frozen mid-motion around it, with optional derived companions suspended within. Model chooses: ring character (complete halo, crown arc, partial asymmetric, explosive scatter); companion positions; camera angle; product orientation within the splash.

[SUBJECT]
Liquid rendered true to the product — correct colour, true specular highlights, edge tension. The product stays dry — splash is around it, never on it.

[BRAND CONSTRAINTS]
Single product. No humans. Splash around, never on, the product. {brand.anti_attributes}

[OUTPUT]
8K photoreal high-speed product photography. Editorial grade toward {brand.palette.primary}. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context}. {saudi.material_context} supplies any culturally-specific companion (e.g. cardamom for Arabic coffee per CS-21). {saudi.color_palette_adjust} warms the rim. No alcohol cues; food/beverage rules per CS-21.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary ring shape/density, companion positions, product orientation, light direction, camera angle. Hold constant: brand-derived palette, product-matched liquid, dramatic strobe, material texture. Each render a different instant of the same action.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. The product stays dry and undistorted; only the splash and camera move.

[MOTION]
The frozen splash ring animates into life: liquid droplets pulse outward and fall with real gravity over the duration, the ring breathing once. A slow micro push-in on the product. The product itself never moves, rotates, or gets wet — the motion is entirely in the surrounding liquid.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character {brand.aesthetic.capture_character} preserved. No synthetic grain, no fake shake.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal high-speed cinematography. Silent. No text overlay, no watermark.
```

---

## Chain T04 · Beverage Pour Crown Splash

```
FAMILY        TF02 · Splash & Motion
SECTORS       F&B, Beverage
QUALITY TIER  universal → premium
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-18 serving vessels, CS-21 food/beverage rules
WHEN TO USE   "Product becomes the drink" reveal. The product is shown as the source, pouring into a derived serving vessel.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — pour angle, vessel placement, and lighting are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Product, pouring stream, and receiving vessel are one captured event under one warm backlight. Any surface beneath reflects tones onto both; the crown splash sits in the same atmospheric volume as the product.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed liquid, photoreal. Material truth: {product.material_texture}. Real flow physics, correct viscosity, honest refraction. No CGI water, no syrup-thick fakery.

[SCALE CALIBRATION]
{product.dimensions}. Render the product-to-vessel proportion honestly per the dimensions anchor.

[FRAMING & PROXIMITY]
Hero proximity — product, stream, and vessel fill the frame intimately, no dead space.

[COLOR & CONTRAST · brand-derived]
{brand.palette.background_tone} field. Anchored to {brand.palette.primary} + the derived liquid colour + the vessel. Field colours from {brand.color_field_palette}. No foreign colours.

[LIGHT & LENS · dramatic, mood not spec]
Warm backlit appetite drama — the liquid arc glows translucent. Model chooses key direction, backlight placement (rear-right, rear-left, full back-glow), surface-reflection strength. Hard enough to freeze droplets. Lens: macro for liquid texture, or natural-perspective showing product, arc, and vessel.

[SCENE · creative seed]
The product as the source, mid-pour into a derived serving vessel — the "product becomes the drink" reveal. Model chooses: product pour position (the opened edge as the stream origin); vessel placement; crown splash character (gentle ring, high crown, low ripple); surface (tray, wood, warm-dark void).

[SUBJECT]
Liquid rendered true to the product. The receiving vessel is the culturally/category-correct one. Product dry except where the pour connects at its opening.

[BRAND CONSTRAINTS]
Single source product. No human hands holding vessels — captured magic. Vessel is category-authentic. {brand.anti_attributes}

[OUTPUT]
8K photoreal high-speed liquid photography. Rich saturated grade toward {brand.palette.primary}. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.material_context} supplies the serving vessel (e.g. finjan + brass tray per CS-18). Pour may respect right-to-left serving convention per CS-21. {saudi.color_palette_adjust} warms the liquid. No alcohol cues.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary pour position, vessel placement, crown character, backlight direction, surface type. Hold constant: brand palette, backlit drama, material texture, honest product-to-vessel proportion. Each render a different pour instant.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. The product does not distort; only the pour and camera move.

[MOTION]
The pour stream flows continuously from the product's opening into the vessel; the crown splash rises and settles once over the duration; steam (if a hot product) drifts upward. A gentle push-in. The product holds its position and form throughout — only the liquid is alive.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character {brand.aesthetic.capture_character} preserved. No synthetic grain.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal high-speed cinematography. Silent. No text overlay, no watermark.
```

---

## Chain T05 · Ingredient / Aromatic Explosion *(restrained)*

```
FAMILY        TF02 · Splash & Motion
SECTORS       F&B, Beauty
QUALITY TIER  universal → premium
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     1-2× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-21 food/beverage rules
WHEN TO USE   "What's inside" reveal — the product surrounded by its derived hero ingredients in arrested motion.
              RESTRAINED: feature ONE lead ingredient, not a scatter of many.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — product orientation, ingredient arrangement, and lighting are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Product and ingredients share one captured moment under one warm key. Suspended elements tint the product's nearest edges; the dark atmosphere wraps the whole suspension as one volume.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed product-and-ingredient, photoreal. Material truth: {product.material_texture}. Each ingredient rendered as the real thing — honest texture, natural colour variation. No CGI ingredients, no plastic surfaces.

[SCALE CALIBRATION]
{product.dimensions}. Ingredients are small accents relative to the product — render the size relationship honestly, never oversized.

[FRAMING & PROXIMITY]
Hero proximity — product ~30-40% of frame, ingredients suspended close around it. Tight, not vast.

[COLOR & CONTRAST · brand-derived]
Deep {brand.palette.background_tone} field. Anchored to {brand.palette.primary} + the lead ingredient's colour. Disciplined to a few colours from {brand.color_field_palette}. No foreign accents.

[LIGHT & LENS · dramatic, mood not spec]
Dramatic strobe with warm appetite atmosphere. Model chooses key direction (upper angles to define every edge), warm fill, optional steam. Moody dark backdrop. Lens: macro intimacy.

[SCENE · creative seed]
The product as hero of its own ingredient moment — RESTRAINED. Model chooses ONE lead ingredient to feature (derived from the product) plus an optional splash arc — NOT all ingredients at once. A few suspended pieces of the lead ingredient, not a dense scatter. Model chooses explosion geometry (upward arc, radial, gentle mid-fall) and camera elevation.

[SUBJECT]
The lead ingredient (and optional splash), rendered true. Product is the absolute center; the lead ingredient orbits sparingly. Restraint over abundance.

[BRAND CONSTRAINTS]
Single hero product. ONE lead ingredient featured — never a scatter of many small props (it cheapens the frame). No human hands. {brand.anti_attributes}

[OUTPUT]
8K photoreal high-speed product photography. Rich warm grade, deep blacks. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.material_context} supplies culturally-correct ingredients (e.g. cardamom/saffron/dates for Arabic coffee per CS-21) — but ONE leads per render. No milk/sugar/Western decoration where culturally inappropriate. No alcohol, no pork.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary which single ingredient leads, explosion geometry, product orientation, camera elevation. Hold constant: restraint (one lead ingredient), brand palette, dramatic strobe, material texture. Each render features a different lead ingredient — never an overloaded scatter.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. Only the suspended ingredients and camera move.

[MOTION]
The suspended lead ingredient drifts and settles with gentle gravity over the duration; an optional splash arc completes its motion once. A slow push-in on the product. The product never moves or distorts — the life is in the floating ingredients.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character {brand.aesthetic.capture_character} preserved. No synthetic grain.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal high-speed cinematography. Silent. No text overlay, no watermark.
```

---

## Chain T06 · Ice Cube Cluster Embrace

```
FAMILY        TF02 · Splash & Motion
SECTORS       Beverage (cold), F&B
QUALITY TIER  universal
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     seasonal / cold-product lines
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-21 food/beverage rules
WHEN TO USE   Cold-refreshment hero. Best for genuinely cold/iced products. Conceptually mismatched for hot products —
              the agent should skip this chain when the product is a hot/warm item.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — cluster arrangement and lighting are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Ice cluster and product in one cold-volume event under one cool key. Condensation forms on both ice and product where they meet; the cool cast tints both equally.

[REALISM & CAPTURE CHARACTER]
Capture character: cold-product editorial, photoreal. Material truth: {product.material_texture} — plus real condensation beading where the cold meets the product surface. Real ice with angular fracture geometry, frost crystallization, melt-water. No CGI ice, no perfect geometric cubes.

[SCALE CALIBRATION]
{product.dimensions}. Render the ice cluster scaled honestly around the product.

[FRAMING & PROXIMITY]
Hero proximity — product ~30-40% of frame, cluster filling the immediate surround. Tight.

[COLOR & CONTRAST · brand-derived]
Cool-toned field with a {brand.palette.background_tone} undertone shifting cooler at the edges. Anchored to {brand.palette.primary}. (The one chain where a cool field is acceptable — it serves the cold concept.) No foreign warm accents.

[LIGHT & LENS · dramatic, mood not spec]
Cool cinematic with cold rim. Model chooses key direction (upper angles for ice facet definition), cool rim placement (back, side, top halo), vapour haze density. The primary brand colour still pops. Deep cool backdrop. Lens: macro or natural-perspective.

[SCENE · creative seed]
Cold-refreshment hero — the product embraced by an ice cluster. Model chooses cluster arrangement (wrapping the lower half, floating around, dense-behind/sparse-front, asymmetric) and frost vapour density.

[SUBJECT]
Single product embraced by ice. Real frost, refraction, melt-water. Condensation where temperature meets temperature.

[BRAND CONSTRAINTS]
Single product. No humans. Real angular ice. {brand.anti_attributes}

[OUTPUT]
8K photoreal cold-product photography. Cool-toned grade, controlled saturation, {brand.palette.primary} preserved sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context}. Faint warm-cool contrast (a warm desert tone at deep edges) reinforces cold-against-heat. The agent skips this chain for hot/warm products.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary cluster arrangement, ice angles/sizes, vapour density, light direction, camera height. Hold constant: material texture, cool drama. Each render a different cold moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. Only the ice, condensation, vapour, and camera move.

[MOTION]
Frost vapour curls upward gently; a single condensation droplet traces down the product surface; the ice settles almost imperceptibly. A slow push-in. The product stays locked in form and position.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character preserved. No synthetic grain.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal cold-product cinematography. Silent. No text overlay, no watermark.
```

---

## Chain T07 · Smoke Ring Mystique

```
FAMILY        TF02 · Splash & Motion
SECTORS       F&B (hot), Beauty, Fragrance, Luxury
QUALITY TIER  premium
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     1-2× per week / hero
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee, @danatreasures
CULTURAL SPEC CS-19 incense/bukhoor atmosphere
WHEN TO USE   Premium mystique hero. Hot drinks (steam/smoke), fragrance/oud (incense), luxury reveals.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — smoke pattern, product angle, and light atmosphere are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The product sits within a volumetric smoke atmosphere — the same warm light making the smoke translucent also catches the product's edges. The deep warm shadow defining the negative space is the same shadow defining the product's lower third.

[REALISM & CAPTURE CHARACTER]
Capture character: cinematic luxury, film_grain_warmth, photoreal. Material truth: {product.material_texture}. Real smoke — turbulent fluid dynamics, varied opacity, natural curls. Subtle film grain in shadow. No CGI smoke, no symmetric perfect curls.

[SCALE CALIBRATION]
{product.dimensions}. The product is the sole subject within the smoke at honest scale.

[FRAMING & PROXIMITY]
Hero proximity — product ~40-50% of frame, smoke curling in the immediate surround, deep shadow beyond.

[COLOR & CONTRAST · brand-derived]
Deep warm shadow field — {brand.palette.background_tone} fading to near-black. Anchored to {brand.palette.primary}. Field colours from {brand.color_field_palette}. No foreign accents.

[LIGHT & LENS · warm drama, mood not spec]
Warm cinematic key with strong back-rim — premium register. Model chooses key direction, back-rim placement and intensity (the rim making smoke translucent), shadow depth. The shadow cuts deep. The primary brand colour glows softly at the rim. Lens: portrait compression or near-macro.

[SCENE · creative seed]
Ceremonial mystique — the product within a slow vortex of smoke/incense. Model chooses: smoke flow (ring at midline, ascending vortex, lateral drift, dense-base thinning up); density (enveloping, medium, sparse wisps); product angle; optional single derived companion at the base if it enriches without cluttering; surface visibility (dark surface, tray edge, floating).

[SUBJECT]
Smoke rendered true — volumetric behavior, density variation, honest light scatter. Smoke around the product, never obscuring brand elements.

[BRAND CONSTRAINTS]
Single product. Optional single companion only. No humans. Smoke around, not on, the product. {brand.anti_attributes}

[OUTPUT]
8K photoreal luxury cinematography. Warm rich grade, deep blacks, {brand.palette.primary} with rim warmth. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context}. Smoke is authentic bukhoor/oud ceremony per CS-19 — NOT Western smoke, NOT shisha, NOT fog-machine. Subtle gold particles permitted at premium tier or during {saudi.occasion_overlay}.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary smoke flow, density, product angle, optional-companion presence, surface, rim direction. Hold constant: warm brand palette, deep shadow-cut, material texture. Each render a different ceremonial moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, proportions, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — preserved exactly. Only the smoke and camera move.

[MOTION]
The smoke curls and rises in a slow continuous vortex around the product; density shifts naturally; the back-rim catches the moving volume. A gentle push-in. The product holds form and position absolutely.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character {brand.aesthetic.capture_character} preserved. No synthetic grain.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal luxury cinematography. Silent. No text overlay, no watermark.
```

---
# FAMILY F5 · TF05 — Hand & Human Touch

*4 chains · H01, H02, H03, H04 · Sectors: F&B, Retail, Beauty · Quality tier: universal → premium* *Human presence is suggested through partial body cues — hands, wrists, sleeves. No faces.*

---

## Chain H01 · Hand & Product — Sky / Window Hero

```
FAMILY        TF05 · Hand & Human Touch
SECTORS       F&B, Beverage, Retail
QUALITY TIER  universal
INTENT        launch, grow
REFERENCE     Recommended
FREQUENCY     3-4× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-01 apparel, CS-06 accessories, CS-08 right-hand rules, CS-24 women framing by tier
WHEN TO USE   Everyday lifestyle hero — a hand holding the product against open sky / out of a car window. Universal,
              relatable, strong launch energy.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — hand pose, sky composition, and light angle are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Hand and product are one captured event under one light. The same light warms skin and product; the sky's gradient tints the product's upper edge; the sleeve fabric reflects faintly onto the product's lower edge.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, phone_natural with editorial lift, photoreal. Real skin — pores, natural undertone, knuckles, faint veins, real nail beds. Sleeve fabric drapes with honest weight. Material truth: {product.material_texture} — including faint sky reflection on any semi-gloss zones.

[SCALE CALIBRATION]
{product.dimensions}. The product sits naturally within a hand's grip at honest hand-to-product proportion.

[FRAMING & PROXIMITY]
Hero proximity — hand and product fill the upper-center third, sky filling the rest but kept intimate, not a vast empty void.

[COLOR & CONTRAST · brand-derived]
Saturated sky as the field — the {saudi.color_palette_adjust} sky tone (or brand-appropriate sky). Anchored to {brand.palette.primary} popping against the sky, with skin and sleeve as supporting tones. Field from {brand.color_field_palette}. No foreign accents.

[LIGHT & LENS · hard directional, mood not spec]
Hard directional golden-hour light with real clarity — defined enough to throw a clear shadow. Model chooses rake direction (upper-left, upper-right, or rim-lit from behind). POPPING COLOR INTENT: deep saturated sky, warm skin, product popping, {brand.palette.primary} as the chromatic anchor. Lens: natural phone-perspective; model chooses depth for hand vs sky.

[SCENE · creative seed]
A single hand raising the product into open sky — a window-down moment of personal ownership. Model chooses: hand position (overhead toward sky, mid-height center, low-and-forward, angled across frame); grip and product angle (fingers wrapped face-squared, thumb-forefinger pinch, fist-grip, relaxed cradle); sky composition (deep blue dominant, gold-blue horizon, sunset-pink, midday cobalt); context cue (car-door curve, window frame, side-mirror, near-absent); light angle.

[SUBJECT]
A single hand per {saudi.apparel_context} / {brand.modesty_register} — real skin texture, sleeve cuff at the wrist, optional accessory per CS-06. Right-hand grip preferred (CS-08). Confident but real, never modeling-stiff.

[BRAND CONSTRAINTS]
Single product. Only the hand — no full body, no face, no other people. Context suggested only. {brand.anti_attributes}

[OUTPUT]
8K photoreal editorial commercial photography. Warm grade, color pushed toward popping, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the cultural register. {saudi.apparel_context} fills the wrist/sleeve styling (e.g. white thobe cuff, Najdi cut). {saudi.color_palette_adjust} for the sky. Right-hand rule per CS-08. Women framing per CS-24 and {brand.modesty_register}. For {saudi.occasion_overlay}: light shifts to match the occasion.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary hand position, grip and product angle, sky composition, context cue, light direction. Hold constant: brand-derived sky field, hard golden-hour light, material texture, CS-08 grip. Each render a different ownership moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hand, product, sleeve fabric, accessories, sky gradient, context cue — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
Two layers: the hand holds steady with the faintest natural human micro-settle (not a shake); the sky and light shift subtly — clouds drift, warmth shifts 10-15% — as a real outdoor moment unfolds. A slow push-in. The product never rotates or distorts.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Hand pose and grip stable. Capture character {brand.aesthetic.capture_character} preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal lifestyle cinematography. Silent. No text overlay, no watermark.
```

---

## Chain H02 · Hand & Product — Cultural Moment

```
FAMILY        TF05 · Hand & Human Touch
SECTORS       F&B, Beauty, Luxury, Heritage
QUALITY TIER  universal → premium
INTENT        launch, grow, brand
REFERENCE     Recommended
FREQUENCY     1-2× per week / heritage campaigns
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @danatreasures, @barnscoffee
CULTURAL SPEC CS-01 apparel, CS-08 right-hand rules, CS-13 authentic-vs-Hollywood, CS-15 majlis, CS-18 vessels, CS-21 food rules
WHEN TO USE   Heritage moment — a hand holding the product beside authentic cultural elements. Warm, intimate. Best for
              heritage campaigns and occasion launches.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — gesture pose, cultural-element arrangement, and tungsten character are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Hand, product, and the cultural element share one warm tungsten-lit moment. Metallic/ceramic elements reflect warmth onto the product's nearest edges; tungsten tints the sleeve cuff, skin, product edge, and cultural objects equally; textile warm-gold threads rhyme with {brand.palette.primary}.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth heritage, photoreal, warm-toned film science, subtle warm grain in shadow. Real skin, honest material patina, authentic ceramic. Material truth: {product.material_texture}. No Hollywood-Middle-East gloss.

[SCALE CALIBRATION]
{product.dimensions}. Render the size hierarchy honestly among the product and its companions (per {saudi.material_context} object sizes).

[FRAMING & PROXIMITY]
Intimate hero proximity — product and the gesture fill the frame, the cultural element close, background falling deep.

[COLOR & CONTRAST · brand-derived + authentic heritage]
Warm tungsten field, plus authentic culturally-grounded tones from {saudi.material_context} (e.g. brass gold, Najdi textile deep reds — real heritage colours, not borrowed accents). Anchored to {brand.palette.primary} as the modern chromatic note.

[LIGHT & LENS · warm tungsten chiaroscuro, mood not spec]
Warm intimate tungsten — the quality of a cultural interior after sunset. Directional and moody with deep shadow in the negative space, but WARM and soft-edged, not hard editorial, so it reads as intimate. Model chooses key direction, fill from below (surface reflection), shadow depth. POPPING COLOR INTENT: rich warmth, metallic gleam, {brand.palette.primary} as the modern note. Lens: portrait compression; model chooses depth across the elements.

[SCENE · creative seed]
An intimate heritage moment — a hand interacting with the product beside authentic cultural elements. Model chooses: gesture pose (holding upright beside the element, mid-pass, lifting from beside it, resting in reverence); which element foregrounds; element count (RESTRAINED — never crowded); depth/focus.

[SUBJECT]
A hand per {saudi.apparel_context} / {brand.modesty_register} — sleeve cuff, optional accessory, right-hand grip (CS-08). Cultural elements authentic per CS-13 / {saudi.material_context}.

[BRAND CONSTRAINTS]
Single product. Cultural elements as singular supporting pieces — never multiples. Only the hand — no faces. Authentic per CS-13. No alcohol, no pork (CS-21). {brand.anti_attributes}

[OUTPUT]
8K photoreal heritage commercial photography. Warm rich grade, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets the register. {saudi.material_context} supplies the elements (majlis per CS-15, vessels per CS-18, dates per CS-21). {saudi.apparel_context} fills the cuff. Textile warm-gold thread rhymes with the brand colour. For {saudi.occasion_overlay}: deepen evening warmth (Ramadan) or add Saudi-green textile thread (Founding Day).

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary gesture pose, which element foregrounds, element count (restrained), hand position, depth of field. Hold constant: warm tungsten chiaroscuro, material texture, restraint, CS-08 grip. Each render a different heritage moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hand, product, sleeve, accessories, cultural elements, surface — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The hand holds the product with a slow, intentional settle as if presenting it; steam (if hot) or a candle flicker adds warm life; the tungsten light breathes subtly. A gentle push-in. The product never rotates or distorts.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Cultural elements stable. Capture character film_grain_warmth preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal heritage cinematography. Silent. No text overlay, no watermark.
```

---

## Chain H03 · Hand Reaching for Product (Shelf / Retail)

```
FAMILY        TF05 · Hand & Human Touch
SECTORS       Retail, F&B, Beauty
QUALITY TIER  universal
INTENT        grow, harvest
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-08 right-hand rules, CS-13 authentic retail
WHEN TO USE   Point-of-purchase moment — a hand selecting the hero product from a shelf of competitors. "Chosen one"
              energy. CRITICAL: surrounding products carry NO readable text (no fake brands).
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — shelf arrangement, hand entry, and POV are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Hero product, hand, and shelf are one captured shopping moment under shared retail light. The product picks up warm-overhead cast on top and cool shelf-depth cast on its sides; hand warmth and shelf packs share atmospheric continuity.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, broadcast_cinematic with editorial saturation, photoreal. Real shelf wear, price-rail smudges, real material variation on neighbors, honest retail color cast, natural skin texture. Material truth: {product.material_texture}.

[SCALE CALIBRATION]
{product.dimensions}. The hero product is the SAME physical size as the surrounding competitor packs — it stands out by position and light, NOT by being oversized.

[FRAMING & PROXIMITY]
Immersive POV proximity — hand and hero product fill the focal zone, shelf receding behind. Tight enough to feel the selection moment.

[COLOR & CONTRAST · disciplined, hero pops]
The surrounding shelf is a saturated rainbow of competing packs (the field is the retail chaos). The hero product pops with {brand.palette.primary} clarity by forward position and a slightly stronger key. Hero's own palette disciplined per {brand.color_field_palette}. No foreign accents on the hero.

[LIGHT & LENS · retail + hero key, mood not spec]
Retail lighting — warm overhead with cooler shelf-depth behind. Model chooses overhead placement, the warm/cool contrast ratio, and a stronger key on the hand-and-hero zone so it separates. (Can't fully shadow-cut — retail is bright — but push contrast where possible.) Lens: wide immersive POV or natural perspective.

[SCENE · creative seed]
First-person POV reaching toward a retail shelf, selecting the hero product from a field of generics. Model chooses: POV character (wide immersive, eye-level natural, slight low-angle, medium-close); hand entry angle; product lift position (forward of shelf, just-grasped, fully lifted); surrounding arrangement (dense rainbow, organized rows, partial cooler-door at edge).

[SUBJECT]
Surrounding packs are generic — recognizable category types but with NO readable text and NO invented brand names. Keep neighbors slightly out of focus so any printed elements read as ambient color noise, never legible fake labels. The hero product carries full label fidelity. Hand per {saudi.apparel_context} / {brand.modesty_register}, right-hand grip (CS-08).

[BRAND CONSTRAINTS]
Hero product is the only branded item with readable fidelity. ALL neighbors have NO readable text — plain colored packaging or out-of-focus. Do NOT invent brand names or wordmarks. One hand, no other body, no face. {brand.anti_attributes}

[OUTPUT]
8K photoreal cinematic commercial photography. High-saturation retail grade, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets a modern Saudi supermarket aisle per CS-13 (Carrefour/Lulu/Danube/Othaim). Aisle signage in Arabic if visible. {saudi.apparel_context} for the hand/cuff. Right-hand rule per CS-08.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary POV, hand entry, product lift, surrounding arrangement, warm/cool balance. Hold constant: neighbors have NO readable text, hero same size as neighbors, material texture, CS-08 grip. Each render a different selection moment — never with fake brand labels.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hand, hero product, shelf, surrounding packs — all preserved exactly. Hero product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect. Surrounding packs stay text-free.

[MOTION]
The hand completes the selection — fingers close on the hero product and lift it slightly forward off the shelf over the duration. A natural human motion, smooth, not robotic. The shelf behind stays still. The hero product never distorts; its labels stay locked.

[WHAT STAYS STATIC]
Hero product silhouette, every label character, color values, logo, material finish — locked. Surrounding packs remain text-free. Capture character {brand.aesthetic.capture_character} preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal retail cinematography. Silent. No text overlay, no watermark.
```

---

## Chain H04 · Hand Detail Macro — Reverence

```
FAMILY        TF05 · Hand & Human Touch
SECTORS       Beauty, Fragrance, Luxury, Jewelry
QUALITY TIER  premium
INTENT        launch, brand
REFERENCE     Recommended
FREQUENCY     1× per week / premium
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @danatreasures
CULTURAL SPEC CS-01 apparel, CS-08 right-hand rules, CS-24 women framing by tier
WHEN TO USE   Premium reverence close-up — fingers cradling the product like a treasure. Best for high-tier/luxury
              products. Over-positions everyday SKUs — the agent should reserve it for premium tiers.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — fingertip pose, product orientation, and key angle are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Hand and product are ONE light event — a single warm key catches both with the same falloff. Skin warmth reflects onto the product at the fingertip contact; the deep shadow embraces both equally.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth at premium register, photoreal, subtle warm grain in shadow. Real skin — pores, knuckle definition, fine palm lines, faint veins. Material truth: {product.material_texture} — fingers may slightly indent soft/pliable materials where they grip.

[SCALE CALIBRATION]
{product.dimensions}. The product sits naturally cradled in a hand at honest proportion.

[FRAMING & PROXIMITY]
Extreme close hero proximity — product and contact-point fingers fill the frame, deep negative space around.

[COLOR & CONTRAST · brand-derived]
Deep dark field. Skin warmth + {brand.palette.primary} as the single sharp chromatic accent against cinema-deep negative space. Field from {brand.color_field_palette}. No foreign accents.

[LIGHT & LENS · single hard key, mood not spec]
Single cinematic warm key against deep shadow — reverent treatment. Model chooses key direction (upper-left, upper-right, top halo), warmth, rim placement. The shadow falls deep and rich. POPPING COLOR INTENT: warm skin, {brand.palette.primary} as the sharp accent. Lens: macro at extreme shallow depth — only the contact point sharp.

[SCENE · creative seed]
Luxury reverence close-up — fingers cradling the product like a treasure against deep negative space. Model chooses: fingertip pose (thumb-forefinger pinch, palm cradle, fingertip balance, refined hold); product orientation; wrist visibility; depth of field.

[SUBJECT]
A hand per {saudi.apparel_context} / {brand.modesty_register} — defined skin, sleeve cuff at frame edge, right-hand grip (CS-08), women framing per CS-24.

[BRAND CONSTRAINTS]
Single product. Only the hand, wrist forward maximum. Pure deep darkness, no props. {brand.anti_attributes}

[OUTPUT]
8K photoreal premium commercial photography. Rich black grade, single-light warmth, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills the cuff (e.g. white thobe or bisht edge; abaya sleeve with modest accessory per {brand.modesty_register} and CS-24). Key warmth per {saudi.color_palette_adjust}. Right-hand rule per CS-08.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary fingertip pose, product orientation, wrist visibility, key angle, depth. Hold constant: single hard key, deep shadow, material texture, CS-08 grip. Each render a different reverent moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hand, product, sleeve cuff — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The fingers turn the product a few degrees as if presenting it to the light; the single key catches a new highlight as it turns; the deep shadow holds. Extremely slow, reverent pacing. The product turns only enough to reveal — it does not spin or distort.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Capture character film_grain_warmth preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal premium cinematography. Silent. No text overlay, no watermark.
```

---
# FAMILY F-GROUND · TF-GROUND — Product Embedded in Saudi Environment

*6 chains · G01-G06 · Sectors: F&B, Retail, Beauty, Auto-culture · Quality tier: universal → premium* *The product lives in authentic Saudi environments. Natural placement governs all six.*

---

## Chain G01 · Product on Classical Saudi Car Hood

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       F&B, Beverage, Retail, Auto-culture
QUALITY TIER  universal → premium
INTENT        launch, grow, brand
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-13 authentic-vs-Hollywood, CS-18 vessels (companions)
WHEN TO USE   Bold editorial lifestyle hero — the product on a classical Saudi vehicle's hood. Road-trip / car-culture
              energy. The flagship of the natural-placement + chiaroscuro + color-blocking approach.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — placement, orientation, framing, and lighting are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Product, companion, and hood are one moment under one hard light. The hood's saturated paint reflects faintly onto the product; contact shadows agree in direction and hardness; steam/companion and product share the same shaft of light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, broadcast_cinematic high-contrast editorial, photoreal — not CGI. Material truth: {product.material_texture} — including faint car-color reflection on any semi-gloss zones. Real paint texture, clear-coat specular, micro-dust from desert driving.

[SCALE CALIBRATION]
{product.dimensions}. The product is small relative to the hood; render the product-to-companion proportion honestly per the dimensions anchor. The product is NOT enlarged for emphasis.

[FRAMING & PROXIMITY]
Medium-close hero proximity. Product occupies ~25-35% of frame at a rule-of-thirds anchor. We see only the immediate hood area around the product and companion. No vast empty hood or sky.

[COLOR & CONTRAST · brand-derived field]
The car-body color FIELD is drawn from {brand.color_field_palette} and culturally-grounded Saudi car colors — NEVER a color foreign to the brand, never a hue borrowed from a reference image. The product and {brand.palette.primary} contrast against that field. Discipline to a few colors: the car field, the product's own colors, and warm context amber. No muddy mid-tones.

[LIGHT & LENS · dramatic, shadow-cutting]
HARD directional light — never soft. A single dominant source (low raking golden-hour, or hard editorial key) creates a bright lit band where the product sits and DEEP near-black shadow elsewhere. The shadow CUTS across the frame. Background falls into shadow — a pool of light on the subject. Specular gleam on glossy paint and any companion; the product's material truth holds; {brand.palette.primary} catches a bright highlight. Lens: medium-close, shallow-enough depth to soften the dark backdrop.

[NATURAL PLACEMENT]
The product and companion came to rest naturally — gravity governs orientation. The product may lie flat (brand face angled to camera), lean, or sit propped. The companion sits as if just set down. Nothing in a perfect grid. Brand-readable face toward camera is a probable outcome of the close framing, not a forced pose.

[COMPANION ELEMENTS · restrained]
ONE hero companion from {product.companion_elements}, placed with natural physics (e.g. a serving cup with rising steam). Optionally ONE more clean shape — never garnish scatter of many small props.

[SCENE · creative seed]
A bold editorial still-life on a classical Saudi vehicle's hood — one product, one companion, hard light, brand-derived color, deep shadow. Model chooses: vehicle (from the culturally-grounded Saudi-classic set — NOT colors foreign to the brand); time/light for max contrast (low golden-hour rake, side-lit dusk — background dark); natural placement; setting band (Saudi desert, AlUla, Riyadh silhouette — kept dark).

[SUBJECT]
The product is hero by light and color contrast; the single companion tells its story; the brand-derived saturated hood is the color field; the dark setting is negative space.

[BRAND CONSTRAINTS]
Single product hero. ONE companion, optionally one clean shape. One vehicle. No humans. No license plates (or generic/blurred). {brand.anti_attributes}

[OUTPUT]
8K photoreal commercial lifestyle photography, high-contrast editorial grade. Deep rich shadows, brand-derived saturated field, {brand.palette.primary} popping. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets a Saudi-classical vehicle per CS-13. {saudi.material_context} supplies the companion (e.g. finjan per CS-18). For {saudi.occasion_overlay}: subtle Saudi-green accent (Founding Day).

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary car color (within the brand-derived range only), light direction and shadow-cut location, natural placement, second-companion presence. Hold constant: hard directional light, brand-derived palette, deep shadow, honest proportion, material texture. Never a foreign color, never cluttered, never soft.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The product, companion, hood, setting — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The world breathes: steam rises from the companion, heat-haze shimmers off the hood, the hard light shifts warmth 10-15% as if the sun moves. A slow push-in toward the product. The product and companion never move, rotate, or distort — only light and atmosphere are alive.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Natural placement held. Capture character {brand.aesthetic.capture_character} preserved. Deep shadow-cut maintained.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal lifestyle cinematography. Silent. No text overlay, no watermark.
```

---

## Chain G02 · Product Nested in Garment / Pocket

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       F&B, Retail, Beauty
QUALITY TIER  universal
INTENT        grow, brand
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @tiadress, @barnscoffee
CULTURAL SPEC CS-01 apparel/thobe variants
WHEN TO USE   Intimate everyday — the product nested in a garment pocket (thobe/abaya), fabric only, no wearer.
              "Travels with me through the day." Soft natural light, not hard editorial.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — fabric drape, pocket framing, and accent are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: Product and garment are one warm intimate moment. The fabric reflects onto the product at the pocket-contact edges; soft window light wraps fabric folds and the product with the same softness; the pocket-shadow holding the product is the same shadow defining the fabric wrinkles.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, phone_natural with editorial lift, photoreal. Real cotton weave, micro-fiber detail, honest wrinkles, authentic fabric tone. Material truth: {product.material_texture} — the pocket fabric gently presses against any soft/pliable product surface.

[SCALE CALIBRATION]
{product.dimensions}. The product fits inside a chest pocket with its branded top portion emerging — honest pocket-to-product proportion.

[FRAMING & PROXIMITY]
Intimate proximity — pocket and product are the focal subject, most of the frame the fabric. Tight, no dead space.

[COLOR & CONTRAST · brand-derived]
The garment fabric is the clean color field (per {saudi.apparel_context}). {brand.palette.primary} is the singular saturated accent; the product's dark/light body the secondary anchor. High clarity through chromatic economy. No foreign accents.

[LIGHT & LENS · soft natural, gentle contrast, mood not spec]
Soft natural indoor light — filtered window, warm-neutral. Gentler than the hard editorial chains (this is intimate, not graphic-bold) but still directional enough to reveal weave and a soft shadow. Model chooses light direction and how strongly shadow reveals the fabric. Lens: macro intimacy; model chooses depth across fabric texture.

[NATURAL PLACEMENT]
The product sits in the pocket naturally — slight backward tilt as pocket geometry creates, branded top emerging, supported by fabric. Not posed stiffly.

[COMPANION ELEMENTS · minimal]
Minimal — the fabric is the story. Optionally ONE small cultural accent at frame edge from {product.companion_elements} or {saudi.material_context}, OR nothing for purest minimalism. No scatter.

[SCENE · creative seed]
The product nested in a garment pocket, fabric only — no wearer. "Travels with me through the day." Model chooses: framing scale (tight macro, medium chest-drape, wider shoulder/collar); pocket angle; fabric drape (heavy, summer-weight, pressed-formal); accent (one small element, or none).

[SUBJECT]
Real garment fabric per {saudi.apparel_context} — honest weave, subtle wrinkles, authentic pocket stitching (CS-01). The product nestles naturally, branded face emerging.

[BRAND CONSTRAINTS]
Single product in pocket. Only fabric — no wearer, no skin, no face. One small accent permitted. {brand.anti_attributes}

[OUTPUT]
8K photoreal lifestyle commercial photography. Soft natural grade, true {brand.palette.primary} punch. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} sets the garment (Najdi thobe cotton per CS-01, or abaya fabric per {brand.modesty_register}). {saudi.material_context} supplies any small cultural accent. {saudi.scene_context} for register.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary framing scale, pocket angle, fabric drape, accent choice, natural light direction. Hold constant: garment color field, soft intimate light, material texture. Each render a different everyday moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The garment, pocket, product, accent — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The fabric breathes with the faintest natural movement — as if the wearer just inhaled — and the soft window light shifts gently. The product stays nestled, locked in form and position. Extremely subtle, intimate pacing.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Pocket placement held. Capture character {brand.aesthetic.capture_character} preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal lifestyle cinematography. Silent. No text overlay, no watermark.
```

---

## Chain G03 · Product on Cultural Majlis Tray

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       F&B, Beauty, Luxury, Heritage
QUALITY TIER  universal → premium
INTENT        launch, grow, brand
REFERENCE     Recommended
FREQUENCY     1-2× per week / heritage
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @danatreasures, @barnscoffee
CULTURAL SPEC CS-13 authentic-vs-Hollywood, CS-15 majlis, CS-18 vessels, CS-21 food rules
WHEN TO USE   Heritage hospitality — the product welcomed onto a traditional majlis tray. Warm tungsten chiaroscuro,
              authentic cultural elements built in. Best for heritage and occasion campaigns.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — tray viewpoint, element arrangement, and tungsten character are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The product belongs to the still-life. Metallic elements reflect warm gold onto the product's edges; tungsten tints every surface — vessels, product, dates, textile — the same warmth; textile warm-gold thread rhymes with {brand.palette.primary}.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth heritage cinema, photoreal, warm-toned film science, organic grain in shadow. Real metal patina (CS-18), genuine wood/textile, natural dates, honest ceramic. Material truth: {product.material_texture}. No Hollywood-Middle-East gloss.

[SCALE CALIBRATION]
{product.dimensions}. Render the size hierarchy honestly among the product and the cultural elements (per {saudi.material_context} object sizes).

[FRAMING & PROXIMITY]
Intimate tray proximity — the still-life fills the frame, edges falling soft. No dead space.

[COLOR & CONTRAST · brand-derived + authentic heritage]
Warm tungsten field plus authentic culturally-grounded tones from {saudi.material_context} (metal gold, textile deep-reds — real heritage colours, not borrowed accents). Anchored to {brand.palette.primary} as the modern note.

[LIGHT & LENS · warm tungsten chiaroscuro, mood not spec]
Warm intimate tungsten — a cultural interior after sunset. Directional and moody with deep shadow in negative space — WARM and soft-edged, not hard editorial, so it reads intimate. Model chooses key direction, fill from below (surface reflection), shadow depth, optional gentle flicker. POPPING COLOR INTENT: rich warmth, metallic gold gleam, textile depth, {brand.palette.primary} as the modern note. Lens: portrait compression; model chooses depth across the tray.

[NATURAL PLACEMENT]
The product sits naturally beside the elements as if just set down — upright on its base or gently leaning. Elements rest in their natural positions. Not a perfect grid.

[COMPANION ELEMENTS · heritage built-in, restrained]
The cultural elements ARE the companions — RESTRAINED: model chooses the count (minimal trio, quartet, or expanded with a small detail at the edge) but never crowds. Singular pieces, drawn from {saudi.material_context} / {product.companion_elements}.

[SCENE · creative seed]
Heritage hospitality — the product welcomed onto a traditional tray. Model chooses: tray viewpoint (top-down, three-quarter elevated, near-eye-level intimate, low-angle); tray material; element arrangement and count (restrained); textile visibility (rug edge at lower frame, cushion in bokeh, near-absent).

[SUBJECT]
Authentic cultural elements per CS-13 / {saudi.material_context} (e.g. brass dallah + Najdi spout per CS-18, dates per CS-21, Najdi textile). The product reads as modern but welcome.

[BRAND CONSTRAINTS]
Single product hero. Cultural elements as singular supporting context — never multiples. No alcohol, no pork (CS-21). Authentic per CS-13. No humans. {brand.anti_attributes}

[OUTPUT]
8K photoreal heritage commercial photography. Warm rich grade, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets the register. {saudi.material_context} supplies the full majlis config per CS-15 (vessels CS-18, dates CS-21, Najdi textile with warm-gold thread rhyming with the brand colour). For {saudi.occasion_overlay}: deepen Ramadan evening warmth or add Founding-Day green thread.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary tray viewpoint, material, arrangement, element count (restrained), textile visibility, tungsten character. Hold constant: warm tungsten chiaroscuro, material texture, restraint, CS-13 authenticity. Each render a different majlis moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The product, cultural elements, tray, textile — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
Steam rises from the serving vessel; the tungsten light flickers warmly as if from a nearby flame; the warm atmosphere breathes. A gentle push-in toward the product. The product and elements never move or distort — only warm light and steam are alive.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Element placement held. Capture character film_grain_warmth preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal heritage cinematography. Silent. No text overlay, no watermark.
```

---
## Chain G04 · Product on Car Dashboard

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       F&B, Beverage, Retail, Auto-culture
QUALITY TIER  universal
INTENT        grow, brand
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-13 authentic-vs-Hollywood, CS-18 vessels (companions)
WHEN TO USE   On-the-go lifestyle — the product on a dashboard with open Saudi context through the windscreen.
              "Travels Saudi life with you." Hard directional through-windshield light.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — windshield context, interior, and time of day are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The product on the dashboard is one captured car-interior moment. Through-windshield light fills the cabin and lights the product — sky tint on its top edge, warm dashboard tones on its lower edge; foreground dust drifts in the same air volume.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, phone_natural with editorial lift, photoreal. Real leather/vinyl grain, sun-warmth, faint dust, honest windscreen reflections. Material truth: {product.material_texture} — faint interior reflection on semi-gloss zones.

[SCALE CALIBRATION]
{product.dimensions}. Render the product-to-companion proportion honestly; both small on the dashboard surface.

[FRAMING & PROXIMITY]
Medium-close proximity — product and companion on the dash fill the foreground; through-windshield context is an intimate backdrop band, not a vast empty expanse.

[COLOR & CONTRAST · brand-derived]
Brand-derived interior field (per {brand.color_field_palette} — tan, cream, dark grey) with the through-windshield sky as a saturated band. Anchored to {brand.palette.primary}. No foreign-color interior.

[LIGHT & LENS · hard directional, mood not spec]
Through-windshield daylight with directional rake catching the dash and product. Hard enough to throw a defined product shadow on the dash. Model chooses light direction and color-temp mood (warm morning, hard midday, golden afternoon). POPPING COLOR INTENT: saturated sky band, rich warm interior, {brand.palette.primary} as the sharp foreground anchor. Lens: natural interior perspective; model chooses depth for windshield context.

[NATURAL PLACEMENT]
The product and companion came to rest on the dash naturally — product may lie, lean against the windscreen base, or stand if the dash cradles it; companion set down. Not posed.

[COMPANION ELEMENTS · restrained]
ONE hero companion from {product.companion_elements} (e.g. a serving cup with steam), resting on the dash or in a cupholder. Optionally one clean shape. No scatter.

[SCENE · creative seed]
An on-the-go moment — the product on the dashboard, open Saudi context through the windscreen. Model chooses: windshield context (desert highway, Riyadh boulevard, AlUla road, Jeddah corniche, Najdi dunes); interior (vintage cream/tan + wood-grain, modern dark-grey + chrome, mid-range cloth + beige); natural placement; time of day; POV (passenger-seat, low driver-seat, near-windshield).

[SUBJECT]
Car interior reads classical or modern Saudi (CS-13), authentic wear and sun-warmth. The product sits naturally, branded face toward the imagined photographer.

[BRAND CONSTRAINTS]
Single product. ONE companion. No humans, no driver's hand, no passenger. Saudi interior per CS-13. No plates/external identifiers. {brand.anti_attributes}

[OUTPUT]
8K photoreal lifestyle commercial photography. Saturated warm grade, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets open Saudi through the windshield (Najdi desert, Riyadh, AlUla, Jeddah). Interior per CS-13. {saudi.material_context} supplies the companion (e.g. finjan per CS-18). For {saudi.occasion_overlay}: matching context.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary windshield context, interior, natural placement, time of day, POV. Hold constant: hard directional light, brand-derived interior, one companion, honest proportion, material texture. Each render a different road moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The product, companion, dashboard, through-windshield context — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The world outside the windscreen drifts gently (landscape parallax as if parked with heat-haze, or slow passing scenery); steam rises from the companion; light shifts warmth. A subtle push-in. The product stays locked on the dash — no movement, no distortion.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Dashboard placement held. Capture character {brand.aesthetic.capture_character} preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal lifestyle cinematography. Silent. No text overlay, no watermark.
```

---

## Chain G05 · Product on Retail Shelf — Hero Stands Out

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       Retail, F&B, Beauty
QUALITY TIER  universal
INTENT        grow, harvest
REFERENCE     Recommended
FREQUENCY     2-3× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @barnscoffee
CULTURAL SPEC CS-13 authentic retail
WHEN TO USE   Shelf presence — the hero product standing out from a field of competitors, no hands. CRITICAL:
              surrounding products carry NO readable text (no fake brands).
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — shelf arrangement, camera angle, and lighting balance are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The hero product is one of the products on the shelf — same overhead light lights it and the neighbors; cool back-shelf light wraps its edges. It stands out by forward position and a slightly stronger key, NOT by being studio-lit on a documentary shelf.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character}, broadcast_cinematic saturated commercial grade, photoreal. Real shelf wear, price-rail smudges, real material variation on neighbors, authentic retail LED cast. Material truth: {product.material_texture}.

[SCALE CALIBRATION]
{product.dimensions}. The hero product is the SAME physical size as the surrounding competitor packs — it stands out by position and light, not size.

[FRAMING & PROXIMITY]
Medium proximity — the hero product and its immediate shelf row fill the frame, deeper shelves receding. Tight enough to feel the shelf moment.

[COLOR & CONTRAST · disciplined, hero pops]
The surrounding shelf is a saturated rainbow of competing packs (the field is the retail chaos). The hero pops with {brand.palette.primary} clarity by forward position and a stronger key. Hero's own palette disciplined per {brand.color_field_palette}. No foreign accents on the hero.

[LIGHT & LENS · retail + hero key, mood not spec]
Retail lighting — warm overhead with cool shelf-depth behind. Model chooses key brightness on the hero vs ambient on neighbors, warm/cool ratio, and any directional emphasis making the hero separate without breaking integration. (Can't fully shadow-cut — retail is bright — but push contrast.) Lens: wide immersive or natural perspective.

[NATURAL PLACEMENT]
The hero product sits on its shelf naturally — forward of its neighbors as if recently restocked, facing camera, maybe slightly tilted. Not perfectly posed.

[COMPANION ELEMENTS]
None — the shelf context is the scene.

[SCENE · creative seed]
A retail shelf moment — the hero stands out from a field of generics, positioned slightly forward. No hands. Model chooses: camera angle (slight low-angle, eye-level, high-angle three-quarter, close-medium); shelf arrangement (dense rainbow, organized rows, partial cooler-door at edge); hero shelf position; background depth.

[SUBJECT]
Surrounding packs are generic — recognizable category types with NO readable text and NO invented brand names. Keep neighbors slightly soft so any printed elements read as ambient color noise, never legible fake labels. Hero carries full label fidelity.

[BRAND CONSTRAINTS]
Hero product is the only branded item with readable fidelity. ALL neighbors have NO readable text — plain colored packaging or out-of-focus. Do NOT invent brand names. No humans. {brand.anti_attributes}

[OUTPUT]
8K photoreal cinematic commercial photography. Saturated overhead-retail grade, {brand.palette.primary} sharp against the field. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} sets a modern Saudi supermarket aisle per CS-13. Generic neighbors may carry Arabic-script color blocks (no real names).

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary camera angle, shelf arrangement, hero position, background depth, overhead-light balance. Hold constant: neighbors have NO readable text, hero same size as neighbors, material texture. Each render a different shelf moment — never with fake brand labels.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hero product, shelf, surrounding packs — all preserved exactly. Hero product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect. Surrounding packs stay text-free.

[MOTION]
A slow dolly push-in toward the hero product through the shelf field, the surrounding packs softening as the hero sharpens — drawing the eye to the chosen product. The hero never moves or distorts; surrounding packs stay text-free.

[WHAT STAYS STATIC]
Hero product silhouette, every label character, color values, logo, material finish — locked. Surrounding packs remain text-free. Capture character {brand.aesthetic.capture_character} preserved.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal retail cinematography. Silent. No text overlay, no watermark.
```

---

## Chain G06 · Product on Heritage Surface

```
FAMILY        TF-GROUND · Product in Saudi Environment
SECTORS       F&B, Beauty, Luxury, Heritage
QUALITY TIER  universal → premium
INTENT        launch, grow, brand
REFERENCE     Recommended
FREQUENCY     1-2× per week
IMAGE MODEL   fal-ai/flux-2-pro/edit    (8,000 chars)
VIDEO MODEL   fal-ai/kling-video/v1.6/pro/i2v    (2,500 chars)
REF ACCOUNTS  @danatreasures, @barnscoffee
CULTURAL SPEC CS-13 authentic-vs-Hollywood, CS-18 vessels (companions)
WHEN TO USE   Heritage rootedness — the product on identifiably Saudi heritage stone/material. Golden-hour hard rake.
              Best for heritage and National/Founding Day campaigns.
```

### ◆ Image prompt → fal-ai/flux-2-pro/edit (8,000 chars)

```
[BRAND LOCK · identity invariant, placement and composition open]
The reference image teaches the {product.name} brand identity. Identity is invariant — heritage surface, light angle, and placement are creative decisions.
Identity DNA: {product.identity_dna}
INTEGRATION: The product on heritage stone is one golden-hour moment. The warm stone reflects subtle color onto the product's base — the brand color rhymes warmly with the stone; the long stone-shadow is the same shadow dropping from the product; fine desert particles drift across stone and product alike.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth heritage cinema, photoreal, warm-toned film, warm grain in shadow. Real stone truth — mudbrick straw inclusions, sandstone striations, coral-stone fossil character, weathered wood grain. Material truth: {product.material_texture}.

[SCALE CALIBRATION]
{product.dimensions}. Render the product-to-companion proportion honestly; both small on the heritage surface.

[FRAMING & PROXIMITY]
Medium-close proximity — product and companion on the stone fill the frame, the surface texture filling the surround, edges soft. No vast dead space.

[COLOR & CONTRAST · brand-derived earth]
Warm earth field from Saudi heritage stone (mudbrick beige, sandstone honey, coral-stone rose, AlUla red-earth, weathered-wood brown — authentic earth tones, not borrowed candy accents). Anchored to {brand.palette.primary} rhyming with the warm tones. Field per {brand.color_field_palette} + {saudi.material_context}.

[LIGHT & LENS · golden-hour hard rake, mood not spec]
Saudi golden-hour directional rake — hard quality catching stone texture, long shadows revealing depth. The shadow can cut across the frame for drama. Background falls into warm shade. Model chooses rake direction (upper-left/right, near-frontal, low-side shadow-emphasis). POPPING COLOR INTENT: warm earth field at full natural depth, {brand.palette.primary} as the modern accent rhyming with the honey tones. Lens: portrait compression; model chooses depth for surface vs context.

[NATURAL PLACEMENT]
The product and companion came to rest on the stone naturally — product may lie, lean, or stand; companion set down. Not posed in a grid.

[COMPANION ELEMENTS · restrained]
ONE hero companion from {product.companion_elements} (e.g. a serving cup with steam). Optionally one clean shape only if it stays minimal. No scatter.

[SCENE · creative seed]
Heritage textural placement — the product on identifiably Saudi heritage material, rooted in place and time. Model chooses: surface (Diriyah mudbrick, Najdi sandstone, Hejazi coral-stone, weathered wood, AlUla rock); placement (centered, off-centered rule-of-thirds, near a corner); light angle; architectural anchor (subtle Najdi carving at edge, mudbrick joint, coral fossil, or pure texture); frame depth.

[SUBJECT]
Authentic Saudi material truth per CS-13 — specifically Diriyah/Najdi/Hejazi/AlUla, not generic Middle Eastern. Honest, scale-correct texture. The product is the modern note against heritage stone.

[BRAND CONSTRAINTS]
Single product. ONE companion. Only heritage surface — no other props, no humans. Specifically Saudi per CS-13. {brand.anti_attributes}

[OUTPUT]
8K photoreal heritage commercial photography. Warm earth-tone grade, {brand.palette.primary} sharp. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} maps the surface to brand region per CS-13 (Najdi sandstone for Riyadh, Hejazi coral-stone for Jeddah, Diriyah mudbrick for national-heritage, AlUla rock for premium). {saudi.material_context} supplies the companion. For {saudi.occasion_overlay}: Founding/National Day heritage emphasis.

[TEXT OVERLAY — conditional, agent appends only when brief.text_request is present]
Render this text directly in the image: "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}, contrasting color. If absent, no text appears.

[CREATIVE VARIANCE DIRECTIVE]
Vary surface, placement, golden-hour angle, architectural anchor, frame depth. Hold constant: golden-hour hard rake, brand-derived earth field, one companion, honest proportion, material texture. Each render a different heritage moment.
```

### ▶ Video prompt → fal-ai/kling-video/v1.6/pro/i2v (2,500 chars)

```
[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The product, companion, heritage surface, architectural anchor — all preserved exactly. Product silhouette, all label color values, every Arabic ({product.label_text_arabic}) and Latin ({product.label_text_latin}) character, logo, material finish — character-perfect.

[MOTION]
The golden-hour light rakes slowly across the stone as if the sun moves, lengthening shadows over the duration; fine particles drift; steam rises from the companion. A gentle push-in. The product never moves or distorts — only light and air are alive.

[WHAT STAYS STATIC]
Product silhouette, every label character, color values, logo, material finish — locked. Natural placement held. Capture character film_grain_warmth preserved. Golden-hour shadow-cut maintained.

[PACING & DURATION]
5 seconds. Continuous single take. No cuts.

[OUTPUT]
8K photoreal heritage cinematography. Silent. No text overlay, no watermark.
```

---

## Section D · Agent runtime notes (tested 18)

**Block inclusion rules:**

- `[SAUDI ADAPTATION]` fires only when the brand/brief is Saudi-relevant (most OpenClaw brands). Skip for non-Saudi brands.
- `[TEXT OVERLAY]` fires only when `brief.text_request` is present. Otherwise omit entirely — no empty text block.
- `[COMPANION ELEMENTS]` is present on environmental + splash chains; absent on clean studio chains (U01, T02) and retail chains (H03, G05, where the scene is the companion).
- `[NATURAL PLACEMENT]` is present on environmental chains (G01-G06) and the lifestyle hand chains; studio chains use a hero-framing line instead.

**Per-chain drama calibration (the dial):**

- Full editorial punch (hard light, deep shadow-cut, color-block): G01, G04, G06, T03, T04, T05, T07, T01
- Warm tungsten chiaroscuro (intimate, soft-edged): H02, G03
- Soft natural, gentle contrast: G02, H01 (hard golden-hour but outdoor-natural)
- Palette discipline only (busy scene, can't fully block): H03, G05
- Clean even (no drama): U01, T02 (locked)
- Single hard key, deep dark: H04

**Char-limit discipline:** every image block stays under 8,000 chars; every video block under 2,500. The Baja-filled versions ran 2,800-4,900 image chars, leaving ample headroom for longer `{product.identity_dna}` values on complex products.

**Reusable beyond Saudi:** the four new fields (`color_field_palette`, `dimensions`, `material_texture`, `companion_elements`) and the two derivation logics (companion + color-field) are product- and market-agnostic. For a non-Saudi brand, the `{saudi.*}` blocks simply don't fire, and the color-field/companion logic draws from that brand's own world.

---
---

<!-- ══════════ OpenClaw_v3_7_Batch1_TF03_TF04_TF06_TF07.md ══════════ -->

# FAMILY TF03 · SPOTLIGHT & DARK STAGE — 4 chains
**Drama dial: single hard key, deep dark** (T09 variant: luminous-halo dark)

---

## T08 · Single Overhead Spotlight

**Family:** TF03 · Spotlight & Dark Stage | **Tier:** premium | **Sectors:** Beauty, Retail, F&B | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** single hard key, deep dark
**Color story:** Single pool of warm white light against pure black void. Product brand color is the only chromatic event in the frame — maximum saturation against total darkness. Drama through isolation.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @tiadress | **Cultural Spec:** CS-22

**WHEN TO USE:** Theatrical single-spotlight reveal. Product under one overhead beam against pitch black — the most dramatic isolation chain. Premium launches, beauty hero moments, jewelry — any product that earns a main-stage treatment. The darkness does the work.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity — it teaches WHAT the product is, not how this frame must look. Identity DNA, preserved across any camera angle: {product.identity_dna}
Angle, framing, exact placement within the light pool, and the spotlight's precise character are creative decisions — choose what serves the theatrical reveal, keeping brand-readable surfaces oriented toward camera. INTEGRATION: the product is photographed inside this dark stage, not pasted onto it — the single spotlight that defines the void defines the product; its contact pool, falloff, and specular response all belong to the same light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with theatrical lift. Material truth: {product.material_texture} — the substrate behaves as its real self under the hard beam (film stays pliable with honest creases, glass refracts, carton edges stay crisp). The lit portion shows genuine specular response and real texture where the spotlight rakes it; the shadowed portion falls to honest black, not crushed digital void. No CGI-clean perfection, no plastic uniformity, no artificial glow halo.

[SCALE CALIBRATION]
{product.dimensions} — the product reads at its true real-world size. The spotlight pool is scaled to the product: an intimate beam for a small item, a wider theatrical pool for a large one. The pool of light on the ground is proportionate to the object standing in it.

[FRAMING & PROXIMITY]
Hero through closeness: the product holds a commanding share of frame — the negative black space is dramatic, not empty distance. Frame close enough that the spotlit material texture reads. No dead space between viewer and subject; the darkness presses in around a near, present hero.

[COLOR & CONTRAST]
The product's brand color, drawn from {brand.color_field_palette}, is the only chromatic event in the entire frame — full saturation against total black; every other pixel is darkness. No borrowed accent colors, no secondary chromatic elements. Maximum drama through chromatic isolation.

[LIGHT & LENS]
ONE hard overhead spotlight, slightly forward, warm-white theatrical character with tight beam and rapid falloff — no fill; shadows fall to true black. A soft pool grounds the product beneath. Lens choice serves intimacy and compression — the model chooses focal feel and depth treatment that keeps the product crisp and the void absolute.

[NATURAL PLACEMENT]
The product stands or rests as gravity and its own form dictate within the pool — a sachet may lean or lie with honest folds, a bottle stands plumb, a jar sits square. No forced floating, no impossible balance.

[SCENE]
Theatrical single-spotlight composition. Product within a tight pool of hard light on an invisible dark surface, the light falling off rapidly into pure surrounding black. Strong negative space of pure black. The mood is reverent, theatrical, main-stage. Choice points for the model: beam angle nuance, product orientation within the pool, pool size and edge softness.

[SUBJECT]
Single product as the sole illuminated subject. Material rendered with full physical truth where the light touches; shadowed portions fall naturally dark while form stays readable.

[BRAND CONSTRAINTS]
Single product only. No human elements, no props, no secondary objects. Background pure black void. The single spotlight is the only light. {brand.anti_attributes}

[OUTPUT]
Photoreal theatrical product photography, maximum fidelity. Deep-black cinema grade with the brand color punching at full saturation. No overlay text, no watermark, no logo other than the product's own.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — minimal environmental localization. For oud/fragrance/heritage sectors the spotlight may warm toward candlelight reverence. {saudi.color_palette_adjust} can warm the beam toward gold.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Across multiple generations of this chain, vary your choices: beam angle, product orientation, pool tightness, camera height, distance. Identity stays locked; the theatrical reveal should never look the same twice.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, every label character (Latin and Arabic character-perfect), all colors, {product.material_texture}, the spotlight pool, the surrounding black — all locked.

[MOTION]
Primary — light: the overhead spotlight slowly intensifies ~12% over the duration, as if a theatrical operator brings it up, the product emerging more fully from darkness.
Secondary — atmosphere: faint dust motes drift through the beam, catching as tiny points.
Tertiary — camera: extremely subtle 2% push-in.

[WHAT STAYS STATIC]
Product identity locked — every label character, color, material texture. Pure-black surround absolute. Spotlight position fixed. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Slow reverent pacing — the light reveal unfolds like a stage moment.

[OUTPUT]
Photoreal theatrical product cinematography. Silent. No text overlay, no watermark.

---

## T09 · Ring Backlight Halo

**Family:** TF03 · Spotlight & Dark Stage | **Tier:** premium | **Sectors:** Beauty, Retail | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** luminous-halo dark
**Color story:** Glowing circular halo of cool or warm rim light behind the product. The ring is the second chromatic anchor; the product brand color is the first. Silhouette drama with luminous edge.
**Reference accounts:** @danatreasures, @alyafie_jewelry, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Halo-backlit silhouette hero. Use for beauty, skincare, premium retail — anything that benefits from a luminous, almost-sacred framing. Strong on dark feeds where the glow pops.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product renders against the backlit halo with edges catching the rim glow while the front face stays brand-readable. Exact halo size, product offset, and rim intensity are creative decisions. INTEGRATION: one lighting event — the halo ring — governs the entire frame; the product's rim bloom, ambient front fill, and the deepening dark all belong to that single source logic.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio. Material truth: {product.material_texture} — the substrate's real behavior at the glowing edge (specular bloom on glass, soft glow-wrap on matte film, crisp rim on metal) and at the shadowed front face, where real texture stays visible. The halo glows with authentic light diffusion, never a flat digital ring. No CGI-clean glow, no plastic uniformity, no artificial lens-flare overlay.

[SCALE CALIBRATION]
{product.dimensions} — true real-world size; the halo ring is proportioned to the product (a generous ring that frames, never dwarfs or crowds the silhouette).

[FRAMING & PROXIMITY]
The product and its halo dominate the frame — centered, iconic, near. The dark margins deepen toward the edges but the luminous event fills the viewer's attention. No distant-object emptiness.

[COLOR & CONTRAST]
Two chromatic anchors only: the halo's glow (warm gold or cool tone — chosen to serve {brand.color_field_palette}, never borrowed from a reference) and the product's own brand color. These two create the entire palette against the dark surround.

[LIGHT & LENS]
ONE circular ring light directly behind the product — warm for heritage registers, cool for beauty-tech (agent picks per brand) — with only the minimal ambient front fill needed to keep the face brand-readable. Lens and depth treatment chosen for a sharp product and a softly bloomed halo.

[NATURAL PLACEMENT]
The product stands as its form dictates before the ring — plumb, square, or honestly leaning if its substrate would.

[SCENE]
Backlit halo composition. Product centered against the glowing ring, front face in soft shadow lifted by subtle bounce, edges glowing with rim light, background deepening to dark at the frame edges so the halo reads as the single luminous event. Centered, reverent, iconic. Choice points: halo diameter, rim intensity, product rotation.

[SUBJECT]
Single product, halo-framed. Edges catch rim light; the front face stays brand-readable. Material truth at both the glowing edge and the shadowed face.

[BRAND CONSTRAINTS]
Single product only. No human elements, no props. The backlight ring and minimal frontal fill are the only light. Background dark. {brand.anti_attributes}

[OUTPUT]
Photoreal product photography, maximum fidelity. Dark cinema grade with luminous halo and brand-color punch. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — minimal localization. For heritage/oud: halo warms to deep lamp-glow gold. {saudi.color_palette_adjust} sets halo temperature.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: halo diameter and intensity, product rotation, camera height, the balance between silhouette and readable face. Identity locked; the halo moment fresh every time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product silhouette, every label character, colors, {product.material_texture}, the halo ring, the dark surround — all locked.

[MOTION]
Primary — light: the halo pulses with extremely subtle luminance breathing, brightening ~8% then settling, as if alive.
Secondary — atmosphere: faint particles drift through the rim glow at the product's edges.
Tertiary — camera: imperceptible 1.5% push-in.

[WHAT STAYS STATIC]
Product identity locked — labels, colors, material texture. Halo position and silhouette fixed. Dark surround constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Slow, meditative — the halo breathes.

[OUTPUT]
Photoreal product cinematography. Silent. No text overlay, no watermark.

---

## T10 · Column Light From Above

**Family:** TF03 · Spotlight & Dark Stage | **Tier:** premium | **Sectors:** Beauty, Retail | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** single hard key, deep dark + atmosphere
**Color story:** A visible volumetric column of light descends through atmospheric haze onto the product. The beam itself glows (warm or cool); the product brand color anchors the base. Sacred, descending-light drama.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-22, CS-19 | **Note:** Seedance video workflow with audio (2,000-char limit on video prompt)

**WHEN TO USE:** Descending-beam reverence — light through a cathedral window, a beam through incense smoke. Premium/heritage launches, fragrance, oud, jewelry — anything that earns a chosen-by-the-light treatment.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product sits at the base of the descending column with brand-readable surfaces catching the beam; beam width, haze density, and product orientation are creative decisions. INTEGRATION: the descending column is the single light event — it defines the product's top-lit modeling, the visible haze, and the deep surrounding shadow as one continuous physical system.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — atmospheric cinema, subtle warm grain in shadow regions. Material truth: {product.material_texture} — the substrate catches the descending beam as its real self (top surfaces lit true, lower portions in honest atmospheric shadow). The volumetric beam shows real scatter through suspended haze, density variation across the column, honest light-shaft physics. No CGI god-ray, no plastic surfaces.

[SCALE CALIBRATION]
{product.dimensions} — true size; the column is a grand vertical event relative to the product, the small-against-the-light proportion creating the sacred scale contrast.

[FRAMING & PROXIMITY]
The beam and its base — where the product stands — anchor the frame. The product holds presence through the lit pool; the vertical column gives height without pushing the hero into distant smallness.

[COLOR & CONTRAST]
The glowing column (warm amber for heritage/oud, cool white for modern beauty) is the dominant luminous element; the product's brand color from {brand.color_field_palette} anchors the base at full saturation. Rich darkness everywhere else. No third color.

[LIGHT & LENS]
ONE sharp column light from directly above, heavy atmospheric haze revealing the beam's full descent, no fill — surroundings fall to deep shadow. Lens and depth chosen for a sharp product and beam-base with the upper column softly atmospheric.

[NATURAL PLACEMENT]
The product rests at the beam's landing pool exactly as gravity places it — standing plumb, or lying with honest folds if its substrate lies.

[SCENE]
Descending light-column composition. A sharp vertical shaft falls from the upper frame through visible haze onto the product at its base, center-frame. Surrounding darkness deepens toward the edges. The mood is sacred, descending, chosen. Choice points: beam width, haze character, base-pool spread, camera height.

[SUBJECT]
Single product at the base of the beam, upper surfaces raked by the descending light, lower portions in atmospheric shadow, the column itself rendered with authentic volumetric scatter.

[BRAND CONSTRAINTS]
Single product only. No human elements, no props. The descending column is the only light. Background dark. {brand.anti_attributes}

[OUTPUT]
Photoreal atmospheric product photography, maximum fidelity. Deep cinema grade, luminous descending beam, brand-color base anchor. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for oud/heritage the haze reads as bukhoor/oud incense smoke (CS-19), beam warms to gold. {saudi.color_palette_adjust} sets beam temperature.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: beam width and angle nuance, haze density, product orientation in the pool, camera height. The sacred descent never repeats identically.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, the light column, haze, dark surround — all locked.

[MOTION]
Primary — the column: atmospheric particles drift slowly downward through the visible beam, density shifting gently as if smoke moves through it.
Secondary — the product: subtle catch-light shifts as the beam breathes ~6%.

[WHAT STAYS STATIC]
Product identity locked — labels, colors, material texture. Beam and product positions fixed. Dark surround constant. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Slow sacred pacing. Audio: subtle low ambient atmospheric tone (Seedance native audio).

[OUTPUT]
Photoreal atmospheric cinematography via Seedance. Subtle ambient audio. No text overlay, no watermark.

---

## T11 · Noir Smoke & Spotlight

**Family:** TF03 · Spotlight & Dark Stage | **Tier:** premium | **Sectors:** Retail, Beauty, Fragrance | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** single hard key, deep dark
**Color story:** Hard side-spotlight rakes the product casting long dramatic shadow. Atmospheric smoke catches the side light. Masculine cinema-noir palette — deep blacks, single warm or steel-cool key, brand color as the sharp accent.
**Reference accounts:** @alyafie_jewelry, @danatreasures | **Cultural Spec:** CS-22, CS-19

**WHEN TO USE:** Cinema-noir masculine drama. Masculine fragrance, oud, watches, premium men's grooming, bold retail — anything that wants a moody, powerful, film-noir character. The shadow is as important as the product.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The hard side light models the product's form while brand-readable surfaces face camera; key angle, shadow length, and smoke density are creative decisions. INTEGRATION: one hard side key governs everything — the product's raked modeling, the long cast shadow, the lit smoke — a single coherent noir light system.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with noir grade — deep dynamic range, film-noir commercial aesthetic. Material truth: {product.material_texture} — the lit side reveals real micro-texture as the substrate truly behaves under raking light; the shadow side falls to rich honest black with form still readable. The smoke shows true turbulent fluid behavior; the cast shadow has authentic penumbra softening. No CGI render, no flat digital smoke.

[SCALE CALIBRATION]
{product.dimensions} — true size; the cast shadow is proportionally honest to the object casting it, long and theatrical but physically real.

[FRAMING & PROXIMITY]
The product and its shadow share the frame as co-subjects — close, present, powerful. The noir darkness surrounds a near hero, not a distant one.

[COLOR & CONTRAST]
Noir restraint: deep blacks dominate; the single key carries warm amber (oud-masculine) or steel-cool (modern-masculine) tone; the product's brand color from {brand.color_field_palette} punches as the one sharp chromatic accent on the lit face. Nothing else carries color.

[LIGHT & LENS]
ONE hard key from the extreme side (80–90°), no fill — the shadow side falls to deep black. Smoke catches the side beam; the long cast shadow crosses the surface into the dark. Lens and depth chosen for a sharp product with smoke and shadow atmospheric.

[NATURAL PLACEMENT]
The product stands or rests off-center as its form and gravity dictate, the side light defining its honest posture.

[SCENE]
Cinema-noir composition. Product slightly off-center, hard-raked from one side, long dramatic shadow cast across the surface, smoke drifting through the side beam in turbulent wisps, the unlit side and surround in deep noir shadow. Masculine, powerful, cinematic. Choice points: key angle, shadow direction, smoke density, product offset.

[SUBJECT]
Single product, hard-modeled by the side light. Lit side in full material detail; shadow side dark with readable form. The cast shadow is a compositional element. Smoke surrounds, never obscures the brand-readable face.

[BRAND CONSTRAINTS]
Single product only. No human elements. Smoke around the product, not on it. The dramatic shadow is intentional. Background deep noir black. {brand.anti_attributes}

[OUTPUT]
Photoreal cinema-noir product photography, maximum fidelity. Deep-black noir grade, single-key drama, brand-color accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for oud/masculine heritage the smoke reads as bukhoor (CS-19), key warms to amber. {saudi.color_palette_adjust} sets key temperature.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: key angle and temperature, shadow length and direction, smoke behavior, product offset and rotation. Noir mood constant; the frame never repeats.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, the side-light modeling, cast shadow, smoke, noir darkness — all locked.

[MOTION]
Primary — smoke: drifts through the side beam in slow turbulent wisps, curling and dissipating.
Secondary — light: the hard key flickers fractionally (under 4%) as from an unstable theatrical source, subtly shifting the cast shadow.
Tertiary — camera: extremely subtle 2% lateral drift, deepening the dimensional noir feel.

[WHAT STAYS STATIC]
Product identity locked — labels, colors, material texture. Product and shadow positions fixed. Noir black surround constant. Capture character: broadcast_cinematic noir preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow brooding noir pacing.

[OUTPUT]
Photoreal cinema-noir cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF04 · NATURAL ENVIRONMENT — 5 chains
**Drama dial: soft natural** (T15 variant: hard golden-hour, outdoor-natural · T16 variant: palette discipline, warm retail)

---

## T12 · Bathroom Marble Counter

**Family:** TF04 · Natural Environment | **Tier:** premium | **Sectors:** Beauty, Home, Retail | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** soft natural
**Color story:** Cool white marble with warm gold fixtures — classic luxury bathroom contrast. Soft natural daylight. Product brand color sits as the focal accent against the marble-and-gold neutral field.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-13

**WHEN TO USE:** Luxury bathroom context for skincare, beauty, fragrance, home/bath products. Communicates "this belongs in a beautiful Saudi home." Context grounds the product in lived luxury.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is photographed INSIDE this bathroom — placement on the counter, camera angle, and framing are creative decisions for a real placed object. INTEGRATION: the window daylight that defines the room defines the product; its surface picks up cool marble bounce and warm gold reflection at the edges, its contact shadow agrees with every other shadow in the scene, it shares the room's focus plane logic. Never a studio-lit product on an environment photo.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with natural-light warmth. Material truth: {product.material_texture} — the substrate behaves as its real self on the marble (film lies with soft honest creases, glass stands with true refraction, a jar sits with real weight). Real marble veining, honest gold-metal reflectance with tiny water spots, true fabric weave on the towel. No CGI-clean render, no over-styled showroom sterility.

[SCALE CALIBRATION]
{product.dimensions} — the product reads at true size against the bathroom's real-world anchors: counter depth, faucet height, folded towel. A serum bottle is hand-small beside the faucet; a large jar reads proportionally bigger. Honest scale, never a giant hero looming over the counter.

[FRAMING & PROXIMITY]
Hero through closeness — frame in at counter level so the product commands the foreground while the bathroom breathes softly behind. No wide empty-room dead space; the viewer is at the counter, near the product.

[COLOR & CONTRAST]
The marble-and-gold neutral field (cool white + warm gold) sets the elegant base; the product's brand color from {brand.color_field_palette} is the focal chromatic accent that draws the eye. One natural green counter-note maximum. No borrowed colors.

[LIGHT & LENS]
ONE light logic: soft natural daylight from a side window — gentle, directional, soft-shadowed — with warm bounce returning from the gold fixtures as part of the same system. Lens and depth chosen for a sharp product and softly contextual environment.

[NATURAL PLACEMENT]
The product sits exactly as a person would have placed it on the counter — square, slightly turned, or honestly leaning per its substrate. Gravity governs.

[COMPANION ELEMENTS]
ONE hero companion drawn from {product.companion_elements} (e.g., a neatly folded hand towel OR a small green plant OR the gold faucet softly behind — never all crowding together). The companion obeys the same light and physics. Restraint is the luxury.

[SCENE]
Luxury bathroom counter composition. Product on polished warm-white marble as the focal subject, soft window daylight from the side, the chosen companion supporting, the room reading as a beautiful real Saudi bathroom (CS-13) — aspirational-real, never a sterile showroom. Choice points: camera height, product turn, companion selection and placement, depth treatment.

[SUBJECT]
Single hero product on the marble, the one companion softly secondary. Marble, metal, fabric — every material rendered with authentic truth.

[BRAND CONSTRAINTS]
Single hero product. One companion maximum from the bathroom's authentic world. No human elements. The interior reads as a real upscale Saudi home (CS-13), not a Hollywood set. No readable text on any background object. {brand.anti_attributes}

[OUTPUT]
Photoreal interior lifestyle photography, maximum fidelity. Soft luxury grade — warm whites, gold accents, brand-color focal punch. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the interior register — modern Saudi luxury bathroom. {saudi.material_context} can specify Saudi-preferred marble and fixture styles. For Ramadan/Eid: warm evening light variant.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: camera height and angle, product position and turn, which single companion appears, window-light direction, depth of field. The bathroom moment is never the same twice.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product position, marble, fixtures, companion, lighting, {product.material_texture} — all preserved. Every label character locked.

[MOTION]
Primary — light: daylight shifts fractionally as if a cloud passes the window, the highlight gliding across product and marble.
Secondary — atmosphere: leaves (if plant present) shift microscopically; faint steam-warmth shimmer if bath-related.
Tertiary — camera: extremely subtle 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Counter, fixtures, companion positions fixed. Light direction and warmth. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Calm serene pacing — a quiet luxury moment.

[OUTPUT]
Photoreal interior lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T13 · Kitchen Window Morning

**Family:** TF04 · Natural Environment | **Tier:** universal | **Sectors:** F&B, Home | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** soft natural (warm morning)
**Color story:** Warm morning sunlight streaming across rustic wood. Honest natural tones — wood browns, cream walls, soft shadow. Product brand color glows in the morning light as the warm focal point.
**Reference accounts:** @aseeb.najd, @cafe.najd, @laylali_riyadh | **Cultural Spec:** CS-13

**WHEN TO USE:** Morning kitchen warmth for F&B (coffee, breakfast, pantry) and home brands. The warm start-of-day Saudi home moment — inviting, natural, everyday-aspirational.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is photographed INSIDE this morning kitchen — angle, counter position, and framing are creative decisions. INTEGRATION: the streaming window sun is the one light defining wood, wall, and product alike; the product's surface carries the warm cast, its shadow runs long and parallel with every other morning shadow.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with warm editorial lift — captured as if on a high-end phone in real morning light. Material truth: {product.material_texture} — the substrate sits on the wood as its real self, catching the warm beam truthfully. Rustic wood with genuine grain, knots, honest age; faint dust in the light beam; everyday lived-in character. No CGI wood, no staged set.

[SCALE CALIBRATION]
{product.dimensions} — true size against the kitchen's anchors: counter depth, window sill, any companion vessel. The product is a real countertop object, honestly small in a real room.

[FRAMING & PROXIMITY]
In close at counter level — the product holds the warm foreground, kitchen context breathing softly behind. The viewer stands at the counter in the morning light, not across the room.

[COLOR & CONTRAST]
Warm morning palette — wood browns and cream set the cozy base; the product's brand color from {brand.color_field_palette} glows as the focal point catching the sun. No borrowed accents.

[LIGHT & LENS]
ONE light: warm low morning sun through the side window — soft directional rake, long gentle shadows, the beam faintly visible in the air. Lens and depth chosen for a sharp product and softly atmospheric kitchen.

[NATURAL PLACEMENT]
The product rests where a hand left it this morning — gravity-honest, perhaps slightly turned, a sachet leaning against a canister if its substrate leans.

[COMPANION ELEMENTS]
ONE hero companion from {product.companion_elements} (a simple ceramic cup, a wooden scoop, the product's prepared result steaming gently — one only). Same light, same physics, supporting never competing.

[SCENE]
Morning kitchen composition. Product on a rustic warm-toned wooden counter near the window, morning sun raking across, soft kitchen context behind — cream wall, window frame hint. The warm start of a Saudi morning (CS-13). Choice points: camera height, sun angle, product turn, companion choice.

[SUBJECT]
Single hero product on the wood; the counter and the morning light are the supporting characters, rendered with authentic truth.

[BRAND CONSTRAINTS]
Single hero product, one companion maximum, softly secondary context. No human elements. A real Saudi home kitchen (CS-13), warm and lived-in. No readable text on any background object. {brand.anti_attributes}

[OUTPUT]
Photoreal lifestyle photography, maximum fidelity. Warm morning grade — wood tones, cream warmth, brand-color glow. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the kitchen register — modern Saudi home or traditional Najdi kitchen. For Ramadan: pre-dawn suhoor warmth or evening iftar-prep light.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: sun angle and beam visibility, camera height, product position and turn, companion selection. A different real morning every time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product position, counter, window, morning light, context, {product.material_texture} — all preserved. Every label character locked.

[MOTION]
Primary — light: the morning sunbeam slowly strengthens and shifts angle by a few degrees, the warm highlight gliding across wood and product.
Secondary — atmosphere: fine dust motes drift through the visible beam.
Tertiary — camera: extremely subtle 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Counter, window, context fixed. Warm morning temperature. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle waking-morning pacing.

[OUTPUT]
Photoreal lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T14 · Bedroom Side Table Morning

**Family:** TF04 · Natural Environment | **Tier:** premium | **Sectors:** Beauty, Home | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** soft natural (softest, intimate)
**Color story:** Soft neutral linen tones — warm beige, cream, taupe. Gentle morning light. Quiet, calm, intimate. Product brand color is the single gentle accent in the soft neutral field.
**Reference accounts:** @tiadress, @danatreasures, @themodestbride | **Cultural Spec:** CS-13

**WHEN TO USE:** Intimate bedroom calm for beauty (night creams, fragrance), home (candles, textiles), wellness. A quiet personal-ritual moment — the gentlest of the natural-environment chains.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is photographed INSIDE this calm bedroom — table position, angle, and framing are creative decisions. INTEGRATION: one soft diffused morning light defines linen, table, and product together; the product carries the room's gentle warmth, its soft shadow agreeing with the scene's quiet light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with soft natural warmth. Material truth: {product.material_texture} — the substrate rests with its honest weight and surface behavior in the gentle light. Real linen weave with soft natural wrinkles, honest table material. No CGI render, no over-styled staging.

[SCALE CALIBRATION]
{product.dimensions} — true intimate size against the side table and linen folds; a night cream is palm-small on the table, honestly scaled to its real world.

[FRAMING & PROXIMITY]
Close and quiet — the product near, the linen world soft behind. Intimacy through proximity; no wide empty bedroom.

[COLOR & CONTRAST]
A deliberately soft neutral palette (warm beige, cream, taupe) creates calm; the product's brand color from {brand.color_field_palette} is the single gentle chromatic accent — present, not loud, in keeping with the intimate mood.

[LIGHT & LENS]
ONE soft diffused natural morning light, very gentle directionality, minimal shadow — the whole scene quietly, evenly held. Lens and depth chosen for a sharp product against dreamy-soft linen.

[NATURAL PLACEMENT]
The product sits as part of a real nightly ritual — placed by hand, gravity-honest, perhaps beside a folded linen corner.

[COMPANION ELEMENTS]
ONE hero companion maximum from {product.companion_elements} (a folded linen corner, a small simple object) — or none. Minimal is the mood.

[SCENE]
Intimate bedroom side-table composition. Product on a minimal table (light wood or soft-painted) against softly blurred neutral linen bedding, gentle diffused morning light. A calm Saudi home space (CS-13), intimate not staged. Choice points: camera height, product turn, linen arrangement, companion or none.

[SUBJECT]
Single hero product, the quiet hero of a personal moment. Linen weave, table, gentle light — authentic truth throughout.

[BRAND CONSTRAINTS]
Single hero product, minimal elements. No human elements. No readable text on any background object. A real calm Saudi bedroom (CS-13). {brand.anti_attributes}

[OUTPUT]
Photoreal intimate lifestyle photography, maximum fidelity. Soft neutral grade — beige and cream, gentle brand-color accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the bedroom register — modern calm Saudi home. For Ramadan: subtle pre-dawn or evening warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: camera angle, product placement, linen folds, light softness, companion presence. The quiet moment stays fresh.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product position, table, linen, soft light, {product.material_texture} — all preserved. Every label character locked.

[MOTION]
Primary — light: the soft morning light gently breathes, brightening fractionally as the day wakes.
Secondary — atmosphere: linen shifts microscopically in the gentlest air.
Tertiary — camera: imperceptible 1% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Table, linen positions fixed. Soft light direction and warmth. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Very slow, serene, intimate.

[OUTPUT]
Photoreal intimate lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T15 · Café Outdoor Terrace

**Family:** TF04 · Natural Environment | **Tier:** universal | **Sectors:** F&B, Beauty | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** hard golden-hour, outdoor-natural
**Color story:** Golden-hour warmth across an outdoor terrace. Saturated warm light, deep shadows, café greenery. Product brand color glows as the warm centerpiece. The most color-alive TF04 chain.
**Reference accounts:** @barnscoffee, @cafe.najd, @coffeebeantealeaf.sa | **Cultural Spec:** CS-13, CS-22

**WHEN TO USE:** Golden-hour café moment for F&B (coffee, cold drinks, desserts) and lifestyle brands. Modern Saudi third-wave café culture — Boulevard, Diriyah, Jeddah corniche. Warm, social, aspirational-everyday.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is photographed AT this terrace table — table position, angle, golden-light direction are creative decisions. INTEGRATION: the low golden sun is the single light defining terrace, greenery, and product as one system; the product glows with the same warm cast that backlights the leaves, its long shadow parallel to every other shadow on the terrace.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with golden editorial lift — a high-end phone in real golden-hour light. Material truth: {product.material_texture} — the substrate catches the raking gold truthfully (condensation beads on a cold cup, film creases glowing warm, glass refracting the low sun). Honest café-table wear, warm haze in the air. No CGI render, no over-styled set.

[SCALE CALIBRATION]
{product.dimensions} — true size on a real café table; anchored against the table surface and any companion vessel. An honest tabletop object, never an oversized hero.

[FRAMING & PROXIMITY]
Seated at the table with the product — close, foreground-commanding, terrace world glowing softly behind. The viewer is in the moment, not observing from across the terrace.

[COLOR & CONTRAST]
Saturated golden-hour palette — warm gold light, deep café greens, rich shadow; the product's brand color from {brand.color_field_palette} glows as the warm centerpiece fully alive in the light. The most color-vibrant TF04 chain — hard light, deep shadow, alive.

[LIGHT & LENS]
ONE light: low golden-hour sun raking from the side — warm, directional, hard-edged with long shadows, backlit greenery glowing translucent. Lens and depth chosen for a sharp product in dreamy golden bokeh.

[NATURAL PLACEMENT]
The product sits where a server or hand just placed it — gravity-honest on the table, naturally turned, real contact shadow.

[COMPANION ELEMENTS]
ONE hero companion from {product.companion_elements} (a filled glass of the prepared drink, a small plate, a finjan — one only), in the same golden light with the same physics.

[SCENE]
Golden-hour terrace composition. Product on an outdoor café table, terrace greenery and modern Saudi café architecture in soft golden bokeh behind, golden sky beyond. The warm social pleasure of a modern Saudi café moment (CS-13) — Boulevard, Diriyah, or Jeddah corniche register, never a generic Western coffee shop. Choice points: camera height, sun direction, product turn, companion choice, terrace depth.

[SUBJECT]
Single hero product on the terrace table, café context softly secondary, every surface in the golden light rendered true.

[BRAND CONSTRAINTS]
Single hero product, one companion maximum. No human elements. Modern Saudi café register (CS-13). No readable text on any background object — café signage and menus stay out of focus or text-free. {brand.anti_attributes}

[OUTPUT]
Photoreal lifestyle photography, maximum fidelity. Saturated golden-hour grade — warm gold, café green, glowing brand color. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the café register — Riyadh Boulevard / Diriyah / Jeddah corniche terrace. {saudi.color_palette_adjust} tunes the golden warmth. For Ramadan: post-iftar evening terrace ambiance.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: sun direction, camera height and seat position, product turn, companion, terrace depth and greenery. A different golden evening each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product position, table, terrace context, golden light, {product.material_texture} — all preserved. Every label character locked.

[MOTION]
Primary — atmosphere: terrace greenery sways gently in a soft breeze, backlit leaves shimmering in the gold.
Secondary — light: the golden hour warms fractionally toward sunset, shadows lengthening slightly.
Tertiary — camera: extremely subtle 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Table and product fixed. Greenery sways but doesn't relocate. Golden temperature. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Relaxed warm café pacing.

[OUTPUT]
Photoreal lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T16 · Retail Boutique Interior

**Family:** TF04 · Natural Environment | **Tier:** premium | **Sectors:** Retail, Beauty, Fashion | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** palette discipline (warm retail — busy scene, controlled color)
**Color story:** Sophisticated retail palette — warm display lighting, rich materials (wood, brass, stone), curated neutral backdrop. Product brand color is the curated focal accent.
**Reference accounts:** @tiadress, @planb_boutique, @danatreasures | **Cultural Spec:** CS-13

**WHEN TO USE:** Aspirational retail context for retail, fashion accessories, beauty, premium goods. "This product lives in a beautiful curated Saudi boutique." The environment signals quality tier.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is photographed INSIDE this boutique — display choice, angle, and framing are creative decisions for a curated retail placement. INTEGRATION: the boutique's warm display lighting is the governing light system; the product catches the same pools and accents that model the brass and stone around it, its shadow agreeing with the display lighting's direction.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default broadcast_cinematic with retail-editorial warmth. Material truth: {product.material_texture} — the substrate sits on the display surface as its real self under warm accent light. Real wood grain, brass patina, stone texture; honest directional warmth with soft pools. No CGI render, no sterile showroom.

[SCALE CALIBRATION]
{product.dimensions} — true size on the display: anchored against plinth height and shelf depth. A curated object at honest retail scale.

[FRAMING & PROXIMITY]
At the display, close — the product commands the curated foreground while the boutique glows softly behind. The viewer leans in to the piece, not surveying the store.

[COLOR & CONTRAST]
Palette discipline for a busy scene: warm display light and rich neutral materials (wood, brass, stone) form the controlled field; the product's brand color from {brand.color_field_palette} is the single curated focal accent the lighting celebrates. Background merchandise stays chromatically quiet.

[LIGHT & LENS]
ONE governing light system: warm directional retail display lighting forming soft pools with controlled shadow, a subtle accent on the product within the same system. Lens and depth chosen for a sharp product and softly aspirational boutique depth.

[NATURAL PLACEMENT]
The product is placed as a merchandiser would — square or deliberately angled on the plinth/shelf, gravity-honest with a true contact shadow.

[COMPANION ELEMENTS]
The boutique scene IS the companion — no additional hero prop. Any hint of other curated merchandise stays softly out of focus, chromatically quiet, and text-free.

[SCENE]
High-end boutique composition. Product staged on a curated display surface (wooden plinth, brass shelf, or stone pedestal) within a sophisticated Saudi boutique; warm ambiance, rich materials, an architectural hint behind in soft focus. A beautiful curated retail moment (CS-13). Choice points: display surface, camera height, product angle, background depth.

[SUBJECT]
Single hero product on the display; the boutique context softly secondary, signaling quality and aspiration. Display materials and lighting rendered with authentic truth.

[BRAND CONSTRAINTS]
Single hero product. Boutique context softly secondary. No human elements. NO readable text anywhere in the background — neighboring merchandise, signage, and packaging carry no legible wordmarks; out of focus or plain surfaces only. A real high-end Saudi retail space (CS-13), never a generic Western store. {brand.anti_attributes}

[OUTPUT]
Photoreal retail lifestyle photography, maximum fidelity. Warm aspirational grade — display warmth, rich materials, brand-color focal accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the boutique register — modern Saudi luxury retail (Riyadh malls, boutique districts). {saudi.material_context} can specify Saudi-preferred display materials.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: display surface and material, camera height, product angle, boutique depth and warmth. A different curated corner each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product position, display surface, boutique context, retail lighting, {product.material_texture} — all preserved. Every label character locked.

[MOTION]
Primary — light: display lighting shifts gently, accent highlights sliding fractionally across the product as if from a slowly adjusting source.
Secondary — atmosphere: soft ambient depth, faint bokeh shimmer of boutique lighting.
Tertiary — camera: extremely subtle 2% push-in, drawing the viewer into the curated moment.

[WHAT STAYS STATIC]
Product identity and material texture locked. Display and product fixed. Boutique context stable. Lighting warmth constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Smooth aspirational retail pacing.

[OUTPUT]
Photoreal retail lifestyle cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF06 · STUDIO PRODUCTION REVEAL — 3 chains
**Drama dial: clean even, production-confident** (T22 variant: warm opulent single key)

---

## T21 · Twin Softbox Studio Reveal

**Family:** TF06 · Studio Production Reveal | **Tier:** premium | **Sectors:** Beauty, Retail, F&B | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** clean even, production-confident
**Color story:** Visible softbox lights as part of the frame — the production reveals itself. Clean neutral backdrop, two soft sources glowing. Product brand color is the focal subject the studio is built around.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Self-aware production aesthetic — the studio lights intentionally in frame. For brands that want a confident "we made this with intention" signal. The visible production IS the styling statement.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is the centered subject of a real studio setup; softbox positions, backdrop tone, and camera distance are creative decisions within the self-aware production concept. INTEGRATION: the twin softboxes ARE the scene's light — their wraparound modeling, the floor reflection, and the backdrop falloff all belong to the same two visible sources. (This chain's intentional exception to the single-source rule: TWO matched soft sources acting as one symmetrical system — both visible, both honest.)

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with self-aware production honesty. Material truth: {product.material_texture} — the substrate under even soft light shows its genuine self (true specular from two sources, real film pliability, honest glass weight). The softbox diffusion fabric shows real texture and falloff; subtle floor reflection beneath. No CGI render, no fake-studio flatness.

[SCALE CALIBRATION]
{product.dimensions} — true size between the flanking softboxes; the lights are real studio-scale equipment, the product an honestly sized subject between them. The proportion of equipment to subject is what tells the production story.

[FRAMING & PROXIMITY]
The product commands center frame at close presence, the softboxes glowing at the frame edges — the production surrounds a near hero, not a distant speck on a seamless.

[COLOR & CONTRAST]
Clean neutral studio field (soft grey-white backdrop, glowing white diffusion) sets the confident production base; the product's brand color from {brand.color_field_palette} is the saturated focal subject the entire setup exists to celebrate. No other color competes.

[LIGHT & LENS]
Two large matched softboxes at 45° each side, angled inward, soft even wraparound modeling with minimal harsh shadow — both visibly glowing in frame. Lens and depth chosen for a sharp product with the softboxes softly glowing at the edges.

[NATURAL PLACEMENT]
The product stands or rests at set center as gravity and its substrate dictate — a deliberate studio placement, honestly seated with a true contact reflection.

[SCENE]
Self-aware studio composition. Product centered on a clean seamless backdrop, deliberately flanked by the two visible softboxes — the viewer sees the craft of the shoot. Confident, intentional, production-proud. Choice points: backdrop tone, softbox proximity, camera height, floor reflection strength.

[SUBJECT]
Single hero product, evenly modeled by twin soft sources; the softboxes are intentional compositional elements. Full material truth under the soft even light.

[BRAND CONSTRAINTS]
Single hero product. The two softboxes are the only supporting elements. No human elements. Clean backdrop. {brand.anti_attributes}

[OUTPUT]
Photoreal studio production photography, maximum fidelity. Clean confident grade, brand-color focal punch, visible-production aesthetic. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — minimal localization for studio chains. {saudi.color_palette_adjust} may tune backdrop tone per sector.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: backdrop tone, softbox distance and angle-in, camera height, product rotation, reflection strength. The production concept holds; the frame never repeats.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, twin softboxes, backdrop, floor reflection — all locked.

[MOTION]
Primary — light: the softboxes pulse with extremely subtle luminance breathing, brightening fractionally as if powered on and stabilizing.
Secondary — camera: a slow smooth dolly forward, ~6% closer, the softboxes sliding gently toward frame edges.

[WHAT STAYS STATIC]
Product identity and material texture locked. Softbox and product positions fixed. Backdrop constant. Capture character: clean_studio preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Smooth confident studio pacing.

[OUTPUT]
Photoreal studio cinematography. Silent. No text overlay, no watermark.

---

## T22 · Gold Spotlight Pedestal

**Family:** TF06 · Studio Production Reveal | **Tier:** luxury | **Sectors:** Fragrance, Jewelry, Oud, Luxury Retail | **Intent:** launch | **Frequency:** 1× per quarter | **Reference image:** Required | **Drama dial:** warm opulent single key
**Color story:** Reflective gold pedestal catching warm directional spotlight. Gold-on-warm-dark luxury palette. The product brand color punches against the gold reflectance — opulent, Saudi-luxury-resonant.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-22

**WHEN TO USE:** Opulent pedestal presentation. The gold resonates strongly with Saudi luxury aesthetics. Fragrance, oud, jewelry, premium launches — maximum opulence; the gold pedestal itself signals prestige.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product crowns the gold pedestal; camera angle, pedestal proportion, and spotlight character are creative decisions. INTEGRATION: one warm directional spotlight governs everything — the product's modeling, the pedestal's specular highlights, the gold bounce returning onto the product's lower surfaces, the warm-dark falloff behind. One light, one physical system.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with luxury warmth. Material truth: {product.material_texture} — the substrate catches the warm key and the gold bounce as its true self. Real reflective gold-metal behavior on the pedestal: honest specular highlights, a soft mirror of the product's base. No CGI render, no plastic-gold, no artificial sparkle overlay.

[SCALE CALIBRATION]
{product.dimensions} — true size atop the pedestal; the pedestal is proportioned to present the product (a plinth that serves, never a column that dwarfs). The product-to-pedestal ratio reads as deliberate luxury staging.

[FRAMING & PROXIMITY]
Close, reverent, ascending — the product and gold pedestal-top fill the frame as the luminous center; the warm dark surround presses near.

[COLOR & CONTRAST]
Opulent warm palette: glowing gold pedestal against warm-dark surround; the product's brand color from {brand.color_field_palette} punches against the gold reflectance as the prized focal subject. Two chromatic players only — the gold and the brand color.

[LIGHT & LENS]
ONE warm directional spotlight from upper-side, hard-soft quality modeling product and pedestal together, the gold returning warm fill as part of the same system. Lens and depth chosen for a sharp product and pedestal-top against a softly deepening warm dark.

[NATURAL PLACEMENT]
The product stands centered and plumb on the pedestal — the one deliberate ceremonial placement this chain calls for — honestly seated with a true mirrored contact on the polished gold.

[SCENE]
Opulent pedestal composition. Product atop a reflective gold cylindrical pedestal under the warm spotlight, the polished surface softly mirroring its base, warm dark gradient deepening toward the edges. Prestigious, Saudi-luxury. Choice points: camera height, pedestal height and finish, spotlight angle, background warmth.

[SUBJECT]
Single hero product on the gold pedestal; the reflective gold is the supporting luxury element. Gold reflectance and product material in full physical truth.

[BRAND CONSTRAINTS]
Single hero product. The gold pedestal is the only supporting element. No human elements. Warm dark background. {brand.anti_attributes}

[OUTPUT]
Photoreal luxury product photography, maximum fidelity. Opulent warm-gold grade, brand-color punch. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — gold resonates with Saudi luxury; for Eid/Founding Day a subtle gold particle haze may drift in the warm air. {saudi.color_palette_adjust} tunes the gold warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: camera height, pedestal proportion and finish, spotlight angle and warmth, background depth. Opulence constant; staging fresh.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, gold pedestal, reflection, warm spotlight — all locked.

[MOTION]
Primary — the pedestal: product and pedestal rotate together with extreme slowness, ~20° over the duration, the gold catching shifting highlights. Brand-readable face stays toward camera.
Secondary — atmosphere: faint warm particles drift through the spotlight.

[WHAT STAYS STATIC]
Product identity and material texture locked — sharp through the rotation. Spotlight direction, warm-dark background. Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow opulent pacing.

[OUTPUT]
Photoreal luxury cinematography. Silent. No text overlay, no watermark.

---

## T23 · Gallery Pedestal Solo

**Family:** TF06 · Studio Production Reveal | **Tier:** luxury | **Sectors:** Luxury Retail, Fragrance, Fashion, Beauty | **Intent:** launch | **Frequency:** 1× per quarter | **Reference image:** Required | **Drama dial:** clean even, gallery restraint
**Color story:** Museum-gallery minimalism — soft neutral walls, single clean pedestal, gentle museum lighting. Restrained palette so the product brand color reads as the single art object on display.
**Reference accounts:** @danatreasures, @alyafie_jewelry, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Art-object positioning for luxury launches, designer collaborations, premium fragrance/fashion. The gallery restraint is the prestige signal; less is everything.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product is exhibited as a museum object; pedestal material, wall tone, and viewing angle are curatorial decisions left open. INTEGRATION: one soft museum light system governs product, pedestal, and wall together — the same gentle directional quality, the same soft shadow logic, one coherent gallery atmosphere.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with gallery restraint. Material truth: {product.material_texture} — the substrate presents its genuine surface under museum light. Subtle real wall texture, honest pedestal material (matte stone or painted wood), authentic soft directional shadow. No CGI render, no sterile flatness.

[SCALE CALIBRATION]
{product.dimensions} — true size on a gallery pedestal proportioned to exhibit it; the generous negative space is curated emptiness around an honestly scaled object, never an accidentally tiny one.

[FRAMING & PROXIMITY]
The museum approach: the viewer stands before the piece at contemplation distance — the product clearly the destination of the frame, near enough that its material reads, the negative space deliberate and composed.

[COLOR & CONTRAST]
Deliberately restrained neutral palette (soft gallery white-grey, neutral pedestal) creates museum calm; the product's brand color from {brand.color_field_palette} is the single chromatic event — the art object the gallery exists to display.

[LIGHT & LENS]
ONE soft museum directional light from above-front, gentle quality, controlled soft shadow beneath the product, even gallery ambience as its quiet extension. Lens and depth chosen for a sharp product against a softly neutral wall.

[NATURAL PLACEMENT]
The product stands centered and plumb on the pedestal — deliberate curatorial placement, honestly seated.

[SCENE]
Museum gallery composition. Product atop a minimal clean pedestal (matte white, pale stone, or warm-neutral) in an understated gallery, soft neutral wall with gentle depth behind, generous composed negative space. Reverent, collectible, prestige through restraint. Choice points: pedestal material and height, wall tone, camera height and distance.

[SUBJECT]
Single hero product as gallery art object; pedestal and space deliberately understated; quiet authentic material truth.

[BRAND CONSTRAINTS]
Single hero product on the pedestal. Gallery deliberately minimal — no human elements, no other artworks, no props, no readable wall text. {brand.anti_attributes}

[OUTPUT]
Photoreal fine-art product photography, maximum fidelity. Restrained gallery grade, single brand-color art-object accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — gallery context is culturally neutral; for heritage brands the pedestal may shift to warm Najdi stone. {saudi.color_palette_adjust} tunes wall tone.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: pedestal material and height, wall tone, viewing distance and height, shadow softness. The exhibition changes; the artwork's identity never does.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, pedestal, gallery wall, museum lighting — all locked.

[MOTION]
Primary — camera: a slow, smooth, reverent dolly forward toward the product, ~7% closer — the museum approach.
Secondary — light: museum lighting holds steady with the faintest ambient breathing.

[WHAT STAYS STATIC]
Product identity and material texture locked. Pedestal and product fixed. Gallery wall constant. Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow reverent gallery-approach pacing.

[OUTPUT]
Photoreal fine-art cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF07 · PASTEL & SHADOW PLAY — 4 chains
**Drama dial: bright pastel pop** (the pastels ARE the color block — this family's own register)

---

## T24 · Pink-Mint Split Background

**Family:** TF07 · Pastel & Shadow Play | **Tier:** universal | **Sectors:** Beauty, Retail | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** bright pastel pop
**Color story:** Bold split pastel field — soft pink meeting soft mint, hard color division. Crisp botanical shadow cast across. The pastels ARE the popping color; the product is the clean focal anchor where they meet.
**Reference accounts:** @tiadress, @planb_boutique, @danatreasures | **Cultural Spec:** CS-22

**WHEN TO USE:** Playful pastel pop for beauty, youthful retail, lifestyle brands wanting bright, modern, social-native energy. The bold pastel split is the scroll-stopping hook.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product anchors the split pastel field; the division's angle, the shadow's foliage character, and the product's exact bridge position are creative decisions. INTEGRATION: one bright source lights field and product together AND casts the botanical shadow — the shadow falls across backdrop and product with one continuous geometry; the product's contact shadow belongs to the same light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with crisp modern lift. Material truth: {product.material_texture} — the substrate under bright even light behaves as its real self. The pastel backdrop shows subtle real surface gradient and honest paper/wall texture; the botanical shadow carries authentic soft penumbra edges. No CGI flatness, no fake-sharp shadow.

[SCALE CALIBRATION]
{product.dimensions} — true size against the graphic field; the botanical shadow's fronds are real-foliage scale relative to the product, the split division proportioned so the product genuinely bridges both zones.

[FRAMING & PROXIMITY]
The product near and commanding at the color seam — graphic negative space is part of the design language here, but the hero stays close and large enough that material texture reads.

[COLOR & CONTRAST]
The two pastels ARE the popping color statement — divided graphically at full pastel saturation. Pastel selection serves the brand: defaults of soft pink + soft mint, or substituted from {brand.color_field_palette}-harmonious pastel derivatives (the agent derives pastels the brand can own — never tones borrowed from an unrelated reference). The product's brand color sits as the clean focal anchor, harmonizing or contrasting.

[LIGHT & LENS]
ONE bright source, even and frontal in feel but hard enough to throw the crisp botanical shadow — clean, controlled, the foliage shadow the single intentional shadow event. Lens and depth chosen for crisp product AND crisp shadow.

[NATURAL PLACEMENT]
The product stands or rests at the seam as its substrate honestly sits — plumb bottle, square jar, or a sachet with true pliable lean.

[SCENE]
Split-pastel composition. Background divided into two bold pastel zones with a clean graphic division (vertical or diagonal), the product bridging at the meeting line, a crisp botanical shadow (palm frond, monstera, tropical silhouette) cast across backdrop and partly over the product. Bright, modern, social-native. Choice points: division angle, foliage species, shadow direction, product offset.

[SUBJECT]
Single hero product bridging the pastel zones; the split field and botanical shadow are the styling. Full physical truth under the bright light.

[BRAND CONSTRAINTS]
Single hero product. The split background and ONE botanical shadow are the only elements. No human elements. {brand.anti_attributes}

[OUTPUT]
Photoreal modern commercial photography, maximum fidelity. Bright pastel grade, graphic split, crisp brand-color anchor. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — pastels are culturally neutral; {saudi.color_palette_adjust} can shift toward Saudi-resonant tones (sand-cream + soft sage). For Founding Day: pink-mint can shift to white-green.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: division angle and direction, foliage species and shadow density, product offset, pastel pairing within the brand-derived range. The graphic concept holds; the design never repeats.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, split pastel background, botanical shadow — all locked.

[MOTION]
Primary — the botanical shadow: sways gently as if the casting foliage moves in a soft breeze, drifting subtly across field and product.
Secondary — camera: extremely subtle 2% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Pastel zones fixed. Product position fixed. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Light, breezy, modern pacing.

[OUTPUT]
Photoreal modern commercial cinematography. Silent. No text overlay, no watermark.

---

## T25 · Soft Pink Petals Scatter

**Family:** TF07 · Pastel & Shadow Play | **Tier:** premium | **Sectors:** Beauty, Fragrance, Retail | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** bright pastel pop (romantic-soft register)
**Color story:** Soft romantic pink field with scattered rose petals. Gentle warm-pink monochrome with real petal texture as the only variation. Product brand color is the tender focal accent.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride | **Cultural Spec:** CS-22

**WHEN TO USE:** Romantic feminine beauty — beauty, fragrance, bridal, romantic retail. Tenderness, femininity, gift-worthiness. Strong for bridal season, Mother's Day, romantic launches.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product holds the romantic pink world; petal scatter pattern, density, and product angle are creative decisions. INTEGRATION: one soft beauty light holds petals, field, and product in the same tender glow — petal translucency, product reflectance, and every soft shadow belong to that single source.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with romantic softness. Material truth: {product.material_texture} — the substrate in soft light shows its genuine surface. Rose petals with real velvet texture, natural color variation, soft curling edges, honest translucency where light passes through. No plastic petals, no fake uniform scatter.

[SCALE CALIBRATION]
{product.dimensions} — true size among real rose petals (each petal a few centimeters); the petal-to-product proportion is the honest anchor that sells the scene's reality.

[FRAMING & PROXIMITY]
Close and tender — the product near, petals gathering at its base and drifting past, the soft pink world wrapping a present hero.

[COLOR & CONTRAST]
Soft romantic pink monochrome — background and petals in gentle warm-pink saturation; the product's brand color from {brand.color_field_palette} is the tender focal accent anchoring the romantic world. No third color.

[LIGHT & LENS]
ONE soft diffused beauty light from upper-front, gentle quality, very soft shadow, petal edges glowing translucent. Lens and depth chosen for a sharp product, sharp nearest petals, soft far petals.

[NATURAL PLACEMENT]
The product rests centered with honest gravity; petals lie flat, stand on edge, overlap — natural scatter physics, never rigid arrangement.

[COMPANION ELEMENTS]
The petals ARE this chain's world — no additional companion object enters the frame.

[SCENE]
Romantic petal composition. Product on a soft pink surface, fresh rose petals scattered naturally around its base, a few drifting nearby, the dreamy pink background gentle behind. Tender, feminine, gift-worthy. Choice points: scatter density and pattern, petal freshness character, product turn, camera height.

[SUBJECT]
Single hero product amid the petals; petal texture and product material in full physical truth.

[BRAND CONSTRAINTS]
Single hero product. Rose petals the only styling element. No human elements. Soft pink background. {brand.anti_attributes}

[OUTPUT]
Photoreal romantic beauty photography, maximum fidelity. Soft pink grade, tender brand-color accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — suits bridal/gift contexts; for Saudi wedding season petals may include Damask rose (ward taifi from Taif). {saudi.color_palette_adjust} tunes pink warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: scatter density and pattern, drifting-petal count, camera height, product turn, pink depth. A different romantic moment each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, scattered petals, soft pink background — all locked.

[MOTION]
Primary — petals: one or two drift down slowly from above, settling near the product; existing petals shift microscopically in gentle air.
Secondary — light: the soft beauty light gently breathes.
Tertiary — camera: imperceptible 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product position fixed. Background constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle romantic pacing — petals drift like a soft moment.

[OUTPUT]
Photoreal romantic beauty cinematography. Silent. No text overlay, no watermark.

---

## T26 · Ribbon Flat Lay Tactile

**Family:** TF07 · Pastel & Shadow Play | **Tier:** premium | **Sectors:** Beauty, Retail, Fashion, Fragrance | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** bright pastel pop (tactile-sheen register)
**Color story:** Flowing satin ribbon in soft pastel sheen, top-down flat lay. Tactile fabric highlights catch light. Product brand color is the focal jewel on the fabric.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Tactile gift-worthy flat lay for beauty, fragrance, fashion accessories, gift-set launches. The satin sheen communicates luxury and giftability. Strong for gifting occasions.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved through the overhead angle: {product.identity_dna}
The product rests in the top-down flat lay with brand-readable face up; the ribbon's flow path, curve language, and the product's position on or beside it are creative decisions. INTEGRATION: one overhead light system holds ribbon and product together — the sheen rolling along the satin folds and the product's top-light reflectance come from the same source; their soft shadows share one direction.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with tactile sheen. Material truth: {product.material_texture} — the substrate viewed from above presents its true top surfaces. The satin shows real silky sheen with honest highlight rolloff along folds, authentic weave, natural drape and curl; the pastel surface gently textured. No plastic ribbon, no fake-perfect drape.

[SCALE CALIBRATION]
{product.dimensions} — true size against standard ribbon width (a few centimeters); the ribbon flows in honest proportion to the product it presents.

[FRAMING & PROXIMITY]
The flat lay frames close — the ribbon's curves lead directly to a near, generous hero; no vacant tabletop expanses.

[COLOR & CONTRAST]
Soft pastel base (blush, champagne, or sage — chosen or derived to harmonize with {brand.color_field_palette}, never borrowed from an unrelated reference) with the ribbon's silky sheen as luminous texture; the product's brand color is the focal jewel resting on the fabric.

[LIGHT & LENS]
ONE soft overhead system with a slight directional bias to roll the sheen along the satin folds; gentle controlled shadow. Perfectly overhead framing; full flat-lay sharpness.

[NATURAL PLACEMENT]
Top-down placement with honest physics: the product lies or sits with true weight on/beside the fabric, the ribbon draping and curling as real satin does under it and around it.

[COMPANION ELEMENTS]
The ribbon IS the companion — one ribbon, no further props.

[SCENE]
Top-down flat lay. A length of satin ribbon flows across the frame in elegant curves and folds; the product rests on or beside it, face up, on a soft complementary pastel surface. Curated-tactile, gift-worthy, social-native. Choice points: ribbon path and curl language, product position, pastel pairing, sheen direction.

[SUBJECT]
Single hero product on the ribbon, viewed top-down; ribbon sheen and product material in full physical truth.

[BRAND CONSTRAINTS]
Single hero product. ONE satin ribbon is the only styling element. No human elements. Soft pastel surface. {brand.anti_attributes}

[OUTPUT]
Photoreal flat-lay commercial photography, maximum fidelity. Soft pastel grade, satin sheen, brand-color focal jewel. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — gift-worthy flat lay suits Eid and wedding gifting; ribbon can shift to gold satin for premium Saudi occasions. {saudi.color_palette_adjust} tunes pastel tone.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: ribbon path, curve and curl language, product position relative to the flow, pastel pairing, sheen direction. The gift moment re-stages every time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, satin ribbon, pastel surface — all locked. Top-down framing preserved.

[MOTION]
Primary — the ribbon: loose ends shift gently as if from a soft breath of air, the sheen sliding along the folds as they move microscopically.
Secondary — light: the directional sheen highlight drifts subtly across the satin.
Tertiary — camera: imperceptible 1.5% overhead push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product position fixed. Top-down angle constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle tactile pacing.

[OUTPUT]
Photoreal flat-lay cinematography. Silent. No text overlay, no watermark.

---

## T27 · Cherry Blossom Backdrop

**Family:** TF07 · Pastel & Shadow Play | **Tier:** premium | **Sectors:** Beauty, Fragrance, Retail | **Intent:** launch, grow | **Frequency:** 1× per month (seasonal) | **Reference image:** Required | **Drama dial:** bright pastel pop (dreamy-spring register)
**Color story:** Soft cherry-blossom pink with delicate white-pink blossoms, petals drifting. Dreamy spring palette with airy depth. Product brand color is the fresh focal note in the blossom haze.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride | **Cultural Spec:** CS-22

**WHEN TO USE:** Spring blossom dreaminess for beauty, fragrance, spring/seasonal launches. Renewal, freshness, delicate beauty.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The product holds the sharp foreground against the blossom world; the blossoms' density, the drifting petals' paths, and the product's angle are creative decisions. INTEGRATION: one soft spring light holds the whole frame — blossoms glowing translucent in it, the product catching it with the same gentle quality, all soft shadows in one direction.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with dreamy spring softness. Material truth: {product.material_texture} — the substrate in soft spring light presents its true surface. Blossoms with real petal delicacy, natural white-to-pink gradient, honest branch texture; drifting petals with authentic motion-soft edges. No plastic blossoms, no fake-perfect bloom.

[SCALE CALIBRATION]
{product.dimensions} — true size against real blossom scale (each bloom small, branches fine); the product is honestly proportioned in front of a real flowering depth.

[FRAMING & PROXIMITY]
The product close and sharp in the foreground, the blossom field opening in dreamy depth behind — hero through nearness, the spring world as atmosphere.

[COLOR & CONTRAST]
Dreamy spring palette — soft white-pink blossoms creating the airy depth field; the product's brand color from {brand.color_field_palette} is the fresh focal note standing clear against the blossom haze. Two players: blossom-pink and brand color.

[LIGHT & LENS]
ONE soft diffused spring daylight, gentle quality, airy soft shadow, backlit blossoms glowing translucent. Lens and depth chosen for a sharp product, dreamy blossom bokeh, soft drifting petals.

[NATURAL PLACEMENT]
The product stands or rests with honest gravity at the foreground's natural surface.

[COMPANION ELEMENTS]
The blossoms ARE the chain's world — no further companion object.

[SCENE]
Cherry blossom composition. Product sharp in the foreground, cherry blossom branches in full bloom filling the background in dreamy bokeh, a few petals drifting mid-fall around it, soft spring light bathing everything. Fresh, delicate, renewal. Choice points: blossom density, petal count and drift paths, product turn, camera height.

[SUBJECT]
Single hero product sharp in the foreground; the blossom backdrop dreamy behind; blossom texture and product material in authentic truth.

[BRAND CONSTRAINTS]
Single hero product in foreground. Cherry blossoms are the backdrop element. No human elements. {brand.anti_attributes}

[OUTPUT]
Photoreal spring beauty photography, maximum fidelity. Dreamy spring grade, soft blossom field, fresh brand-color focal note. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — blossom backdrop is seasonal-neutral; for Saudi spring, shift to almond blossom or local flowering varieties. {saudi.color_palette_adjust} tunes blossom tone.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: blossom density and depth, drifting-petal paths, product turn, camera height, light softness. Spring renews differently each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, blossom backdrop, drifting petals — all locked.

[MOTION]
Primary — petals: blossom petals drift down gently and continuously through the frame around the product, a soft falling-blossom motion.
Secondary — backdrop: blossom branches sway very gently, the bokeh shimmering.
Tertiary — camera: imperceptible 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product position fixed and sharp. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle drifting spring pacing.

[OUTPUT]
Photoreal spring beauty cinematography. Silent. No text overlay, no watermark.

---
---

# BATCH 1 · AGENT RUNTIME NOTES

**Block inclusion in this batch:**
- [NATURAL PLACEMENT] present on all 16 (studio/dark-stage chains carry the deliberate-placement variant).
- [COMPANION ELEMENTS] active with {product.companion_elements} on T12, T13, T15 (one hero companion). Declared structurally absent/self-contained on T14 (minimal), T16 (scene-is-companion), all TF03, TF06 (pedestal/softboxes are structural), all TF07 (petals/ribbon/blossoms are the chain concept).
- [SAUDI ADAPTATION] and [TEXT OVERLAY] conditional on every chain — omit entirely when not triggered.

**Drama dial in this batch:** TF03 = single hard key, deep dark (T09 luminous-halo variant) · TF04 = soft natural (T15 hard golden-hour outdoor, T16 palette discipline) · TF06 = clean even production-confident (T22 warm opulent single key) · TF07 = bright pastel pop.

**Single-light rule notes:** T21 carries the family's one declared exception — two matched softboxes acting as one symmetrical visible-production system. T24's single source both lights and casts the botanical shadow. Everywhere else: one hard/soft source governs all.

**Failure-ledger compliance:** all 16 chains carry the 15-block order, {product.material_texture}, {product.dimensions} proportion anchoring, brand-derived color via {brand.color_field_palette}, framing-proximity, natural placement, companion restraint, no-readable-background-text (T15, T16 explicit), conditional text block, and the CREATIVE VARIANCE DIRECTIVE. No fixed mm / f-stop / Kelvin commands remain — light is specified by intent and character.

**Char discipline:** image prompts in this batch run well under the 8,000-char block ceiling; video prompts under 2,500. T10 video stays within the Seedance 2,000-char limit.

*OpenClaw · Master Prompt Library v3.7 · Batch 1 · TF03 + TF04 + TF06 + TF07 · 16 chains · Confidential*

<!-- ══════════ OpenClaw_v3_7_Batch2_TF08_TF09_TF10_TF11_TF12.md ══════════ -->

# FAMILY TF08 · CINEMATIC ENVIRONMENT — 5 chains
**Drama dial: full editorial punch** (T29 warm-chiaroscuro variant · T30/T31 epic-landscape variants)

---

## T28 · Rain-Slick Neon Street

**Family:** TF08 · Cinematic Environment | **Tier:** premium | **Sectors:** Fashion, Tech, Beauty (bold), Retail (youth) | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** full editorial punch (maximum saturation)
**Color story:** Wet asphalt mirroring saturated neon — electric magenta, cyan, deep blue reflections. Cyberpunk-noir maximum saturation. Product brand color cuts through the neon haze as the sharp hero accent.
**Reference accounts:** @planb_boutique, @tiadress | **Cultural Spec:** CS-13

**WHEN TO USE:** Cyberpunk-noir energy for bold fashion, tech, youth retail, statement beauty. Riyadh Boulevard night energy, youthful drops. Maximum chromatic intensity.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Street position, camera angle, and neon arrangement are creative decisions. INTEGRATION: the product lives inside this night street — the neon colors that bleed across the wet asphalt also rim the product's edges; its reflection sits in the same wet mirror as the signs'; one continuous night-light system.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with cyberpunk grade, deep dynamic range. Material truth: {product.material_texture} — the substrate catches multiple colored sources as its real self (film creases carrying magenta rim, glass refracting cyan, metal edge-lighting true). Wet asphalt with real water-sheen, neon reflections breaking on the rippled surface, authentic glow bloom and color bleed. No flat digital neon, no plastic-wet surface.

[SCALE CALIBRATION]
{product.dimensions} — true size on the street surface or ledge; the neon signs read at real urban-signage scale behind, the product an honest street-level object before the glowing depth.

[FRAMING & PROXIMITY]
Low and close at street level — the product near and commanding, its wet reflection immediate, the neon city receding in dramatic bokeh. The viewer crouches with the hero in the night.

[COLOR & CONTRAST]
Maximum chromatic intensity — electric magenta, cyan, and deep blue neon at full saturation reflecting on wet asphalt; the product's brand color from {brand.color_field_palette} cuts through the neon haze as the sharp hero accent. The neon palette bends to flatter the brand color, never to drown it.

[LIGHT & LENS]
The neon signs ARE the light system — multiple saturated colored sources acting as one coherent night-street logic: colored rim and edge light on the product, the wet surface mirroring it, deep night shadow between the highlights. Lens and depth chosen for a sharp product against dramatic neon bokeh.

[NATURAL PLACEMENT]
The product sits on the wet surface as gravity placed it — standing, leaning, or lying with honest contact, its reflection true to its posture.

[SCENE]
Rain-slick neon street. Product on wet reflective ground or a wet ledge on a night street, saturated neon glowing in the background bokeh, colors bleeding across the wet surface around it. Cyberpunk-noir, urban-night, bold. Choice points: neon color balance, camera height, reflection prominence, street depth.

[SUBJECT]
Single hero product on the wet surface; the neon environment and wet reflections are the cinematic styling, in full physical truth.

[BRAND CONSTRAINTS]
Single hero product. No human elements. No real-brand neon signage and NO readable text in any sign — generic glowing shapes/colors only. {brand.anti_attributes}

[OUTPUT]
Photoreal cyberpunk-noir photography, maximum fidelity. Maximum-saturation neon grade, wet reflections, sharp brand-color hero accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — modern Riyadh Boulevard night aesthetic (CS-13), not a generic Tokyo/Western cyberpunk cliché. {saudi.color_palette_adjust} tunes the neon palette.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: neon color mix and placement, camera height, wet-surface character, street depth, product posture. The night never repeats.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, wet surface, neon reflections, night street — all locked.

[MOTION]
Primary — neon: signs flicker and pulse subtly, colored reflections shimmering and rippling on the wet surface around the product.
Secondary — atmosphere: faint drizzle or mist drifts through the colored light; a subtle wisp of street steam.
Tertiary — camera: extremely subtle 2% lateral drift.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product position fixed. Neon sources stable (flicker, don't relocate). Capture character: broadcast_cinematic preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Moody urban-night pacing.

[OUTPUT]
Photoreal cyberpunk-noir cinematography. Silent. No text overlay, no watermark.

---

## T29 · Library Light Beam

**Family:** TF08 · Cinematic Environment | **Tier:** premium | **Sectors:** Fragrance, Luxury Retail, Heritage, Beauty | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** warm tungsten chiaroscuro (scholarly)
**Color story:** Deep warm wood tones, dust-filled golden beam cutting through dim library air. Scholarly warm-amber palette with rich shadow. Product brand color glows where the beam lands.
**Reference accounts:** @danatreasures, @alyafie_jewelry, @diplomat_sweets | **Cultural Spec:** CS-13

**WHEN TO USE:** Scholarly heritage atmosphere for fragrance, premium retail, heritage brands, intellectual/refined positioning. Warm, contemplative, prestigious.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Table position, beam angle, and library depth are creative decisions. INTEGRATION: one warm beam governs the whole room — it lands on the product, fills the air with lit dust, and leaves the shelving in the same warm shadow; the product's reflectance and shadow belong to that single diagonal light.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — scholarly cinema, subtle warm grain in shadow. Material truth: {product.material_texture} — the substrate catches the warm beam as its true self on the dark polished wood. Real wood grain and age patina, authentic dust-filled volumetric scatter, true material depth in the shadowed shelving. No flat digital beam, no plastic wood.

[SCALE CALIBRATION]
{product.dimensions} — true size on the reading table; anchored against table depth and the book spines behind. An honest table-top object in a grand dim room.

[FRAMING & PROXIMITY]
At the table with the product — close in the beam's landing pool, the library's warm depth receding behind. The viewer leans into the lit moment.

[COLOR & CONTRAST]
Scholarly warm-amber palette — deep wood browns, dim golden shadow; the product's brand color from {brand.color_field_palette} glows where the beam lands as the single illuminated focal point in the warm dim space.

[LIGHT & LENS]
ONE dramatic warm beam from a high side angle (as from a tall window), cutting diagonally through dust-filled air; deep warm shadow fills the rest. Lens and depth chosen for a sharp product and beam with softly atmospheric library depth.

[NATURAL PLACEMENT]
The product rests on the table as a reader's hand left it — gravity-honest, true contact shadow on the polished wood.

[SCENE]
Old library composition. Product on a dark polished wooden table in the warm diagonal beam, dust motes floating visibly, rich wooden shelving and rows of books softly out of focus in warm shadow behind. Scholarly, contemplative, timeless. Choice points: beam angle, table position, library depth, dust density.

[SUBJECT]
Single hero product in the beam; the library and dust-filled light are the cinematic styling, in authentic truth.

[BRAND CONSTRAINTS]
Single hero product. The library softly secondary. No human elements. No readable book titles or text anywhere — generic spines only. {brand.anti_attributes}

[OUTPUT]
Photoreal cinematic heritage photography, maximum fidelity. Warm scholarly grade, dust-filled beam, glowing brand-color focal point. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — the library can shift toward a traditional Saudi/Islamic scholarly aesthetic: warm Najdi wood, Arabic manuscript context (generic, non-readable), brass details (CS-13). {saudi.color_palette_adjust} tunes warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: beam angle and width, table position, library depth and shelving character, dust density. A different contemplative hour each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, table, beam, library context — all locked.

[MOTION]
Primary — the beam: dust motes drift slowly through the volumetric light, swirling gently in warm air.
Secondary — light: the beam's intensity breathes subtly as if clouds pass the distant window.
Tertiary — camera: extremely subtle 1.5% push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product and table fixed. Library context stable. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow contemplative scholarly pacing.

[OUTPUT]
Photoreal cinematic heritage cinematography. Silent. No text overlay, no watermark.

---

## T30 · Desert Sand Dune Placement

**Family:** TF08 · Cinematic Environment | **Tier:** premium | **Sectors:** F&B, Beauty, Fragrance, Fashion, Heritage | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** epic golden landscape (hard low sun)
**Color story:** Golden Saudi desert dune — warm sand tones, deep ridge shadows, vast clear sky gradient. The desert IS the Saudi-native color world. Product brand color anchors against the endless golden sand.
**Reference accounts:** @aseeb.najd, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-13, CS-22

**WHEN TO USE:** The signature Saudi-native landscape chain — Empty Quarter / AlUla / Nafud dune aesthetic. For any brand wanting to root deeply in Saudi land and identity. Cinematic and unmistakably Saudi.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Dune position, ridge geometry, and horizon height are creative decisions. INTEGRATION: the low desert sun is the one light over everything — it sculpts the ridge shadows, warms the product's surfaces, and grades the sky; the product's long shadow runs with the dune's own; fine sand gathers honestly at its base.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with Saudi-landscape grade. Material truth: {product.material_texture} — the substrate sits in real sand as its true self (film with warm-lit creases, glass catching desert glare, fine grains resting against its base edge). Real sand grain, wind-rippled patterns, honest ridge shadows, authentic desert-sky gradient. No flat digital sand.

[SCALE CALIBRATION]
{product.dimensions} — true size against the desert's vastness: the product is an honest small human-made object on an immense dune; sand ripples read at real centimeter scale around it. The scale contrast IS the drama — never an artificially giant product on a miniature dune.

[FRAMING & PROXIMITY]
Close to the product on the sand — the hero near and grounded while the ridge curves away and the vast horizon opens behind. Epic depth earned through a near foreground, not a distant speck.

[COLOR & CONTRAST]
The Saudi desert IS the color world — warm golden sand at full saturation, deep ridge shadows, blue-gold sky gradient; the product's brand color from {brand.color_field_palette} anchors against the endless golden landscape as the human-made focal point.

[LIGHT & LENS]
ONE light: strong low golden-hour desert sun, raking warmly across the ridges, long elegant shadows, sculpted sand texture revealed. Lens and depth chosen for a sharp product and near dune with an atmospheric distant horizon.

[NATURAL PLACEMENT]
The product rests on the sand exactly as gravity and the slope dictate — settled slightly into the surface, leaning with the grade if its substrate leans, fine grains against its base.

[SCENE]
Saudi desert dune composition. Product on the crest or warm-lit slope of a golden dune, the wind-sculpted ridge curving away, vast horizon and gradient sky beyond, fine windblown sand catching light at its base. Empty Quarter, Nafud, or AlUla register — vast, golden, iconic, deeply Saudi-native. Choice points: ridge geometry, horizon height, sun direction, sand drift.

[SUBJECT]
Single hero product on the sand; dune and sky the epic Saudi-native environment, in authentic truth.

[BRAND CONSTRAINTS]
Single hero product. No human elements, no footprints, no vehicles. Authentic Saudi desert (CS-13), not generic Sahara or Hollywood. {brand.anti_attributes}

[OUTPUT]
Photoreal Saudi landscape photography, maximum fidelity. Epic golden desert grade, vast sky, brand-color anchor. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the specific desert — Empty Quarter (Rub al Khali) red dunes, Nafud golden, or AlUla rock-and-sand. {saudi.color_palette_adjust} tunes sand tone. For Founding/National Day: subtle Saudi-green or flag-tone accent possible.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: ridge geometry, sun direction and height, horizon line, sand-drift presence, camera height. The desert composes itself differently each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, dune, ridge, sky gradient — all locked.

[MOTION]
Primary — sand: fine windblown sand drifts gently across the dune surface and around the product's base, the desert breeze made visible.
Secondary — light: the golden sun shifts subtly, ridge shadows lengthening and warming toward deeper gold.
Tertiary — camera: extremely subtle 2% push-in or slow rise revealing more horizon.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product position fixed. Dune form stable (sand drifts, the dune holds). Sky gradient constant. Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow epic desert pacing — vast and unhurried.

[OUTPUT]
Photoreal Saudi landscape cinematography. Silent. No text overlay, no watermark.

---

## T31 · Foggy Cityscape Above Clouds

**Family:** TF08 · Cinematic Environment | **Tier:** premium | **Sectors:** Tech, Fashion, Fragrance, Corporate | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** epic cool atmospheric
**Color story:** Modern Riyadh skyline emerging from soft fog — cool blue-grey atmosphere with warm tower lights piercing through. Epic urban gradient. Product brand color is the bold focal cut against the misty depth.
**Reference accounts:** @planb_boutique, @danatreasures | **Cultural Spec:** CS-13

**WHEN TO USE:** Epic urban-aspirational for tech, fashion, fragrance, corporate, Vision-2030 era brands. Ambition, modernity, reach — Riyadh towers, KAFD.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Foreground surface, skyline arrangement, and fog density are creative decisions. INTEGRATION: one atmospheric light system holds frame — the cool diffused light that softens the towers also wraps the product, with the warm tower lights as accents within the same fog; the product's cool rim and soft shadow belong to that atmosphere.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with epic-urban grade. Material truth: {product.material_texture} — the substrate in cool ambient light reads true (matte film holding the cool cast, glass edge-lit against the mist). Real fog density variation, honest architectural detail emerging and dissolving, authentic glow bloom of tower lights through mist. No flat digital fog.

[SCALE CALIBRATION]
{product.dimensions} — true size on its foreground ledge; the towers read at real architectural scale in the atmospheric distance. The product is honest and near; the city is vast and far.

[FRAMING & PROXIMITY]
The product sharp and close on the foreground ledge, the misty skyline opening in layered depth behind — aspiration framed from an intimate vantage.

[COLOR & CONTRAST]
Epic urban gradient — cool blue-grey fog with warm tower lights glowing through; the product's brand color from {brand.color_field_palette} is the bold focal cut against the misty depth. Three registers: cool atmosphere, warm city accents, brand cut.

[LIGHT & LENS]
ONE atmosphere: cool diffused daylight or blue-hour light through fog, soft ambient on the product with a cool rim, warm tower accents piercing within it. Lens and depth chosen for a sharp product against atmospheric cityscape depth.

[NATURAL PLACEMENT]
The product stands or rests on the implied ledge with honest gravity and a true contact shadow in the soft light.

[SCENE]
Foggy cityscape composition. Product sharp in the foreground; a modern skyline emerges from soft fog or rises above clouds behind — towers piercing the mist, lights glowing, atmospheric layers receding. Epic, ambitious, Vision-2030-era aspiration. Choice points: fog density, skyline arrangement, blue-hour vs morning haze, foreground surface.

[SUBJECT]
Single hero product in sharp foreground; the misty cityscape the epic aspirational backdrop, in authentic truth.

[BRAND CONSTRAINTS]
Single hero product. No human elements. No identifiable real-brand building signage and NO readable text anywhere — generic modern towers. {brand.anti_attributes}

[OUTPUT]
Photoreal epic-urban photography, maximum fidelity. Cool aspirational grade, foggy depth, bold brand-color focal cut. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — the skyline reads as modern Riyadh (Kingdom Tower, KAFD, Vision-2030 architecture) emerging from morning haze (CS-13), not generic NYC/Dubai. {saudi.color_palette_adjust} tunes fog and light tone.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: fog density and movement, skyline composition, hour of light, foreground surface and camera height. The city emerges differently each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, foggy cityscape, tower lights — all locked.

[MOTION]
Primary — fog: drifts slowly across the cityscape, towers emerging and softening, lights glimmering through.
Secondary — light: blue-hour light shifts fractionally, tower lights twinkling subtly.
Tertiary — camera: extremely subtle 2% push-in or slow rise.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product fixed and sharp. Skyline stable (fog moves, buildings hold). Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow epic aspirational pacing.

[OUTPUT]
Photoreal epic-urban cinematography. Silent. No text overlay, no watermark.

---

## T32 · Brutalist Architecture Portrait

**Family:** TF08 · Cinematic Environment | **Tier:** premium | **Sectors:** Fashion, Tech, Beauty (bold), Fragrance (modern) | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** full editorial punch (hard architectural)
**Color story:** Raw concrete in warm-grey and sand tones, hard directional sun, strong geometric shadow. Minimal monochrome-architectural palette. Product brand color is the single bold chromatic statement.
**Reference accounts:** @planb_boutique, @tiadress, @danatreasures | **Cultural Spec:** CS-13, CS-22

**WHEN TO USE:** Modern editorial architecture for bold fashion, tech, modern fragrance, statement beauty. Contemporary design confidence; editorial-magazine aesthetic. Concrete restraint with brand-color boldness.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference image teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The concrete forms, shadow geometry, and product position are creative decisions. INTEGRATION: one hard sun governs concrete and product — the same crisp geometric shadows that cut the planes cut across or beside the product; its surface carries the sun's raking angle and the concrete's warm bounce.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with architectural-editorial grade. Material truth: {product.material_texture} — the substrate under hard sun reads true (raking light revealing film grain-creases or glass edge highlights). Real board-form concrete texture, honest aggregate, weathering marks, crisp true-edged shadows. No flat digital concrete.

[SCALE CALIBRATION]
{product.dimensions} — true size on or against the architectural forms; ledges and planes read at real built scale, the product an honest object within monumental geometry.

[FRAMING & PROXIMITY]
The product near, framed by the geometry — close enough that material reads, the architectural lines leading to it rather than dwarfing it into the distance.

[COLOR & CONTRAST]
Minimal monochrome-architectural palette — warm-grey and sand-toned concrete with strong shadow geometry; the product's brand color from {brand.color_field_palette} is the single bold chromatic statement punching against the restrained concrete world.

[LIGHT & LENS]
ONE hard directional sun creating crisp geometric shadows across the planes — strong contrast between lit concrete and shadow. Lens and depth chosen for crisp product AND crisp architecture.

[NATURAL PLACEMENT]
The product sits on the ledge or against the plane as gravity places it — square, leaning, or lying honestly with a true hard-light contact shadow.

[SCENE]
Brutalist architecture composition. Product on or against raw concrete forms — clean geometric planes, angular ledges, board-formed walls — hard sun raking across, geometric shadows becoming part of the composition. Contemporary, confident, editorial. Choice points: shadow geometry, plane arrangement, product position, camera angle.

[SUBJECT]
Single hero product against the concrete; the architecture and geometric shadows the modern editorial styling, in authentic truth.

[BRAND CONSTRAINTS]
Single hero product. No human elements. Generic brutalist architecture — no identifiable real buildings, no readable signage or text. {brand.anti_attributes}

[OUTPUT]
Photoreal architectural-editorial photography, maximum fidelity. Minimal concrete grade, geometric shadow, bold brand-color statement. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — modern Saudi brutalist/contemporary design (KAFD, modern Riyadh civic architecture), warm sand-toned concrete rather than cold grey (CS-13). {saudi.color_palette_adjust} warms the concrete tone.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: shadow angles and geometry, plane composition, sun height, product position, camera angle. The geometry recomposes every time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, concrete architecture, geometric shadows — all locked.

[MOTION]
Primary — light: the hard sun shifts angle slowly, crisp geometric shadows sliding across the planes and product — architectural shadow play in motion.
Secondary — atmosphere: faint dust or heat shimmer in the strong sunlight.
Tertiary — camera: extremely subtle 2% push-in or lateral track along the lines.

[WHAT STAYS STATIC]
Product identity and material texture locked. Product fixed. Architecture stable (shadows move, concrete holds). Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow confident editorial pacing.

[OUTPUT]
Photoreal architectural-editorial cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF09 · PORTRAIT & MODEL — 5 chains
**Drama dial: clean editorial** (T35 warm golden urban · T36 luminous beauty-soft)
**Family-wide identity-tier rules:** SINGLE SUBJECT only, never a group. Modesty register {brand.modesty_register} per CS-24/CS-01, never violated in any frame. Real skin texture, never plastic. Video: ONE primary motion only.

---

## T33 · Hijab Full-Figure Colored Backdrop

**Family:** TF09 · Portrait & Model | **Tier:** premium | **Sectors:** Retail, Beauty, Fashion | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required (product/brand reference; model generated) | **Drama dial:** clean editorial, high-saturation backdrop
**Color story:** Single vivid solid-color studio backdrop against which the model and her modest fashion pop. Backdrop color and brand/garment color are the two chromatic anchors.
**Reference accounts:** @tiadress, @themodestbride, @planb_boutique | **Cultural Spec:** CS-24, CS-01, CS-22

**WHEN TO USE:** Editorial modest-fashion hero for modest fashion retail, abaya brands, beauty. The bold backdrop color is the scroll-stopping hook.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity (garment, product, or brand palette). Identity DNA, preserved across any camera angle: {product.identity_dna}
Pose, gesture, and framing (full-figure or three-quarter) are creative decisions; the featured garment/product reads brand-accurate, brand-readable surfaces camera-friendly if held. INTEGRATION: one studio light system models her and saturates the backdrop together — her rim light separates her from the same color field her shadow falls within.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with editorial-fashion lift. Material truth: {product.material_texture} for any featured product; the garment fabric drapes with true weight and natural fold shadows. Real Saudi skin: natural pores, honest individual variation, warm authentic undertone; expression real and self-possessed. No plastic skin, no porcelain uniformity, no over-retouching.

[SCALE CALIBRATION]
{product.dimensions} for any held/worn product — true to-hand and to-body scale; the garment's proportions honest to a real wearer.

[FRAMING & PROXIMITY]
Full-figure or three-quarter, the model commanding the frame against the pure color — confident editorial presence, never a small distant figure in empty backdrop.

[COLOR & CONTRAST]
The vivid solid backdrop is one bold chromatic anchor at full saturation, chosen from or harmonized to {brand.color_field_palette} — the agent derives a tone the brand can own (e.g., deep teal, rich terracotta, royal blue, warm mustard, as brand-compatible candidates), never a color borrowed from an unrelated reference. The garment/brand color is the second anchor; skin reads warm and true.

[LIGHT & LENS]
Clean editorial studio system: large soft key from upper-front, gentle fill, subtle hair/rim light separating model from backdrop — even fashion-catalog clarity with soft modeling shadow. Lens and depth chosen for a sharp model against a cleanly saturated field.

[NATURAL PLACEMENT]
Her pose is a real body's pose — weight honestly carried, fabric falling with gravity, mid-gesture or composed stillness as a human truly stands.

[SCENE]
Editorial modest-fashion composition. A SINGLE Saudi woman, full-figure or three-quarter, posed confidently against the vivid solid backdrop. Fashion-editorial: relaxed-powerful. The featured garment/product clearly presented. Choice points: pose and gesture, backdrop tone (brand-derived), crop, camera height.

[SUBJECT]
ONE Saudi woman only — never a group. Modesty register {brand.modesty_register} from the 4-point spectrum (CS-24 governs):
- traditional: full hijab, conservative elegant abaya, fully covered, refined
- mainstream: neatly styled hijab, modest fashionable abaya, contemporary everyday Saudi
- modern: loose elegant scarf with front waves of hair visible at the hairline, fashion-forward modest outfit, statement jewelry
- editorial: fashion-forward styled hair visible with artful scarf draping, high-fashion modest silhouette, bold styling
Saudi cosmopolitan features, warm honey-bronze skin, contemporary makeup appropriate to register, confident self-possessed expression, real skin texture.

[BRAND CONSTRAINTS]
SINGLE subject only — one woman, never a group, no other people in frame. Modesty maintained per register, never violated. Authentic modern Saudi fashion (CS-01, CS-24) — not Western generic, not costume-orientalist. No readable text anywhere in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal editorial fashion photography, maximum fidelity. Confident high-saturation grade — bold backdrop, true skin, brand-color presence. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills exact abaya/hijab styling by region and register (CS-01, CS-24). {saudi.color_palette_adjust} tunes backdrop toward Saudi-resonant tones. For Founding/National Day: backdrop or styling may incorporate Saudi green.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: pose and gesture, backdrop tone within the brand-derived range, crop and camera height, styling details within register. Her identity rules hold; the editorial moment is new each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The model's appearance, modest styling, garment, backdrop color, every brand-readable element — all preserved character-perfect. Modesty maintained across every frame.

[MOTION]
SINGLE primary motion only (validated for human content): ONE subtle natural action — a slow confident turn of the head toward camera, OR a gentle hand adjustment of the garment, OR a soft natural smile forming. The rest stays composed. NO multi-limb choreography.
Secondary: abaya/scarf fabric shifts naturally with the single motion, modesty preserved throughout.

[WHAT STAYS STATIC]
Facial features, skin tone, modest styling, garment, backdrop color — all locked. Modesty compliance absolute. Capture character preserved. Camera steady.

[PACING & DURATION]
5 seconds. Continuous single take. Calm confident editorial pacing — one believable human moment.

[OUTPUT]
Photoreal editorial fashion cinematography. Silent. No text overlay, no watermark.

---

## T34 · Thobe On Geometric Cube

**Family:** TF09 · Portrait & Model | **Tier:** premium | **Sectors:** Retail, Fashion, Grooming | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required (product/brand reference; model generated) | **Drama dial:** clean editorial, graphic contrast
**Color story:** Crisp white thobe against a bold saturated geometric prop and clean backdrop. White-on-bold-color contrast. Brand/product color is the third accent note.
**Reference accounts:** @planb_boutique, @tiadress | **Cultural Spec:** CS-01, CS-22

**WHEN TO USE:** Modern menswear editorial for menswear, men's grooming, modern retail. Contemporary confident Saudi masculinity; the white thobe against bold color is the graphic hook.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Seated posture, cube position, and backdrop tone are creative decisions; any featured product reads brand-accurate, camera-friendly if held. INTEGRATION: one studio system lights man, cube, and backdrop together — his rim separation, the cube's clean shading, and his soft grounded shadow share the same light logic.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with modern editorial lift. Material truth: {product.material_texture} for any featured product; the white thobe shows authentic cotton crispness, natural fold shadows, true white (never blown out). Real Saudi skin, honest texture, warm undertone, composed confident expression. No plastic skin, no over-retouching.

[SCALE CALIBRATION]
{product.dimensions} for any featured product at honest to-hand scale; the cube proportioned as real seating-height furniture relative to a real man.

[FRAMING & PROXIMITY]
The man and his bold cube command the frame — close editorial presence, graphic simplicity through nearness, not emptiness.

[COLOR & CONTRAST]
White thobe against a bold saturated geometric prop — the prop color drawn from or harmonized to {brand.color_field_palette} (the agent derives a brand-ownable bold tone; yellow as classic default only where brand-compatible), against a clean complementary backdrop. The brand/product color is the third accent note.

[LIGHT & LENS]
Clean editorial studio system: soft key upper-front, gentle fill, subtle rim separating the white thobe from the backdrop, even modern clarity. Lens and depth chosen for a sharp model against a clean field.

[NATURAL PLACEMENT]
Seated naturally on or beside the cube — weight honestly settled, thobe falling with true gravity folds.

[SCENE]
Modern menswear editorial. A SINGLE Saudi man in a crisp white thobe, seated on or beside the bold geometric cube against a clean complementary backdrop. Relaxed-confident, design-forward, graphic simplicity. Choice points: posture, cube color within brand-derived range, backdrop tone, crop.

[SUBJECT]
ONE Saudi man only — never a group. Crisp white thobe (CS-01), ghutra/shemagh styled contemporary or bare-headed modern per register. Warm honey-bronze skin, real texture, groomed contemporary appearance, confident composed expression. Modern confident Saudi masculinity — not costume, not stereotype.

[BRAND CONSTRAINTS]
SINGLE subject only — one man, never a group, no other people. Thobe and styling authentic modern Saudi (CS-01), not costume-orientalist. No readable text anywhere in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal modern menswear editorial photography, maximum fidelity. Clean high-contrast grade — white thobe, bold geometric color, brand accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills thobe and headwear specifics by region (Najdi/Hejazi cut, ghutra vs bare-headed) (CS-01). {saudi.color_palette_adjust} tunes the prop color.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: posture and seating, cube color within brand range, backdrop tone, crop and camera height, headwear per register. The graphic concept holds fresh.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The model's appearance, white thobe, geometric prop, backdrop, brand-readable elements — all preserved character-perfect.

[MOTION]
SINGLE primary motion only: ONE subtle natural action — a confident slow head turn toward camera, OR a relaxed shift of seated posture, OR a subtle thobe adjustment. The rest composed. NO complex choreography.
Secondary: thobe fabric shifts naturally with the single motion.

[WHAT STAYS STATIC]
Facial features, skin tone, white thobe, prop, backdrop — all locked. Capture character preserved. Camera steady.

[PACING & DURATION]
5 seconds. Continuous single take. Calm confident editorial pacing.

[OUTPUT]
Photoreal menswear editorial cinematography. Silent. No text overlay, no watermark.

---

## T35 · Modest Fashion Walking Shot

**Family:** TF09 · Portrait & Model | **Tier:** premium | **Sectors:** Fashion, Retail, Beauty | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required (garment/brand reference; model generated) | **Drama dial:** warm golden urban (outdoor-natural)
**Color story:** Flowing abaya catching motion against a modern Saudi urban backdrop. The fabric movement is the hero; warm urban tones support.
**Reference accounts:** @tiadress, @themodestbride, @planb_boutique | **Cultural Spec:** CS-01, CS-24, CS-13, CS-22

**WHEN TO USE:** Dynamic modest fashion motion for abaya/modest fashion brands, lifestyle retail. The flowing fabric communicates elegance and confidence; modern Saudi urban context grounds it.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} garment identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Stride moment, urban backdrop, and camera position are creative decisions; the garment reads brand-accurate in cut, fabric, and detail even in motion. INTEGRATION: the urban daylight that warms the architecture models her and the flowing fabric — one sun, one shadow direction, the abaya's motion-folds lit by the same light that grazes the pavement.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default broadcast_cinematic with fashion-film motion. Material truth: the abaya fabric flows with true physical weight, authentic motion-drape, honest fold dynamics mid-stride; {product.material_texture} for any featured product. Real Saudi skin and natural expression, real urban-light interaction. No CGI-fabric, no frozen-stiff motion.

[SCALE CALIBRATION]
True human scale within real architecture — walkway widths, plaza elements at honest built proportion to her figure.

[FRAMING & PROXIMITY]
She commands the frame mid-stride — near, dynamic, the urban setting in soft supporting depth, never a distant figure lost in plaza.

[COLOR & CONTRAST]
The flowing abaya's color — from {brand.color_field_palette} / the garment's true brand color — is the hero chromatic statement in motion; warm modern-urban Saudi tones (sandstone, glass, warm pavement) support; skin warm and true.

[LIGHT & LENS]
ONE light: natural urban daylight, golden-hour warmth preferred, directional enough to model the flowing fabric and cast dynamic soft shadows. Lens and depth chosen for a sharp model with crisp fabric motion against a soft urban backdrop.

[NATURAL PLACEMENT]
Her stride is a real walk — natural gait, weight transferring honestly, the fabric trailing by true physics.

[SCENE]
Dynamic modest-fashion composition. A SINGLE Saudi woman in a flowing abaya mid-stride, fabric caught in elegant motion behind and around her, modern Saudi urban environment — contemporary Riyadh architecture, Boulevard walkway, modern plaza — softly out of focus behind. Graceful, confident, alive. Choice points: stride moment, fabric-flow direction, urban depth, camera height and distance.

[SUBJECT]
ONE Saudi woman only — never a group. Modesty register {brand.modesty_register} (CS-24): mainstream = styled hijab + modest flowing abaya; modern = loose elegant scarf with front hair visible, fashion-forward flowing silhouette; editorial = high-fashion modest drama. Warm honey-bronze skin, confident graceful carriage, real texture. Modesty maintained throughout the motion.

[BRAND CONSTRAINTS]
SINGLE subject only — one woman, never a group, no other people in frame. Modesty maintained across the motion — flowing fabric never compromises coverage. Authentic modern Saudi urban setting (CS-13), not generic Western city. No readable signage or text in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal fashion-film photography, maximum fidelity. Dynamic warm urban grade — flowing garment hero, modern Saudi context. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the urban setting (Riyadh Boulevard, modern Jeddah, KAFD plaza). {saudi.apparel_context} fills abaya styling by region/register (CS-01, CS-24).

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: stride moment and fabric-flow, urban backdrop composition, hour of light, camera height and distance. The walk is never the same frame twice.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The model's appearance, modest styling, flowing abaya, urban setting — all preserved character-perfect. Modesty maintained across every frame.

[MOTION]
SINGLE coherent motion: she walks forward gracefully at a natural pace, the abaya flowing elegantly with her stride. ONE continuous believable action — walking — not layered competing motions. The fabric movement is the visual richness.
Secondary: hair tendrils (if modern register) or scarf edge move naturally with the walk; urban background carries gentle ambient life softly out of focus.

[WHAT STAYS STATIC]
Facial features, skin tone, garment identity, modest styling — all locked. Modesty compliance absolute including fabric motion. Urban context stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Graceful walking pace — natural, elegant, confident.

[OUTPUT]
Photoreal fashion-film cinematography. Silent. No text overlay, no watermark.

---

## T36 · Beauty Extreme Close-Up

**Family:** TF09 · Portrait & Model | **Tier:** premium | **Sectors:** Beauty, Cosmetics, Skincare | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required (product reference; model generated) | **Drama dial:** luminous beauty-soft
**Color story:** Luminous skin glow, dewy highlight, rich eye makeup tones. Warm intimate beauty palette. The makeup product's signature color is the chromatic hero on the skin.
**Reference accounts:** @danatreasures, @tiadress | **Cultural Spec:** CS-24, CS-22

**WHEN TO USE:** Intimate beauty hero — extreme close-up of eyes or partial face showing glowing makeup/skin result. The tight crop is itself a face-fidelity mitigation. SINGLE SUBJECT, tightly cropped.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} beauty product identity — its color payoff, finish, signature shade. Identity DNA: {product.identity_dna}
The exact crop (eyes/brow/cheekbone or lips/cheek) and gaze direction are creative decisions; the product's signature color/finish shows accurately on the skin. INTEGRATION: one soft beauty light creates the dewy glow, the catchlight, and the shade's true payoff together — the makeup lives on lit skin, not painted over it.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with luminous beauty grade, macro beauty standard. Material truth of skin and product: real pores, fine peach-fuzz catching light, natural texture, honest individual variation, true dewy highlight, real lash detail; the makeup sits on real skin. No CGI-smooth skin, no porcelain uniformity.

[SCALE CALIBRATION]
True macro facial scale — lashes, skin texture, and shade payoff at honest close-up proportion; the crop intimate but anatomically true.

[FRAMING & PROXIMITY]
Extreme intimate crop — eyes and partial face, or lips and cheek — filling the frame. (Deliberate face-fidelity mitigation: the tight crop avoids the hardest AI failure zone while delivering aspirational beauty.)

[COLOR & CONTRAST]
Luminous warm skin glow as the base; the makeup product's signature color (lip shade, eye tone) is the chromatic hero on the skin at true saturation — the brand's own shade from its real palette, never an invented tone.

[LIGHT & LENS]
ONE soft luminous beauty system: large soft key creating dewy glow, gentle fill preserving dimensional skin texture, catchlight in the eye. Macro sharpness on eyes/lips with soft falloff.

[NATURAL PLACEMENT]
The expression and gaze are a real human micro-moment — natural, composed, alive.

[SCENE]
Extreme beauty close-up. Tightly cropped Saudi woman's eyes and partial face (or lips and partial face) showing the glowing makeup result — luminous skin, defined eyes, rich shade payoff. Aspirational, intimate, luminous. Choice points: crop selection, gaze direction, highlight placement.

[SUBJECT]
ONE Saudi woman, extreme close-up. Modesty register respected even in tight crop ({brand.modesty_register}, CS-24): traditional/mainstream — eyes focus with hijab edge visible; modern/editorial — fuller face features. Warm honey-bronze skin with authentic texture, the makeup result luminous and true to the product's shade.

[BRAND CONSTRAINTS]
SINGLE subject, tightly cropped. No full group. Modesty per register even in close crop (CS-24). The beauty result reads aspirational-real, achievable, not fantasy-airbrushed. {brand.anti_attributes}

[OUTPUT]
Photoreal beauty macro photography, maximum fidelity. Luminous warm beauty grade, true shade payoff, glowing skin. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} governs crop framing relative to hijab (CS-24). {saudi.color_palette_adjust} tunes makeup tones toward Saudi-market-preferred shades.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: crop selection (eyes vs lips), gaze direction, highlight placement, depth falloff. The intimate moment renews; the shade stays true.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The cropped face/eyes/lips, skin texture, makeup result, lighting — all preserved character-perfect.

[MOTION]
SINGLE subtle motion: a slow natural blink, OR the faintest smile beginning at the lip corner, OR eyes shifting gently toward camera. ONE micro-expression only — extreme close-ups amplify motion; restraint is essential.
Secondary: the catchlight shifts microscopically; dewy highlight glimmers faintly.

[WHAT STAYS STATIC]
Facial features, skin tone, makeup result, crop framing — all locked. Modesty maintained. Capture character preserved. Camera absolutely steady (close-ups punish drift).

[PACING & DURATION]
4 seconds. Continuous single take. Very slow intimate pacing — one tiny human moment.

[OUTPUT]
Photoreal beauty macro cinematography. Silent. No text overlay, no watermark.

---

## T37 · Full Studio Portrait Solo

**Family:** TF09 · Portrait & Model | **Tier:** premium | **Sectors:** Retail, Beauty, Fashion, Corporate | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required (product/brand reference; model generated) | **Drama dial:** clean editorial, classical restraint
**Color story:** Classical portrait lighting on a neutral backdrop — controlled, timeless, dignified. Restrained neutral palette lets the subject and any brand/garment color carry the chromatic weight.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-24, CS-01, CS-22

**WHEN TO USE:** Classic dignified portrait for brand ambassadors, founder features, refined retail/beauty/corporate. The most classical, restrained, timeless of the portrait chains.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Pose, crop (full or three-quarter), and backdrop tone are creative decisions; any featured product/garment reads brand-accurate. INTEGRATION: one classical light system models subject and backdrop together — the key's dimensional shadow, the rim's separation, and the backdrop's gentle falloff are one portrait logic.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with classical-portrait grade. Material truth: {product.material_texture} for any featured product; clothing with true fabric weight. Real Saudi skin, authentic texture, honest individual character, natural dignified expression; classical lighting revealing real dimensional form. No plastic skin, no over-retouching.

[SCALE CALIBRATION]
{product.dimensions} for any featured product at honest to-hand/to-body scale; the figure framed at true human proportion within the portrait space.

[FRAMING & PROXIMITY]
Dignified full or three-quarter portrait presence — the subject near, commanding, composed; the neutral field a frame, not an emptiness.

[COLOR & CONTRAST]
Deliberately restrained neutral backdrop (warm grey, soft taupe, or deep neutral — warmed or tuned toward {brand.color_field_palette} compatibility) lets the subject's presence and any brand/garment color carry the chromatic weight. Refined, never loud.

[LIGHT & LENS]
ONE classical portrait system: soft key at 45° (Rembrandt or loop character), gentle fill preserving dimensional shadow, subtle hair/rim light. Timeless, controlled, flattering-real. Lens and depth chosen for a sharp subject against a softly neutral field.

[NATURAL PLACEMENT]
The pose is composed, dignified, honestly weighted — a real person standing or seated in self-possession.

[SCENE]
Classical studio portrait. A SINGLE Saudi subject (man or woman per brief) in a dignified full or three-quarter portrait against the neutral backdrop, classical lighting modeling face and form with timeless elegance. Restrained, classic, refined. Choice points: pose, crop, backdrop tone, key character (Rembrandt vs loop).

[SUBJECT]
ONE Saudi subject only — never a group. Modesty register {brand.modesty_register} fully respected (CS-24, CS-01). Warm honey-bronze skin, real texture, dignified composed expression, attire appropriate to register and brand. Classical portraiture dignity — respect and timelessness.

[BRAND CONSTRAINTS]
SINGLE subject only — never a group, never multiple figures, no other people. Modesty per register (CS-24). Dignified, respectful, authentic Saudi presentation — not costume, not stereotype. No readable text in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal classical portrait photography, maximum fidelity. Refined neutral grade, dignified subject presence. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills attire by register and region (CS-01, CS-24). {saudi.color_palette_adjust} can warm the neutral backdrop.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: pose and crop, backdrop tone, key character and shadow depth, attire details within register. Classical dignity, freshly composed.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The subject's appearance, attire, modest styling, neutral backdrop, classical lighting — all preserved character-perfect.

[MOTION]
SINGLE primary motion: one dignified natural action — a slow composed head turn toward camera, OR a subtle settling of posture, OR a gentle natural breath. Restrained. NO complex motion.
Secondary: clothing settles naturally; the faintest ambient presence.

[WHAT STAYS STATIC]
Facial features, skin tone, attire, modest styling, backdrop — all locked. Modesty maintained. Capture character preserved. Camera steady.

[PACING & DURATION]
5 seconds. Continuous single take. Slow dignified classical pacing.

[OUTPUT]
Photoreal classical portrait cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF10 · EDITORIAL POSTER — 3 chains · TEXT-CENTRAL
**Drama dial: clean even, designed** · **TEXT is a CORE block in this family, not conditional.**
**Arabic-fidelity dependency (failure ledger #13):** generative models re-paint the canvas; for Arabic-heavy copy the platform solution is the deterministic overlay node (Pillow + arabic-reshaper + python-bidi — not yet built). Until it ships: shortest Arabic copy only (single word renders most reliably, e.g. إتقان), or run these chains Latin-only / post-production type.

---

## T38 · Magazine Cover With Typography

**Family:** TF10 · Editorial Poster | **Tier:** premium | **Sectors:** Beauty, Retail, Fashion | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** clean even, premium-editorial
**Color story:** Bold magazine-cover palette — strong hero color, confident typographic contrast designed as one cover composition.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-22, CS-24 (if subject present)

**WHEN TO USE:** Magazine-cover editorial — product or single subject composed with magazine typography as an integral design element. TEXT IS CENTRAL. Premium launches, brand statements, editorial campaigns.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Cover layout choices — hero angle, type zones, masthead position — are creative decisions within magazine-cover logic. INTEGRATION: hero and typography are designed together as ONE cover; the light that models the hero defines the cover's overall grade, and the type zones live in deliberately composed space, not pasted over.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with high-editorial-magazine grade, premium cover-shoot standard. Material truth: {product.material_texture} for a product hero; real skin, single subject, modesty per register (CS-24) for a human hero. Authentic texture, honest light, real depth. No plastic perfection.

[SCALE CALIBRATION]
{product.dimensions} — the hero at honest scale, framed with cover intentionality; type zones proportioned as real magazine design (masthead, cover lines) relative to the hero.

[FRAMING & PROXIMITY]
The hero dominates the cover the way premium covers work — large, near, commanding, with designed negative space reserved for the type, never accidental dead space.

[COLOR & CONTRAST]
Bold magazine-cover palette: a strong hero color anchoring the composition, drawn from {brand.color_field_palette}, deliberately paired against the typographic color as one cover-design system. The brand owns every color on its cover.

[LIGHT & LENS]
ONE premium editorial cover light system — clean, confident, magazine-grade modeling appropriate to the hero (product or subject). Lens and depth serving cover clarity.

[NATURAL PLACEMENT]
The hero is composed with cover intentionality — a deliberate, gravity-honest stance or placement that anchors the layout.

[SCENE — TEXT CENTRAL]
Magazine cover composition. The hero (product or SINGLE Saudi subject) composed as a premium cover with deliberate space for editorial typography that is part of the design: masthead-style headline zone at top, supporting cover-line zones, hero in the dominant visual space. Bold, premium, designed-as-one. Choice points: masthead position, cover-line arrangement, hero crop.

[SUBJECT]
The hero product or ONE single Saudi subject (modesty register per CS-24 if human) — strong central presence, editorial styling, designed negative space for type.

[TEXT — CORE BLOCK for this family]
Render editorial magazine typography directly in the image as a central design element:
- Masthead/headline: "{brief.text_request.copy}" (or brand-appropriate cover headline) — bold editorial display type
- Style: {brief.text_request.style} — default high-fashion magazine masthead aesthetic
- Placement: integrated cover layout — headline prominent, hero dominant
- Latin and/or Arabic per {brief.text_request} — ARABIC RULE: shortest copy only (single word most reliable) until the deterministic overlay node ships; Arabic-heavy covers route to post-production typography for character accuracy
The typography is essential to this chain — designed WITH the image as a unified cover.

[BRAND CONSTRAINTS]
Single hero (one product or one subject). If human: single subject, modesty per register (CS-24). Typography reads as authentic premium editorial design — no garbled characters, no pseudo-text anywhere else in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal editorial magazine-cover composition with integrated typography, maximum fidelity. Premium designed grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} and {saudi.apparel_context} (if subject) per register. Arabic masthead typography for Saudi-market covers per the Arabic rule above.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: masthead position, cover-line arrangement, hero crop and angle, cover palette pairing within the brand range. Each generation is a new issue of the same magazine.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The hero, composition, typography content and placement (every character) — all preserved.

[MOTION]
Primary — hero: extremely subtle motion (product: slow drift/rotation; subject: one micro-expression).
Secondary — typography: the type may animate in subtly (gentle fade or settle) as a motion-poster effect, OR stay static while the hero breathes.
Tertiary — camera: imperceptible push-in.

[WHAT STAYS STATIC]
Hero identity and material texture locked. Typography content locked — no character changes. Composition stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Premium motion-poster pacing.

[OUTPUT]
Photoreal editorial motion-cover. Silent. No watermark.

---

## T39 · Billboard Mockup On Building

**Family:** TF10 · Editorial Poster | **Tier:** premium | **Sectors:** Retail, Corporate, F&B, Beauty | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** clean even, architectural-real
**Color story:** Brand campaign rendered large on a modern building's billboard against sky. Campaign color dominates; architecture and sky frame it. The brand made monumental.
**Reference accounts:** @planb_boutique, @danatreasures | **Cultural Spec:** CS-13

**WHEN TO USE:** Out-of-home campaign mockup — launch announcements, brand presence statements, campaign "in the world," investor/brand-deck visuals. TEXT/campaign visual central.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} campaign identity. Identity DNA: {product.identity_dna}
Street vs aerial perspective, building composition, and billboard proportion are creative decisions. The campaign visual on the billboard reads brand-accurate — logo, product, colors correct at billboard scale. INTEGRATION: the billboard belongs to the architecture — real mounting, real perspective, the same daylight grading building, billboard surface, and sky as one photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with architectural-realism grade — a real out-of-home photograph. Material truth: the billboard surface shows honest real-world mounting and subtle sheen, and the campaign's product hero renders with {product.material_texture} truth even at billboard magnification; authentic modern architecture, real daylight and sky, true perspective. No flat pasted-on billboard.

[SCALE CALIBRATION]
True out-of-home scale — the billboard at honest architectural proportion on the building, the campaign's product hero rendered at believable billboard magnification, legible from the street.

[FRAMING & PROXIMITY]
The billboard commands the frame from a believable street or aerial vantage — monumental and near enough to read, the building and sky framing rather than shrinking it.

[COLOR & CONTRAST]
The brand campaign color from {brand.color_field_palette} dominates the billboard at full saturation; modern architecture (glass, concrete) and sky frame it. The brand made large and bold against the urban sky.

[LIGHT & LENS]
ONE light: natural daylight with clear sky, the billboard well-lit and legible, real architectural perspective. Lens chosen for architectural lines and full-composition clarity.

[NATURAL PLACEMENT]
The billboard sits on the building as real OOH installations do — structurally mounted, perspective-true, weather-real.

[SCENE — TEXT CENTRAL]
Out-of-home composition. A large billboard displaying the brand campaign — hero product/visual plus campaign typography — mounted on a modern building, photographed from street or aerial perspective against the sky. Aspirational arrival: the brand made monumental and legitimate. Choice points: vantage, building character, billboard proportion, sky state.

[SUBJECT]
The brand campaign on the billboard — hero visual plus campaign text at billboard scale on believable modern architecture.

[TEXT — CORE BLOCK for this family]
Render the campaign typography on the billboard as central:
- Campaign headline: "{brief.text_request.copy}" — bold OOH display type, legible at scale
- Style: {brief.text_request.style} — default bold out-of-home campaign aesthetic
- The typography is part of the campaign visual on the billboard, essential not optional
- ARABIC RULE: shortest copy only until the deterministic overlay node ships; Arabic-heavy campaigns route to post-production for character fidelity at scale

[BRAND CONSTRAINTS]
The billboard campaign is the single brand element. Generic modern architecture — no identifiable real-brand buildings, no other real-brand advertising, no other readable text anywhere in the scene. {brand.anti_attributes}

[OUTPUT]
Photoreal out-of-home campaign photography with billboard typography, maximum fidelity. Aspirational grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — the building reads as modern Riyadh/Jeddah architecture (CS-13). Arabic campaign typography per the Arabic rule.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: vantage (street vs aerial), building character, billboard proportion, sky and hour. The campaign arrives in a different corner of the city each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The billboard campaign, building, sky, typography (every character) — all preserved.

[MOTION]
Primary — atmosphere: clouds drift slowly behind the building, daylight shifting subtly across the billboard; if digital, a gentle content glow-breath.
Secondary — camera: a slow cinematic push-in or rise toward the billboard, emphasizing scale.

[WHAT STAYS STATIC]
Campaign visual and typography locked. Building stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Slow aspirational reveal pacing.

[OUTPUT]
Photoreal out-of-home cinematography. Silent. No watermark.

---

## T40 · Brand Announcement Card

**Family:** TF10 · Editorial Poster | **Tier:** universal | **Sectors:** Beauty, Retail, F&B | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** clean even, announcement-crisp
**Color story:** Branded packaging beside a clean typography card on a split pastel background. Designed announcement palette — pastel base, brand color, clean type.
**Reference accounts:** @tiadress, @planb_boutique, @danatreasures | **Cultural Spec:** CS-22

**WHEN TO USE:** Social announcement card for product announcements, new arrivals, promotions. The most everyday/flexible editorial-poster chain. TEXT is central.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} brand identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The balance of packaging and card, the split's angle, and the card's design are creative decisions. The packaging reads brand-accurate, brand-readable face toward camera. INTEGRATION: one clean light holds packaging, card, and pastel field together — shared soft shadows, one surface, one designed photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with crisp announcement grade. Material truth: {product.material_texture} — the packaging substrate honest (film pliable, carton crisp, glass weighted); real card-stock texture, true soft shadows. No CGI-clean flatness.

[SCALE CALIBRATION]
{product.dimensions} — the packaging at true size beside a real announcement-card-sized insert; honest tabletop proportions between the two.

[FRAMING & PROXIMITY]
A tight, designed composition — packaging and card close and balanced, the pastel field active design space, not emptiness.

[COLOR & CONTRAST]
Designed announcement palette: split pastel base derived from {brand.color_field_palette}-harmonious pastels (the agent derives tones the brand can own — never borrowed reference colors), the brand color on the packaging, clean typographic contrast on the card.

[LIGHT & LENS]
ONE soft even commercial light, clean and bright with gentle soft shadow. Full-composition sharpness.

[NATURAL PLACEMENT]
Packaging and card sit with honest gravity on the surface — the packaging standing or lying as its substrate dictates, the card flat or gently propped.

[SCENE — TEXT CENTRAL]
Announcement card composition. The branded packaging beside a clean typography card (a designed announcement insert) on a split pastel background — product on one side, message card on the other, two-tone field unifying. Crisp, modern, designed-for-sharing. Choice points: split angle, card design language, packaging pose, pastel pairing within brand range.

[SUBJECT]
The branded packaging plus the typography card, composed as a designed announcement — packaging hero, card carrying the message, pastel field unifying.

[TEXT — CORE BLOCK for this family]
Render the announcement typography on the card directly:
- Message: "{brief.text_request.copy}" — clean modern announcement type (new arrival, launch, offer)
- Style: {brief.text_request.style} — default clean modern sans-serif announcement aesthetic
- Placement: on the typography card within the composition
- ARABIC RULE: shortest copy only (single word most reliable) until the deterministic overlay node ships; Arabic-heavy announcements route to post-production typography
The typography IS the announcement — essential to this chain.

[BRAND CONSTRAINTS]
Single branded packaging plus one typography card. Split pastel background. No human elements. No readable text anywhere except the card and the product's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal announcement-card composition with integrated typography, maximum fidelity. Clean pastel grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} tunes pastels toward Saudi-resonant tones. Arabic announcement typography per the Arabic rule. For occasions: pastel and message shift to occasion theme.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: split angle and pastel pairing, card design language, packaging pose and position, shadow softness. The announcement layout redesigns itself each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Packaging, {product.material_texture}, typography card, pastel background, message (every character) — all preserved.

[MOTION]
Primary — typography: the announcement text settles/fades in gently as a motion-card effect.
Secondary — packaging: a subtle highlight drift or micro-rotation.
Tertiary — camera: imperceptible push-in.

[WHAT STAYS STATIC]
Packaging identity and material texture locked. Typography content locked. Pastel background stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Clean announcement pacing.

[OUTPUT]
Photoreal announcement motion-card. Silent. No watermark.

---
---

# FAMILY TF11 · TEXTURE & MACRO — 3 chains
**Drama dial: product-color immersion** (the product's own true color IS the field — this family's own register)

---

## T41 · Foundation Cream Swatch Macro

**Family:** TF11 · Texture & Macro | **Tier:** premium | **Sectors:** Beauty, Cosmetics, Skincare | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** product-color immersion
**Color story:** The product's own color is the entire palette — a cream/foundation/balm swatch in extreme macro, true shade and finish filling the frame. Texture-as-hero.
**Reference accounts:** @danatreasures, @tiadress

**WHEN TO USE:** Texture-as-subject beauty macro — the formula's richness and true color sell it. No packaging needed; the substance itself is the brand expression.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} product's true shade, finish, and texture character. Identity DNA: {product.identity_dna}
Swatch form (swipe, dollop, ridge) and light direction are creative decisions; the swatch shows the product's true signature color and finish (matte, dewy, glossy, satin) accurately — this IS the brand expression, carried by the texture itself. INTEGRATION: one light, one formula, one surface — sheen, shadow, and pigment belong to a single photographed substance, never a composited swatch.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with extreme-macro beauty grade. Material truth at formula level: {product.material_texture} — glossy peaks where light catches, soft folds and ridges, authentic pigment density, honest surface tension, true finish behavior (matte absorbs, dewy reflects). No CGI-smooth swatch, no fake uniform surface.

[SCALE CALIBRATION]
{product.dimensions} translated to swatch scale — a real swipe or dollop at honest macro magnification; ridges and peaks at true formula-body proportion.

[FRAMING & PROXIMITY]
The texture fills the frame entirely — an immersive surface landscape; the closest the library gets to its subject.

[COLOR & CONTRAST]
The product's own true color IS the entire palette — filling the frame at honest saturation, its finish the defining character. Pure product-color immersion; no second color enters.

[LIGHT & LENS]
ONE soft directional macro light raking gently across the swatch to reveal texture, peaks, and finish behavior, controlled highlight on glossy areas. Macro sharpness on texture detail with soft falloff.

[NATURAL PLACEMENT]
The swatch lies as the formula truly behaves — a swipe with honest drag, a dollop with real surface tension and settle.

[SCENE]
Extreme texture macro. A swatch of the product fills the frame — a landscape of glossy peaks, soft folds, the formula's body and finish. Abstract, sensory, tactile. Choice points: swatch form, light direction, ridge topology.

[SUBJECT]
The product texture as sole subject — no packaging, no hands. True color, finish, tactile character in full physical truth.

[BRAND CONSTRAINTS]
The product texture only — no packaging, no hands, no props, no text. Shade and finish true to the real product. {brand.anti_attributes}

[OUTPUT]
Photoreal beauty macro photography, maximum fidelity. True-shade grade, tactile texture detail. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} — culturally neutral; shade range can reflect Saudi-market-preferred tones if relevant.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: swatch form (swipe/dollop/ridge), light direction, peak topology, magnification depth. A different texture landscape each time; the shade never drifts.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The swatch texture, color, finish, lighting — all preserved.

[MOTION]
Primary — light: the directional light slowly shifts angle, sheen and highlights gliding across the peaks and folds, revealing the finish dynamically.
Secondary — texture: if dewy/liquid, the faintest settling or glisten; if matte, stable.
Tertiary — camera: extremely subtle macro push-in deeper into the texture.

[WHAT STAYS STATIC]
Product color and finish locked. Swatch form stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Slow sensory macro pacing.

[OUTPUT]
Photoreal beauty macro cinematography. Silent. No text overlay, no watermark.

---

## T42 · Lipstick Smear With Roses

**Family:** TF11 · Texture & Macro | **Tier:** premium | **Sectors:** Beauty, Cosmetics | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** product-color immersion (romantic register)
**Color story:** Rich lipstick shade as the bold chromatic hero — bullet and creamy smear in true color, fresh roses echoing the tone. Romantic beauty palette.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride

**WHEN TO USE:** Romantic lipstick hero for lip-product launches, romantic beauty campaigns, gifting season. The smear shows true shade and creamy texture; roses add romance.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} lipstick identity — true shade, finish, and bullet form. Identity DNA: {product.identity_dna}
Smear gesture, rose arrangement, and crop are creative decisions; bullet and smear show the true signature shade and finish, the bullet's brand-readable details preserved. INTEGRATION: one soft light holds bullet, smear, and roses in a single romantic system — shared shadows, shared glow, one photographed moment.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with romantic beauty-editorial grade, macro standard. Material truth: {product.material_texture} — the smear with real creamy texture, honest drag marks, pigment density; the bullet's true material sheen; fresh roses with real petal velvet, natural color variation, subtle dew. No plastic roses, no fake-perfect smear.

[SCALE CALIBRATION]
{product.dimensions} — a real lipstick bullet (finger-length) beside its true-width smear and real-scale rose blooms; honest macro-to-close proportions among the three.

[FRAMING & PROXIMITY]
Intimate macro-to-close — bullet, smear, and roses near and sensual; the composition breathes through closeness.

[COLOR & CONTRAST]
The lipstick shade is the bold chromatic hero — bullet and smear in true rich color from the product's real palette; fresh roses echo the tone (reds/pinks) as romantic support. One color family, two voices.

[LIGHT & LENS]
ONE soft romantic directional light, warm and gentle, revealing creamy smear texture and making petals glow. Macro sharpness on bullet and smear; roses soft.

[NATURAL PLACEMENT]
The bullet lies as gravity placed it beside the swiped smear; petals and blooms rest with natural physics, never a rigid arrangement.

[COMPANION ELEMENTS]
The roses are this chain's ONE hero companion — fresh blooms echoing the shade. Nothing else enters.

[SCENE]
Romantic lipstick composition. A lipstick bullet beside a bold creamy smear of its shade swiped across a clean surface, fresh roses arranged nearby echoing the lip color, soft romantic light. Sensual, editorial, gift-worthy. Choice points: smear gesture and direction, rose placement and count, crop, surface tone.

[SUBJECT]
The bullet, its creamy smear, and fresh roses — shade payoff and texture in full physical truth.

[BRAND CONSTRAINTS]
The lipstick (bullet + smear) is the hero; roses romantic support only. No hands, no full faces, no text. Shade true to the real product. {brand.anti_attributes}

[OUTPUT]
Photoreal romantic beauty macro photography, maximum fidelity. Rich true-shade grade, romantic rose support. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for Saudi bridal/gifting, roses can be Taif Damask roses (ward taifi). {saudi.color_palette_adjust} respects true product shade.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: smear gesture, rose arrangement, crop and angle, surface tone. The romance restages; the shade holds true.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The bullet, smear, roses, lighting — all preserved.

[MOTION]
Primary — light: soft romantic light shifts gently, the smear's creamy sheen and the petals' glow shifting subtly.
Secondary — roses: petals shift microscopically in soft air; a dew drop may glisten.
Tertiary — camera: extremely subtle macro push-in toward the smear.

[WHAT STAYS STATIC]
Lipstick shade, bullet form, smear, rose arrangement — all locked. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Slow sensual romantic pacing.

[OUTPUT]
Photoreal romantic beauty macro cinematography. Silent. No text overlay, no watermark.

---

## T43 · Food Texture Extreme Macro

**Family:** TF11 · Texture & Macro | **Tier:** premium | **Sectors:** F&B, Restaurant, Dessert | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** product-color immersion (appetite-warm register)
**Color story:** The food's own rich appetite-colors fill the frame — golden crusts, glossy sauces, melting textures. Mouthwatering saturated palette. Texture-as-craving.
**Reference accounts:** @aseeb.najd, @diplomat_sweets, @laylali_riyadh | **Cultural Spec:** CS-21

**WHEN TO USE:** Mouthwatering food macro — the craving-trigger shot for F&B, restaurant, dessert launches. The texture itself creates appetite.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} food identity — true colors, textures, signature character. Identity DNA: {product.identity_dna}
The craving moment (drizzle, pull, break, crust) and light direction are creative decisions; the food shows its true appetizing character — real colors, authentic textures, signature details. INTEGRATION: one warm light and one dish — glisten, steam, and shadow belong to the same physical plate, never a composited texture.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with extreme food-macro grade. Material truth at food level: {product.material_texture} — glossy sauce with honest viscosity and light-catch, melting cheese with authentic stretch, flaky pastry with true crumb and golden layering, juicy detail with real moisture. Honest appetizing imperfection. No plastic food.

[SCALE CALIBRATION]
{product.dimensions} translated to macro food scale — crumb, drizzle, and crust at true close-up proportion; an honest bite-distance view.

[FRAMING & PROXIMITY]
The appetizing texture fills the frame — bite-close, immersive, the viewer's hunger distance.

[COLOR & CONTRAST]
The food's own rich appetite-colors fill the frame at full mouthwatering saturation — golden crusts, glossy sauce reds and browns, fresh ingredient hues. Pure craving-trigger immersion; nothing competes.

[LIGHT & LENS]
ONE warm directional food-macro light raking to reveal texture, glisten, and steam — appetite-warm with controlled glossy highlights. Macro sharpness on the craving detail, soft appetizing falloff.

[NATURAL PLACEMENT]
The food behaves with real physics — the drizzle flows, the pull stretches, the break crumbles as the real dish truly would.

[SCENE]
Extreme food texture macro. The food's most appetizing texture fills the frame — glossy drizzle, melting pull, flaky break, juicy interior, golden crust; steam may rise. Abstract, sensory, mouthwatering. Choice points: craving moment, light rake direction, steam presence, crop depth.

[SUBJECT]
The food texture as sole subject — no full plating, no hands. Craveable color, sheen, and moisture in full appetizing truth.

[BRAND CONSTRAINTS]
The food texture only — no full plating, no hands, no utensils, no text. Saudi market: no pork, no alcohol (CS-21). True to the real product. {brand.anti_attributes}

[OUTPUT]
Photoreal food macro photography, maximum fidelity. Mouthwatering warm grade, appetizing texture detail. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for Saudi cuisine, textures reflect authentic Saudi/Gulf dishes (CS-21). For Ramadan: warm iftar-context tones.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: craving moment (drizzle vs pull vs break), light rake, steam, crop depth. A new trigger of the same appetite each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The food texture, colors, sheen, steam, lighting — all preserved.

[MOTION]
Primary — appetite motion: steam rises gently; if sauce, a slow glossy drip moves; if cheese, the faintest settling pull; moisture glistens. The craving detail in slow motion.
Secondary — light: warm light shifts subtly, glossy highlights gliding across the texture.
Tertiary — camera: extremely subtle macro push-in.

[WHAT STAYS STATIC]
Food colors, texture, form — all locked (the food doesn't morph). Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Slow mouthwatering macro pacing.

[OUTPUT]
Photoreal food macro cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF12 · ACTIVE PRODUCT MOMENT — 3 chains
**Drama dial: full editorial punch, high-speed crisp**

---

## T44 · Dropper Drip Mid-Fall

**Family:** TF12 · Active Product Moment | **Tier:** premium | **Sectors:** Beauty, Skincare, Serum | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** high-speed crisp, fresh-precise
**Color story:** Crystal-clear or amber serum droplet catching light mid-fall against a clean gradient. The droplet is a tiny glowing lens; the serum color is the chromatic hero.
**Reference accounts:** @danatreasures, @tiadress

**WHEN TO USE:** Serum efficacy hero — a droplet suspended about to fall, showing the formula's clarity and richness. Precision, potency, freshness; the suspended droplet is the science-luxury moment.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity — dropper, bottle, the serum's true color/clarity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Bottle presence (below or beside), gradient tone, and crop are creative decisions; dropper and bottle read brand-accurate, the serum's true color and clarity preserved. INTEGRATION: one high-speed light system freezes droplet, dropper, and bottle together — the droplet's lens-glow, the glass reflections, and the gradient falloff are a single photographed instant.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed macro photography — frozen-instant strobe character, premium skincare grade. Material truth: {product.material_texture} — real glass reflectance on dropper and bottle; the suspended droplet with true surface tension forming a perfect-imperfect sphere, real internal refraction (a tiny lens), honest light-catch; serum with authentic viscosity. No CGI droplet, no fake fluid.

[SCALE CALIBRATION]
{product.dimensions} — true dropper-and-bottle scale; the droplet at honest millimeter size relative to the dropper tip. The tiny-real proportion is the precision story.

[FRAMING & PROXIMITY]
Macro-close on the suspended instant — dropper tip and droplet commanding the frame, bottle as near anchor; the viewer inside the moment of release.

[COLOR & CONTRAST]
The crystal-clear or true-color serum droplet glows as a tiny lens; the serum/product color is the chromatic hero against a clean gradient drawn from {brand.palette.background_tone} within {brand.color_field_palette}. Precise fresh palette — droplet, brand color, gradient. Nothing else.

[LIGHT & LENS]
ONE dramatic high-speed key from upper-side, hard enough to freeze and light the droplet as a glowing lens, with a cool rim for separation as its counterpart within the same system. Macro sharpness on droplet and dropper tip.

[NATURAL PLACEMENT]
Physics truth: the droplet hangs at the true instant before release — surface tension honest, the fall line plumb beneath the tip.

[SCENE]
Active serum drip composition. Dropper in the upper frame, a single droplet suspended mid-fall just below the tip — caught at the instant before falling. Bottle visible below or beside. Clean gradient background. Precise, fresh, scientific-luxurious. Choice points: bottle placement, gradient tone, crop, droplet stage.

[SUBJECT]
The dropper, the suspended droplet, the serum — surface tension, internal refraction, light-catch in full physical truth; serum clarity and color true.

[BRAND CONSTRAINTS]
Single product (dropper + bottle). No hands, no human elements, no text. The droplet is the hero action. Serum color true. {brand.anti_attributes}

[OUTPUT]
Photoreal high-speed skincare macro photography, maximum fidelity. Fresh precise grade, glowing droplet, true serum color. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — scientifically neutral; for heritage/oud-based serums, amber tones and warm rim apply. {saudi.color_palette_adjust} respects true product color.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: droplet stage (forming/hanging/just-released), bottle placement, gradient tone within brand range, crop. The precise instant is caught differently each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Dropper, bottle, suspended droplet, serum color, {product.material_texture}, background — all locked. Every label character preserved.

[MOTION]
Primary — the droplet: completes its fall in extreme slow motion, descending and impacting a surface (or the serum pool) below, a delicate crown ripple forming; a new droplet begins forming at the tip.
Secondary — light: the droplet's glowing lens-catch shifts as it falls.

[WHAT STAYS STATIC]
Product identity locked — dropper, bottle, labels, serum color, material texture. Background stable. Capture character: high-speed macro preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Hyper-slow-motion droplet pacing.

[OUTPUT]
Photoreal high-speed skincare cinematography. Silent. No text overlay, no watermark.

---

## T45 · Perfume Spray Application

**Family:** TF12 · Active Product Moment | **Tier:** luxury | **Sectors:** Fragrance, Perfume, Oud | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** high-speed ethereal, luminous-dark
**Color story:** Fine perfume mist catching light against dark or warm gradient — the mist glows like illuminated vapor. Product brand color anchors below the luminous spray.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-19

**WHEN TO USE:** Fragrance spray hero — a bottle mid-spray, fine mist glowing in light. The sensory moment of application; scent made visible.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} fragrance bottle identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Spray-cone direction, backdrop warmth, and crop are creative decisions; the bottle reads brand-accurate, brand-readable face toward camera, nozzle actively spraying. INTEGRATION: one light system holds bottle and mist together — the backlight that ignites the mist also rims the glass; spray and anchor are one photographed event.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed macro with luxury-fragrance grade, frozen-instant strobe character. Material truth: {product.material_texture} — true glass and cap reflectance; the mist with real atomized droplet dispersion — varied particle sizes, authentic spray-cone physics, honest light-scatter glow. No CGI mist, no flat digital fog.

[SCALE CALIBRATION]
{product.dimensions} — true bottle size; the spray cone at honest atomizer scale, the fine particles real-mist small. The delicacy of true scale is the luxury.

[FRAMING & PROXIMITY]
Close on bottle and erupting mist — the luminous cone and its anchor filling the frame, the dark gradient pressing near.

[COLOR & CONTRAST]
The luminous glowing mist (cool-white or warm-gold per register, tuned to {brand.color_field_palette}) is the ethereal hero; the product's brand color anchors the bottle below the spray. Two chromatic players against the dark/warm gradient.

[LIGHT & LENS]
ONE light logic: a dramatic key with strong backlight making the fine mist glow as it scatters — the backlight is the system's defining act. Dark or warm gradient backdrop for mist contrast. Sharpness on bottle and near-mist.

[NATURAL PLACEMENT]
Physics truth: the cone erupts from the nozzle with real atomizer geometry, particles dispersing and decelerating honestly.

[SCENE]
Fragrance spray composition. The bottle captured mid-spray, a fine luminous mist erupting in an elegant cone, frozen as it catches the light, glowing against the gradient. Bottle anchor; illuminated spray the ethereal action. Sensory, luxurious, scent-made-visible. Choice points: cone direction, backdrop warmth, mist density, crop.

[SUBJECT]
The bottle and its glowing mist — atomized dispersion and light-scatter in full physical truth; glass and brand details true.

[BRAND CONSTRAINTS]
Single fragrance bottle. No hands, no human elements, no text. The mist is the hero action. {brand.anti_attributes}

[OUTPUT]
Photoreal high-speed fragrance macro photography, maximum fidelity. Luminous ethereal grade, glowing mist, brand-color anchor. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for oud/heritage fragrance, the mist carries warm-gold tone evoking bukhoor luxury (CS-19); warm backdrop. {saudi.color_palette_adjust} sets mist temperature.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: cone direction and density, backdrop warmth, crop, mist-glow temperature within register. The ethereal instant re-forms every time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Bottle, every label character, {product.material_texture}, the mist cone, lighting — all locked.

[MOTION]
Primary — the mist: continues dispersing in slow motion, the cone expanding, fine particles drifting outward and settling, glowing in the light; a fresh subtle spray pulse may emerge.
Secondary — atmosphere: the dispersed mist drifts gently in ambient air.

[WHAT STAYS STATIC]
Bottle identity locked — labels, glass, cap, color, material texture. Background stable. Capture character: high-speed macro preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Hyper-slow ethereal spray pacing.

[OUTPUT]
Photoreal high-speed fragrance cinematography. Silent. No text overlay, no watermark.

---

## T46 · Beverage Pour Stream

**Family:** TF12 · Active Product Moment | **Tier:** premium | **Sectors:** F&B (beverages), Coffee, Cold drinks | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** high-speed crisp, appetite-saturated
**Color story:** Rich beverage stream pouring in a glossy ribbon from height — coffee browns, juice golds, or true drink color — into a glass catching the crown splash.
**Reference accounts:** @barnscoffee, @cafe.najd, @coffeebeantealeaf.sa | **Cultural Spec:** CS-18, CS-21

**WHEN TO USE:** Beverage pour hero — the classic dynamic pour for coffee, juice, cold drinks. Freshness and abundance; the pour is the appetite trigger.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} beverage identity — its true color, the source vessel/packaging. Identity DNA, preserved across any camera angle: {product.identity_dna}
Pour height, splash stage, and gradient tone are creative decisions; the source vessel reads brand-accurate, brand-readable face toward camera, the beverage's true color preserved. INTEGRATION: one liquid-light system holds vessel, stream, and glass together — the glow in the falling ribbon, the splash highlights, and the vessel's reflections share the same frozen instant.

[REALISM & CAPTURE CHARACTER]
Capture character: high-speed liquid photography — frozen-instant strobe character, premium beverage grade. Material truth: {product.material_texture} — true vessel substrate (glass, can, carton, brass dallah); the stream with real flow physics, surface texture and twist; the glass catching impact with a chaotic real crown splash, rising bubbles, honest refraction. No CGI liquid, no fake splash symmetry.

[SCALE CALIBRATION]
{product.dimensions} — true vessel and glass sizes; the pour height and stream width at honest real-pour proportion between them.

[FRAMING & PROXIMITY]
Tight on the action — stream, splash crown, and vessels filling the frame at appetite distance; the dynamic event near and immediate.

[COLOR & CONTRAST]
The beverage's true color at full appetizing saturation — coffee brown, juice gold, or the drink's real hue — glossy and rich in stream and glass, against a clean or warm gradient from {brand.palette.background_tone} within {brand.color_field_palette}.

[LIGHT & LENS]
ONE light logic: a dramatic key freezing the stream with a backlight making the liquid glow with transparency and color — key and backlight one designed liquid-light system. Sharpness on stream and glass.

[NATURAL PLACEMENT]
Physics truth: the stream falls plumb with honest gravity twist; the crown splash erupts with real chaotic asymmetry; the glass fills as liquid truly fills.

[COMPANION ELEMENTS]
The receiving glass is the chain's structural companion — one glass, nothing more.

[SCENE]
Beverage pour composition. The drink pours from a source (bottle, can, pitcher, or dallah) at height in a steady glossy stream into the glass below, a crown splash rising at impact, frozen at peak drama against the clean/warm gradient. Dynamic, fresh, abundant. Choice points: pour height, splash stage, gradient tone, vessel angle.

[SUBJECT]
The stream, the receiving glass, the source vessel — flow, refraction, true color, crown splash in full physical truth. The beverage is the hero.

[BRAND CONSTRAINTS]
Single beverage hero (source + glass). No hands holding vessels unless culturally required — a dallah pour may imply a hand: keep to wrist only if so (CS-18). No alcohol. No text beyond the product's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal high-speed beverage photography, maximum fidelity. Saturated appetizing grade, glossy pour, true drink color. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — for Saudi coffee, the pour can be from a brass dallah into a finjan, respecting serving ritual (CS-18, CS-21). {saudi.color_palette_adjust} respects true beverage color.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: pour height, splash stage, vessel angle, gradient tone within brand range. The pour catches a different peak instant each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Source vessel, glass, beverage color, {product.material_texture}, the stream, the crown splash — all locked.

[MOTION]
Primary — the pour: continues in a steady stream, the glass filling ~15% over the duration, the crown splash evolving with new droplets. Real-time pour physics.
Secondary — bubbles/surface: rising bubbles and surface motion in the glass.

[WHAT STAYS STATIC]
Source vessel identity locked — labels, color, material texture. Glass position locked. Beverage true color. Background stable. Capture character: high-speed preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Real-time pour pacing — natural liquid physics.

[OUTPUT]
Photoreal high-speed beverage cinematography. Silent. No text overlay, no watermark.

---
---

# BATCH 2 · AGENT RUNTIME NOTES

**Block inclusion:** [NATURAL PLACEMENT] on all chains (physics-truth variant on TF12 action chains; pose-truth variant on TF09 human chains). [COMPANION ELEMENTS] active on T42 (roses, one hero) and T46 (receiving glass, structural); declared absent/self-contained elsewhere. [TEXT] is a CORE block on all TF10 chains (replacing the conditional TEXT OVERLAY); conditional everywhere else. [SAUDI ADAPTATION] conditional on every chain.

**TF09 identity-tier rules (non-negotiable):** SINGLE SUBJECT, never a group; modesty register {brand.modesty_register} per CS-24/CS-01 never violated in any frame including motion; real skin texture; video = ONE primary motion only; camera steady on human chains; T36 tight crop is a deliberate face-fidelity mitigation.

**TF10 Arabic dependency (ledger #13):** the deterministic Pillow overlay node is the platform solution and is NOT yet built — until then these three chains run shortest-Arabic-copy or Latin-only/post-production. Flag in every TF10 brief.

**Drama dial:** TF08 full editorial punch (T29 warm chiaroscuro, T30/T31 epic-landscape variants) · TF09 clean editorial (T35 warm golden urban, T36 luminous-soft) · TF10 clean even designed · TF11 product-color immersion · TF12 high-speed crisp (T45 ethereal luminous-dark).

**Single-light rule notes:** T28's neon multi-source reads as one coherent night-street system (the scene IS the lights); T44/T45/T46 key+rim/backlight pairs are declared single designed high-speed systems. All others: one source.

**Failure-ledger compliance:** all 19 chains carry the 15-block order, the four v3.7 fields, brand-derived color, proportion anchoring, framing-proximity, integration, companion restraint, no-readable-background-text (explicit on T28, T29, T31, T32, T33–T37, T39, T40), conditional/core text logic, and the CREATIVE VARIANCE DIRECTIVE. No fixed mm / f-stop / Kelvin commands anywhere.

*OpenClaw · Master Prompt Library v3.7 · Batch 2 · TF08 + TF09 + TF10 + TF11 + TF12 · 19 chains · Confidential*

<!-- ══════════ OpenClaw_v3_7_Batch3_TF13_TF14_TF15_TF16_TF17.md ══════════ -->

# FAMILY TF13 · LIFESTYLE CONTEXT — 7 chains
**Drama dial: soft natural / authentic** (U04 phone-documentary · U05 clean designed · F02/T47/T49 warm natural · T48 clean abundant · T50 warm candlelit chiaroscuro)

---

## U04 · Behind the Scenes

**Family:** TF13 · Lifestyle Context | **Tier:** universal | **Sectors:** F&B, Retail, Beauty, Hospitality, Services | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Recommended | **Drama dial:** authentic phone-documentary
**Color story:** Authentic phone-camera warmth — real workspace tones, honest natural light, slightly imperfect. Deliberately un-polished for trust.
**Reference accounts:** @aseeb.najd, @barnscoffee, @cafe.najd | **Cultural Spec:** CS-08, CS-13, CS-01 (if human)

**WHEN TO USE:** Authenticity/process content — the human craft behind the brand. Trust-building, founder story, process transparency. If a person appears: single-subject, hands/partial-body preferred.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The candid framing, process moment, and workspace angle are creative decisions; the product reads brand-accurate even in candid framing. INTEGRATION: the workspace's real available light is the only light — product, hands, tools, and clutter all live in the same honest uneven illumination; nothing reads studio-lit.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural — authentic, deliberately un-polished, documentary-candid as if on a real phone during actual work. Material truth: {product.material_texture} — the product mid-process behaves as its real substrate. Natural slightly-uneven phone light, honest workspace clutter, real material textures, true-to-life color. This chain's TRUST comes from looking real, not produced. No glossy over-production, no staged-perfect set.

[SCALE CALIBRATION]
{product.dimensions} — true working scale among real tools, vessels, and hands; everything at honest workbench proportion.

[FRAMING & PROXIMITY]
Candid-close on the process — the working hands and the product taking shape fill the frame; the viewer stands at the maker's shoulder, not across the room.

[COLOR & CONTRAST]
Deliberately authentic, not hyper-saturated — real workspace tones with the product/process color from the brand's true palette sitting naturally and truthfully. Trust through honesty, not polish.

[LIGHT & LENS]
ONE truth: the workspace's natural available light — slightly uneven, honest, phone-camera quality with real shadows and authentic ambiance. Natural phone perspective, moderate depth.

[NATURAL PLACEMENT]
Everything sits where work put it — tools mid-use, ingredients where the hand left them, the product honestly in-progress.

[COMPANION ELEMENTS]
The working process IS the world — tools and materials genuinely in use, never staged props. No decorative additions.

[SCENE]
Behind-the-scenes composition. The product mid-creation in a real working environment — kitchen, workshop, roastery, atelier, prep area — authentic process visible: materials in use, the product taking shape, honest workspace. If a person is present: hands or partial body only, working. Candid, real, trust-building. Choice points: process moment, camera angle, workspace depth.

[SUBJECT]
The product-in-process within a real working context. If human presence: SINGLE person, hands/forearms/partial-body only, right-hand work preferred (CS-08), modest sleeve (CS-01). The authentic process is the subject.

[BRAND CONSTRAINTS]
Product authentic within process. If human: single person, partial-body, modesty maintained (CS-01, CS-08). Real Saudi working environment (CS-13). No glossy over-production. No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic-documentary photography (phone-camera aesthetic), maximum fidelity. Honest natural grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the authentic Saudi working environment (CS-13). {saudi.apparel_context} if hands/partial-body present (CS-01, CS-08).

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: process moment, camera angle and candid framing, workspace character, hand action. A different honest minute of the same real work.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, process scene, working context, any partial-body element — all preserved. Brand-readable elements locked.

[MOTION]
SINGLE coherent process motion: one authentic working action unfolds — a hand stirring, pouring, assembling, finishing the product. ONE believable candid motion, phone-documentary style.
Secondary: ambient workspace life — steam, a tool, natural movement softly in the scene.

[WHAT STAYS STATIC]
Product identity and material texture locked. If human: single-subject and modesty maintained. Working environment stable. Capture character: phone_natural preserved — the authentic look is essential.

[PACING & DURATION]
5 seconds. Continuous single take. Natural candid documentary pacing.

[OUTPUT]
Photoreal authentic-documentary cinematography. Silent. No text overlay, no watermark.

---

## U05 · Social Proof — TEXT-CENTRAL

**Family:** TF13 · Lifestyle Context | **Tier:** universal | **Sectors:** F&B, Retail, Beauty, Services, Hospitality | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Recommended | **Drama dial:** clean even, designed
**Color story:** Clean designed layout — product hero with review/rating/press visuals as designed graphic elements. Brand palette plus clean typographic credibility cues.
**Reference accounts:** @aseeb.najd, @barnscoffee, @danatreasures | **Cultural Spec:** CS-22

**WHEN TO USE:** Credibility content — reviews, ratings, rankings, press features beside the product. TEXT is central. Conversion-stage, harvest-intent.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The proof layout — element arrangement, badge style, quote placement — is a creative decision; the product reads brand-accurate, brand-readable face toward camera. INTEGRATION: one clean light holds product and designed proof elements on one surface and grade — a single designed photograph, not collaged layers.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with designed-graphic clarity. Material truth: {product.material_texture} — authentic product substrate, honest light, real soft shadow. The graphic proof elements clean and designed. No CGI flatness.

[SCALE CALIBRATION]
{product.dimensions} — the product at true size; proof graphics proportioned as designed accents around it, never overwhelming the hero.

[FRAMING & PROXIMITY]
A tight, designed layout — product prominent and near, proof elements arranged close as trustworthy accents; no scattered empty canvas.

[COLOR & CONTRAST]
Brand palette from {brand.color_field_palette} anchors the field; clean credibility cues (star-rating gold, badge accent) provide designed contrast. Trustworthy, polished.

[LIGHT & LENS]
ONE clean even commercial light, bright and trustworthy with gentle soft shadow. Full-composition sharpness.

[NATURAL PLACEMENT]
The product stands or lies with honest gravity within the designed layout.

[SCENE — TEXT CENTRAL]
Social proof composition. Product hero composed with designed credibility graphics — star ratings, a short customer quote, a ranking badge, or a press cue — arranged on a clean brand-aligned background. Polished, credible, social-native. Choice points: proof element selection and arrangement, background tone within brand range, product pose.

[SUBJECT]
The product hero plus designed social-proof elements (ratings, quote, badge) as one trustworthy layout.

[TEXT — CORE BLOCK for this family]
Render the social-proof typography directly as designed elements:
- Proof content: "{brief.text_request.copy}" — star rating, short customer quote, ranking, press cue
- Style: {brief.text_request.style} — default clean trustworthy modern type with rating graphics
- Placement: designed credibility accents around the product
- ARABIC RULE: shortest copy only until the deterministic overlay node ships; Arabic-heavy proof routes to post-production typography
The proof text IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Single product hero with designed proof graphics. No fabricated claims beyond what the brief provides. No real third-party logos unless authorized. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal social-proof composition with integrated typography, maximum fidelity. Clean trustworthy grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns to brand. Arabic proof typography per the Arabic rule.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: proof element selection, layout arrangement, background tone, product pose. The credibility story redesigns each time; the claims never change.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, proof elements, layout, typography (every character) — all preserved.

[MOTION]
Primary — proof elements: rating stars or cues settle/animate in gently as a motion-graphic effect.
Secondary — product: subtle highlight drift or micro-rotation.
Tertiary — camera: imperceptible push-in.

[WHAT STAYS STATIC]
Product identity locked. Proof content locked — no number or text changes. Layout stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Clean credible motion-graphic pacing.

[OUTPUT]
Photoreal social-proof motion-graphic. Silent. No watermark.

---

## F02 · Beverage Showcase

**Family:** TF13 · Lifestyle Context | **Tier:** premium | **Sectors:** F&B (beverages), Coffee, Cafe | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** warm natural (café register)
**Color story:** Appetizing beverage hero in warm café context — rich drink color, warm wood/marble surface, soft ambient glow. Fresh, social, crave-worthy.
**Reference accounts:** @barnscoffee, @cafe.najd, @coffeebeantealeaf.sa | **Cultural Spec:** CS-13, CS-21

**WHEN TO USE:** Café-style beverage hero — the drink styled and ready in its natural café home. Coffee shops, beverage brands, café menus.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} beverage identity — drink color, cup/glass, branding. Identity DNA, preserved across any camera angle: {product.identity_dna}
Surface choice, café depth, and styling moment are creative decisions; the beverage and vessel read brand-accurate, true drink color preserved. INTEGRATION: the café's warm ambient light is the one system — it glows in the drink, warms the wood or marble, and softens into the bokeh behind; steam or condensation catches that same light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default phone_natural with warm café lift. Material truth: {product.material_texture} — real drink texture (crema, foam, condensation, ice), honest café surface (wood grain, marble), true vessel reflectance. No plastic-perfect drink, no sterile set.

[SCALE CALIBRATION]
{product.dimensions} — true cup/glass size on a real café surface; foam, ice, and condensation at honest beverage scale.

[FRAMING & PROXIMITY]
At the table with the drink — close, crave-distance, the café ambiance breathing warm behind.

[COLOR & CONTRAST]
The beverage's rich true color at appetizing saturation is the hero; warm café tones (wood, marble, ambient glow) support; soft café bokeh behind. Inviting, crave-worthy.

[LIGHT & LENS]
ONE warm café light system — soft directional with inviting ambient glow, a backlight quality catching steam or condensation within the same system. Drink sharp, café context warm bokeh.

[NATURAL PLACEMENT]
The drink sits where the barista set it — honest contact, true settle of foam or ice, the vessel turned as a hand would leave it.

[COMPANION ELEMENTS]
ONE hero companion maximum from {product.companion_elements} (a small plate, a date, a spoon — or none); the café scene itself carries the context.

[SCENE]
Café beverage showcase. The drink presented appetizingly on a café surface in a warm café context — soft-focus ambiance behind (warm lighting, interior hint, plant or window glow). Styled ready-to-enjoy: perfect foam, glistening condensation, fresh ice. The drink in its natural home. Choice points: surface, café depth, styling moment, companion or none.

[SUBJECT]
The beverage hero in café context — drink texture, vessel, and surface in appetizing physical truth; ambiance softly secondary.

[BRAND CONSTRAINTS]
Single beverage hero. Café context softly secondary. No human elements (hands only if essential). No alcohol. Authentic modern Saudi café (CS-13). No readable text on background items — menus and signage out of focus or text-free. {brand.anti_attributes}

[OUTPUT]
Photoreal café beverage photography, maximum fidelity. Warm inviting grade, appetizing true drink color. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the café register — modern Saudi specialty café (Boulevard, Diriyah). For Saudi coffee: finjan/dallah context (CS-18, CS-21). {saudi.color_palette_adjust} tunes warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: surface and café depth, styling moment (fresh pour vs settled), camera height, companion presence. A different inviting cup each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Beverage, vessel, {product.material_texture}, café surface and context, drink color — all preserved. Brand elements locked.

[MOTION]
Primary — beverage: appetite motion — steam rises from a hot drink, OR condensation beads trickle on a cold one, OR foam settles gently. The drink's living freshness.
Secondary — café ambiance: soft bokeh shimmer, gentle ambient life.
Tertiary — camera: extremely subtle push-in toward the drink.

[WHAT STAYS STATIC]
Beverage identity locked — vessel, branding, true drink color, material texture. Café surface and context stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Warm inviting café pacing.

[OUTPUT]
Photoreal café beverage cinematography. Silent. No text overlay, no watermark.

---

## T47 · Laptop With Coffee Morning

**Family:** TF13 · Lifestyle Context | **Tier:** universal | **Sectors:** F&B, Tech, Services, Coffee | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** soft natural (warm morning)
**Color story:** Warm morning sunlight across a modern desk — laptop, branded coffee cup, soft productivity warmth. Aspirational everyday.
**Reference accounts:** @barnscoffee, @cafe.najd | **Cultural Spec:** CS-13

**WHEN TO USE:** Morning productivity lifestyle — the modern Saudi professional morning. Coffee brands, tech, services, co-working.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity (the branded cup/product). Identity DNA, preserved across any camera angle: {product.identity_dna}
Desk arrangement, camera angle, and window-light direction are creative decisions; the branded product reads brand-accurate, naturally placed. INTEGRATION: the morning window sun is the one light over desk, laptop, and cup — the warm beam grazes them all, the cup's steam catches it, every shadow runs from the same window.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with warm editorial lift — a high-end phone in a real morning workspace. Material truth: {product.material_texture} — the branded cup with true reflectance, perhaps a steam wisp. Real desk character, honest morning light, authentic laptop and material textures. No staged-perfect desk.

[SCALE CALIBRATION]
{product.dimensions} — the cup at true hand size beside a real laptop; desk objects at honest workspace proportion. The laptop anchors the cup's scale.

[FRAMING & PROXIMITY]
At the desk, in the seat — the cup near and focal, laptop and context soft around it; the viewer's own morning, not an observed office.

[COLOR & CONTRAST]
Warm morning palette — neutral desk tones bathed in golden light; the branded cup's color from {brand.color_field_palette} is the focal warm accent. Aspirational everyday-premium.

[LIGHT & LENS]
ONE light: warm morning sun from a side window — soft directional, long gentle shadows, the beam faintly visible. Cup sharp, desk context soft.

[NATURAL PLACEMENT]
The cup sits where a hand set it down between sips — honest contact, naturally turned; the laptop open mid-work.

[COMPANION ELEMENTS]
The laptop is the structural scene-partner; beyond it, ONE subtle companion maximum (a notebook OR a plant) from the desk's honest world.

[SCENE]
Morning productivity composition. A modern laptop open on a clean desk, the branded cup beside it as focal product, warm sun streaming from a side window, subtle context softly behind (modern home-office). The aspirational productive-morning moment. Choice points: camera angle, beam direction, cup position, companion choice.

[SUBJECT]
The branded cup as hero; laptop and desk the productive-morning context — materials and light in authentic truth.

[BRAND CONSTRAINTS]
Branded product (cup) is hero. Laptop and desk softly secondary. No human elements. No identifiable real-brand laptop logos (generic modern laptop) — laptop screen carries no readable text. Real modern Saudi workspace (CS-13). {brand.anti_attributes}

[OUTPUT]
Photoreal lifestyle photography, maximum fidelity. Warm morning grade — golden productivity warmth, branded-cup focal accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the workspace register — modern Saudi home-office or co-working (CS-13). For Ramadan: evening/night productivity warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: desk arrangement, beam angle, camera height, cup position and turn, companion. A different real morning at the same desk.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Branded cup, {product.material_texture}, laptop, desk, morning light — all preserved. Brand elements locked.

[MOTION]
Primary — atmosphere: steam rises gently from the cup; the warm beam glides subtly across the desk.
Secondary — ambient: soft dust-mote drift in the light; faint background life.
Tertiary — camera: extremely subtle push-in toward the cup.

[WHAT STAYS STATIC]
Branded cup identity and material texture locked. Laptop, desk fixed. Morning warmth constant. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Calm productive-morning pacing.

[OUTPUT]
Photoreal lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T48 · Food Spread Tablet Planning

**Family:** TF13 · Lifestyle Context | **Tier:** premium | **Sectors:** F&B, Restaurant, Catering, Services | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** clean abundant (palette discipline — busy scene)
**Color story:** Abundant food spread on marble with a tablet showing the menu — rich food colors against cool marble, modern tech accent.
**Reference accounts:** @aseeb.najd, @diplomat_sweets, @laylali_riyadh | **Cultural Spec:** CS-13, CS-21

**WHEN TO USE:** Modern dining/planning lifestyle — abundance plus modern convenience. Restaurants, catering, food services, hospitality tech.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity (menu brand, food, or service). Identity DNA: {product.identity_dna}
Spread arrangement, shot angle (top-down or three-quarter), and tablet placement are creative decisions; the brand (on tablet menu, packaging, or presentation) reads accurate. INTEGRATION: one soft daylight holds the entire spread, the marble, and the tablet — the screen's true glow lives inside that light, every dish shares its shadow direction.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with appetizing-lifestyle lift. Material truth: {product.material_texture} where the brand's product appears; real food textures with honest appetizing detail, authentic marble veining, true tablet screen glow. No CGI food, no fake-perfect arrangement.

[SCALE CALIBRATION]
{product.dimensions} where applicable — dishes, tablet, and ingredients at true tabletop scale to each other; the spread's abundance built from honestly sized elements.

[FRAMING & PROXIMITY]
Elevated top-down or three-quarter, close over the spread — abundance filling the frame edge to edge, the viewer at the table's edge.

[COLOR & CONTRAST]
Palette discipline for a busy scene: rich warm appetizing food colors against cool marble as the controlled contrast; the tablet screen and brand provide the modern accent. The brand's color reads clearly within the abundance.

[LIGHT & LENS]
ONE soft even daylight with gentle directional quality revealing food texture and marble sheen; the tablet's subtle true glow within it. Full spread sharp.

[NATURAL PLACEMENT]
Dishes and tablet sit as a real table is set — honest weights, true contacts, the tablet resting at a believable reading angle.

[COMPANION ELEMENTS]
STRUCTURAL EXCEPTION: the composed abundant spread IS this chain's scene — restraint applies as no scatter beyond the deliberate arrangement; every element belongs to the meal.

[SCENE]
Food spread planning composition. An abundant arranged spread on marble — multiple dishes, fresh ingredients, appetizing variety — with a tablet resting among it showing the menu/brand. Modern, aspirational, the contemporary hospitality-planning moment. Choice points: arrangement geometry, shot angle, tablet position, dish variety per brief.

[SUBJECT]
The abundant spread plus the tablet showing menu/brand — food in appetizing physical truth, marble and tablet authentic, brand visible on screen or packaging.

[BRAND CONSTRAINTS]
Food spread plus one tablet. No human elements (hands only if essential). No pork, no alcohol (CS-21). Modern Saudi dining context (CS-13). No identifiable real-brand tablet logos; the only readable text is the brand's own menu on the screen. {brand.anti_attributes}

[OUTPUT]
Photoreal food-lifestyle photography, maximum fidelity. Appetizing abundant grade, marble-and-tech contrast. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — Saudi/Gulf dishes for Saudi cuisine spreads (CS-21). For Ramadan: iftar spread context, evening warmth. For gatherings: traditional communal arrangement.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: arrangement geometry, shot angle, dish selection per brief, tablet position. The abundance recomposes each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Spread, tablet, marble, brand elements, {product.material_texture} — all preserved.

[MOTION]
Primary — atmosphere: steam rises from hot dishes; the tablet screen carries a gentle glow-breath; fresh details glisten.
Secondary — light: soft daylight shifts subtly across the spread.
Tertiary — camera: extremely subtle top-down or three-quarter push-in.

[WHAT STAYS STATIC]
Food arrangement and colors locked. Tablet and brand locked. Marble stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Inviting abundant pacing.

[OUTPUT]
Photoreal food-lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T49 · Kitchen Countertop Morning

**Family:** TF13 · Lifestyle Context | **Tier:** universal | **Sectors:** F&B, Home, Appliances | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** soft natural (bright wholesome)
**Color story:** Bright modern kitchen morning — clean counters, fresh breakfast elements, warm-cool balance. Product centered as the breakfast hero.
**Reference accounts:** @aseeb.najd, @cafe.najd, @laylali_riyadh | **Cultural Spec:** CS-13

**WHEN TO USE:** Breakfast-moment lifestyle — the wholesome modern Saudi morning. F&B breakfast products, spreads, cereals, coffee; home/appliances.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Breakfast arrangement, camera angle, and counter depth are creative decisions; the product reads brand-accurate as the centered hero. INTEGRATION: one bright morning light fills the kitchen — the product, the fresh breakfast elements, and the counter share its warmth and its soft shadow direction.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default phone_natural with bright morning lift. Material truth: {product.material_texture} — the product substrate honest among real fresh-food textures, real counter character, natural lived-in warmth. No staged-sterile kitchen, no plastic food.

[SCALE CALIBRATION]
{product.dimensions} — true size among real breakfast anchors: a bowl, bread, fruit at honest scale; the product centered but never inflated.

[FRAMING & PROXIMITY]
At the counter — the product and its breakfast world close and inviting, the bright kitchen breathing soft behind.

[COLOR & CONTRAST]
Fresh wholesome palette — clean bright kitchen tones, fresh food colors, warm morning glow; the product's color from {brand.color_field_palette} is the centered focal pop.

[LIGHT & LENS]
ONE bright morning light — fresh, clean, soft directional warmth, airy and wholesome. Product sharp, breakfast context soft.

[NATURAL PLACEMENT]
The product stands or rests at the breakfast scene's center as a hand placed it — honest contact among the fresh elements.

[COMPANION ELEMENTS]
ONE hero companion from {product.companion_elements} leads (the prepared result, a poured drink, a fresh ingredient); the remaining breakfast elements stay soft, secondary, uncrowded.

[SCENE]
Kitchen breakfast composition. A bright modern countertop with a morning breakfast scene arranged around the centered product — fresh elements, clean counter, soft-focus bright kitchen behind, morning light filling the space. Wholesome, relatable, modern Saudi morning. Choice points: arrangement, camera height, hero companion, light direction.

[SUBJECT]
The product as centered breakfast hero amid fresh morning context — freshness, counter, and light in wholesome truth.

[BRAND CONSTRAINTS]
Product centered as hero, breakfast context supporting. No human elements (hands only if essential). No pork, no alcohol. Real modern Saudi kitchen (CS-13). No readable text on background packaging — neighboring items text-free or out of focus. {brand.anti_attributes}

[OUTPUT]
Photoreal lifestyle photography, maximum fidelity. Fresh wholesome morning grade, product focal pop. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the kitchen register — modern Saudi family kitchen. For Ramadan: suhoor pre-dawn or iftar context. Breakfast elements reflect Saudi morning foods where relevant.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: breakfast arrangement, hero companion, camera height, light direction. A fresh different morning each generation.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, breakfast scene, counter, morning light — all preserved. Brand elements locked.

[MOTION]
Primary — atmosphere: steam from a hot element, fresh food glisten, morning light shifting gently across the counter.
Secondary — ambient: soft bright kitchen life behind, gentle light breath.
Tertiary — camera: extremely subtle push-in toward the product.

[WHAT STAYS STATIC]
Product identity and material texture locked. Breakfast arrangement stable. Kitchen fixed. Morning warmth constant. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Fresh wholesome morning pacing.

[OUTPUT]
Photoreal lifestyle cinematography. Silent. No text overlay, no watermark.

---

## T50 · Hotel Candle Moment

**Family:** TF13 · Lifestyle Context | **Tier:** luxury | **Sectors:** Hospitality, Beauty, Fragrance, Home | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** warm candlelit chiaroscuro (intimate)
**Color story:** Warm candlelight glow in a soft luxury hotel room at evening — amber flame warmth, deep evening shadow, plush textures. The product glows in the candlelight.
**Reference accounts:** @danatreasures, @diplomat_sweets, @alyafie_jewelry | **Cultural Spec:** CS-13, CS-19

**WHEN TO USE:** Intimate evening luxury for hospitality, premium beauty, fragrance, home/candle brands. Indulgent evening relaxation; the candlelight glow is the warm seductive hook.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Candle position, texture staging, and camera angle are creative decisions; the product reads brand-accurate, catching the candlelight. INTEGRATION: the candle flame is the one light — its amber glow models the product, warms the plush textures, and falls naturally into evening shadow; the product's flicker-lit highlights and soft shadow belong entirely to the flame.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — intimate luxury cinema, subtle warm grain in shadow. Material truth: {product.material_texture} — the substrate in flickering candlelight reads true. Real flame warmth and light-throw, plush hotel textures (linen, velvet, marble) with true character, natural glow falloff. No flat digital flame, no plastic luxury.

[SCALE CALIBRATION]
{product.dimensions} — true size beside a real candle (the candle itself a natural scale anchor); plush textures at honest room scale.

[FRAMING & PROXIMITY]
Intimate and close — product and flame near in the warm pool, the evening room dissolving softly behind.

[COLOR & CONTRAST]
Intimate luxury palette — candle-gold flame warmth, deep warm-dark evening, plush texture tones; the product's brand color glows in the candlelight as the intimate focal hero.

[LIGHT & LENS]
ONE light: the candle's flickering amber flame as primary source with deep evening falloff (optional whisper of ambient evening fill within the same warmth). Product sharp, candlelit scene warm bokeh.

[NATURAL PLACEMENT]
The product rests beside the candle as an evening hand placed it — settled into the plush surface with honest contact.

[COMPANION ELEMENTS]
The lit candle is the chain's ONE hero companion; plush textures are surface, not props. Nothing more enters.

[SCENE]
Hotel candle moment. A lit candle glows in a soft luxury hotel-room setting at evening — fine linen, a velvet surface, marble — the product positioned in the intimate candlelit glow, deep evening warmth surrounding. Indulgent, luxurious-evening. Choice points: candle position, texture staging, camera angle, shadow depth.

[SUBJECT]
The product as intimate hero in candlelight; flame and luxury textures the warm evening context, in authentic truth.

[BRAND CONSTRAINTS]
Product hero in candlelight. Candle and textures as context. No human elements. Real luxury Saudi hospitality aesthetic (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal intimate luxury photography, maximum fidelity. Warm candlelit grade, golden glow, intimate product hero. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the luxury hospitality register — premium Saudi hotel/home evening. For oud/incense: bukhoor warmth context (CS-19). For Ramadan: post-iftar intimate evening warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: candle position, texture staging, camera angle, shadow depth, glow spread. A different intimate evening each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, candle, flame, hotel textures, warm glow — all preserved. Brand elements locked.

[MOTION]
Primary — the flame: flickers naturally and continuously, warm glow subtly dancing across product and textures, shadows shifting gently with it.
Secondary — atmosphere: a faint wisp of candle smoke or warm air shimmer.
Tertiary — camera: extremely subtle push-in toward the product.

[WHAT STAYS STATIC]
Product identity and material texture locked. Candle and product positions fixed. Textures stable. Warm temperature constant. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow intimate evening pacing — the flame breathes.

[OUTPUT]
Photoreal intimate luxury cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF14 · PREMIUM PEDESTAL — 3 chains
**Drama dial:** T51 warm opulent single key · T52 clean design-editorial · T53 museum single key

---

## T51 · Reflective Gold Pedestal Smoke

**Family:** TF14 · Premium Pedestal | **Tier:** luxury | **Sectors:** Fragrance, Oud, Jewelry, Luxury Retail | **Intent:** launch | **Frequency:** 1× per quarter | **Reference image:** Required | **Drama dial:** warm opulent single key
**Color story:** Reflective gold cylindrical pedestal with soft smoke wisps curling around. Gold-and-smoke luxury — warm reflectance, ceremonial vapor, deep warm dark.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-19, CS-22

**WHEN TO USE:** Opulent pedestal with mystique — gold luxury plus ceremonial smoke. The most premium fragrance/oud/jewelry launches; deeply Saudi-luxury-resonant.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Camera height, pedestal proportion, and smoke choreography are creative decisions; the product reads brand-accurate, smoke curling around without obscuring it. INTEGRATION: one warm key governs everything — the product's modeling, the gold's specular highlights and mirrored base, the smoke's lit translucency, the warm-dark falloff; one ceremonial light system.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — opulent luxury cinema, subtle warm grain. Material truth: {product.material_texture} — the substrate catches the warm key and gold bounce truly. Real reflective gold with honest speculars and a soft mirror of the product's base; smoke with true volumetric turbulence. No plastic gold, no flat digital smoke.

[SCALE CALIBRATION]
{product.dimensions} — true size atop a pedestal proportioned to present it; smoke wisps at honest bukhoor-vapor scale curling around real-sized forms.

[FRAMING & PROXIMITY]
Close, ceremonial — product and gold pedestal-top the luminous center, smoke weaving near, warm dark pressing in.

[COLOR & CONTRAST]
Opulent gold-and-smoke palette — glowing gold pedestal, warm ceremonial vapor, deep warm dark; the product's brand color from {brand.color_field_palette} punches against the gold reflectance as the prized hero.

[LIGHT & LENS]
ONE warm directional key modeling product and pedestal, its rim catching the smoke for translucency, deep warm-dark surround. Product and pedestal sharp; smoke and background soft.

[NATURAL PLACEMENT]
The product stands centered and plumb on the gold — ceremonial placement, true mirrored contact on the polished surface.

[COMPANION ELEMENTS]
The smoke is the chain's ONE ceremonial companion — around, never on, never obscuring the brand face.

[SCENE]
Opulent pedestal-with-smoke composition. Product atop a reflective gold cylindrical pedestal, soft smoke wisps curling slowly around — semi-transparent, ascending, ceremonial, reading as bukhoor/oud incense. Deep warm-dark gradient behind. Opulent, mysterious, deeply Saudi-luxury. Choice points: camera height, pedestal proportion, smoke density and path, background depth.

[SUBJECT]
The product atop the gold pedestal, soft smoke around — gold reflectance, volumetric smoke, and product material in full physical truth.

[BRAND CONSTRAINTS]
Single product on the gold pedestal. Smoke around, not obscuring. No human elements. Warm dark background. No text. {brand.anti_attributes}

[OUTPUT]
Photoreal opulent luxury photography, maximum fidelity. Gold-and-smoke warm grade, brand-color hero punch. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — smoke reads as bukhoor/oud incense (CS-19), gold resonates with Saudi luxury. For Eid/Founding Day: subtle gold particles in the smoke. {saudi.color_palette_adjust} tunes gold warmth.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: smoke density and choreography, camera height, pedestal proportion and finish, key warmth. The ceremony never repeats.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, gold pedestal, reflection, smoke wisps, warm light — all locked.

[MOTION]
Primary — smoke: wisps curl and rise slowly around pedestal and product in ceremonial vortex motion, new tendrils forming and dissipating.
Secondary — the pedestal: optional extremely slow rotation (~15°) of product+pedestal, gold catching shifting highlights; brand face stays toward camera.
Tertiary — atmosphere: warm particles drift through the light.

[WHAT STAYS STATIC]
Product identity and material texture locked. Gold pedestal stable. Warm-dark background. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow opulent ceremonial pacing.

[OUTPUT]
Photoreal opulent luxury cinematography. Silent. No text overlay, no watermark.

---

## T52 · Ceramic Stacked Modern Plinth

**Family:** TF14 · Premium Pedestal | **Tier:** premium | **Sectors:** Beauty, Fragrance, Luxury Retail, Home | **Intent:** launch, grow | **Frequency:** 1× per month | **Reference image:** Required | **Drama dial:** clean design-editorial
**Color story:** Stacked ceramic plinth forms in soft matte earth tones — sculptural designer geometry. Muted sophisticated palette (sand, clay, cream).
**Reference accounts:** @danatreasures, @planb_boutique, @alyafie_jewelry | **Cultural Spec:** CS-22

**WHEN TO USE:** Designer-object presentation — sculptural modern forms positioning the product as a design object. Contemporary curated taste.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The plinth stack's geometry, earth-tone selection, and camera angle are creative decisions; the product reads brand-accurate atop the sculptural arrangement. INTEGRATION: one soft directional light models the matte ceramic geometry and the product as a single still life — shared shadow logic, shared falloff.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with design-editorial grade. Material truth: {product.material_texture} — the substrate true under soft light; the ceramics with real matte clay texture, honest hand-formed character, subtle surface variation. No plastic-perfect ceramic.

[SCALE CALIBRATION]
{product.dimensions} — true size atop ceramic forms proportioned as a designer plinth (sculptural blocks, not monuments); the stack serves the product's honest scale.

[FRAMING & PROXIMITY]
The product and its sculptural stack command the frame — close design-gallery presence, geometry leading the eye upward to the hero.

[COLOR & CONTRAST]
Muted sophisticated palette — soft matte earth-tone ceramics (sand, clay, cream, tunable toward {brand.color_field_palette}-harmonious earths); the product's brand color reads as the designer-object focal accent against the restrained forms.

[LIGHT & LENS]
ONE soft directional studio light, gentle quality modeling the matte forms with subtle shadow, revealing the sculptural geometry. Product and plinth sharp, background soft.

[NATURAL PLACEMENT]
The product stands centered and stable atop the stack — deliberate curatorial placement with honest contact.

[SCENE]
Designer ceramic plinth composition. The product atop a stack of sculptural ceramic forms (cylinders, spheres, geometric blocks) in soft matte earth tones — an artful designer arrangement on a clean complementary background. Contemporary, curated, design-forward. Choice points: stack geometry, earth-tone mix, camera angle, background tone.

[SUBJECT]
The product atop the sculptural plinth — matte ceramic texture and geometry as designer styling, all in authentic truth.

[BRAND CONSTRAINTS]
Single product on the ceramic plinth. Sculptural forms the only styling. No human elements. Clean background. No text. {brand.anti_attributes}

[OUTPUT]
Photoreal design-editorial photography, maximum fidelity. Muted sophisticated grade, sculptural ceramic, brand-color designer accent. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} — ceramic tones can shift toward the Saudi earth palette (desert sand, Najdi clay, Diriyah mudbrick tones). Culturally neutral otherwise.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: stack geometry and form mix, earth-tone selection, camera angle and height, shadow softness. A new sculpture for the same object each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, ceramic plinth forms, background, lighting — all preserved. Brand elements locked.

[MOTION]
Primary — light: soft directional light shifts gently, modeling shadow sliding subtly across the matte geometry and product.
Secondary — camera: a slow smooth dolly or gentle arc around the plinth, revealing the sculptural forms dimensionally; brand face stays toward camera.

[WHAT STAYS STATIC]
Product identity and material texture locked. Plinth arrangement stable. Background constant. Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow design-gallery pacing.

[OUTPUT]
Photoreal design-editorial cinematography. Silent. No text overlay, no watermark.

---

## T53 · Marble Plinth With Spotlight

**Family:** TF14 · Premium Pedestal | **Tier:** luxury | **Sectors:** Fragrance, Jewelry, Luxury Retail, Beauty | **Intent:** launch | **Frequency:** 1× per quarter | **Reference image:** Required | **Drama dial:** museum single key
**Color story:** Elegant marble plinth under a precise directional spotlight — museum-quality. Cool-warm veining, dramatic single-light pool, deep surround.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-22

**WHEN TO USE:** Museum-quality presentation — the highest-prestige pedestal chain. Luxury fragrance, fine jewelry, premium launches; marble plus spotlight is the pinnacle of refined presentation.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Marble character, spotlight angle, and camera height are creative decisions; the product reads brand-accurate, spotlit atop the marble. INTEGRATION: one precise spotlight defines everything — the tight pool on product and plinth top, the marble's lit veining, the rapid falloff into deep surround; one museum light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with museum-luxury grade. Material truth: {product.material_texture} — the substrate true under the precise pool; the marble with real veining variation, honest polished sheen. No plastic-perfect marble, no artificial glow.

[SCALE CALIBRATION]
{product.dimensions} — true size on a plinth proportioned to exhibit it; the spotlight pool scaled to the treasure it presents.

[FRAMING & PROXIMITY]
Close, reverent — product and lit plinth-top the singular focus, the deep surround near and pressing; museum intimacy, not gallery distance.

[COLOR & CONTRAST]
Refined museum palette — cool or warm marble veining catching the spotlight, deep surround; the product's brand color from {brand.color_field_palette} is the illuminated treasure, the single chromatic focus.

[LIGHT & LENS]
ONE precise directional spotlight from upper-side — tight controlled pool on product and plinth top, rapid falloff into deep surround shadow, only the subtlest fill preserving brand readability within the same system. Product and plinth-top sharp, surround deep.

[NATURAL PLACEMENT]
The product stands centered and plumb — ceremonial museum placement, true contact on the polished marble.

[SCENE]
Museum marble plinth composition. The product atop an elegant marble plinth (white Calacatta veining or warm-toned), a single precise spotlight pooling tightly on product and plinth top, light falling into a deep surround — the illuminated treasure. Refined, prestigious, museum-grade. Choice points: marble character, spotlight angle, pool tightness, camera height.

[SUBJECT]
The product atop the marble plinth, museum-spotlit — veining and product material in full physical truth; the singular illuminated treasure.

[BRAND CONSTRAINTS]
Single product on the marble plinth. Plinth and spotlight the only elements. No human elements. Deep surround. No text. {brand.anti_attributes}

[OUTPUT]
Photoreal museum-luxury photography, maximum fidelity. Refined marble-and-spotlight grade, brand-color treasure focus. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} — marble can shift to warm Saudi-preferred tones; spotlight warms for heritage/oud. For Eid/Founding Day: subtle gold accent possible.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: marble character, spotlight angle and pool tightness, camera height, surround depth. The treasure is exhibited anew each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, every label character, {product.material_texture}, marble plinth, spotlight pool, deep surround — all locked.

[MOTION]
Primary — light: the spotlight intensifies subtly ~10%, the product emerging more fully as the treasure; OR the plinth slowly rotates (~15°), veining and product catching shifting light, brand face toward camera.
Secondary — atmosphere: faint particles drift through the beam.

[WHAT STAYS STATIC]
Product identity and material texture locked. Marble plinth and product positions (unless slow rotation). Deep surround constant. Capture character preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow reverent museum pacing.

[OUTPUT]
Photoreal museum-luxury cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF15 · PROMOTIONAL & TEXT — 3 chains · TEXT-CENTRAL
**Drama dial: bold promo punch / clean designed** · **TEXT is a CORE block.**
**Arabic-fidelity dependency (ledger #13):** the deterministic Pillow overlay node is NOT yet built. Until it ships: shortest Arabic copy only, or Latin-only/post-production. This family fires 3–5× per month per client — the dependency is on the critical path.

---

## U02 · Promotional Offer

**Family:** TF15 · Promotional & Text | **Tier:** universal | **Sectors:** F&B, Retail, Beauty, Services | **Intent:** harvest, grow | **Frequency:** 3-5× per month | **Reference image:** Required | **Drama dial:** bold promo punch
**Color story:** Bold promotional energy — strong brand color field with high-contrast price/offer typography. The deal IS the design.
**Reference accounts:** @aseeb.najd, @barnscoffee, @danatreasures | **Cultural Spec:** CS-22

**WHEN TO USE:** Price-led conversion — discount, bundle, or offer composed boldly with the product. TEXT IS CENTRAL. The most conversion-direct chain.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The offer layout — badge style, price placement, field geometry — is a creative decision; the product reads brand-accurate, composed with the offer typography. INTEGRATION: one punchy light holds product and field; the offer graphics live in the same designed grade — one promotional photograph, not a sticker collage.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with bold-promo clarity. Material truth: {product.material_texture} — authentic product substrate, honest light, real soft shadow. Promo graphics clean and bold. No CGI flatness.

[SCALE CALIBRATION]
{product.dimensions} — the product at true size; the offer typography scaled as the dominant graphic without dwarfing the hero into a thumbnail.

[FRAMING & PROXIMITY]
Tight conversion layout — product large and near, offer unmissable beside/around it; engineered for instant comprehension at feed size.

[COLOR & CONTRAST]
Bold saturated brand-color field from {brand.color_field_palette} engineered for attention — never a borrowed promo red unless the brand owns it; high-contrast offer typography (white or brand accent) on the field; the product punches as hero.

[LIGHT & LENS]
ONE clean punchy commercial light, bright with controlled shadow. Full composition sharp.

[NATURAL PLACEMENT]
The product stands or lies with honest gravity within the designed field.

[SCENE — TEXT CENTRAL]
Promotional offer composition. The product hero against the bold brand-color field, the offer/price composed as the dominant graphic message — a large price, a discount badge, a bundle callout. Instant comprehension, scroll-stopping. Choice points: badge style, field geometry, price placement, product pose.

[SUBJECT]
The product hero plus the bold offer typography/graphics — one high-impact promotional layout.

[TEXT — CORE BLOCK for this family]
Render the promotional typography directly as the dominant message:
- Offer: "{brief.text_request.copy}" — price, discount %, bundle deal
- Style: {brief.text_request.style} — default bold high-impact promo type
- Placement: dominant, unmissable, composed with the product
- ARABIC RULE: Arabic offer text RTL character-perfect at the SHORTEST possible copy; until the deterministic overlay node ships, Arabic-heavy offers route to post-production typography. SAR currency formatting per market.
The offer text IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Single product hero with bold offer graphics. No fabricated claims beyond brief. No human elements. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal promotional composition with integrated bold typography, maximum fidelity. Punchy saturated grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns to brand. Arabic offer typography per the Arabic rule. For occasions: offer themed to Ramadan/Eid/seasonal sale.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: badge style, field geometry, price placement, product pose. The deal hits differently each time; the numbers never change.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, offer typography (every character), brand-color field, layout — all preserved.

[MOTION]
Primary — offer graphics: the price/offer text and badge animate in punchy — a quick settle, pop, or emphasis pulse drawing the eye.
Secondary — product: subtle highlight drift.
Tertiary — camera: subtle push-in for energy.

[WHAT STAYS STATIC]
Product identity locked. Offer content locked — no price/text changes. Brand-color field stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Punchy conversion-focused pacing.

[OUTPUT]
Photoreal promotional motion-graphic. Silent. No watermark.

---

## F04 · Menu Price Card

**Family:** TF15 · Promotional & Text | **Tier:** universal | **Sectors:** F&B, Restaurant, Cafe | **Intent:** harvest, grow | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** clean appetizing designed
**Color story:** Appetizing food photo paired with a clean bilingual menu card — warm food colors against clean typographic layout.
**Reference accounts:** @aseeb.najd, @cafe.najd, @laylali_riyadh | **Cultural Spec:** CS-21, CS-22

**WHEN TO USE:** Food menu card — dish photo with bilingual (Arabic + English) name and price. TEXT IS CENTRAL; bilingual typography essential.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} food and menu identity. Identity DNA: {product.identity_dna}
Layout balance, card design, and dish angle are creative decisions; the dish and brand elements read accurate within the menu card design. INTEGRATION: one appetizing light grades dish and card together — one designed menu photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with appetizing menu-commercial grade. Material truth: real appetizing food texture, honest plate and card material, true color. Menu typography clean and legible. No plastic dish.

[SCALE CALIBRATION]
{product.dimensions} where applicable — the dish at true plated scale; the card proportioned as real menu design beside it.

[FRAMING & PROXIMITY]
A balanced close layout — appetizing dish hero near, menu card legible beside; order-decision distance.

[COLOR & CONTRAST]
Warm appetizing food colors as the hero against a clean typographic layout grounded in {brand.color_field_palette}. Crisp, appetizing, informative.

[LIGHT & LENS]
ONE clean appetizing food light, warm and inviting with controlled highlight on the dish. Full composition sharp.

[NATURAL PLACEMENT]
The dish sits plated as the kitchen sends it — honest portion, true garnish physics; the card flat or gently angled.

[SCENE — TEXT CENTRAL]
Menu price card composition. An appetizing photo of the dish paired with a clean menu-card layout showing the item's bilingual name (Arabic + English) and price — a professional menu card balancing food hero with legible typography. Appetizing, informative, order-ready. Choice points: layout balance, card design language, dish angle.

[SUBJECT]
The dish photo plus the bilingual menu typography (name + price), composed as a clean menu card; food appetizing-true.

[TEXT — CORE BLOCK for this family]
Render the bilingual menu typography directly:
- Item name + price: "{brief.text_request.copy}" — bilingual Arabic + English, with price
- Style: {brief.text_request.style} — default clean professional menu type
- Placement: menu-card layout balanced with the food photo
- ARABIC RULE: Arabic name RTL character-perfect at the shortest viable form; until the overlay node ships, Arabic-heavy menus route to post-production typography. (CS-21 governs dish authenticity.)
Bilingual menu text IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Dish hero plus menu card typography. No pork, no alcohol (CS-21). No human elements. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal menu-card composition with bilingual typography, maximum fidelity. Appetizing clean grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — authentic naming and presentation for Saudi dishes (CS-21). Bilingual Arabic-English standard. For Ramadan: iftar menu theming.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: layout balance, card design language, dish angle and plating moment. The menu redesigns; names and prices never change.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Dish photo, menu typography (every character), layout — all preserved.

[MOTION]
Primary — atmosphere: steam rises from the hot dish; appetizing glisten.
Secondary — typography: menu text settles in gently.
Tertiary — camera: subtle push-in toward the dish.

[WHAT STAYS STATIC]
Dish identity locked. Menu content locked — names/prices unchanged. Layout stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Clean appetizing menu pacing.

[OUTPUT]
Photoreal menu-card motion. Silent. No watermark.

---

## R03 · Price Tag Reveal

**Family:** TF15 · Promotional & Text | **Tier:** universal | **Sectors:** Retail, Fashion, Beauty | **Intent:** harvest, grow | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** dramatic reveal (single key)
**Color story:** Retail product with a dramatic price-tag reveal — clean product hero, the tag as a designed focal graphic with reveal drama.
**Reference accounts:** @tiadress, @planb_boutique, @danatreasures | **Cultural Spec:** CS-22

**WHEN TO USE:** Retail price reveal — price drops, sale reveals, new-price announcements. TEXT IS CENTRAL; the dramatic tag reveal creates the deal-discovery moment.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Tag styling, reveal staging, and crop are creative decisions; the product reads brand-accurate, the price tag composed as the focal reveal. INTEGRATION: one dramatic light stages product and tag together — the reveal spotlight that finds the tag also models the product; one theatrical retail moment.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with dramatic reveal lift. Material truth: {product.material_texture} — authentic product substrate; real tag texture, string, paper/card. No plastic tag.

[SCALE CALIBRATION]
{product.dimensions} — the product at true size with a real retail-tag-sized tag; honest proportions between hero and tag.

[FRAMING & PROXIMITY]
Tight on the discovery — product and tag near, the reveal moment filling the frame.

[COLOR & CONTRAST]
Brand color from {brand.color_field_palette} anchors the product; the tag is the crisp focal graphic the lighting reveals. Retail-conversion palette with reveal drama.

[LIGHT & LENS]
ONE dramatic directional light creating the spotlight-reveal feel on tag and product, controlled shadow for drama. Product and tag sharp.

[NATURAL PLACEMENT]
The tag hangs or rests with honest string-and-card physics against the product; the product posed as retail presents it.

[SCENE — TEXT CENTRAL]
Price tag reveal composition. The product hero with its price tag presented dramatically — the tag catching the spotlight as a designed focal reveal, the price prominent. The composition makes the price the discovery. Choice points: tag styling, reveal staging, crop, shadow drama.

[SUBJECT]
The product plus the dramatic price tag — both in authentic truth, the price as the focal reveal.

[TEXT — CORE BLOCK for this family]
Render the price tag typography directly:
- Price/reveal: "{brief.text_request.copy}" — the price, possibly with "was/now" or sale framing
- Style: {brief.text_request.style} — default crisp retail price-tag type
- Placement: on the tag as the dramatic focal reveal
- ARABIC RULE: Arabic/SAR numerals per brief at shortest viable copy; Arabic-heavy reveals route to post-production until the overlay node ships
The price reveal IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Single product with one price tag. No fabricated claims beyond brief. No human elements. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal price-reveal composition with tag typography, maximum fidelity. Dramatic retail grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns to brand. Arabic price typography / SAR currency for Saudi market. For sale events: themed reveal.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: tag styling, reveal staging, crop, shadow drama. The discovery moment restages; the price never changes.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, price tag, typography (every character), lighting — all preserved.

[MOTION]
Primary — the reveal: the tag swings gently into the spotlight, OR the price text emphasis-pulses as the reveal lands.
Secondary — light: the reveal spotlight intensifies.
Tertiary — camera: push-in toward the tag.

[WHAT STAYS STATIC]
Product identity locked. Price content locked. Layout stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Dramatic reveal pacing.

[OUTPUT]
Photoreal price-reveal motion. Silent. No watermark.

---
---

# FAMILY TF16 · OCCASION & CULTURAL — 2 chains · SAUDI ADAPTATION CENTRAL
**Drama dial: occasion-themed (its own register)** · The occasion drives the entire brief; SAUDI ADAPTATION is a core driving block, not conditional.

---

## U03 · Occasion Greeting

**Family:** TF16 · Occasion & Cultural | **Tier:** universal | **Sectors:** F&B, Retail, Beauty, Services, Hospitality | **Intent:** grow | **Frequency:** occasion-triggered | **Reference image:** Recommended | **Drama dial:** occasion-themed (dignified festive)
**Color story:** Occasion-themed — Founding/National Day: Saudi green + white + gold; Eid: warm festive gold + jewel tones; Ramadan: deep night blue/purple + gold crescent warmth. The occasion sets the entire color world.
**Reference accounts:** @aseeb.najd, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-13, CS-19, CS-21, occasion overlay fields

**WHEN TO USE:** Occasion greeting — national holidays (Founding Day Feb 22, National Day Sep 23), Islamic occasions (Ramadan, Eid Al-Fitr, Eid Al-Adha), seasonal moments. AUTO-TRIGGERED by the occasion layer. The greeting text is core.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
The occasion scene's composition is the creative space; the brand/product is present respectfully — never overwhelming the occasion's dignity. Brand DNA preserved but secondary to the occasion's meaning. INTEGRATION: the occasion's themed light (lantern glow, proud daylight, festive warmth) is the one system holding occasion elements and brand together.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default film_grain_warmth for occasion warmth, dignified festive standard. Material truth: {product.material_texture} where the product appears; authentic occasion elements — real crescent/lantern/flag textures, true material character. No plastic festive props, no kitsch.

[SCALE CALIBRATION]
{product.dimensions} — the brand element at honest scale within the occasion scene; lanterns, dates, flags at true real-world proportion.

[FRAMING & PROXIMITY]
The occasion's beauty fills the frame with the brand near but deferential — a warm, close, dignified greeting, not a distant tableau.

[COLOR & CONTRAST]
The occasion sets the ENTIRE color world (Saudi green+white+gold for national days; festive gold+jewel for Eid; night-blue+gold for Ramadan); the brand color from {brand.color_field_palette} integrates respectfully within it — the one chain where the occasion palette leads and the brand follows.

[LIGHT & LENS]
ONE occasion-themed light — warm festive glow for Eid, serene night warmth for Ramadan, bright proud daylight for National/Founding Day.

[NATURAL PLACEMENT]
Occasion elements and brand sit with honest physics — lanterns hang true, dates rest in their bowl, the product placed respectfully within the scene.

[COMPANION ELEMENTS]
Occasion elements ARE the scene; the brand/product is the respectful guest. Restraint: dignified curation, never prop-pile.

[SCENE — OCCASION CENTRAL]
Occasion greeting composition, built around the specific occasion (filled by {saudi.occasion_overlay}):
- Founding Day (Feb 22): Saudi heritage pride — Najdi cultural elements, Diriyah motifs, Saudi green, the 1727 founding spirit
- National Day (Sep 23): modern Saudi pride — green and white, flag motifs, modern Riyadh + heritage blend, celebratory
- Ramadan: spiritual night warmth — crescent moon, lanterns (fanoos), deep night-blue/purple with gold, dates, serene reverent mood
- Eid Al-Fitr: festive joy — warm gold, jewel tones, sweets, celebration
- Eid Al-Adha: dignified celebration — heritage warmth, gathering, generosity
Beautiful, dignified, culturally true. Choice points: scene composition within the occasion's world, element selection, depth.

[SUBJECT]
The occasion as hero, the brand integrated respectfully. Occasion elements rendered authentically (CS-13, CS-19, CS-21). If any human presence: single-subject, modest, dignified.

[TEXT — CORE BLOCK for this family]
Render the occasion greeting typography (often Arabic-primary):
- Greeting: "{brief.text_request.copy}" — e.g. كل عام وأنتم بخير · رمضان كريم · عيد مبارك · يوم التأسيس · اليوم الوطني
- Style: {brief.text_request.style} — elegant occasion-appropriate type, often Arabic calligraphic
- ARABIC RULE: the Arabic greeting is typically primary and dignified — keep to the shortest established greeting form; for calligraphic Arabic, prefer post-production typography until the deterministic overlay node ships
The greeting is central to this chain.

[BRAND CONSTRAINTS]
Occasion dignity comes first; the brand integrates respectfully, never crassly commercial on sacred/national moments. Authentic Saudi occasion elements (CS-13, CS-19, CS-21). Religious occasions handled with reverence. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal occasion greeting composition with dignified typography, maximum fidelity. Occasion-themed grade. No watermark.

[SAUDI ADAPTATION — CENTRAL (this is the brief, not conditional)]
{saudi.occasion_overlay} defines the entire scene. {saudi.scene_context} and {saudi.color_palette_adjust} execute the occasion's visual world authentically. This block drives the chain.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: scene composition within the occasion's world, element selection and arrangement, depth and light warmth. The same occasion greeted freshly each year, each post.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Occasion scene, brand integration, greeting typography (every character), themed elements — all preserved.

[MOTION]
Primary — occasion atmosphere: gentle themed motion — lantern glow flickering (Ramadan), flags or banners stirring softly (national days), festive elements shimmering (Eid). Dignified, not busy.
Secondary — typography: the greeting settles in elegantly.
Tertiary — camera: slow dignified push-in.

[WHAT STAYS STATIC]
Brand integration locked. Greeting content locked. Occasion scene stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Dignified celebratory pacing.

[OUTPUT]
Photoreal occasion greeting motion. Silent (or gentle ambient if appropriate). No watermark.

---

## F03 · Ramadan Iftar Spread — HIGH RISK (multi-element)

**Family:** TF16 · Occasion & Cultural | **Tier:** premium | **Sectors:** F&B, Restaurant, Catering, Hospitality | **Intent:** launch, grow | **Frequency:** Ramadan-triggered | **Reference image:** Required | **Drama dial:** occasion-themed (warm reverent golden)
**Color story:** Warm Ramadan iftar table — golden evening glow, rich traditional dish colors, dates and water, brass and ceramic. Reverent and abundant.
**Reference accounts:** @aseeb.najd, @diplomat_sweets, @laylali_riyadh | **Cultural Spec:** CS-15, CS-18, CS-21, CS-13, CS-08
**RISK NOTE:** abundant multi-dish spread — prefer still over video where identity fidelity is critical; keep human presence to right-hand serving only (CS-08) if at all.

**WHEN TO USE:** Ramadan iftar hero — the breaking-of-fast moment. AUTO-TRIGGERS during Ramadan. F&B, restaurants, catering, hospitality Ramadan campaigns. Deeply Saudi, reverent.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Spread arrangement, shot angle, and dish selection are creative decisions; the brand/product (a dish, beverage, or packaged item) integrates into the iftar spread, brand-readable but respectful of the occasion. INTEGRATION: the golden iftar-hour light — just after Maghrib, lamp warmth supplementing within the same system — holds the entire spread, the brass, the dates, and the brand element in one reverent glow.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — Ramadan evening cinema, warm grain. Material truth: {product.material_texture} for the brand element; real food textures of authentic Saudi iftar dishes, honest dates with natural variation, true brass dallah patina, authentic ceramic and textile. No plastic spread, no inauthentic Hollywood-Arabian aesthetic.

[SCALE CALIBRATION]
{product.dimensions} — the brand element at honest scale among real iftar anchors: dates, a finjan, the dallah, serving dishes all at true tabletop proportion.

[FRAMING & PROXIMITY]
Elevated top-down or three-quarter, close over the table — the abundance edge to edge, the viewer seated at the iftar table.

[COLOR & CONTRAST]
Warm Ramadan palette — golden evening glow, rich traditional dish colors, deep dates brown, brass gold, the serene abundance of iftar; the brand color integrates within the warm spread, never shouting over the occasion.

[LIGHT & LENS]
ONE light system: the warm golden iftar-hour glow just after sunset, lamp warmth supplementing as part of it. Rich, reverent, abundant. Spread sharp.

[NATURAL PLACEMENT]
Every dish, date bowl, and vessel sits as a real iftar table is laid — honest weights and contacts, the dallah and finjan placed per serving ritual (CS-18).

[COMPANION ELEMENTS]
STRUCTURAL EXCEPTION: the composed iftar spread IS the scene — dates and water prominent as the traditional fast-breaking elements, dallah and finjan per ritual; restraint applies as nothing outside the authentic iftar table enters.

[SCENE — OCCASION CENTRAL]
Ramadan iftar spread composition. A full, beautifully abundant iftar table set for breaking the fast — dates and water prominent, traditional and modern Saudi dishes (CS-21), a brass dallah and finjan (CS-18), warm ceramic, geometric Saudi textile. Warm golden evening light. The brand integrates as one beautiful element. Reverent, abundant, spiritual-festive. Choice points: arrangement geometry, shot angle, dish selection by region, textile character.

[SUBJECT]
The iftar spread as hero, brand integrated. Authentic Saudi iftar foods, dates, water, dallah, traditional serving elements in full physical truth (CS-15, CS-18, CS-21). No human figures — or hands only, right-hand serving (CS-08).

[BRAND CONSTRAINTS]
Iftar spread hero, brand integrated respectfully. No pork, no alcohol (CS-21). Authentic Saudi iftar (CS-15, CS-18, CS-21), not generic Arabian. Reverent treatment of the religious occasion. No readable text beyond the brand's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal Ramadan iftar photography, maximum fidelity. Warm reverent abundant grade. No overlay text, no watermark.

[SAUDI ADAPTATION — CENTRAL (this is the brief, not conditional)]
{saudi.occasion_overlay} = Ramadan iftar drives the scene. {saudi.scene_context} fills authentic Saudi iftar dishes and serving by region. {saudi.material_context} fills dallah/ceramic/textile authenticity. This block drives the chain.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style} (Ramadan greeting if requested; shortest Arabic form, post-production preferred), placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: arrangement geometry, shot angle, regional dish selection, textile and vessel character. The iftar table is laid anew each evening.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Iftar spread, dishes, dates, dallah, brand integration, {product.material_texture}, warm light — all preserved.

[MOTION]
Primary — atmosphere: steam rises gently from hot iftar dishes; warm lamp light flickers softly; the serene evening glow breathes.
Secondary — if dallah present: a subtle steam wisp from the coffee.
Tertiary — camera: slow reverent push-in or gentle top-down descent over the spread.

[WHAT STAYS STATIC]
Brand integration locked. Spread arrangement stable. Dates, dallah, dishes fixed. Warm temperature constant. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow reverent abundant pacing.

[OUTPUT]
Photoreal Ramadan iftar cinematography. Silent — reverent. No text overlay, no watermark.

---
---

# FAMILY TF17 · BEFORE / AFTER — 2 chains · ELEVATED COMPLIANCE
**Drama dial: clean even, clinical/aspirational** · Human chains under ELEVATED COMPLIANCE: single subject, treatment area only, modesty per CS-24 absolute.

---

## B01 · Before / After Service

**Family:** TF17 · Before / After | **Tier:** premium | **Sectors:** Beauty, Skincare, Salon, Aesthetic Services | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** clean even clinical
**Color story:** Clean clinical-aspirational palette — even neutral lighting, true skin tones, the result spoken through clarity. Consistent color across the split so the improvement reads honestly.
**Reference accounts:** @danatreasures, @tiadress | **Cultural Spec:** CS-24, CS-22

**WHEN TO USE:** Beauty service proof — a split before-and-after. ELEVATED COMPLIANCE: strictly modest framing, single subject, result on appropriate areas only (skin, hair within modesty, nails, treatment zones). The honest result drives the booking decision.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} service identity. Identity DNA: {product.identity_dna}
The split layout (side-by-side vs divided) and the treatment-area crop are creative decisions within elevated compliance; the service brand context is accurate, the result honest and achievable. INTEGRATION: ONE identical light system across both halves — same source, same angle, same grade — so the comparison is physically fair; the only variable is the result.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with honest clinical-aspirational grade, consistent lighting across both halves. Material truth of skin: real authentic texture in BOTH before and after — the after is improved, not airbrushed to fantasy. Honest true-to-life result, consistent color. No CGI-smooth fake result, no deceptive over-retouching, no impossible transformation.

[SCALE CALIBRATION]
True anatomical scale — the treatment area at identical crop and magnification in both halves; the comparison reads at matched scale or it doesn't read at all.

[FRAMING & PROXIMITY]
Tight on the treatment area in both halves — close enough that real texture and the honest improvement read clearly.

[COLOR & CONTRAST]
Clean neutral palette with true skin tones; the result reads through clarity, not color drama. Identical white balance across both halves.

[LIGHT & LENS]
ONE even clinical-aspirational light, identical across both halves — fair, trustworthy, flattering-real. Treatment area sharp.

[NATURAL PLACEMENT]
The subject's position and angle match across both halves — same pose, same turn, the honest constancy that makes the comparison legitimate.

[SCENE — ELEVATED COMPLIANCE]
Before/after split composition. A clean split-frame showing the same treatment area before and after — consistent angle, consistent lighting, honest comparison. The treatment zone shown modestly: facial skin within modest framing, hair within modesty register, nails, hands, or the specific area. Clean neutral background. Choice points: split orientation, crop selection, background tone.

[SUBJECT]
SINGLE subject, ELEVATED modest framing (CS-24). The before/after shows ONLY the appropriate treatment area — never objectifying, never exposing beyond the modest register, fully Saudi-appropriate. For facial/skin: modest crop respecting hijab register. The honest result is the subject.

[BRAND CONSTRAINTS]
SINGLE subject. ELEVATED modesty (CS-24) — treatment area only. Honest achievable result, no deceptive transformation. No full-body exposure. No readable text (labels fire only via the conditional block). {brand.anti_attributes}

[OUTPUT]
Photoreal before/after beauty photography, maximum fidelity. Clean honest grade, consistent comparison. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} governs modest framing of the treatment area (CS-24). Result presentation respects Saudi modesty fully.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style} (e.g. "before / after" labels), placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: split orientation, crop selection within compliance, background tone. The honesty rules never vary.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The before/after composition, treatment area, modest framing, consistent lighting — all preserved. Modesty maintained.

[MOTION]
Primary — transition: a clean wipe or dissolve between before and after states, OR a subtle reveal of the after result. ONE honest, clear transition.
Secondary: minimal — the comparison clarity is the point.

[WHAT STAYS STATIC]
Subject identity, modest framing, treatment area — locked. Modesty compliance absolute. Consistent lighting across both states. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Clean honest reveal pacing.

[OUTPUT]
Photoreal before/after cinematography. Silent. No text overlay, no watermark.

---

## B02 · Service Showcase Static

**Family:** TF17 · Before / After | **Tier:** premium | **Sectors:** Beauty, Skincare, Salon, Aesthetic Services | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** soft aspirational glow
**Color story:** Aspirational beauty-result glow — soft flattering light, true radiant result, clean elegant backdrop. The single result speaks for itself.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride | **Cultural Spec:** CS-24, CS-22

**WHEN TO USE:** Single-result beauty showcase — the achieved result without a before comparison. ELEVATED COMPLIANCE, modest framing, single subject. Cleaner and more aspirational than the split.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} service identity. Identity DNA: {product.identity_dna}
The result crop and backdrop tone are creative decisions within elevated compliance; the service result is honest and aspirational, brand context accurate. INTEGRATION: one soft beauty light creates the result's glow and the backdrop's elegance together — a single aspirational photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with aspirational beauty-result grade — glowing-but-honest. Material truth of skin/hair/nails: real radiant texture, honest achievable glow, true result — aspirational but real, never airbrushed fantasy. No impossible result.

[SCALE CALIBRATION]
True anatomical scale at the chosen crop — the result area at honest close-up proportion.

[FRAMING & PROXIMITY]
Close on the result — radiant skin, styled hair within register, elegant nails, or the treatment result filling the frame aspirationally.

[COLOR & CONTRAST]
Aspirational beauty glow — soft radiant result tones against a clean elegant backdrop tuned toward {brand.color_field_palette} compatibility; the result is the focus, color soft and flattering.

[LIGHT & LENS]
ONE soft flattering beauty light, glowing and aspirational with gentle dimensional shadow. Result area sharp.

[NATURAL PLACEMENT]
The pose is a natural composed human moment presenting the result honestly.

[SCENE — ELEVATED COMPLIANCE]
Service showcase composition. A single beautiful image of the achieved result — shown modestly and aspirationally against a clean elegant backdrop. The result glows. Single-result, aspirational, trustworthy. Choice points: crop, backdrop tone, glow emphasis.

[SUBJECT]
SINGLE subject, ELEVATED modest framing (CS-24). The result on the appropriate area only, modest register respected, never objectifying. Radiant achievable beauty; real skin, honest glow.

[BRAND CONSTRAINTS]
SINGLE subject. ELEVATED modesty (CS-24) — result area only. Honest achievable result. No readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal beauty showcase photography, maximum fidelity. Glowing aspirational grade, honest result. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} governs modest framing (CS-24). Result respects Saudi modesty fully.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: crop selection within compliance, backdrop tone, glow emphasis, pose nuance. The aspiration renews; the modesty rules never vary.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The result, modest framing, lighting, backdrop — all preserved. Modesty maintained.

[MOTION]
SINGLE subtle motion: a gentle glow-shimmer across the result (radiant skin catching light), OR if hair, the faintest movement, OR a soft light breath emphasizing the glow. Restrained, aspirational.

[WHAT STAYS STATIC]
Subject identity, modest framing, result area — locked. Modesty compliance absolute. Lighting stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Soft aspirational pacing.

[OUTPUT]
Photoreal beauty showcase cinematography. Silent. No text overlay, no watermark.

---
---

# BATCH 3 · AGENT RUNTIME NOTES

**Block inclusion:** [TEXT] CORE on U05, U02, F04, R03, U03 (Arabic rule embedded in each); conditional everywhere else. [SAUDI ADAPTATION] CENTRAL (drives the brief) on U03 and F03; conditional elsewhere. [COMPANION ELEMENTS] one-hero active on F02, T47, T49, T50 (candle), T51 (smoke), T42-style logic; STRUCTURAL EXCEPTIONS declared on T48 and F03 (composed abundant spreads ARE the scene — restraint = nothing beyond the deliberate arrangement).

**Human-chain rules:** U04 partial-body only (CS-08 right-hand, CS-01 sleeve); B01/B02 ELEVATED COMPLIANCE (single subject, treatment area only, CS-24 absolute, honest non-deceptive results, identical lighting across B01's halves).

**Arabic dependency (ledger #13):** TF15 fires 3–5×/month per client — the highest-frequency text-central family in the library. The deterministic Pillow overlay node is on the critical path for this family's production use. Until built: shortest Arabic copy or post-production.

**Drama dial:** TF13 soft natural/authentic (U04 phone-documentary, U05 clean designed, T50 warm candlelit chiaroscuro) · TF14 warm opulent / design-editorial / museum single key · TF15 bold promo punch / clean designed · TF16 occasion-themed (occasion palette leads, brand follows — the one family where this inverts) · TF17 clean even clinical/aspirational.

**Failure-ledger compliance:** all 17 chains carry the 15-block order, the four v3.7 fields where applicable, brand-derived color (occasion chains documented as the deliberate inversion), proportion anchoring, framing-proximity, integration, no-readable-background-text, conditional/core text logic, and the CREATIVE VARIANCE DIRECTIVE. No fixed mm / f-stop / Kelvin commands anywhere.

*OpenClaw · Master Prompt Library v3.7 · Batch 3 · TF13 + TF14 + TF15 + TF16 + TF17 · 17 chains · Confidential*

<!-- ══════════ OpenClaw_v3_7_Batch4_TF18_TF19_TF20_TF21.md ══════════ -->

# FAMILY TF18 · PRODUCT FLAT LAY — 4 chains
**Drama dial: palette discipline (busy curated compositions — controlled color, overhead light)**

---

## B03 · Beauty Product Flat Lay

**Family:** TF18 · Product Flat Lay | **Tier:** premium | **Sectors:** Beauty, Cosmetics, Skincare | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** palette discipline, editorial-curated
**Color story:** Curated top-down beauty arrangement — the product hero among complementary props in a designed palette. Brand color leading, props echoing, clean negative space.
**Reference accounts:** @danatreasures, @tiadress, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Editorial beauty flat lay — cosmetics/skincare launches, collection reveals, beauty editorial. Curated overhead taste; social-native and shareable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved through the overhead angle: {product.identity_dna}
The arrangement geometry, prop selection, and negative-space design are creative decisions; the product reads brand-accurate, brand-readable face up toward the overhead camera. INTEGRATION: one soft overhead light holds product and props on one surface with one shadow direction — a single curated photograph, never a collaged board.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with editorial flat-lay grade, perfectly overhead. Material truth: {product.material_texture} — the product's top surfaces true; fresh petals with real delicacy, real fabric weave, true tool materials, honest soft shadow, natural arrangement character. No plastic props, no sterile-perfect placement.

[SCALE CALIBRATION]
{product.dimensions} — the product at true size among real-scale props (petals a few centimeters, tools at honest hand size); the arrangement's believability lives in true proportions.

[FRAMING & PROXIMITY]
The curated arrangement fills the frame with intentional negative space as design — the hero large and central in the composition's flow, never a small object lost on a wide surface.

[COLOR & CONTRAST]
Editorial flat-lay harmony with palette discipline: the brand color from {brand.color_field_palette} leads; props echo the brand-derived palette (never tones borrowed from an unrelated reference); clean negative space gives the arrangement room to breathe.

[LIGHT & LENS]
ONE soft even overhead light with gentle directional quality for subtle shadow and dimension. Perfectly overhead; full arrangement sharp.

[NATURAL PLACEMENT]
Every element lies with honest top-down physics — petals curling naturally, fabric draping with real folds, the product resting face-up with true contact shadow.

[COMPANION ELEMENTS]
Curated-arrangement logic: props derived from {product.companion_elements} (florals, a fabric length, a beauty tool, a raw ingredient) — selected to echo the product's story, supporting never crowding; the hero stays unmistakable.

[SCENE]
Beauty flat lay, shot directly overhead. The product hero surrounded by a curated arrangement of complementary props with editorial taste and intentional negative space, on a clean designed background. Curated, tasteful, complete. Choice points: arrangement geometry, prop selection within the derived world, negative-space design, background tone.

[SUBJECT]
The product as flat-lay hero, props supporting — all materials in authentic truth, arranged with editorial intention.

[BRAND CONSTRAINTS]
Product hero with curated complementary props. No human elements. Clean designed background. Props support, never crowd. No readable text on any prop. {brand.anti_attributes}

[OUTPUT]
Photoreal beauty flat-lay photography, maximum fidelity. Curated editorial grade, brand-color harmony. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} tunes the palette toward Saudi-resonant tones; props can include Saudi elements (Taif rose, oud chips, gold) for heritage beauty brands.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: arrangement geometry, prop selection and count, negative-space flow, background tone within the brand range. A newly curated board each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, prop arrangement, background, top-down framing — all preserved. Brand elements locked.

[MOTION]
Primary — props: petals or fabric edges shift gently as if from soft air; a fresh element glistens.
Secondary — light: soft overhead light shifts subtly across the arrangement.
Tertiary — camera: imperceptible overhead push-in.

[WHAT STAYS STATIC]
Product identity and material texture locked. Arrangement stable. Top-down angle constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle editorial flat-lay pacing.

[OUTPUT]
Photoreal beauty flat-lay cinematography. Silent. No text overlay, no watermark.

---

## B05 · Bridal Beauty Package — COLLECTION chain

**Family:** TF18 · Product Flat Lay | **Tier:** luxury | **Sectors:** Beauty, Bridal, Cosmetics, Fragrance | **Intent:** launch, grow | **Frequency:** 1× per month (bridal season) | **Reference image:** Required | **Drama dial:** palette discipline, romantic-luxury
**Color story:** Luxurious bridal palette — soft whites, blush, gold, pearl, the premium collection beautifully arranged. Romantic-luxury, gift-worthy, dreamy.
**Reference accounts:** @themodestbride, @danatreasures, @tiadress | **Cultural Spec:** CS-22

**WHEN TO USE:** Bridal collection flat lay — wedding-occasion targeted. Bridal beauty, premium cosmetics, fragrance gift sets. Strong for the lucrative Saudi bridal market.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} collection identity. Identity DNA, preserved through the overhead angle: {product.identity_dna}
The collection's arrangement and bridal-prop styling are creative decisions; EVERY product in the collection reads brand-accurate, brand-readable faces up. Identity fidelity is required on each piece — a multi-product chain raises the verification bar, not lowers it. INTEGRATION: one soft luminous overhead light holds collection and bridal props in a single romantic photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with luxury-bridal grade, perfectly overhead. Material truth: {product.material_texture} across the collection — real luxury sheen on each piece; real silk, fresh florals, pearl and gold detail with true reflectance. No plastic props, no sterile arrangement.

[SCALE CALIBRATION]
{product.dimensions} per piece — the collection's items at true relative sizes to each other and to the bridal props; honest gift-set proportions.

[FRAMING & PROXIMITY]
The treasured collection fills the frame as the centerpiece — generous, near, complete; the bridal props weaving close around it.

[COLOR & CONTRAST]
Luxurious bridal palette — soft whites, blush, gold, pearl — harmonized with {brand.color_field_palette}; the collection leads as the treasured centerpiece, props echoing the romantic luxury.

[LIGHT & LENS]
ONE soft luminous overhead light, gentle and romantic with delicate shadow. Full collection sharp.

[NATURAL PLACEMENT]
Each piece rests face-up with honest weight; silk drapes with real folds; florals lie with natural physics; a veil edge falls as tulle truly falls.

[COMPANION ELEMENTS]
COLLECTION EXCEPTION: the multi-product collection IS the hero. Bridal props (silk, white/blush florals, pearl, gold, a veil edge) are the curated supporting world — elegant, never crowding the collection's readability.

[SCENE]
Bridal beauty package, shot overhead. The premium collection (multiple coordinated products) arranged luxuriously among elegant bridal props. Romantic, gift-worthy, complete — dreamy luxury bridal mood. Choice points: collection arrangement, prop styling, gold-pearl balance, background warmth.

[SUBJECT]
The bridal collection as hero, elegant props supporting — full physical truth, romantic editorial intention.

[BRAND CONSTRAINTS]
The product collection hero with elegant bridal props. No human elements. Romantic luxury arrangement. No readable text on props. {brand.anti_attributes}

[OUTPUT]
Photoreal bridal flat-lay photography, maximum fidelity. Romantic luxury grade — soft whites, blush, gold. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — Saudi bridal can incorporate gold (significant in Saudi weddings), Taif roses, oud/bukhoor elements. {saudi.color_palette_adjust} warms toward Saudi-bridal gold.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: collection arrangement, prop styling and selection, gold-pearl balance, background warmth. A different dream of the same gift each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Collection (every piece, every label character), {product.material_texture}, bridal props, arrangement, overhead framing — all preserved.

[MOTION]
Primary — props: silk shifts gently, florals tremble softly as if from a breath of air, pearl/gold catches shifting light.
Secondary — light: soft romantic light breathes.
Tertiary — camera: imperceptible overhead push-in.

[WHAT STAYS STATIC]
Collection identities locked — every piece. Arrangement stable. Overhead angle constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle romantic-luxury pacing.

[OUTPUT]
Photoreal bridal flat-lay cinematography. Silent. No text overlay, no watermark.

---

## R01 · Apparel Flat Lay

**Family:** TF18 · Product Flat Lay | **Tier:** premium | **Sectors:** Fashion, Retail, Apparel | **Intent:** launch, grow | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** palette discipline, fashion-styled
**Color story:** Styled apparel laid out top-down with coordinated accessories — fabric texture and color as hero, accessories completing the look.
**Reference accounts:** @tiadress, @planb_boutique, @themodestbride | **Cultural Spec:** CS-01, CS-22

**WHEN TO USE:** Fashion apparel flat lay — the complete look laid out. Fashion, abaya brands, lookbooks; the outfit story at a glance.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} apparel identity — fabric, cut, color, detail. Identity DNA, preserved through the overhead angle: {product.identity_dna}
The garment's lay, fold language, and accessory styling are creative decisions; the garment reads brand-accurate in fabric, color, and detail. INTEGRATION: one soft overhead light reveals the fabric's true texture and ties garment and accessories into a single styled photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with fashion flat-lay grade, overhead. Material truth: {product.material_texture} — real fabric texture and weave, honest natural drape and fold as laid out, authentic accessory materials, true color. No plastic-perfect fabric, no impossibly-flat styling.

[SCALE CALIBRATION]
{product.dimensions} — the garment at true worn-size proportions; accessories (shoes, bag, jewelry) at honest real scale beside it. The look reads shoppable because the sizes are true.

[FRAMING & PROXIMITY]
The complete look fills the frame — garment generous and central, accessories close in the styling flow, negative space designed not vacant.

[COLOR & CONTRAST]
The garment's fabric color and texture are the hero — its true brand color; coordinated accessories echo a {brand.color_field_palette}-harmonized palette; clean negative space.

[LIGHT & LENS]
ONE soft even overhead light with gentle directional quality revealing fabric texture and drape. Full look sharp.

[NATURAL PLACEMENT]
The garment lies as real fabric lies — honest folds, natural sleeve placement, true drape weight; accessories rest with real contact.

[COMPANION ELEMENTS]
The coordinated accessories ARE the curated companions — derived from the look's world (shoes, bag, jewelry, scarf), completing never crowding.

[SCENE]
Apparel flat lay, shot overhead. The apparel piece (abaya, dress, garment) laid out and styled with coordinated accessories as a complete look on a clean designed background. Styled, aspirational, shoppable-at-a-glance. Choice points: lay and fold language, accessory selection, arrangement flow, background tone.

[SUBJECT]
The garment as hero, accessories telling the complete look — fabric texture, detail, and accessories in authentic truth.

[BRAND CONSTRAINTS]
The apparel garment hero with coordinated accessories. No human elements (flat lay, not worn). Clean background. Modest fashion styling where applicable (CS-01). No readable text on accessories. {brand.anti_attributes}

[OUTPUT]
Photoreal apparel flat-lay photography, maximum fidelity. Styled fashion grade, fabric-texture hero. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} — for abaya/modest fashion, styling reflects Saudi modest fashion conventions (CS-01); accessories appropriate to Saudi taste. {saudi.color_palette_adjust} tunes palette.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: lay and fold language, accessory mix, arrangement flow, background tone. The same garment styled into a new look each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Garment, {product.material_texture}, accessories, arrangement, overhead framing — all preserved. Brand elements locked.

[MOTION]
Primary — fabric: the garment shifts gently as if from a soft breath, drape settling subtly; accessory details catch shifting light.
Secondary — light: soft overhead light breathes.
Tertiary — camera: imperceptible overhead push-in.

[WHAT STAYS STATIC]
Garment identity locked — fabric, color, detail, material texture. Arrangement stable. Overhead angle constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Gentle fashion flat-lay pacing.

[OUTPUT]
Photoreal apparel flat-lay cinematography. Silent. No text overlay, no watermark.

---

## R04 · Collection Story Flat Lay — COLLECTION chain

**Family:** TF18 · Product Flat Lay | **Tier:** premium | **Sectors:** Retail, Fashion, Beauty, F&B | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** palette discipline, brand-world cohesive
**Color story:** A full product line as a narrative flat lay — the collection's shared color story told through coordinated arrangement. Complete, considered, brand-cohesive.
**Reference accounts:** @tiadress, @danatreasures, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Collection/range reveal — line launches, gift sets, brand-world storytelling. Shows the full range and how the pieces relate.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} collection identity. Identity DNA, preserved through the overhead angle: {product.identity_dna}
The narrative arrangement (by size, by use-order, by hero-to-supporting) is the creative decision; EVERY product reads brand-accurate, brand-readable faces up, the line shown as a cohesive family. Identity fidelity on each piece. INTEGRATION: one soft overhead light, consistent across the arrangement, makes the collection read as one photographed family.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with collection-editorial grade, overhead. Material truth: {product.material_texture} across the range — real materials, authentic surface variation, honest soft shadow, true coordinated color. No plastic-perfect lineup.

[SCALE CALIBRATION]
{product.dimensions} per piece — the line's true relative sizes ARE part of the story (travel size beside full size, hero beside supporting); honest proportions across the range.

[FRAMING & PROXIMITY]
The full line fills the frame in its narrative flow — complete and near, sequenced to be read, never scattered across emptiness.

[COLOR & CONTRAST]
The collection's shared color story from {brand.color_field_palette} told through coordinated arrangement — the brand-world palette as a cohesive family, hero pieces leading.

[LIGHT & LENS]
ONE soft even overhead light, consistent across the arrangement so the collection reads as a unified family. Full collection sharp.

[NATURAL PLACEMENT]
Each piece rests with honest weight and true contact in its narrative position.

[COMPANION ELEMENTS]
COLLECTION EXCEPTION: the line IS the hero. Subtle complementary props (if any) only tie the story — minimal, never competing with the range's readability.

[SCENE]
Collection story flat lay, shot overhead. The full product line in a considered narrative layout — grouped or sequenced to tell the collection's story — shared color story evident, clean designed background. Complete, cohesive, brand-world storytelling. Choice points: narrative logic (size/use/hero order), grouping geometry, prop presence, background tone.

[SUBJECT]
The full collection as hero, arranged to tell the line's story — each product and the cohesive arrangement in authentic truth.

[BRAND CONSTRAINTS]
The product collection from one line. Coordinated props minimal if any. No human elements. Clean background. One cohesive story. No readable text beyond the products' own labels. {brand.anti_attributes}

[OUTPUT]
Photoreal collection flat-lay photography, maximum fidelity. Cohesive brand-world grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns the collection palette to brand and Saudi-market taste. For occasion collections: themed arrangement.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: narrative logic, grouping geometry, prop presence, background tone. The same family, a new telling each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Collection (every piece, every label character), {product.material_texture}, arrangement, background, overhead framing — all preserved.

[MOTION]
Primary — light: soft overhead light shifts gently across the collection, highlights gliding over the coordinated pieces revealing the family relationship.
Secondary — props: any complementary element shifts subtly.
Tertiary — camera: imperceptible overhead push-in or slow reveal across the arrangement.

[WHAT STAYS STATIC]
Collection identities locked — every piece. Arrangement stable. Overhead angle constant. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Considered brand-story pacing.

[OUTPUT]
Photoreal collection flat-lay cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF19 · ON-MODEL APPAREL — 1 chain
**Drama dial: clean editorial / warm location-natural** · Human chain: SINGLE SUBJECT, modesty per CS-24/CS-01, single-motion video.

---

## R02 · Apparel On-Model

**Family:** TF19 · On-Model Apparel | **Tier:** premium | **Sectors:** Fashion, Retail, Apparel | **Intent:** launch, grow | **Frequency:** 2-3× per month | **Reference image:** Required (garment reference; model generated) | **Drama dial:** clean editorial (studio) / warm golden (location)
**Color story:** The garment color and fabric are the hero, worn and alive on a single model against a complementary editorial backdrop.
**Reference accounts:** @tiadress, @themodestbride, @planb_boutique | **Cultural Spec:** CS-01, CS-24, CS-22

**WHEN TO USE:** On-model apparel hero — fit, drape, and styling on-body. SINGLE SUBJECT. The key conversion content for fashion.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} garment identity — fabric, cut, color, detailing. Identity DNA, preserved across any camera angle: {product.identity_dna}
Pose, studio-vs-location setting, and crop are creative decisions; the garment reads brand-accurate in fabric, cut, color, and detail as worn — drape and fit true to the real piece. INTEGRATION: one light system models the model and the garment together — the key that flatters her face defines the fabric's folds; backdrop or location lives in the same light.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio or broadcast_cinematic with fashion-editorial grade. Material truth: the garment drapes with true fabric weight, honest fold dynamics, real fit on a real body, authentic fabric texture per its substrate. Real Saudi skin with authentic texture and warm undertone, natural confident expression. No plastic skin, no CGI-clean fabric.

[SCALE CALIBRATION]
True garment-on-body scale — the cut and length honest to the real piece on a real human frame; accessories at true proportion.

[FRAMING & PROXIMITY]
The model and garment command the frame — full-length or three-quarter, near enough that fabric texture and detailing read; the backdrop frames, never swallows.

[COLOR & CONTRAST]
The garment's color and fabric — its true brand color — are the hero chromatic statement, worn and alive; a complementary clean backdrop tuned toward {brand.color_field_palette} harmony supports; skin warm and true.

[LIGHT & LENS]
ONE editorial fashion light system — soft key with dimensional modeling (studio) or natural golden warmth (location) — flattering the garment's fabric and the model together. Model and garment sharp, backdrop soft.

[NATURAL PLACEMENT]
Her pose is a real body's pose — weight honestly carried, the garment falling and folding by true gravity, mid-gesture or composed.

[SCENE]
On-model editorial composition. A SINGLE Saudi model wears the garment in an editorial fashion shoot — studio (clean complementary backdrop) or location (modern Saudi setting). Fashion-editorial pose: confident, showing fit, drape, and styling to advantage. The garment is the hero, worn and alive. Choice points: pose, setting, crop, backdrop tone.

[SUBJECT]
ONE Saudi model only — never a group. Modesty register {brand.modesty_register} (CS-24): mainstream = styled hijab + the modest garment; modern = loose elegant scarf with front hair visible, fashion-forward; editorial = high-fashion modest styling. Warm honey-bronze skin, real texture, confident carriage. Modesty maintained.

[BRAND CONSTRAINTS]
SINGLE subject only — one model, never a group, no other people. Modesty per register (CS-01, CS-24). The garment and styling read authentic modern Saudi fashion, not Western generic or costume. No readable text in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal fashion-editorial photography, maximum fidelity. Garment-forward grade, true skin, confident styling. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills styling by region/register (CS-01, CS-24). {saudi.scene_context} fills location if location shoot (modern Saudi setting). {saudi.color_palette_adjust} tunes backdrop.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: pose, setting (studio vs location), crop, backdrop tone, styling details within register. The garment lives a new moment each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The model's appearance, modest styling, the worn garment, backdrop — all preserved character-perfect. Modesty maintained every frame.

[MOTION]
SINGLE primary motion only (validated for human content): ONE natural action — a slow confident turn showing the garment's drape, OR a gentle walk-in-place revealing the fit, OR a soft adjustment of the garment. The fabric moves naturally with the single action. NO complex multi-limb choreography.
Secondary: fabric drape and any scarf/hair (modern register) move naturally with the single motion, modesty preserved.

[WHAT STAYS STATIC]
Model's features, skin tone, modest styling, garment identity — locked. Modesty compliance absolute every frame including fabric motion. Backdrop stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Confident editorial pacing — one believable styled moment.

[OUTPUT]
Photoreal fashion-editorial cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF20 · PREMIUM FRAGRANCE & PACKAGING — 2 chains
**Drama dial:** R05 warm tungsten chiaroscuro (the flagship Saudi oud-luxury register) · F05 clean elevated appetizing

---

## R05 · Fragrance / Oud Showcase

**Family:** TF20 · Premium Fragrance & Packaging | **Tier:** luxury | **Sectors:** Fragrance, Oud, Perfume, Luxury Retail | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Required | **Drama dial:** warm tungsten chiaroscuro
**Color story:** Deep luxury staging — rich oud-warm tones, gold accents, dark opulent surround, the bottle as the glowing jewel. The Saudi oud-market luxury palette: amber, gold, deep brown.
**Reference accounts:** @alyafie_jewelry, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-19, CS-22

**WHEN TO USE:** Premium fragrance/oud hero — the single most important chain for the lucrative Saudi fragrance/oud sector. Opulence, sophistication, the prestige of fine fragrance.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} fragrance bottle identity — form, glass, cap, label, signature details. Identity DNA, preserved across any camera angle: {product.identity_dna}
Staging surface, oud-context styling, and camera height are creative decisions; the bottle reads brand-accurate — true glass form, cap, label characters (Latin AND Arabic character-perfect — Arabic wordmark fidelity is the highest-risk identity element), brand color, brand-readable face toward camera. INTEGRATION: one warm key holds bottle, staging, and atmosphere — its refraction through the glass, its gleam on the gold, its glow in any bukhoor wisp are a single luxury light system.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — opulent fragrance cinema, subtle warm grain. Material truth: {product.material_texture} — real glass refraction, honest reflectance, true liquid color within; authentic cap material (metal/weighted); real texture on luxury surfaces. No plastic-perfect glass, no artificial sparkle.

[SCALE CALIBRATION]
{product.dimensions} — true bottle size on real staging anchors: oud chips at honest centimeter scale, a brass burner at true vessel size, the gold tray proportioned to the bottle it presents.

[FRAMING & PROXIMITY]
Close and reverent — the glowing bottle commanding the frame, the oud-luxury world pressing warm and near, deep dark beyond.

[COLOR & CONTRAST]
Saudi oud-luxury palette — amber, gold, deep brown warmth; the bottle's brand color from {brand.color_field_palette} and the liquid's true hue glow as the treasured hero against the deep opulent surround.

[LIGHT & LENS]
ONE warm directional luxury key modeling the bottle and catching glass refraction, a warm rim within the same system for separation, deep falloff into opulent dark. Bottle sharp, staging soft, background deep.

[NATURAL PLACEMENT]
The bottle stands plumb on its rich surface (dark marble, polished wood, gold tray) — true weighted contact, real mirror-kiss on a polished surface.

[COMPANION ELEMENTS]
ONE hero companion from {product.companion_elements} (oud wood chips OR a brass incense burner with a bukhoor wisp OR a gold accent) — authentic Saudi fragrance signifiers (CS-19), restrained, never crowding the jewel.

[SCENE]
Premium fragrance showcase. The bottle as glowing hero in deep luxury staging — a rich surface, warm directional light, the chosen oud-context companion, deep luxurious surround falling to opulent dark. Sophisticated, prestigious, the luxury of fine fragrance and oud. Choice points: surface, companion selection, camera height, warm-dark depth.

[SUBJECT]
The fragrance bottle as luxury hero — glass refraction, true liquid color, cap material, staging in full physical truth.

[BRAND CONSTRAINTS]
Single fragrance bottle hero. Authentic Saudi luxury staging (CS-19). No human elements. Deep opulent surround. No readable text beyond the bottle's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal luxury fragrance photography, maximum fidelity. Opulent warm grade, glowing bottle hero, true liquid color. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — oud/bukhoor staging is core to the Saudi fragrance market (CS-19): oud chips, brass burner, gold elements. {saudi.material_context} fills authentic luxury surfaces. For Eid: gold particle haze in the warm air.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: staging surface, companion selection, camera height, warm-dark depth, refraction emphasis. The jewel is presented anew each time; its identity never wavers.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The bottle, every label character (Arabic wordmark verified), {product.material_texture}, glass refraction, liquid color, luxury staging, warm light — all locked.

[MOTION]
Primary — the bottle: extremely slow rotation (~15°) catching shifting glass refraction and warm highlights, brand face staying toward camera; OR a slow warm light bloom revealing the bottle.
Secondary — atmosphere: if bukhoor/oud present, a soft smoke wisp curls warmly; gold particles drift faintly.

[WHAT STAYS STATIC]
Bottle identity locked — glass, cap, labels, liquid color, material texture. Luxury staging stable. Warm temperature. Capture character: film_grain_warmth preserved.

[PACING & DURATION]
6 seconds. Continuous single take. Slow opulent fragrance pacing.

[OUTPUT]
Photoreal luxury fragrance cinematography. Silent. No text overlay, no watermark.

---

## F05 · Cloud Kitchen Packaging

**Family:** TF20 · Premium Fragrance & Packaging | **Tier:** premium | **Sectors:** F&B, Cloud Kitchen, Delivery, Restaurant | **Intent:** launch, grow, harvest | **Frequency:** 2-3× per month | **Reference image:** Required | **Drama dial:** clean elevated appetizing
**Color story:** Premium F&B packaging hero — clean appetizing staging making delivery/takeaway packaging look craveable. Brand-led packaging palette.
**Reference accounts:** @aseeb.najd, @laylali_riyadh, @diplomat_sweets | **Cultural Spec:** CS-22

**WHEN TO USE:** Premium F&B packaging hero — the delivery-era essential. Cloud kitchens, delivery brands, packaged F&B; the packaging IS the brand touchpoint.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} packaging identity — box/cup/bag form, branding, colors, label. Identity DNA, preserved across any camera angle: {product.identity_dna}
Staging, food-hint styling, and camera angle are creative decisions; the packaging reads brand-accurate — true form, branding, label characters (Arabic branding character-perfect), brand colors, brand-readable face toward camera. INTEGRATION: one warm commercial light holds packaging, surface, and any food hint in a single appetizing photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with premium packaging-commercial grade. Material truth: {product.material_texture} — real packaging substrate (kraft paper, coated card, cup texture) with honest surface and print character, true reflectance, real soft shadow. No plastic-perfect box.

[SCALE CALIBRATION]
{product.dimensions} — true delivery-packaging size; any food hint or prop at honest scale beside it; real takeaway proportions.

[FRAMING & PROXIMITY]
The packaging commands the frame at craveable closeness — hero-product respect for a delivery box, near and elevated.

[COLOR & CONTRAST]
Brand-led packaging palette — the packaging's brand color from {brand.color_field_palette} leading, warm appetizing support, clean modern surface; the packaging punches as the craveable branded hero.

[LIGHT & LENS]
ONE clean warm commercial light, appetizing and elevated with controlled soft shadow. Packaging sharp.

[NATURAL PLACEMENT]
The packaging sits with honest weight and true contact — a kraft box square on the surface, a cup with real base shadow, a bag with natural slump.

[COMPANION ELEMENTS]
ONE hero companion maximum: a subtle hint of the food (a glimpse inside, a garnish detail) OR one complementary brand prop — never crowding the branded hero.

[SCENE]
Premium packaging showcase. The branded F&B packaging as hero with elevated staging — clean modern surface, warm appetizing light, the one chosen hint. Elevated, branded, appetizing — the delivery-era brand moment. Choice points: staging surface, food-hint vs prop, camera angle, packaging pose.

[SUBJECT]
The branded packaging as hero — material, branding, and any subtle food hint in appetizing authentic truth.

[BRAND CONSTRAINTS]
Single branded packaging hero. Subtle food hint or one brand prop only. No human elements. No pork, no alcohol. No readable text beyond the packaging's own branding. {brand.anti_attributes}

[OUTPUT]
Photoreal premium packaging photography, maximum fidelity. Elevated appetizing grade, brand-color packaging hero. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} — staging reflects Saudi F&B branding aesthetics. Arabic branding on packaging rendered accurately (verify wordmark fidelity). {saudi.color_palette_adjust} aligns to brand.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: staging surface, food-hint vs prop, camera angle, packaging pose. The delivery moment elevates differently each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The packaging, every label/branding character, {product.material_texture}, staging, lighting — all preserved.

[MOTION]
Primary — the packaging: a slow subtle rotation (~12°) showing the branding, OR a gentle reveal of a food hint (lid lifting slightly, steam escaping). Brand face stays toward camera.
Secondary — atmosphere: if hot food, a warm steam wisp; appetizing glisten on any visible food.

[WHAT STAYS STATIC]
Packaging identity locked — form, branding, colors, material texture. Staging stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Elevated appetizing pacing.

[OUTPUT]
Photoreal premium packaging cinematography. Silent. No text overlay, no watermark.

---
---

# FAMILY TF21 · SERVICE CTA — 2 chains · TEXT-CENTRAL
**Drama dial: clean conversion-designed** · TEXT is a CORE block; Arabic overlay-node dependency applies.

---

## B04 · Booking CTA

**Family:** TF21 · Service CTA | **Tier:** universal | **Sectors:** Services, Salon, Beauty, Hospitality, Healthcare | **Intent:** harvest | **Frequency:** 2-3× per month | **Reference image:** Recommended | **Drama dial:** clean inviting conversion
**Color story:** Clean inviting service palette with a clear appointment/booking visual and strong CTA. Trustworthy, clear, action-driving.
**Reference accounts:** @danatreasures, @tiadress | **Cultural Spec:** CS-22

**WHEN TO USE:** Service booking conversion — appointment-slot visual driving bookings. Salons, clinics, services, hospitality. TEXT/CTA central.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} service identity. Identity DNA: {product.identity_dna}
The service visual (result, welcoming space, or representative product) and CTA layout are creative decisions; the brand context is accurate, composed with the booking CTA. INTEGRATION: one clean inviting light grades visual and CTA graphics together — one designed conversion photograph.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with inviting service-commercial grade. Material truth: {product.material_texture} where a product appears; authentic service-context material, honest light, real soft shadow. CTA graphics clean and clear. No CGI flatness.

[SCALE CALIBRATION]
{product.dimensions} where applicable — service visual at honest scale; the appointment-slot graphic proportioned as a designed UI cue, legible at feed size.

[FRAMING & PROXIMITY]
A tight conversion layout — inviting visual near, the booking CTA unmissable; designed for the tap.

[COLOR & CONTRAST]
Clean inviting service palette — trustworthy brand tones from {brand.color_field_palette}, a clear appointment-slot cue, and a strong CTA accent within the brand's own range.

[LIGHT & LENS]
ONE clean inviting commercial light, trustworthy and warm with gentle shadow. Full composition sharp.

[NATURAL PLACEMENT]
The service visual sits with honest physics; CTA graphics composed as designed layout elements.

[SCENE — TEXT CENTRAL]
Booking CTA composition. A clean inviting service visual composed with a clear appointment/booking cue — a calendar/slot graphic, available times, a strong booking call-to-action. Inviting visual, unmissable CTA. Choice points: service visual selection, slot-graphic style, CTA placement.

[SUBJECT]
The service context visual plus the booking CTA graphics — one conversion-designed layout.

[TEXT — CORE BLOCK for this family]
Render the booking CTA typography directly:
- CTA: "{brief.text_request.copy}" — e.g. "Book now", available slots, appointment prompt
- Style: {brief.text_request.style} — default clean inviting CTA type with appointment-slot graphic
- Placement: unmissable booking call-to-action with appointment cue
- ARABIC RULE: Arabic/bilingual CTA at shortest viable copy; until the deterministic overlay node ships, Arabic-heavy CTAs route to post-production typography
The booking CTA IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Service visual plus booking CTA. No fabricated availability beyond brief. If human present: single-subject, modest (CS-24). No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal service-CTA composition with integrated typography, maximum fidelity. Clean inviting grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns to brand. Arabic/bilingual booking CTA per the Arabic rule.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: service visual, slot-graphic style, CTA placement, palette balance within brand range. The invitation re-designs; the offer never changes.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Service visual, booking CTA (every character), appointment cue, layout — all preserved.

[MOTION]
Primary — CTA: the booking call-to-action and appointment-slot graphic animate in invitingly — a settle, a gentle pulse drawing the tap.
Secondary — service visual: subtle warmth/highlight drift.
Tertiary — camera: subtle push-in toward the CTA.

[WHAT STAYS STATIC]
Service context locked. CTA content locked. Layout stable. Capture character preserved.

[PACING & DURATION]
4 seconds. Continuous single take. Inviting conversion pacing.

[OUTPUT]
Photoreal service-CTA motion-graphic. Silent. No watermark.

---

## U06 · New Arrival / Launch

**Family:** TF21 · Service CTA | **Tier:** universal | **Sectors:** Retail, Beauty, F&B, Fashion, Services | **Intent:** launch | **Frequency:** per launch | **Reference image:** Required | **Drama dial:** dramatic launch-reveal
**Color story:** Anticipation-and-reveal palette — the product hero with 'new' announcement energy, dramatic reveal lighting, bold launch typography.
**Reference accounts:** @danatreasures, @tiadress, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** New product launch announcement — the go-to launch-day chain, cross-sector. TEXT/announcement central; builds launch excitement.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Reveal staging and announcement layout are creative decisions; the product reads brand-accurate, brand-readable face toward camera, composed with launch energy. INTEGRATION: one dramatic reveal light stages product and typography as a single launch moment — the unveiling light IS the design.

[REALISM & CAPTURE CHARACTER]
Capture character: {brand.aesthetic.capture_character} — default clean_studio with dramatic launch-reveal grade. Material truth: {product.material_texture} — authentic product substrate, honest reveal lighting, real reflectance. Launch graphics bold and clean. No plastic perfection.

[SCALE CALIBRATION]
{product.dimensions} — the product at true size; launch typography scaled as a bold announcement without dwarfing the hero.

[FRAMING & PROXIMITY]
Tight on the unveiling — product hero large in the reveal light, the launch message unmissable beside it.

[COLOR & CONTRAST]
Launch-excitement palette — the brand color hero from {brand.color_field_palette} in reveal light, bold launch-typography contrast within the brand range. Fresh, attention-commanding.

[LIGHT & LENS]
ONE dramatic reveal light — directional with unveiling drama, bright highlight on the product, controlled anticipation shadow. Product sharp.

[NATURAL PLACEMENT]
The product stands or rests with honest gravity at the center of its reveal.

[SCENE — TEXT CENTRAL]
New arrival launch composition. The product presented with reveal-and-anticipation energy — dramatic launch lighting, a sense of unveiling, bold 'new arrival' announcement typography. Attention-commanding freshness. Choice points: reveal staging, announcement layout, shadow drama, field tone.

[SUBJECT]
The product hero with launch reveal energy plus the announcement typography — one exciting launch layout.

[TEXT — CORE BLOCK for this family]
Render the launch announcement typography directly:
- Announcement: "{brief.text_request.copy}" — e.g. "New Arrival", "Now Available", launch name
- Style: {brief.text_request.style} — default bold exciting launch type
- Placement: composed with the product as the launch message
- ARABIC RULE: Arabic/bilingual announcement at shortest viable copy (e.g. جديد); until the overlay node ships, Arabic-heavy announcements route to post-production typography
The launch announcement IS the message — essential to this chain.

[BRAND CONSTRAINTS]
Single product launch hero with announcement graphics. No human elements. No other readable text. {brand.anti_attributes}

[OUTPUT]
Photoreal launch composition with integrated typography, maximum fidelity. Exciting reveal grade. No watermark.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} aligns to brand. Arabic launch typography per the Arabic rule. For occasion launches: themed.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: reveal staging, announcement layout, shadow drama, field tone within brand range. Every launch feels like the first; the message never changes.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Product, {product.material_texture}, launch typography (every character), reveal lighting, layout — all preserved.

[MOTION]
Primary — reveal: the product emerges into reveal light (light bloom, or a subtle rise), the announcement typography landing with launch energy.
Secondary — product: subtle highlight drift.
Tertiary — camera: dramatic push-in to the product reveal.

[WHAT STAYS STATIC]
Product identity locked. Announcement content locked. Layout stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Building launch-reveal pacing.

[OUTPUT]
Photoreal launch motion-reveal. Silent. No watermark.

---
---

# BATCH 4 · AGENT RUNTIME NOTES

**Block inclusion:** [TEXT] CORE on B04 and U06 (Arabic rule embedded); conditional elsewhere. [COMPANION ELEMENTS] curated-arrangement logic on B03/R01 (props derived, support never crowd), COLLECTION EXCEPTIONS on B05/R04 (the multi-product collection IS the hero — identity fidelity required on EVERY piece, verification bar raised not lowered), one-hero on R05 (oud signifier) and F05 (food hint).

**Human-chain rules:** R02 single subject, modesty register per CS-24/CS-01 absolute including fabric motion, single-primary-motion video, camera steady.

**Arabic wordmark fidelity:** R05 and F05 carry explicit Arabic label/branding verification language — fragrance bottles and F&B packaging are the two highest-exposure surfaces for Arabic identity drift.

**Drama dial:** TF18 palette discipline (curated overhead) · TF19 clean editorial / warm location · TF20 R05 warm tungsten chiaroscuro (flagship oud register), F05 clean elevated · TF21 clean conversion / dramatic launch-reveal.

**Failure-ledger compliance:** all 9 chains carry the 15-block order, the four v3.7 fields, brand-derived color, proportion anchoring, framing-proximity, integration, companion logic, no-readable-background-text, conditional/core text logic, and the CREATIVE VARIANCE DIRECTIVE. No fixed mm / f-stop / Kelvin commands anywhere.

*OpenClaw · Master Prompt Library v3.7 · Batch 4 · TF18 + TF19 + TF20 + TF21 · 9 chains · Confidential*

<!-- ══════════ OpenClaw_v3_7_Batch5_TF22_TF23.md ══════════ -->

# FAMILY TF22 · VIDEO (NATIVE) — 5 chains · text-to-video
**Drama dial: per-chain registers** (V01 warm reverent · V02 clean honest · V03 bright satisfying · V04 occasion grandeur + native audio · V05 cinematic anticipation-to-glory)

---

## V01 · Ramadan Atmosphere Clip — NATIVE t2v

**Family:** TF22 · Video (Native) | **Tier:** premium | **Sectors:** F&B, Retail, Hospitality, Services | **Intent:** grow | **Frequency:** Ramadan-triggered | **Reference image:** Optional (brand element to integrate) | **Drama dial:** warm reverent (occasion register)
**Color story:** Warm Ramadan night — lantern glow, deep night-blue and gold, dates and iftar-prep warmth. Spiritual-festive serenity.
**Reference accounts:** @aseeb.najd, @diplomat_sweets, @laylali_riyadh | **Cultural Spec:** CS-08, CS-13, CS-19, CS-21

**WHEN TO USE:** Ramadan atmosphere native video — the serene moment before breaking fast. Auto-triggers during Ramadan.

### ► Native video prompt (text-to-video)

[BRAND LOCK — when a brand element is provided]
{product.identity_dna} — if a brand element is provided (a branded dish, beverage, or product), it integrates naturally among the iftar elements with {product.material_texture} truth, brand-readable where the gentle framing allows, never staged above the occasion.

[REALISM & CAPTURE CHARACTER]
Capture character: film_grain_warmth — Ramadan evening cinema, subtle warm grain. Material truth throughout: real fanoos metal and glass, honest dates with natural variation, true brass dallah patina, authentic steam physics. No plastic festive props, no CGI glow.

[SCENE]
A warm atmospheric Ramadan evening. The scene moves gently through Ramadan signifiers: a glowing fanoos casting warm amber light, a beautifully arranged plate of dates, iftar preparation in a warm Saudi home or restaurant setting (CS-13), the serene moment before breaking fast. Everything at honest real-world scale — the lantern, the dates plate, the dallah in true proportion to each other.

[MOTION]
Single coherent gentle arc: lantern light flickers warmly; a hand (single, modest sleeve, right-hand per CS-08) may arrange dates or pour Arabic coffee from a dallah; soft steam rises; warm air shimmer. ONE gentle motion at a time — never busy. Unhurried, serene, reverent.

[COLOR & CONTRAST]
The Ramadan occasion palette leads (deep night-blue, amber lantern gold); any brand element's color from {brand.color_field_palette} integrates respectfully within it. One warm light source — the lantern glow — governs the scene.

[STYLE & PACING]
Cinematic warm Ramadan atmosphere. Slow, contemplative, reverent. 6–8 seconds. Spiritual-festive serenity.

[CULTURAL — CENTRAL]
Authentic Saudi Ramadan (CS-13, CS-19, CS-21) — dates, fanoos, dallah, iftar elements true to Saudi tradition, never generic-Arabian. No pork, no alcohol. Reverent treatment. {saudi.occasion_overlay} = Ramadan drives the scene.

[OUTPUT]
Photoreal native Ramadan atmosphere video, maximum fidelity. Warm reverent grade. Silent. No text overlay, no watermark.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: which signifier leads (lantern, dates, dallah pour), camera path, scene depth, glow warmth. A different serene minute of the same evening.

---

## V02 · Before/After Transition Video — NATIVE t2v · ELEVATED COMPLIANCE

**Family:** TF22 · Video (Native) | **Tier:** premium | **Sectors:** Beauty, Skincare, Salon, Aesthetic Services | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference image:** Optional | **Drama dial:** clean honest clinical
**Color story:** Clean clinical-aspirational palette, consistent honest lighting across the transition. Trustworthy transformation.
**Reference accounts:** @danatreasures, @tiadress | **Cultural Spec:** CS-24

**WHEN TO USE:** Native before/after transition for beauty services. ELEVATED COMPLIANCE — single subject, treatment area only, strictly modest.

### ► Native video prompt (text-to-video)

[BRAND LOCK — when a brand element is provided]
{product.identity_dna} — if the service product appears, it renders accurately with {product.material_texture} truth within the clean clinical frame.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio, honest clinical-aspirational grade. Material truth of skin: real authentic texture in BOTH states — the after is improved, never airbrushed to fantasy. No CGI-smooth fake result, no impossible transformation.

[SCENE — ELEVATED COMPLIANCE]
A beauty/skincare/salon before-and-after as a smooth native transition. The SAME treatment area transforms from before to after — identical angle, identical honest lighting across both states so the comparison is physically fair; the only variable is the result. ELEVATED COMPLIANCE: single subject, strictly modest framing, treatment area only (facial skin within modest hijab framing, hair within register, nails, or the specific zone), never objectifying, fully Saudi-modest (CS-24). Clean neutral background, true anatomical scale held constant across the transition.

[MOTION]
ONE smooth transition from before to after — a clean morph, wipe, or dissolve revealing the honest improvement. One clear transition motion only. Modesty maintained absolutely in every frame.

[COLOR & CONTRAST]
Clean neutral palette, true skin tones, identical white balance across both states. The result reads through clarity, not color drama.

[STYLE & PACING]
Clean clinical-aspirational. Smooth, satisfying, trustworthy. 4–5 seconds. Credible transformation.

[COMPLIANCE — CENTRAL]
SINGLE subject, ELEVATED modest framing (CS-24). Treatment area only. Honest achievable result, no deceptive transformation. Fully Saudi-modest every frame.

[OUTPUT]
Photoreal native before/after transition video, maximum fidelity. Clean honest grade. Silent. No text overlay, no watermark.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: transition style (morph/wipe/dissolve), crop within compliance, background tone. The honesty rules never vary.

---

## V03 · Product Unboxing Loop — NATIVE t2v

**Family:** TF22 · Video (Native) | **Tier:** premium | **Sectors:** Retail, Beauty, F&B, Tech, Fashion | **Intent:** launch, grow | **Frequency:** 1-2× per month | **Reference image:** Optional (product to feature) | **Drama dial:** bright satisfying (ASMR-clean)
**Color story:** Clean satisfying unboxing — bright even light, the product revealed from beautiful packaging, true product color emerging.
**Reference accounts:** @danatreasures, @tiadress, @planb_boutique | **Cultural Spec:** CS-01, CS-08

**WHEN TO USE:** Satisfying unboxing loop — the hands-and-product reveal that drives social engagement. Loop-friendly.

### ► Native video prompt (text-to-video)

[BRAND LOCK — when a product is provided]
{product.identity_dna} — the featured product is revealed brand-accurate, brand-readable face emerging toward camera, true brand color; {product.material_texture} governs both packaging substrate and product surface.

[REALISM & CAPTURE CHARACTER]
Capture character: clean_studio with ASMR-satisfying clarity. Material truth: crisp real packaging (card flexes, tissue rustles, lid lifts with honest weight), real Saudi hands with authentic skin texture and warm undertone, true product reflectance. No CGI-clean perfection.

[SCENE]
A satisfying product unboxing loop. Beautiful branded packaging opens to reveal the product on a clean bright surface — packaging and product as heroes at true real-world scale to the hands and to each other ({product.dimensions}). The reveal is the satisfying payoff. Modern, crisp, social-native. No faces — hands and product only.

[MOTION]
ONE coherent unboxing action: hands (single person, hands/forearms only, right-hand per CS-08, modest sleeve per CS-01) open the packaging and reveal the product in one smooth satisfying motion — lid lifting, product emerging, a gentle turn to show it. Designed to loop seamlessly. One clear unhurried motion.

[COLOR & CONTRAST]
Bright clean field; the product's true brand color from {brand.color_field_palette} emerges as the chromatic payoff of the reveal. One bright even light system.

[STYLE & PACING]
Clean satisfying ASMR-style unboxing. Tactile, crisp. 5–6 seconds, loop-friendly. The satisfying reveal moment.

[CONSTRAINTS]
Single product revealed. Hands: single person, hands/forearms only, right-hand (CS-08), modest sleeve (CS-01). Brand-readable face revealed toward camera. True product color. No readable text beyond the brand's own packaging.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills the sleeve register. {saudi.scene_context} can localize the surface/setting.

[OUTPUT]
Photoreal native unboxing loop, maximum fidelity. Clean satisfying grade. Silent. No text overlay, no watermark.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: packaging-opening choreography, reveal angle, surface tone, the product's emerging turn. A fresh satisfying reveal each loop.

---

## V04 · Occasion Announcement Video — NATIVE t2v · NATIVE AUDIO

**Family:** TF22 · Video (Native) | **Tier:** luxury | **Sectors:** Retail, F&B, Corporate, Hospitality, Services | **Intent:** grow | **Frequency:** occasion-triggered | **Reference image:** Optional (brand element) | **Drama dial:** occasion grandeur (occasion palette leads)
**Color story:** Premium occasion-themed with NATIVE AUDIO — National Day green-white pride, Founding Day heritage, or Eid celebration grandeur.
**Reference accounts:** @aseeb.najd, @danatreasures, @diplomat_sweets | **Cultural Spec:** CS-13, occasion overlay fields | **Note:** Seedance native-audio workflow; keep prompt within the 2,000-char audio-workflow ceiling.

**WHEN TO USE:** Premium occasion announcement with audio — major Saudi occasions. Cinematic, dignified, emotionally resonant.

### ► Native video prompt (text-to-video · native audio)

[BRAND LOCK — when a brand element is provided]
{product.identity_dna} — the brand integrates respectfully into the occasion's cinematic world, {product.material_texture} true, never crassly commercial over the occasion's dignity.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic with occasion grandeur. Material truth: real flags and banners with honest fabric physics, true heritage materials (Diriyah mudbrick, Najdi detail), authentic festive elements. No kitsch, no plastic props.

[SCENE — OCCASION CENTRAL]
A premium occasion announcement for a major Saudi occasion, filled by {saudi.occasion_overlay}: National Day (Sep 23) — modern Saudi pride, green and white, flags, modern Riyadh + heritage blend; Founding Day (Feb 22) — Najdi cultural depth, Diriyah, the 1727 founding spirit; Eid Al-Fitr / Al-Adha — warm gold, jewel tones, gathering, generosity, joy. The brand integrates respectfully (CS-13). Dignified, premium, emotionally resonant.

[MOTION]
One coherent emotional build: flags or banners stirring with pride, lantern/festive elements glowing, heritage or modern Saudi imagery flowing gently, building to the brand's respectful occasion greeting. Dignified, never busy.

[COLOR & CONTRAST]
The occasion palette leads (the documented inversion): Saudi green-white-gold, heritage earth, or Eid gold-jewel; the brand color from {brand.color_field_palette} follows respectfully within it.

[AUDIO — NATIVE]
A native audio bed matching the occasion's emotion: dignified ambient or subtle original instrumental swell for National/Founding Day (no copyrighted music); warm celebratory ambient tones for Eid. Dignified, occasion-appropriate.

[STYLE & PACING]
Cinematic premium occasion grandeur. Dignified emotional pacing. 6–10 seconds.

[CULTURAL — CENTRAL]
Authentic Saudi occasion (CS-13). {saudi.occasion_overlay} drives the entire piece. Religious occasions with reverence; national occasions with pride.

[OUTPUT]
Photoreal native occasion announcement with native audio, maximum fidelity. Occasion-themed grade. No text overlay unless the brief requests occasion greeting typography (shortest Arabic form; post-production preferred until the overlay node ships). No watermark.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: imagery sequence, motion build, scene depth, audio mood within the occasion's register. The same pride, freshly told.

---

## V05 · New Arrival Reveal Video — NATIVE t2v

**Family:** TF22 · Video (Native) | **Tier:** premium | **Sectors:** Retail, Beauty, F&B, Fashion, Tech | **Intent:** launch | **Frequency:** per launch | **Reference image:** Optional (product to reveal) | **Drama dial:** cinematic anticipation-to-glory
**Color story:** Building from dark/mysterious to the product emerging in hero light — shadow and anticipation resolving into full brand-color glory.
**Reference accounts:** @danatreasures, @tiadress, @planb_boutique | **Cultural Spec:** CS-22

**WHEN TO USE:** Cinematic launch reveal — anticipation → reveal → product glory. The launch-day native-video companion to U06.

### ► Native video prompt (text-to-video)

[BRAND LOCK — when a product is provided]
{product.identity_dna} — the revealed hero renders brand-accurate, brand-readable face resolving toward camera in the reveal, {product.material_texture} true under the emerging hero light.

[REALISM & CAPTURE CHARACTER]
Capture character: broadcast_cinematic launch grade. Material truth: the product's substrate behaves honestly as light finds it (glass catching the bloom, film creasing true, metal edging crisp). No CGI-clean emergence.

[SCENE]
A cinematic new-product launch reveal. The sequence builds anticipation — beginning in shadow, mystery, or abstract brand-world atmosphere — then resolves to the product emerging into hero light in full glory at honest real-world scale. The arc: anticipation → reveal → product glory. Cinematic, exciting, climactic.

[MOTION]
ONE building motion arc: the camera moves through anticipation (drifting through shadow, light, or brand-atmosphere) toward the product, which emerges into hero light — a light bloom, a turn into illumination, or a rise into frame. The reveal is the climactic payoff, resolving on the brand-readable face. One coherent unhurried build.

[COLOR & CONTRAST]
Dark anticipation field resolving into the product's true brand color from {brand.color_field_palette} at full saturation — the chromatic arrival IS the climax. One hero light system emerging from the dark.

[STYLE & PACING]
Cinematic launch-reveal. Building anticipation resolving to climactic reveal. 6–8 seconds.

[CONSTRAINTS]
Single product revealed as hero. True brand color emerging in full saturation. No human elements. No readable text beyond the product's own label.

[SAUDI ADAPTATION — conditional]
{saudi.color_palette_adjust} can tune the anticipation atmosphere; for occasion launches the reveal world themes accordingly.

[OUTPUT]
Photoreal native launch reveal, maximum fidelity. Cinematic anticipation-to-glory grade. Silent (brief may add audio). No text overlay unless the brief requests launch typography. No watermark.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: anticipation world (shadow/light/abstract brand atmosphere), camera path, reveal mechanism (bloom/turn/rise), climax framing. Every launch arrives differently; the hero never changes.

---
---

# FAMILY TF23 · SAUDI UGC AUTHENTIC — 10 chains
**Drama dial: authentic phone-natural** (S10 golden heritage variant) · The UGC authenticity IS the value — phone_natural capture character is identity-tier on this family.
**Risk tiers binding:** S04 SAFEST · S01/S02/S06/S08/S10 RELIABLE · S05 COMPLIANCE-SENSITIVE · S09 MODERATE (two subjects) · S03/S07 HIGH RISK (multi-subject).

---

## S01 · Saudi Woman Lifestyle — Coffee Moment

**Tier:** universal | **Sectors:** F&B, Beauty, Retail, Lifestyle | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference:** Optional (product; subject generated) | **Risk:** RELIABLE (single subject) | **Drama dial:** authentic phone-natural
**Color story:** Authentic phone-camera warmth — natural daylight, real café/home tones, the product naturally present. Candid lived-in palette.
**Reference accounts:** @barnscoffee, @cafe.najd, @tiadress | **Cultural Spec:** CS-24, CS-01, CS-22

**WHEN TO USE:** Authentic single-woman UGC — relatable everyday "real person enjoying this" content. SINGLE SUBJECT, reliable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA, preserved across any camera angle: {product.identity_dna}
Her pose, the setting, and the candid framing are creative decisions; the product is naturally present (held or on the table beside her), brand-readable where the candid framing allows, never feeling staged. INTEGRATION: the setting's natural daylight is the only light — her skin, the product, and the café/home world share its honest warmth and one shadow direction.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural — authentic UGC, as if shot on a real phone by a friend. Material truth: {product.material_texture} — the product caught with true reflectance; real skin with authentic texture and warm Saudi undertone; honest natural daylight; true candid mid-moment expression. The UGC authenticity IS the point. No glossy over-production, no plastic skin, no staged-perfect composition.

[SCALE CALIBRATION]
{product.dimensions} — the product at true hand/table scale; an honest takeaway cup or beauty item in a real human moment.

[FRAMING & PROXIMITY]
Friend-distance candid framing — she and the product near and present, the setting breathing softly behind; slightly imperfect phone framing is part of the truth.

[COLOR & CONTRAST]
Authentic-but-alive: real café/home tones; the product's color from {brand.color_field_palette} sitting naturally and truthfully in the moment; warm true skin. Candid lived-in palette, never hyper-produced.

[LIGHT & LENS]
ONE truth: natural available daylight — soft window or pleasant outdoor light, honest and slightly imperfect like real phone capture. Phone-natural perspective, moderate authentic depth.

[NATURAL PLACEMENT]
She sits as a person actually sits — relaxed weight, the product held or set down exactly where a hand would leave it.

[COMPANION ELEMENTS]
The candid setting carries the context — no staged props; at most one honest element of the real moment.

[SCENE]
Authentic coffee-moment composition. A SINGLE Saudi woman seated casually — café, home, or a pleasant everyday spot — with the brand product naturally part of the moment. Relaxed, candid, mid-enjoyment; the kind of shot a friend would take. Choice points: setting, pose, product placement, candid angle.

[SUBJECT]
ONE Saudi woman only. Modesty register {brand.modesty_register} (CS-24): mainstream = styled hijab + modest abaya; modern = loose elegant scarf with front hair visible, contemporary casual; editorial = fashion-forward. Warm honey-bronze skin, real texture, relaxed candid expression. Modesty maintained.

[BRAND CONSTRAINTS]
SINGLE subject — one woman only, never a group, no other people. Product naturally present, not staged-perfect. Modesty maintained (CS-01, CS-24). Authentic Saudi setting (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic UGC photography (phone-camera aesthetic), maximum fidelity. Honest natural grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the authentic café/home (CS-13). {saudi.apparel_context} fills modest styling by register (CS-01, CS-24).

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: setting, pose, candid angle, product placement, light warmth. A different real moment each time; her identity rules never vary.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Her appearance, modest styling, the product, {product.material_texture}, the candid setting — all preserved. Modesty maintained every frame.

[MOTION]
SINGLE primary motion only: ONE natural candid action — she lifts the coffee for a slow sip, OR a soft natural smile forms, OR she glances warmly toward the product. The rest stays relaxed. NO complex motion.
Secondary: gentle ambient life (scarf/hair shifts naturally, soft background motion).

[WHAT STAYS STATIC]
Facial features, skin tone, modest styling, product identity and material texture — locked. Modesty compliance every frame. Setting stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Relaxed candid UGC pacing — one real moment.

[OUTPUT]
Photoreal authentic UGC cinematography. Silent. No text overlay, no watermark.

---

## S02 · Saudi Man Lifestyle — Thobe Casual Moment

**Tier:** universal | **Sectors:** F&B, Retail, Grooming, Lifestyle | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference:** Optional | **Risk:** RELIABLE (single subject) | **Drama dial:** authentic phone-natural
**Color story:** Authentic phone daylight — crisp white thobe, real setting tones, the product candidly present.
**Reference accounts:** @aseeb.najd, @barnscoffee, @cafe.najd | **Cultural Spec:** CS-01, CS-22, CS-13

**WHEN TO USE:** Authentic single-man UGC targeting Saudi men. SINGLE SUBJECT, reliable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
His setting, pose, and candid framing are creative decisions; the product is naturally present, brand-readable where framing allows. INTEGRATION: the setting's available daylight is the one light over thobe, skin, product, and space.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural — authentic UGC. Material truth: {product.material_texture} — the product true in the candid light; real Saudi skin with authentic texture and warm undertone; the white thobe with real cotton crispness and natural folds; honest daylight, true candid expression. No glossy over-production, no plastic skin.

[SCALE CALIBRATION]
{product.dimensions} — the product at true hand/table scale within his real moment.

[FRAMING & PROXIMITY]
Friend-distance candid framing — he and the product present and near, the setting soft behind.

[COLOR & CONTRAST]
Authentic-but-alive: real setting tones, white thobe clarity as the bright field, the product's color from {brand.color_field_palette} natural in the moment, warm true skin.

[LIGHT & LENS]
ONE truth: natural available daylight, honest and slightly imperfect like real phone capture. Phone-natural perspective, moderate authentic depth.

[NATURAL PLACEMENT]
He sits or stands as a man actually relaxes — honest weight, the product held or placed exactly as a hand would.

[COMPANION ELEMENTS]
The candid setting carries the context — no staged props.

[SCENE]
Authentic casual-moment composition. A SINGLE Saudi man in white thobe and ghutra in a relaxed everyday moment with the brand product — café, majlis, home, or a pleasant spot. Candid, mid-moment, friend-shot. Choice points: setting, pose, product placement, candid angle.

[SUBJECT]
ONE Saudi man only. Crisp white thobe and ghutra/shemagh styled contemporary (CS-01), or modern casual register per brand. Warm honey-bronze skin, real texture, groomed, relaxed candid expression. Authentic, never costume.

[BRAND CONSTRAINTS]
SINGLE subject — one man only, never a group, no other people. Product naturally present. Authentic thobe styling (CS-01). Authentic Saudi setting (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic UGC photography (phone aesthetic), maximum fidelity. Honest natural grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the setting (CS-13). {saudi.apparel_context} fills thobe/ghutra by region (CS-01).

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: setting, pose, candid angle, product placement. A different honest moment; his identity rules never vary.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. His appearance, thobe, ghutra, the product, {product.material_texture}, the setting — all preserved.

[MOTION]
SINGLE primary motion only: ONE natural candid action — a relaxed sip, OR a confident nod, OR a warm glance toward the product. NO complex motion.
Secondary: gentle ambient life (thobe shifts naturally, soft background motion).

[WHAT STAYS STATIC]
Facial features, skin tone, thobe/ghutra, product identity and material texture — locked. Setting stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Relaxed candid UGC pacing.

[OUTPUT]
Photoreal authentic UGC cinematography. Silent. No text overlay, no watermark.

---

## S03 · Saudi Family — Iftar Table Gathering — HIGH RISK (multi-subject)

**Tier:** premium | **Sectors:** F&B, Retail, Services, Hospitality | **Intent:** grow, harvest | **Frequency:** Ramadan-triggered | **Reference:** Optional | **Risk:** HIGH — multi-subject (see risk note) | **Drama dial:** warm reverent golden
**Color story:** Warm Ramadan iftar gathering — golden evening glow, abundant table, multi-generational warmth.
**RISK NOTE (binding):** Three generations around a table is exactly the wide multi-subject scene current AI struggles with (proven: groups go stiff, faces degrade, video motion fails). APPROACH: (a) prefer a STILL over video; (b) frame the gathering via the ABUNDANT TABLE with family presence SUGGESTED — hands reaching, partial figures, warm out-of-focus background — rather than multiple sharp full faces; (c) if a full family is required, generate as a still and expect retries, OR substitute F03 (Iftar Spread, no faces). Do NOT attempt complex multi-person video motion.
**Reference accounts:** @aseeb.najd, @diplomat_sweets, @laylali_riyadh | **Cultural Spec:** CS-15, CS-18, CS-21, CS-24, CS-13

**WHEN TO USE:** Multi-generational Ramadan family iftar — emotionally powerful. Use when the togetherness message justifies the effort, fallback ready.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} / {brand.name} identity. Identity DNA: {product.identity_dna}
The table's arrangement and the gathering's framing are creative decisions within the risk-note approach; the brand integrates into the iftar table respectfully, secondary to the family moment. INTEGRATION: the golden iftar-hour glow holds table, brand element, and every suggested figure in one warm light system.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with warm family-candid grade (or film_grain_warmth for a more produced feel). Material truth: {product.material_texture} for the brand element; real warm evening light, authentic Saudi iftar foods, honest gathering candor. No plastic spread, no inauthentic staging.

[SCALE CALIBRATION]
{product.dimensions} — the brand element at honest scale among real iftar anchors (dates, finjan, dallah, dishes) at true tabletop proportion.

[FRAMING & PROXIMITY]
Table-forward per the risk note: the abundant table fills the near foreground; family presence reads through closeness of hands and warmth of soft figures, never a wide sharp group portrait.

[COLOR & CONTRAST]
Warm Ramadan family palette — golden evening glow, rich food tones, amber togetherness; the brand integrates within (occasion palette leads).

[LIGHT & LENS]
ONE light system: warm golden iftar-hour glow after Maghrib, lamp warmth within it. Table sharp, background family presence soft.

[NATURAL PLACEMENT]
The table is laid as a real iftar is laid — honest weights, dallah and finjan per serving ritual (CS-18); reaching hands obey real anatomy and right-hand custom (CS-08).

[COMPANION ELEMENTS]
STRUCTURAL EXCEPTION: the composed iftar table IS the scene; restraint = nothing outside the authentic table.

[SCENE — MULTI-SUBJECT, table-forward per risk note]
Ramadan family iftar composition. An extended Saudi family gathered around an abundant iftar table, warm golden evening light. PREFERRED FRAMING: the abundant table in the foreground (dates, water, traditional Saudi dishes — CS-21) with togetherness SUGGESTED through hands reaching to share, partial figures, warm softly-out-of-focus background presence. Reverent, warm, multi-generational. Choice points: table arrangement, hands choreography, depth of family suggestion.

[SUBJECT — multi-subject caution]
If full figures appear: few and partly soft, modesty maintained for all (CS-24). PREFER the table as hero, family as warm context. Warmth over crowd.

[BRAND CONSTRAINTS]
Brand integrated respectfully. No pork, no alcohol (CS-21). Authentic Saudi iftar (CS-15, CS-18, CS-21). Modesty for all visible figures (CS-24). Reverent Ramadan treatment. Table-forward framing per risk note. No readable text beyond the brand's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal warm Ramadan family photography, maximum fidelity. Warm reverent abundant grade. No overlay text, no watermark.

[SAUDI ADAPTATION — CENTRAL (occasion-driven)]
{saudi.occasion_overlay} = Ramadan iftar drives the scene. {saudi.scene_context} fills authentic family iftar by region.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: table arrangement, hands choreography, depth and warmth of the suggested gathering. The same togetherness, never the same frame — within the risk-note approach always.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Table, brand integration, {product.material_texture}, warm light, any family presence — all preserved. Modesty maintained.

[MOTION — multi-subject caution]
MINIMAL and table-focused: steam rising from dishes, warm light flickering, ONE hand reaching to share a date. AVOID multi-person choreography (it fails). STRONGLY PREFER a STILL if motion destabilizes figures.

[WHAT STAYS STATIC]
Brand integration locked. Table stable. Any figures hold position, modesty maintained. Warm temperature. Capture character preserved.

[PACING & DURATION]
5-6 seconds. Continuous single take. Slow reverent warmth. (If figures degrade, deliver as still.)

[OUTPUT]
Photoreal warm Ramadan family cinematography (or still). Silent — reverent. No text overlay, no watermark.

---

## S04 · Hands-Only Product Interaction — Saudi Context — SAFEST

**Tier:** universal | **Sectors:** F&B, Beauty, Retail, Tech, Services | **Intent:** grow, harvest | **Frequency:** 2-3× per month | **Reference:** Optional | **Risk:** SAFEST human chain (no face = no face risk) — the go-to substitute when face-forward chains are too risky | **Drama dial:** clean authentic phone-natural
**Color story:** Clean authentic phone light on a Saudi-context surface — the product held or used by hands only.
**Reference accounts:** @danatreasures, @barnscoffee, @tiadress | **Cultural Spec:** CS-08, CS-01, CS-13

**WHEN TO USE:** Hands-only product interaction — human warmth without face-AI risk. The reliable workhorse across all sectors.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The hand action, grip, and setting are creative decisions; the product is held/used naturally, brand-readable face toward camera through the grip. INTEGRATION: one natural phone-light holds hands, product, and surface in a single honest moment.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural — authentic UGC. Material truth: {product.material_texture} — true reflectance in the grip; real Saudi hands with authentic skin texture, warm honey-bronze undertone, natural knuckle and nail detail. No plastic skin, no staged sterility.

[SCALE CALIBRATION]
{product.dimensions} — true to-hand scale; the grip itself is the proportion anchor (a sachet folds in the fingers, a bottle fills the palm honestly).

[FRAMING & PROXIMITY]
Close on hands and product — the interaction filling the frame, the Saudi-context setting soft behind.

[COLOR & CONTRAST]
The product's color from {brand.color_field_palette} is the focal point; warm true skin and modest sleeve frame it naturally. Clean authentic palette.

[LIGHT & LENS]
ONE natural phone-camera light, honest and clean. Phone-equivalent macro/normal perspective; hands and product sharp.

[NATURAL PLACEMENT]
The grip and gesture obey real hand anatomy — honest finger pressure, the product's substrate responding truly (film flexing, glass weighted).

[COMPANION ELEMENTS]
None — hands, product, and an honest surface only.

[SCENE]
Hands-only interaction. A single pair of Saudi hands holds or uses the product naturally — opening, applying, presenting, or holding — in an authentic Saudi-context setting (real surface; home, café, or workspace softly behind). No face; hands and product are the subject. Choice points: action, grip, surface, setting depth.

[SUBJECT]
Saudi hands only — no face, no full body. Warm honey-bronze, real texture, modest sleeve at the wrist (white thobe cuff or modern abaya sleeve per register, CS-01). Right-hand interaction preferred (CS-08).

[BRAND CONSTRAINTS]
Single product, hands-only — no face, no full body, no other people. Modest sleeve (CS-01), right-hand preferred (CS-08). Authentic Saudi context (CS-13). No readable text beyond the product's own label. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic UGC photography (phone aesthetic), maximum fidelity. Clean honest grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills the sleeve (CS-01). {saudi.scene_context} fills the surface/setting.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: hand action and grip, surface, setting depth, sleeve register. The interaction renews; the rules never vary.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Hands, product, {product.material_texture}, modest sleeve, setting — all preserved. Every label character locked.

[MOTION]
SINGLE primary motion: one natural hand action — turning the product to show it, opening/using it, or a gentle presenting gesture. Smooth and authentic; the product stays brand-readable.
Secondary: subtle ambient setting life.

[WHAT STAYS STATIC]
Product identity and material texture locked. Hands and modest sleeve consistent. Setting stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Natural authentic interaction pacing.

[OUTPUT]
Photoreal authentic UGC cinematography. Silent. No text overlay, no watermark.

---

## S05 · Saudi Woman Beauty Routine — Bathroom Mirror — COMPLIANCE-SENSITIVE

**Tier:** premium | **Sectors:** Beauty, Skincare, Cosmetics | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** COMPLIANCE-SENSITIVE + single subject — private at-home framing (hair may be uncovered ONLY in genuine private self-care context), strictly modest, never suggestive; if brand register is conservative, keep hair covered or substitute S04 hands-only | **Drama dial:** soft intimate phone-natural
**Color story:** Soft at-home light, clean private bathroom — intimate self-care warmth, the product's color focal.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride | **Cultural Spec:** CS-24, CS-22, CS-13

**WHEN TO USE:** At-home beauty routine UGC — private self-care framing. SINGLE SUBJECT; the sensitivity is compliance, not AI difficulty.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The routine moment and crop are creative decisions within the compliance frame; the skincare product is naturally present in the routine, brand-readable toward camera. INTEGRATION: one soft bathroom light holds her, the mirror, and the product in a single private moment.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with soft self-care warmth. Material truth: {product.material_texture} — the product true in her hand; real skin with authentic texture and a healthy natural glow (not airbrushed), honest soft light, true candid self-care expression, real application. No plastic skin, no staged glamour.

[SCALE CALIBRATION]
{product.dimensions} — the product at true palm/fingertip scale within the real routine.

[FRAMING & PROXIMITY]
Intimate-private framing — her routine and the product near and focused; the private bathroom soft behind.

[COLOR & CONTRAST]
Soft intimate self-care palette — clean private bathroom tones, warm true skin with healthy glow; the product's color from {brand.color_field_palette} as the focal point.

[LIGHT & LENS]
ONE soft at-home bathroom light — morning or evening, gentle and flattering, honest phone-natural quality. Subject and product sharp, setting soft.

[NATURAL PLACEMENT]
The routine gestures are real — honest application pressure, the product held as it's truly used.

[COMPANION ELEMENTS]
None beyond the honest routine — the private moment is the world.

[SCENE — PRIVATE AT-HOME, compliance-sensitive]
At-home beauty routine. A SINGLE Saudi woman applies skincare at a clean bathroom mirror in her private home — an authentic morning or evening self-care moment. Intimate-private and strictly modest: focus on the routine and product, modest at-home clothing, the genuine ritual. Choice points: routine moment, crop, light hour.

[SUBJECT]
ONE Saudi woman only. PRIVATE at-home context: per {brand.modesty_register} and the genuine private-home framing, hair may be uncovered ONLY in this authentic private self-care context, kept strictly modest, non-suggestive, focused on the routine (CS-24). Modest at-home clothing. Warm honey-bronze skin with authentic healthy glow. If brand register is conservative: hair covered, or shift to S04 hands-only.

[BRAND CONSTRAINTS]
SINGLE subject. PRIVATE self-care context, strictly modest and non-objectifying (CS-24). Focus on the routine. No other people. Authentic Saudi home (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic self-care UGC photography (phone aesthetic), maximum fidelity. Soft intimate grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} governs the modest at-home framing per register (CS-24). {saudi.scene_context} fills the Saudi home bathroom.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: routine moment, crop, light hour, bathroom character. The compliance frame never varies.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Her appearance, modest at-home framing, the product, {product.material_texture}, the private bathroom — all preserved. Modesty/privacy maintained every frame.

[MOTION]
SINGLE primary motion: one natural routine action — gently applying the product to the cheek/face, OR a soft satisfied expression as it's used. Calm, strictly modest, routine-focused. NO complex motion.
Secondary: subtle ambient — soft light shift, a strand of hair settling.

[WHAT STAYS STATIC]
Facial features, skin tone, modest framing, product identity — locked. Modesty/privacy every frame. Bathroom stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Calm intimate self-care pacing.

[OUTPUT]
Photoreal authentic self-care UGC cinematography. Silent. No text overlay, no watermark.

---

## S06 · Saudi Man Grooming Mirror Moment

**Tier:** premium | **Sectors:** Grooming, Beauty (men), Retail | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** RELIABLE (single subject) | **Drama dial:** clean authentic phone-natural
**Color story:** Clean at-home morning light, modern bathroom — the grooming product applied at the mirror.
**Reference accounts:** @aseeb.najd, @barnscoffee | **Cultural Spec:** CS-22, CS-13

**WHEN TO USE:** At-home men's grooming UGC — beard care, men's skincare. SINGLE SUBJECT, reliable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The grooming moment and crop are creative decisions; the product is naturally present, brand-readable toward camera. INTEGRATION: one soft morning bathroom light holds him, mirror, and product in a single honest routine.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with authentic grooming warmth. Material truth: {product.material_texture} — the product true in his hand; real Saudi skin with authentic texture, honest beard/grooming detail, candid focused expression. No plastic skin, no staged glamour.

[SCALE CALIBRATION]
{product.dimensions} — the product at true palm scale within the real routine.

[FRAMING & PROXIMITY]
Close on the routine — him and the product near and focused, the modern bathroom soft behind.

[COLOR & CONTRAST]
Clean authentic grooming palette — modern bathroom tones, warm true skin; the product's color from {brand.color_field_palette} as focal point.

[LIGHT & LENS]
ONE soft at-home morning light, honest phone-natural quality. Subject and product sharp.

[NATURAL PLACEMENT]
Real grooming gestures — honest application, the product handled as truly used.

[COMPANION ELEMENTS]
None — the honest routine is the world.

[SCENE]
At-home grooming composition. A SINGLE Saudi man applies a grooming product (beard oil, skincare, styling) at a modern bathroom mirror — an authentic morning moment, modern clean bathroom, soft light. Choice points: grooming action, crop, bathroom character.

[SUBJECT]
ONE Saudi man only. Modern groomed appearance — well-kept beard or clean-shaven per brand, contemporary style. Warm honey-bronze skin, real texture, focused candid expression. Modest at-home clothing.

[BRAND CONSTRAINTS]
SINGLE subject. Focus on the routine. No other people. Authentic Saudi home (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic grooming UGC photography (phone aesthetic), maximum fidelity. Clean authentic grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the Saudi home bathroom (CS-13). Grooming style reflects contemporary Saudi men's grooming.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: grooming action, crop, bathroom character, light hour. The routine renews honestly.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. His appearance, the product, {product.material_texture}, the bathroom — all preserved.

[MOTION]
SINGLE primary motion: one natural grooming action — applying the product to beard/face, OR a satisfied check in the mirror. Calm. NO complex motion.
Secondary: subtle ambient light shift.

[WHAT STAYS STATIC]
Facial features, skin tone, product identity — locked. Bathroom stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Calm authentic grooming pacing.

[OUTPUT]
Photoreal authentic grooming UGC cinematography. Silent. No text overlay, no watermark.

---

## S07 · Saudi Friends Group — Café Setting — HIGH RISK (multi-subject)

**Tier:** premium | **Sectors:** F&B, Retail, Lifestyle | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** HIGH — multi-subject (see risk note) | **Drama dial:** warm social golden
**Color story:** Warm modern café social energy — golden light, the product on the table amid a friends moment.
**RISK NOTE (binding):** 3–4 friends is the wide multi-subject scene current AI struggles with (faces degrade, groups stiffen, video motion fails). APPROACH: (a) prefer a STILL over video; (b) frame via the TABLE and shared product with friends SUGGESTED through hands, partial figures, warm out-of-focus presence; (c) single-gender group only; (d) two subjects partly soft is far more reliable than four sharp faces; (e) S01/S02 single-subject is the safer substitute. Do NOT attempt complex multi-person video motion.
**Reference accounts:** @barnscoffee, @cafe.najd, @coffeebeantealeaf.sa | **Cultural Spec:** CS-24, CS-01, CS-13, CS-22

**WHEN TO USE:** Friends social moment — single-gender group, social-proof energy. Use when the social message justifies the effort, fallback ready.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The table composition and social suggestion are creative decisions within the risk-note approach; the product sits naturally on the table, brand-readable face toward camera. INTEGRATION: the café's warm golden light holds table, product, and every suggested figure in one social glow.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with warm social-candid grade. Material truth: {product.material_texture} — the product true on the table; real warm café light, authentic candid social energy, honest phone framing. No plastic staging.

[SCALE CALIBRATION]
{product.dimensions} — the product at true tabletop scale among real cups and plates.

[FRAMING & PROXIMITY]
Table-forward per the risk note: the table and shared product fill the near foreground; the friends' togetherness reads through reaching hands and warm soft presence, never a wide sharp group portrait.

[COLOR & CONTRAST]
Warm social café palette — inviting golden tones; the product on the table as the focal anchor from {brand.color_field_palette}; friends as warm context.

[LIGHT & LENS]
ONE warm modern café light, golden and social. Table and product sharp; friends' presence soft.

[NATURAL PLACEMENT]
The table is set as friends actually share it — honest cups mid-drink, the product placed where a hand set it; reaching hands obey real anatomy.

[COMPANION ELEMENTS]
The shared café table IS the scene — its real cups and plates are the honest context, nothing staged beyond it.

[SCENE — MULTI-SUBJECT, table-forward per risk note]
Café friends composition. Three or four Saudi friends (single-gender group) share a social moment in a modern Saudi café, the brand product on the table. PREFERRED FRAMING: the table and product in the foreground with togetherness SUGGESTED — hands reaching for drinks, partial figures, warm laughter energy in softly-out-of-focus presence. Choice points: table composition, hands choreography, depth of social suggestion.

[SUBJECT — multi-subject caution]
Single-gender group of Saudi friends. If figures shown: few and partly soft, modesty maintained for all (CS-24, CS-01). PREFER table and product as hero, friends as warm context. Warmth over crowd.

[BRAND CONSTRAINTS]
Product on the table as anchor. Single-gender group. Modesty for all visible figures (CS-01, CS-24). Authentic modern Saudi café (CS-13). Table-forward framing per risk note. No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal authentic social UGC photography (phone aesthetic), maximum fidelity. Warm social grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the modern Saudi café (CS-13). {saudi.apparel_context} for visible figures (CS-01, CS-24).

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: table composition, hands choreography, café depth, golden warmth. The social energy renews — within the risk-note approach always.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Café table, product, {product.material_texture}, any friends presence, warm light — all preserved. Modesty maintained.

[MOTION — multi-subject caution]
MINIMAL and table-focused: steam from drinks, ONE hand reaching for a cup, warm ambient social energy in the soft background. AVOID multi-person choreography (it fails). STRONGLY PREFER a STILL if figures destabilize.

[WHAT STAYS STATIC]
Product identity and material texture locked. Table stable. Any figures hold position, modesty maintained. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Warm social pacing. (If figures degrade, deliver as still.)

[OUTPUT]
Photoreal authentic social UGC cinematography (or still). Silent. No text overlay, no watermark.

---

## S08 · Saudi Workplace Moment — Modern Office

**Tier:** premium | **Sectors:** Corporate, Tech, Services, F&B | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** RELIABLE (single subject) | **Drama dial:** clean modern aspirational
**Color story:** Modern Vision-2030 office light — clean contemporary workspace, the product naturally present in a professional moment.
**Reference accounts:** @aseeb.najd, @barnscoffee, @danatreasures | **Cultural Spec:** CS-24, CS-01, CS-13, CS-22

**WHEN TO USE:** Professional workplace UGC — modern Saudi professional life, Vision-2030 energy. SINGLE SUBJECT, reliable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The work moment, office depth, and crop are creative decisions; the product is naturally present in the professional moment, brand-readable toward camera. INTEGRATION: one bright modern daylight (through office glass) holds professional, product, and workspace in a single aspirational frame.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with modern-professional lift (or clean_studio for a more produced feel). Material truth: {product.material_texture} — the product true in the office light; real Saudi skin with authentic texture, honest modern-office light, true professional candor, real workspace detail. No staged corporate stiffness.

[SCALE CALIBRATION]
{product.dimensions} — the product at true desk/hand scale within a real workspace.

[FRAMING & PROXIMITY]
The professional and the product near and engaged — the modern office breathing aspirationally soft behind.

[COLOR & CONTRAST]
Modern professional palette — clean contemporary office tones, true skin; the product's color from {brand.color_field_palette} as focal point. Confident Vision-2030 energy.

[LIGHT & LENS]
ONE light: bright natural daylight through glass, contemporary and aspirational. Subject and product sharp, office soft.

[NATURAL PLACEMENT]
A real working posture — honest engagement, the product placed or held as in actual work.

[COMPANION ELEMENTS]
The real workspace carries the context — no staged props.

[SCENE]
Modern workplace composition. A SINGLE Saudi professional (man in thobe or modern business attire; woman in professional modest attire) in a contemporary Vision-2030 era office — clean modern design, glass, natural light, modern Riyadh/KAFD aesthetic — the brand product naturally present, a confident work moment. Choice points: work moment, office depth, crop, attire register.

[SUBJECT]
ONE Saudi professional only. Man: thobe or modern business attire; woman: professional modest attire per {brand.modesty_register} (CS-24, CS-01). Warm honey-bronze skin, real texture, confident professional expression.

[BRAND CONSTRAINTS]
SINGLE subject. Product naturally present. Modesty per register (CS-01, CS-24). Modern Saudi office (CS-13), Vision-2030 aesthetic, not generic Western. No readable text on screens or background items. {brand.anti_attributes}

[OUTPUT]
Photoreal modern workplace UGC photography, maximum fidelity. Aspirational professional grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the modern Saudi office (KAFD, modern Riyadh corporate). {saudi.apparel_context} fills professional attire by register.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: work moment, office depth, crop, attire within register. A different confident minute of modern Saudi work.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The professional's appearance, attire, the product, {product.material_texture}, the office — all preserved. Modesty maintained.

[MOTION]
SINGLE primary motion: one natural professional action — a confident glance up from work, OR lifting the coffee, OR a subtle engaged gesture. Composed. NO complex motion.
Secondary: subtle modern-office ambient life softly behind.

[WHAT STAYS STATIC]
Facial features, skin tone, attire, product identity — locked. Modesty maintained. Office stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Confident professional pacing.

[OUTPUT]
Photoreal modern workplace UGC cinematography. Silent. No text overlay, no watermark.

---

## S09 · Saudi Mother & Daughter Moment — MODERATE RISK (two subjects)

**Tier:** premium | **Sectors:** Beauty, Retail, F&B, Fashion | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** MODERATE — two subjects (see risk note) | **Drama dial:** warm tender
**Color story:** Warm generational tenderness — soft light, two generations together with the product.
**RISK NOTE (binding):** Two faces is more achievable than 3–4 but both must hold fidelity; video motion must stay simple. APPROACH: (a) prefer a STILL or very simple single-motion video; (b) compose them CLOSE TOGETHER sharing the product so the composition is intimate, not a wide two-shot; (c) both in modest hijab (canonical); (d) if faces degrade, tighten to a shared-hands-with-product moment (toward S04). Two subjects is the realistic ceiling for reliable warmth.
**Reference accounts:** @danatreasures, @tiadress, @themodestbride | **Cultural Spec:** CS-24, CS-01, CS-13

**WHEN TO USE:** Generational warmth — mother (forties) and adult daughter (twenties) with the product. Mother-daughter campaigns, generational messaging.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The shared moment and intimate composition are creative decisions within the risk-note approach; the product is naturally shared between them, brand-readable toward camera. INTEGRATION: one soft warm light holds both women and the product in a single tender moment.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with warm tender grade. Material truth: {product.material_texture} — the product true between them; real Saudi skin with authentic texture on BOTH, honest warm light, true tender candid expressions. No plastic skin, no staged stiffness.

[SCALE CALIBRATION]
{product.dimensions} — the product at true shared-hands scale within the intimate moment.

[FRAMING & PROXIMITY]
Intimate close composition per the risk note — the two composed close together around the product, never a wide two-shot; intimacy makes two faces more reliable AND more moving.

[COLOR & CONTRAST]
Warm family palette — gentle home tones, true skin on both; the product as the shared focal point from {brand.color_field_palette}.

[LIGHT & LENS]
ONE soft warm natural light, gentle and tender. Both subjects and product sharp, setting soft.

[NATURAL PLACEMENT]
A real shared gesture — one handing or applying the product to the other with honest anatomy and tenderness.

[COMPANION ELEMENTS]
None — the shared product moment is the world.

[SCENE — TWO-SUBJECT, compose intimate per risk note]
Mother-daughter composition. A Saudi mother (forties, warm mature presence) and her adult daughter (twenties) share a warm moment with the brand product — at home or a pleasant setting — composed CLOSE TOGETHER in an intimate shared moment (sharing skincare, coffee, a beauty item). Both in modest hijab. Warm generational tenderness. Choice points: shared action, setting, crop within the intimate frame.

[SUBJECT — two subjects, compose intimate]
TWO Saudi women — mother and daughter, both in modest hijab (canonical), modesty maintained (CS-24, CS-01). Composed close. Warm honey-bronze skin, real texture, tender genuine expressions. If faces degrade: tighten toward shared-hands-with-product (S04 logic).

[BRAND CONSTRAINTS]
TWO subjects, composed intimate (risk note). Both modest hijab (CS-01, CS-24). Product shared naturally. Authentic Saudi home (CS-13). No readable text on background items. {brand.anti_attributes}

[OUTPUT]
Photoreal warm generational UGC photography (phone aesthetic), maximum fidelity. Warm tender grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.apparel_context} fills modest hijab styling for both (CS-01, CS-24). {saudi.scene_context} fills the Saudi home.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: the shared action, setting, crop within the intimate frame, light warmth. The tenderness renews — within the risk-note approach always.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. Both women's appearances, modest hijab, the product, {product.material_texture}, the warm setting — all preserved. Modesty every frame.

[MOTION — two-subject caution]
SINGLE shared motion only: ONE simple shared action — a warm shared look, OR one gently applies/hands the product to the other, OR a soft shared smile. Two subjects cannot sustain complex independent motion. If either face destabilizes, deliver as a STILL.
Secondary: gentle ambient warmth.

[WHAT STAYS STATIC]
Both subjects' features, skin tones, modest hijab, product identity — locked. Modesty every frame. Setting stable. Capture character: phone_natural preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Warm tender pacing — one shared moment. (If faces degrade, deliver as still.)

[OUTPUT]
Photoreal warm generational UGC cinematography (or still). Silent. No text overlay, no watermark.

---

## S10 · Saudi Outdoor Lifestyle — Heritage Setting

**Tier:** premium | **Sectors:** F&B, Fashion, Beauty, Retail, Tourism | **Intent:** grow, harvest | **Frequency:** 1-2× per month | **Reference:** Optional | **Risk:** RELIABLE (single subject — the heritage backdrop is a major asset, lean into it) | **Drama dial:** golden heritage warmth
**Color story:** Golden Saudi heritage-outdoor light — Diriyah mudbrick, AlUla rock, Najdi architecture, or palm groves; cultural-pride warmth.
**Reference accounts:** @aseeb.najd, @tiadress, @danatreasures | **Cultural Spec:** CS-13, CS-01, CS-24, CS-22

**WHEN TO USE:** Heritage outdoor lifestyle — rooting the brand in Saudi cultural pride and stunning heritage settings. SINGLE SUBJECT, reliable.

### ◆ Image prompt

[BRAND LOCK — identity invariant, composition open]
The provided reference teaches the {product.name} identity. Identity DNA: {product.identity_dna}
The heritage setting, pose, and golden hour are creative decisions; the product is naturally present, brand-readable toward camera against the heritage backdrop. INTEGRATION: one golden outdoor sun holds subject, product, and heritage materials — mudbrick, sandstone, or palm glowing in the same light that warms her or his skin.

[REALISM & CAPTURE CHARACTER]
Capture character: phone_natural with golden heritage warmth (or broadcast_cinematic for more production). Material truth: {product.material_texture} — the product true in golden light; real Saudi skin with authentic texture and warm undertone; true heritage material textures (mudbrick grain, sandstone strata, palm fronds); candid proud expression. No plastic skin, no staged stiffness.

[SCALE CALIBRATION]
{product.dimensions} — the product at true hand scale; the heritage architecture at honest monumental proportion behind a real human figure.

[FRAMING & PROXIMITY]
The subject and product near and proud in the foreground, the stunning heritage setting opening in golden soft depth behind — pride framed close.

[COLOR & CONTRAST]
Heritage-outdoor palette — warm earth tones (mudbrick beige, sandstone honey, palm green), golden light, true skin; the product's color from {brand.color_field_palette} as focal point. Deep Saudi pride.

[LIGHT & LENS]
ONE light: golden-hour Saudi outdoor sun, directional and beautiful, the heritage materials glowing. Subject and product sharp, heritage backdrop soft.

[NATURAL PLACEMENT]
A real relaxed stance — honest weight, the product held or present as in a true moment.

[COMPANION ELEMENTS]
The heritage setting IS the world — no staged props.

[SCENE]
Heritage outdoor composition. A SINGLE Saudi subject (man or woman per brief) in a stunning Saudi heritage setting — Diriyah mudbrick architecture, AlUla rock formations, Najdi traditional architecture, or palm groves — with the brand product naturally present, golden light bathing the scene. Relaxed, proud, connected. Choice points: heritage setting, pose, sun direction, depth.

[SUBJECT]
ONE Saudi subject only. Man: thobe/ghutra or modern; woman: modest abaya/hijab per {brand.modesty_register} (CS-24, CS-01). Warm honey-bronze skin, real texture, proud relaxed expression. Modesty maintained.

[BRAND CONSTRAINTS]
SINGLE subject — never a group. Product naturally present. Modesty maintained (CS-01, CS-24). Authentic Saudi heritage setting (CS-13) rendered with cultural respect. No readable text in frame. {brand.anti_attributes}

[OUTPUT]
Photoreal heritage-outdoor UGC photography, maximum fidelity. Golden cultural-pride grade. No overlay text, no watermark.

[SAUDI ADAPTATION — conditional]
{saudi.scene_context} fills the specific heritage setting (Diriyah / AlUla / Najdi / palm grove). {saudi.apparel_context} fills attire by register. Cultural pride is central.

[TEXT OVERLAY — conditional, only when brief.text_request is present]
Render "{brief.text_request.copy}" — style: {brief.text_request.style}, placement: {brief.text_request.zone}.

[CREATIVE VARIANCE DIRECTIVE]
Vary across generations: heritage setting, pose, sun direction, depth, golden warmth. A different proud golden hour each time.

### ▶ Video prompt

[STARTING IMAGE HOLD]
Starting image is immutable ground truth. The subject's appearance, attire, the product, {product.material_texture}, the heritage setting — all preserved. Modesty maintained.

[MOTION]
SINGLE primary motion: one natural action — the subject turns warmly toward camera, OR lifts/presents the product, OR a relaxed proud gesture. Composed. NO complex motion.
Secondary: gentle outdoor ambient — a soft breeze moving fabric, warm light shifting across heritage materials.

[WHAT STAYS STATIC]
Facial features, skin tone, attire, product identity — locked. Modesty maintained. Heritage setting stable. Capture character preserved.

[PACING & DURATION]
5 seconds. Continuous single take. Relaxed proud heritage pacing.

[OUTPUT]
Photoreal heritage-outdoor UGC cinematography. Silent. No text overlay, no watermark.

---
---

# BATCH 5 · AGENT RUNTIME NOTES

**TF22 native chains** use the v3.7 native-video block order (no starting image; no 15-block image prompt). All v3.7 hard rules hold; all prompts under the 2,500-char native ceiling; V04 within the 2,000-char Seedance audio-workflow ceiling. V02 carries ELEVATED COMPLIANCE; V01/V04 carry occasion-palette-leads (the documented inversion).

**TF23 risk tiers are binding metadata** — the agent routes by risk: S03/S07 prefer still + table-forward framing + fallback substitution (F03 for S03; S01/S02 for S07); S09 intimate two-shot ceiling with S04 tightening fallback; S05 compliance gate (conservative register → hair covered or S04); S04 is the universal safe substitute.

**phone_natural is identity-tier on TF23** — the authentic look IS the value; any drift toward glossy production is a failure on this family even if the image is "better."

**Failure-ledger compliance:** all 15 chains carry the v3.7 architecture (15-block on TF23, native-adapted on TF22), the four v3.7 fields where applicable, brand-derived color (occasion chains documented inversions), proportion anchoring, framing-proximity, integration, single/companion restraint, no-readable-background-text, conditional/core text logic, and the CREATIVE VARIANCE DIRECTIVE. No fixed mm / f-stop / Kelvin commands anywhere. Multi-subject risk notes preserved verbatim in substance from v3.2 and elevated to binding status.

*OpenClaw · Master Prompt Library v3.7 · Batch 5 · TF22 + TF23 · 15 chains · Confidential*
