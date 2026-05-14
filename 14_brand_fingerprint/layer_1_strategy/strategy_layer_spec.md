---
title: "Layer 1 — Strategy"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 1 — Strategy

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
