# Compliance Failure Cases
# OGZ Saudi Instagram — Documented Hard Blocks and Near-Misses
# Sourced from corpus compliance_check data | Updated: 2026-05-25

---

## How to Read This Document

Each case documents a real or near-miss compliance issue observed in the 636-observation corpus.
**Hard blocks** = content that must not publish.
**Soft flags** = content that needs review before publishing.

---

## Hard Block Cases

### Case HB-001 — Alcohol Product in Food Photography
**Account:** Steakhouse-adjacent F&B (corpus)
**Content type:** Image
**What happened:** International food styling template used for a steak and sides composition. A Perrier sparkling water bottle was placed center-left in the frame — standard international food styling. The brand (green glass bottle, French text) is visually associated with alcohol in the Saudi market context.
**Hard block triggered:** `ALCOHOL_PRODUCT_DETECTION` — severity: severe
**How it was caught:** Corpus observation flagged during extraction
**What should have happened:** All props in food styling must be pre-approved. International water brands (Perrier, San Pellegrino) are blocked. Use Saudia, Berain, or clear-glass local brands only.
**Production rule:** Add to brief: "No European sparkling water brands. Arabic water brands only."

---

## Soft Flag Cases (Near-Misses)

### Case SF-001 — Two-Handed Gloved Service
**Account:** F&B retail / fast casual
**Content type:** Image
**What happened:** Production used a food handler lifting a woven basket dome using both hands (gloved). Left hand contacted the serving vessel.
**Flag type:** `two_handed_gloved_service`
**Assessment:** Resolved as clean — professional gloved food service is standard practice; bare-left-hand cultural violation does not apply in hygiene-compliant contexts. Not a hard block.
**Learning:** Brief should specify: gloves = acceptable two-handed service. Bare hands = right hand only.

---

### Case SF-002 — Hand Dominance Ambiguity in Craft Shot
**Account:** F&B specialty (incense / qahwa service)
**Content type:** Image
**What happened:** Two-person scene examining an incense burner. The hand holding the object had ambiguous dominance from the camera angle.
**Flag type:** `hand_visibility_ambiguity`
**Assessment:** Resolved as clean — dual-handed craft examination is culturally distinct from serving action. Camera angle does not show the serving gesture.
**Learning:** For any shot involving hands and cultural objects (dallah, bukhoor, serving trays), specify the camera angle in the brief to make hand dominance unambiguous. Front-on or 45° angle shots confirm right-hand primacy.

---

### Case SF-003 — Cross-Gender Context Review
**Account:** F&B corporate / brand story
**Content type:** Image
**What happened:** A handshake image between two figures, both wearing gloves. Gender of one party was not determinable from torso-only framing. Described as military/medical solidarity context.
**Flag type:** `cross_gender_contact_review`
**Assessment:** Resolved as clean — both gloved, context is professional solidarity (not personal/social contact), gender indeterminate from available framing.
**Learning:** Any physical contact between two people in a frame must have gender context confirmed in brief. If gender is ambiguous and contact is present, the shot requires pre-production review.

---

### Case SF-004 — Serving Hand Check on Right-Hand Shot
**Account:** F&B (specialty product)
**Content type:** Image
**What happened:** Product served in right hand — culturally appropriate. Flagged as a soft note for awareness about hand dominance in serving context.
**Flag type:** `right_hand_serving_prominence`
**Assessment:** Correct execution — noted only for documentation.
**Learning:** Right-hand serving shots are always clean. This is the target state for all hand-visible serving content.

---

## Compliance Checklist for Production Briefs

Copy this into every brief that includes talent, food styling with props, or hand-visible shots:

```
COMPLIANCE PRE-CHECK:
☐ Hand visibility: right hand only for serving, offering, pouring
☐ Gloved service: two-handed acceptable in hygiene context
☐ Water/beverage props: Arabic brands only (no Perrier, San Pellegrino, Evian)
☐ Cross-gender contact: none between non-mahram individuals
    - Handshakes: same-gender only, or both-gloved professional context
    - Physical proximity: maintain respectful distance in mixed scenes
☐ Religious iconography: no unauthorized use of calligraphy, mosque images, Quran references
☐ Alcohol: zero tolerance — no bottles, glasses, or visual associations
☐ Pork: zero tolerance in F&B content — all meat must be visually identifiable as halal
☐ Male/female wardrobe: culturally appropriate for sector × region
    - Female: abaya or modest coverage unless beauty sector (face/hands/neck)
    - Male: thobe, formal, or smart casual (context-dependent)
```

---

## Recurring Production Mistakes by Category

| Category | Most Common Error | Prevention |
|----------|------------------|------------|
| Food photography | International props (EU water, EU packaging) | Props whitelist in brief |
| Talent direction | Unspecified hand for serving | "Right hand only" in talent brief |
| Food styling | Left-hand natural grip during setup | BTS monitoring for hand compliance |
| Architecture / atmosphere | Uncleared Arabic calligraphy in background | Location scout checklist |
| Beauty / skincare | Bare-shoulder or décolletage international models | Saudi-market casting brief |
