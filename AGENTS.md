# AGENTS.md — instructions for Cursor / Claude Code / cloud agents

**Repo:** `ogz-knowledge` (THE BRAIN) · Mac Mini home: `~/Desktop/ogz-knowledge`

---

## Critical: where you run

| Action | Where |
|--------|--------|
| Edit docs, scripts, missions | **Any agent** (repo edits) |
| `launchctl`, park/unpark daemons | **Mac Mini only** — cloud agents cannot do this |
| `brain_api` always-on | **Mac Mini only** (`com.ogz.brain-api`) |
| FAL render spend | **Mohamed says `render go`** only |
| Production wire / Vercel | **Mohamed says `wire`** only |

**Cloud Cursor agent:** write files + output exact bash blocks for Mohamed to run on the Mac. Never assume LaunchAgents were changed unless verified on the Mac.

---

## Control surface (Mohamed)

- **Primary:** Cursor chat (mobile + Mac)
- **Status:** ask `status` → read `data/unified_status.txt` (Mac pushes via `mac_sync`)
- **Mac setup:** one command — `./scripts/mac_onboard.sh` (see [docs/MOBILE_CONTROL.md](docs/MOBILE_CONTROL.md))
- **Mac debug:** http://localhost:4141 (not mobile)
- **Portal:** taste pairs only
- **Telegram:** parked — optional DS side chat, not commands

See [docs/SYSTEM_MAP.md](docs/SYSTEM_MAP.md) and [data/cursor_missions/artifacts/MASTER_PLAN.md](data/cursor_missions/artifacts/MASTER_PLAN.md).

---

## Dev environment (first session on Mac)

```bash
cd ~/Desktop/ogz-knowledge
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```

This installs `requirements.txt` into `.venv`, verifies `unified_status.py`, checks brain `:4140`.

**Keys:** `~/.abraham_env` (never commit). Needs at minimum `BRAIN_API_TOKEN` for authenticated brain calls.

**Python:** 3.11+ · tested path `/opt/homebrew/bin/python3`

---

## Honest execution model

| Label | Reality |
|-------|---------|
| `claude_code_claim_executor.py` | **Shell executor** — runs `commands[]`, not Claude LLM |
| `BUILDER` agent | `not_wired_24h` — needs live Claude Code session |
| `EXECUTOR-SHELL` | Optional daemon; park during organization phase |

---

## Orchestra rules (Cursor)

1. **Plan and queue** — drop missions to `data/cursor_missions/pending/`
2. **Do not shell-execute** missions from Cursor unless Mohamed asks
3. **Consult DeepSeek** before big moves: `python3 scripts/consult.py "..."`
4. **Never automate:** render go, wire, taste pairs, client send

Mission types: `commands` (shell) vs `agent` (live Claude Code).

---

## Repo vs Mac commands

### Repo edits (agent can do)

- `docs/SYSTEM_MAP.md`, `MASTER_PLAN.md`, scripts, registry
- Queue JSON missions
- `unified_status.py` improvements

### Run on Mac (output for Mohamed)

Park noisy daemons:

```bash
for label in com.ogz.consult-shift com.ogz.memory-keeper com.ogz.orchestra; do
  launchctl unload ~/Library/LaunchAgents/${label}.plist 2>/dev/null || true
done
```

Keep brain alive:

```bash
launchctl load ~/Library/LaunchAgents/com.ogz.brain-api.plist
```

Full reference: [docs/DAEMON_PARK.md](docs/DAEMON_PARK.md)

---

## Data truth

| Path | Purpose |
|------|---------|
| `data/unified_status.txt` | Plain status for mobile (Mac pushes via mac_sync) |
| `data/mac_status/sync_meta.json` | Last Mac sync time + LaunchAgent state |
| `data/cursor_missions/` | Mission bus |
| `data/cursor_missions/artifacts/handoff/` | Pilot wire bundle |
| `data/rabie_verdicts.jsonl` | Judge memory |
| `data/agents/AGENT_REGISTRY.json` | Agent roster |
| `~/claude_operator_state/CURSOR.md` | 6-month recovery |

---

## Roadmap (v2 — after organize)

1. **Mac mobile bridge** — `mac_sync` + `mac_onboard.sh` (done in repo; run on Mac)
2. **ogz-proposals** — scaffold in `proposals/`; split + Drive on Mac
3. **Google Drive** — Amira templates + quotations
4. **Google Slides** — proposal output from Cursor
5. **OGZ posts** — brain/render, 20 perfect posts
6. **Mode B** — optional 24/7 daemons, one at a time

---

## Quick commands

```bash
python3 scripts/unified_status.py --plain    # status
python3 scripts/consult.py "question"        # DeepSeek
python3 scripts/validate_stack.py            # health checks
touch data/cursor_missions/.paused           # stop auto-queue
```
