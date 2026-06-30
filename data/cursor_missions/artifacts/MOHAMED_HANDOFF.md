# Mohamed — control surface update

**One place to talk:** Cursor (mobile + Mac)

**Status on phone:** ask **status** in Cursor — reads `data/unified_status.txt` (Mac pushes every 5 min via `mac_sync`)

**When you reach the Mac:** run once:

```bash
cd ~/Desktop/ogz-knowledge && git pull && ./scripts/mac_onboard.sh
```

See `data/cursor_missions/artifacts/MAC_ONBOARDING.md` and `docs/MOBILE_CONTROL.md`.

**Mac debug only:** http://localhost:4141 (not your mobile control surface)

---

## What changed (2026-06-30)

| Before | After |
|--------|-------|
| Live feed said `mac` 72% of the time | Digest → `digest`, daemon → `executor` |
| `claude_code_claim_executor` implied Claude | Documented as **shell executor** only |
| 11 agents 24/7 | **Mode A:** brain always-on, rest on-demand |
| Telegram + :4141 + Cursor | **Cursor primary**; others parked/optional |
| Conflicting master plans | One `MASTER_PLAN.md` + `docs/SYSTEM_MAP.md` |

---

## What's running

| Service | Status |
|---------|--------|
| Brain API :4140 | **Always on** |
| consult-shift, memory-keeper, orchestra | **Parked** (see `docs/DAEMON_PARK.md`) |
| Executor | Optional — only when you say **go** |
| Claude Code 24/7 | **Not wired** — live session when needed |

---

## Pilots

Check **status** in Cursor for latest. Handoff bundle: `data/cursor_missions/artifacts/handoff/README.json`

---

## Your gates

- **render go** — FAL
- **wire** — Vercel production
- Taste pairs on portal
- **stop** / **لخ** — pause

---

## Docs

- Agent onboarding: `AGENTS.md` + `./scripts/setup_dev_env.sh` (run on Mac)
- System map: `docs/SYSTEM_MAP.md`
- Master plan: `data/cursor_missions/artifacts/MASTER_PLAN.md`
- Park/unpark daemons: `docs/DAEMON_PARK.md`
