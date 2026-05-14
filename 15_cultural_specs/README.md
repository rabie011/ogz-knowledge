# 15_cultural_specs/

The cultural moat. 80-field specs per sector × region + universal forbidden lists + Cultural Advisor playbook.

## Layout

```
15_cultural_specs/
├── sector_defaults/        — 8 YAMLs, each validates against cultural_spec_v1.schema.json
│   ├── f_and_b_najdi.yaml
│   ├── f_and_b_hejazi.yaml
│   ├── retail_modern.yaml
│   ├── retail_heritage.yaml
│   ├── beauty_modern.yaml
│   ├── beauty_heritage.yaml
│   ├── real_estate_modern_najdi.yaml
│   └── healthcare_modern.yaml
├── forbidden_lists/        — 4 universal hard-block lists (no formal schema; provenance enforced)
│   ├── universal_gestures_forbidden.yaml
│   ├── universal_props_forbidden.yaml
│   ├── universal_behaviors_forbidden.yaml
│   └── universal_visuals_forbidden.yaml
└── advisor_playbook/       — 3 markdown docs for the Cultural Advisor role
    ├── README.md
    ├── escalation_procedures.md
    └── review_checklist.md
```

## How the 80 fields are used

- **At onboarding:** A new brand inherits the sector × region default. The brand overrides ~10 fields (modesty_threshold, face_visibility, mixed_gender rules, brand_signature_hero_prop, dialect_default, etc.) based on the 15-question Pipeline A intake.
- **At generation:** The COO agent reads the brand's compiled cultural spec when composing CaptionContext. Fields shape voice, register, prop allowance, gesture forbiddance.
- **At QC:** The CCO agent cross-checks generated content against the brand's spec + the universal forbidden lists. Mismatches trigger HARD_BLOCK or SOFT_FLAG depending on severity.

## The 8 categories of the 80-field spec

| # | Category | Fields | Purpose |
|---|---|---|---|
| 1 | `characters` | 10 | Ethnic/regional look, age distribution, gender presentation, modesty defaults |
| 2 | `wardrobe` | 12 | Thobe/abaya/head-covering rules per gender + region |
| 3 | `body_language` | 8 | Sitting, standing, walking, greeting, eye contact, cross-gender distance |
| 4 | `gestures` | 10 | Forbidden universals + brand-allowed list + counting/beckoning conventions |
| 5 | `settings_architecture` | 10 | Najdi / Hejazi / Eastern / modern-Riyadh + material palette + religious-setting treatment |
| 6 | `props_objects` | 10 | Coffee/tea service, dates, frankincense, modern tech, heritage props, forbidden list |
| 7 | `behaviors_rituals` | 12 | Coffee-serving order, prayer treatment, Ramadan + Eid + Hajj behaviors, hierarchy |
| 8 | `social_dynamics` | 8 | Mixed-gender rules per context, modesty threshold, religious authority treatment |

Plus 5 top-level orientation fields: `scope_label`, `regional_orientation`, `heritage_gravity`, `religious_sensitivity`, `generational_orientation`.

## Confidence and validation

- All 8 sector-default specs are marked `confidence: experimental`.
- The Cultural Advisor (role defined in `advisor_playbook/README.md`) reviews each before it transitions to `confidence: inferred` or `confirmed`.
- Brand-level overrides ride on top of the sector default; they don't replace the spec.

## Forbidden lists

The 4 forbidden lists are universal hard-blocks — they apply to every brand, every sector, every occasion. They are read by the CCO agent at QC time. A caption or imagery referencing an entry triggers HARD_BLOCK and the score is floored to 0.

| List | Examples |
|---|---|
| `universal_gestures_forbidden` | left-hand serving, palm-up beckoning, sole-of-foot visible, OK-circle |
| `universal_props_forbidden` | alcohol, pork, gambling, other-faith religious symbols, Quranic overlay |
| `universal_behaviors_forbidden` | eating during Ramadan daylight, cross-gender contact (non-mahram), commercial prayer staging |
| `universal_visuals_forbidden` | Saudi flag misuse, competitive political imagery, Kaaba-as-backdrop, named royals unauthorized |

These lists are versioned via the file (no separate schema). Updates go through PR + Cultural Advisor sign-off.

## Cultural Advisor role

Defined in `advisor_playbook/README.md`. The Advisor is the human authority who:
- Reviews new sector × region defaults before production
- Adjudicates CCO soft-flag holds
- Reviews Two-CD Diagnostic outputs in culturally sensitive territory
- Proposes updates to forbidden lists

The Advisor's verdict is final unless escalated to Mohamed + brand jointly (sovereignty / royal / political content).

## Updating

- Sector specs: PR + Cultural Advisor review
- Forbidden lists: PR + Cultural Advisor review + Mohamed sign-off
- Advisor playbook: PR + Mohamed sign-off
