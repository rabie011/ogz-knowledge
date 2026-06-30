#!/usr/bin/env python3
"""Memory keeper — mine Claude history + scar index every 6h."""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cursor_missions/.memory_keeper_state.json"
OUT_DIR = ROOT / "data/artifacts/memory"
PYTHON = "/opt/homebrew/bin/python3"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def _scar_index() -> dict:
    reg = ROOT / "data/mistake_registry.jsonl"
    scars: dict[str, int] = {}
    if reg.exists():
        for line in reg.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                c = json.loads(line).get("scar_class", "?")
                scars[c] = scars.get(c, 0) + 1
            except Exception:
                pass
    master = ROOT / "data/cursor_missions/done/claude-code-history-master.json"
    mined = {}
    if master.exists():
        try:
            mined = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"ts": _now(), "mistake_counts": scars, "history_keys": list(mined.keys()) if mined else []}


def main() -> int:
    st = _load_state()
    now = time.time()
    if now - float(st.get("last_run", 0)) < 21600:  # 6h
        return 0

    subprocess.run([PYTHON, str(ROOT / "scripts/cursor_mine_history.py")], cwd=str(ROOT), check=False)
    subprocess.run([PYTHON, str(ROOT / "scripts/cursor_build_context.py")], cwd=str(ROOT), check=False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = _scar_index()
    (OUT_DIR / "scar_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    master = ROOT / "data/cursor_missions/done/claude-code-history-master.json"
    if master.exists():
        import shutil

        shutil.copy2(master, OUT_DIR / "claude-code-history-master.json")

    st["last_run"] = now
    st["scar_classes"] = len(index.get("mistake_counts", {}))
    _save_state(st)

    subprocess.run(
        [PYTHON, str(ROOT / "scripts/live_feed.py"), "memory", "index", f"Memory keeper ran — {index.get('mistake_counts', {})}"],
        cwd=str(ROOT),
        check=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
