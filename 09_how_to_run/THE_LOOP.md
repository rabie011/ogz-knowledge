cat > 09_how_to_run/THE_LOOP.md <<'EOF'
# THE LOOP — how the system improves itself (June 11, 2026)

```
Mohamed rates at /cross-compare (both-bad = B · winner rating 1-5)
        │
        ├─→ ratings ≥4 → scripts/gold_from_ratings.py → GOLD per-brand few-shot
        │   (v5_prompt leads few-shot with GOLD — founder taste outranks engagement)
        │
        ├─→ at 30+ ratings → scripts/calibrate_judge.py vs scorer_v2
        │   (the judge is NEVER trusted uncalibrated — the AI-judge lesson)
        │
        └─→ both-bad reasons → new caption_filter.py patterns (bans live in CODE,
            never in prompts — pink-elephant doctrine)

Weekly: scripts/check_archive_freshness.py --enqueue   (archives >30d re-extract)
After re-extraction: build_brand_dna_v2.py + _v3.py --force   (DNA follows the feed)
Monthly: build_pattern_engagement_evidence.py   (the library stays predictive)

Run after every rating session: python3 scripts/gold_from_ratings.py
Scoreboard: GET /api/cross/stats → .scoreboard (both-bad rate, avg rating by model,
queue by prompt version)
