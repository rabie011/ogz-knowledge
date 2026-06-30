#!/usr/bin/env bash
# OGZ live mirror — one tmux window, four panes. Mohamed runs: ./scripts/ogz-mirror.sh
set -euo pipefail
ROOT="$HOME/Desktop/ogz-knowledge"
SESSION="OGZ Mirror"
LOG_ORCHESTRA="$HOME/logs/orchestra_shift.log"
cd "$ROOT"
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux required: brew install tmux" >&2
  exit 1
fi
if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
fi
LATEST_LOG="$(ls -t data/cursor_missions/done/*.log 2>/dev/null | head -1 || echo /dev/null)"
tmux new-session -d -s "$SESSION" -n mirror \
  "echo '=== PENDING ===' && tail -F data/cursor_missions/pending/ 2>/dev/null || tail -f /dev/null"
tmux split-window -h -t "$SESSION" \
  "echo '=== LATEST DONE LOG ===' && tail -F \"$LATEST_LOG\" 2>/dev/null || tail -f /dev/null"
tmux split-window -v -t "$SESSION" \
  "echo '=== ORCHESTRA ===' && tail -F \"$LOG_ORCHESTRA\" 2>/dev/null || tail -f /dev/null"
tmux split-window -v -t "$SESSION" \
  "echo '=== LIVE_STATUS ===' && watch -n 10 cat data/cursor_missions/LIVE_STATUS.md"
tmux select-layout -t "$SESSION" tiled
tmux set-option -t "$SESSION" pane-border-status top
tmux select-pane -t "$SESSION" -T pending
tmux select-pane -t "$SESSION".1 -T done-log
tmux select-pane -t "$SESSION".2 -T orchestra
tmux select-pane -t "$SESSION".3 -T status
echo "Mirror session ready. Attaching..."
tmux attach -t "$SESSION"
