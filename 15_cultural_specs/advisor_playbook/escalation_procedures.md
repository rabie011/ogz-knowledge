# Escalation Procedures — Cultural Advisor

## When content reaches the Cultural Advisor

Content routes to the Cultural Advisor under any of these conditions:

| Trigger | Source | Urgency |
|---|---|---|
| CCO flagged `cultural_flag: true` | CCO output | High — within 24h |
| CCO flagged `brave_route_flag: true` and brand is in Healthcare / Finance / Government sector | CCO output | High — within 24h |
| CCO `religious_reference_detected` and brand's `religious_sensitivity` is High | CCO output | Highest — within 4h |
| Content was generated for Ramadan / Eid / National Day and falls within the 7 days before the occasion | CEO routing | High |
| Two-CD Diagnostic where one or both brains is the Heritage Decoder and the brief is heritage-sensitive | Router | Standard — within 24h |
| First-ever campaign for a new sector × region cultural spec | Memory Controller | Standard |
| Brand owner explicitly requests Cultural Advisor review | Platform UI | Per request urgency |

## How escalation works (operational)

1. **Auto-route:** Memory Controller writes a `cultural_review_request` event with: brand_id, post_id(s), reason, urgency, deadline.
2. **Notify:** The Cultural Advisor receives notification (Telegram + email + platform inbox).
3. **Review:** Advisor opens the post(s) in the platform's Review queue. Reads caption, sees imagery (if present), sees the CCO flags + score, sees the relevant cultural-spec fields, sees the relevant forbidden-list entries.
4. **Verdict:** One of:
   - **Approve** — content publishes (or moves to next gate). Verdict logged with reason.
   - **Approve with watermark** — content publishes with the beta-quality watermark.
   - **Hold for rewrite** — back to COO with specific cultural revision notes.
   - **Hold for brand decision** — escalate to brand owner.
   - **Reject** — content blocked. Reason added to brand's NegativePattern list (proposed).
5. **Log:** All verdicts append to the audit trail as event-log entries.

## When to escalate further

The Cultural Advisor escalates to **Mohamed + brand owner jointly** when:

- Content touches Saudi sovereignty, royal family, or named historical/political figures
- Content touches Hajj, Kaaba, Mecca, Medina visual context for a non-Hajj brand
- Content involves a religious-text reference (Quranic verse, hadith, religious authority quote)
- Content involves cross-sectarian religious imagery
- The brand insists on a creative direction the Advisor judges culturally damaging

For all other cases, the Advisor's verdict is final.

## Sector-default cultural spec review

When a new sector × region default is added (e.g. `eastern_province_modern`), the Cultural Advisor reviews:

1. The full 80 fields, with focus on:
   - `characters` block (especially `face_visibility_women_rule`, `gender_presentation_rule`)
   - `wardrobe` block (regional accuracy)
   - `gestures` block (correct interpretation of cultural conventions)
   - `behaviors_rituals` block (occasion behaviors, prayer treatment)
   - `social_dynamics` block (mixed-gender rules)
2. Cross-checks against:
   - The relevant chains' `cultural_constraints` blocks
   - Sector baseline file (e.g. `05_sector_defaults/retail.yaml`)
   - Universal forbidden lists
3. Submits review notes as a draft ADR if changes affect more than this one spec.

Approved spec is updated from `confidence: experimental` to `confidence: inferred` (or `confirmed` if validated through real client use).

## Provenance

- Source: `MASTER_PROMPT_FOR_CLAUDE_CODE.md` §3.3 + AGENT_MANIFEST.md + agent prompts
- Confidence: experimental
- Scope: universal
