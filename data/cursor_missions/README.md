# Cursor Missions — file bus between Cursor and Claude Code

Task queue for split execution: **Cursor** writes missions, **Claude Code** (or `cursor_mission_consumer.py`) executes them.

## Layout

```
pending/    ← drop mission JSON here (Cursor)
running/    ← consumer moves mission here while executing
done/       ← result JSON + .log files land here
failed/     ← hard failures (unparseable mission, crash)
```

## Run pending missions

```bash
cd ~/Desktop/ogz-knowledge
python3 scripts/cursor_mission_consumer.py          # process all pending
python3 scripts/cursor_mission_consumer.py --once   # one mission only
```

## Mission types

| `type` | Behavior |
|---|---|
| *(omit)* or `commands` | Run `commands[]` shell lines sequentially |
| `brain-readiness` | Run `scripts/run_brain_readiness.py` (Phase A suite) |
| `orchestra` | Run brain-readiness runner; set `"workflow": "brain-readiness-test"` |

## Claude Code standing instruction

On session start or when Mohamed says **"check cursor missions"**:

```bash
python3 scripts/cursor_mission_consumer.py
```

Then read `data/cursor_missions/done/` for the latest result JSON.

## 24/7 operation

| Daemon | Interval | What |
|---|---|---|
| `com.ogz.brain-api` | KeepAlive | `brain_api` on :4140 |
| `com.ogz.cursor-missions` | 5 min | `cursor_24h_shift.py` — run one mission, hourly context refresh, brain heartbeat |

**Standing role:** `.cursor/rules/ogz-autonomous-mission-control.mdc` — chain waves until Mohamed texts in Cursor.

Logs: `~/logs/brain_api.*.log`, `~/logs/cursor_missions.*.log`, `~/logs/cursor_24h_shift.log`  
Heartbeat: `data/cursor_missions/done/24h-heartbeat.jsonl`  
**Full status:** `data/cursor_missions/done/autonomous-status-report.json`  
**Artifacts:** `data/cursor_missions/artifacts/` (wire-handoff, deepseek, etc.)
