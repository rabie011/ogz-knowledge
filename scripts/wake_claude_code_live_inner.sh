#!/usr/bin/env bash
# Inner launcher — called from iTerm/Terminal by wake_claude_code_live.sh
set -euo pipefail
ROOT="$HOME/Desktop/ogz-knowledge"
CLAUDE="$HOME/.local/bin/claude"
cd "$ROOT"
exec "$CLAUDE" -n "OGZ Executor" --permission-mode acceptEdits "$(cat data/cursor_missions/.wake_prompt.txt)"
