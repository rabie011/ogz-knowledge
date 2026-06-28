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
