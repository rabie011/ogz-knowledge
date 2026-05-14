# 02_what_to_build — Chain Library

**88 production chains organized into 23 technique families (TF01–TF23).**

Each chain is a single, parameterized fal.ai generation workflow that produces one type of content. The system selects which chain(s) to run based on the brand's fingerprint, the current brief, sector defaults, occasion context, and CD-brain routing.

---

## How to Read This Folder

- `INDEX.json` — machine-readable inventory of all 88 chains with metadata for fast routing/filtering
- `TF01/` through `TF23/` — one folder per technique family
- Each chain is a single JSON file conforming to `../12_data_shapes/chain_v1.schema.json`
- Naming: `tf{family}_{seq}_{slug}.json` — e.g., `tf01_03_product_hero_static.json`

---

## The 23 Technique Families

| ID | Family | Chains | Purpose |
|---|---|---|---|
| TF01 | Product Hero (Clean) | 3 | Daily backbone — single product on clean background |
| TF02 | Splash & Motion | 5 | Liquid/smoke/ice frozen mid-motion — high-energy hero |
| TF03 | Spotlight & Dark Stage | 4 | Theatrical dramatic — single light source on dark BG |
| TF04 | Natural Environment | 5 | Product in real-world settings (bathroom, kitchen, café) |
| TF05 | Hand & Human Touch | 4 | Human hand interacting with product — sense of scale + warmth |
| TF06 | Studio Production Reveal | 3 | Behind-the-scenes studio aesthetic — pedestal/softbox |
| TF07 | Pastel & Shadow Play | 4 | Soft pastels + cast shadows — feminine, beauty register |
| TF08 | Cinematic Environment | 5 | Atmospheric placement — desert, rain, fog, brutalism |
| TF09 | Portrait & Model | 5 | Person-led — fashion, beauty, modest fashion, full studio |
| TF10 | Editorial Poster | 3 | Typography + design — magazine/billboard/announcement |
| TF11 | Texture & Macro | 3 | Extreme close-up — texture is the subject |
| TF12 | Active Product Moment | 3 | Product in active use — pour, spray, drip mid-action |
| TF13 | Lifestyle Context | 7 | Product within a lived moment — desk, table, hotel, BTS |
| TF14 | Premium Pedestal | 3 | Plinth/pedestal placement — luxury showcase |
| TF15 | Promotional & Text | 3 | Price/offer-driven — menu cards, tags, promotional |
| TF16 | Occasion & Cultural | 2 | Iftar spread, occasion greetings — culturally anchored |
| TF17 | Before/After Transformation | 2 | Service transformation — before/after split or static |
| TF18 | Product Flat Lay | 4 | Top-down flat lay — collection, bundle, story |
| TF19 | On-Model Apparel | 1 | Apparel on full model — modest fashion register |
| TF20 | Premium Fragrance/Oud | 2 | Fragrance/oud-specific — amber, smoke, packaging |
| TF21 | Service CTA | 2 | Direct CTA — booking, launch announcement |
| TF22 | Video (legacy native) | 5 | Native video generation — Ramadan, B/A, unboxing, occasion, reveal |
| TF23 | Saudi UGC Authentic | 10 | **The Saudi differentiation engine** — engineered against AI-look failure modes |

---

## Reading a Chain File

Each chain JSON has these key sections:

- **Identity** — `chain_ulid`, `chain_id_short`, `family`, `name_en`, `name_ar`, `schema_version`
- **Purpose** — what the chain does, one paragraph
- **Models** — fal.ai model(s) used + their role
- **Inputs** — what the operator/system must supply
- **Prompt template** — literal fal.ai prompt with `{placeholders}` resolved at runtime from brand fingerprint + cultural spec + brief
- **Output type + dimensions** — image vs video, aspect ratio, duration
- **Eligibility filters** — sector × occasion × quality-tier × maturity gates (used by router to filter the 88 chains per brand)
- **Cultural constraints** — which compliance gates this chain triggers
- **Cost + latency estimates** — for runtime budget enforcement
- **Best-for CD brains** — which strategic methodologies pair well with this chain
- **Anti-patterns** — explicit "don't do these"
- **Notes** — Saudi adaptation guidance, reference image requirements, frequency hints, source code
- **Provenance** — source / date / confirmer / confidence / scope

---

## How Chains Are Selected at Runtime

The router (CEO + COO agents) selects chains via this funnel:

1. **Filter by brand sector** — keep chains where `eligibility_filters.sectors_allowed` includes the brand's sector or `*`
2. **Filter by brand quality tier** — keep chains where the tier is in `quality_tiers_allowed`
3. **Filter by brand maturity** — drop chains where `min_brand_maturity_days` exceeds brand age
4. **Filter by occasion** — if brief is occasion-anchored, prefer chains where the occasion is in `occasions_allowed`
5. **Score remaining chains** by CD-brain affinity (`best_for_cd_brains`) × current brand-fingerprint primary CD brain
6. **Apply diversity constraint** — avoid same chain twice in the same content batch
7. **Return top N chains** with their composed prompts ready for fal.ai

---

## Why TF23 Matters Most

The Saudi UGC Authentic family (TF23, 10 chains) is the **single most important differentiation lever** in the system. AI image/video models default to generic, Western-leaning, or tourist-aesthetic Saudi imagery. TF23 chains are engineered against those failure modes:

- Specific architectural anchoring (Najdi mudbrick from Diriyah, AlUla sandstone, Al-Ahsa palm groves)
- Body language and gesture rules (right-hand serving, elder-first, etc.)
- Wardrobe specificity (thobe cut, hijab style, abaya regional variation)
- Authentic-not-staged composition rules
- Anti-tourist-aesthetic explicit negative prompts

Other families could be replicated by any competitor with the same fal access. TF23 cannot, because it encodes 80-field cultural specification + behavioral correctness that requires the OGZ knowledge layer to produce well.

---

## Adding a New Chain

1. Pick the right family folder
2. Use the next sequential `chain_id_short` (e.g., if family has tf01_01 through tf01_03, new one is tf01_04)
3. Mint a fresh ULID
4. Copy an existing chain in the same family as your starting structure
5. Validate against `../12_data_shapes/chain_v1.schema.json` via `python3 scripts/validate.py {your_chain.json} 12_data_shapes/chain_v1.schema.json`
6. Update `INDEX.json` (currently generated; will become Memory-Controller-managed at runtime)
7. PR for review

---

## Validation

All chains MUST pass schema validation:

```bash
python3 scripts/validate.py 02_what_to_build/TF23/tf23_10_saudi_outdoor_lifestyle_heritage_setting.json 12_data_shapes/chain_v1.schema.json
```

Run all 88 at once:

```bash
for f in 02_what_to_build/TF*/tf*.json; do
  python3 scripts/validate.py "$f" 12_data_shapes/chain_v1.schema.json
done
```

The full validation is run by CI on every PR.
