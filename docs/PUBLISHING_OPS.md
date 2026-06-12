# PUBLISHING OPS — SPEC v1 (FLANK-06 / B170, June 12)
*The «انشر» button's missing floor. Spec now; build behind gates. PROVISIONAL — pending Mohamed.*

## THE GAP THIS CLOSES
The 60-second gate spec gives the client an «انشر» tap (gate #4 listed publishing ops as a
prerequisite) — but today NOTHING exists behind that tap: no credentials home, no scheduler,
no send-window enforcement, no failure play. A tap that publishes nothing is a broken promise;
this spec is the floor under the promise.

## STAGED MATURITY (the repo's own law applied)
**Stage 0 — HUMAN HANDS, MACHINE PREP (buildable today, zero new trust):**
- انشر tap → `clients/{handle}/publish_queue.json` entry: card ULID, caption (exact),
  image path, target channel, computed send window.
- The machine PREPARES: copy-ready caption + image + window on a portal card for the
  human publisher (Mohamed/team). One tap = everything on the clipboard. The HUMAN posts.
- Every human publish confirmed back via the card → `published` event in the ledger
  (feeds trust + the full circle).

**Stage 1 — AUTO-PUBLISH, NARROW (gated):**
- Meta Graph API (Instagram Business) — auto-publish ONLY for clients at trust **L1+**,
  ONLY content the client approved verbatim (no regen between approval and publish).
- Hard pre-send chain, in order: blackout gate (hard block) → etiquette windows (warn)
  → CTA-day check → red-line touch counter. Any block = card back to queue + portal note.

**Stage 2 — SCHEDULER (far gate):** calendar-driven sends from the year map. Not specced
further until Stage 1 survives a month with a real client.

## CREDENTIALS REGISTRY (the part that must NEVER live in git)
- Secrets live OUTSIDE the repo: `~/.ogz_creds/{handle}.env` (chmod 600), one file per client.
- The repo holds only `data/credentials_registry.json`: POINTERS + metadata —
  `{handle, channel, env_file, scopes, confirmer, granted, rotate_by, status}`.
- Registry rule mirrors the assets law: an unregistered credential doesn't exist.
- Token expiry/rotation overdue → urgent portal card (the drift-watch pattern applied to keys).
- Client keys are granted by THE CLIENT (Meta Business handoff) — never harvested from
  shared passwords. No password ever transits chat, portal, or repo.

## SEND-WINDOW POLICY (already mostly built — this wires it)
1. `blackout_gate.check()` — the only HARD block (human-flipped switch).
2. Etiquette warnings (quiet hours, maghrib ±20, jumu'ah window, ramadan inversion).
3. CTA-day awareness: a brand-build-day card never carries an order CTA (cta_allowed —
   live since June 12).

## FAILURE PLAYS (the 2-NOs law applied to sends)
- Publish API failure → ONE retry after 10 min → still failing = STOP, urgent portal card,
  human call. Never loop.
- Token dead → publish_queue freezes for that client + urgent card; queue never silently drops.
- Blackout flips ON mid-queue → ALL queued sends hold; release requires the human who lifted it.

## BUILD-GATES (nothing builds until)
1. First real client credential exists (Khwila's Meta handoff or Mohamed's test account).
2. Trust engine shows the client at L1 (for Stage 1 only; Stage 0 has no trust requirement).
3. Mohamed taps yes on this spec (portal card).
4. Meta app review / API access confirmed on a dev account (reality-check before code).

*Build estimate when gated-open: Stage 0 ≈ one session (queue file + portal card builder
+ ledger writer). Stage 1 ≈ two sessions + Meta review latency.*
