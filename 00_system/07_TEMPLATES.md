# 📊 TEMPLATES TREE
# Scored template library — tier system, coverage, gaps
# ⚠️ THE TEMPLATE LIBRARY DOESN'T EXIST AS A FILE YET
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 TEMPLATES
│
├── ⚠️ CURRENT STATUS
│   ├── The DATA exists: 1,409 obs with real Arabic captions + real likes
│   ├── The GENERATED templates exist: 40 total (text strings in brain)
│   ├── But NO template_library.json file exists yet
│   └── Fix: Build scripts/build_template_library.py (see 14_BUILD_ORDER.md)
│
├── 🏆 TIER SYSTEM
│   │
│   ├── 🥇 GOLD — real caption, 1000+ likes (PROVEN)
│   │   ├── Source: real Instagram post, verified by Apify
│   │   ├── Trust: HIGHEST — proven engagement
│   │   ├── Use: first choice in style transfer
│   │   ├── Example (AlBaik, 11,716 likes):
│   │   │   "#برجر_فيليه_سمك.. طعم تغوص فيه 🫧 #البيك"
│   │   └── Counts: F&B:104 | Fashion:178 | Retail:13 | Beauty:4
│   │
│   ├── 🥈 SILVER — real caption, 100-999 likes (GOOD)
│   │   ├── Source: real Instagram post, verified
│   │   ├── Trust: good — real but not top performing
│   │   ├── Use: when gold < 3 for this sector+occasion
│   │   └── Counts: F&B:200 | Retail:83 | Fashion:54 | Beauty:49
│   │
│   ├── 🥉 BRONZE — real caption, 1-99 likes (OK)
│   │   ├── Source: real Instagram post, verified
│   │   ├── Trust: real but low performance
│   │   ├── Use: last resort when silver insufficient
│   │   └── Counts: F&B:259 | Retail:266 | Fashion:114 | Beauty:85
│   │
│   ├── 📝 GENERATED — created from gold/silver patterns (UNPROVEN)
│   │   ├── Source: GPT created from pattern analysis
│   │   ├── Trust: moderate — Saudi style but unproven
│   │   ├── Use: when no real captions exist for sector+occasion
│   │   └── Current: beauty(20) + retail(10) + healthcare(10) = 40 total
│   │
│   └── 📋 FALLBACK — cross-sector adaptation (LOW)
│       ├── Source: adapting templates from a different sector
│       ├── Trust: low — style may not match
│       ├── Use: ONLY for empty sectors (real_estate, healthcare)
│       └── Current: 0 built yet
│
├── 📋 WHAT EACH TEMPLATE SHOULD HAVE
│   ├── caption: Arabic text with {brand} and {product} placeholders
│   ├── tier: "gold" | "silver" | "bronze" | "generated" | "fallback"
│   ├── sector: canonical sector name
│   ├── occasion: occasion name or "evergreen"
│   ├── content_type: "image" | "video" | "carousel_slide"
│   ├── tone: "informative" | "playful" | "celebratory" etc.
│   ├── brand_source: which brand it came from (for real tiers)
│   ├── original_likes: real likes count (for real tiers)
│   └── original_url: Instagram URL (for real tiers)
│
├── 📊 COVERAGE MATRIX (what we have vs what we need)
│   │
│   │  Target: every sector × occasion needs ≥3 GOLD templates
│   │
│   ├── F&B — RICH ✅
│   │   ├── evergreen:      104 gold ← excellent
│   │   ├── riyadh_season:  21 gold
│   │   ├── ramadan:        12 gold
│   │   ├── jeddah_season:  14 gold
│   │   ├── eid_al_fitr:    3 gold (minimum)
│   │   ├── eid_al_adha:    4 gold
│   │   ├── national_day:   3 gold (minimum)
│   │   ├── founding_day:   1 gold ← needs generated
│   │   └── hajj_season:    1 gold ← needs generated
│   │
│   ├── FASHION — GOOD FOR EVERGREEN ✅, WEAK ELSEWHERE ⚠️
│   │   ├── evergreen:      22 gold ← good
│   │   ├── eid_al_fitr:    3 gold (minimum)
│   │   ├── hajj_season:    1 gold ← needs generated
│   │   └── all others:     0 gold ← needs generated
│   │
│   ├── RETAIL — WEAK ⚠️
│   │   ├── eid_al_adha:    7 gold ← only strong occasion
│   │   ├── eid_al_fitr:    1 gold ← needs more
│   │   └── all others:     0 gold ← needs generated
│   │
│   ├── BEAUTY — VERY WEAK ⚠️
│   │   ├── unknown/general: 4 gold (no occasion tagged)
│   │   └── all others:      0 gold ← needs generated
│   │
│   ├── REAL ESTATE — EMPTY ❌
│   │   └── all occasions: 0 gold, 0 silver, 0 bronze
│   │       → Use cross-sector fallback templates
│   │
│   └── HEALTHCARE — EMPTY ❌
│       └── all occasions: 0 gold, 0 silver, 0 bronze
│           → Use generated templates (10 exist as text)
│
├── 🛠️ HOW TO BUILD THE LIBRARY (scripts/build_template_library.py)
│   ├── Step 1: Scan all 3,816 observation files
│   ├── Step 2: Filter: Arabic caption + likes_count > 0
│   ├── Step 3: Assign tier: gold(1000+), silver(100-999), bronze(1-99)
│   ├── Step 4: Tag each: sector, occasion, content_type, brand, tone
│   ├── Step 5: Extract placeholders: replace brand name with {brand}
│   │          replace product name with {product}
│   ├── Step 6: Import 40 generated templates as "generated" tier
│   ├── Step 7: Generate fallbacks for empty sectors
│   ├── Step 8: Print coverage matrix
│   └── Output: 11_who_to_learn_from/template_library.json
│
├── 🔍 HOW TEMPLATES ARE SELECTED (in content engine)
│   ├── Query: sector + occasion + tier=gold
│   ├── If < 3 results: add tier=silver
│   ├── If < 3 results: add tier=bronze
│   ├── If < 3 results: add tier=generated
│   ├── If < 3 results: add tier=fallback (cross-sector)
│   └── Always cap at 5 templates (don't overwhelm LLM)
│
└── 📡 API ENDPOINT (not built yet)
    └── GET /api/templates?sector=f_and_b&occasion=ramadan&tier=gold
        Returns: [{caption, tier, original_likes, original_url, tone}, ...]
```

---
*See [08_ENGINE](08_ENGINE.md) for how templates feed the content pipeline.*
*See [14_BUILD_ORDER](14_BUILD_ORDER.md) for how to build the template library.*
