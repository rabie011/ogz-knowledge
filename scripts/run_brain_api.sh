#!/bin/bash
# Always-on brain_api (:4140) — LaunchAgent entry. Owns the port.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/ogz_env.sh
source "$ROOT/scripts/ogz_env.sh"

export BRAIN_API_PORT="${BRAIN_API_PORT:-4140}"

# LaunchAgent owns :4140 — clear stale listeners before bind.
if lsof -ti ":${BRAIN_API_PORT}" >/dev/null 2>&1; then
  lsof -ti ":${BRAIN_API_PORT}" | xargs kill 2>/dev/null || true
  sleep 1
fi

exec /opt/homebrew/bin/python3 "$ROOT/scripts/brain_api.py"
