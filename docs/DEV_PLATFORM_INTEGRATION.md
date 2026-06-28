# DEV PLATFORM INTEGRATION — the connection contract (discovered June 27, 2026)

Discovered empirically by walking the live onboarding at `o-gz-studios-web-hlhi.vercel.app`
with albaik's data (a full signup + the 16-step "smart registration form"). This is the
contract ogz-knowledge (the brain) must fulfill. **Pipeline A (self-service) per ogz-knowledge's
own CLAUDE.md.**

## The architecture the devs built
- Customer signs up (email+pass or Google) → 16-step onboarding wizard (`/onboarding-start`).
- Step 4 collects **brand links** (IG @handle, website URL, Google Maps name, city) + a
  **"Start analysis"** button → kicks off a background **extraction job** (a `brand_id` UUID).
- The platform polls **`GET /api/onboarding/extraction-status/{brand_id}`** while the user
  answers the remaining questions ("we'll read them to learn your brand while you answer").
- The extraction is supposed to fill an **81-field `pre_fill` brand profile** from the sources
  (Instagram + website + Google Places).

## THE KEY GAP (what we need to do)
**The extraction is NOT working.** On the live run: `onboarding_status: "extraction_pending"`,
`source_status: {instagram: "pending", website: "pending", places: "unavailable"}`, every
`pre_fill` field `null`, and the UI showed **"Analysis ran into an issue — something on our end
interrupted the process."** So the dev platform has the FULL API surface + the 81-field contract,
but **the extraction engine (the brain) is failing / not connected.** That extraction is exactly
what ogz-knowledge's intake does (`client_intake.py` harvest + `research_fill_established` +
the openclaw visual fields). **Our job: provide a working extraction that fills `pre_fill`.**

## The contract — `GET /api/onboarding/extraction-status/{brand_id}` returns:
```json
{
  "ok": true,
  "brand_id": "<uuid>",
  "onboarding_status": "extraction_pending | ...",
  "sources_present": {"instagram": bool, "website": bool, "places": bool},
  "source_status": {"instagram": "pending|...", "website": "...", "places": "unavailable|..."},
  "seed": {"brand_name_ar": null, "sector": "F&B", "city_primary": "Jeddah"},
  "pre_fill": { ...81 fields, all null until extraction fills them... },
  "confidence": ...,
  "brand_understanding": ...
}
```

## The 81 `pre_fill` fields → mapped to OUR organs
**Identity** (→ product_truth._meta / passport / l1_strategy):
  brand_name_en, brand_name_ar, business_category, sector_hint, sub_sector_hint,
  founded_year_hint, lifecycle_stage_hint, online_native, has_holding_page,
  differentiator_seed, differentiator_source

**Cultural / dialect / tone** (→ cultural_overrides + the 80-field cultural_spec):
  dialect_hint, region_primary_hint, city_hint, formality_level, humor_tolerance,
  religious_sensitivity, bilingual_ratio, tone_register_hint, communication_style_hint,
  tone_anti_attribute_ids, caption_style_hint, style_register

**Visual DNA** (→ visual_dna + openclaw v3.7 fields):
  color_palette, primary_color_hex, color_field_palette, style_descriptor, lighting,
  people_in_frame (→ face_visibility), filter_style, identity_dna, material_texture,
  companion_elements, dimensions, capture_character, logo_url, brand_assets_bundle

**Strategy / goals** (→ l1_strategy):
  price_position, primary_channel, primary_kpi_type, intent_state, brand_goals_hint,
  posting_cadence_hint, posting_rhythm_hint

**Audience** (→ audience_mirror): audience_female_pct, audience_male_pct

**Occasions** (→ year_map): ramadan_relevance, eid_fitr_relevance, eid_adha_relevance,
  national_day_relevance, founding_day_relevance

**Instagram raw** (→ client_intake harvest): ig_username, ig_full_name, ig_followers_count,
  ig_follows_count, ig_posts_count_total, ig_profile_pic_url, ig_is_verified,
  ig_is_business_account, ig_external_url, ig_post_image_urls

**Engagement** (→ fingerprint): engagement_baseline_likes, engagement_baseline_comments,
  engagement_baseline_views, posts_observed_count, signature_hashtags, signature_phrases,
  brand_reply_samples_count, account_age_months, post_count, post_frequency_30d

**Website** (→ client_intake website): website_url, website_page_count, website_language,
  website_og_image, website_canonical_url

