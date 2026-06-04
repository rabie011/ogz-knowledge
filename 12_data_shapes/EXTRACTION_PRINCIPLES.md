# Extraction Principles — Never Lose Real Data Again

## The Rule: 3 Layers, Clearly Separated

Every observation has 3 layers. Never mix them.

### Layer 1: RAW (from Instagram/Apify — REAL, VERIFIABLE)
Store exactly what the platform returns. Never modify, never discard.

```json
"raw_metrics": {
  "likes_count": 3200,
  "comments_count": 145,
  "views_count": 48000,
  "saves_count": null,
  "shares_count": null,
  "follower_count_at_capture": 850000,
  "engagement_rate": 0.0039,
  "post_timestamp": "2026-01-15T14:30:00Z",
  "caption_text": "original caption exactly as posted",
  "hashtags": ["#البيك", "#صنع_في_السعودية"],
  "location_tag": "Riyadh, Saudi Arabia",
  "media_type": "IMAGE",
  "media_url": "https://...",
  "source_url": "https://www.instagram.com/p/XXX/",
  "account_handle": "albaik",
  "account_followers": 850000
}
```

**Rules:**
- NEVER throw away raw numbers
- NEVER modify the original caption
- ALWAYS store the timestamp from Instagram, not our extraction time
- ALWAYS store follower count at time of extraction (for engagement rate calculation)

### Layer 2: CALCULATED (deterministic — VERIFIABLE, REPRODUCIBLE)
Derived from Layer 1 using simple rules. Anyone can verify by re-running.

```json
"calculated": {
  "engagement_rate": 0.0039,
  "engagement_tier": "high",
  "word_count": 23,
  "hashtag_count": 5,
  "has_emoji": true,
  "day_of_week": "thursday",
  "hour_posted": 14,
  "aspect_ratio": "square_1x1",
  "caption_language_detected": "arabic",
  "caption_length_bucket": "medium"
}
```

**Rules:**
- engagement_tier thresholds must be DOCUMENTED and FIXED:
  - high: engagement_rate > 0.03 OR (likes + comments) > 500
  - medium: engagement_rate > 0.01 OR (likes + comments) > 100
  - low: everything else
- Every calculation must be reproducible from Layer 1 data
- NEVER use AI for Layer 2 — only math and rules

### Layer 3: AI-ESTIMATED (GPT classification — LABELED AS ESTIMATES)
AI-derived insights. Useful but not ground truth.

```json
"ai_classification": {
  "confidence_note": "AI-estimated by GPT-4o-mini — not verified by human",
  "patterns": ["heritage_storytelling_hook", "product_hero"],
  "emotion": "pride",
  "content_pillar": "community",
  "visual_lighting": "dramatic_moody",
  "visual_setting": "studio",
  "dialect": "gulf",
  "cultural_notes": "heritage reference, traditional props"
}
```

**Rules:**
- ALWAYS prefix with confidence_note
- NEVER present AI estimates as facts without disclosure
- AI estimates are for INSIGHT, real metrics are for PROOF
- When presenting to clients/stakeholders, always show Layer 1 numbers alongside Layer 3 insights

## Engagement Rate Calculation

```
engagement_rate = (likes + comments) / follower_count_at_capture

Tier:
  high   = engagement_rate ≥ 3.0% OR total_interactions ≥ 500
  medium = engagement_rate ≥ 1.0% OR total_interactions ≥ 100
  low    = below medium threshold
```

This is the industry-standard calculation. It's verifiable by anyone who can see the post.

## What Apify Returns (store ALL of these)

| Field | Apify Key | What It Is | Layer |
|-------|-----------|-----------|-------|
| Likes | likesCount | Real metric | 1 - RAW |
| Comments | commentsCount | Real metric | 1 - RAW |
| Views | videoViewCount | Real metric (video) | 1 - RAW |
| Caption | caption | Original text | 1 - RAW |
| Timestamp | timestamp | When posted | 1 - RAW |
| URL | url | Post link | 1 - RAW |
| Media URL | displayUrl | Image/video link | 1 - RAW |
| Type | type | Image/Video/Carousel | 1 - RAW |
| Location | locationName | Geo tag | 1 - RAW |
| Owner followers | ownerFullName | Account info | 1 - RAW |
| Hashtags | (extracted from caption) | Tags used | 2 - CALCULATED |
| Engagement rate | (likes+comments)/followers | Performance metric | 2 - CALCULATED |
| Pattern | GPT classification | Content pattern | 3 - AI-ESTIMATED |
| Emotion | GPT classification | Emotional tone | 3 - AI-ESTIMATED |

## The Proof Chain

When the brain recommends a pattern, it should show:

```
RECOMMENDATION: Use heritage_storytelling_hook
PROOF:
  - 13 real posts using this pattern
  - Average likes: 3,200 (vs sector average 850)
  - Average engagement rate: 3.8% (vs sector 1.2%)
  - Source: instagram.com/p/XXX, instagram.com/p/YYY (clickable)
  - AI confidence in pattern classification: moderate
```

This is what Alhareth can verify. Click the link, see the post, check the numbers.

## What Was Wrong Before

We had likes + comments from Apify → fed them to GPT → GPT said "high" → we stored "high" → threw away 3200 and 145 → presented "high" as proof → Alhareth said "this could be fake" → he was right.

## What's Fixed

Now: store 3200 likes + 145 comments + calculate 3.8% rate → ALSO ask GPT for pattern/emotion → store both → present: "3,200 likes (3.8% engagement) using heritage_storytelling_hook pattern (AI-classified)"

Real numbers + AI insights = trustworthy intelligence.
