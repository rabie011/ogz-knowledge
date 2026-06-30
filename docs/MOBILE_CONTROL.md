# Mobile control — work from Cursor on your phone

**You talk here (Cursor mobile).** The Mac Mini runs the brain. GitHub is the bridge.

Updated: 2026-06-30

---

## The loop

```
Phone (Cursor cloud agent)
    → edits GitHub repo · queues missions
         ↓
GitHub (ogz-knowledge)
         ↓
Mac Mini (pull + run + push status back)
         ↓
Phone asks "status" → agent reads data/unified_status.txt from repo
```

Cloud agents **cannot** SSH to your Mac. The Mac must **push truth** into the repo.

---

## What runs where

| Layer | Where | Role |
|-------|-------|------|
| **Cursor chat** | Cloud / phone | Plan, approve, status questions |
| **ogz-knowledge repo** | GitHub | Shared truth, scripts, missions |
| **brain_api :4140** | Mac Mini only | Extract/produce for pilots |
| **mac_sync** | Mac Mini (LaunchAgent) | Pull repo → refresh status → push to GitHub |
| **executor** | Mac Mini (optional) | Run shell missions from `pending/` |

---

## One-time Mac setup (when you're at the machine)

Run **one command**:

```bash
cd ~/Desktop/ogz-knowledge
git pull
chmod +x scripts/mac_onboard.sh
./scripts/mac_onboard.sh
```

This will:

1. Install Python deps (`setup_dev_env.sh`)
2. Park noisy daemons (consult-shift, memory-keeper, orchestra)
3. Keep **brain-api** alive
4. Install **mac-sync** (pushes status to GitHub every 5 min)
5. Optionally install **executor** (runs queued shell missions)
6. Push first status snapshot so phone can read it

Full checklist: [MAC_ONBOARDING.md](../data/cursor_missions/artifacts/MAC_ONBOARDING.md)

---

## From your phone (no Mac needed)

| You say | What happens |
|---------|----------------|
| **status** | Cloud agent reads `data/unified_status.txt` (+ `data/mac_status/sync_meta.json` for last Mac sync) |
| **go proposals** | Cloud agent edits repo / scaffolds `proposals/` |
| **queue …** | Cloud agent drops JSON to `data/cursor_missions/pending/` — Mac executor runs it when online |

If status says **BRAIN: DOWN** and `mac_last_sync` is old → Mac is offline or sync not installed yet.

---

## Mac sync daemon

| Item | Value |
|------|--------|
| Script | `scripts/mac_sync.py` |
| LaunchAgent | `com.ogz.mac-sync` |
| Interval | 5 minutes |
| Pushes | `data/unified_status.txt`, `data/unified_status.json`, `data/mac_status/*` |

Manual run:

```bash
cd ~/Desktop/ogz-knowledge
python3 scripts/mac_sync.py --push
```

Requires: Mac git credentials for `git push` (SSH key or credential helper).

---

## Mission bus (cloud → Mac)

Cloud agent writes `data/cursor_missions/pending/<id>.json`:

```json
{
  "id": "my-mission",
  "from": "cursor",
  "type": "commands",
  "goal": "Short description",
  "fix_allowed": false,
  "commands": [
    "cd ~/Desktop/ogz-knowledge && python3 scripts/unified_status.py --plain"
  ]
}
```

Mac **executor** (`com.ogz.executor`) drains these when loaded.

**Pause auto-work:** `touch data/cursor_missions/.paused`

---

## What cloud builds while you're away

- Docs, plans, mission JSON (in repo)
- `proposals/` scaffold (future `ogz-proposals` repo)
- Scripts that Mac will run later

## What only Mac can do

- `launchctl`, brain_api, render, FAL
- Google Drive service account files in `~/.abraham_env`
- Copy from `~/agents` into proposals repo

---

## Related docs

- [SYSTEM_MAP.md](SYSTEM_MAP.md) — inventory
- [DAEMON_PARK.md](DAEMON_PARK.md) — park/unpark
- [AGENTS.md](../AGENTS.md) — agent rules
- [MASTER_PLAN.md](../data/cursor_missions/artifacts/MASTER_PLAN.md) — two modes
