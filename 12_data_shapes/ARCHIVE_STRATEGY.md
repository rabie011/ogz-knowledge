# Archive Strategy — Never Re-Extract

## Principle: Extract Once, Store Forever, Process Many Times

Raw data is the most expensive thing we have. Apify costs money, Instagram rate-limits, posts get deleted. Every extraction is irreplaceable. Store it ALL.

## 4-Tier Storage

### Tier 1: Raw Archive (NEVER MODIFY)
**What:** Full Apify JSON response per account extraction
**Where:** `11_who_to_learn_from/_raw_archive/{handle}/{date}/`
**Format:** `{handle}_{date}_apify_raw.jsonl` — one line per post, full Apify response
**Size:** ~2KB per post × 125 posts × 100 accounts = ~25 MB
**Rule:** NEVER modify, NEVER delete. This is the source of truth for all re-processing.

```
11_who_to_learn_from/_raw_archive/
  albaik/
    2026-05-26/
      albaik_20260526_apify_raw.jsonl    ← full Apify response per post
      albaik_20260526_metadata.json       ← extraction params, Apify run ID
  barnscoffee/
    2026-05-26/
      barnscoffee_20260526_apify_raw.jsonl
      barnscoffee_20260526_metadata.json
```

### Tier 2: Media Archive (downloaded files)
**What:** Actual images and videos downloaded from Instagram
**Where:** `11_who_to_learn_from/_inbox/{sector}/{handle}/`
**Format:** `{shortcode}.jpg` or `{shortcode}.mp4`
**Size:** Currently 3.6 GB (7,322 files) — this is already stored
**Rule:** Download media AT extraction time. Instagram URLs expire within days.

### Tier 3: Processed Observations (current system)
**What:** Our parsed, classified observation JSONs
**Where:** `11_who_to_learn_from/observations/{sector}/`
**Format:** `{ULID}.json` with Layer 1 (raw metrics) + Layer 2 (calculated) + Layer 3 (AI)
**Size:** 8.6 MB (2,730 files)
**Rule:** Can be regenerated from Tier 1 + Tier 2 if needed.

### Tier 4: Intelligence (derived)
**What:** Analytics, intelligence layer, brand DNA, patterns
**Where:** `logs/`, `11_who_to_learn_from/intelligence_layer.json`
**Size:** ~20 MB total
**Rule:** Can be regenerated from Tier 3 at any time by running scripts.

## Backup Locations

| Tier | Local Disk | GitHub | Google Drive | VPS |
|------|-----------|--------|-------------|-----|
| 1 Raw Archive | ✅ | ✅ (if <100MB) | ✅ | ✅ |
| 2 Media | ✅ | ❌ (too large) | ✅ | ❌ |
| 3 Observations | ✅ | ✅ | ✅ | ✅ |
| 4 Intelligence | ✅ | ✅ | ✅ | ✅ |

## What to Store Per Extraction

When extracting an account, save these files:

```
1. {handle}_{date}_apify_raw.jsonl
   - Full Apify response for every post
   - MUST include: likesCount, commentsCount, timestamp, caption, displayUrl, type

2. {handle}_{date}_metadata.json
   {
     "handle": "albaik",
     "extraction_date": "2026-05-26T10:30:00Z",
     "apify_run_id": "abc123",
     "apify_actor": "apify/instagram-post-scraper",
     "posts_fetched": 125,
     "sector": "f_and_b",
     "extractor_version": "extract_account_obs.py v2.1"
   }

3. Downloaded media files (.jpg, .mp4)
   - One per post, named by shortcode
   - Download AT extraction time — URLs expire
```

## Recovery Scenarios

| Scenario | Recovery Path |
|----------|--------------|
| Observation JSON corrupted | Re-process from Tier 1 raw archive |
| Instagram deletes a post | We have the media file + raw data |
| Apify changes their API | Raw archive has the old format, re-parse |
| Need to re-classify with better AI | Re-process Tier 1 → new Tier 3 |
| Need engagement metrics we didn't extract | Raw archive has full Apify response including ALL metrics |
| GitHub goes down | Google Drive + local disk + VPS have copies |
| Mac Mini dies | GitHub + Google Drive + VPS have copies |

## Implementation

Update `extract_account_obs.py` to:
1. Save raw Apify response to `_raw_archive/` BEFORE any processing
2. Download media files to `_inbox/` BEFORE any processing
3. THEN parse and classify into observations

The raw archive is the insurance policy. Everything else can be rebuilt from it.
