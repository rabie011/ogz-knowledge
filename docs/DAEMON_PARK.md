# Daemon park / unpark

Organization phase: minimal always-on. Reversible — nothing deleted.

## Repo edits vs run on Mac

| Who | Can do |
|-----|--------|
| **Cursor cloud agent** | Edit docs/scripts in repo; write these commands for Mohamed |
| **Mac Mini (you or local agent)** | `launchctl load/unload`, keep `brain_api` alive |

Cloud agents **cannot** park LaunchAgents on your Mac. After repo changes, run the blocks below **on the Mac**.

---

## Keep running (RUN ON MAC)

```bash
launchctl load ~/Library/LaunchAgents/com.ogz.brain-api.plist
```

Verify:

```bash
curl -sf http://127.0.0.1:4140/health && echo "brain OK"
```

## Parked (unload) — RUN ON MAC

These overlap Cursor control or add noise without Claude Code:

```bash
for label in com.ogz.consult-shift com.ogz.memory-keeper com.ogz.orchestra; do
  launchctl unload ~/Library/LaunchAgents/${label}.plist 2>/dev/null || true
done
```

Optional — park shell executor if you only work on-demand from Cursor without **go** waves:

```bash
launchctl unload ~/Library/LaunchAgents/com.ogz.executor.plist 2>/dev/null || true
```

Optional — park Telegram DeepSeek side chat:

```bash
launchctl unload ~/Library/LaunchAgents/com.ogz.ds-telegram.plist 2>/dev/null || true
```

## Unpark (Mode B — later, one at a time) — RUN ON MAC

```bash
cp ~/Desktop/ogz-knowledge/deploy/launchagents/com.ogz.consult-shift.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ogz.consult-shift.plist
```

## Pause auto-queuing without unloading

```bash
touch ~/Desktop/ogz-knowledge/data/cursor_missions/.paused
```

Remove to resume:

```bash
rm ~/Desktop/ogz-knowledge/data/cursor_missions/.paused
```

Say **stop** or **لخ** in Cursor — same effect.

## Verify (RUN ON MAC)

```bash
launchctl list | grep ogz
python3 ~/Desktop/ogz-knowledge/scripts/validate_stack.py
python3 ~/Desktop/ogz-knowledge/scripts/unified_status.py --plain
```

Parked daemons (`consult-shift`, `orchestra`, `memory-keeper`) showing unloaded is **expected** in Mode A.
