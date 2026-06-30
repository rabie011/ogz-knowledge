#!/usr/bin/env python3
"""Single source of truth — JSON + plain English for Cursor mobile."""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data/unified_status.json"
OUT_PLAIN = ROOT / "data/unified_status.txt"
MISSIONS = ROOT / "data/cursor_missions"
PYTHON = "/opt/homebrew/bin/python3"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _brain() -> dict:
    token = ""
    env = Path.home() / ".abraham_env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
                break
    req = urllib.request.Request(
        "http://127.0.0.1:4140/health",
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return {"ok": True, "body": json.loads(r.read().decode())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _executor_live() -> bool:
    lock = MISSIONS / ".executor_live.lock"
    if not lock.exists():
        return False
    try:
        pid = int(json.loads(lock.read_text()).get("pid", 0))
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _paused() -> bool:
    return (MISSIONS / ".paused").exists()


def _waiting_on_mohamed() -> list[str]:
    waiting: list[str] = []
    im_here = ROOT / "data/im_here.md"
    if im_here.exists() and "BLOCKED" in im_here.read_text(encoding="utf-8", errors="replace"):
        waiting.append("im_here decision needed")
    if _paused():
        waiting.append("system paused (you said stop)")
    return waiting


def _pilot_lines() -> list[str]:
    lines: list[str] = []
    handoff = ROOT / "data/cursor_missions/artifacts/handoff/README.json"
    exports: list[dict] = []
    if handoff.exists():
        try:
            doc = json.loads(handoff.read_text(encoding="utf-8"))
            exports = doc.get("exports") or []
            pilots = doc.get("pilots") or {}
            for handle in ("albaik", "eatjurisha", "myfitness.sa"):
                exp = next((e for e in exports if e.get("handle") == handle), None)
                if exp:
                    ready = "ready" if exp.get("ready") else "not ready"
                    cov = exp.get("coverage_pct", "?")
                    lines.append(f"  · {handle}: {ready}, {cov}% coverage")
                elif handle in pilots:
                    lines.append(f"  · {handle}: {pilots[handle]}")
        except Exception:
            pass
    if not lines:
        lines.append("  · (handoff bundle not refreshed — run refresh_handoff_bundle.py)")
    return lines


def build() -> dict:
    pending = sorted(p.name for p in (MISSIONS / "pending").glob("*.json"))
    running = sorted(p.name for p in (MISSIONS / "running").glob("*.json"))
    knowledge_raw = len(list((ROOT / "data/knowledge/raw").glob("**/*.json")))
    knowledge_indexed = len(list((ROOT / "data/knowledge/indexed").glob("**/*.json")))
    mistakes = 0
    reg = ROOT / "data/mistake_registry.jsonl"
    if reg.exists():
        mistakes = sum(1 for _ in reg.open(encoding="utf-8"))
    return {
        "ts": _now(),
        "paused": _paused(),
        "waiting_on_mohamed": _waiting_on_mohamed(),
        "brain": _brain(),
        "executor_live": _executor_live(),
        "queue": {"pending": len(pending), "running": len(running), "pending_files": pending},
        "pilots_summary": _pilot_lines(),
        "knowledge": {"raw_docs": knowledge_raw, "indexed_docs": knowledge_indexed},
        "mistake_count": mistakes,
        "control_surface": "Cursor (mobile + Mac)",
        "live_feed_mac_debug": "http://localhost:4141",
        "brain_api": "http://localhost:4140",
    }


def to_plain(st: dict) -> str:
    brain_ok = st.get("brain", {}).get("ok")
    q = st.get("queue", {})
    pending_n = q.get("pending", 0)
    running_n = q.get("running", 0)
    lines = [
        f"OGZ Status · {st.get('ts', '')}",
        "",
        "CONTROL: Cursor (this chat) — mobile and Mac",
        "",
        f"BRAIN: {'healthy :4140' if brain_ok else 'DOWN — check com.ogz.brain-api'}",
        f"QUEUE: {pending_n} pending, {running_n} running"
        + (f" ({', '.join(q.get('pending_files', [])[:3])})" if pending_n else " — idle"),
        f"EXECUTOR: {'running a mission' if st.get('executor_live') else 'idle (shell only — not Claude Code)'}",
        "",
        "PILOTS:",
        *st.get("pilots_summary", []),
        "",
        f"KNOWLEDGE: {st.get('knowledge', {}).get('indexed_docs', 0)} docs indexed",
        f"MISTAKES LOGGED: {st.get('mistake_count', 0)}",
        "",
    ]
    waiting = st.get("waiting_on_mohamed") or []
    if waiting:
        lines.append("WAITING ON YOU:")
        for w in waiting:
            lines.append(f"  · {w}")
        lines.append("")
    if st.get("paused"):
        lines.append("System paused — say go to resume auto-queuing.")
        lines.append("")
    lines.extend([
        "YOUR GATES: render go · wire to prod · taste pairs · stop/لخ",
        "",
        "Mac debug feed (not mobile): http://localhost:4141",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", action="store_true", help="Print and save plain English summary")
    args = ap.parse_args()

    st = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")

    plain = to_plain(st)
    OUT_PLAIN.write_text(plain, encoding="utf-8")

    if args.plain:
        print(plain)
    else:
        print(json.dumps(st, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
