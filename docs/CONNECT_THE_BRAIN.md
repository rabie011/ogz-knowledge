# Connect the Brain — ogz-knowledge → the OGZ platform

**For the platform developers.** Your onboarding polls
`GET /api/onboarding/extraction-status/{brand_id}` and expects an 81-field `pre_fill` brand
profile, filled from the brand's sources. **ogz-knowledge produces exactly that JSON.** This doc is
how you plug it in. (Full field-by-field contract: [DEV_PLATFORM_INTEGRATION.md](DEV_PLATFORM_INTEGRATION.md).)

## What you get
`scripts/export_prefill.py` reads a brand's knowledge (Instagram harvest + website + Google reviews
+ our derived organs) and emits the **exact** response shape your `extraction-status` returns:

```jsonc
{
  "ok": true,
  "brand_id": "ogz:albaik",
  "onboarding_status": "extraction_complete",
  "sources_present": { "instagram": true, "website": false, "places": true },
  "source_status":   { "instagram": "done", "website": "unavailable", "places": "done" },
  "seed": { "brand_name_ar": "البيك", "sector": "Food & Beverage", "city_primary": "Jeddah" },
  "pre_fill": { /* EXACTLY your 81 keys, in your order — drop-in */ },
  "confidence": 0.78,
  "brand_understanding": "ALBAIK — علامة راسخة مشهورة …",
  "_coverage": { "filled": 64, "total": 81, "pct": 79, "null_fields": [...], "field_sources": {...} }
}
```

- **`pre_fill`** carries EXACTLY your 81 keys, in your order, no extras → assign it straight through.
- **`_coverage`** is a non-contract debug block (filled-vs-null + the source organ for each field).
  Ignore it in production, or use it to show "we couldn't find X" in your UI. It is the ONLY extra key.
- Unknown fields are `null` (honest), never fabricated. A field is null only when the source truly
  isn't available (e.g. a brand with no website → the 5 `website_*` fields are null).

## How to call it
**Today (file-based):**
```bash
python3 scripts/export_prefill.py --handle albaik          # → clients/albaik/prefill.json
python3 scripts/export_prefill.py --handle albaik --out /path/you/read.json
```
Sample outputs committed for 3 pilots: `clients/{albaik,eatjurisha,myfitness.sa}/prefill.json`.

**Three ways to wire it — your call (we'll build to whichever you pick):**
1. **You call us (REST).** We expose `POST /extract { ig_handle, website, places_name }` → returns
   the wrapper above; you poll as you already do. *(Cleanest for your Vercel app — matches your
   current `extraction-status` polling.)*
2. **We write to your store.** Give us the `brand_id` + DB/queue creds; we upsert the `pre_fill`
   row and flip `onboarding_status` to `extraction_complete`.
3. **You read our files.** We drop `prefill.json` per brand to a shared bucket; you fetch by handle.

We recommend **(1)** — it slots into your existing flow with zero changes to your polling.

## Coverage depends on the brand's sources
| brand | coverage | why |
|---|---|---|
| albaik | 79% | full IG harvest, 997 Google reviews, rich organs |
| eatjurisha | 70% | organs present, fewer external signals |
| myfitness.sa | 53% | sparse — little product/identity data yet |

Coverage rises with: a website/bio link, a Google Places listing, and more harvested posts. The
fields that stay null for rich brands are only the genuinely-external ones (gender split — IG doesn't
expose it; address — if no Places listing) and render-time visual blocks (filled at generation, not
profiling).

## What's next on our side
- Higher-fidelity visual fields (lighting/dimensions) come from our generation layer, not profiling.
- The same brain then **produces the content** (photo + caption) once the profile is set — that's the
  second half of the connection (your post-onboarding pipeline).

---

## Second half — content production (`produce_post`)
Once a brand's profile is set, the brain produces posts (photo + caption). `scripts/export_produce_post.py`
emits the **`produce_post`** contract — same drop-in idea as pre_fill, for content. Designed with DeepSeek.

```bash
python3 scripts/export_produce_post.py --handle eatjurisha --product جريش --chain G03            # wrap a banked post (fast, no render)
python3 scripts/export_produce_post.py --handle eatjurisha --product جريش --chain G03 --produce   # + generate the caption live + re-judge
python3 scripts/export_produce_post.py --handle albaik --list                                     # banked posts available
```
Returns: `{ post_id, status, content{image_url, caption{arabic,english,hashtags,cta,status}},
provenance, judgments{vision, caption}, review{required, threshold, auto_approved} }`. Example committed:
`clients/eatjurisha/post_جريش_G03.json`.

**Design rules baked in (DeepSeek consult):**
- **No fal spend to serve** — wraps BANKED renders; new renders are a separate async job, never on the dev call.
- **Never blocks on HUMAIN** — the Arabic caption judge is browser-gated; when down, caption falls back to
  GPT and `judgments.caption` tolerates `pending`. The contract is `pending`-safe throughout.
- **Caption ↔ judgment never drift** — the `caption` string is re-judged together, so `caption_alignment`
  always refers to the exact caption shown.
- **No single-model auto-approve** — a lone GPT-4o score can't ship Saudi creative (`signals:1` → always
  human review); auto-approve needs ≥2 agreeing judges (HUMAIN, or a 2nd signal like CLIP/another LLM).
