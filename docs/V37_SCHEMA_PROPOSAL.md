# PROPOSAL — brand_visual_dna_v37 schema (the contract for v3.7 prompts)

## The standard it must satisfy
OpenClaw v3.7 prompts consume 23 placeholders. The brand DNA must persist the **brand-level**
and **product-level** ones (brief.* comes from the generation request; saudi.* from the
Cultural Spec library at runtime — neither belongs in brand DNA). v3.7 philosophy: **lock
identity, open everything else; brand-derived colour; mood not spec.**

## What this schema RETIRES (v3.2 → v3.7 inversion)
The old fingerprint's `l4_cinematography` commanded **fixed specs v3.7 explicitly bans**:
`focal_length, key_fill_ratio, camera_angle, camera_height, depth_of_field, sensor_look,
color_grade_lock, signature_camera_move`. v3.7 says these are the **model's creative choices**
(LIGHT & LENS = "mood/intent, not fixed spec"; CREATIVE VARIANCE varies them). So they leave
brand DNA entirely. What survives from l3/l4/l5: palette, mood/tone, cultural resonance.

## The proposed shape
```
brand_visual_dna_v37:
  brand:                          # shared across all the brand's products
    region, sector, tone_register, quality_tier, price_position, modesty_register
    palette: { primary, background_tone }
    color_field_palette: [colours]          # NEW v3.7 — brand-OWNED field colours, never borrowed
    capture_character: "<aesthetic>"        # e.g. clean_studio / warm_lifestyle_film
    anti_attributes: [things never to render]
  products: [                     # per-product — each product has its own truth
    { name,
      identity_dna,               # the locked identity (reference image carries it)
      silhouette_description,
      material_finish,
      material_texture,           # NEW v3.7 — true substrate behaviour
      dimensions,                 # NEW v3.7 — real size + scale-anchor object
      companion_elements,         # NEW v3.7 — the product's "world", one hero companion
      label_text_arabic, label_text_latin }
  ]
```
Every field carries the 5-field provenance block + a `_status`: **GREEN** (client-confirmed) /
**YELLOW** (agent-derived candidate via the canon's own logic) / **RED** (client-only, can't be
inferred — exact hex, wordmark, the deep identity). The status drives the gap engine: RED/YELLOW
fields become the confirm-questions. The converter reads GREEN as `organ`, YELLOW as `derived`,
RED as `client_needed`.

## Why per-product (not brand-flat)
A brand has many products; dimensions/material/identity/label differ per product. The chain
prompt is always about ONE product, so the converter selects the product and fills product-level
fields from that product's record, brand-level from the shared block.

## Migration / non-destruction
New schema FILE (`brand_visual_dna_v37_v1.schema.json`); the frozen `brand_fingerprint_v1`
stays. An ADR records the retirement of the fixed-spec fields. Organs gain `visual_dna.json`
(this shape); l3/l4/l5 in fingerprint are left as-is (legacy) or pointed to read from here.

## The question for the mind
Does this fully align to the v3.7 canon (15-block image prompt, 10 hard rules, the 4 new
fields, mood-not-spec)? What breaks in production? What's missing? Is per-product right?
