# MISTAKE LOG — OGZ Knowledge
# Permanent record. Never cleared. Appended by Claude. Read by Mohamed.
# Every bug, wrong assumption, failed test, silent failure goes here.
# Format: [CATEGORY] description — how it was found — fix (commit hash if applicable)

---

## 2026-06-06

- [API] /api/create and /api/check crashed with NameError: `BASE` not defined.
  Root cause: new endpoints used `BASE` (undefined) instead of `REPO` (module-level var).
  How found: Test 4 returned "Internal Server Error", checked logs/api_4100.log.
  Fix: Replaced all `BASE` with `REPO` in api/server.py — commit cbfb98c1.

- [API] /api/create and /api/check crashed with NameError: `intel` not defined.
  Root cause: `intel` (intelligence_layer.json) was only loaded inside /api/intelligence
  handlers, not at module level. New endpoints used it without loading it.
  How found: Same error log after BASE fix.
  Fix: Added module-level `intel = json.loads(...)` at server startup — commit cbfb98c1.

- [SERVER] API server running old binary after commits.
  Root cause: uvicorn started without --reload flag. Code changes don't auto-apply.
  How found: /api/create still returned 404 after commit added the route.
  Fix: Manual kill + restart required after every change to api/server.py.
  Rule added: Always kill+restart after api/server.py changes, verify with /openapi.json.

- [SCHEMA] 40 obs files failed validate_all.py.
  Root cause: extraction pipeline added real fields (likes_count, comments_count,
  engagement_total, followers_at_capture, engagement_rate, display_url, video_url
  to content_ref; engagement_method to quality_assessment) but schema had
  additionalProperties: false and didn't include these fields.
  How found: validate_all.py output showed "Additional properties not allowed".
  Fix: Added 8 fields to observation_v1.schema.json — validate_all now exits 0.

- [PRODUCT_NAMES] 20 of 23 brands had `top_words_in_captions` instead of
  `correct`/`wrong` product name lists. Quality gate product name check was
  silently passing for brands without curated lists.
  How found: Explored intelligence_layer.json brand_product_names section.
  Fix: [PENDING] — build_product_names.py to be written and run.

- [CONTEXT] Session resumed without knowing what was last worked on.
  Multiple sessions spent re-exploring state instead of building.
  Fix: Created CURSOR.md in ~/claude_operator_state/ — updated at session end,
  read first at session start. Session-start.sh now prints it automatically.