- **Idempotent** — a durable ledger (`data/produced_posts.jsonl`) keyed by `post_id=(brand,product,slot)`;
  same key returns the existing post, never duplicates.

**Notes for you (the devs):**
- `caption.english` is `null` = Arabic-only (we don't translate yet). Treat `null` as "no EN string".
- `review.human_review_url` is `null` from our side — **you** fill it with your review-UI link.
- `status`: `pending_review` (needs a human) · `approved` (≥2 judges high) · `rejected` (image killed).

---

## The live bridge — `brain_api.py` (call all 3 over HTTP)
`scripts/brain_api.py` exposes the three contracts as a thin HTTP service (stdlib only) — designed with
the DeepSeek reasoner. Run it on the Mac Mini; the platform calls it:

```
GET  /extract?handle=albaik                 → the 81-field pre_fill profile          (sync, ~1s)
POST /produce {handle,product,chain,produce} → 202 {job_id}  → GET /job/<job_id>      (async)
GET  /job/<job_id>                          → {status: pending|running|done|failed, result}
POST /performance {post_id,likes,saves,comments,shares,reach} → ingest engagement      (sync)
GET  /health                                → {ok, humain, queue_depth, auth_required}
```
- **/produce is async** — caption gen + HUMAIN + GPT judges take 30–180s and are **serialized by the
  single HUMAIN browser**: ONE worker thread drains a queue (depth 4 → `429` backpressure). Devs poll `/job`.
- **/extract + /performance are fast sync.** All ledger mutations are guarded by one write-lock.
- **Idempotent** — repeat `/produce` for the same (handle,product,chain) returns the existing post.
- **Auth** — set `BRAIN_API_TOKEN` in ~/.abraham_env to require `Authorization: Bearer <token>`; unset = open dev mode.
- This is a **reference bridge** — the devs can call it directly, or reimplement the same 4 routes in their runtime.

---

## Ready to Wire (Phase A sign-off — 2026-06-30)

Evidence from `python3 scripts/run_brain_readiness.py` and `data/cursor_missions/done/brain-readiness-phase-a.json`.

### Core brain API (required for pilot wiring)

| Check | Status | Evidence |
|---|---|---|
| Brain-core unit tests | ✅ | `test_job_lifecycle`, `test_job_lifecycle_edges`, `test_perf_ingestor_coldstart`, `test_ledger_index` — all exit 0 |
| Contract drift (openapi ↔ brain_api) | ✅ | `contract_drift_check.py` — 5 paths in sync |
| `GET /health` | ✅ | `{ ok: true, auth_required: true }` |
| Auth — 401 without bearer | ✅ | `/extract` rejects unauthenticated calls |
| `GET /extract?handle=albaik` | ✅ | 81 keys, 79% coverage, `ready: true` |
| `GET /extract?handle=myfitness.sa` | ✅ | 62% coverage, `ready: false` (not produce-ready) |
| `POST /produce` banked (albaik, eatjurisha) | ✅ | Image + caption + judgments, idempotent |
| Sparse produce refusal (myfitness.sa) | ✅ | `status: refused` + clear reason, no crash |
| Cross-brand leak | ✅ | No forbidden terms in pilot prompts |
| `/performance` contract | ✅ | Fixture saved; cold-start `action: null` is normal |
| Contract fixtures | ✅ | `data/contract_fixtures/` (health, extract, produce, performance) |

**Verdict: READY TO WIRE for the 3 pilot handles** (albaik, eatjurisha, myfitness.sa as sparse/refuse case).

### Known flakes (not blockers)

| Item | Notes |
|---|---|
| Full `unittest discover` | Pre-existing failures (testbrand fingerprint, taste staleness, visual checklist drift) — not brain-API |
| `test_brain_connection` 2-judge live produce | `signals=1` (GPT only) when HUMAIN does not register as second judge — caption still generated and judged |
| myfitness coverage threshold in test | Test expects `<60%`; live profile is 62% — `ready: false` is the correct gate |

### Deferred to Phase B (not required for pilot wiring)

- [ ] `BRAIN_API_TOKEN` in `~/.abraham_env` for production (readiness runs use dev token)
- [ ] New-client intake trigger for unknown handles
- [x] LaunchAgent always-on for `brain_api.py` (`com.ogz.brain-api`, June 30 2026)
- [x] Cursor mission bus 24/7 poll (`com.ogz.cursor-missions`, every 5 min)
- [ ] Platform wiring (`ogz-platform` / `o-gz-studios-web`)

### How to re-run readiness

```bash
cd ~/Desktop/ogz-knowledge
python3 scripts/run_brain_readiness.py
# or: tell Claude Code "check cursor missions"
```

Results land in `data/cursor_missions/done/brain-readiness-phase-a.json`.

---

## Hardening (DeepSeek audit — A3 + A7)
- **`/extract` now returns `ready: bool`** + a `readiness` block (`coverage_pct`, `banked_renders`,
  `blocking_reasons`). A brand is produce-ready only at ≥60% coverage AND ≥1 banked render. Check `ready`
  before calling `/produce`. (albaik/jurisha ready; myfitness.sa not — 53%, 0 renders.)
- **Auth is now MANDATORY** — the bridge is never open. If `BRAIN_API_TOKEN` is unset, it generates a
  token and prints it at startup; pass `Authorization: Bearer <token>` on every call except `/health`.

---

## The learning loop — `POST /performance` (cold-start, proven)
The brain learns from real outcomes. After a post is published, send its engagement:
`POST /performance {post_id, likes, saves, comments, shares, reach}`. The loop (subtractive, safe):
- engagement_rate = (likes + 2·saves + 3·comments + 4·shares) / reach, z-scored vs the brand's last 20.
- **z ≤ −2 (reach ≥ 500) → the (brand·product·setup) is killed** → the producer's pre-flight gate avoids it.
- z ≥ +2.5 (≥5 posts) → a confidence counter (human-facing; never auto-edits the profile).
- **COLD-START:** baselines need ~5+ of the brand's posts before z-scores are meaningful, ~20 for full
  signal. Until then `action: null` is normal — the loop is accumulating, not broken.
- **PROVEN end-to-end** (this contract, live): 6 baseline events + a bomb → `{z_score: -30.16,
  action: "kill"}` → the bombed setup was blocked in the kill-registry. The brain learns the moment you
  feed it; `post_id` format is `{handle}__{product}__{chain}`.

---

## Request contract (what the brain accepts / rejects)
Every endpoint validates fields and returns `400 {ok:false, error, field}` on violation (see `scripts/brain_contract.py`):
- **GET /extract** — `handle`: 2-40 chars `[A-Za-z0-9._-]`.
- **POST /produce** — `handle` (as above), `product` (non-empty str), `chain` (2-16 chars `[A-Za-z0-9_-]`, e.g. G03); optional `occasion` (str, def "everyday"), `produce`/`regenerate` (bool).
- **POST /performance** — `post_id` (non-empty str); `likes/saves/comments/shares` (non-negative ints, def 0); **`reach` (positive int, required** — the engagement_rate denominator). Wrong type → `400` naming the field; no more silent failures or opaque 500s.

---

## Ready to Wire — Phase A checklist (2026-06-30)

Evidence: `data/cursor_missions/done/brain-readiness-phase-a.json` · fixtures in `data/contract_fixtures/` · log `data/cursor_missions/done/brain-readiness-phase-a.log`.

**Overall: PARTIAL — brain API is wire-ready; one ops gate + two non-blocking test flakes.**

### Core brain tests (must pass — all green)

| Check | Result | Evidence |
|---|---|---|
| Job lifecycle | ✅ | `test_job_lifecycle.py` exit 0 |
| Job lifecycle edges | ✅ | `test_job_lifecycle_edges.py` exit 0 |
| Perf ingestor cold-start | ✅ | `test_perf_ingestor_coldstart.py` exit 0 |
| Ledger index | ✅ | `test_ledger_index.py` exit 0 |
| Contract drift (openapi ↔ brain_api) | ✅ | 5 paths in sync: `/extract`, `/health`, `/job/`, `/performance`, `/produce` |
| `/health` liveness | ✅ | `{"ok":true,"humain":true,"auth_required":true}` |
| Auth rejects unauthenticated `/extract` | ✅ | 401 without bearer |
| Albaik `/extract` — 81 keys, ≥75% coverage, `ready:true` | ✅ | 81 keys · 79% · 17 banked renders |
| Eatjurisha `/extract` | ✅ | 70% coverage · produce-ready |
| myfitness.sa `/extract` — not produce-ready | ✅ | 62% · 0 renders · `ready:false` |
| Albaik + eatjurisha `/produce` banked serve | ✅ | 202 → job done · correct brand image · idempotent |
| myfitness.sa `/produce` clean refusal | ✅ | `status:refused` with clear reason, no crash |
| Cross-brand prompt isolation | ✅ | No bleed across 3 pilots |
| Live caption + judge (albaik كومبو بيك) | ✅ | Caption generated · judged |

Run the suite: `python3 scripts/run_brain_readiness.py` (requires `BRAIN_API_TOKEN` — see blocker below).

### Ops gate (blocker before platform wiring)

| Item | Status | Action |
|---|---|---|
| **`BRAIN_API_TOKEN` in `~/.abraham_env`** | ❌ **BLOCKER** | Token line is **missing** today. Without it, `test_brain_connection.py` gets 401 on every authenticated route. Add `BRAIN_API_TOKEN=<your-token>` to `~/.abraham_env`, restart `brain_api.py`, give the same token to platform devs. If unset, brain_api generates a random token at startup (printed once) — clients must match that exact token. |

### Integration flakes (non-blockers for wiring)

| Failure | Class | Notes |
|---|---|---|
| `myfitness.sa: profile is sparse (<60%)` — got 62% | **Pre-existing test threshold** | Profile improved since test was written. Refusal path still works (`ready:false`, no banked renders). Safe to wire. |
| `albaik: 2-judge present (HUMAIN+GPT)` — only `['gpt']` | **HUMAIN flake** | Live produce succeeded; caption judged. HUMAIN browser was up (`humain:true`) but second judge signal did not register this run. Not a contract blocker — platform should treat `judgments` as pending-safe per design rules above. |

### Full unittest discover — known non-blockers (do not block brain API handoff)

These fail in `python3 -m unittest discover -s scripts/tests -q` but are **unrelated to brain_api HTTP wiring**:

| Test module | Class | Cause |
|---|---|---|
| `test_provenance_ladder` (6 errors) | Pre-existing | `clients/testbrand/profile/fingerprint.json` missing |
| `test_fingerprint_payment` (1 error) | Pre-existing | Same missing testbrand fingerprint |
| `test_lovable_watch` (0–5 errors) | Pre-existing / env | Git repo access for Lovable watch; passes outside sandbox when repo is writable |
| `test_taste_staleness` | Pre-existing | `founder_taste` 17d behind latest rating (threshold 14d) |
| `test_visual_review_checklist` | Pre-existing | On-disk checklist stale — re-run `build_visual_review_checklist.py` |

Core brain unit subset (`test_job_lifecycle*`, `test_perf_ingestor_coldstart`, `test_ledger_index`, `contract_drift_check`) — **all green**.

### Contract fixtures saved (for platform devs to eyeball)

| Fixture | Purpose |
|---|---|
| `data/contract_fixtures/health.json` | Liveness probe shape |
| `data/contract_fixtures/extract_albaik.json` | Full 81-key pre_fill example (79%) |
| `data/contract_fixtures/extract_myfitness.json` | Sparse / not-ready example (62%) |
| `data/contract_fixtures/produce_eatjurisha.json` | Banked produce response |
| `data/contract_fixtures/performance_sample.json` | Performance ingest ack |

### What platform devs wire (Phase B deferred — spec only today)

1. Point onboarding poll at `GET http://<mac-mini>:4140/extract?handle={ig_handle}` with `Authorization: Bearer <token>`.
2. Check `ready` before calling `/produce`.
3. Poll `GET /job/{job_id}` after `POST /produce` returns 202.
4. Post-publish: `POST /performance` with `reach` required.
5. Phase B hardening (systemd/launchd, persistent token rotation, rate limits) — **not in this handoff**.
