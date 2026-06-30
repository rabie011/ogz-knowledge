#!/usr/bin/env python3
"""Build machine-readable onboarding brief for Cursor mission control."""
from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/done/cursor-onboarding-brief.json"


def sh(cmd: str) -> dict:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45)
        return {"exit": r.returncode, "out": (r.stdout or r.stderr)[:4000]}
    except Exception as e:
        return {"error": str(e)}


def main() -> int:
    brief: dict = {
        "id": "cursor-onboarding-brief",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": "claude-code",
        "repo": str(ROOT),
    }

    cursor = Path.home() / "claude_operator_state/CURSOR.md"
    if cursor.exists():
        text = cursor.read_text(encoding="utf-8")
        brief["recovery_point_head"] = text[:3000]
        brief["recovery_point_tail"] = text[-2000:] if len(text) > 2000 else None

    brief["git"] = sh(f"cd {ROOT} && git log -15 --oneline")
    brief["git_branch"] = sh(f"cd {ROOT} && git branch --show-current")
    brief["git_status"] = sh(f"cd {ROOT} && git status -sb")

    for port, name in [(4140, "brain_api"), (4199, "portal"), (4100, "intelligence_api"), (4111, "humain")]:
        brief[f"port_{port}_{name}"] = sh(f"lsof -i :{port} 2>/dev/null | head -3")

    token = sh("grep '^BRAIN_API_TOKEN=' ~/.abraham_env 2>/dev/null | cut -d= -f1")
    brief["brain_token_set"] = token.get("exit") == 0
    brief["health"] = sh(
        'curl -s -H "Authorization: Bearer $(grep ^BRAIN_API_TOKEN= ~/.abraham_env 2>/dev/null | cut -d= -f2)" '
        "http://127.0.0.1:4140/health 2>/dev/null || echo unreachable"
    )

    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        keys = {
            ln.split("=")[0]
            for ln in env_path.read_text().splitlines()
            if "=" in ln and not ln.strip().startswith("#")
        }
        brief["abraham_env_keys"] = sorted(keys)
    else:
        brief["abraham_env_keys"] = []

    clients_dir = ROOT / "clients"
    brief["client_handles"] = (
        sorted(p.name for p in clients_dir.iterdir() if p.is_dir()) if clients_dir.exists() else []
    )

    la = Path.home() / "Library/LaunchAgents"
    brief["launchagents"] = sorted(
        [p.name for p in la.glob("com.ogz.*")] + [p.name for p in la.glob("com.abraham.*")]
    )

    for name in ["ogz-platform", "ogz-website", "agents", "war-room"]:
        for base in [Path.home(), Path.home() / "Desktop", Path.home() / "Projects"]:
            p = base / name
            if p.exists():
                brief[f"repo_{name}"] = {
                    "path": str(p),
                    "git": sh(f"cd {p} && git log -5 --oneline 2>/dev/null"),
                }
                break

    bl_path = ROOT / "data/backlog.json"
    if bl_path.exists():
        bl = json.loads(bl_path.read_text(encoding="utf-8"))
        steps = bl.get("steps", bl) if isinstance(bl, dict) else bl
        if isinstance(steps, list):
            brief["backlog_status"] = dict(Counter(s.get("status", "?") for s in steps))
            brief["backlog_todo"] = [
                {"id": s.get("id"), "what": s.get("what"), "who": s.get("who")}
                for s in steps
                if s.get("status") == "todo"
            ][:40]
            brief["backlog_mohamed_must"] = [
                {"id": s.get("id"), "what": s.get("what")}
                for s in steps
                if s.get("who") == "mohamed_must" and s.get("status") not in ("done", "skipped")
            ]

    cm = ROOT / "data/cursor_missions"
    for sub in ["pending", "running", "done", "failed"]:
        d = cm / sub
        brief[f"missions_{sub}"] = (
            sorted(f.name for f in d.iterdir() if f.suffix == ".json") if d.exists() else []
        )

    # Key docs one-liners
    for doc in [
        "docs/REALITY.md",
        "docs/CONNECT_THE_BRAIN.md",
        "docs/DEV_PLATFORM_INTEGRATION.md",
        "docs/HOW_IT_WORKS.md",
        "HANDOVER.md",
        "BACKLOG.md",
    ]:
        p = ROOT / doc
        if p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()[:8]
            brief.setdefault("doc_heads", {})[doc] = lines

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
