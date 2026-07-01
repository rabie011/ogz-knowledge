# OGZ Master Plan

Updated: 2026-06-30 · Cursor as one control surface

See also: [docs/SYSTEM_MAP.md](../docs/SYSTEM_MAP.md) · [docs/DAEMON_PARK.md](../docs/DAEMON_PARK.md)

---

## One rule

**You talk to Cursor (mobile + Mac).** Everything else is background or on-demand.

| Surface | Role |
|---------|------|
| **Cursor** | Plan, go, stop, status, approve |
| **Portal** | Taste pairs only |
| **:4141 live feed** | Mac debug — not your phone |
| **Telegram** | Parked — optional DS chat, not commands |

Ask **status** in Cursor → reads `data/unified_status.txt`.

---

## Mode A — Default (NOW)

**On-demand via Cursor.** Organize first, then work.

### Always-on (minimal)

- `com.ogz.brain-api` — extract/produce for 3 pilots + platform wire

### On-demand (you say go)

- Shell health/tests via mission queue + executor (optional)
- DeepSeek consult via `consult.py` (Cursor calls it)
- Claude Code **live session** for code fixes (not 24/7)
- RABIE / render / HUMAIN when producing posts (**render go** gates FAL)

### Parked (organization phase)

- `com.ogz.consult-shift` — auto DeepSeek every 15 min
- `com.ogz.memory-keeper` — auto history mine every 6h
- `com.ogz.orchestra` — auto queue board
- Telegram as command layer

### Phase A deliverables (done)

- [x] Mobile bridge wired — Mac pushes status to `main`, phone **status** works
- [x] `docs/SYSTEM_MAP.md` — inventory
- [x] `docs/MOBILE_CONTROL.md` — phone ↔ Mac ↔ GitHub loop
- [x] `scripts/mac_sync.py` + `mac_onboard.sh` — Mac pushes status for mobile
- [x] `AGENTS.md` — agent instructions + Mac vs cloud separation
- [x] `scripts/setup_dev_env.sh` — reproducible env setup
- [x] Honest naming (shell executor ≠ Claude Code)
- [x] `unified_status.txt` — plain English for mobile
- [x] Feed labels fixed (`digest`, not `mac`)
- [x] Agent registry v2 with status fields

### Open decisions (2026-06-30)

| Decision | Mohamed's choice |
|----------|------------------|
| Repo | **New clean repo** for proposals (brain stays in `ogz-knowledge`) |
| First track | **Proposals** — Drive then Slides |
| Archive after merge | `~/agents` (contains router + proposal pipeline; not named `abraham-agents`) |

See `data/cursor_missions/artifacts/DECISIONS.md` and `PROPOSAL_TRACK_PR_PLAN.md`.

### Phase B — Proposals track (next)

**Foundation:** [docs/AGENT_KIT.md](../docs/AGENT_KIT.md) — universal agent homes, Drive + Mac archive, append-only memory.

**Scaffold:** `proposals/` in repo — split to `ogz-proposals` on Mac.

**Source of truth:** Google Drive

- Amira proposal templates (quality bar)
- Quotations / pricing sheets

**Output:** Google Slides links (on-demand from Cursor — not built yet)

**Open question for Mohamed:** new clean repo for proposal tooling vs keep everything in `ogz-knowledge`? Decide before building.

### Phase C — OGZ creative posts

- 20 perfect posts, 3 pilots (brain/render mostly built)
- Production wire — cloudflared tunnel → Vercel (**wire** gate)

### Phase A next (pick one when ready)

1. Proposals (Drive → Slides) — Phase B
2. OGZ posts — Phase C
3. Clean repo decision — unblock proposal agent layout

---

## Mode B — Optional later (24/7 autonomy)

Only after Mode A is clean. Re-enable **one daemon at a time**:

1. Health cron every 6h (shell only)
2. Knowledge SEARCH on schedule
3. Consult-shift (DeepSeek auto-queue)

**Not** fake "Claude Code 24/7" until `type:agent` missions wake a real live session.

---

## Execution split (honest)

| Job | Who |
|-----|-----|
| Plan / queue | Cursor |
| Consult | DeepSeek on-demand (Mode A) or shift daemon (Mode B) |
| Shell tests | `claude_code_claim_executor.py` (misnamed — shell only) |
| Code / organs | Claude Code live |
| Creative / FAL | Brain + render — **render go** |
| Proposals / Slides | Future Cursor agent + Drive API |

---

## Mohamed gates (never automate)

- **render go** — FAL spend
- **wire** — production promote
- Taste pairs / portal
- **stop** / **لخ** — `data/cursor_missions/.paused`

---

## Your commands

| Say | Effect |
|-----|--------|
| **status** | Plain summary from `unified_status.txt` |
| **go** | Queue mission wave |
| **stop** / **لخ** | Pause auto-queuing |
| **learn [domain]** | SEARCH + LEARNER mission |
| **render go** | FAL missions |

---

## What NOT to build now

- Another chat UI
- Telegram command bot
- 11 agents running 24/7 while naming is wrong
- Treating :4141 as mobile control

---

## Success = organized

- Cursor on phone → **status** → truth in 30 seconds
- You know what runs always vs on-demand vs parked
- No "Claude Code" label on shell scripts
- One system map, one master plan, no contradictions
