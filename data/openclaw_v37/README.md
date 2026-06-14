# OpenClaw v3.7 — the locked image/video prompt canon (saved 2026-06-13)

The single source of truth for how the system turns a creative idea into an
image/video **prompt**. v3.7 is the LOCKED canonical architecture (5 rounds of live
visual testing). The prompt is the durable asset — "the LLM will change, the prompt
will not."

## What's here
- `source/` — the 3 canon files VERBATIM (every word, sha256-stamped):
  - `OpenClaw_Master_Prompt_Library_v3_7_COMPLETE.md` — all 94 chains
  - `OpenClaw_v3_7_Canon_and_Retrofit_Spec.md` — the why: version history, 10 hard rules, failure ledger
  - `OpenClaw_Complete_System_v3_7.pdf` — the designed document (186 pp)
- `chains/<ID>.json` — 94 chains parsed losslessly (verbatim template text + metadata +
  block list + placeholder list + char stats). 89 image chains + 5 native-video (V01–V05).
- `INDEX.json` — roster (id, title, family, sectors, tier, locked, char counts).
- `placeholder_index.json` — the 23 placeholders × which chains use each.
- `samples/` — converter output (the prompts shown to Mohamed for feedback).

## The architecture (canon)
**15-block image prompt** (block order): BRAND LOCK · REALISM & CAPTURE · SCALE
CALIBRATION · FRAMING & PROXIMITY · COLOR & CONTRAST · LIGHT & LENS · NATURAL PLACEMENT
*(studio chains: hero-framing line instead)* · COMPANION ELEMENTS *(where relevant)* ·
SCENE *(creative seed)* · SUBJECT · BRAND CONSTRAINTS · OUTPUT · SAUDI ADAPTATION
*(conditional)* · TEXT OVERLAY *(conditional)* · CREATIVE VARIANCE DIRECTIVE.
**5-block video**: STARTING IMAGE HOLD → MOTION → WHAT STAYS STATIC → PACING → OUTPUT.

**Models**: image `fal-ai/flux-2-pro/edit` (≤8,000 chars, **needs a reference image** that
teaches identity) · video `fal-ai/kling-video/v1.6/pro/i2v` (≤2,500 chars).

**The 4 NEW v3.7 fields** (open schema questions with Mohamed; must be brand-confirmed):
`{brand.color_field_palette}` (used by 76 chains), `{product.dimensions}` (84),
`{product.material_texture}` (89), `{product.companion_elements}` (13).

**10 hard rules**: one hard light source · one hero companion max · neighbours carry no
readable text · color fields brand-derived (never borrowed from the reference) · scale
proportion-anchored · material truth · TEXT OVERLAY conditional · T02 locked · Arabic
wordmark = highest-risk identity (verify every gen) · char caps image<8000 / video<2500.

## The converter — `scripts/openclaw_convert.py`
Takes (handle, chain, creative seed) → emits the full v3.7 prompt with every placeholder
filled from THREE honestly-tagged sources:
- **organ** — read from the brand's organ files (a confirmed fact)
- **derived** — agent-side logic the canon itself prescribes (companion table, color-field
  principle, material-by-substrate, scale-by-product) — a CANDIDATE, becomes a confirm Q
- **client_needed** — brand truth no logic can invent (exact hex, label text, identity) —
  rendered `«CLIENT: …»` so the gap is loud

It runs a conformance lint (all required blocks present, char cap, no unfilled `{}`,
conditional rules) and never spends. Regenerate the parse with
`python3 scripts/parse_openclaw_v37.py` (deterministic, asserts 94 chains).

## Rendering (GATED — not yet wired)
`render_image.py` currently uses `flux/schnell` with a generic prompt — it does NOT emit
the v3.7 15-block prompt. A v3.7 render path needs: (1) a FAL key (none found in
`~/.abraham_env`), (2) Mohamed's flip of `no_fal_photos`, (3) per-pilot reference images
(present in `clients/<h>/media/`), (4) the B141 ruling reconciled (no AI product
depiction vs flux-2-pro/edit's reference-locked recomposition of the REAL product).
