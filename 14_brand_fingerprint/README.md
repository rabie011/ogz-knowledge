# 14_brand_fingerprint/

The 6-layer brand fingerprint specs + onboarding flows + distinctiveness scoring.

## Layout

```
14_brand_fingerprint/
├── layer_1_strategy/strategy_layer_spec.md
├── layer_2_voice/voice_layer_spec.md
├── layer_2_voice/voice_examples_per_sector.md
├── layer_3_visual_identity/visual_identity_spec.md
├── layer_3_visual_identity/color_extension_rules.md
├── layer_4_cinematography/cinematography_spec.md
├── layer_5_look_and_feel/look_and_feel_spec.md
├── layer_6_production_signature/production_signature_spec.md
├── enhanced_onboarding/
│   ├── 15_question_critical_starter.md
│   ├── 60_question_full_intake.md
│   ├── pipeline_a_intake_flow.md
│   └── pipeline_b_intake_flow.md
└── distinctiveness_scoring/
    ├── brand_fingerprint_score_spec.md
    └── anti_convergence_monitor.md
```

## The 6 layers

| Layer | Owns | Schema fields |
|---|---|---|
| L1 — Strategy | Which CD methodology(s) lead | primary_cd_brain, cd_routing_weights, contrarian_belief |
| L2 — Voice | Audible identity | voice_triangle, love-lines, hate-lines, dialect |
| L3 — Visual | Color, typography, composition | primary_color, secondary_color, typography, logo_behavior |
| L4 — Cinematography | Lens grammar | lighting, focal length, motion, signature camera move |
| L5 — Look & Feel | Felt experience | mood_lexicon, reference_brand_anchors, audience_state_lock |
| L6 — Production | Recurring details | talent, location, props, wardrobe, signature ritual |

## Pipeline A vs Pipeline B

- **Pipeline A** (Starter, SAR 2,500/mo): 15-question critical starter form. Self-service. 8 posts/month. ~4 min onboarding.
- **Pipeline B** (Growth + Enterprise, managed): 60-question full intake form. Strategist + Cultural Advisor involved. 20-40+ posts/month. 25-40 min onboarding across 2-3 sessions.

## Distinctiveness scoring

`distinctiveness_score = 1.0 - avg_cosine_similarity_to_sector_peers`

Higher = more distinct. Anti-convergence monitor detects drift over time.

## Schema

The brand fingerprint composite validates against `12_data_shapes/brand_fingerprint_v1.schema.json`. Brand fingerprints themselves live in the runtime database (RLS-isolated), NOT in this repo. This folder holds the SPECS that govern their structure.
