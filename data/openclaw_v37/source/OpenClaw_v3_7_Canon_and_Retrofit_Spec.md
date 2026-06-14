# OpenClaw · v3.7 Canon & Retrofit Specification
**Purpose:** Single source of truth consolidating everything established across the testing sessions, plus the exact specification for aligning all 88 chains so no prompt carries the issues hit during live testing.
**Status:** v3.7 is the locked canonical architecture (established via 5 rounds of live Baja visual testing)
**Date:** 2026-06-10 · OGZ Studios LLC · Confidential

---

# PART 1 — WHAT WE ESTABLISHED (THE CANON)

## 1.1 Version history — what each round fixed

| Version | What it added | Problem it killed |
|---|---|---|
| v3.2 | Original 9-block architecture, fixed camera/light specs per chain | — (baseline) |
| v3.3 | Identity locked / composition open · CREATIVE VARIANCE DIRECTIVE · INTEGRATION principle | Same composition repeating across every chain; product pasted on top of scene |
| v3.4 | NATURAL PLACEMENT (gravity-governed) · SCALE CALIBRATION (honest real-world size) | Giant floating hero product; forced-upright posing |
| v3.5 | FRAMING & PROXIMITY (hero through closeness) · COMPANION ELEMENTS system | Dead space around product; no world context |
| v3.6 | Brand-derived COLOR & CONTRAST blocking · chiaroscuro shadow-cut light · COMPANION RESTRAINT | Flat images; garnish-scatter clutter |
| **v3.7 (LOCKED)** | Color field **brand-derived** (never borrowed from reference) · scale **proportion-anchored** · **material truth** (pliable film, not rigid) | Off-brand color fields; wrong sachet-to-finjan proportion; plastic-rigid texture |

**The core lesson:** lock identity, open everything else. When borrowing an aesthetic from a reference (e.g., the Ppang editorial punch), extract the *principle* — never its literal palette. Each brand fills the frame with its own colors.

## 1.2 The 12 prompt needs (distilled from all five rounds)

1. Identity locked, everything else open
2. Real creative variance across generations
3. Integration, not placement-on-top
4. Natural placement over forced hero-posing
5. Honest scale
6. Hero through proximity, not dead space
7. Companion elements, derived and restrained
8. Editorial graphic punch — chiaroscuro + brand-derived color blocking
9. True material texture
10. Per-chain calibration (the drama dial)
11. Conditional Saudi + text blocks
12. Platform-agnostic placeholders

## 1.3 The 15-block v3.7 image architecture (canonical block order)

1. **[BRAND LOCK · identity invariant, composition open]** — teaches identity via `{product.identity_dna}`; states that angle/framing/placement/light are creative decisions; carries the INTEGRATION principle
2. **[REALISM & CAPTURE CHARACTER]** — `{brand.aesthetic.capture_character}` + `{product.material_texture}` material-truth
3. **[SCALE CALIBRATION]** — `{product.dimensions}` + relationship to environment/companions
4. **[FRAMING & PROXIMITY]** — hero-through-closeness; share-of-frame target; no dead space
5. **[COLOR & CONTRAST]** — brand-derived color-field blocking (calibrated per chain)
6. **[LIGHT & LENS]** — mood/intent, not fixed spec; chiaroscuro calibrated per chain
7. **[NATURAL PLACEMENT]** *(environmental chains; studio chains use a hero-framing line instead)*
8. **[COMPANION ELEMENTS]** *(where relevant — one hero companion, restrained)*
9. **[SCENE]** — the creative seed + the model's choice points
10. **[SUBJECT]** — what's in frame + physical truth
11. **[BRAND CONSTRAINTS]** — `{brand.anti_attributes}` + chain-specific limits
12. **[OUTPUT]** — grade, resolution, exclusions
13. **[SAUDI ADAPTATION — conditional]** — fires only when brand/brief is Saudi-relevant
14. **[TEXT OVERLAY — conditional]** — fires only when `brief.text_request` is present; otherwise omitted entirely
15. **[CREATIVE VARIANCE DIRECTIVE]** — explicit instruction to vary choices across generations of the same chain

