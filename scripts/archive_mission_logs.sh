#!/usr/bin/env bash
# Archive mission logs older than 24h so ogz-mirror tail stays fast.
set -euo pipefail
ROOT="$HOME/Desktop/ogz-knowledge"
ARCHIVE="$ROOT/data/cursor_missions/archive/logs"
mkdir -p "$ARCHIVE"
find "$ROOT/data/cursor_missions/done" -maxdepth 1 -name '*.log' -mtime +1 -print -exec mv {} "$ARCHIVE"/ \;
echo "archived logs to $ARCHIVE"
