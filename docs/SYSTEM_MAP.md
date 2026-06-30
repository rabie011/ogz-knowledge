# OGZ System Map

One-page inventory. **Control = Cursor (mobile + Mac).** Everything else is background or on-demand.

Updated: 2026-06-30

---

## Control plane (you touch this)

| Surface | Role | Mobile? | Status |
|---------|------|---------|--------|
| **Cursor chat** | Plan, go, stop, status, approve | Yes | **Primary** |
| **Portal** | Taste pair approvals only | Yes (browser) | Active |
| **localhost:4141** | Mac debug dashboard (live feed SSE) | No | Optional |
| **Telegram** (`ds_telegram`) | Private DeepSeek side chat | Yes | **Parked** — not commands |

Ask **status** in Cursor → reads `data/unified_status.txt` (plain English).

**Agent onboarding:** read [AGENTS.md](../AGENTS.md) · run `./scripts/setup_dev_env.sh` on the Mac.

---

## THE BRAIN (`brain_api.py` :4140)

**Must stay always-on** for pilots and platform wire.

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /extract?handle=` | Brand profile + coverage + ready gate |
| `POST /produce` | Post generation job |
| `GET /job/{id}` | Poll job |
| `POST /performance` | Engagement loop |

**Consumers:** `ogz-platform` (`lib/brain/client.ts`), fake platform tests, 3 pilots.

**LaunchAgent:** `com.ogz.brain-api` — **KEEP**

---

## BUILD MACHINES (on-demand or gated)

| Machine | Script | Who runs it |
|---------|--------|-------------|
| Render | `render_openclaw.py` | You say **render go** (FAL spend) |
| RABIE judge | `rabie_judge.py` | GPT-4o vision, harsh taste |
| HUMAIN | `humain_service.py` :4111 | Saudi Arabic caption pen |
| Consult | `consult.py` | DeepSeek + panel — Cursor calls on-demand |
| Shell missions | `claude_code_claim_executor.py` | **Misnamed** — runs shell only, not Claude LLM |
| Claude Code live | iTerm / IDE session | Code fixes — **not wired 24/7** |

---

## DATA (where truth lives)

| Path | What |
|------|------|
| `data/backlog.json` | Build steps |
| `data/rabie_verdicts.jsonl` | Judge memory |
| `data/cursor_missions/` | Mission bus: pending → done |
| `data/cursor_missions/artifacts/handoff/` | Pilot prefill + wire bundle |
| `data/unified_status.json` | Machine status |
| `data/unified_status.txt` | Plain English for Cursor mobile |
| `data/knowledge/` | raw → staged → indexed → domains |
| `data/mistake_registry.jsonl` | Scar log |
| `data/agents/AGENT_REGISTRY.json` | Agent roster |
| `~/claude_operator_state/CURSOR.md` | 6-month recovery context |

---

## Background services (LaunchAgents)

| Label | Script | Verdict |
|-------|--------|---------|
| `com.ogz.brain-api` | `brain_api_launcher.py` | **KEEP** |
| `com.ogz.executor` | `executor_daemon.py` | **Park** — only when you say go |
| `com.ogz.live-feed` | `live_feed_server.py` | Optional — Mac debug |
| `com.ogz.live-feed-digest` | `live_feed_digest.py` | Optional — Mac debug |
| `com.ogz.orchestra` | `orchestra_shift.py` | **PARKED** — Cursor replaces |
| `com.ogz.consult-shift` | `orchestra_consult_shift.py` | **PARKED** — consult on-demand |
| `com.ogz.memory-keeper` | `memory_keeper.py` | **PARKED** — run manually |
| `com.ogz.ds-telegram` | `~/agents/deepseek/ds_telegram.py` | Optional — not control |

Park/unpark: see [docs/DAEMON_PARK.md](DAEMON_PARK.md).

---

## What works today

- Brain API healthy, 3 pilots wired (albaik, eatjurisha, myfitness.sa)
- Platform brain client local (`~/ogz-platform`)
- Mission file bus + shell executor drains health/tests
- RABIE + HUMAIN + render pipeline (FAL gated)
- Knowledge: 15 docs indexed (cinematography, filmmaking)
- Consult on-demand via `consult.py`

---

## What is named wrong (honest)

| Says | Reality |
|------|---------|
| `claude_code_claim_executor.py` | **Shell mission executor** — no Claude reasoning |
| Live feed source `mac` | Was digest/daemon noise — now `digest` / `executor` |
| "Claude builds 24/7" | Shell scripts run 24/7; Claude Code needs live session |
| `BUILDER` agent in registry | Status: `not_wired_24h` |
| `:4141` as "one tab" | Mac-only; **phone = Cursor chat** |

---

## What is parked (organization phase)

- Auto consult every 15 min
- Auto memory mine every 6h
- Orchestra shift auto-queuing
- Telegram as command layer

Re-enable one daemon at a time only after Mode A is clean (see `MASTER_PLAN.md`).

---

## Mohamed gates (never automate)

- **render go** — FAL spend
- **wire** — production / Vercel tunnel
- Taste pairs / portal DELETE
- **stop** / **لخ** — creates `data/cursor_missions/.paused`

---

## Execution flow (target)

```
You (Cursor mobile/Mac)
    → plan / go / status
    → Cursor queues shell missions OR opens Claude Code live for code
    → Brain API (always on) serves extract/produce
    → Outputs: artifacts, posts, Slides links (future)
    → You approve in Cursor
```
