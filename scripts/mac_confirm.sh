#!/usr/bin/env bash
# Post-onboard confirm + git fix for mobile status bridge.
# Run ON THE MAC (one command, no copy-paste traps):
#   cd ~/Desktop/ogz-knowledge && ./scripts/mac_confirm.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
BRANCH="${OGZ_GIT_BRANCH:-cursor/cloud-agent-1782842649010-84hv4}"

cd "$ROOT"
chmod +x "$ROOT/scripts/mac_sync.py" "$ROOT/scripts/mac_confirm.sh" 2>/dev/null || true

echo "== OGZ Mac confirm =="
echo "ROOT=$ROOT"
echo "BRANCH=$BRANCH"
echo ""

echo "== Git: fetch + checkout feature branch =="
git fetch origin
current="$(git branch --show-current)"
if [[ "$current" != "$BRANCH" ]]; then
  echo "  switching: $current -> $BRANCH"
  git checkout "$BRANCH"
fi

status_paths=(
  data/unified_status.txt
  data/unified_status.json
  data/mac_status
  data/cursor_missions/artifacts/validate_stack.json
)
if ! git diff --quiet -- "${status_paths[@]}" 2>/dev/null || \
   ! git diff --cached --quiet -- "${status_paths[@]}" 2>/dev/null; then
  echo "  stashing local status files..."
  git stash push -m "mac-status-$(date +%Y%m%d%H%M)" -- "${status_paths[@]}" || true
  stashed=1
else
  stashed=0
fi

git pull --rebase origin "$BRANCH" || {
  echo "WARN: git pull failed — fix credentials/conflicts, then re-run this script"
}

if [[ "$stashed" -eq 1 ]]; then
  git stash pop || echo "WARN: stash pop had conflicts — resolve manually if needed"
fi

echo ""
echo "== Status (before push) =="
"$PY" "$ROOT/scripts/unified_status.py" --plain || true

echo ""
echo "== Push status to GitHub =="
export MAC_SYNC_PUSH=1
"$PY" "$ROOT/scripts/mac_sync.py" --push || {
  echo "NOTE: push failed — check SSH/credentials, then:"
  echo "  MAC_SYNC_PUSH=1 python3 scripts/mac_sync.py --push"
}

echo ""
echo "== Drain pending shell missions =="
"$PY" "$ROOT/scripts/claude_code_claim_executor.py" drain || true

echo ""
echo "== Status (after) =="
"$PY" "$ROOT/scripts/unified_status.py" --plain || true

echo ""
echo "== LaunchAgents =="
launchctl list | grep com.ogz || true

echo ""
echo "Done. Phone: ask 'status' in Cursor."
