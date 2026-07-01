# LIVE — Orchestra status

Updated: 2026-07-01T06:30:00Z

| Role | Who |
|------|-----|
| **Conductor** | Cursor cloud — plan, queue, read artifacts |
| **Hands** | Mac Mini — executor, brain, keys, Tailscale |
| **You** | Mohamed — **Cursor only** (phone + Mac) |

## Right now

- **Mac sync:** `2026-07-01T02:03Z` — **STALE** (needs Mac push)
- **Brain:** healthy `:4140` (last report)
- **Queue:** 6 pending · 3 stuck in `running/`
- **Track:** PROPOSALS + wire (Tailscale / Mac Bridge claimed on Mac, **not on GitHub yet**)

## Pending

- `executor-recover-stuck.json` (priority -3)
- `wire-go.json` (-2)
- `wire-test-go.json` (-1)
- `mac-post-reboot-check.json`
- `tailscale-brain-wire.json`
- `mac-organize-cleanup.json`

## Stuck running (fix first)

- `agent-run-now.json`
- `consult-mirror-proposals-foundation.json`
- `proposals-foundation-go.json`

## Artifacts waiting on Mac push

- `data/mac_status/remote_endpoint.json`
- `artifacts/WIRE_STATUS.json`
- `artifacts/mac_diagnostic_latest.json`
- `artifacts/consult_mirror_proposals_latest.txt`
- `artifacts/proposals_agent_demo_latest.txt`

## Mohamed commands

`status` · `check Mac` · `go` · `stop`/`لخ` · `render go` · `wire` · **update handoff**

## Continuity rule

New chat → read `artifacts/CLOUD_AGENT_HANDOFF.md` + this file + `unified_status.txt`. If not in repo, it didn't happen.
