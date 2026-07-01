# Mac organize — after mobile bridge is live

**When:** Mode A wired (brain + mac-sync + executor on `main`).  
**Who runs this:** Claude Code on the Mac Mini — cloud agents queue only.

---

## Goals

1. Clean git tree (no unstaged fight with mac-sync)
2. Park extra daemons not in Mode A
3. Recover disk / logs
4. Prep proposals split (`~/Desktop/ogz-proposals`)

---

## Safe to do now

### A. Git hygiene

```bash
cd ~/Desktop/ogz-knowledge
git checkout main
git fetch origin main
./scripts/mac_confirm.sh
git stash list    # drop runtime-only stash: git stash drop stash@{N}
```

### B. Park non-Mode-A daemons (optional quieter Mac)

```bash
DOMAIN="gui/$(id -u)"
for label in com.ogz.live-feed com.ogz.live-feed-digest com.ogz.portal; do
  launchctl bootout "$DOMAIN" ~/Library/LaunchAgents/${label}.plist 2>/dev/null || \
    launchctl unload ~/Library/LaunchAgents/${label}.plist 2>/dev/null || true
done
```

Keep: brain-api, mac-sync, executor.

### C. Logs (review before delete)

```bash
du -sh ~/logs/* 2>/dev/null | sort -hr | head -20
# Truncate only if huge: : > ~/logs/noisy.log
```

### D. Proposals prep (next track)

```bash
cp -R ~/Desktop/ogz-knowledge/proposals ~/Desktop/ogz-proposals
# Copy useful bits from ~/agents when ready — see proposals/README.md
```

### E. Archive old code home (after proposals copy verified)

```bash
mv ~/agents ~/agents_ARCHIVE_$(date +%Y%m%d)
```

Do **not** delete until `ogz-proposals` has router + proposal_agent.

---

## Do NOT

- `render go`, `wire`, taste pairs, client send
- `./scripts/ogz_live.sh` (re-installs noisy 24/7 stack)
- Unpark consult-shift / orchestra until Mode B

---

## Verify

```bash
python3 scripts/unified_status.py --plain
launchctl list | grep com.ogz
git status -sb
```

Phone: ask **status** in Cursor — should still show BRAIN healthy + fresh MAC SYNC.
