# Post-Publish Veto — Approver-Conflict Takedown Play (B157)

> **Status:** OPERATIONAL PLAY, not a cultural ruling. Persisted by the RABIE orchestra (B157, 2026-06-23).
> Designs the *mechanism* for a post-publish veto. The numbered decisions inside (takedown SLA,
> who-is-pinged, single-vs-primary authority) are **Mohamed's fork** — staged to his portal, not decided here.
> Top-trace: **trust is the currency** — a live conflict with no takedown protocol is exactly the
> "looking unprofessional in a one-shot client moment" the platform exists to prevent.

## The conflict in one line
A post goes **live** — the client-side daughter taps **انشر** (publish) — and a second client
authority, the **mother / owner**, says **لا** (no): take it down. Two approvers, one already-public
post, and the clock running on a public mistake. Who acts, how fast, and how do we make sure it
never re-occurs silently?

## Why this is dangerous (the bedrock, not the symptom)
The symptom is "a post the owner dislikes is live." The **root** is that approval authority on the
client side is **plural and unresolved** — we let a publish happen before the conflict surfaced.
A takedown alone fixes the symptom; the play must also **fix the root** by feeding the conflict back
so the *next* batch routes BOTH authorities before publish, not after.

## The takedown protocol (the mechanism — what the system does)

1. **DETECT.** A veto can arrive by any channel (WhatsApp, a call, a portal tap). The OGZ account
   owner logs it the moment it lands as an `approver_veto` event — `{client, post_id, vetoed_by,
   channel, received_at}` — so the clock is stamped and the trail is auditable (never-lose-anything).

2. **FREEZE.** The instant a veto is logged, the post's slot is marked `veto_frozen`: no further
   amplification (no boosting, no cross-post, no story re-share) touches it while the takedown runs.
   A frozen slot is inert, not yet deleted — deletion waits for step 4 so we never destroy the
   evidence of what was published before it is captured.

3. **PING.** The veto pages the **OGZ account owner for that client** (role defined per pilot — see
   *Fork → B161*). The page carries the post, the screenshot-of-record, and the veto reason. This is
   a one-reusable-card alert (Rule #10), not a flood: one card per `post_id`, auto-closed on takedown.

4. **TAKE DOWN + CAPTURE.** The account owner (a) captures the as-published artifact to the client
   archive (screenshot + caption + publish timestamp), THEN (b) removes the post from the live
   platform, THEN (c) confirms removal with a second look. Order matters: **capture before delete** so
   the archive is whole. The `approver_veto` event is updated `taken_down_at` + `removed_by`.

5. **CONFIRM TO CLIENT.** A short, calm confirmation to the vetoing authority: "تم الحذف" (done,
   removed) + the as-published artifact for their records. No defensiveness, no blame of the daughter —
   the relationship outranks being right.

6. **PREVENT (close the root).** The conflict is written back as a `routing_signal` for that client:
   the next batch's publish gate now requires the **named primary approver** to sign off before any
   post can go live (not just whoever taps first). The conflict that cost one takedown buys a routing
   rule that prevents the next — scar → scar tissue (Rule: rules-from-pain).

## What this play does NOT do
- It does **not** rewrite or re-render the vetoed content (Rule #12 — if content was wrong, the
  machine is fixed and re-run; a veto is a *publish-authority* event, not a content-quality event).
- It does **not** pre-judge whose authority wins. It captures, freezes, takes down on a logged veto,
  and routes the standing question to Mohamed. The cultural weight of "mother overrides daughter"
  is **his ruling**, not the play's.

## Fork points for Mohamed (staged — the play runs on placeholders until he rules)
- **B159 → Takedown SLA.** The target time from veto-logged to post-removed. *No number is asserted
  here* (Rule #9 — a number reaches him verified, and the SLA is his to set against the ping budget).
- **B161 → OGZ account owner per pilot.** Step 3/4 page a *role*; the named person per
  eatjurisha / albaik / myfitness.sa is his to assign.
- **Authority rule.** Is a single veto from *either* client authority sufficient to take down
  (current play default: **yes — any logged veto freezes + removes**, because a public mistake is
  more expensive than an unnecessary takedown), or must the **named primary approver** confirm?
  Gated on **Mohamed's ruling**.

## One-line summary for his card
"Post-publish veto play is built: any logged veto → freeze → page the account owner → capture →
take down → confirm → route the conflict back so the next batch needs the primary approver first.
Three numbers/rules are yours: the takedown SLA (B159), the account owner per client (B161), and
whether any-veto or only-primary-veto takes a post down."
