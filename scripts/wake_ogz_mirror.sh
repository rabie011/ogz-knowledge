#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/Desktop/ogz-knowledge"
MIRROR="$ROOT/scripts/ogz-mirror.sh"
if [[ ! -x "$MIRROR" ]]; then
  echo "missing $MIRROR" >&2
  exit 1
fi
if [[ -d /Applications/iTerm.app ]]; then
  osascript <<APPLESCRIPT
 tell application "iTerm"
  activate
  create window with default profile
  tell current session of current window
   set name to "OGZ Mirror"
   write text "cd '$ROOT' && '$MIRROR'"
  end tell
 end tell
APPLESCRIPT
else
  osascript <<APPLESCRIPT
 tell application "Terminal"
  activate
  do script "cd '$ROOT' && '$MIRROR'"
 end tell
APPLESCRIPT
fi
echo "woke OGZ Mirror"