Video prompts keep the 5-block structure (IMAGE HOLD · MOTION 3-layer · WHAT STAYS STATIC · PACING · OUTPUT) — that part of v3.2 was validated and survives unchanged.

## 1.4 The four new v3.7 fields (open schema questions with Mohamed Rabie)

- **`{brand.color_field_palette}`** — the brand-owned colors a color-blocking chain may fill the frame with. Never an accent borrowed from a reference image.
- **`{product.dimensions}`** — real-world size + a scale-anchor object (e.g., "≈10cm tall; a serving cup is ≈5–6cm, so product is ~1.5–2× cup height")
- **`{product.material_texture}`** — material-truth description for the product's substrate (flexible film, glass, rigid carton, metal tin…)
- **`{product.companion_elements}`** — the product's "world" of related objects + the one-hero-companion restraint rule

These are **additive** to the v3.2 placeholder taxonomy, not renames. Find-replace harmonization to Mohamed's canonical BrandDNA schema still applies post-testing.

## 1.5 The two agent-side derivation logics (product-agnostic)

**Companion derivation:** every product belongs to a category world; derive 1–3 related objects; integrate ONE hero companion per environmental scene with natural physics.
- Coffee/tea → serving cup, pot, beans, dates, cardamom, steam
- Cold beverage → ice, condensation, citrus, frosted glass, mint
- Fragrance → the box, scent-matched botanicals, vanity surface
- Sweets → cocoa dusting, the unwrapped piece, nuts
- Skincare → water droplets, hero ingredient, folded towel
- Packaged food → prepared dish, raw hero ingredient, utensil

**Color-field derivation:** when a chain calls for color-blocking, the field color comes from `{brand.color_field_palette}` only. Extract the principle (saturated field, pop via contrast or harmony); exclude any color the brand's identity does not own.

## 1.6 Block inclusion rules (agent runtime)

- `[SAUDI ADAPTATION]` — only when brand/brief is Saudi-relevant; skip otherwise
- `[TEXT OVERLAY]` — only when `brief.text_request` present; no empty text block ever
- `[COMPANION ELEMENTS]` — environmental + splash chains; absent on clean studio (U01, T02) and retail-shelf chains (where the scene IS the companion)
- `[NATURAL PLACEMENT]` — environmental chains + lifestyle hand chains; studio chains use a hero-framing line instead

## 1.7 The drama calibration dial (per-chain, from 18-chain set — extend per family in retrofit)

| Setting | Chains (18-set) | Character |
|---|---|---|
| Full editorial punch | G01, G04, G06, T01, T03, T04, T05, T07 | Hard light, deep shadow-cut, color-block |
| Warm tungsten chiaroscuro | H02, G03 | Intimate, soft-edged — majlis, not product-studio |
| Soft natural | G02, H01 | Gentle contrast (H01: hard golden-hour but outdoor-natural) |
| Palette discipline only | H03, G05 | Busy scene — can't fully color-block |
| Clean even (no drama) | U01, T02 | T02 stays locked by design (marketplace uniformity) |
| Single hard key, deep dark | H04 | — |

## 1.8 Hard rules (non-negotiable in every chain)

1. One hard light source governs both product and environment
2. One hero companion element maximum per environmental scene
3. Neighboring shelf products carry NO readable text — out of focus or plain color only
4. Color fields derived from brand palette, never reference images
5. Scale proportion-anchored to a real-world anchor object
6. Material reads as its true substrate (film is pliable, never rigid)
7. TEXT OVERLAY is conditional — fires only on `brief.text_request`
8. T02 Pure Silhouette stays locked-tight (uniformity is its purpose)
9. Arabic wordmark fidelity is the highest-risk identity element — verify every generation
10. Char limits: image blocks < 8,000 chars; video blocks < 2,500 chars

## 1.9 Authority & format decisions (established, unchanged)

