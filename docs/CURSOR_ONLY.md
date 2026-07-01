# Cursor only — your permanent control surface

**Locked:** You talk only in **Cursor** (phone or Mac). Nothing else is required for commands.

Updated: 2026-07-01

---

## The rule

| You use | For |
|---------|-----|
| **Cursor chat** | status · go · stop · plan · queue · approve |
| **Portal** | Taste pairs only |
| **:4141** | Mac debug (optional, not commands) |

Telegram, iTerm, and ad-hoc scripts are **not** your command layer.

---

## How it stays on forever (Mode A)

Three LaunchAgents on the Mac Mini — survive reboot if once onboarded:

| Daemon | Job |
|--------|-----|
| `com.ogz.brain-api` | Brain `:4140` always-on |
| `com.ogz.mac-sync` | Every 5 min: refresh status → push GitHub |
| `com.ogz.executor` | Drain shell missions from `data/cursor_missions/pending/` |

Cloud agent (this chat) **never** SSHs to the Mac. The loop is:

```
You → Cursor → GitHub (repo + missions) → Mac daemons → GitHub (status) → Cursor
```

---

## One-time Mac install (already done if mobile status works)

```bash
cd ~/Desktop/ogz-knowledge
./scripts/mac_onboard.sh
```

## If something breaks after reboot

```bash
cd ~/Desktop/ogz-knowledge
git fetch origin main && git rebase origin/main
./scripts/mac_ensure_control.sh
```

That re-bootstraps the three daemons and pushes status.

---

## What you say (same on phone and Mac)

| Say | Result |
|-----|--------|
| **status** | Live truth from **`data/ogz_live.txt`** on GitHub |
| **go …** / **queue …** | Mission dropped; Mac executor runs it |
| **stop** / **لخ** | `touch data/cursor_missions/.paused` |
| **render go** | FAL spend (your gate) |
| **wire** | Production (your gate) |

---

## What only the Mac does (invisible to you)

- `launchctl`, brain API, render, keys in `~/.abraham_env`
- Pull repo, run missions, push status

You never need to open Terminal for normal work.

---

## Pause everything (vacation / quiet)

```bash
touch ~/Desktop/ogz-knowledge/data/cursor_missions/.paused
```

Remove `.paused` when you want the executor to pick up missions again.

---

See also: [MOBILE_CONTROL.md](MOBILE_CONTROL.md) · [DAEMON_PARK.md](DAEMON_PARK.md) · [AGENTS.md](../AGENTS.md)
