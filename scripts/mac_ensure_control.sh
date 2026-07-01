#!/usr/bin/env bash
# Re-ensure Mode A control daemons (brain + mac-sync + executor). Idempotent.
# Run ON THE MAC after reboot or if status goes stale:
#   cd ~/Desktop/ogz-knowledge && ./scripts/mac_ensure_control.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
LA="$HOME/Library/LaunchAgents"
DEPLOY="$ROOT/deploy/launchagents"
QUIET=0

if [[ "${1:-}" == "--quiet" ]]; then
  QUIET=1
fi

log() {
  [[ "$QUIET" -eq 1 ]] || echo "$@"
}

# shellcheck source=lib/mac_launchctl.sh
source "$ROOT/scripts/lib/mac_launchctl.sh"

mkdir -p "$HOME/logs" "$LA"

log "== OGZ ensure control (Mode A) =="

for pair in \
  "com.ogz.brain-api:$DEPLOY/com.ogz.brain-api.plist" \
  "com.ogz.mac-sync:$DEPLOY/com.ogz.mac-sync.plist" \
  "com.ogz.executor:$DEPLOY/com.ogz.executor.plist"; do
  label="${pair%%:*}"
  plist="${pair#*:}"
  if mac_launchctl_loaded "$label"; then
    log "  $label: already loaded"
  else
    log "  $label: bootstrapping..."
    mac_launchctl_enable "$label" "$plist"
  fi
done

sleep 1
if curl -sf http://127.0.0.1:4140/health >/dev/null; then
  log "  brain: OK"
else
  log "  brain: WARN — check ~/logs/brain_api.err.log"
fi

export MAC_SYNC_PUSH=1
"$PY" "$ROOT/scripts/mac_sync.py" --push --no-pull >/dev/null 2>&1 || \
  "$PY" "$ROOT/scripts/mac_sync.py" --push >/dev/null 2>&1 || true

log "== Done — ask status in Cursor =="
