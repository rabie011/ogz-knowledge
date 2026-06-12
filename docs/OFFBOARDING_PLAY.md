# OFFBOARDING PLAY + offboard_client.py SPEC (B153, June 12)
*The lifecycle's last door, designed before the first client walks through it.
Spec-only; build gated. PROVISIONAL — pending Mohamed.*

## TRIGGERS (any one)
1. Client asks to stop (any phrasing — their word is enough).
2. Non-payment past the grace Mohamed sets (B159's sibling number — unset = no auto-trigger).
3. Mohamed's call (culture conflict, scope abuse, his taste).
Never machine-initiated: every offboarding starts with a HUMAN decision logged as
`offboarding_request` (enum live since June 12).

## THE PLAY (graceful by default)
1. **The thank-you** — one WhatsApp message (Stage-0, human-sent): gratitude, zero guilt,
   door explicitly left open («بابنا مفتوح متى ما رجعتو»).
2. **The handover** — they receive THEIR things: approved/published content (it's theirs),
   their brand assets, their gate-link history export. We never hold work hostage.
3. **The close-out receipt** — one page: what ran, what was published, what remains drafted.
   Honest numbers (the unit-economics discipline applied to the goodbye).

## WHAT WE KEEP vs RELEASE
- **Released to client:** published content, approved drafts, their own assets/answers.
- **Kept (quarantine law):** ledgers (append-only history is OURS — it's how the system
  learned), organs (frozen, stamped `offboarded`), unapproved drafts (never delivered).
- **PDPL erasure request:** follows Mohamed's precedence ruling (portal card pending) —
  this spec inherits whatever he rules; no independent policy here.

## offboard_client.py (build spec)
1. Write `offboarding_request` event (human confirmer required — the B156 registry enforces).
2. Freeze: state.json → `offboarded` + freeze stamp; publish/gate queues for the handle
   refuse new entries; render scripts exit on offboarded clients (one check in load_client).
3. Generate the close-out receipt (week_receipt pattern, client-scoped).
4. Export the handover bundle (their releases) to a folder — human delivers it.
5. Write `offboarding_complete` event. NOTHING is deleted — quarantine law absolute
   (subject only to the PDPL ruling).
6. Re-onboarding = normal intake; the frozen organs become priors, freshness laws apply
   (born-expired etc. — myfitness taught us returning truth is old truth).

## BUILD-GATES
1. First real client exists (offboarding needs someone to offboard).
2. Mohamed approves this play (portal card when the deck thins — NOT pushed now, 22 open).
3. PDPL precedence ruled (the data-handling branch depends on it).

*Build estimate when gated-open: one session (state freeze + receipt + bundle export + 2 events).*
