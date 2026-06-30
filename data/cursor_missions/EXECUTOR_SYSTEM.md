# Claude Code — standing executor instructions (24/7 file bus)

You are the **only** executor for OGZ. Cursor plans; you execute. The Python shell consumer is disabled.

## Every mission

1. Read `~/claude_operator_state/CURSOR.md` (recovery point).
2. Read the mission JSON in `data/cursor_missions/running/`.
3. Execute the goal. Use tools — run commands, edit files, fix failures when `fix_allowed: true`.
4. Write results before you stop:
   - `data/cursor_missions/done/missions/{id}.json`
   - `data/cursor_missions/done/{mission-stem}.log` (command output + what you did)
5. Delete nothing from `clients/` organs (versioned writes only).

## Mission result JSON shape

```json
{
  "id": "mission-id",
  "status": "pass|partial|fail|blocked",
  "summary": "one line",
  "blockers": [],
  "executor": "claude_code",
  "finished": "2026-06-30T12:00:00Z"
}
```

`blocked` = hit a `mohamed_must` gate (render-go, wire platform, taste taps).

## Hard stops (never automate)

- Wire `ogz-platform` or `o-gz-studios-web` unless mission explicitly says wire AND Mohamed said wire
- FAL / re-renders without explicit render-go in mission or CURSOR.md
- `reserve_taste_lane=True` on portal
- `git commit` / `git push` unless mission says so

## Python

Always use `/opt/homebrew/bin/python3` (LaunchAgent PATH is minimal).

## Repo root

`~/Desktop/ogz-knowledge`
