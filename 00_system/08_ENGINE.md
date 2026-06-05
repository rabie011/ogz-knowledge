# ⚙️ ENGINE TREE
# Unified content creation pipeline — input to output
# ⚠️ NOT BUILT YET — this is the most important missing piece
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 CONTENT ENGINE
│
├── ⚠️ CURRENT STATE
│   ├── 20 scattered API endpoints each doing their own thing
│   ├── /api/caption says "Gulf Arabic" (not Saudi Arabic)
│   ├── /api/caption doesn't use style transfer
│   ├── /api/caption doesn't run quality gate
│   ├── /api/calendar doesn't use brain context
│   └── No single path: input → templates → generate → check → deliver
│
├── 🎯 WHAT IT SHOULD BE
│   Single function: create_content(brand, product, occasion)
│   File to build: scripts/content_engine.py
│   API endpoint: POST /api/create
│
├── 🔄 THE FULL PIPELINE (8 steps)
│   │
│   │  INPUT: {brand:"albaik", product:"بروستد سبايسي", occasion:"founding_day"}
│   │
│   ▼ STEP 1: CONTEXT LOADING
│   ├── Call: build_agent_context.py → brand voice + real metrics + examples
│   ├── Load: occasion from occasion_calendar (content_approach + required_words)
│   ├── Load: cultural guardrails (always injected)
│   ├── Load: honest_gaps for this sector (warn LLM about weak data)
│   └── Result: ~200 tokens of context
│   │
│   ▼ STEP 2: LEARNING STORE CHECK
│   ├── Read: last 10 mistakes from logs/learning_store.jsonl
│   ├── Format: "Avoid these mistakes: [mistake1, mistake2...]"
│   └── Inject into prompt as negative examples
│   │
│   ▼ STEP 3: TEMPLATE SELECTION
│   ├── Query: template_library for sector + occasion + tier=gold
│   ├── Fallback chain: gold → silver → bronze → generated → fallback
│   ├── Cap at 5 templates max
│   └── Note tier of selected templates (determines confidence)
│   │
│   ▼ STEP 4: GENERATION (style transfer)
│   ├── Build prompt:
│   │   ├── System: brand context + cultural rules + mistakes to avoid
│   │   ├── Templates: "Here are real captions from similar posts:"
│   │   ├── Task: "Adapt for: {product} + {occasion}"
│   │   └── Rules: Saudi Arabic, max length for sector, product in first 5 words
│   ├── Call: LLM (gpt-4o-mini for speed/cost)
│   └── Receive: Arabic caption draft
│   │
│   ▼ STEP 5: QUALITY GATE (10 checks)
│   ├── Import: from scripts/lib/quality_gate import check, auto_fix
│   ├── Run: check(caption, brand, occasion) → {score, checks[], fixes[]}
│   ├── Apply: auto_fix if score 60-80
│   └── Result: fixed caption + score
│   │
│   ▼ STEP 6: REFINEMENT LOOP (if score < 80)
│   ├── Iteration 1: identify failures → targeted rewrite prompt
│   ├── Iteration 2: stricter prompt → force Saudi markers + required words
│   ├── Iteration 3: simplified prompt (shorter, safer)
│   └── After 3 iterations: accept best or reject (score < 50 = hard reject)
│   │
│   ▼ STEP 7: VISUAL DIRECTION
│   ├── Generate: Arabic visual brief (إضاءة, خلفية, تصوير)
│   ├── Based on: sector visual rules + brand visual DNA
│   └── Language: ALL in Arabic
│   │
│   ▼ STEP 8: DELIVERY + LOGGING
│   ├── Package output (see OUTPUT FORMAT below)
│   ├── Log: if score < 80 → mistakes to learning_store.jsonl
│   └── Track: which template was used
│   │
│   OUTPUT: {
│     content: {
│       caption: "الحين.. بروستد سبايسي الجديد من #البيك 🔥 #يوم_التأسيس",
│       visual_direction: "إضاءة دافئة دراماتيكية، خلفية تراثية بألوان الأخضر والذهبي...",
│       hashtags: ["#البيك", "#يوم_التأسيس"],
│       content_type: "carousel_slide"
│     },
│     quality: {
│       score: 87,
│       confidence: "high",
│       template_tier: "gold",
│       fixes_applied: [],
│       iterations: 1
│     },
│     proof: {
│       template_caption: "#برجر_فيليه_سمك.. طعم تغوص فيه 🫧 #البيك",
│       template_likes: 11716,
│       template_url: "https://www.instagram.com/p/CxYczJBoGZr/",
│       brand_metrics: "111 verified posts, avg 2,689 likes"
│     }
│   }
│
├── ✅ WHAT EXISTS NOW (can reuse)
│   ├── scripts/build_agent_context.py — STEP 1 context loading ✅
│   ├── scripts/lib/engagement.py — engagement calculation ✅
│   ├── scripts/lib/normalize_gpt.py — sector normalization ✅
│   ├── logs/learning_store.jsonl — mistakes log (4 entries) ✅
│   └── 11_who_to_learn_from/intelligence_layer.json — brain ✅
│
├── ❌ WHAT NEEDS TO BE BUILT
│   ├── 11_who_to_learn_from/template_library.json — STEP 3
│   ├── scripts/lib/quality_gate.py — STEP 5
│   ├── scripts/content_engine.py — THE ENGINE ITSELF
│   └── POST /api/create in api/server.py
│
└── 🔌 API ENDPOINT
    POST /api/create
    Input:  {brand: str, product: str, occasion: str}
    Output: {content, quality, proof}
    Calls:  content_engine.create_content()
    Replaces: /api/caption, /api/brief, /api/calendar (individually)
```

---
*See [07_TEMPLATES](07_TEMPLATES.md) for template library structure.*
*See [09_QUALITY](09_QUALITY.md) for quality gate details.*
*See [14_BUILD_ORDER](14_BUILD_ORDER.md) for build steps.*
