#!/usr/bin/env python3
"""Full autonomous status report + optional next-wave queue hint."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/done/autonomous-status-report.json"


def sh(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, timeout=30)
    return (r.stdout or r.stderr or "").strip()[:2000]


def brain_health() -> dict:
    token = ""
    env = Path.home() / ".abraham_env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
    req = urllib.request.Request(
        "http://127.0.0.1:4140/health",
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return {"ok": True, "body": json.loads(r.read().decode())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> int:
    pending = sorted(p.name for p in (ROOT / "data/cursor_missions/pending").glob("*.json"))
    done_recent = sorted(
        (ROOT / "data/cursor_missions/done").glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:15]
    done_ids = [p.stem for p in done_recent]

    prefill = {}
    snap = ROOT / "data/cursor_missions/done/overnight-prefill-snapshot.json"
    if snap.exists():
        prefill = json.loads(snap.read_text(encoding="utf-8"))

    heartbeats = []
    hb = ROOT / "data/cursor_missions/done/24h-heartbeat.jsonl"
    if hb.exists():
        for line in hb.read_text().strip().splitlines()[-8:]:
            try:
                heartbeats.append(json.loads(line))
            except Exception:
                pass

    bl = json.loads((ROOT / "data/backlog.json").read_text(encoding="utf-8"))
    steps = bl.get("steps", bl)
    from collections import Counter
    backlog_status = dict(Counter(s.get("status") for s in steps)) if isinstance(steps, list) else {}

    studios_paths = [
        Path.home() / "o-gz-studios-web",
        Path.home() / "Projects/o-gz-studios-web",
        Path.home() / "Desktop/o-gz-studios-web",
    ]
    studios_cloned = next((str(p) for p in studios_paths if p.exists()), None)

    report = {
        "id": "autonomous-status-report",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "role": "run-until-mohamed-texts",
        "daemons": sh("launchctl list 2>/dev/null | grep -E 'com.ogz.brain-api|com.ogz.cursor-missions'"),
        "brain": brain_health(),
        "portal": sh("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4199/health 2>/dev/null || echo unreachable"),
        "humain": sh("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4111/health 2>/dev/null || echo unreachable"),
        "prefill_pilots": prefill,
        "pending_missions": pending,
        "recent_done_missions": done_ids,
        "backlog_status": backlog_status,
        "git": sh("git log -3 --oneline"),
        "git_dirty": sh("git status -sb | head -5"),
        "studios_web_local": studios_cloned,
        "heartbeats_last_8": heartbeats,
        "blockers_mohamed_must": [
            "4 killed posts — render-go required (~$0.12 fal)",
            "13 bridge taste pairs on portal",
            "reserve_taste_lane flip — only when queue ≤7 AND you approve",
        ],
        "autonomous_next": [] if pending else [
            "wave: clone o-gz-studios-web if repo URL found",
            "wave: lib/brain smoke client against :4140",
            "wave: consult DeepSeek on wire checklist",
        ],
    }

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
