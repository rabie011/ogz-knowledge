# Cultural Advisor — Role and Playbook

**Confidence:** experimental — the Cultural Advisor role is defined here but not yet staffed.

## What this role exists for

`{PLATFORM_NAME}` competes on Saudi cultural authenticity as a moat. The system has structural safeguards (forbidden lists, CCO agent, compliance gates) — but every brand-launch carries the risk that no machine layer catches a culturally off-key choice that a Saudi reader would flag instantly.

The Cultural Advisor is the human authority who validates that risk surface:

- Reviews the 80-field cultural spec for each new sector × region default before it enters production
- Reviews HARD_BLOCK forbidden lists periodically and proposes updates
- Adjudicates Soft-flagged content the CCO routes for human review
- Reviews Two-CD Diagnostic outputs that touch culturally sensitive territory (religious occasions, gender depiction, heritage interpretation)

## Authority

- The Cultural Advisor can override the CCO score and route a post to publish or hold.
- The Cultural Advisor cannot modify Schemas in `12_data_shapes/` (those are frozen at v1) — but can propose changes to sector-default cultural specs, forbidden lists, and the advisor playbook itself via PR.
- The Cultural Advisor's verdict on a culturally-sensitive piece is final unless escalated to the brand and to Mohamed for a joint decision.

## Position in the workflow

```
   COO compiles CaptionContext  →  DeepSeek generates  →  CCO Arabic QC
                                                         ↓
                                          CCO returns score + flags
                                                         ↓
                                         CEO confidence + human gate
                                                         ↓
   ┌────────────────────┬───────────────────┐
   ↓                    ↓                   ↓
clean (score ≥75)   watermarked         hold (score <50)
publishes           publishes with         ↓
                    watermark         routed to Cultural Advisor
                                       (or to Production Copilot for
                                       non-cultural holds)
```

The Cultural Advisor sits at the rightmost branch — the hold queue, plus any cultural soft-flag routed by CCO.

## Expected SLA

- Routine cultural review: 24 hours from CCO routing.
- Urgent (scheduled publish within 24h): 4 hours.
- Sector-default cultural spec review: completed within 5 business days of submission.

## What this role is NOT

- Not a copy editor. Arabic copy quality is the CCO's call; cultural appropriateness is the Advisor's.
- Not a brand strategist. Brand voice is the brand's call.
- Not a content moderator. The CCO HARD_BLOCK list handles the unambiguous cases; the Advisor handles the judgment cases.

## Files in this playbook

- `escalation_procedures.md` — when content gets escalated, to whom, expected SLA
- `review_checklist.md` — the standing checklist used on each major deliverable

## Provenance

- Source: `MASTER_PROMPT_FOR_CLAUDE_CODE.md` §3.3 + AGENT_MANIFEST.md
- Confidence: experimental
- Scope: universal
