# Cloud conductor — finish line (sent 2026-07-01)

Mohamed said **send** — complete this loop. No Terminal for Mohamed.

---

## Done (merged to `main`)

- **OGZ Live Truth** — `data/ogz_live.json` + `data/ogz_live.txt`
- `scripts/ogz_live.py`, mac_sync push, executor heartbeat, agent kit hook
- Missions: `queue-clear-stuck-running` (p -5), `executor-sync-always` (p -4)

---

## Your job now (cloud only)

1. **Confirm GitHub `main`** has `data/ogz_live.txt` after next Mac push (not before).
2. **Do not shell on Mac.** Mac executor + mac-sync drain `pending/` automatically.
3. **`status`** → read only `data/ogz_live.txt` on GitHub.
4. **`check Mac`** → read `data/ogz_live.json` — look at:
   - `healthy` / `stale_reason`
   - `executor.ghost_running` (must be `[]`)
   - `sync.last_push` (must be < 10 min old)
5. **When healthy=true** → resume **PROPOSALS** track (Google SA gate if blocked).
6. **If still stale >30 min after merge** → connection blocker: tell Mohamed Mac sync not pushing (one line, no bash blocks).

---

## Expected Mac sequence (automatic)

```
pull main → queue-clear-stuck-running (clears ghosts)
         → executor-sync-always (bootstrap)
         → mac_sync --push → ogz_live fresh on GitHub
```

---

## Do not

- Paste Terminal commands to Mohamed for normal work
- Edit `LIVE_STATUS.md` as truth (use `ogz_live.*`)
- Run `render go` / production `wire` without Mohamed saying so

---

**Report to Mohamed in one paragraph when `ogz_live.txt` shows HEALTH: OK.**
