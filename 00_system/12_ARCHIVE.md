# 📦 ARCHIVE TREE
# 4-tier immutable storage, 61 brands, reprocessing
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 ARCHIVE
│
├── 🏛️ PHILOSOPHY: Never lose data. Everything is recoverable.
│   ├── Every extraction saves raw data FIRST
│   ├── Processed data can always be regenerated from raw
│   └── Intelligence can always be regenerated from processed
│
├── 4 TIERS (from ARCHIVE_STRATEGY.md)
│   │
│   ├── TIER 1: RAW — IMMUTABLE (never modify)
│   │   ├── Path: 11_who_to_learn_from/_raw_archive/{handle}/
│   │   ├── Format: 3 files per brand
│   │   │   ├── {handle}_{date}_apify_raw.jsonl — one post per line
│   │   │   ├── {handle}_{date}_metadata.json — account info
│   │   │   └── {handle}_{date}_extraction_log.json — what happened
│   │   ├── Content: FULL Apify response (every field)
│   │   │   ├── likes_count: real number from Instagram
│   │   │   ├── commentsCount: real number
│   │   │   ├── displayUrl: image URL
│   │   │   ├── videoUrl: video URL (if video)
│   │   │   ├── caption: exact text
│   │   │   └── ALL other Apify fields (even unused ones)
│   │   ├── Rule: NEVER delete, NEVER modify
│   │   ├── Rule: If file exists → SKIP re-extraction
│   │   └── Why: algorithm changes? Just reprocess. Data never lost.
│   │
│   ├── TIER 2: PROCESSED — observations/ folder
│   │   ├── Path: 11_who_to_learn_from/observations/{sector}/{ulid}.json
│   │   ├── Format: one JSON per post (schema-validated)
│   │   ├── Can regenerate: python3 scripts/reprocess_from_raw.py --handle X
│   │   └── Total: 3,816 files
│   │
│   ├── TIER 3: INTELLIGENCE — intelligence_layer.json
│   │   ├── Path: 11_who_to_learn_from/intelligence_layer.json
│   │   ├── Can regenerate: overnight_full_rebuild.py phases 3-4
│   │   └── Size: 82KB
│   │
│   └── TIER 4: DERIVED — analytics + templates + models
│       ├── Path: logs/ (analytics), models/ (ML), template_library.json
│       └── Can regenerate: run_all_analytics.py + build_template_library.py
│
├── 61 BRANDS IN RAW ARCHIVE
│   │
│   ├── Have substantial data (>1MB):
│   │   ├── @zara: 3,839KB
│   │   ├── @riyadhfood: 3,250KB
│   │   ├── @lcwaikiki: 3,056KB
│   │   ├── @hm: 3,020KB
│   │   ├── @namshi: 2,846KB
│   │   ├── @levelshoes: 2,781KB
│   │   ├── @bathandbodyworksarabia: 2,505KB
│   │   ├── @ajmalperfumes: 2,491KB
│   │   ├── @noon: 2,048KB
│   │   ├── @maxfashionmena: 2,064KB
│   │   ├── @fitnessfirstme: 1,947KB
│   │   ├── @asteribeautysa: 1,879KB
│   │   ├── @barnscoffee: 1,880KB
│   │   └── @mikyajy: 1,877KB
│   │
│   ├── Have some data (100KB-1MB):
│   │   └── @mcdonaldsksa, @tamimimarkets, @pandasaudi, @kyancafe,
│   │       @albaik, @hashibasha, @elixirbunn, @herfyfsc, @kuduksa,
│   │       @niceonesa, @crumblcookiespr, @myfitness.sa, @prettynature.official,
│   │       @kiabiksa, @mumzworld, @aldeebajofficial, @ounass, @randbfashion
│   │
│   └── Empty / failed extraction (0KB):
│       └── @abyat, @bootsksa, @carrefourksa, @danubesaudi, @dosecafe_sa,
│           @drcafe, @femi9, @footlockermiddleeast, @janburger,
│           @luluhypermarketsaudi, @ratio_sa, @rivafashion, @sivvi,
│           @sunsandsports, @thebodyshoparabia
│
└── 🔄 REPROCESSING (when you change the algorithm)
    │
    ├── What reprocess_from_raw.py does:
    │   ├── Reads raw archive JSONL for a brand
    │   ├── Matches posts by shortcode (from source_url)
    │   ├── Fills in: likes_count, comments_count, display_url, video_url
    │   └── Saves updated observation files
    │
    ├── Usage:
    │   python3 scripts/reprocess_from_raw.py --handle albaik --sector f_and_b
    │
    └── When to run:
        ├── After changing extraction schema (new fields added)
        ├── After fixing engagement calculation
        └── After realizing stored metrics were wrong
```

---
*See [01_DATA](01_DATA.md) for what's in the processed observations.*
*See [11_INFRA](11_INFRA.md) for extraction scripts.*
