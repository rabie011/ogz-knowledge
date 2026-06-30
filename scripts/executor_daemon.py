#!/usr/bin/env python3
"""Background mission executor — no iTerm. Drains pending/ via claim_executor drain."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/opt/homebrew/bin/python3"
CLAIM = ROOT / "scripts/claude_code_claim_executor.py"
PENDING = ROOT / "data/cursor_missions/pending"
POLL_SEC = 15

sys.path.insert(0, str(ROOT / "scripts"))
from live_feed import emit  # noqa: E402


def _pending_count() -> int:
    return len(list(PENDING.glob("*.json")))


def main() -> int:
    emit("executor", "startup", "Executor daemon started — shell missions in background (not Claude Code)")
    while True:
        try:
            if _pending_count():
                emit("executor", "queue", f"Draining {_pending_count()} mission(s) in background")
                subprocess.run([PYTHON, str(CLAIM), "drain"], cwd=str(ROOT), check=False)
        except Exception as exc:
            emit("executor", "error", f"Executor daemon error: {exc}", level="error")
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    raise SystemExit(main())
