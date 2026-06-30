#!/usr/bin/env bash
# Start OGZ Live Feed + open one browser tab. No iTerm required.
set -euo pipefail
ROOT="$HOME/Desktop/ogz-knowledge"
PY="/opt/homebrew/bin/python3"
LA="$HOME/Library/LaunchAgents"
DEPLOY="$ROOT/deploy/launchagents"

install_agent() {
  local name="$1"
  cp "$DEPLOY/$name.plist" "$LA/"
  launchctl unload "$LA/$name.plist" 2>/dev/null || true
  launchctl load "$LA/$name.plist"
}

mkdir -p "$HOME/logs" "$ROOT/data/live_feed"

# Live feed server (:4141)
install_agent "com.ogz.live-feed"

# Background executor (replaces iTerm wake)
install_agent "com.ogz.executor"

# Digest every 60s
install_agent "com.ogz.live-feed-digest"

# Orchestra + consult + memory (24/7 brain)
install_agent "com.ogz.orchestra"
install_agent "com.ogz.consult-shift"
install_agent "com.ogz.memory-keeper"
install_agent "com.ogz.brain-api"

"$PY" "$ROOT/scripts/live_feed.py" live-feed startup "OGZ Live started — Mac debug at http://localhost:4141 (use Cursor on mobile)"

sleep 1
open "http://localhost:4141" 2>/dev/null || true

echo "OGZ Live: http://localhost:4141"
echo "Pin this tab — your single situation room."
