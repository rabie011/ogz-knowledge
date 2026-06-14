# V3.7 ALIGNMENT MAP — the whole system through the OpenClaw v3.7 lens
*2026-06-13 · Mohamed: "everything we have must align with these 3 files… go back to all
the data and extraction and the full work and see it through the files' lens." Scope = Everything.*
*This is the DIAGNOSIS (Rule #11 diagnose→show→wait). No fix is built until the sequence is agreed.*

## THE ROOT (dive to bedrock)
The whole visual system was built to **OpenClaw v3.2** — *describe the past, command fixed
camera specs*. **v3.7 inverted the philosophy**: *lock identity, open everything else;
brand-derived colour; mood not spec; scale/material truth.* So this is not patching fields —
it is a **generational re-alignment**. The deepest layers (the extraction schema + the chain
library) are the wrong generation, and everything downstream inherits that.

## THE MAP (evidence-backed, 6 dimensions)

| # | Dimension | v3.7 lens demands | Today (evidence) | Verdict |
|---|---|---|---|---|
| 1 | **Extraction schema** (`brand_fingerprint_v1`) | the 23 v3.7 fields; identity-locked; **NO fixed mm/f-stop/Kelvin** | l3_visual/l4_cinematography carry exactly the **fixed specs v3.7 BANS** (focal_length, key_fill_ratio, camera_angle, color_grade_lock); **missing** color_field_palette, dimensions, material_texture, companion_elements, identity_dna, label_text_ar/latin, anti_attributes, capture_character | 🔴 contradicts + incomplete |
| 2 | **Organ coverage** (all clients) | every brand carries the v3.7 fields | l3/l4/l5 **EMPTY for all 4 pilots**; `build_visual_dna_profiles.py` produces **past-describing STATS** (dominant_color_family, character_presence_rate) not prescriptive v3.7 fields | 🔴 empty + wrong shape |
| 3 | **Chain library** | run on the **94 v3.7 chains** (15-block, identity-locked) | whole pipeline reads `02_what_to_build/` = **127 v3.2 chains** (tf01_01…, 9-block, fixed-spec); **10 consumer scripts** point at it; v3.7 wired into nothing | 🔴 wrong generation; 10 to re-point |
| 4 | **Creative-brain handoff** | scene→[SCENE]; chain pick = a v3.7 id | `idea.scene_ar` wire **OK**; but `visual.pro_chain` points at v3.2 ids; output = phone_shoot_card / generic string, not the v3.7 prompt | 🟡 half-aligned |
| 5 | **Gap engine** (`gap_report`) | gaps = which v3.7 fields are RED per brand | tracks strategy organs only (identity/goals/red_lines/truth); **blind to the v3.7 visual fields** | 🟡 missing a dimension |
| 6 | **Render path** | `flux-2-pro/edit` + reference image, the v3.7 15-block prompt | `render_image.py` = `flux/schnell` + generic string; `render_client_slot` = phone_shoot_card | 🔴 rebuild |

## What ALREADY aligns (don't rebuild)
- The 94 v3.7 chains are saved + parsed (`data/openclaw_v37/`).
- `openclaw_convert.py` already produces lint-clean v3.7 prompts with honest fill-sourcing.
- `idea.scene_ar` → `[SCENE · creative seed]` handoff works.
- Reference images exist per pilot (`clients/<h>/media/`).
- The provenance/organ-write discipline + the gap→confirm-card loop is the right machinery —
  it just needs the v3.7 fields added to what it tracks.

## PROPOSED SEQUENCE (top-down — Pyramid Law: dig from the top, the contract first)
1. **SCHEMA** — redefine the fingerprint's visual layers to the v3.7 23-field taxonomy;
   retire the fixed-spec fields v3.7 bans. (the contract everything else obeys)
2. **CHAIN LIBRARY** — make v3.7 the canonical chains; re-point the 10 consumers (or bridge).
3. **EXTRACTION/DERIVATION** — rebuild visual-DNA so it *produces* the v3.7 fields (the canon's
   own derivation logic) as candidates, not past-stats; persist to organs with provenance.
4. **GAP ENGINE** — add v3.7-field readiness to `gap_report` → the real confirm-questions.
5. **BRAIN HANDOFF** — `pro_chain`→v3.7 ids; output→the v3.7 prompt (the converter is the path).
6. **RENDER** — `flux-2-pro/edit` + reference + the converter's prompt (behind the 4 gates already named).

*Nothing here is built until Mohamed confirms the sequence / names the start.*
