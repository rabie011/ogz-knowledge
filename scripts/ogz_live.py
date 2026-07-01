#!/usr/bin/env python3
"""Aggregate Mac sync, executor, agents → single live truth file.

Writes data/ogz_live.json + data/ogz_live.txt. Called by mac_sync every cycle,
executor on mission start/finish, and optionally log_event.py.

  python3 scripts/ogz_live.py          # refresh both files
  python3 scripts/ogz_live.py --plain  # print txt summary
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data/ogz_live.json"
OUT_TXT = ROOT / "data/ogz_live.txt"
MISSIONS = ROOT / "data/cursor_missions"
PENDING = MISSIONS / "pending"
RUNNING = MISSIONS / "running"
DONE = MISSIONS / "done"
LOCK = MISSIONS / ".executor_live.lock"
SYNC_META = ROOT / "data/mac_status/sync_meta.json"
AGENT_REGISTRY = ROOT / "data/agents/AGENT_REGISTRY.json"
KIT_REGISTRY = ROOT / "data/agent_kit/registry.json"
DEBOUNCE = ROOT / "data/.ogz_live_debounce"

STALE_SYNC_MIN = 10
STUCK_MISSION_MIN = 30
JAMMED_DRAIN_MIN = 15
RECENT_EVENTS = 15


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _minutes_ago(ts: str | None) -> float | None:
    dt = _parse_ts(ts)
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 60.0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock() -> dict[str, Any] | None:
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except Exception:
        return None


def _http_health(url: str, token: str = "") -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            body = r.read().decode()
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body[:200]}
            return {"ok": True, "body": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _brain_token() -> str:
    env = Path.home() / ".abraham_env"
    if not env.exists():
        return ""
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("BRAIN_API_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def _sync_block() -> dict[str, Any]:
    block: dict[str, Any] = {
        "last_push": None,
        "last_pull_ok": False,
        "git_sha": None,
        "hostname": None,
        "launchagents": {},
        "last_drain_at": None,
        "last_drain_ok": None,
    }
    if SYNC_META.exists():
        try:
            meta = json.loads(SYNC_META.read_text(encoding="utf-8"))
            block["last_push"] = meta.get("ts")
            pull = meta.get("pull") or {}
            block["last_pull_ok"] = bool(pull.get("ok", False))
            block["git_sha"] = meta.get("git_sha")
            block["hostname"] = meta.get("hostname")
            block["launchagents"] = meta.get("launchagents") or {}
            drain = meta.get("drain") or {}
            block["last_drain_at"] = meta.get("last_drain_at") or meta.get("ts")
            block["last_drain_ok"] = drain.get("ok") if drain else meta.get("last_drain_ok")
        except Exception:
            pass
    return block


def _ghost_running() -> list[str]:
    ghosts: list[str] = []
    for path in sorted(RUNNING.glob("*.json")):
        if (DONE / f"{path.stem}.json").exists():
            ghosts.append(path.name)
    return ghosts


def _executor_block(sync: dict[str, Any]) -> dict[str, Any]:
    lock = _read_lock()
    lock_alive = bool(lock and _pid_alive(int(lock.get("pid", 0))))
    pending = sorted(p.name for p in PENDING.glob("*.json"))
    running = sorted(p.name for p in RUNNING.glob("*.json"))
    ghosts = _ghost_running()
    paused = (MISSIONS / ".paused").exists()

    current_mission: str | None = None
    started_at: str | None = None
    if running:
        first = RUNNING / running[0]
        current_mission = first.stem
        started_at = datetime.fromtimestamp(first.stat().st_mtime, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat().replace("+00:00", "Z")

    daemon = "unknown"
    launchagents = sync.get("launchagents") or {}
    if launchagents:
        daemon = launchagents.get("com.ogz.executor", "unknown")

    state = "idle"
    if paused:
        state = "paused"
    elif ghosts:
        state = "jammed"
    elif lock_alive and running:
        mins = _minutes_ago(started_at)
        if mins is not None and mins > STUCK_MISSION_MIN:
            state = "stuck"
        else:
            state = "running"
    elif pending and not lock_alive:
        drain_mins = _minutes_ago(sync.get("last_drain_at"))
        if drain_mins is None or drain_mins > JAMMED_DRAIN_MIN:
            state = "jammed"
    elif lock_alive:
        state = "running"

    return {
        "daemon": daemon,
        "lock_alive": lock_alive,
        "state": state,
        "current_mission": current_mission,
        "started_at": started_at,
        "pending": pending,
        "running": running,
        "ghost_running": ghosts,
        "last_drain_at": sync.get("last_drain_at"),
        "last_drain_ok": sync.get("last_drain_ok"),
    }


def _agent_ids() -> list[str]:
    ids: set[str] = set()
    for path in (AGENT_REGISTRY, KIT_REGISTRY):
        if not path.exists():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            for agent in doc.get("agents", []):
                aid = agent.get("id")
                if aid:
                    ids.add(str(aid).upper())
        except Exception:
            continue
    return sorted(ids)


def _tail_agent_events(path: Path, limit: int = 1) -> dict[str, Any] | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def _resolve_agent_events_path(agent_id: str) -> Path | None:
    if not KIT_REGISTRY.exists():
        return None
    try:
        reg = json.loads(KIT_REGISTRY.read_text(encoding="utf-8"))
        for agent in reg.get("agents", []):
            if agent.get("id", "").upper() != agent_id.upper():
                continue
            home = Path(agent.get("mac_home", ".")).expanduser()
            rel = agent.get("events", "events/agent_events.jsonl")
            if rel.endswith("/") or "creative_outputs" in rel:
                return home / "data" / "agent_events.jsonl"
            return home / rel
    except Exception:
        return None
    return None


def _agents_block() -> dict[str, dict[str, Any]]:
    agents: dict[str, dict[str, Any]] = {}
    for aid in _agent_ids():
        entry: dict[str, Any] = {"last_seen": None, "state": "unknown", "summary": ""}
        events_path = _resolve_agent_events_path(aid)
        if events_path:
            last = _tail_agent_events(events_path)
            if last:
                entry["last_seen"] = last.get("timestamp")
                entry["summary"] = (last.get("summary") or last.get("event_type") or "")[:200]
                entry["state"] = "active" if _minutes_ago(entry["last_seen"]) is not None and _minutes_ago(entry["last_seen"]) < 60 else "idle"
        agents[aid] = entry
    return agents


def _recent_events() -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from live_feed import read_recent

        return read_recent(RECENT_EVENTS)
    except Exception:
        return []


def _stale_reason(executor: dict[str, Any], sync: dict[str, Any]) -> str | None:
    if executor.get("ghost_running"):
        return "ghost running missions"
    if executor.get("state") == "stuck":
        return "executor stuck on mission"
    if executor.get("state") == "jammed" and not (MISSIONS / ".paused").exists():
        return "executor jammed"
    push_age = _minutes_ago(sync.get("last_push"))
    if push_age is not None and push_age > STALE_SYNC_MIN:
        return "stale: sync dead"
    return None


def build() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from unified_status import build as unified_build

    unified = unified_build()
    sync = _sync_block()
    executor = _executor_block(sync)
    token = _brain_token()
    brain = _http_health("http://127.0.0.1:4140/health", token)
    bridge = _http_health("http://127.0.0.1:4150/health")

    updated_at = _now()
    stale_reason = _stale_reason(executor, sync)
    healthy = stale_reason is None and executor.get("state") not in ("jammed", "stuck")

    doc: dict[str, Any] = {
        "version": 1,
        "updated_at": updated_at,
        "healthy": healthy,
        "stale": stale_reason is not None,
        "stale_reason": stale_reason,
        "sync": sync,
        "executor": executor,
        "brain": {"ok": brain.get("ok", False), "port": 4140},
        "bridge": {"ok": bridge.get("ok", False), "port": 4150},
        "agents": _agents_block(),
        "recent_events": _recent_events(),
        "waiting_on_mohamed": unified.get("waiting_on_mohamed") or [],
        "pilots_summary": unified.get("pilots_summary") or [],
        "unified_status_ts": unified.get("ts"),
    }
    return doc


def to_plain(doc: dict[str, Any]) -> str:
    ex = doc.get("executor") or {}
    sync = doc.get("sync") or {}
    brain_ok = (doc.get("brain") or {}).get("ok")
    bridge_ok = (doc.get("bridge") or {}).get("ok")
    healthy = doc.get("healthy")
    state = ex.get("state", "?")
    pending_n = len(ex.get("pending") or [])
    ghosts = ex.get("ghost_running") or []
    current = ex.get("current_mission") or "—"
    host = sync.get("hostname") or "mac"
    last_push = sync.get("last_push") or "never"

    lines = [
        f"OGZ Live · {doc.get('updated_at', '')}",
        f"HEALTH: {'OK' if healthy else 'NOT OK'} — {doc.get('stale_reason') or state}",
        f"EXECUTOR: {state} · mission={current} · pending={pending_n}",
        f"GHOSTS: {', '.join(ghosts) if ghosts else 'none'}",
        f"BRAIN :4140: {'up' if brain_ok else 'down'} · BRIDGE :4150: {'up' if bridge_ok else 'down/skip'}",
        f"SYNC: {last_push} ({host}) · drain_ok={ex.get('last_drain_ok')}",
        "",
    ]
    waiting = doc.get("waiting_on_mohamed") or []
    if waiting:
        lines.append("WAITING: " + "; ".join(waiting))
    pilots = doc.get("pilots_summary") or []
    if pilots:
        lines.append("PILOTS: " + " · ".join(p.strip(" ·") for p in pilots[:2]))
    recent = doc.get("recent_events") or []
    if recent:
        last = recent[-1]
        lines.append(f"LAST EVENT: {last.get('source', '?')}: {(last.get('message') or '')[:80]}")
    lines.append("")
    lines.append("Full JSON: data/ogz_live.json")
    return "\n".join(lines[:15] if len(lines) > 15 else lines)


def write(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    doc = doc or build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_TXT.write_text(to_plain(doc), encoding="utf-8")
    return doc


def refresh_if_debounced(min_seconds: float = 30.0) -> bool:
    """Return True if refresh ran; skip if written within min_seconds."""
    now = datetime.now(timezone.utc).timestamp()
    if DEBOUNCE.exists():
        try:
            last = float(DEBOUNCE.read_text(encoding="utf-8").strip())
            if now - last < min_seconds:
                return False
        except ValueError:
            pass
    write()
    DEBOUNCE.write_text(str(now), encoding="utf-8")
    return True


def patch_agent(agent_id: str, *, summary: str = "", state: str = "active") -> bool:
    """Merge one agent heartbeat into ogz_live (debounced full rebuild)."""
    agent_id = agent_id.upper()
    now = _now()
    if OUT_JSON.exists():
        try:
            doc = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        except Exception:
            doc = build()
    else:
        doc = build()
    agents = doc.setdefault("agents", {})
    entry = agents.setdefault(agent_id, {})
    entry["last_seen"] = now
    entry["state"] = state
    if summary:
        entry["summary"] = summary[:200]
    doc["updated_at"] = now
    OUT_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_TXT.write_text(to_plain(doc), encoding="utf-8")
    DEBOUNCE.write_text(str(datetime.now(timezone.utc).timestamp()), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh OGZ live truth files")
    ap.add_argument("--plain", action="store_true", help="Print ogz_live.txt to stdout")
    args = ap.parse_args()
    try:
        doc = write()
    except Exception as e:
        print(f"ogz_live fatal: {e}", file=sys.stderr)
        return 1
    if args.plain:
        print(to_plain(doc))
    else:
        print(json.dumps({"ok": True, "path": str(OUT_JSON), "healthy": doc.get("healthy")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
