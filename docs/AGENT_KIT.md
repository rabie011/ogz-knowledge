# Agent Kit — universal foundation for any OGZ agent

**Build once. Every agent plugs in the same way.**  
Updated: 2026-07-01 · Control = Cursor only · Mac executes · Drive = design/archive truth

---

## The 3 layers (every agent)

| Layer | Where | Holds |
|-------|--------|--------|
| **Think** | GitHub + Cursor | Plans, prompts, registry, mission queue, learnings (jsonl) |
| **Run** | Mac Mini | Scripts, API keys, brain `:4140`, shift daemon |
| **Archive** | Google Drive + Mac disk | Templates, finished decks, PDFs, exports — **never lose work** |

```
You (Cursor phone/Mac)
    → data/cursor_missions/pending/*.json
    → data/agent_kit/registry.json
         ↓
Mac: agent home (e.g. ~/Desktop/ogz-proposals)
    → run → events.jsonl → learn
    → archive copy → ~/OGZ-Archive/agents/{AGENT_ID}/
    → push manifest → Google Drive archive folder
         ↓
Cursor reads status + events → grows memory
```

---

## Agent home layout (copy per agent)

Every agent repo or folder uses the same skeleton:

```
{agent_home}/
├── AGENTS.md                 # how Cursor + Mac run this agent
├── requirements.txt
├── scripts/                  # runnable entrypoints
├── lib/                      # router, helpers
├── prompts/                  # system prompts (versioned in git)
├── knowledge/                # durable facts (clients, references)
│   ├── clients/              # client bibles (.md)
│   ├── reference/            # gold examples
│   └── learnings.jsonl       # append-only — what worked (agent memory)
├── data/
│   ├── drive_manifest.json     # Drive file IDs (no secrets)
│   ├── assets_index.json       # pointers to templates + archive
│   └── runs/                   # active runs (gitignored heavy files)
└── events/
    └── agent_events.jsonl      # append-only run log (or symlink to brain data/)
```

Register each home in `data/agent_kit/registry.json`.

---

## Google Drive layout (shared across agents)

Create once under your OGZ shared drive:

```
OGZ Agents/
├── _manifest.json              # folder IDs (maintained by drive_list.py)
├── PROPOSALS/
│   ├── templates/              # Amira-quality masters
│   ├── quotations/             # pricing sheets
│   └── archive/{client}/{yyyy-mm}/   # finished decks + exports
├── CREATIVE/
│   └── archive/...
└── SHARED/
    ├── brand/                  # OGZ brand assets
    └── clients/                # optional shared client folders
```

**Rule:** Git stores **IDs + manifests**. Drive stores **heavy files**.

---

## Mac archive layout (local mirror)

```
~/OGZ-Archive/
└── agents/
    └── {AGENT_ID}/
        └── {yyyy-mm-dd}_{run_ulid}/
            ├── manifest.json     # what this run was, links to Drive
            ├── inputs/           # brief, client slug, prompt snapshot
            ├── outputs/          # slides export, json, screenshots
            └── events.jsonl      # copy of run events
```

Mac archive = fast local recovery. Drive archive = team + phone access.

---

## Memory model (grow, don't restart)

| File | Purpose |
|------|---------|
| `knowledge/learnings.jsonl` | Success patterns — "ROSHN deck: use quotation sheet X" |
| `events/agent_events.jsonl` | Every run — inputs, outputs, approve/reject |
| `data/mistake_registry.jsonl` | Brain-wide scars (already exists) |
| `logs/learning/*.jsonl` | Decisions + calibration (`learning_system.py`) |

**Append-only.** Corrections = new events, not edits.

### Continuity (cloud visibility)

Each agent also reports heartbeat into **`data/ogz_live.json`** → `agents.{AGENT_ID}`:

- `last_seen` — timestamp of latest `log_event.py` call
- `state` — `active` / `idle`
- `summary` — one line from last event

Long-term memory stays in local `events/agent_events.jsonl`; cloud reads the aggregated map in ogz_live after Mac push. See [OGZ_LIVE.md](OGZ_LIVE.md).


```json
{
  "event_ulid": "01JXXXXXXXXXXXXXXXXXXXXXX",
  "agent_id": "PROPOSALS",
  "event_type": "run_started|run_completed|approved|rejected|harvested|learned",
  "timestamp": "2026-07-01T12:00:00Z",
  "client_slug": "roshn",
  "run_ulid": "01JYYYYYYYYYYYYYYYYYYYYYY",
  "artifacts": {
    "slides_url": "https://docs.google.com/...",
    "drive_folder_id": "...",
    "mac_archive_path": "~/OGZ-Archive/agents/PROPOSALS/..."
  },
  "summary": "One line for Cursor status",
  "provenance": {
    "source": "proposal_agent.py",
    "date_added": "2026-07-01T12:00:00Z",
    "confirmer": "Mohamed",
    "confidence": "confirmed",
    "scope": "brand:roshn"
  }
}
```

Log with: `python3 scripts/agent_kit/log_event.py --agent PROPOSALS --type run_completed ...`

---

## Lifecycle (any agent)

1. **Bootstrap** — `bootstrap_home.py` creates folders + registry entry  
2. **Harvest** — one-time copy from old code (`~/agents`, Claude Code output)  
3. **Index Drive** — `drive_list.py` → `drive_manifest.json`  
4. **On-demand run** — you say go in Cursor → mission or script  
5. **Archive** — `archive_run.py` copies to Mac + updates Drive manifest  
6. **Learn** — append `learnings.jsonl` + event  
7. **24h shift** (optional later) — Mac LaunchAgent: index, test, one small learn task  

---

## What NOT to build

- Second chat UI (Telegram commands)  
- Qdrant/mem0 empire per agent  
- Postgres as source of truth  
- Auto-send to clients  

---

## First agent: PROPOSALS

| Item | Path |
|------|------|
| Registry | `data/agent_kit/registry.json` → `PROPOSALS` |
| Mac home | `~/Desktop/ogz-proposals` |
| Harvest from | `~/agents` + Claude Code work |
| Drive | `OGZ Agents/PROPOSALS/` |

Say **proposals go** → queues harvest mission after foundation lands.

---

## Consult DeepSeek

Before big architecture moves: `python3 scripts/consult.py "..."` on Mac (needs `DEEPSEEK_API_KEY` in `~/.abraham_env`). Cloud agent queues consult missions if keys are Mac-only.

---

See: `data/agent_kit/README.md` · `PROPOSAL_TRACK_PR_PLAN.md` · `CONVENTIONS.md`
