#!/usr/bin/env bash
set -euo pipefail
#
# dev_quickstart.sh — runnable curl walkthrough of the OGZ Brain API for a dev integrating the brain.
#
# Mirrors scripts/openapi.yaml + scripts/brain_contract.py exactly (field names, the required `reach`, etc).
# Walks the 3 capabilities in order: profile IN (/extract) → content OUT (/produce, async) → performance
# BACK (/performance). Run it top-to-bottom; each step prints its raw JSON response.
#
# Auth: every route except /health needs `Authorization: Bearer $BRAIN_API_TOKEN`.
#
#   BRAIN_API_TOKEN=your-token ./scripts/dev_quickstart.sh
#   BRAIN_BASE=https://your-instance:4140 BRAIN_API_TOKEN=... ./scripts/dev_quickstart.sh

TOK="${BRAIN_API_TOKEN:?set BRAIN_API_TOKEN}"   # bearer token; /health is the only open route
BASE="${BRAIN_BASE:-http://127.0.0.1:4140}"     # reference bridge on the Mac Mini by default

HANDLE="albaik"      # an onboarded brand handle (^[A-Za-z0-9._-]{2,40}$)
PRODUCT="بروست"      # what the post features (non-empty string)
CHAIN="G03"          # openclaw chain id (^[A-Za-z0-9_-]{2,16}$)

# ---------------------------------------------------------------------------
# 1. GET /health — liveness + queue depth + HUMAIN judge state. NO auth.
#    Expect 200: {"ok":true,"humain":<bool>,"queue_depth":<int>,"auth_required":true}
# ---------------------------------------------------------------------------
echo "== 1. GET /health (no auth) =="
curl -sS "$BASE/health"
echo

# ---------------------------------------------------------------------------
# 2. GET /extract?handle=albaik — brand profile IN: the 81-field pre_fill + readiness gate. Fast/sync.
#    Expect 200: {"ok":true,"brand_id":"ogz:albaik","ready":<bool>,"readiness":{...},"pre_fill":{...}, ...}
#    (404 if the brand isn't onboarded; 401 on a bad token.)
# ---------------------------------------------------------------------------
echo "== 2. GET /extract?handle=$HANDLE (Bearer) =="
curl -sS -H "Authorization: Bearer $TOK" \
  "$BASE/extract?handle=$HANDLE"
echo

# ---------------------------------------------------------------------------
# 3. POST /produce {handle, product, chain} — content OUT: one post (banked image + system caption + 2-judge).
#    Slow → async. Expect 202: {"ok":true,"job_id":"...","poll":"/job/...","queue_position":<int>,"estimated_seconds":<int>}
#    (429 with retry_after_seconds if the produce queue is full.)
# ---------------------------------------------------------------------------
echo "== 3. POST /produce (Bearer) =="
PRODUCE_RESP=$(curl -sS -X POST -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"handle\":\"$HANDLE\",\"product\":\"$PRODUCT\",\"chain\":\"$CHAIN\"}" \
  "$BASE/produce")
echo "$PRODUCE_RESP"

# pull job_id out of the 202 body to poll it next
JOB_ID=$(printf '%s' "$PRODUCE_RESP" | sed -n 's/.*"job_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
echo "job_id=$JOB_ID"
echo

# ---------------------------------------------------------------------------
# 4. GET /job/$JOB_ID — poll the produce job until it finishes.
#    Expect 200: {"status":"pending|running|done|failed","result":{post_id,image,caption,passed,slot},...}
#    (404 if no such job.) In real code, loop with a backoff until status is "done" or "failed".
# ---------------------------------------------------------------------------
echo "== 4. GET /job/$JOB_ID (poll, Bearer) =="
curl -sS -H "Authorization: Bearer $TOK" \
  "$BASE/job/$JOB_ID"
echo

# ---------------------------------------------------------------------------
# 5. POST /performance {post_id, likes, reach} — performance BACK: engagement feeds the learning loop. Sync.
#    `reach` is REQUIRED and must be > 0 (it's the engagement_rate denominator); counts are non-negative ints.
#    Expect 200: {"ok":true,"z_score":<num|null>,"action":"kill|promote|null","detail":<str|null>}
#    (z_score is null during cold-start, <5 posts.)
# ---------------------------------------------------------------------------
echo "== 5. POST /performance (Bearer) =="
POST_ID="${HANDLE}__${PRODUCT}__${CHAIN}"
curl -sS -X POST -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"post_id\":\"$POST_ID\",\"likes\":10,\"reach\":1000}" \
  "$BASE/performance"
echo