- **Creative chain decisions** (count, concepts, wording): Alhareth + creative side
- **Schemas, field naming, agent routing**: Mohamed Rabie
- **Cultural Spec** (80 fields, 0%): Hisham, Ohoud, Nada, Kamal
- **Platform storage format**: schema-validated JSON per `chain_v1.schema.json` (ULID IDs, five-field provenance, append-only, frozen v1 — ADR process for changes). Markdown is working format only; JSON rebuild parked until 18-chain testing completes AND the four schema fields are resolved.
- **Model-agnostic prompts** — no workflow assignments inside prompt text; 8 base fal topologies execute, Supabase injects at runtime
- **Arabic in-image text**: generative models re-paint the canvas; the platform solution is a deterministic overlay node (Pillow + arabic-reshaper + python-bidi). Not yet built. Until built, shortest Arabic copy only (single word, e.g., إتقان), or Latin-only on text-central chains.

---

# PART 2 — THE FAILURE LEDGER

Every issue hit in live testing → root cause → the v3.7 rule that prevents it → the audit check to run on every chain.

| # | Issue seen in testing | Root cause | v3.7 fix | Audit check per chain |
|---|---|---|---|---|
| 1 | Same composition repeating across chains | v3.2 prescribed angle, light direction, K-temp, f-stop in every chain | Identity locked / composition open + CREATIVE VARIANCE DIRECTIVE | LIGHT & LENS contains no fixed mm/f-stop/K as commands; variance directive present |
| 2 | Product pasted on top of scene | No integration language | INTEGRATION principle in BRAND LOCK — same light defines scene and product; environmental color cast on product edges; contact shadows agree | Integration language present in block 1 |
| 3 | Giant floating hero product | No scale anchor | SCALE CALIBRATION block + `{product.dimensions}` proportion anchor | Block 3 present with anchor-object relationship |
| 4 | Forced-upright posing | Hero-posing default | NATURAL PLACEMENT — gravity decides; may lie, lean, tilt | Block 7 present on environmental chains |
| 5 | Dead space around product | No proximity rule | FRAMING & PROXIMITY — share-of-frame target | Block 4 present |
| 6 | Garnish-scatter clutter | Unrestrained props | COMPANION ELEMENTS + one-hero restraint | Block 8 names ONE hero companion max |
| 7 | Flat, no punch | No color/contrast strategy | COLOR & CONTRAST block + chiaroscuro | Block 5 present, calibrated to drama dial |
| 8 | Off-brand color field (borrowed red/orange) | Reference palette leaked into prompt | Brand-derived `{brand.color_field_palette}` only | No literal reference colors anywhere in prompt |
| 9 | Wrong sachet-to-finjan proportion | Vague size language | Proportion anchoring ("~1.5–2× cup height") | Dimensions expressed as ratio to anchor |
| 10 | Rigid/plastic sachet texture | No substrate truth | `{product.material_texture}` — pliable flexible film | Material named with behavior (folds, creases, light response) |
| 11 | Fake invented wordmarks on shelf neighbors | No neighbor-text rule | Neighbors carry NO readable text | Constraint present in shelf/retail chains |
| 12 | Heritage chains reading hard-editorial | One-size drama | Drama dial — warm tungsten chiaroscuro for heritage | Dial setting matches chain family |
| 13 | Broken Arabic text in image | Generative models re-paint canvas | Conditional TEXT OVERLAY + deterministic overlay node (parked) + shortest-copy rule | Text-central chains flagged Latin-only / overlay-pending |
| 14 | Multi-subject scenes stiff/degraded | Known model limit | Single-subject rule + honest fallbacks (S03/S07/S09 risk notes) | Fallback strategy present on multi-subject chains |

---

# PART 3 — GAP AUDIT: v3.2 MASTER LIBRARY vs v3.7 CANON

What the 88-chain v3.2 library (the 210-page PDF) is missing, block by block:

