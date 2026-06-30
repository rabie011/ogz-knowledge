#!/usr/bin/env python3
"""Consult shift — DeepSeek every 15 min: read state, propose missions, log consult."""
from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cursor_missions/.consult_shift_state.json"
PAUSED = ROOT / "data/cursor_missions/.paused"
PENDING = ROOT / "data/cursor_missions/pending"
CONSULT_LOG = ROOT / "data/consult_logs"
PYTHON = "/opt/homebrew/bin/python3"
FEED_PY = ROOT / "scripts/live_feed.py"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _feed(source: str, type_: str, message: str, level: str = "info") -> None:
    subprocess.run([PYTHON, str(FEED_PY), source, type_, message, level], cwd=str(ROOT), check=False)


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


def _shift_block() -> str:
    h = datetime.now().hour
    if h < 6:
        return "night"
    if h < 12:
        return "morning"
    if h < 18:
        return "afternoon"
    return "evening"


def _build_prompt(status: dict, scars: list[str]) -> str:
    return f"""OGZ 24/7 consult shift ({_shift_block()} block).

UNIFIED STATUS (facts):
{json.dumps(status, indent=2, ensure_ascii=False)[:4000]}

RECENT SCAR CLASSES: {', '.join(scars[-8:]) or 'none'}

AGENT REGISTRY: ORCHESTRA, CONSULT, EXECUTOR-SHELL, BUILDER, RABIE, SEARCH, LEARNER, MEMORY, CREATIVE.

Mohamed is AWAY. System must work autonomously on shell missions only.
NEVER: FAL spend, production wire, taste pairs.

Reply in this EXACT format:

VERDICT: (2 lines — what state we're in, biggest risk)
DO_NOT: (bullet list, max 3)
MISSIONS: (0-2 shell missions as JSON array, each with id, type, goal, fix_allowed, commands[])
  type must be "commands" or "research"
  commands must use full path /opt/homebrew/bin/python3 and ~/Desktop/ogz-knowledge only
  NO home glob, NO fix_allowed true

If queue has pending missions, MISSIONS should be [].
"""


def _parse_missions(text: str) -> list[dict]:
    m = re.search(r"MISSIONS:\s*(\[[\s\S]*?\])\s*(?:$|VERDICT|DO_NOT)", text)
    if not m:
        m = re.search(r"(\[[\s\S]*\])", text)
    if not m:
        return []
    try:
        arr = json.loads(m.group(1))
        return [x for x in arr if isinstance(x, dict) and x.get("commands")]
    except Exception:
        return []


def _recent_scars() -> list[str]:
    reg = ROOT / "data/mistake_registry.jsonl"
    if not reg.exists():
        return []
    lines = reg.read_text(encoding="utf-8").strip().splitlines()[-10:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line).get("scar_class", "?"))
        except Exception:
            pass
    return out


def main() -> int:
    if PAUSED.exists():
        _feed("consult", "paused", "Consult shift paused — Mohamed said stop")
        return 0

    st = _load_state()
    now = time.time()
    interval = 900  # 15 min
    if now - float(st.get("last_run", 0)) < interval:
        return 0

    subprocess.run([PYTHON, str(ROOT / "scripts/unified_status.py")], cwd=str(ROOT), check=False)
    status_path = ROOT / "data/unified_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}

    pending = list(PENDING.glob("*.json"))
    if len(pending) >= 3:
        st["last_run"] = now
        st["skipped"] = "queue_full"
        _save_state(st)
        return 0

    sys_path = str(ROOT / "scripts")
    import sys

    sys.path.insert(0, sys_path)
    from consult import ask_deepseek

    prompt = _build_prompt(status, _recent_scars())
    answer = ask_deepseek(prompt, max_tokens=1500, timeout=120)

    CONSULT_LOG.mkdir(parents=True, exist_ok=True)
    log_path = CONSULT_LOG / f"shift-{_now()[:19].replace(':', '')}.md"
    log_path.write_text(f"# Consult shift {_now()}\n\n## Prompt\n\n{prompt[:2000]}\n\n## DeepSeek\n\n{answer}\n", encoding="utf-8")

    verdict = ""
    for line in answer.splitlines():
        if line.startswith("VERDICT:"):
            verdict = line[8:].strip()
            break
    if not verdict:
        verdict = answer[:200].replace("\n", " ")

    _feed("deepseek", "consult", f"Shift ({_shift_block()}): {verdict[:200]}")

    missions = _parse_missions(answer)
    queued = 0
    for i, mission in enumerate(missions[:2]):
        mid = mission.get("id", f"consult-{_now()[:16].replace(':', '')}-{i}")
        mission.setdefault("from", "consult-shift")
        mission.setdefault("type", "commands")
        mission.setdefault("fix_allowed", False)
        mission.setdefault("created", _now())
        mission["id"] = mid
        path = PENDING / f"{_now()[:16].replace(':', '')}-{mid}.json"
        path.write_text(json.dumps(mission, indent=2, ensure_ascii=False), encoding="utf-8")
        queued += 1

    if queued:
        _feed("orchestra", "queue", f"DeepSeek queued {queued} mission(s) for executor")
        subprocess.run([PYTHON, str(ROOT / "scripts/cursor_emit_queue.py")], cwd=str(ROOT), check=False)

    st["last_run"] = now
    st["last_verdict"] = verdict
    st["queued"] = queued
    _save_state(st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
