# Cursor Missions — file bus (Orchestra ↔ Claude Code LIVE)

**Cursor** = orchestra (plan + queue). **Claude Code** = sole executor (live session you watch).

## Watch Claude work

1. **Claude Code app** → `/resume` → session **OGZ Executor**
2. **iTerm/Terminal** — orchestra opens a tab when missions are pending
3. **Status board** — `LIVE_STATUS.md` (this folder)

## Layout

```
pending/     ← Cursor drops mission JSON here
running/     ← Claude moves mission while executing
done/        ← results + .log files
.wake_claude ← Cursor touches this to request a live session
```

## Claude Code standing orders

Read `CLAUDE_CODE_STANDING.md` on every session start.

```bash
python3 scripts/claude_code_claim_executor.py claim
python3 scripts/claude_code_claim_executor.py run-next   # repeat until empty
python3 scripts/claude_code_claim_executor.py release
```

## Orchestra daemon (does NOT execute missions)

| Daemon | Interval | What |
|---|---|---|
| `com.ogz.orchestra` | 5 min | Brain heartbeat, queue health missions, **wake Claude live** |
| `com.ogz.brain-api` | KeepAlive | brain_api :4140 |

Install orchestra (replaces old cursor-missions consumer):

```bash
launchctl unload ~/Library/LaunchAgents/com.ogz.cursor-missions.plist 2>/dev/null
cp deploy/launchagents/com.ogz.orchestra.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ogz.orchestra.plist
```

## Shell consumer — DISABLED

`cursor_mission_consumer.py` is blocked. Claude Code only.

Emergency: `ALLOW_SHELL_CONSUMER=1 python3 scripts/cursor_mission_consumer.py --once`
