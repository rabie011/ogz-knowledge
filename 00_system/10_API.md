# 🌐 API TREE
# 18 existing endpoints + 3 missing — input/output/status
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 API (api/server.py — FastAPI — port 4100)
│
├── 🏠 DISPLAY ENDPOINTS
│   ├── GET /
│   │   └── Demo page (standalone HTML)
│   ├── GET /presentation
│   │   └── Proof presentation for Alhareth
│   └── GET /report
│       └── Latest weekly intelligence report
│
├── 🧠 INTELLIGENCE ENDPOINTS
│   │
│   ├── GET /api/intelligence
│   │   ├── Input: ?sector=f_and_b (optional filter)
│   │   └── Output: full brain JSON
│   │
│   ├── GET /api/intelligence/rules/{sector}
│   │   ├── Input: sector in URL path
│   │   └── Output: sector-specific rules from brain
│   │
│   └── POST /api/intelligence/context ← THIN BRAIN
│       ├── Input: {brand: str, occasion: str}
│       ├── Calls: build_agent_context.py
│       ├── Output: {context_block: text, token_count: int}
│       ├── ~200 tokens of brand + metrics + guardrails
│       └── ⚠️ Gap: does NOT include templates or Arabic rules
│
├── 📊 SCORING ENDPOINT
│   └── POST /api/score
│       ├── Input: {content: str, sector: str, brand: str}
│       ├── Uses: 832KB ML model + rule-based scoring
│       └── Output: {score, ml_score, rule_score}
│
├── ✍️ GENERATION ENDPOINTS
│   │
│   ├── POST /api/brief ← rule-based
│   │   ├── Input: {sector, occasion, format}
│   │   └── Output: creative brief from pattern rules
│   │
│   ├── POST /api/brief/ai ← GPT-generated
│   │   ├── Input: {brand, product, occasion}
│   │   └── Output: GPT creative brief
│   │
│   ├── POST /api/calendar
│   │   ├── Input: {sector, month, year, posts_per_week}
│   │   ├── Maps month → occasion automatically
│   │   ├── Distributes posts: Sun/Tue/Thu pattern
│   │   ├── ⚠️ Says "Gulf Arabic" → fix to "Saudi Arabic"
│   │   └── ⚠️ Doesn't use brain context in generation
│   │
│   └── POST /api/caption
│       ├── Input: {sector, pattern, occasion, tone, count}
│       ├── Pulls sample captions from DB
│       ├── ⚠️ Says "Gulf Arabic dialect" → fix to Saudi Arabic
│       ├── ⚠️ Does NOT use style transfer method
│       └── ⚠️ Does NOT run quality gate on output
│
├── 🔍 DISCOVERY ENDPOINTS
│   ├── POST /api/recommend
│   │   ├── Input: {sector, occasion}
│   │   └── Output: recommended content to post next
│   ├── POST /api/search
│   │   ├── Input: {query, sector}
│   │   └── Output: semantic search in obs (pgvector)
│   ├── GET /api/benchmark/{sector}
│   │   └── Output: sector engagement benchmarks
│   └── GET /api/patterns/{sector}
│       ├── Input: ?min_obs=5 (optional)
│       └── Output: top performing patterns
│
├── 🔐 PROOF ENDPOINT
│   └── GET /api/proof/{ulid}
│       ├── Input: observation ULID
│       ├── Returns: source Instagram URL + real likes + caption
│       └── Clickable verification — every output traceable
│
├── 🔧 ADMIN ENDPOINTS
│   ├── POST /api/report/generate
│   │   └── Generates weekly intelligence report
│   └── GET /api/health
│       └── System health check
│
├── ❌ 3 MISSING ENDPOINTS (build these)
│   │
│   ├── POST /api/create ← THE MAIN ONE
│   │   ├── Input: {brand: str, product: str, occasion: str}
│   │   ├── Calls: content_engine.create_content()
│   │   ├── Output: {content, quality, proof}
│   │   └── Replaces: scattered endpoints for full creation
│   │
│   ├── GET /api/templates
│   │   ├── Input: ?sector=f_and_b&occasion=ramadan&tier=gold&limit=5
│   │   ├── Queries: template_library.json
│   │   └── Output: [{caption, tier, original_likes, original_url, tone}]
│   │
│   └── POST /api/check
│       ├── Input: {text: str, brand: str, occasion: str}
│       ├── Calls: quality_gate.check()
│       └── Output: {score, checks[], fixes_applied[], confidence}
│
└── 📊 OUTPUT FORMAT STANDARD (all generation endpoints should return)
    ├── content:
    │   ├── caption: Arabic text
    │   ├── visual_direction: Arabic description
    │   ├── hashtags: [list]
    │   └── content_type: recommended format
    ├── quality:
    │   ├── score: 0-100
    │   ├── confidence: "high"|"medium"|"low"
    │   ├── template_tier: "gold"|"silver"|"bronze"|"generated"
    │   ├── fixes_applied: [list]
    │   └── iterations: number
    └── proof:
        ├── template_caption: what we adapted from
        ├── template_likes: real likes of the source
        ├── template_url: https://www.instagram.com/p/...
        └── brand_metrics: "111 verified posts, avg 2,689 likes"
```

---

## RUNNING THE API

```bash
# Start:
cd ~/Desktop/ogz-knowledge && python3 -m uvicorn api.server:app --port 4100

# Test:
curl localhost:4100/api/health
curl -X POST localhost:4100/api/intelligence/context \
  -H "Content-Type: application/json" \
  -d '{"brand":"albaik","occasion":"founding_day"}'
```

---
*See [08_ENGINE](08_ENGINE.md) for the content pipeline the API calls.*
*See [09_QUALITY](09_QUALITY.md) for the quality gate API endpoint.*