| v3.7 element | Status in v3.2 library | Retrofit action |
|---|---|---|
| SCALE CALIBRATION block | **Absent** in all 88 | Add block 3 to every chain |
| FRAMING & PROXIMITY block | **Absent** in all 88 | Add block 4 to every chain |
| COLOR & CONTRAST block | Partially folded into LIGHT & LENS as "Popping Color Intent" — no brand-derivation rule | Split into dedicated block 5 with brand-derived rule |
| NATURAL PLACEMENT block | **Absent** | Add to environmental + hand chains |
| COMPANION ELEMENTS block | **Absent** (some scenes mention props loosely) | Add with one-hero restraint where relevant |
| CREATIVE VARIANCE DIRECTIVE | **Absent** in all 88 | Add block 15 to every chain except locked chains (T02-type) |
| Fixed camera specs (85mm, f/8, 5500K etc.) | **Present everywhere — this is the repetition bug** | Convert to mood/intent language; keep specs only on locked-uniform chains |
| `{product.material_texture}` | Absent — REALISM blocks use generic "authentic material" | Wire placeholder into block 2 |
| `{product.dimensions}` | Absent | Wire into block 3 |
| `{brand.color_field_palette}` | Absent | Wire into block 5 |
| `{product.companion_elements}` | Absent | Wire into block 8 |
| No-readable-neighbor-text rule | Present in some retail chains, inconsistent | Enforce on all shelf/retail/environment chains |
| One-hard-light-source rule | Stated in some chains | Enforce universally |
| Drama dial assignment | Implicit per chain, not codified | Assign explicit dial setting per chain in metadata |
| Video 5-block structure | ✅ Validated, keep | Verify WHAT STAYS STATIC includes material/texture lock |
| Conditional SAUDI + TEXT blocks | ✅ Already correct in v3.2 | Keep |
| Identity-teaching BRAND LOCK | ✅ Present — extend with composition-open + INTEGRATION language | Amend, don't replace |

**The 18 chains (F1/F2/F5/F-GROUND) already exist in full v3.7 form** from the testing session (`openclaw_master_prompts_v3_7_platform.md`). The retrofit applies to the remaining **70 canonical chains** across TF03–TF04, TF06–TF23, plus any GROUND chains outside the tested six.

---

# PART 4 — RETROFIT EXECUTION PLAN

## 4.1 Sequence

1. **Re-confirm 18-chain test status** — if any of the 18 still shows a failure-ledger issue, tune before scaling (one chain, one variable, retest)
2. **Extend the drama dial** to all 23 families (proposed mapping below — needs creative sign-off)
3. **Retrofit the 70 remaining chains** to the 15-block v3.7 architecture, in batches (credit-conscious), preserving each chain's creative concept, sectors, CS refs, and reference accounts from v3.2 — only the architecture changes
4. **Run the 14-point audit** (Part 2 ledger) against every chain — automated check script where possible (block presence, placeholder presence, no fixed-spec language, char limits)
5. **Resolve the four schema fields with Mohamed** → then JSON rebuild per `chain_v1.schema.json`
6. **Build the Arabic overlay node** before TF10/TF15 text-central chains go live

## 4.2 Proposed drama-dial mapping for untested families (for sign-off)

| Dial setting | Families |
|---|---|
| Full editorial punch | TF02 splash, TF06 luxury dark, TF08 cinematic environment, TF12 silhouette/halo |
| Warm tungsten chiaroscuro | TF19 heritage craft, TF16 occasion (Ramadan-register chains) |
| Soft natural | TF03 lifestyle real, TF23 UGC authentic, TF09 portrait (outdoor) |
| Palette discipline only | TF13 retail shelf/scene, TF18 flat lay collection (busy compositions) |
| Clean even (locked) | TF01 catalog chains, TF15 promo cards, TF10 announcement cards |
| Bright pastel pop | TF07 pastel & shadow play (its own register — pastels ARE the color block) |

## 4.3 Open dependencies

| Item | Owner | Blocks |
|---|---|---|
| Four schema fields (`color_field_palette`, `dimensions`, `material_texture`, `companion_elements`) | Mohamed Rabie | JSON rebuild |
| 18-chain test completion confirmation | MAD | 70-chain retrofit go/no-go |
| Arabic overlay node (Pillow + arabic-reshaper + python-bidi) | Unassigned | TF10/TF15 production use |
| Cultural Spec 80 fields | Hisham, Ohoud, Nada, Kamal | `{saudi.*}` runtime fills |
| Drama-dial mapping sign-off (4.2) | Alhareth / MAD | Retrofit calibration |
| Storefront/signage + service-in-action chains (library gap from barber test) | Creative side | Service-business coverage |

---

*OGZ Studios LLC · OpenClaw · v3.7 Canon & Retrofit Spec · Confidential*
