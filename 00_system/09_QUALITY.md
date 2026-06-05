# 🔍 QUALITY TREE
# 10 checks, auto-fix, scoring, learning store
# ⚠️ Rules exist but NOT an importable module yet
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 QUALITY GATE
│
├── ⚠️ CURRENT STATE
│   ├── Rules: defined in brain (quality_gate section)
│   ├── Problem: scattered across scripts, not importable
│   └── Fix needed: scripts/lib/quality_gate.py
│
├── 📊 SCORING SYSTEM
│   ├── Total: 100 points
│   ├── 90-100: excellent → ship immediately
│   ├── 80-89: good → ship with notes
│   ├── 70-79: pass → auto-fix applied first
│   ├── 60-69: refine loop triggered (1 iteration)
│   ├── 50-59: hard refine (2-3 iterations)
│   └── <50: hard reject — don't ship
│
├── ✅ 10 CHECKS (weighted total = 100)
│   │
│   ├── Check 1: Product name correct (weight: 20)
│   │   ├── Look up: brand_product_names in brain
│   │   ├── @albaik: "بروستد" must appear, not "مشوي" or "grilled"
│   │   ├── @pizzahutsaudi: "بيتزا" must appear, not "pizza"
│   │   └── Hard block if wrong → reject entirely
│   │
│   ├── Check 2: Brand hashtag present (weight: 15)
│   │   ├── Look up: signature_phrases in brand_profile
│   │   ├── @albaik: #البيك must appear
│   │   └── Score 0 if missing (no partial credit)
│   │
│   ├── Check 3: Saudi markers present (weight: 10)
│   │   ├── Must have at least one: وش, حيّاكم, الحين, كذا, يالله, طيب, حلو
│   │   ├── Auto-fix: add حيّاكم or الحين naturally if missing
│   │   └── Note: 9% frequency in gold captions is enough
│   │
│   ├── Check 4: No non-Saudi words (weight: 10)
│   │   ├── Forbidden: شنو, جذي, زين, تسحرني, تفضلوا, رائع, هيا بنا
│   │   └── Auto-fix: replace with Saudi equivalents
│   │
│   ├── Check 5: Occasion keyword present (weight: 10)
│   │   ├── Look up: occasion_required_words in brain
│   │   ├── founding_day: must contain تأسيس or يوم التأسيس
│   │   └── Auto-fix: add required word naturally
│   │
│   ├── Check 6: Arabic > English ratio (weight: 15)
│   │   ├── Count Arabic chars vs English chars
│   │   ├── Hard block if English-only → reject entirely
│   │   └── Flag if < 60% Arabic → rewrite
│   │
│   ├── Check 7: No cultural violations (weight: 20)
│   │   ├── Scan for: forbidden_props, forbidden_behaviors, forbidden_visuals
│   │   └── Hard block if found → reject entirely
│   │
│   ├── Check 8: Emoji count within limit (weight: 5)
│   │   ├── fashion: max 1 emoji
│   │   ├── f_and_b: max 2 emojis
│   │   ├── beauty: max 4 emojis (influencer culture)
│   │   └── Auto-fix: strip excess emojis
│   │
│   ├── Check 9: Hashtag count ≤ 2 (weight: 5)
│   │   ├── Count hashtags in caption
│   │   └── Auto-fix: strip hashtags beyond first 2
│   │
│   └── Check 10: No MSA formality (weight: 5)
│       ├── Forbidden MSA: تفضلوا, تسحرني, رائع, مذهل, استثنائي
│       └── Auto-fix: replace with Saudi equivalents
│
├── 🔧 AUTO-FIXES (applied before scoring)
│   ├── hashtag_limit: strip all hashtags beyond first 2
│   ├── emoji_limit: fashion>1 strip; any sector>3 strip
│   ├── product_name: replace wrong → correct (from brand_product_names)
│   ├── language_check: flag if English > Arabic chars
│   └── msa_replace:
│       ├── تفضلوا → تعالوا
│       ├── تسحرني → يعجبني
│       └── رائع → حلو
│
├── 🚫 HARD BLOCKS (reject entirely, no auto-fix)
│   ├── Cultural violation (any forbidden content found)
│   ├── Wrong brand name used
│   └── English-only output for Saudi brand
│
├── ⚡ SOFT WARNINGS (fix and continue)
│   ├── No Saudi markers → add حيّاكم or الحين naturally
│   ├── Missing occasion keyword → add to caption
│   └── Generic question ending → replace with brand hashtag
│
├── 📝 LEARNING STORE (logs/learning_store.jsonl)
│   │
│   ├── Location: ~/Desktop/ogz-knowledge/logs/learning_store.jsonl
│   ├── Current entries: 4
│   ├── Format: {handle, score, mistake, timestamp}
│   ├── Sample entry:
│   │   {
│   │     "handle": "pizzahutsaudi",
│   │     "score": 70,
│   │     "mistake": "Lack of Unique Selling Proposition...",
│   │     "timestamp": "2026-06-05T19:34:38"
│   │   }
│   │
│   ├── READ before every generation:
│   │   → inject as "avoid these mistakes in this generation"
│   │
│   └── WRITE after every failed generation (score < 80):
│       → log handle + score + what failed + why
│
└── 🛠️ HOW TO BUILD THE MODULE (scripts/lib/quality_gate.py)
    │
    ├── Functions to build:
    │   ├── check(text, brand, occasion) → {score, checks[], fixes[]}
    │   ├── auto_fix(text, brand, sector) → fixed_text
    │   ├── hard_block_check(text, brand) → True/False
    │   └── log_mistake(handle, score, mistake) → None
    │
    ├── Imports from:
    │   ├── intelligence_layer.json (brand_product_names, occasion_required_words,
    │   │   quality_gate, arabic_quality_rules, cultural_guardrails)
    │   └── normalize_gpt.py (sector normalization)
    │
    └── Usage in content_engine.py:
        from lib.quality_gate import check, auto_fix
        result = check(caption, brand="albaik", occasion="founding_day")
        if result["score"] < 80:
            caption = auto_fix(caption, brand="albaik", sector="f_and_b")
```

---
*See [08_ENGINE](08_ENGINE.md) for where quality gate fits in the pipeline.*
*See [14_BUILD_ORDER](14_BUILD_ORDER.md) for build steps.*
