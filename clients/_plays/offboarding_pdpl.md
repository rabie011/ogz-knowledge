# PDPL Erasure vs. Append-Only Ledgers — Research (B152)

> **Status:** RESEARCH, not legal advice. Persisted by the RABIE orchestra (B152, 2026-06-22).
> Feeds Mohamed's pending **PDPL precedence ruling** referenced in [docs/OFFBOARDING_PLAY.md](../../docs/OFFBOARDING_PLAY.md).
> We present the law as found + two reconciliation options + a recommendation. **We do NOT make the ruling** — that is Mohamed's fork.

## The conflict in one line
A client (or an individual whose data we hold) has a **right to erasure** under Saudi PDPL.
Our learning system keeps **append-only ledgers** (taste picks, make_sure log, gold/kills,
pattern-engagement evidence, decision queue) — immutable history is *how the system learns*.
Erasure vs. immutability collide. Which wins, and how do we honor both?

## What the law says (verified against multiple sources, 2026-06)

1. **Destruction is mandatory once purpose ends — Art. 18.** Once personal data fulfills the
   purpose it was collected for, the controller must destroy it. The data subject may also
   *request* destruction when: the data is no longer needed, consent is withdrawn and was the
   *sole* legal basis, or the data is being processed in violation of the PDPL.

2. **Anonymization is the explicit carve-out — Art. 18.** The controller **may retain** data
   if it has been **anonymized** — *all pointers that could lead to discovery of the data
   subject removed*. **Anonymized data is not considered personal data**, so it falls outside
   the erasure right entirely. → This is the legal hook that lets append-only *aggregate/learning*
   signal survive.

3. **Erasure has exceptions for legal/statutory/judicial retention.** Destruction can be
   superseded where a **legal justification** requires keeping the data longer, or where
   **judicial/litigation proceedings** require retention until they conclude (e.g. a statutory
   accounting period, an active dispute). Once the basis lapses, secure deletion is required.

4. **Destruction must cascade.** Erasure must reach **all systems, backups, and third parties**
   the data was shared with — *except* where a legal retention basis applies.

5. **Security standard for what we keep — Art. 19 / Impl. Reg. Art. 23.** Retained data must be
   protected to NCA (National Cybersecurity Authority) standards / recognized best practice.

## Two reconciliation options (for Mohamed's ruling)

### Option A — Anonymize-in-place (RECOMMENDED)
On an erasure request, **strip every identifier** from the client's rows in the append-only
ledgers (client name, handle, brand-identifying free text, any pointer) so what remains is
**anonymized learning signal** — which Art. 18 says is no longer personal data and may be
retained lawfully. The append-only history *survives* because the surviving rows are not
personal data.
- **Pros:** Honors erasure AND preserves the learning moat. Single legal basis (anonymization),
  no reliance on a fragile retention argument.
- **Cons:** Requires a *deterministic, asserted* anonymizer over every ledger keyed by the
  entity, with a **Rule #8 refuse-don't-warn guard**: if any residual identifier remains after
  the pass, the erasure is REFUSED (non-zero), never "completed with a note." Anonymization must
  be irreversible (no re-identification key kept).

### Option B — Tombstone + statutory hold
Keep identifiable rows intact **only** where a genuine legal basis exists (active contract,
live dispute, statutory accounting period); mark the erased entity with a **tombstone**; and
**hard-delete** identifiable rows the moment the basis lapses.
- **Pros:** Maximal fidelity while a real hold exists.
- **Cons:** A marketing-content *learning* ledger rarely has a standalone statutory retention
  basis, so this leans on an argument that may not hold for most rows. Use B **only** for the
  narrow set of rows under a real hold; everything else still needs Option A.

**Recommendation:** **A as the default**, with **B layered only where a real statutory/judicial
hold genuinely applies.** A gives us a clean single legal hook (anonymization) that protects the
moat without betting on a retention argument PDPL may not grant a content system.

## What this does NOT decide (Mohamed's gate)
- The **precedence ruling** itself (does erasure trump our quarantine-law ledger keep? which
  option, and the cultural framing). Staged in [docs/OFFBOARDING_PLAY.md](../../docs/OFFBOARDING_PLAY.md);
  the data-handling branch depends on it.
- Whether anything we hold even counts as *personal* data vs. brand data (separate question).

## Build implications if A is chosen (not built here — gated on his ruling)
- A `pdpl_anonymize.py` pass over: taste/pairwise prefs, make_sure_log, gold/kills, attribution,
  decision_queue — keyed by client/entity, asserting **zero residual pointers** (refuse on fail).
- A test fixture proving a known seeded identifier is fully gone post-pass.

## Sources (verified 2026-06)
- [ICLG — Data Protection Laws & Regulations: Saudi Arabia 2025–2026](https://iclg.com/practice-areas/data-protection-laws-and-regulations/saudi-arabia/)
- [DataGuidance — GDPR v. PDPL comparison (PDF)](https://www.dataguidance.com/sites/default/files/gdpr_v_pdpl_v2.pdf)
- [Akin — KSA PDPL & Implementing Regulations: key obligations, rights](https://www.akingump.com/en/insights/alerts/kingdom-of-saudi-arabias-new-personal-data-protection-law-and-implementing-regulations-key-obligations-responsibilities-and-rights)
- [Securiti — Understanding Saudi Arabia's PDPL](https://securiti.ai/saudi-arabia-personal-data-protection-law/)
- [Herbert Smith Freehills Kramer — KSA PDPL: what you need to know](https://www.hsfkramer.com/insights/2023-11/saudi-arabias-personal-data-protection-law-%E2%80%93-what-you-need-to-know)
- [Hala Privacy — PDPL Compliance Guide](https://halaprivacy.com/what-is-pdpl/)

> Evidence rule: each statement above traces to a cited source; primary article numbers
> (Art. 18 destruction/anonymization, Art. 19 security) should be confirmed against the
> official SDAIA text before the ruling is finalized.
