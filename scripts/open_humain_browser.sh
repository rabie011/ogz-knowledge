#!/bin/bash
# open_humain_browser.sh — open a debug-port browser the HUMAIN service attaches to via CDP.
#
# Mohamed (June 29): "humain is working on the browser, you open it in a new one and it's already opened."
# The service used to launch its OWN Chrome-for-Testing window (separate cookie jar) that timed out in 20min.
# Now it CONNECTS (chromium.connect_over_cdp :9222) to the browser THIS launcher opens. You log into
# chat.humain.ai in THIS window ONCE — it stays open, the session persists, and the service reuses it forever.
# Uses a DEDICATED profile (~/.humain_chrome_profile) so it never conflicts with your main Chrome.
#
#   bash scripts/open_humain_browser.sh      # opens the window; log into HUMAIN; leave it open
set -e
PORT="${HUMAIN_CDP_PORT:-9222}"
PROFILE="$HOME/.humain_chrome_profile"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  CHROME="$(ls "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Google\ Chrome\ for\ Testing.app/Contents/MacOS/Google\ Chrome\ for\ Testing 2>/dev/null | head -1)"
fi
if [ -z "$CHROME" ] || [ ! -x "$CHROME" ]; then
  echo "🛑 no Chrome found (looked for Google Chrome.app + Chrome for Testing). Install Chrome or set CHROME=."
  exit 1
fi
echo "🌐 opening HUMAIN browser on CDP port $PORT (profile: $PROFILE)"
echo "   → log into chat.humain.ai IN THIS WINDOW once, then leave it open. The service attaches to it."
exec "$CHROME" --remote-debugging-port="$PORT" --user-data-dir="$PROFILE" \
  --no-first-run --no-default-browser-check "https://chat.humain.ai" >/dev/null 2>&1 &
echo "   ✅ launched (pid $!). Service will connect via http://127.0.0.1:$PORT"
