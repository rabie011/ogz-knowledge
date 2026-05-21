#!/bin/bash
# drive_sync.sh — sync ogz-knowledge to Google Drive
DRIVE_TARGET="/Users/abarihm/Library/CloudStorage/GoogleDrive-rabie@ogzstudios.com/My Drive/ogz-knowledge"
LOG="$HOME/Desktop/ogz-knowledge/logs/drive_sync.log"
mkdir -p "$(dirname "$LOG")"
echo "[$(date '+%Y-%m-%dT%H:%M:%S')] Starting sync..." >> "$LOG"
rsync -av --delete \
  --exclude=".git" \
  --exclude="*.pyc" \
  --exclude="__pycache__" \
  ~/Desktop/ogz-knowledge/ "$DRIVE_TARGET/" >> "$LOG" 2>&1
STATUS=$?
if [ $STATUS -eq 0 ]; then
  echo "[$(date '+%Y-%m-%dT%H:%M:%S')] Sync complete ✓" >> "$LOG"
else
  echo "[$(date '+%Y-%m-%dT%H:%M:%S')] Sync FAILED (exit $STATUS) — retrying once..." >> "$LOG"
  rsync -av --delete --exclude=".git" ~/Desktop/ogz-knowledge/ "$DRIVE_TARGET/" >> "$LOG" 2>&1
  echo "[$(date '+%Y-%m-%dT%H:%M:%S')] Retry done (exit $?)" >> "$LOG"
fi
