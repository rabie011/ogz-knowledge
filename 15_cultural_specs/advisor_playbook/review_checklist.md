# Cultural Advisor — Standing Review Checklist

Run this checklist on each major deliverable that reaches the Advisor's queue. A "fail" on any item routes the deliverable back to COO with the specific note.

## A. Religious sensitivity

- [ ] No prayer/supplication shown as commercial backdrop
- [ ] No Quranic verse overlaid on promotional content
- [ ] No Kaaba/Mecca/Medina imagery used as backdrop for non-Hajj brand
- [ ] No named religious authority depicted commercially without clearance
- [ ] Religious occasion (Ramadan, Eid) tonality matches occasion phase (e.g., Ramadan contemplative-first in first 20 days, joy in last 10)

## B. Gender depiction

- [ ] Mixed-gender scenes respect brand's stated rule (strict / family-only / professional / modern-natural)
- [ ] Women's depiction matches brand's `face_visibility_women_rule` setting
- [ ] No cross-gender physical contact between non-mahrams
- [ ] Modesty level matches brand-defined threshold (strict / moderate / modern-permissive)
- [ ] Same-gender intimacy / proximity is warm but not romantic-coded

## C. Regional accuracy

- [ ] If brand is Najdi: visual language is Najdi (architecture, dress, palette) — not collapsed to "generic Gulf"
- [ ] If brand is Hejazi: Hejazi specifics shown (rawasheen, coastal palette, Red Sea references where relevant)
- [ ] If brand is Eastern: Eastern Province visual cues respected
- [ ] Arabic dialect in caption matches brand's stated dialect (no Najdi-only markers in Hejazi content, no Levantine forms in any Saudi content)

## D. Gestures and props

- [ ] No left-hand serving / handling food / drink / gifts
- [ ] No palm-up Western beckoning
- [ ] No soles of feet visible toward people
- [ ] No alcohol / pork / gambling references
- [ ] Hospitality gestures (coffee dallah, dates) staged correctly (right hand, eldest served first)

## E. Occasion alignment

- [ ] If posted during Ramadan: no food consumption during daylight implied
- [ ] If Eid Al-Fitr Day 1: tone is family-celebratory, not transactional
- [ ] If Eid Al-Adha: entertainment sector blackout respected; no graphic animal imagery
- [ ] If National Day: Saudi green used full-strength; no flag misuse
- [ ] If Founding Day: heritage-deep register, distinct from National Day

## F. Forbidden lists cross-check

- [ ] No item from `forbidden_lists/universal_gestures_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_props_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_behaviors_forbidden.yaml`
- [ ] No item from `forbidden_lists/universal_visuals_forbidden.yaml`

## G. Bilingual quality

- [ ] Arabic copy reads as authentic Saudi Arabic — not translation-smell English
- [ ] Arabic and English are siblings (parallel originals), not one translating the other
- [ ] Arabic is set at equal optical weight to English (never as caption)
- [ ] No machine-translation markers (literal idioms, English sentence shape with Arabic words)

## H. Compliance signals

- [ ] Sector-specific compliance respected (Healthcare: no medical claims without SFDA / MoH clearance; Finance: no guaranteed-return language; Real Estate: no race-targeted pricing)
- [ ] CCO `negpat_flag` outcome reviewed (no HARD_BLOCK, STRONG_WARN reviewed for substantiation)
- [ ] PDPL: no identifiable individuals depicted without consent (especially in Healthcare)

## Decision

After running the checklist:

- **Zero fails** → Approve
- **1-2 minor fails (item in A.5, B.4, C.3, G.3)** → Approve with watermark + send back the specific notes
- **Any severe fail (any in A.1–4, B.1–3, D, F)** → Hold for rewrite
- **Sovereignty / royal / political content** → Escalate to Mohamed + brand jointly

Log the verdict with which checklist items failed (or "all passed") in the audit trail.

## Provenance

- Source: 80-field cultural spec + forbidden lists + agent prompts + Saudi cultural-norm synthesis
- Confidence: experimental
- Scope: universal
