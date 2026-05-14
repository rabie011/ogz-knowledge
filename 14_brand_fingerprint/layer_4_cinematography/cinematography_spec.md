---
title: "Layer 4 — Cinematography"
schema_version: 1
created_at: "2026-05-14T15:27:06Z"
provenance:
  source: "research_corpus_synthesis + brand_fingerprint_v1.schema.json + OGzAI_BrandDNA_Schema_V3_FINAL.docx"
  date_added: "2026-05-14T15:27:06Z"
  confirmer: "Mohamed"
  confidence: "experimental"
  scope: "universal"
---

# Layer 4 — Cinematography

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
