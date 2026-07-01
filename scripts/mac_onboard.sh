#!/usr/bin/env bash
# One-shot Mac Mini setup for mobile-first control (Mode A).
# Run ON THE MAC: cd ~/Desktop/ogz-knowledge && ./scripts/mac_onboard.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
LA="$HOME/Library/LaunchAgents"
DEPLOY="$ROOT/deploy/launchagents"
LOGS="$HOME/logs"
BRANCH="${OGZ_GIT_BRANCH:-main}"
# shellcheck source=lib/mac_git_reconcile.sh
source "$ROOT/scripts/lib/mac_git_reconcile.sh"
# shellcheck source=lib/mac_launchctl.sh
source "$ROOT/scripts/lib/mac_launchctl.sh"

echo "== OGZ Mac onboard (mobile control bridge) =="
echo "ROOT=$ROOT"

mkdir -p "$LOGS" "$LA"

# 1) Dev environment
chmod +x "$ROOT/scripts/setup_dev_env.sh" "$ROOT/scripts/mac_sync.py" "$ROOT/scripts/mac_ensure_control.sh"
"$ROOT/scripts/setup_dev_env.sh"

# 2) Git reconcile (cloud agent may have pushed missions)
cd "$ROOT"
mac_git_reconcile "$BRANCH" || echo "WARN: git reconcile failed — continue anyway"

# 3) Park noisy daemons (Mode A)
echo ""
echo "== Park noisy daemons =="
for label in com.ogz.consult-shift com.ogz.memory-keeper com.ogz.orchestra; do
  mac_launchctl_disable "$label"
  echo "  parked: $label"
done

# 4) Keep brain alive
echo ""
echo "== Load brain-api =="
mac_launchctl_enable com.ogz.brain-api "$DEPLOY/com.ogz.brain-api.plist"
sleep 2
curl -sf http://127.0.0.1:4140/health && echo "  brain: OK" || echo "  brain: starting (check logs)"

# 5) Mac sync — pushes status to GitHub for phone
echo ""
echo "== Install mac-sync (every 5 min) =="
mac_launchctl_enable com.ogz.mac-sync "$DEPLOY/com.ogz.mac-sync.plist"
echo "  mac-sync: loaded"

# 6) Executor — drains shell missions from cloud queue (optional but recommended)
echo ""
echo "== Install executor (shell missions) =="
mac_launchctl_enable com.ogz.executor "$DEPLOY/com.ogz.executor.plist"
if mac_launchctl_loaded com.ogz.executor; then
  echo "  executor: loaded"
else
  echo "  executor: WARN — not visible in launchctl print; check ~/logs/"
fi

# 7) First status push
echo ""
echo "== First status push to GitHub =="
export MAC_SYNC_PUSH=1
"$PY" "$ROOT/scripts/mac_sync.py" --push || {
  echo ""
  echo "NOTE: git push failed — configure credentials, then run:"
  echo "  MAC_SYNC_PUSH=1 python3 scripts/mac_sync.py --push"
}

echo ""
echo "== Done =="
echo "Phone: ask 'status' in Cursor"
echo "Mac debug: http://localhost:4141 (optional)"
echo "Docs: docs/MOBILE_CONTROL.md"
