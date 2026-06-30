#!/usr/bin/env python3
"""Mine Claude Code history into a master brief for Cursor."""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/done/claude-code-history-master.json"


def sh(cmd: str, cwd: Path | None = None) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or ROOT, timeout=60)
    return (r.stdout or r.stderr or "").strip()


def month_commits() -> dict[str, int]:
    log = sh("git log --format='%ad' --date=format:'%Y-%m'")
    return dict(Counter(log.splitlines()))


def scar_memories() -> list[dict]:
    mem = Path.home() / ".claude/projects/-Users-abarihm/memory"
    scars = []
    if not mem.exists():
        return scars
    for p in sorted(mem.glob("feedback_*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        title = ""
        for line in text.splitlines()[:6]:
            if line.startswith("name:"):
                title = line.split(":", 1)[1].strip()
            elif line.startswith("# "):
                title = line[2:].strip()
        scars.append({"file": p.name, "title": title or p.stem, "head": text[:400]})
    return scars


def session_summaries() -> list[dict]:
    sessions = Path.home() / "claude_operator_state/sessions"
    out = []
    if not sessions.exists():
        return out
    for day in sorted(sessions.iterdir(), reverse=True)[:14]:
        if not day.is_dir():
            continue
        brief = day / "00_SESSION_BRIEF.md"
        todo = day / "02_TODO_NEXT.md"
        entry = {"date": day.name}
        if brief.exists():
            entry["brief"] = brief.read_text(encoding="utf-8", errors="replace")[:1500]
        if todo.exists():
            entry["todo"] = todo.read_text(encoding="utf-8", errors="replace")[:800]
        out.append(entry)
    return out


def backlog_snapshot() -> dict:
    bl = json.loads((ROOT / "data/backlog.json").read_text(encoding="utf-8"))
    steps = bl.get("steps", bl)
    by_status = Counter(s.get("status") for s in steps)
    todo = [s for s in steps if s.get("status") == "todo"][:25]
    return {"by_status": dict(by_status), "todo_sample": todo}


def main() -> int:
    cursor = Path.home() / "claude_operator_state/CURSOR.md"
    latest = ""
    if cursor.exists():
        t = cursor.read_text(encoding="utf-8")
        m = re.search(r"^## [^\n]+", t, re.M)
        latest = t[:2500] if m else t[:2500]

    report = {
        "id": "claude-code-history-master",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": "claude-code",
        "purpose": "Everything Cursor needs — 6 months Claude Code on this Mac",
        "timeline": {
            "commits_by_month": month_commits(),
            "total_commits_since_dec_2025": sh("git log --oneline --since='2025-12-01' | wc -l").strip(),
        },
        "three_layers": {
            "THE_BRAIN": "ogz-knowledge — produce pipeline + 3 HTTP contracts (/extract /produce /performance)",
            "THE_BUILD_MACHINE": "RABIE(GPT) + Claude Code + DeepSeek + orchestra + make_sure",
            "THE_DEV_PLATFORM": "o-gz-studios-web (Vercel, not cloned) — external dev team",
        },
        "systems": {
            "repos_local": {
                "ogz-knowledge": str(ROOT),
                "ogz-platform": str(Path.home() / "ogz-platform"),
                "ogz-website": str(Path.home() / "ogz-website"),
                "agents": str(Path.home() / "agents"),
                "war-room": str(Path.home() / "war-room"),
                "operator_state": str(Path.home() / "claude_operator_state"),
            },
            "apis_ports": {
                "4100": "api/server.py intelligence",
                "4140": "scripts/brain_api.py dev handoff",
                "4199": "api/portal_mini.py founder portal",
                "4111": "humain_service.py Saudi pen",
            },
            "daemons": sh("launchctl list 2>/dev/null | grep -E 'ogz|abraham' | head -25"),
            "orchestra": {
                "rabie": str(Path.home() / "agents/rabie/rabie.py"),
                "orchestrator": str(Path.home() / "agents/orchestrator_daemon.py"),
                "backlog": str(ROOT / "data/backlog.json"),
                "memory": str(Path.home() / "agents/rabie/orchestra_memory.json"),
            },
            "consult_panel": "scripts/consult.py — DeepSeek default-first + GPT/Gemini/Groq",
            "cursor_file_bus": "data/cursor_missions/ + scripts/cursor_mission_consumer.py",
        },
        "pivot_june_27": "Stop scaling infra; prepare connectable brain for dev platform",
        "mission_9_posts": "Completed June 29 — 9/9 HUMAIN-taste-grade; photo-fix arc June 29-30",
        "current_work_june_30": "GATE0 product_is_real hardening; art-director wired; awaiting Mohamed go on 4 re-renders",
        "known_scars": scar_memories(),
        "recent_sessions": session_summaries(),
        "backlog": backlog_snapshot(),
        "recovery_point_excerpt": latest,
        "wiring_status": {
            "brain_to_dev_platform": "contracts built + tested; Vercel extraction broken on their side",
            "brain_to_ogz_platform": "NOT wired — separate 10-field BrandDNA",
            "portal_to_learning": "WIRED — apply_rulings every 30s",
            "deepseek_telegram": "WIRED — com.ogz.ds-telegram",
        },
        "key_mistakes_documented": [
            "Over-claiming output quality without verification (June 22)",
            "Hand-seeding scenes instead of fixing machine (Rule #12)",
            "Fail-open gates letting hallucinated products render (fixed GATE0 June 29-30)",
            "Severed wires — art-director brief not reaching fal prompt (fixed C240)",
            "HUMAIN in wrong browser window — use CDP to Mohamed's browser (C227)",
            "Orchestra session leak — claude sessions pile up, load 70+ (June 20)",
            "Claiming 5/9 approved when passed=false without HUMAIN (June 29 correction)",
            "Stale beliefs — render parked when no_fal_photos=False since June 21",
        ],
        "how_cursor_should_work": [
            "Read ~/claude_operator_state/CURSOR.md first every session",
            "Drop missions to data/cursor_missions/pending/ — Claude Code executes",
            "Never ask Mohamed to re-explain — grep CURSOR, backlog, git, scars",
            "Consult DeepSeek+RABIE before substantive builds (Rule #15-19)",
            "Mohamed = decisions/taste only; machine fixes itself",
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"written {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
