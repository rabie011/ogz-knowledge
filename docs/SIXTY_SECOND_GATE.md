# THE 60-SECOND CLIENT GATE — SPEC v1 (B024, June 12)
*The client-side judging card. Spec now; build after Mohamed's pilot judging proves the format. PROVISIONAL — pending Mohamed.*

## THE PROMISE
A client approves a week of content from their phone in 60 seconds. No dashboards, no logins-with-passwords, no PDFs — one link, post-shaped cards, three taps. The gate IS the product's trust engine: every tap feeds the ledger, the trust ladder, and the crystallize loop.

## 1. BATCH SIZE
≤ 20 cards per gate session (Mohamed's money/attention law applied to clients). Typical weekly batch: 7. The gate refuses to load more than 20 — overflow waits for the next session.

## 2. CARD ANATOMY (the post-unit — what they judge is what publishes)
Top to bottom, phone-first, RTL:
1. **التاريخ + المناسبة** chip (e.g. «الثلاثاء ١٢ مارس · رمضان»)
2. **الصورة** — rendered image (fal) or the shoot-card description until images exist
3. **الكابشن** — standalone, big type, exactly as it will publish
4. *(collapsed)* 💡 الفكرة — the scene, for clients who want the why
- NO scores, NO internal jargon, NO brain names — the client sees a post, not a pipeline.

## 3. THE THREE TAPS
| Tap | Effect |
|---|---|
| **✅ انشر** | `client_approved` event → trust counter +1 → card scheduled |
| **✏️ عدّل** + note (required) | `client_rejected` event with `edit_request` + their words verbatim → regen with their note as constraint **via a DIFFERENT brain** (B111: the retry changes the DOOR, not just the wording — pick-set machinery reused) → returns in next batch |
| **❌ لا** + coded reason (one tap from list) | `client_rejected` + reason_code → feeds crystallize; 2 unexplained لا in a row = stop generating, human calls (rejection-recovery play) |

## 4. REASON CODES (the لا sub-taps — client-friendly Arabic, mapped to crystallize codes)
- «مو إحنا» → off_voice
- «ما يناسب ثقافتنا/عيلتنا» → culture_breach (auto-drafts a red-line candidate)
- «معلومة غلط» → factual_error
- «عادي مرّة / مكرر» → too_generic
- «مو هدفنا الحين» → wrong_goal
- «بس ما عجبني» → unexplained
Every code lands in the ledger with the card's ULID; the crystallize loop watches ×3 patterns across clients.

## 5. TRUST-COUNTER WIRING
`client_approved` (untouched) increments `trust.json` L1 unlock counter (B021/B022 engine — already live). An ✏️ or ❌ resets it. At 10/10 the L1 proposal card fires — to MOHAMED first (he co-signs upgrades), then the client gets the batch-consent ask. `culture_breach` demotes to L0 instantly.

## 6. RELATIONSHIP TO MOHAMED'S PORTAL
Same engine (portal_mini pattern), separate scope:
- **Client key**: per-client token in the URL — sees ONLY their brand's queue (privacy wall: no other client names, ever, anywhere in the payload)
- **Separate queue file**: `clients/{handle}/gate_queue.json` (never the shared decision_queue)
- **Mohamed's view stays god-mode**: his portal can mirror any client's pending gate read-only
- Same answer mechanics: instant save, reverse-with-reason, general note box (their words = voice gold)

## 7. WHAT THE PILOT MUST PROVE FIRST (gates to building this)
1. Mohamed judges batch-19 → the card format survives his taste (or changes)
2. fal images live → cards judge as real posts
3. Khwila answers her 5 questions → first real client exists to hand a key to
4. FLANK-06 publishing ops → «انشر» has something real to trigger

*Build estimate when unlocked: portal_mini fork + queue file + 3 event writers ≈ one session.*
