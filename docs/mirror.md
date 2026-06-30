# OGZ live mirror

One terminal window for everything outside the Claude executor session.

## Open

```bash
cd ~/Desktop/ogz-knowledge
./scripts/ogz-mirror.sh
```

## Panes

| Pane | Stream |
|------|--------|
| pending | New missions in `data/cursor_missions/pending/` |
| done-log | Latest `data/cursor_missions/done/*.log` |
| orchestra | `~/logs/orchestra_shift.log` |
| status | `LIVE_STATUS.md` refreshed every 10s |

## Two windows

1. **OGZ Executor** — Claude Code live (`wake_claude_code_live.sh`)
2. **OGZ Mirror** — this tmux session

## Log rotation

Run daily or before long shifts:

```bash
./scripts/archive_mission_logs.sh
```

Moves `done/*.log` older than 24h to `data/cursor_missions/archive/logs/`.

## Heartbeat errors

```bash
tail -f data/cursor_missions/done/24h-heartbeat.jsonl | grep -E '"status":"(error|missed)'
```
