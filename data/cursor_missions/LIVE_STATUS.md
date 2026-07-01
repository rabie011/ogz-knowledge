# LIVE — Orchestra status

Updated: 2026-07-01T13:35:00Z (cloud view)

| Role | Who |
|------|-----|
| **Conductor** | Cursor cloud — plan, queue, read GitHub |
| **Hands** | Mac Mini — executor, brain `:4140`, bridge `:4150`, Tailscale |
| **You** | Mohamed — **Cursor only** |

## Two truths (read both)

| Source | Mac disk (hands report) | GitHub (cloud sees) |
|--------|-------------------------|---------------------|
| **Sync time** | ~`13:28Z` fresh | `02:03Z` **stale** |
| **Pending** | 0 | 6+ missions |
| **Running ghosts** | 2 (in done/) | 3 stuck |
| **Wire artifacts** | on disk ✓ | **404** — not pushed |

**Rule:** Cloud conductor trusts GitHub. Mac push closes the gap.

## Mac healthy (local report)

- Brain `:4140` — healthy
- Mac Bridge `:4150` — loaded
- Tailscale — `abarihms-mac-mini.tail174530.ts.net`
- Consult + PROPOSALS — ran locally
- Blocker — git push may fail on `weiblocks-export`

## Queued now

- `queue-clear-stuck-running.json` (priority -5) — clear ghosts + push

## Mohamed commands

`status` · `check Mac` · `go` · `stop`/`لخ` · `render go` · `wire` · **update handoff**

## Continuity

New chat → `CLOUD_AGENT_HANDOFF.md` + this file + `unified_status.txt`. Not in GitHub = cloud doesn't know.