**Google Places** (→ new source we don't harvest yet): rating, user_ratings_total,
  formatted_address

**Meta:** confidence, brand_understanding

## The 16-step onboarding wizard (what the form collects, beyond the links)
1 your name · 2 brand name (ar required + en optional) · 3 owner gender (opt) ·
4 **brand links + Start analysis** (IG/website/maps/city) · 5 brand origin story ("AI can't read this") ·
6 audience gender skew · 7 brand values · 8 occasions (multi) · 9 ideal customer persona ·
10 content goals (multi) · 11 posts/week · 12 off-days · 13 **region → dialect** ·
14 price range band · 15 **red-lines** (never-use topics; direct red_lines match) · 16 finalize.

## 🛑 ISSUES TO FLAG THE DEVS (marked June 27, FULL live signup as albaik, end-to-end)
**The frontend, accounts, onboarding, and data persistence WORK. The AI PIPELINE (the brain) does
NOT — both halves hang. Completed the entire signup; brand created (`albaik-iy2m`,
onboarding_status=submitted, brand_name_ar="البيك" saved), but no content could be produced.**

1. **[BLOCKER] Extraction / "Build your Brand DNA" never completes** — runs ~2 min then
   "Analysis ran into an issue — something on our end interrupted the process." `source_status`
   stays `{instagram: pending, website: pending, places: unavailable}` — **the IG/website analysis
   never runs.** `pre_fill` all-null; the review shows EMPTY brand understanding + "(awaiting review)".
2. **[BLOCKER] Content-generation pipeline times out after submit** — onboarding submits fine →
   `/{slug}/processing` cycles "Getting started… lining up content ideas… picking up your tone of
   voice…" for ~1 min → **"Taking longer than expected. Your form data is saved — retry to re-run
   the pipeline."** The "first post in 5 minutes" never generates. Same root: the brain isn't there.
3. **Google OAuth redirect is misconfigured** — Google sign-in lands on `localhost:3000`
   (Open WebUI) with `flow_state_already_used`, not back on the platform. (Email+password works.)
4. **[minor/UX] Manual "complete your brand" form is misleading + tedious** — says "fill what you
   can — skip the rest" but SEVERAL fields are actually required (dialect, religious_sensitivity,
   ramadan_relevance, price_position, main_channel...) and it validates **one error at a time**, so
   the user hits ~6 sequential "X: Required" errors. (My earlier "un-completable" read was WRONG —
   it IS completable; selecting a value just removes that field from the to-fill list, which looked
   like a bug. Correcting the record.) The friction only exists because extraction (#1) returned
   nothing, forcing manual entry.

## BOTTOM LINE
Everything around the brain works. **The brain — extraction (IG/website → `pre_fill`) and content
generation (organs → posts) — is the missing/broken piece, and it is exactly what ogz-knowledge
provides.** Prepare ogz-knowledge to fill `pre_fill` from sources + produce the first batch, and the
platform comes alive end-to-end.

## Open question for the devs (the only thing that decides the build shape)
HOW do they want the brain to fill `pre_fill`? Three shapes:
(a) **They call us** — we expose `POST /extract {ig,website,places} → pre_fill` (REST), they poll.
(b) **We write to their store** — they give us the brand_id + DB/queue, we fill `pre_fill` rows.
(c) **They already built the extractor** and it's just erroring — then we provide the
    organs/knowledge it reads, not the extractor itself.
The live evidence (their own `/api/onboarding/extraction-status` + `pre_fill` schema) points
to (a) or (b): they own the API + schema, the extraction worker is the missing/broken piece.

## SECOND HALF — content production contract (target; DeepSeek consult June 28)
Once `pre_fill` is set, the brain must PRODUCE posts feeding the platform's post-onboarding pipeline
(their "first post in 5 min", which currently times out). Target `produce_post` return shape:
```jsonc
{ "post_id": "...", "status": "pending_review|approved|rejected|regenerating",
  "content": { "image_url": "...", "caption": { "arabic": "...", "english": "...",
               "hashtags": [...], "cta": "..." } },
  "provenance": { "prompt": "<15-block v3.7>", "model": "flux-2-pro", "generation_attempts": 1 },
  "judgments": { "vision": {"passed": true, "score": 0.87, "flags": [...]},
                 "caption": {"passed": true, "score": 0.92, "dialect_check": "Hejazi", "issues": []} },
  "review": { "required": true, "threshold": 0.85, "auto_approved": false, "human_review_url": "..." } }
```
- **Sync:** `POST /produce` returns `post_id` + `pending_review` immediately (validate only).
- **Async:** render (8-15s) + caption (parallel) + both judges → webhook/poll on completion.
- **Review gate:** auto-approve if both judges ≥0.85; auto-reject <0.4 → regenerate; 0.4–0.85 → human.
  Regeneration carries `{previous_post_id, feedback}`; **escalate to human after 2 fails — never loop a 3rd.**
- **Top failure modes:** (1) caption dialect mismatch — we mitigate (HUMAIN Arabic judge + cultural_overrides
  dialect); (2) image↔caption semantic drift — we partly mitigate (rabie_judge caption_alignment_score;
  strengthen w/ embedding coherence); (3) regen loop w/o improvement — kill_registry + escalate-after-2.

## 🔑 THE BIGGEST MISS (DeepSeek Q6) — no performance→profile feedback loop
The connection today is one-way: profile → content → post → (nothing). The brain never learns from what
actually gets engagement. **Add a `post_performance_ingestor`:** after ~24h, ingest the produced post's
real engagement (likes/saves/shares/comments/CTR) → update field confidence, bias visual_style/tone,
re-rank inferred fields (e.g. IG-category). We already have `12_data_shapes/outcome_event_v1` + the
RABIE verdict→learning loop (Rule #14) — this extends learning from OUR judge to REAL audience signal.
Requires the devs to send post engagement back (or us to harvest the posted content). The 2-way wire.

## CONSULT VERDICT (DeepSeek, June 28) — kept vs disputed
KEPT: schema_version on wrapper · rating null below 10 reviews · low_confidence_fields flag (derived
fills) · field_sources per field (already shipped). DISPUTED: "logo→hex breaks on white/black logos" —
already handled (we skip desaturated pixels → null if logo has no saturated color). NEXT: the
performance feedback loop (Q6) is the real architectural gap.
