# 🏷️ BRANDS TREE
# 39 profiles, DNA, product names, onboarding
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 BRANDS
│
├── 📊 COUNTS
│   ├── 60 brands in raw archive
│   ├── 39 brand profiles in brain
│   ├── 23 brands with verified real metrics
│   └── 113 target accounts (27 done, 86 skip)
│
├── 🏢 23 VERIFIED BRANDS (real metrics — click to verify)
│   │
│   ├── F&B (10 brands):
│   │   ├── @albaik           — avg 2,689 likes | 111 obs | carousel best
│   │   │   ├── voice: celebratory + playful
│   │   │   ├── tone: [celebratory, informative, urgent, playful]
│   │   │   ├── hashtags: [#انتم_والبيك_جيران, #صنع_في_السعودية]
│   │   │   ├── product: بروستد (NOT مشوي or grilled)
│   │   │   └── avoid: CSR posts, corporate programs
│   │   ├── @barnscoffee      — avg 660 likes | 110 obs
│   │   │   ├── tone: good Saudi tone already
│   │   │   └── fix: add more الحين/الآن urgency
│   │   ├── @pizzahutsaudi    — avg 14 likes | 120 obs ← WEAK
│   │   │   ├── problem: generic tone, no hook
│   │   │   └── fix: copy AlBaik structure
│   │   ├── @mcdonaldsksa     — avg 1,090 likes | 12 obs
│   │   │   └── best format: giveaway/competition posts
│   │   ├── @kyancafe         — avg 327 likes | 66 obs
│   │   ├── @elixirbunn       — avg 175 likes | 30 obs
│   │   ├── @altazaj_fakieh   — avg 6,530 likes | 3 obs ← high but few obs
│   │   ├── @hashibasha       — avg 82 likes | 102 obs
│   │   ├── @herfyfsc         — avg 88 likes | 4 obs
│   │   └── @riyadhfood       — avg 243 likes | 4 obs
│   │
│   ├── Fashion (5 brands):
│   │   ├── @zara             — avg 50,836 likes | 63 obs ← global scale
│   │   │   └── note: mostly non-Arabic captions (English/Spanish)
│   │   ├── @hm               — avg 6,074 likes | 88 obs
│   │   ├── @maxfashionmena   — avg 886 likes | 92 obs ← best Saudi fashion
│   │   │   ├── style: long captions (300+ chars), aspirational
│   │   │   └── example: "البني الشوكولاتة يتصدر إطلالات هذا الصيف 🤎"
│   │   ├── @kiabiksa         — avg 44 likes | 72 obs
│   │   └── @randbfashion     — avg 8 likes | 31 obs ← very weak
│   │
│   ├── Retail (4 brands):
│   │   ├── @tamimimarkets    — avg 167 likes | 125 obs
│   │   ├── @pandasaudi       — avg 205 likes | 113 obs
│   │   ├── @mumzworld        — avg 150 likes | 118 obs
│   │   └── @aldeebajofficial — avg 122 likes | 6 obs
│   │
│   └── Beauty (4 brands):
│       ├── @mikyajy          — avg 636 likes | 96 obs (max 48,464 — outlier)
│       ├── @asteribeautysa   — avg 169 likes | 16 obs
│       ├── @lifestyleshops   — avg 1 like ← ghost metrics
│       └── @gissahperfumes   — avg 1 like ← ghost metrics
│
├── 📋 BRAND PROFILE STRUCTURE (7 fields each)
│   ├── sector: canonical name (f_and_b, beauty_personal_care, etc.)
│   ├── voice: 1-2 sentence description of brand voice
│   ├── tone: list of tone descriptors
│   ├── language: "arabic-first" | "bilingual" | "english-first"
│   ├── arabic_style: "saudi" (NOT "colloquial_gulf")
│   ├── signature_phrases: list of brand hashtags
│   └── best_format: "carousel_slide" | "video" | "image"
│
├── ⚠️ BRANDS MISSING FROM PROFILES (have metrics but no profile)
│   ├── @zara
│   ├── @hm
│   ├── @kiabiksa
│   ├── @randbfashion
│   ├── @mikyajy ← most important missing
│   ├── @pandasaudi
│   ├── @mumzworld
│   └── @aldeebajofficial
│
├── ⚠️ WRONG SECTOR NAMES IN 3 PROFILES
│   ├── OGZ-BEAUTY-Reference-001: "beauty" → fix to "beauty_personal_care"
│   ├── OGZ-BEAUTY-Reference-002: "beauty" → fix to "beauty_personal_care"
│   └── OGZ-RETAIL-Reference-001: "retail" → fix to "retail_lifestyle"
│
├── 🏷️ BRAND PRODUCT NAMES (currently only 3/23)
│   │
│   ├── @albaik:
│   │   ├── correct: بروستد
│   │   └── wrong: [مشوي, مقلي, grilled]
│   ├── @pizzahutsaudi:
│   │   ├── correct: بيتزا
│   │   └── wrong: [pizza]
│   ├── @barnscoffee:
│   │   ├── correct: قهوة مختصة
│   │   └── wrong: [coffee]
│   └── ⚠️ 20 other brands: NO product name enforcement
│
└── 🔄 BRAND ONBOARDING (how a new brand enters the system)
    ├── Step 1: Add to target_accounts.json
    │   Fields: handle, brand_name, sector, sub_sector, priority, quota, status
    ├── Step 2: Extract via Apify → save raw archive first
    ├── Step 3: Process → observations in observations/{sector}/ folder
    ├── Step 4: Build brand profile from obs data
    │   Extract: common tones, hashtags, caption styles
    ├── Step 5: Add product names (from real captions)
    ├── Step 6: Add to real_metrics in brain
    ├── Step 7: Add reference_examples (top 5 posts)
    └── Step 8: Run guard_data_quality.py to validate
```

---
*See [02_BRAIN](02_BRAIN.md) for brand_profiles section.*
*See [13_PROBLEMS](13_PROBLEMS.md) for full list of missing profiles.*
