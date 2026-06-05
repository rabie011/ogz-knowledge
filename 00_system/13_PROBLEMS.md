# 🚨 PROBLEMS TREE
# 10 broken things — exact location + fix
# Read this when something doesn't work
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 PROBLEMS (ordered by impact)
│
├── 🔴 P1: TEMPLATE LIBRARY DOESN'T EXIST
│   │
│   ├── Impact: HIGHEST — everything depends on this
│   ├── What's wrong:
│   │   ├── 1,409 obs have real captions + real likes but no extractable library
│   │   ├── 40 generated templates stored as TEXT STRINGS in brain (not structured)
│   │   └── No way to query: "give me gold templates for f_and_b + ramadan"
│   ├── Where: 11_who_to_learn_from/template_library.json → MISSING
│   ├── Fix: Build scripts/build_template_library.py
│   └── Time: 45 min
│
├── 🔴 P2: NO UNIFIED CONTENT PIPELINE
│   │
│   ├── Impact: HIGH — every endpoint does its own thing, inconsistent quality
│   ├── What's wrong:
│   │   ├── /api/caption says "Gulf Arabic" not "Saudi Arabic"
│   │   ├── /api/caption doesn't use style transfer
│   │   ├── /api/caption doesn't run quality gate
│   │   └── /api/calendar doesn't use brain context
│   ├── Where: api/server.py → generate_caption() and content_calendar()
│   ├── Fix: Build scripts/content_engine.py + POST /api/create
│   └── Time: 1 hour
│
├── 🔴 P3: QUALITY GATE NOT A MODULE
│   │
│   ├── Impact: HIGH — quality checks can't be imported by content engine
│   ├── What's wrong:
│   │   ├── Rules exist in brain JSON (quality_gate section)
│   │   ├── Code is scattered, not importable
│   │   └── Can't: from lib.quality_gate import check, auto_fix
│   ├── Where: scripts/lib/quality_gate.py → MISSING
│   ├── Fix: Create importable module with check() + auto_fix()
│   └── Time: 30 min
│
├── 🟡 P4: SECTOR NAMES INCONSISTENT IN BRAIN
│   │
│   ├── Impact: MEDIUM — sector lookup fails for 3 profiles
│   ├── What's wrong:
│   │   ├── 3 brand_profiles use "beauty" and "retail" (short names)
│   │   └── Everything else uses "beauty_personal_care", "retail_lifestyle"
│   ├── Where: intelligence_layer.json → brand_profiles
│   │   ├── OGZ-BEAUTY-Reference-001: "sector": "beauty"
│   │   ├── OGZ-BEAUTY-Reference-002: "sector": "beauty"
│   │   └── OGZ-RETAIL-Reference-001: "sector": "retail"
│   ├── Fix: Change 3 values: "beauty"→"beauty_personal_care", "retail"→"retail_lifestyle"
│   └── Time: 5 min
│
├── 🟡 P5: BRAND PROFILES MISSING FOR 8+ VERIFIED BRANDS
│   │
│   ├── Impact: MEDIUM — engine can't load brand DNA for these brands
│   ├── Missing brands:
│   │   ├── @zara (63 obs, 50,836 avg likes — highest!)
│   │   ├── @hm (88 obs, 6,074 avg likes)
│   │   ├── @mikyajy (96 obs, 636 avg likes) ← main beauty brand
│   │   ├── @kiabiksa (72 obs, 44 avg likes)
│   │   ├── @randbfashion (31 obs)
│   │   ├── @pandasaudi (113 obs)
│   │   ├── @mumzworld (118 obs)
│   │   └── @aldeebajofficial (6 obs)
│   ├── Where: intelligence_layer.json → brand_profiles (missing entries)
│   ├── Fix: Generate profiles from obs captions (voice, tone, hashtags)
│   └── Time: 30 min
│
├── 🟡 P6: PRODUCT NAMES: ONLY 3 OF 23 BRANDS
│   │
│   ├── Impact: MEDIUM — LLM uses wrong product names for 20 brands
│   ├── What's wrong: AlBaik, PizzaHut, Barns defined. 20 others: nothing.
│   ├── Where: intelligence_layer.json → brand_product_names
│   ├── Fix: Extract product names from captions per brand
│   └── Time: 30 min
│
├── 🟡 P7: SECTOR FACTS STALE
│   │
│   ├── Impact: MEDIUM — brain shows wrong numbers in context
│   ├── What's wrong:
│   │   ├── f_and_b: shows 1,607 obs — actual is 1,899
│   │   ├── retail_lifestyle: shows 359 — actual is 723
│   │   ├── fashion: shows 258 — actual is 523
│   │   ├── beauty: shows 320 — actual is 469
│   │   └── retail/fashion/beauty show 0 real metrics — actually 4/5/4 brands
│   ├── Where: intelligence_layer.json → sector_facts
│   ├── Fix: Rebuild from actual obs file count
│   └── Time: 15 min
│
├── 🟢 P8: TWO SECTORS HAVE ZERO REAL DATA
│   │
│   ├── Impact: LOW — these sectors use generated templates only
│   ├── What's wrong:
│   │   ├── real_estate: 113 obs, 0 with likes, 0 Arabic templates
│   │   └── healthcare: 89 obs, 0 with likes, 1 Arabic caption
│   ├── Decision (Mohamed approved): Generated templates only
│   └── Accept as limitation — document in honest_gaps
│
├── 🟢 P9: FASHION + RETAIL IN SAME FOLDER
│   │
│   ├── Impact: LOW — confusing but data is correct inside files
│   ├── What's wrong: 📁 retail/ contains retail_lifestyle AND fashion obs
│   ├── sector field in JSON is correct ("fashion" or "retail_lifestyle")
│   └── Decision: Keep folder structure — moving would break paths
│
└── 🟢 P10: ONLY 31 REEL OBSERVATIONS
    ├── Impact: LOW — accepted limitation
    ├── Reels get highest engagement but we have almost no data
    └── Decision: Document in honest_gaps, accept for now
```

---

## PRIORITY ORDER

```
Fix first (foundation):
1. P4: Sector names (5 min) — tiny fix, unblocks lookups
2. P7: Sector facts (15 min) — brain accuracy
3. P5: Missing profiles (30 min) — brand engine needs these
4. P6: Product names (30 min) — quality gate needs these

Build then:
5. P1: Template library (45 min) — THE key missing piece
6. P3: Quality gate module (30 min) — needed before engine
7. P2: Content engine (1 hour) — ties everything together

Accept:
8. P8: Zero real data for 2 sectors — generated templates ok
9. P9: Folder structure — don't move files
10. P10: 31 reels — document and accept
```

*See [14_BUILD_ORDER](14_BUILD_ORDER.md) for step-by-step build instructions.*
