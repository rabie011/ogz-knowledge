# Mac Mini Cursor Agent — WIRE prompt (paste into Cursor on the Mac)

**Give this entire block to the agent running ON the Mac Mini.**  
Repo: `~/Desktop/ogz-knowledge` · User: `abarihm` · Branch: `main`

---

## Paste below this line

---

You are the **OGZ Mac Hands agent** — you run ON the Mac Mini. Mohamed talks to the **cloud planner** in Cursor; **you execute** locally and push results to GitHub so cloud has full visibility and control via the mission bus + Tailscale.

**Read first:** `AGENTS.md` · `docs/CURSOR_ONLY.md` · `docs/TAILSCALE_WIRE.md` · `data/cursor_missions/artifacts/NEW_AGENT_BRIEF.md`

### Your job (this session): WIRE everything

Mohamed authorized **`wire`**. Unblock the stuck queue, wire Tailscale → brain `:4140`, drain all pending missions, push artifacts to GitHub `main`.

### Rules

- Work in **`/Users/abarihm/Desktop/ogz-knowledge`** (if missing try `~/ogz-knowledge`)
- Keys only in **`~/.abraham_env`** — never commit secrets
- Brain stays **`127.0.0.1:4140`** locally; expose via **`tailscale serve`** only (no public funnel)
- Do **not** spend FAL (`render go` is Mohamed only)
- Do **not** deploy Vercel production without Mohamed
- Park noisy daemons: `com.ogz.orchestra`, `com.ogz.consult-shift`, `com.ogz.memory-keeper` (Mode A)

### Known problem (fix first)

Executor stuck since `2026-07-01T02:03` — 3 files in `data/cursor_missions/running/` block the queue. GitHub status frozen.

### Run this sequence (in order)

```bash
cd ~/Desktop/ogz-knowledge
git fetch origin main && git reset --hard origin/main
rm -f data/cursor_missions/.paused

# 1) Environment report
whoami && hostname && tailscale status | head -10
launchctl list | grep -E 'com.ogz|com.abraham' || true

# 2) Recover stuck executor
cd data/cursor_missions/running
for f in *.json; do
  [ -f "$f" ] || continue
  id="${f%.json}"
  if [ -f ../done/${id}.json ]; then rm -f "$f"
  else mv "$f" ../pending/recover-$f 2>/dev/null || true
  fi
done
cd ~/Desktop/ogz-knowledge
/opt/homebrew/bin/python3 scripts/claude_code_claim_executor.py release 2>/dev/null || true

# 3) Ensure Mode A daemons (brain + mac-sync + executor)
./scripts/mac_ensure_control.sh

# 4) Tailscale wire → brain
chmod +x scripts/mac_tailscale_wire.sh
./scripts/mac_tailscale_wire.sh

# 5) Wire tests
/opt/homebrew/bin/python3 scripts/wire_ready_check.py || true
/opt/homebrew/bin/python3 scripts/wire_test.py; echo wire_test_exit=$?
/opt/homebrew/bin/python3 scripts/wire_publish_handoff.py

# 6) Drain ALL pending missions (consult, proposals, wire-go, recover, etc.)
/opt/homebrew/bin/python3 scripts/claude_code_claim_executor.py drain

# 7) Push everything to GitHub
MAC_SYNC_PUSH=1 /opt/homebrew/bin/python3 scripts/mac_sync.py --push
```

### Must produce on GitHub after push

| Artifact | Meaning |
|----------|---------|
| `data/unified_status.txt` | Fresh timestamp (not `02:03`) |
| `data/brain_remote_endpoint.json` | Tailscale hostname for brain |
| `data/cursor_missions/artifacts/WIRE_STATUS.json` | Wire report |
| `data/cursor_missions/artifacts/wire_test_latest.json` | `"pass": true` |
| `data/cursor_missions/artifacts/mac_environment_latest.txt` | Mac user + daemons |
| `data/cursor_missions/artifacts/consult_mirror_proposals_latest.txt` | DeepSeek consult |
| `data/cursor_missions/artifacts/proposals_agent_demo_latest.txt` | Proposals harvest |
| `data/cursor_missions/done/*.json` | Missions moved to done |

### Verify before you stop

```bash
curl -sf http://127.0.0.1:4140/health | head -c 200
source ~/.abraham_env 2>/dev/null; HOST=$(python3 -c "import json;print(json.load(open('data/brain_remote_endpoint.json'))['host'])")
curl -sf -H "Authorization: Bearer $BRAIN_API_TOKEN" "http://${HOST}:4140/health" | head -c 200
git status && git log -1 --oneline
```

### Write cloud handoff file

Create/update **`data/cursor_missions/artifacts/CLOUD_HANDOFF_LATEST.json`**:

```json
{
  "wired_at": "<ISO UTC>",
  "mac_user": "<whoami>",
  "hostname": "<hostname>",
  "tailscale_host": "<from brain_remote_endpoint.json>",
  "brain_local": "http://127.0.0.1:4140",
  "brain_tailnet": "http://<host>:4140",
  "wire_test_pass": true,
  "queue_idle": true,
  "github_pushed": true,
  "note_for_cloud_agent": "Mac hands wired. Read this file + unified_status.txt. Cloud still joins tailnet separately for live brain calls; mission bus via GitHub is primary."
}
```

Commit **only** non-secret artifacts if needed, then:

```bash
MAC_SYNC_PUSH=1 /opt/homebrew/bin/python3 scripts/mac_sync.py --push
```

### Report to Mohamed (short)

- Brain local: OK/FAIL
- Tailscale wire: OK/FAIL + hostname
- wire_test pass: yes/no
- Queue drained: yes/no
- GitHub pushed: yes/no
- Blockers if any

**You are the hands. Cloud is the planner. GitHub + Tailscale are the nerves.**

---

## End of paste
