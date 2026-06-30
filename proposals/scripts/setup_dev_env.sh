#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3}"
VENV="${ROOT}/.venv"

"$PY" -c "import sys; assert sys.version_info >= (3, 11)"

[[ -d "$VENV" ]] || "$PY" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -U pip wheel
pip install -r "$ROOT/requirements.txt"
echo "ogz-proposals venv ready: source $VENV/bin/activate"
