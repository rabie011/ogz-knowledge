#!/usr/bin/env bash
# Wake a VISIBLE Claude Code session — Mohamed watches live.
set -euo pipefail

ROOT="$HOME/Desktop/ogz-knowledge"
CLAUDE="$HOME/.local/bin/claude"
LOCK="$ROOT/data/cursor_missions/.executor_live.lock"
WAKE_FLAG="$ROOT/data/cursor_missions/.wake_claude"
PROMPT_FILE="$ROOT/data/cursor_missions/.wake_prompt.txt"
INNER="$ROOT/scripts/wake_claude_code_live_inner.sh"

if [[ ! -x "$CLAUDE" ]]; then
  echo "claude not found at $CLAUDE" >&2
  exit 1
fi

if [[ -f "$LOCK" ]]; then
  pid=$(/opt/homebrew/bin/python3 -c "import json; print(json.load(open('$LOCK')).get('pid',0))" 2>/dev/null || echo 0)
  if [[ "$pid" != "0" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "executor already live pid=$pid"
    exit 0
  fi
fi

cat > "$PROMPT_FILE" <<'EOF'
You are the OGZ SOLE EXECUTOR. Mohamed is watching this session LIVE.
Read data/cursor_missions/CLAUDE_CODE_STANDING.md and follow it exactly.
Run: /opt/homebrew/bin/python3 scripts/claude_code_claim_executor.py claim
Then run-next in a loop until no pending missions, then release.
Work only in ~/Desktop/ogz-knowledge. Use /opt/homebrew/bin/python3 for all python.
EOF

chmod +x "$INNER"
rm -f "$WAKE_FLAG"

if [[ -d "/Applications/iTerm.app" ]]; then
  osascript <<APPLESCRIPT
tell application "iTerm"
  activate
  create window with default profile
  tell current session of current window
    write text "$INNER"
  end tell
end tell
APPLESCRIPT
else
  osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "$INNER"
end tell
APPLESCRIPT
fi

echo "woke claude code live session: OGZ Executor"
