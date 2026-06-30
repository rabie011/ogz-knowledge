#!/usr/bin/env bash
# Reproducible dev environment for ogz-knowledge.
# Run ON THE MAC MINI (not from a cloud VM).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
VENV="${ROOT}/.venv"

echo "== ogz-knowledge dev setup =="
echo "ROOT=$ROOT"
echo "PY=$PY"

"$PY" -c "import sys; assert sys.version_info >= (3, 11), f'need Python 3.11+, got {sys.version}'"

if [[ ! -d "$VENV" ]]; then
  echo "Creating venv at $VENV"
  "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -U pip wheel
python -m pip install -r "$ROOT/requirements.txt"

echo ""
echo "== verify scripts =="
python "$ROOT/scripts/unified_status.py" --plain | head -20

echo ""
echo "== brain health (expects com.ogz.brain-api on Mac) =="
if curl -sf http://127.0.0.1:4140/health >/dev/null 2>&1; then
  echo "brain_api: OK :4140"
else
  echo "brain_api: not reachable — on Mac run:"
  echo "  launchctl load ~/Library/LaunchAgents/com.ogz.brain-api.plist"
  echo "  # or: python3 $ROOT/scripts/brain_api_launcher.py"
fi

echo ""
echo "== validate stack =="
python "$ROOT/scripts/validate_stack.py" || true

echo ""
echo "Setup complete. Activate with:"
echo "  source $VENV/bin/activate"
echo "Status anytime:"
echo "  python3 $ROOT/scripts/unified_status.py --plain"
