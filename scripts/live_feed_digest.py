#!/usr/bin/env python3
"""Rule-based digest — turns recent feed events into one plain-English summary line."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from live_feed import emit, read_recent  # noqa: E402


def _waiting_on_mohamed() -> str | None:
    root = ROOT / "data"
    if (root / "cursor_missions/.paused").exists():
        return "⏸ متوقف — قل stop/لخ للإيقاف"
    waiting = []
    im_here = root / "im_here.md"
    if im_here.exists() and "BLOCKED" in im_here.read_text(encoding="utf-8", errors="replace"):
        waiting.append("قرار منك (im_here)")
    wire = root / "cursor_missions/artifacts/wire_complete.json"
    if not wire.exists():
        waiting.append("wire محلي فقط")
    if waiting:
        return "⏳ بانتظارك: " + " · ".join(waiting)
    return None


def build_digest(events: list[dict]) -> str:
    wait = _waiting_on_mohamed()
    if not events:
        return wait or "لا نشاط بعد — النظام يعمل 24/7 · No activity yet — system running."
    recent = events[-25:]
    missions_started = [e for e in recent if e.get("type") == "mission_start"]
    missions_done = [e for e in recent if e.get("type") == "mission_done"]
    errors = [e for e in recent if e.get("level") == "error"]
    sources = Counter(e.get("source", "?") for e in recent)

    parts: list[str] = []
    if missions_done:
        last = missions_done[-1]
        parts.append(f"Last mission: {last.get('message', 'done')}")
    elif missions_started:
        parts.append(f"In progress: {missions_started[-1].get('message', 'running')}")

    pass_n = sum(1 for e in missions_done if "pass" in e.get("message", "").lower() or e.get("status") == "pass")
    fail_n = sum(1 for e in missions_done if e.get("status") in ("fail", "partial"))
    if missions_done:
        parts.append(f"Recent missions: {len(missions_done)} finished ({pass_n} ok, {fail_n} issues)")

    brain = [e for e in recent if e.get("source") == "brain"]
    if brain:
        parts.append(brain[-1].get("message", ""))

    orch = [e for e in recent if e.get("source") == "orchestra"]
    if orch and not brain:
        parts.append(orch[-1].get("message", ""))

    if errors:
        parts.append(f"⚠ {len(errors)} error(s) — see feed")

    active = ", ".join(f"{k}({v})" for k, v in sources.most_common(4))
    if active:
        parts.append(f"Activity from: {active}")

    digest = " · ".join(p for p in parts if p)[:500]
    if wait:
        digest = f"{wait} · {digest}"
    return digest[:600]


def main() -> int:
    events = read_recent(50)
    msg = build_digest(events)
    emit("digest", "digest", msg, level="info")
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
