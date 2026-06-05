# 🔧 BUILD ORDER TREE
# What to build next — phases, steps, files, verification
# Start here at every new session
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 BUILD ORDER
│
├── 🎯 CURRENT GOAL: Build the foundation so the engine can run
│
├── ⏱️ TOTAL ESTIMATED TIME: ~5 hours
│
├── PHASE 1: FIX FOUNDATION (1.5 hours)
│   │  Fix the broken things before building anything new
│   │
│   ├── Step 1.1: Fix sector names (5 min)
│   │   ├── File: 11_who_to_learn_from/intelligence_layer.json
│   │   ├── Section: brand_profiles
│   │   ├── Find: OGZ-BEAUTY-Reference-001, OGZ-BEAUTY-Reference-002
│   │   ├── Change: "sector": "beauty" → "sector": "beauty_personal_care"
│   │   ├── Find: OGZ-RETAIL-Reference-001
│   │   ├── Change: "sector": "retail" → "sector": "retail_lifestyle"
│   │   └── Verify: grep "\"beauty\"" intelligence_layer.json → 0 results
│   │
│   ├── Step 1.2: Rebuild sector_facts (15 min)
│   │   ├── Script to write: scripts/rebuild_sector_facts.py
│   │   ├── Logic: count obs files per sector + real_metrics brands per sector
│   │   ├── Update: intelligence_layer.json → sector_facts section
│   │   └── Verify: numbers match actual file counts
│   │
│   ├── Step 1.3: Add missing brand profiles (30 min)
│   │   ├── Brands to add: zara, hm, kiabiksa, randbfashion, mikyajy,
│   │   │   pandasaudi, mumzworld, aldeebajofficial
│   │   ├── For each: scan top 5 obs by likes → extract tone, hashtags
│   │   ├── Add to: intelligence_layer.json → brand_profiles section
│   │   └── Verify: all 23 verified brands have profiles
│   │
│   └── Step 1.4: Expand brand product names (30 min)
│       ├── For all 23 verified brands without product names
│       ├── Scan: their captions in obs → find most common product words
│       ├── Add to: intelligence_layer.json → brand_product_names
│       └── Verify: all 23 brands have correct + wrong lists
│
├── PHASE 2: BUILD TEMPLATE LIBRARY (1 hour)
│   │
│   ├── Step 2.1: Write build_template_library.py (45 min)
│   │   ├── New file: scripts/build_template_library.py
│   │   ├── Logic:
│   │   │   1. Scan all 3,816 observation files
│   │   │   2. Filter: Arabic caption (re.search Arabic chars) + likes_count > 0
│   │   │   3. Assign tier: gold(≥1000), silver(100-999), bronze(1-99)
│   │   │   4. Tag: sector, occasion, content_type (from obs fields)
│   │   │   5. Create template: replace brand name with {brand},
│   │   │      product name with {product}
│   │   │   6. Load 40 generated templates from brain.saudi_templates
│   │   │   7. Add fallback templates for empty sectors
│   │   │   8. Print coverage matrix (sector × occasion × tier)
│   │   │   9. Save to: 11_who_to_learn_from/template_library.json
│   │   ├── Output format per template:
│   │   │   {caption, tier, sector, occasion, content_type, tone,
│   │   │    brand_source, original_likes, original_url}
│   │   └── Coverage target: every sector × occasion ≥ 3 templates
│   │
│   └── Step 2.2: Template API endpoint (15 min)
│       ├── File: api/server.py
│       ├── Add: GET /api/templates
│       ├── Params: sector, occasion, tier, limit (default 5)
│       └── Returns: list of templates matching filters
│
├── PHASE 3: BUILD QUALITY GATE MODULE (45 min)
│   │
│   ├── Step 3.1: Write quality_gate.py (30 min)
│   │   ├── New file: scripts/lib/quality_gate.py
│   │   ├── Functions:
│   │   │   ├── check(text, brand, occasion) → {score, checks[], fixes[]}
│   │   │   ├── auto_fix(text, brand, sector) → fixed_text
│   │   │   ├── hard_block_check(text, brand) → True/False
│   │   │   └── log_mistake(handle, score, mistake) → None
│   │   ├── Reads rules from: intelligence_layer.json
│   │   │   quality_gate, brand_product_names, occasion_required_words,
│   │   │   arabic_quality_rules, cultural_guardrails
│   │   └── Logs to: logs/learning_store.jsonl
│   │
│   └── Step 3.2: Quality check API (15 min)
│       ├── File: api/server.py
│       ├── Add: POST /api/check
│       ├── Input: {text, brand, occasion}
│       └── Output: {score, checks[], fixes_applied[], confidence}
│
├── PHASE 4: BUILD CONTENT ENGINE (1.5 hours)
│   │
│   ├── Step 4.1: Write content_engine.py (1 hour)
│   │   ├── New file: scripts/content_engine.py
│   │   ├── Main function: create_content(brand, product, occasion) → dict
│   │   ├── Steps (import from existing):
│   │   │   ├── build_agent_context.build_context(brand, occasion)
│   │   │   ├── read template_library.json → filter by sector + occasion
│   │   │   ├── read learning_store.jsonl → last 10 mistakes
│   │   │   ├── call OpenAI API with context + templates
│   │   │   ├── quality_gate.check() → score
│   │   │   ├── if score < 80: refine loop (max 3x)
│   │   │   └── package output with proof
│   │   └── Returns: {content, quality, proof}
│   │
│   └── Step 4.2: Add create endpoint (30 min)
│       ├── File: api/server.py
│       ├── Add: POST /api/create
│       ├── Input: {brand: str, product: str, occasion: str}
│       ├── Calls: content_engine.create_content()
│       └── Returns: full content + quality + proof
│
└── PHASE 5: TEST EVERYTHING (1 hour)
    │
    ├── Test 1: Sector names fixed
    │   python3 -c "import json; b=json.load(open('11_who_to_learn_from/intelligence_layer.json')); [print(k,v['sector']) for k,v in b['brand_profiles'].items() if v['sector'] in ('beauty','retail')]"
    │   → Should print nothing
    │
    ├── Test 2: Template library exists and has coverage
    │   python3 -c "import json; t=json.load(open('11_who_to_learn_from/template_library.json')); print(f'{len(t)} templates')"
    │   → Should print 400+
    │
    ├── Test 3: Quality gate imports and works
    │   python3 -c "from scripts.lib.quality_gate import check; r=check('اطلبه الحين بروستد جديد من #البيك','albaik','evergreen'); print(r['score'])"
    │   → Should print 70+
    │
    ├── Test 4: Content engine generates passing content
    │   python3 scripts/content_engine.py albaik "بروستد سبايسي" founding_day
    │   → score ≥ 80, confidence = "high"
    │
    ├── Test 5: Content engine for weak sector
    │   python3 scripts/content_engine.py mikyajy "أحمر شفاه" eid_al_fitr
    │   → score ≥ 70, template_tier = "silver" or "generated"
    │
    ├── Test 6: API endpoint works
    │   curl -X POST localhost:4100/api/create \
    │     -H "Content-Type: application/json" \
    │     -d '{"brand":"albaik","product":"بروستد","occasion":"founding_day"}'
    │   → Returns content + quality + proof
    │
    └── Test 7: Learning store grows
        python3 scripts/content_engine.py pizzahutsaudi "بيتزا" evergreen
        tail -1 logs/learning_store.jsonl
        → New entry added if score < 80
```

---

## VERIFICATION CHECKLIST (run before claiming done)

```bash
# Always:
python3 scripts/verify_ship_ready.py
# Should exit 0

# After Phase 1:
python3 -c "import json; b=json.load(open('11_who_to_learn_from/intelligence_layer.json')); print('sector facts:', b['sector_facts']['f_and_b']['obs_count'])"
# Should print 1899

# After Phase 2:
python3 -c "import json; t=json.load(open('11_who_to_learn_from/template_library.json')); print(len(t), 'templates')"

# After Phase 3:
python3 -c "from scripts.lib.quality_gate import check; print('Quality gate OK')"

# After Phase 4:
curl -X POST localhost:4100/api/create -H "Content-Type: application/json" \
  -d '{"brand":"albaik","product":"بروستد","occasion":"evergreen"}'
# Should return content with score >= 70
```
