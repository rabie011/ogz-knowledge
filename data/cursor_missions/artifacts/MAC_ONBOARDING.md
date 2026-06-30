# Mac onboarding — run once when you're at the machine

**Goal:** Phone Cursor can read live Mac status from GitHub.

---

## Quick start (copy-paste)

```bash
cd ~/Desktop/ogz-knowledge
git pull
chmod +x scripts/mac_onboard.sh
./scripts/mac_onboard.sh
```

Expected output: brain OK, mac-sync loaded, first git push of status.

---

## Checklist

### A. Repo + Python

- [ ] `git pull` — get cloud agent changes
- [ ] `./scripts/setup_dev_env.sh` — venv + deps
- [ ] `~/.abraham_env` exists with `BRAIN_API_TOKEN`

### B. Daemons (Mode A)

- [ ] **Keep:** `com.ogz.brain-api` (:4140)
- [ ] **Install:** `com.ogz.mac-sync` (status → GitHub every 5 min)
- [ ] **Install:** `com.ogz.executor` (run shell missions from cloud)
- [ ] **Park:** consult-shift, memory-keeper, orchestra

```bash
# Verify
launchctl list | grep com.ogz
curl -sf http://127.0.0.1:4140/health && echo brain OK
```

### C. Git push (required for phone status)

Mac must push status files. Test:

```bash
MAC_SYNC_PUSH=1 python3 scripts/mac_sync.py --push
```

If push fails → set up SSH key for GitHub on the Mac.

### D. Proposals track (next, after onboard)

- [ ] Create `~/Desktop/ogz-proposals` from `proposals/` scaffold (see `proposals/README.md`)
- [ ] Copy good parts from `~/agents` (router, proposal_agent, client knowledge)
- [ ] Google Drive service account → `~/.config/ogz/google_sa.json` (gitignored)

---

## Verify from phone

1. Wait 5 min after onboard (or run mac_sync manually)
2. In Cursor mobile ask: **status**
3. Should show `BRAIN: healthy` and recent `mac_last_sync`

---

## After onboard — confirm (one command)

Do **not** paste numbered comment lines like `# 5) Confirm` into zsh — the `)` can cause `parse error near ')'`.

Do **not** use bare `git pull` on the Mac — if branches diverged you get *Need to specify how to reconcile*. Use `mac_confirm.sh` or the bootstrap block below.

```bash
cd ~/Desktop/ogz-knowledge
chmod +x scripts/mac_confirm.sh
./scripts/mac_confirm.sh
```

### Bootstrap (stay on main — do not switch to cloud branch)

PR #1 is merged. Mac local `main` may have unpushed commits — keep them.

```bash
cd ~/Desktop/ogz-knowledge
git fetch origin main
git checkout main
git stash push -m mac-status -- data/unified_status.txt data/unified_status.json data/mac_status data/cursor_missions/artifacts/validate_stack.json data/LIVE_STATUS.md data/events.jsonl 2>/dev/null || true
git rebase origin/main
git stash pop 2>/dev/null || true
chmod +x scripts/mac_confirm.sh
./scripts/mac_confirm.sh
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `zsh: parse error near ')'` | You pasted a markdown comment/numbered step. Run `./scripts/mac_confirm.sh` instead |
| `Need to specify how to reconcile` | Do not use bare `git pull`. Use bootstrap block above or `./scripts/mac_confirm.sh` |
| git pull/push fails | Run `./scripts/mac_confirm.sh` (stashes status files, fetch + rebase) |
| BRAIN DOWN | `launchctl load ~/Library/LaunchAgents/com.ogz.brain-api.plist` |
| Status stale on phone | `MAC_SYNC_PUSH=1 python3 scripts/mac_sync.py --push` |
| Missions not running | `launchctl load ~/Library/LaunchAgents/com.ogz.executor.plist` |
| Too much auto-noise | `touch data/cursor_missions/.paused` |

---

## Do NOT run (Mode A)

- `./scripts/ogz_live.sh` — installs orchestra + consult + memory (noisy legacy)
- Unpark consult-shift until you want Mode B 24/7

See [docs/MOBILE_CONTROL.md](../../docs/MOBILE_CONTROL.md).
