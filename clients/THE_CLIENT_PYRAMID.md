# THE CLIENT PYRAMID v1.2
*Synthesis of 6 seats: client persona · busy owner · CEO · COO · CCO · skeptic. 2026-06-11. v1.1 repair pass: trust-clause contradiction killed, goal-ratio overwrite deleted, state routing honestly marked stats-assisted, two false on-disk claims purged, open flanks filed (§8).*
*v1.2 — doc-truth pass June 12 (B108): every TO-BUILD claim re-verified on disk and flipped where built; what is still missing stays marked TO-BUILD.*

---

## 1. THE TOP

**The client's repeated YES — he approves the content, it grows his business, and his trust survives every touch.**
Measured ONLY as `client_approved` events repeating in an append-only ledger. Never an AI score, never engagement-as-proxy (the AI-judge scar: +0.08 vs random — Mohamed's 5s and 0s scored identically).

---

## 2. THE TREE

### LAYER 1 — THE SEVEN LAWS OF THE YES
*What the client's eyes check in 10 seconds at every touch. Every node below feeds one law.*

**1. HOMEWORK LAW — "you arrived knowing me."**
- **What:** every first contact opens with a brand mirror — the «اللي فهمناه عن جريشة» block in `clients/eatjurisha/KHWILA_PRESENTATION.md`: products, channels, best post WITH numbers (Eid jurisha: 31 likes / 28 followers), the silence date.
- **Why:** a professional grants one shot only to someone who already read the account. The first proposal demonstrates knowledge, never requests it.
- **Source:** scraped.
- **Diagnose:** count — ≥5 concrete facts, each cross-verifiable against `clients/{handle}/raw/instagram/{date}/`. 0 verifiable facts = not ready to contact.
- **Archive:** `clients/{handle}/presentations/{date}_*.md`, every cited fact traceable to raw **provenance mixin** (`provenance_mixin_v1`).
- **Track:** re-scrape delta changing any cited fact regenerates the mirror; facts >30d old block sending.

**2. VOICE LAW — "it sounds like us, exactly."**
- **What:** a filled, client-CHOSEN `l2_voice` block per **brand_fingerprint_v1**: voice triangle, three love lines, three hate lines, dialect, anti_vocabulary. Statistics describe a voice; love-lines let one WRITE in it.
- **Why:** the `not_saudi` kill is the client's instant walk-away — one MSA-flavored caption on a Najdi family brand spends the whole shot.
- **Source:** scraped (active brands) | client-given (the pick — newborns).
- **Diagnose:** `l2_voice` carries `confirmer:client, confidence:confirmed`. Albaik's hole exactly: `logs/brand_dna/albaik.json` has `dominant_dialect:hijazi` with no confirmer — past description, not future contract. Confirmation test: 10-pair "sounds like you?" — ≥8/10 generated passing.
- **Archive:** `clients/{handle}/profile/fingerprint.json` (validates `brand_fingerprint_v1.schema.json`).
- **Track:** every "not our voice" rejection appends a hate-line SAME DAY; 3 same-direction edits trigger a PROPOSED amendment — inferred never silently overwrites confirmed.

**3. TRUTH LAW — "everything stated is real."**
- **What:** every noun a caption asserts (product, price, channel, branch, hashtag) must resolve to a `truth_pack.json` entry ID. Deterministic lookup — the one automation the AI-judge scar permits (fact resolution, never quality judgment).
- **Why:** founder kill `hallucinated_product_tags` is literal history (#ماك_مع_ججك — "ججك what is this"). One invented fact = trust death in one touch.
- **Source:** scraped proposes → client-given confirms. Never inferred — a guessed price is a lie with confidence.
- **Diagnose:** unresolved noun = HARD BLOCK on the render (block, not warn — silent-failure law). Blocked-reason count per batch.
- **Archive:** resolution results inside each **generation_event_v1** record, append-only.
- **Track:** recurring unresolved nouns become truth-pack candidates or intake questions, weekly.

**4. SAFETY LAW — "it can never embarrass me."**
- **What:** two fences: client red lines verbatim (`red_lines.json` — وجوه العائلة؟ قصة الوالدة؟ أسعار؟) + the ~10 brand-must-override fields of **cultural_spec_v1** pinned at STRICTEST default until the client relaxes; `15_cultural_specs/forbidden_lists/` as hard floor.
- **Why:** asymmetric stakes — conservative miss = one bland post; permissive miss = screenshotable public embarrassment, unrecoverable. "Trust survives every touch" is decided here.
- **Source:** client-given (red lines ONLY) + inferred (sector defaults, strictest reading).
- **Diagnose:** count of fields both unconfirmed AND relaxed = 0, always. Per-field provenance audit before first publish.
- **Archive:** `clients/{handle}/profile/red_lines.json` + `cultural_overrides.json` (validates `cultural_spec_v1.schema.json`, scope `brand:{handle}`, delta-only).
- **Track:** relaxation only via explicit client message logged verbatim as an event; every generated piece records which spec version it was checked against. Both former holes closed 2026-06-12: the rendered image — `scripts/visual_gate_checklist.py` + Mohamed's case_by_case AI-imagery ruling (FLANK-01); the days to go SILENT — `scripts/blackout_gate.py`, wired into both pipelines (FLANK-02).

**5. IDEA LAW — "there's a nameable angle."**
- **What:** founder reward verbatim — the angle must be nameable in ONE sentence before rendering; raw material = real product × real moment × real customer words from `moments_bank.json` + `truth_pack.json`.
- **Why:** the kills that lose the YES with nothing "wrong": `very_normal` ("if any brand could post it, it's dead"), `generic_celebration_template`, `describing_the_photo`. Correct-but-dead never earns a REPEATED yes.
- **Source:** inferred (creation) standing entirely on scraped + client-given truth.
- **Diagnose:** angle sentence present + specific; survives `data/founder_taste.json` kills as written rules (offer energy only on offer occasions). Landing judged by human eyes only.
- **Archive:** angle + resolved ULIDs in **generation_event_v1**; approved angles promoted into `moments_bank.json`.
- **Track:** rejected angle → client taste kill with his words, same day.

**6. GROWTH LAW — "it sells, within my capacity."**
- **What:** content matched to his declared goal ratio (sales vs brand), offers written clean (what/how much/until when/where — reward `clean_clear_offer`), routed to real channels (جاهز/هنقرستيشن from bio), capped by his capacity ceiling (a mother+daughter kitchen absorbs N orders/day, not a viral spike).
- **Why:** "grows his business" is one third of the top. Approval with flat sales churns him by month 3-4; growth that breaks the kitchen grows complaints.
- **Source:** client-given (ratio, capacity) + scraped (channels) + observed (engagement deltas).
- **Diagnose:** content mix deviating >20% from declared ratio = flag before it reaches him; missing capacity number = hard block on push content.
- **Archive:** `clients/{handle}/profile/goals.json` + monthly receipt in `events/receipts.jsonl`.
- **Track:** declared-vs-approved divergence >30% over 30d = a PROPOSED-amendment card raised TO the client; his declared ratio stays law until HIS explicit confirm. A goal he gave us is `confirmed` — inferred never overwrites confirmed, here least of all. No silent adoption, ever.

**7. MEMORY LAW — "I never repeat myself."**
- **What:** every answer, approval, rejection, edit written immediately; ledger grepped before ANY outbound question. CURSOR.md's mid-session rule, client edition: discovered = written.
- **Why:** re-asking a known fact tells a professional the system has no memory — trust dies on the second ask. Memory is why YES #2 costs less than YES #1.
- **Source:** observed-over-time.
- **Diagnose:** trust-budget meter — questions whose answers already existed on disk = logged violations. Target: 0, forever.
- **Archive:** `clients/{handle}/events/*.jsonl` — append-only ULID events (**outcome_event_v1** + CONVENTIONS rule 9).
- **Track:** nightly replay rebuilds derived state; pre-send gate greps profile + ledger before every outbound.

---

### LAYER 2 — THE PROFILE ORGANS
*Ten files under `clients/{handle}/profile/`. This layer IS the albaik fix: stats-only DNA becomes identity. Every field carries the 5-field provenance mixin.*

**1. fingerprint.json** — full **brand_fingerprint_v1** (l1_strategy → l6_production).
- **Why:** feeds Voice + Idea Laws; l1 routes the CD brains. The schema exists and sat unused while stats were built — reuse, never reinvent.
- **Source:** scraped extraction (active) | client pick (newborn) | inferred (l1 strategic read).
- **Diagnose:** field-fill census per layer + confidence histogram. Albaik today: l2 ~60% stats-mappable, l1 = 0%.
- **Archive:** validates via `scripts/validate.py` before any commit; ULID brand ref.
- **Track:** quarterly re-extract diff = drift flag, never silent overwrite; approved posts append evidence.

**2. truth_pack.json** — the ONLY citable facts: products AR/EN, prices, sizes, channels, branches, hours, real_hashtags[], approved story fragments, customer words verbatim.
- **Why:** Truth Law's fence + Idea Law's nouns. `founder_taste.json` already presumes this file ("hashtags ONLY from the truth pack's real list"). BUILT 2026-06-12 — the organ exists for all 3 clients (`clients/{handle}/profile/truth_pack.json`); albaik's CONFIRMED entries still 0/0/0 (candidates only) — client confirms pending (GAP-02).
- **Source:** scraped (bio, captions, website.html) → client-given (prices, menu).
- **Diagnose:** token-resolution over the caption archive; per-entry `ttl_class`; expired offer in copy = truth error, same class as hallucination.
- **Archive:** schema BUILT 2026-06-12 — `12_data_shapes/client_truth_pack_v1.schema.json`. The full census landed with it: client_red_lines, client_goals, client_moments_bank, client_audience_mirror, client_state, client_taste, client_gap_report (+ client_trust, client_competitor_set, client_event) all have schemas on disk — 26 schemas in `12_data_shapes/`, the `validate.py` gate is enforceable for every organ (GAP-11 closed). Every entry cites post shortcode, website, or event ULID.
- **Track:** weekly re-scrape; daily during campaign windows; >7d staleness FAIL-CLOSES offer generation.

**3. cultural_overrides.json** — the CCO's ten fields that can never ride a sector default: gender_presentation, face_visibility_women, head_covering, mixed_gender_scene, modesty_threshold, talent/family visibility, class_signaling, regional+dialect, heritage_gravity, religious_sensitivity. The other ~70 inherit `15_cultural_specs/sector_defaults/` silently by ULID reference.
- **Why:** asking the 70 insults a Saudi professional; skipping the 10 risks the violation that ends everything. The card is the exact boundary.
- **Source:** inferred (strictest sector default) → client-given flips.
- **Diagnose:** field-state census confirmed/inferred/default-conservative; any field at default forces the conservative render branch.
- **Archive:** validates **cultural_spec_v1**, scope `brand:{handle}`, stores only the delta.
- **Track:** client's own posts contradicting an inferred field demote it; upstream spec updates diff-checked; nothing ever auto-relaxes.

**4. red_lines.json** — never_post[] / never_say[] / never_show[] in the client's verbatim words. One source question: gap_report always_ask #2.
- **Why:** the one organ where a wrong default is catastrophic, not bland. Hard blocks at generation, not style preferences.
- **Source:** client-given ONLY — no inference is acceptable for a NEVER.
- **Diagnose:** exists + `confirmer:client`? Absent = system locked strict (no faces, no family, no prices) and NOT production-ready.
- **Archive:** confirmed-by-definition; changes append, old lines quarantined never deleted.
- **Track:** any rejection revealing an unknown NEVER enters same day + logged as a pyramid failure event.

**5. goals.json + business_frame** — content goal ratio, capacity ceiling, launches/branches/seasons, who-speaks, success metric in HIS terms (orders/footfall/DMs).
- **Why:** Growth Law's data. Goals make the YES compound into renewal.
- **Source:** client-given only (always_ask #1, #3, #5).
- **Diagnose:** 5/5 always_ask answered with `confirmer:client`; every goal carries a horizon date — expired = flag.
- **Archive:** answers land HERE the moment they arrive (mid-session save rule), never parked in chat.
- **Track:** season-boundary revisits; launch-signal deltas open a review item, never silent edits.

**6. moments_bank.json** — real evidenced moments: occasions with counts, real scenes (سفرة الجمعة، القدر على النار), customer rituals from comments, upcoming launches.
- **Why:** Idea Law's pantry — `concrete_warm_scene` is the founder's highest reward (herfy eid = 5); concreteness comes from somewhere real.
- **Source:** scraped + inferred (rituals) + client-given (the future).
- **Diagnose:** ≥5 evidenced moments = idea-ready; newborn floor = 2-3 intake answers + **occasion_v1** sector calendar at `experimental`.
- **Archive:** each moment cites shortcodes / comment ids / client quotes.
- **Track:** monthly mining; every APPROVED angle appended back — the bank compounds with every YES.

**7. audience_mirror.json** — customers' actual voice: comment themes TALLIED (complaint/question/praise counts + verbatim examples), never AI-scored for sentiment.
- **Why:** content answering what his audience actually asks gets the fast yes. Complaint-spotting = trust bought without asking (jurisha's delivery complaint → the «قيمة فورية» gift).
- **Source:** scraped + client-given (WhatsApp FAQ when thin — <10 comments fires «وش أكثر سؤال يجيكم واتساب؟», already coded).
- **Diagnose:** corpus size counter (jurisha: 10 = thin → question fired).
- **Archive:** raw `comments.jsonl` immutable; distilled themes with line-range provenance.
- **Track:** monthly comment re-pull; detected complaint pings the client as a service. Known blind spot: this organ hears Instagram only (FLANK-05 — scouted 2026-06-12: Maps actor found, B162; consent ask parked with Mohamed, B165; delivery-app reviews still TO-BUILD).

**8. taste.json** — the client's taste law, EXACT `data/founder_taste.json` shape (kills[]/rewards[]/open_gaps[], every entry quoting the rater + the rated ULID). Born containing one line: "inherits founder_taste.json (universal floor)".
- **Why:** founder law = floor every client inherits; his own ratings = the ceiling. The proven rate-20 mechanism, one file per client.
- **Source:** observed-over-time — human ratings ONLY. No model-generated kill may ever enter this file.
- **Diagnose:** calibration count — client law goes live after 20 ratings; below 20, founder floor governs alone.
- **Archive:** `_meta.source` names every session; updated SAME DAY (the rule whose breaking birthed CURSOR.md).
- **Track:** a kill repeating twice gains a `rule:` field; founder reversals retrain and are logged.

**9. state.json** — newborn / dormant / active-messy / active-strong. Newborn and dormant compute from counts and dates ONLY (genuinely countable). The messy/strong split is honestly marked **STATS-ASSISTED**: dominant register/tone/dialect are model-derived stats from `derived/voice_stats` — so the split lands as a PROPOSAL with `confidence:inferred`, corroborated by cadence variance (timestamps, pure arithmetic), and a HUMAN confirms it before any play routes on it.
- **Why:** state routes the entire intake and proposal style (see §3). Counts and dates may gate alone; model-derived dominance may only PROPOSE. Calling the whole table "zero AI judgment" was the +0.08 scar hiding in the foundation row — named, not papered over.
- **Source:** observed (manifest counts, post timestamps) + inferred (voice_stats dominance — messy/strong split only).
- **Diagnose:** thresholds with rule-trace; 0 posts = ERROR until proven empty (`client_intake.py` line 92), so a scrape failure can never misdiagnose an active brand as newborn. Unconfirmed messy/strong proposal = the conservative MESSY play until the human click.
- **Archive:** `state.json` with the exact input numbers cited + the confirming human event for any messy/strong ruling.
- **Track:** recomputed every re-scrape; transitions are appended events — dormant→active after our return plan is itself an outcome metric.

**10. derived/voice_stats.json** — the statistical fingerprint (what `logs/brand_dna/albaik.json` is today), relocated to its honest place: a DERIVED signal, not the DNA.
- **Why:** stats may STEER style, feed drift detection, and PROPOSE the messy/strong state split (§3 — human-confirmed before routing); they may never ASSERT identity or gate content (health_score C blocks nothing).
- **Source:** inferred (computed from raw).
- **Diagnose:** validator rejects any fingerprint field whose provenance cites a stats file instead of raw evidence or a client event.
- **Archive:** under `derived/` — safe to delete and rebuild; that reproducibility is the test of correct placement.
- **Track:** recomputed after every re-extraction; events outrank statistics on conflict.

---

### LAYER 3 — THE MACHINES
*One clean extraction moment, ≤5+2 questions, propose-don't-interrogate. Same machines fill the tree top-down (corpus) and bottom-up (real client).*

**1. ONE-SHOT INTAKE** — `scripts/client_intake.py` AS-IS: 5 surfaces (profile/posts/comments/media/website), raw-first, immutable, counts verified.
- **Why:** everything taken from links is one less question from his trust budget. Proven live: jurisha 8/8 posts, 100% coverage, 0 warnings.
- **Source:** scraped.
- **Diagnose:** `manifest.json` ships its own diagnosis — coverage <90% = investigate; ZERO POSTS = error; empty profile = stop. Any warning blocks profile-building until a human resolves it.
- **Archive:** `clients/{handle}/raw/instagram/{date}/` + `manifest.json` with provenance block; new dates = new folders, never overwritten.
- **Track:** monthly disclosed light refresh into new dated folders; deltas feed drift watch.

**2. GAP REPORT = THE ONLY QUESTIONS** — `gap_report.json`: 5 always_ask (goals / red lines / who-speaks / USP / offer ratio) + extraction-derived extras (jurisha: phone-archive photos), hard cap ~7. Nothing outside this file may EVER be asked.
- **Why:** the contract that caps interrogation — a question is legitimate only where links provably could NOT answer.
- **Source:** inferred (derived from what scraping failed to answer).
- **Diagnose:** pre-send audit — any question answerable from the 5 surfaces (jurisha's channels ARE in her bio) = logged defect. Question count >7 fails review.
- **Archive:** answers projected into target organ files the moment they arrive, `confirmer:client`; the gap file keeps only open items.
- **Track:** open-list size = onboarding burndown; unanswered items resurface ONE per natural touchpoint, never a form; a re-ask = trust violation event.

**3. SECTOR INHERITANCE SPINE** — sector baselines (**sector_baseline_v1**), ~70/80 cultural fields, **occasion_v1** calendar inherited from ogz-knowledge as `inferred`.
- **Why:** why the first proposal reads native (gulf coffee, Friday sofra, Najdi register) with zero questions spent.
- **Source:** inferred from the corpus + 100 benchmark accounts — NEVER other clients' private data.
- **Diagnose:** inheritance audit — every inherited field keeps `scope:sector:*`; borrowed-fields list = the standing to-confirm queue, so defaults never silently become his position.
- **Archive:** by ULID reference into the repo; client folder stores only its override delta (brand isolation, rule 6).
- **Track:** upstream updates propagate as flagged diffs; promotion to confirmed requires client action or Cultural Advisor — never AI.

**4. VOICE PATH ROUTER** — state-gated: ACTIVE-STRONG → extract l2_voice from their real captions, then 10-pair eyes test; NEWBORN → birth ritual (`voice_birth_week.json` exactly as run: A بنت نجد الدافئة / B الحرفية الأنيقة / C خفيفة الدم — client picks, pick becomes law); ACTIVE-MESSY → best-20%-of-posts persona + 2 designed alternatives → mini birth (mess = candidates, never law); DORMANT → extract but demote every factual item to "still true?".
- **Why:** statistics on 8 posts is confident fiction; a birth ritual on 164 observations is an insult. Routing protects the one shot both ways.
- **Source:** scraped (extraction) | client-given (every final pick).
- **Diagnose:** routing defect check — newborn given extraction or strong brand given birth = bug. Birth confirmed when pick + first week approved.
- **Archive:** `voice_birth_week.json` kept forever as birth certificate (incl. RABIE's 2/5 truth-error regeneration of C); losers quarantined, never deleted.
- **Track:** post-birth rejections feed hate-lines; quarterly check-in ONLY on ≥3 same-direction corrections.

**5. PROFILE COMPOSER** — `scripts/build_brand_profile.py` (BUILT 2026-06-12 — composed all 3 client profiles): one deterministic script composing all organs from raw + `derived/voice_stats` + sector defaults + the pick + the answers. The SAME script backfills albaik with everything `confidence:inferred`.
- **Why:** the pyramid is only real when one script materializes it for ANY brand — built top-down, runs bottom-up.
- **Source:** inferred.
- **Diagnose:** output validates via `scripts/validate.py` (exit 0 or not done — a real gate since 2026-06-12: all organ schemas on disk, GAP-11 closed); the completeness report IS the next gap_report — the albaik hole becomes a field-count, not a vibe.
- **Archive:** script saved in `scripts/` (save-your-generators law); deterministic → reproducible from raw + events.
- **Track:** re-composed after every event batch; every backfilled brand becomes a frozen regression fixture — template changes must never reduce filled-%.

**6. THE ANGLE FORGE** — gated creation: (1) moment × product × occasion from the organs → (2) ONE-sentence angle → (3) deterministic gates: noun resolution (Truth), red-line + override scan (Safety), offer-energy/occasion match (kill #4), hashtags only from real_hashtags → (4) render (caption + visual via the 88 chains — open_gap `image_pairing`: caption is HALF a post; the rendered half gained its deterministic gate 2026-06-12: `scripts/visual_gate_checklist.py` + Mohamed's case_by_case AI-imagery ruling, FLANK-01 closed) → (5) human eyes.
- **Why:** where the YES is manufactured. Every founder kill is a gate; every reward a target. No gate scores "quality" by model.
- **Source:** inferred, standing entirely on client-given + scraped truth.
- **Diagnose:** per-generation gate log with enumerable reasons; weekly failure-reason histogram shows which organ is starving.
- **Archive:** **generation_event_v1** append-only, carrying angle + resolved ULIDs.
- **Track:** approved angle → moments_bank; rejected angle → taste kill, same day.

**7. THE 60-SECOND GATE** — delivery surface: ≤20 candidates per batch, one-tap verdicts (انشر / لا / عدّل) + optional one-line reason, WhatsApp-friction, his dialect. The founder's proven rate-20 mechanic, productized for the client.
- **Why:** the YES must cost seconds, not meetings. An undone gate is an unearned YES. Validated on the founder (sessions complete, avg 2.95 baseline). Mohamed's own channel BUILT 2026-06-12 — the decision portal, `api/portal_mini.py` (key-gated, answer/reverse, rulings landing in `data/mohamed_answers.jsonl`). The CLIENT edition still does not exist (B024-B028, delivery channel = Mohamed's pick): the single highest-leverage missing piece. TO-BUILD.
- **Source:** client-given (the verdicts).
- **Diagnose:** median seconds-per-verdict + batch completion rate; ratio of choice-questions to open-questions in any outbound ≥4:1.
- **Archive:** every tap = one **outcome_event_v1** in `events/verdicts.jsonl`, reason verbatim.
- **Track:** completion-rate trend = the LEADING churn indicator — a client who stops rating is leaving before he says so.

---

### LAYER 4 — BEDROCK: THE REPEAT ENGINE
*Below this layer there is nothing but client eyes and raw facts. The layer albaik's DNA never had.*

**1. THE EVENT LEDGER** — `clients/{handle}/events/*.jsonl`: append-only ULID events for every touch (presentation_sent, intake_answer, client_approved, client_rejected+reason, client_edited, redline_relaxed, state_transition, outcome). Current truth = replay, never a mutable number.
- **Why:** "repeated yes" is literally a property of this event series. Also the corpus replayed when client #50 arrives.
- **Source:** observed-over-time.
- **Diagnose:** every send reaches a terminal event; an orphaned send = process bug; nightly replay must reproduce profile state exactly. A ledger gap is THE broken rule that triggered this design.
- **Archive:** **outcome_event_v1** / **generation_event_v1**, corrections as new events (rule 9), quarantine-not-delete (rule 8); PDPL alignment: the erasure-vs-quarantine precedence awaits Mohamed's ruling (staged on the portal June 12) — until ruled, no PDPL-compatibility is CLAIMED, only designed-for.
- **Track:** it IS the tracking substrate — taste, trust meter, state, churn, priors are all derived views. Commercial event types landed 2026-06-12: `payment_received` / `renewal` / `scope_change` live in `client_event_v1.schema.json`; pricing pinned by Mohamed 700/2650/9000 SAR (FLANK-03 closed at the schema layer — terms doc still draft).

**2. PROVENANCE PROMOTION LADDER** — every field in every organ on one ladder: default-conservative → inferred (≥3 feed evidences) → confirmed (client's word, or 3 approved posts using the field). Demotion instant on contradiction. Promotions/demotions are themselves events.
- **Why:** we always know WHY we believe each fact — never stating a guess with the voice of knowledge. Epistemics = the trust clause, mechanized.
- **Source:** the ladder records which (scraped / client-given / inferred / observed), per field.
- **Diagnose:** profile health census — % per rung per organ; the culture-safe and truth-safe gates read this directly.
- **Archive:** in-field **provenance_mixin_v1** blocks; CONVENTIONS confidence enum reused verbatim.
- **Track:** a field stuck at `inferred` 90 days under production use becomes a parked one-question ask.

**3. FRESHNESS & DRIFT WATCH** — TTL clocks per organ + monthly disclosed light re-scrape (profile + last 12 posts), diffed against prior dated folders. Expiry drops a task file into `~/agents/queue/pending/` — the orchestrator daemon owns execution; Mira reports expiries.
- **Why:** a YES earned in June dies in Ramadan if the profile froze. A stale truth pack produces a confident lie — the fastest trust-killer.
- **Source:** observed (clocks over event + provenance timestamps).
- **Diagnose:** days-since-verified per organ; stale organ blocks or flags dependent proposals. Zero diffs for 6 months on an ACTIVE client = OUR scrape is broken (silent-failure law, applied to monitoring).
- **Archive:** immutable dated `raw/` folders + `deltas/{date}.json`; diffs land as inbox proposals, NEVER auto-applied (One Write Path).
- **Track:** a delta changing any fact cited in a sent mirror forces regeneration; giant diff triggers state reclassification.

**4. COMPOUNDING WRITEBACK** — nightly replay of new verdicts into derived state: confidences promoted, taste kills extended, truth entries confirmed. Includes the **edit diff-miner** (proposed-vs-published diffs by shortcode: 3 repeated diff patterns = field update — his fixes are his taste in his own words, zero questions spent) and the **trust ladder** (BUILT 2026-06-12 — `scripts/trust_ladder.py` replay engine + `clients/{handle}/profile/trust.json`, all 3 clients at L0; the covering-click audit B023 NOT yet live) (L0 every piece individually approved → L1 BATCH consent: after 10 unchanged approvals, evergreen ships as pre-approved batches — he clicks once PER BATCH on its full contents BEFORE anything posts, every published piece traceable to that click; no standing "auto" grant exists at any level, because pass authority = client or Mohamed click, NOTHING else (§5) → L2 offers join batch approval with a 24h preview window before his batch click; silence NEVER advances, rejection drops one level).
- **Why:** the literal mechanism by which every approval teaches the system — without it month 12 costs what month 1 cost and the economics never bend.
- **Source:** observed (replay of client-given events).
- **Diagnose:** fields-promoted-per-month; zero promotions in 60 days on an active client = the loop is broken, alarm. Approval-rate curve must trend UP. Audit: every published piece resolves to a covering client click — uncovered publishes must count 0, forever.
- **Archive:** events append-only; derived state recomputed by replay — every promotion auditable to the verdicts that earned it.
- **Track:** monthly report doubles as the renewal artifact: "the system now knows N confirmed things it didn't know in month 1."

**5. OUTCOME TRUTH — THE BUSINESS RECEIPT** — per published piece: scraped countables (likes, comments, follower delta at T+7d) + ONE monthly button («هل حسّيتي بفرق بالطلبات؟ أكثر / نفس الشي / أقل»). Never AI-estimated impact.
- **Why:** approval without growth eventually kills the yes anyway. The receipt is what he forwards to his partner to justify renewal.
- **Source:** observed (countables) + client-given (sales testimony — only he holds it).
- **Diagnose:** outcome events present per piece; no outcome 30 days after publishing = flagged blind spot, never assumed success (0-results law, extended to results). Flat receipts 2 months = human review.
- **Archive:** `events/receipts.jsonl`, referencing the generation ULID, vs HIS OWN baseline only — never cross-brand.
- **Track:** occasion-vs-outcome tallies update his calendar priors and roll up anonymized into sector baselines.

**6. SECTOR PRIOR LIBRARY** — monthly aggregation of client-CONFIRMED values (anonymized, n≥3 brands agreeing) proposed as PRs into `15_cultural_specs/` + sector defaults. Client rejections revealing a general law become kill candidates for `data/founder_taste.json`.
- **Why:** Mohamed's rule closed — built top-down to learn, runs bottom-up: client #200 in f_and_b gets a draft sharpened by 199 confirmations; his gap interview shrinks from 7 toward 3.
- **Source:** inferred (aggregated from client-given) — promotion ALWAYS via human-merged PR (rules 7 + 11 + the scar forbid auto-promotion).
- **Diagnose:** two trend lines per sector: questions-per-new-client (must fall), prior hit-rate (must rise). Flat after 20 clients = aggregation not reaching the drafter.
- **Archive:** One Write Path PRs; each prior counts its contributing brands.
- **Track:** a default overridden 3× in a row by new clients demotes back to experimental — priors are alive, not carved. Delivered to Mohamed as ≤5 yes/no cards quarterly.

**7. SCALE INSTRUMENTS** — unit-economics ledger (`logs/unit_economics/{month}.jsonl`: Apify cost, questions asked, human minutes, days-to-first-YES, cost-per-YES) + churn-risk dashboard (verdict latency rising, completion falling, days-silent, flat receipts — thresholded by STATE; all arithmetic over events, no AI sentiment).
- **Why:** 1000 clients is a business only if cost-per-YES falls; quiet churn (rubber-stamp approvals: variance→0, latency→0) is invisible without instruments.
- **Source:** observed (telemetry + event derivations).
- **Diagnose:** cost-per-YES rising 2 consecutive months = drift or broken writeback, both findable; dashboard's own hit-rate tracked (% of churned clients red ≥30d before leaving).
- **Archive:** derived views recomputed from events; fired alerts appended to `events/alerts.jsonl`.
- **Track:** weekly recompute; red client auto-creates a human-touch task naming the indicator that fired.

---

## 3. THE STATES

*NEWBORN and DORMANT are deterministic from `manifest.json` counts and dates — genuinely countable, zero judgment. The MESSY↔STRONG split is NOT: dominant register/tone/dialect are model-derived stats from `derived/voice_stats` — the very file forbidden from gating content. So it is honestly marked: countables (post count, cadence variance, dates) gate alone; stats only PROPOSE the split, and a HUMAN confirms before the play fires. The +0.08 scar applies to classifiers too.*

| State | Threshold | The play it triggers | Standing example |
|---|---|---|---|
| **NEWBORN** | posts < 30 — **countable** | Voice BIRTH (3 personas, client picks), sector defaults carry the load, 2-3 moments from intake. Stats engine FORBIDDEN — 8 posts of statistics is confident fiction. | jurisha — 8 posts, 28 followers |
| **DORMANT** | last post > 90d — **countable** | ONE question first («وش تغير من يوم وقفتو؟»), revival arc not continuation; every stored fact demoted to "still true?"; voice extracted but flagged historical. | jurisha is ALSO this (silent since Apr 20) → newborn-dormant = birth + return plan |
| **ACTIVE-MESSY** | ≥30 posts + high cadence variance — **countable**; no dominant register/tone >50% — **stats-PROPOSED, human-confirmed** | NEVER average the mess into a fake voice — surface inconsistency as a finding + mini birth (best-20% persona + 2 designed). | the routing check albaik must pass: `dominant_register: None` but tone/dialect dominant |
| **ACTIVE-STRONG** | ≥30 posts + steady cadence — **countable**; dominant dialect+tone present — **stats-PROPOSED, human-confirmed** | Mirror-and-confirm, near-zero questions. Extraction = law candidate; identity holes remain client-only. Interrogating him insults the public record. | albaik — 164 obs, hijazi, celebratory |

Transitions are appended events. An unconfirmed messy/strong proposal routes the conservative MESSY play until the human click. dormant→active on OUR watch = a WIN the receipt cites; active→dormant on OUR watch = churn alarm.

---

## 4. ONLY THE CLIENT CAN GIVE

*Merged, deduplicated, ordered by danger-of-defaulting (wrong default = how dead).*

1. **RED LINES** — the never-publish list (وجوه العائلة؟ قصة الوالدة؟ أسعار؟). Strictest until explicitly relaxed; nothing may relax it for him. (Deadly default.)
2. **THE ~10 CULTURAL RELAXATIONS** — face visibility, mixed-gender, modesty, family visibility... client-only, logged verbatim. (Deadly default.)
3. **THE YES ITSELF + every rejection reason** — the only quality ground truth that exists (+0.08 scar); no node may manufacture, predict, or proxy it. (Cannot be defaulted at all.)
4. **GROUND-TRUTH FACTS** — menu, prices as HE spells them, live ordering channels, the handle itself confirmed. (Defaulted = confident lie.)
5. **WHO SPEAKS + THE PICK** — daughter / family / neutral; which of A/B/C is "them". Identity is chosen, not extracted. (Defaulted = not_saudi-grade kill.)
6. **CAPACITY CEILING** — orders/day the kitchen absorbs; growth above it damages the business the top serves. (Defaulted = viral push breaks a 2-woman kitchen.)
7. **CONTENT GOAL RATIO** — sales vs brand, % offers tolerated; gates all offer-energy. (Defaulted = poetry drift or discount spam.)
8. **CONSENT SCOPE** — what we may re-scrape, which media we may reuse, what stays private. (Defaulted = the "how did you know that?" moment.)
9. **FORWARD CALENDAR FACTS** — launches, branches, his private seasons; no scrape sees the future. (Defaulted = missed moments, survivable.)
10. **USP IN HIS OWN WORDS** — his phrasing is voice raw material, feeds `contrarian_belief`. (Defaulted = generic, survivable.)
11. **OUTCOME TESTIMONY** — whether orders actually moved; we scrape likes, only he knows sales. (Defaulted = flying blind on renewal.)

---

## 5. THE IMMUNE SYSTEM

*The skeptic's gates, placed at their layers. AI may KILL; AI may never PASS.*

**@ Layer 1 — verdict gates**
- **HUMAN-VERDICT GATE:** automated checks only block (kills, truth violations, forbidden lists); pass authority = client or Mohamed click, nothing else — including batch publishing: every published piece must trace to an explicit covering client click (the L1 batch consent in Layer 4 §4; no standing auto-grant exists). Banned from approval logic: `health_score` (0.616 describes a corpus, judges nothing), `engagement_profile`, any critic score. Audit branch added to `scripts/verify_ship_ready.py`; score-raises-confidence count must be 0; uncovered-publish count must be 0.
- **REJECTION RECOVERY PLAY:** every proposal ships as 3 NAMED angles (the voice_birth pattern). NO → one-tap coded reason (culture_breach | off_voice | wrong_goal | too_generic | factual_error | unexplained) → ONE recovery round from surviving angles. Two unexplained NOs = stop generating, human calls. Healthy = yes ≤2 rounds on ≥80%. culture_breach immediately writes a red-line candidate.

**@ Layer 2 — truth gates**
- **INFERENCE QUARANTINE:** `scripts/fingerprint_status.py` (BUILT 2026-06-12, modeled on verify_ship_ready) renders voice GREEN / identity RED side-by-side — so 164 observations can never again impersonate completeness. Identity fields (who-speaks, USP, goals, red lines) may not be inferred at all.
- **CITATION GATE:** uncited claim = hard block; every hashtag from `real_hashtags[]` only (the #ماك_مع_ججك fence, structural not behavioral).

**@ Layer 3 — intake gates**
- **IDENTITY CROSS-CHECK:** handle↔brand verification (verified badge OR bio URL matches client domain OR written confirmation) + fan-account check BEFORE anything downstream runs (`manifest.surfaces.profile.identity_check`). Big Saudi brands have fan accounts; a wrong root poisons every node above.
- **PRIVACY WALL:** never DMs, private accounts, follower lists, commenter identities (aggregate only, never quoted back), deleted posts, undisclosed re-scrapes. Every scrape appends a disclosure entry to manifest; quarterly provenance audit of all `clients/` trees.
- **DEADLY-DEFAULTS TABLE — BUILT 2026-06-12 (B105):** `15_cultural_specs/defaults/brand_override_defaults_v1.yaml` — 14 rows, 12 deadly, parked rulings included. Deadly-vs-survivable pairs as written: face_visibility → `never`; mixed_gender → family-only; family-voice («أمي جابت...») OFF (parked, Mohamed's call); masculinity framing OFF (parked); offers on emotional occasions OFF; prices OFF until truth-confirmed; comment-quoting OFF. Any deadly field running non-conservative without a client event = release block — ENFORCED 2026-06-12 (B106): `scripts/deadly_defaults_gate.py`, exit 1 names the field, wired into `verify_ship_ready.py` + `full_circle_test.py`.

**@ Layer 4 — rot and memory gates**
- **TTL REGISTRY:** offers/prices 7d · products 30d · channels 60d · bio 90d · voice stats 180d · red lines NEVER auto-expire but re-confirm every 5th touch («لسه ما ننشر وجوه العائلة — صح؟», one tap). Past-TTL auto-downgrades confirmed→inferred → uncitable by the citation gate. Gates compose; no human has to remember. Hole closed 2026-06-12 (B071): `scripts/staleness_report.py` BUILT with season-scoped truth — a fact valid in one season is uncitable in another regardless of age (the Shawwal-price-dies-in-Ramadan test) — plus the born-expired law for deep-dormant scrapes. Expired-but-cited count must be 0.
- **DRIFT-WATCH ALARM:** zero diffs 6 months on an active client = our monitoring broke, not their brand froze.
- **CRYSTALLIZE LOOP:** weekly pass over all `events/` — any coded reason ×3 across clients drafts a kill/default change, queued to Mohamed as a 60-second yes/no. Tripwire: `founder_taste.json _meta` >2 weeks behind the last session = the loop itself is broken. (B101 closed 2026-06-20: RABIE's 2/5 truth-error ruling lives as a `voice_rating` ledger event in `clients/eatjurisha/events/ledger.jsonl`, guarded by `scripts/tests/test_b101_voice_c_regeneration_logged.py` so it can never regress to a bare note — events first, notes never.)
- **PARKED-RULINGS LEDGER:** family_voice_rule + masculinity_framing stay in open_gaps; generation routes AROUND parked themes; leakage count must be 0. Work never blocks on a ruling; a machine ruling on a parked cultural question is the scar in new clothes.

---

## 6. BOTTOM-UP REPLAY — jurisha fills the tree

*The same tree, filled from the bottom by a real client. Every step verified on disk.*

1. **Evidence floor (L3→bedrock):** intake ran 2026-06-11 — 8/8 posts (100% coverage), 28 followers, 10 comments, 8 media saved, linktree captured (176,444 bytes), **0 warnings** → `clients/eatjurisha/raw/` + `manifest.json`, provenance `confirmer:pending_client`.
2. **State computed:** 8 posts (<30) + silent since Apr 20 (>90d... compound) → **NEWBORN-DORMANT** → routes birth ritual + return-plan framing. Stats engine forbidden. (Pure countables — no stats-assisted split needed at this size.)
3. **Sector spine fills silently:** ~70 cultural fields, f_and_b baseline, occasion calendar — all `scope:sector:*`, strictest reading.
4. **Voice path = BIRTH:** 3 personas proposed in `voice_birth_week.json` (A بنت نجد الدافئة / B الحرفية الأنيقة / C خفيفة الدم); C regenerated after RABIE's 2/5 truth-error rating — logged as a `voice_rating` ledger event (B101, 2026-06-20) and pinned by a regression test.
5. **Gap report generated:** exactly 5 always_ask + 1 extraction-derived (thin feed → phone-archive photos). Channels NOT asked — جاهز/هنقرستيشن already in her bio. Comments=10 → WhatsApp question armed.
6. **The mirror sent:** `KHWILA_PRESENTATION.md` — homework block (Eid post 31/28, silence date), 3 voices, 5 questions, one gift (the delivery complaint found in comments → «قيمة فورية»). Parked awaiting Mohamed's approval.
7. **Her answers land same-day:** red lines → `red_lines.json` (confirmed); goals/capacity/ratio → `goals.json`; who-speaks + USP → fingerprint l1/l2. Each = an `intake_answer` event with verbatim Arabic.
8. **Her pick becomes law:** chosen persona merges into `fingerprint.json l2_voice`, `confirmer:client`; losers quarantined; birth certificate kept.
9. **First 3-post return week:** Angle Forge (nouns resolve to her truth pack: جريشة فردي/عائلي، رز كابلي، جاهز، هنقرستيشن، الرياض) → 60-second gate → verdicts append to `events/` → first taste.json entries.
10. **Outcomes close the loop:** T+7d countables + her monthly button → receipts; her confirmed answers flow (anonymized, n≥3) toward f_and_b priors — making client #2's pyramid need fewer questions.

**Pass numbers (live half):** reply ≤48h · picks a voice · answers ≥4/5 in one ~10-min sitting · first week YES with ≤1 edit · 0 cultural rejections · every reply in `events/` same day.

---

## 7. FIRST EYES-TEST — the albaik dry-run

*Fill the same pyramid from the existing corpus (164 observations, no client). Every hole = a gap card. Numbers verified on disk 2026-06-11.*

### The fill (what the corpus gives today)

| Organ | Fillable now | Measured |
|---|---|---|
| `state.json` | proposal only | 164 obs (countable) + dialect hijazi, tone celebratory (stats-PROPOSED) → ACTIVE-STRONG **pending the human checkpoint** (§3). Borderline on disk: `dominant_register: None` — cadence variance (countable) corroborates; until a human confirms, routes the conservative MESSY play |
| `derived/voice_stats.json` | YES — relocate `logs/brand_dna/albaik.json` as-is | health 0.616/C, compliance green/0, heritage split modern .555 / blended .25 / heritage .11, evergreen ratio 0.122 |
| `fingerprint.json` l2_voice | ~60% from stats + caption mining | dialect ✓, tone ✓; love-lines: 5 candidates in top_phrases; hate-lines 0/3, anti_vocabulary 0 |
| `fingerprint.json` l3_visual | YES from stats | white_light 97 / warm_red 95, setting restaurant 70, video 74/image 52/carousel 38, lifestyle_integrated, character_presence 0.0 |
| `fingerprint.json` l1_strategy | NO | 0/3 (contrarian_belief, positioning, CD routing) — CCO read + founder confirm |
| `truth_pack.json` | candidates only | **0 real products, 0 prices, 0 channels.** The hole is on disk: existing `data/truth_packs/albaik__daily_post.json` has `real_products` filled with **8 hashtags** (#البيك، #جدة…) — the field itself documents the disease. Minable: f_and_b_beverage 110 obs; «ساندوتش وبرجر فيليه» named in top_phrases |
| `cultural_overrides.json` | proposals only | 0/10 confirmed; all pinned strictest; 1 strong feed evidence: character_presence_rate 0.0 → face fields proposable at `inferred` citing 164 obs |
| `red_lines.json` | **NO — cannot exist without the client** | 0 lines. 164 observations contain zero of this |
| `goals.json` | NO | 0/5 always_ask answered |
| `moments_bank.json` | YES | 5 evidenced moments ≥ the idea-ready bar: evergreen 20, national_day 18, ramadan 9, jeddah_season 9, eid_al_adha 7 |
| `taste.json` | floor only | inherits founder_taste (8 kills / 4 rewards); client calibration 0/20 |
| `events/` | empty | 0 verdicts. Real-client verdict count, whole company: **0** |

### The gap cards

- **GAP-01 — red_lines.json absent (0 lines).** Client-only. System locks strict; albaik is NOT production-ready regardless of corpus size. The richest profile lies loudest.
- **GAP-02 — truth pack CONFIRMED entries still 0/0/0 (products/prices/channels).** Schema half closed: `client_truth_pack_v1.schema.json` BUILT 2026-06-12 (26 schemas now in `12_data_shapes/`), and the organ exists with bio-mined candidates. Still open: mine the 110 beverage obs into `inferred` candidates + client confirms — nothing confirmed yet.
- **GAP-03 — identity layer 0%:** l1_strategy 0/3, love-lines 0/3 confirmed, hate-lines 0/3, who-speaks unknown, USP unknown. fingerprint_status must show **voice GREEN / identity RED**, not defaulted-confirmed.
- **GAP-04 — cultural overrides 0/10 confirmed.** Survivable (strictest defaults govern) but every relaxation parks until a client or Cultural Advisor event.
- **GAP-05 — goals 0/5.** No receipt possible; "flying blind" flag on.
- **GAP-06 — verdict loop half-built (2026-06-12):** ledgers are no longer empty — albaik 18 / eatjurisha 19 / myfitness 13 events (version_verdict, compare_verdict, batch_rating, intake_answer, red_line_added…) — but every verdict is founder/internal; real-CLIENT verdict count, whole company: still **0**. Mohamed's decision portal exists (`api/portal_mini.py`); the 60-second CLIENT gate does not (B024-B028) — highest-leverage missing machine. TO-BUILD.
- **GAP-07 — identity cross-check never run.** Albaik handle came in as a benchmark; fan-account risk for big Saudi brands; `identity_check` block missing from manifest pattern.
- **GAP-08 — CLOSED 2026-06-12:** `scripts/build_brand_profile.py` + `scripts/fingerprint_status.py` both BUILT and on disk; composer ran on all 3 clients.
- **GAP-09 — CLOSED 2026-06-12:** albaik comment corpus counted — 161 comments in `profile/audience_mirror.json` (delivery-app reviews still NOT read, FLANK-05).
- **GAP-10 — consent scope:** albaik is a benchmark, not a client. Dry-run is INTERNAL ONLY; nothing client-facing ships from it.
- **GAP-11 — CLOSED 2026-06-12: schema coverage 10/10 organs.** All eight missing schemas landed in `12_data_shapes/` (client_truth_pack_v1, client_red_lines_v1, client_goals_v1, client_moments_bank_v1, client_audience_mirror_v1, client_state_v1, client_taste_v1, client_gap_report_v1 — plus client_trust_v1, client_competitor_set_v1, client_event_v1; 26 schemas total). The `validate.py` "exit 0 or not done" gate is now enforceable for every organ.

### The eyes-test protocol (one week, no AI judge anywhere)

1. **Backfill:** build the composer, run it on albaik's corpus + `derived/voice_stats` + f_and_b defaults. PASS = ≥70% of brand_fingerprint_v1 fields filled with per-field provenance, `validate.py` exit 0, gap list collapses to ≤7 yes/no-able questions, 10 sampled facts each trace to a real raw source.
2. **Hostile rehearsal:** Mohamed plays the owner — rejects round 1 as «مو احنا» withholding the reason, answers 2/5 questions, corrects one asserted fact. PASS = round 2 reaches YES via coded-reason recovery; every NO/code/correction lands in `events/`; the 3 unanswered identity fields still read EMPTY.
3. **Blind rate-20:** 10 captions from the pyramid profile vs 10 from today's stats-only DNA, shuffled, Mohamed rates 0-5 with words. PASS = pyramid wins the session average, **0 unresolved nouns** (no invented products/hashtags), ≥3 pyramid captions at 4+.
4. **Same week, opposite direction:** the identical tree on jurisha (newborn path, §6 numbers). Same template fills from a 164-obs giant top-down AND an 8-post newborn bottom-up — or the failing node is named by its own diagnose metric.

**Scorecard delta = the proof:** identity 0% → measured %, products 0 → counted entries, red lines absent → strict card present + 1 client question pending. Anything under 4/5 by Mohamed's eyes root-hunts the failing gate before any layer is built further.

---

## 8. THE OPEN FLANKS — named gaps no seat caught

*Design-level holes filed as standing gap cards. None blocks the eyes-test; each blocks "production-ready." Two are trust-killers (FLANK-01, FLANK-02); none may be closed by AI judgment. Status pass 2026-06-12 (B108): 01, 02 and 04 closed; 03 closed at the schema layer; 05 scouted; 06 still unbuilt.*

- **FLANK-01 — THE VISUAL HALF IS UNGATED (trust-killer).** Every Truth/Safety gate in this document scans TEXT; face_visibility, modesty, mixed_gender, and family-visibility violations actually live in the rendered IMAGE (the 88 chains), with no deterministic check between render and human eyes. Worse, an undecided Truth Law question: an AI-generated photo of "her jurisha" is not her jurisha — a customer who orders off a beautiful synthetic image and receives the real product is the Truth Law violated in pixels. `open_gap image_pairing` admits captions are half a post; the immune system currently guards only that half. CLOSED 2026-06-12: `scripts/visual_gate_checklist.py` BUILT — deterministic checklist between render and human eyes; the real-vs-synthetic-product question RULED by Mohamed: case_by_case (`data/mohamed_answers.jsonl`, ruling_ai_imagery) — human eyes remain the final visual verdict, never AI.
- **FLANK-02 — NO NEGATIVE-SPACE CALENDAR (trust-killer).** Every calendar node says when to POST; nothing says when to GO SILENT. A scheduled celebratory post on a national mourning day passes every gate in this document — the exact screenshotable public embarrassment the Safety Law exists to prevent. CLOSED 2026-06-12: `scripts/blackout_gate.py` BUILT — one flag halts publishing on BOTH pipelines (wired into `render_client_slot.py` + `api/server.py`), with prayer-time/late-night etiquette and Ramadan's inverted hours; the flat-TTL rot killed by season-scoped truth in `scripts/staleness_report.py` (B071 — the Shawwal price dies outside its season). Landed BEFORE any batch consent went live, as required.
- **FLANK-03 — THE COMMERCIAL SPINE IS ABSENT.** The pyramid models the client's YES but never what he BUYS: no package/tier, no posts-per-week commitment, no price, no contract or renewal date, no `payment_received` / `renewal` / `scope_change` event types in the ledger. Layer 4 calls the monthly report "the renewal artifact" and tracks cost-per-YES with no revenue side — a repeated YES from a client who stopped paying is churn the instruments literally cannot see. A Saudi SME relationship dies over a disputed invoice or a late payment more often than over a bad caption. STATUS 2026-06-12: closed at the schema layer — pricing PINNED by Mohamed (Starter 700 / Growth 2650 / Enterprise 9000 SAR/month) and `payment_received` / `renewal` / `scope_change` event types live in `client_event_v1.schema.json`; the commercial terms doc is still DRAFT — not fully closed.
- **FLANK-04 — NO COMPETITOR WATCH.** Zero nodes. The owner watches 2-3 named rivals (the kabsa kitchen two streets over, the rival on HungerStation's front page); half his real requests arrive as «سويلي زي ذا» + a forwarded competitor post. CLOSED 2026-06-12: `competitor_set.json` per client (validates `client_competitor_set_v1.schema.json`) + `scripts/competitor_request.py` — the «سويلي زي ذا» intake path: rival post gives the ANGLE-CLASS only, 4-word shingle-overlap kill, rival product/brand words banned, every request an append-only `competitor_reference` event.
- **FLANK-05 — HIS CUSTOMERS OFF-INSTAGRAM ARE INVISIBLE.** audience_mirror reads IG comments (jurisha: 10) + one WhatsApp question — yet the doc itself routes orders to جاهز/هنقرستيشن and never reads the reviews/ratings THERE, or Google Maps. For a delivery-first F&B SME the delivery-app review section IS the customer voice and the loudest reputation surface; a 3.2-star «وصلت باردة» reality makes every warm-family-kitchen caption a lie the system cannot detect. This is the missing feed-vs-door check — the gap between the image and what actually arrives. STATUS 2026-06-12: SCOUTED only — Apify Google Maps actor found (B162); fetcher + consent ask parked with Mohamed (B163/B165). Still TO-BUILD.
- **FLANK-06 — PUBLISHING OPERATIONS DON'T EXIST.** Who presses publish? Batch consent (L1) implies posting access — Instagram/Meta Business credentials, 2FA, access revocation on offboarding, an audit trail of who posted what: none modeled. Also absent: posting times, story/reel/carousel format strategy (the engine is feed-caption shaped), and syncing the truth pack with the LIVE delivery-app menu — the place prices actually change first. STATUS 2026-06-12: still UNBUILT — the covering-click audit (B023, `trust_ladder.py --audit`) is queued but NOT live; posting-access model awaits Mohamed's decision (B171). TO-BUILD.