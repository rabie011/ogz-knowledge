# Claude Code — SOLE EXECUTOR (standing orders)

**Executor runs in background. Mohamed watches http://localhost:4141 — not iTerm.**

## On every wake / session start (if using Claude Code manually)

1. Read `~/claude_operator_state/CURSOR.md` (recovery point)
2. Read `data/cursor_missions/LIVE_STATUS.md` (what's queued)
3. Prefer: let `com.ogz.executor` drain via `claude_code_claim_executor.py drain`
4. Manual drain:
   ```bash
   /opt/homebrew/bin/python3 scripts/claude_code_claim_executor.py drain
   ```

## Per mission

1. Move JSON from `pending/` → `running/` (claim script does this)
2. Execute `goal` — run commands, edit files, fix if `fix_allowed: true`
3. Write result to `done/missions/{id}.json` + log to `done/{id}.log`
4. Update `data/cursor_missions/LIVE_STATUS.md` with what you did

## Hard stops (never automate)

- Platform wiring (`ogz-platform`, `o-gz-studios-web`) until Mohamed says **wire**
- FAL spend / re-renders without explicit **render go**
- `reserve_taste_lane=True` on portal
- git commit/push unless mission says so or Mohamed asked

## Python path

Always use `/opt/homebrew/bin/python3` (LaunchAgent PATH is minimal).

## When blocked

Write `status: "blocked"` with `blocker: "mohamed_must — …"` and stop the queue. Do not fake success.
