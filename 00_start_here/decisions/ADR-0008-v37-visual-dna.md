# ADR-0008 — Brand Visual DNA aligns to OpenClaw v3.7 (retire v3.2 fixed-spec fields)

- **Status:** Accepted (Mohamed: "everything must align to these 3 files… go build", 2026-06-13)
- **Owner of this layer:** Mohamed Rabie (per the v3.7 canon: "Schemas, field naming, agent routing: Mohamed Rabie")
- **Consulted:** GPT-4o-mini cold mind (verdict: risky → fixes integrated) + RABIE chair (added reference_images; enforced YELLOW-never-silently-confirmed)

## Context
OpenClaw v3.7 is the locked image/video prompt canon. Its prompts consume 23 placeholders,
4 of them NEW (`color_field_palette`, `dimensions`, `material_texture`, `companion_elements`).
The legacy `brand_fingerprint_v1` was built for v3.2: its `l4_cinematography` layer **commands
fixed camera specs** (`focal_length`, `key_fill_ratio`, `camera_angle`, `camera_height`,
`depth_of_field`, `sensor_look`, `color_grade_lock`, `signature_camera_move`). v3.7 **bans
all of these** — "no fixed mm / f-stop / Kelvin commands anywhere"; LIGHT & LENS is "mood/intent,
not fixed spec"; the model chooses, CREATIVE VARIANCE varies. So the legacy schema both
*contradicts* (commands what v3.7 forbids) and is *incomplete* (lacks the 4 new fields + the
v3.7-shaped identity/material/scale fields).

## Decision
A NEW schema, `brand_visual_dna_v37_v1.schema.json`, becomes the contract that feeds the
converter. Shape: a shared `brand` block + a per-product array. Each placeholder is a
`statusField` (value + GREEN/YELLOW/RED + provenance). The retired fixed-spec fields are
**absent** — those are runtime model choices, not brand DNA.

Integrated from the consult:
- **Per-product overrides** (cold mind) — a product MAY override brand-level palette/
  color_field/capture_character/anti_attributes when a sub-line differs; else it inherits.
- **YELLOW is a renderable default, never silently promoted to confirmed** (RABIE / Mohamed's
  anti-hallucination law) — derived candidates render now AND raise a confirm-question; only a
  client tap turns YELLOW→GREEN. RED doesn't block either (the reference image carries identity).
- **`reference_images` per product** (RABIE) — confirmed real photos of THIS product, the
  flux-2-pro/edit identity anchor, each with provenance it is verified (not a lookalike).
- **Field definitions + examples** embedded in the schema (cold mind: prevent misinterpretation).

## Non-destruction
`brand_fingerprint_v1` is **not changed** (frozen v1 rule honoured). Its l3/l4/l5 stay as
legacy; brands gain a new `visual_dna.json` (this shape). The converter reads visual_dna first.

## Consequences
- The extraction/derivation layer must PRODUCE these fields (P3), replacing the past-stats
  visual-DNA builder.
- The gap engine reads `_status` → RED/YELLOW become the real confirm-questions (P4).
- The converter's three fill-sources map exactly: GREEN→organ, YELLOW→derived, RED→client_needed.
