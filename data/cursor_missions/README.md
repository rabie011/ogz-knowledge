# Cursor Missions — file bus

**Cursor** = plan + queue (mobile + Mac). **Shell executor** = `commands` missions. **Claude Code live** = `agent` missions only.

See [docs/MOBILE_CONTROL.md](../../docs/MOBILE_CONTROL.md) · [docs/DAEMON_PARK.md](../../docs/DAEMON_PARK.md)

## Layout

```
pending/     ← Cursor drops mission JSON here
running/     ← executor moves mission while executing
done/        ← results + .log files
.paused      ← touch to stop auto-queuing (say stop / لخ)
.wake_claude ← agent missions need live Claude Code session
```

## Mission types

| type | Who runs |
|------|----------|
| `commands` | Shell executor (`claude_code_claim_executor.py` — historical name) |
| `agent` | Claude Code **live** — flagged, not shell-run |
| `brain-readiness` | Shell via executor |

## Drain queue (Mac)

```bash
python3 scripts/claude_code_claim_executor.py drain
```

Or load `com.ogz.executor` LaunchAgent — drains in background.

## Mode A (default) — parked

- `com.ogz.orchestra` — **parked** (Cursor replaces)
- `com.ogz.consult-shift` — **parked**
- `com.ogz.memory-keeper` — **parked**

**Keep:** `com.ogz.brain-api` · `com.ogz.mac-sync` · optional `com.ogz.executor`

## Pause without unloading

```bash
touch data/cursor_missions/.paused
```

## Status on phone

Ask **status** in Cursor → `data/unified_status.txt` (Mac pushes via `mac_sync`).
