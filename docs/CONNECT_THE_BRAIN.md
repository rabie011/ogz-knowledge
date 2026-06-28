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
