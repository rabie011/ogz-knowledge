# OGZ Live — Mac debug feed

**Primary control:** Cursor (mobile + Mac). This page is **Mac-only** debug.

**Open:** [http://localhost:4141](http://localhost:4141)

**Status on phone:** ask **status** in Cursor → `data/unified_status.txt`

Pin this tab on Mac if you want local visibility — not code, not iTerm.

## What shows up

| Badge | Source |
|-------|--------|
| cursor | Missions Cursor queued |
| executor | Shell mission start / done (not Claude Code) |
| digest | 60s summary line |
| orchestra | Queue nudges, planning |
| brain | Brain API health |
| deepseek | Consult shift (if unparked) |
| live-feed | Server startup |

A **digest** line at the top summarizes the last ~25 events every 60 seconds.

## Start / restart

```bash
cd ~/Desktop/ogz-knowledge
chmod +x scripts/ogz_live.sh
./scripts/ogz_live.sh
```

This loads three LaunchAgents:

- `com.ogz.live-feed` — web UI on port 4141
- `com.ogz.executor` — drains `pending/` in background (no iTerm)
- `com.ogz.live-feed-digest` — rule-based summary every 60s

## Retired

- **iTerm OGZ Executor** — no longer opened automatically
- **tmux OGZ Mirror** — replaced by this feed

Debug logs still exist at `data/cursor_missions/done/*.log` if needed.

## Architecture

```
Cursor → pending/*.json + live_feed emit
orchestra_shift (5min) → brain heartbeat + feed
executor_daemon → claim_executor drain → feed
live_feed_server :4141 → your browser (SSE)
```
