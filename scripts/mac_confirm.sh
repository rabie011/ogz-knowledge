#!/usr/bin/env bash
# Post-onboard confirm + git fix for mobile status bridge.
# Run ON THE MAC (one command, no copy-paste traps):
#   cd ~/Desktop/ogz-knowledge && ./scripts/mac_confirm.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
BRANCH="${OGZ_GIT_BRANCH:-main}"
# shellcheck source=lib/mac_git_reconcile.sh
source "$ROOT/scripts/lib/mac_git_reconcile.sh"

cd "$ROOT"
chmod +x "$ROOT/scripts/mac_sync.py" "$ROOT/scripts/mac_confirm.sh" 2>/dev/null || true

echo "== OGZ Mac confirm =="
echo "ROOT=$ROOT"
echo "BRANCH=$BRANCH"
echo ""

status_paths=(
  data/unified_status.txt
  data/unified_status.json
  data/mac_status
  data/cursor_missions/artifacts/validate_stack.json
)
stashed=0
if ! git diff --quiet -- "${status_paths[@]}" 2>/dev/null || \
   ! git diff --cached --quiet -- "${status_paths[@]}" 2>/dev/null; then
  echo "== Stash local status files =="
  git stash push -m "mac-status-$(date +%Y%m%d%H%M)" -- "${status_paths[@]}" || true
  stashed=1
fi

echo ""
echo "== Git: fetch + rebase (no bare git pull) =="
if ! mac_git_reconcile "$BRANCH"; then
  echo "WARN: git reconcile failed — resolve conflicts, then re-run this script"
fi

if [[ "$stashed" -eq 1 ]]; then
  git stash pop || echo "WARN: stash pop had conflicts — resolve manually if needed"
fi

echo ""
echo "== Clear stale mission executor lock =="
LOCK="$ROOT/data/cursor_missions/.executor_live.lock"
RUNNING="$ROOT/data/cursor_missions/running"
# shellcheck source=lib/mac_launchctl.sh
source "$ROOT/scripts/lib/mac_launchctl.sh"

if [[ -f "$LOCK" ]]; then
  if ! mac_launchctl_loaded com.ogz.executor; then
    echo "  removing stale lock (executor not running)"
    rm -f "$LOCK"
    for f in "$RUNNING"/*.json; do
      [[ -f "$f" ]] || continue
      echo "  moving stale running mission back to pending: $(basename "$f")"
      mv "$f" "$ROOT/data/cursor_missions/pending/"
    done
  else
    echo "  executor running — leaving lock in place"
  fi
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
