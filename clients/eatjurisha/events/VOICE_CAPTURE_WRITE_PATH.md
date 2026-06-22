# Khwila voice-capture write-path (B190)

How eatjurisha owner **Khwila's** voice pick merges into the brand fingerprint `l2_voice`
the **same day** she answers — no manual editing of the fingerprint (Rule #12: the system
produces; Rule #6: every writer has a reader).

## The wire (end to end)

1. **Card** — the question-pack card-builder reads a voice template from
   `clients/_templates/intake_answer_templates.jsonl` and shows Khwila a choice card.
   The five voice templates (B190): `q_voice_dialect`, `q_voice_register`, `q_voice_tone`
   (scalars → set) and `q_voice_love`, `q_voice_hate` (lines → append).

2. **Event** — her tap becomes a `client_event_v1` `intake_answer` via
   `intake_projection.event_from_template(tmpl, value, confirmer="client", ts, stamp)`.
   The event self-routes: it carries `target="fingerprint"`, `field="l2_voice.*"`, and for
   the line questions `op="append"`. It is written through `ledger_write()` (schema-validated;
   `confirmer="client"` is a HUMAN confirmer, so it is allowed to move trust — B156).

3. **Reader** — the nightly `writeback_replay` calls `intake_projection.project_intake()`
   over the full ledger. A confirmed voice answer:
   - scalar (`l2_voice.dialect/register/tone`) → **set** at the dotted path
   - line (`l2_voice.love_lines/hate_lines`) → **appended** (deduped, idempotent)
   The result lands in `clients/eatjurisha/profile/fingerprint.json` → `l2_voice`, flipping it
   from AMBER (`source: none`, `confirmer: pending_client`) toward a client-confirmed voice.

4. **Downstream consumer** — the composer reads `l2_voice` when it writes captions, so her
   confirmed voice shapes production from the next run.

## Laws held
- **Rule #6 (Consumer Law):** the voice pick is a write WITH a reader — `project_intake`
  already consumes fingerprint-target `intake_answer`s; B190 only added the `l2_voice` routing
  rows + list-append op.
- **Rule #9 / B156:** only HUMAN-confirmed answers (`confirmer ∈ {mohamed, client, alhareth}`)
  move organ state. Provisional/machine answers are ignored.
- **Idempotent:** re-deriving from the full ledger yields no new change (append dedupes).

## Staging note
Sending the card to Khwila is **client-facing** → it rides Mohamed's approval (mohamed_must),
never auto-sent. This step pre-stages the *capture machinery* so her answer merges same-day
once he approves the send.
