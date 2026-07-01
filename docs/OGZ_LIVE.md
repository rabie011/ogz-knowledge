# OGZ Live — single truth file

**Canonical status:** `data/ogz_live.json` (full) · `data/ogz_live.txt` (15-line summary)

If it is not in `ogz_live.json` after Mac push, cloud treats it as **unknown**.

---

## Writers (Mac)

| Writer | When |
|--------|------|
| `scripts/mac_sync.py` | Every sync cycle (after drain + unified_status) |
| `scripts/claude_code_claim_executor.py` | Mission start / finish / claim / release |
| `scripts/agent_kit/log_event.py` | After each agent event (debounced 30s full rebuild) |

Generator: `python3 scripts/ogz_live.py`

---

## Readers

| Who | Read |
|-----|------|
| Cloud conductor | `status` → `data/ogz_live.txt` |
| Cloud deep check | `check Mac` → `data/ogz_live.json` |
| Mohamed mobile | Same files on GitHub after `mac_sync --push` |

---

## Key fields

- `healthy` — overall OK for cloud to proceed
- `stale` / `stale_reason` — sync or executor problems
- `executor.state` — `idle` · `running` · `jammed` · `stuck` · `paused`
- `executor.ghost_running` — missions in `running/` already in `done/`
- `agents.{ID}` — last heartbeat per agent

---

## Staleness rules

| Check | Threshold | Effect |
|-------|-----------|--------|
| File age / sync push | > 10 min | `stale: sync dead` |
| `running/` also in `done/` | any | `executor.state: jammed`, ghosts listed |
| Lock alive + same mission | > 30 min | `executor.state: stuck` |
| Pending + no drain | > 15 min | `executor.state: jammed` |
| `.paused` exists | — | `executor.state: paused` |

---

## Cloud recovery

When `healthy=false` or `stale=true`:

1. Read `stale_reason` and `executor.ghost_running`
2. Queue `queue-clear-stuck-running` (priority -5) if ghosts exist
3. Queue `executor-sync-always` if sync stale > 30 min
4. Only bother Mohamed on **connection blockers** (push fails twice, etc.)

---

## Legacy (kept, not canonical)

| File | Role |
|------|------|
| `data/unified_status.txt` | Mobile compat; embedded in ogz_live |
| `data/cursor_missions/LIVE_STATUS.md` | Orchestra scratch; points to ogz_live |
| `data/live_feed/events.jsonl` | Detailed log; last 15 copied into ogz_live |

See also: [CURSOR_ONLY.md](CURSOR_ONLY.md) · [AGENTS.md](../AGENTS.md)
