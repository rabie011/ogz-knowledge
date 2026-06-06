#!/usr/bin/env python3
"""
memory_keeper.py — Autonomous 24/7 memory freshness daemon.

Runs via LaunchAgent (com.abraham.memory-keeper) using the SAME venv python3
that ogz_enricher uses — so it inherits that binary's Full Disk Access grant
(a plain /bin/bash LaunchAgent is blocked by macOS TCC from reading ~/Desktop).

WHAT IT DOES:
  Refreshes the FACTUAL half of CURSOR.md — git state, obs/template counts,
  brain version, API health, what's running. A new session always opens to
  current facts, never a stale recap.

WHAT IT NEVER TOUCHES:
  The agent-written NARRATIVE (LAST THING DONE / NEXT ACTION). Only the agent
  knows that mid-session. The daemon owns only the text between the AUTO markers.

SAFE:
  - Read-only on all repos.
  - SANITY GUARD: if obs count reads 0 (repo unreadable), it ABORTS the write
    and leaves CURSOR untouched — never corrupts good memory with bad data.
"""
from __future__ import annotations
import json, subprocess, re, urllib.request
from datetime import datetime
from pathlib import Path

HOME       = Path.home()
STATE_DIR  = HOME / "claude_operator_state"
CURSOR     = STATE_DIR / "CURSOR.md"
HEARTBEAT  = STATE_DIR / ".memory-keeper-heartbeat"
LOG        = HOME / "logs" / "memory-keeper.log"
OGZ        = HOME / "Desktop" / "ogz-knowledge"
WAR        = HOME / "war-room"
LOG.parent.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sh(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:
        return ""


def log(msg: str):
    with LOG.open("a") as f:
        f.write(f"[{TS}] {msg}\n")
    # trim to last 200 lines
    lines = LOG.read_text().splitlines()[-200:]
    LOG.write_text("\n".join(lines) + "\n")


# ── Gather facts ────────────────────────────────────────────
obs_count = len(list((OGZ / "11_who_to_learn_from" / "observations").rglob("*.json"))) if OGZ.exists() else 0

try:
    tlib = json.loads((OGZ / "11_who_to_learn_from" / "template_library.json").read_text())
    template_count = len(tlib.get("templates", []))
except Exception:
    template_count = "?"

try:
    brain = json.loads((OGZ / "11_who_to_learn_from" / "intelligence_layer.json").read_text())
    brain_version = brain.get("meta", {}).get("version", "?")
except Exception:
    brain_version = "?"

ogz_commit = sh(["git", "log", "--oneline", "-1"], cwd=OGZ)
ogz_tag    = sh(["git", "describe", "--tags", "--abbrev=0"], cwd=OGZ)
ogz_dirty  = len(sh(["git", "status", "--short"], cwd=OGZ).splitlines())
war_dirty  = len(sh(["git", "status", "--short"], cwd=WAR).splitlines())

# API health
try:
    with urllib.request.urlopen("http://localhost:4100/api/health", timeout=3) as r:
        api_status = "✅ running (port 4100)" if json.loads(r.read()).get("status") == "healthy" else "⚠️ unhealthy"
except Exception:
    api_status = "❌ down — restart: cd ~/Desktop/ogz-knowledge && nohup python3 -m uvicorn api.server:app --port 4100 --host 0.0.0.0 > ~/logs/api_4100.log 2>&1 &"

# Daemons
def running(name: str) -> str:
    return "✅" if sh(["pgrep", "-f", name]) else "❌"

enricher = running("ogz_enricher.py")
abraham  = running("abraham_os.py")

# API keys (status only, never the value)
env_text = (HOME / ".abraham_env").read_text() if (HOME / ".abraham_env").exists() else ""
openai_ok = "✅ paid key" if "OPENAI_API_KEY=sk-" in env_text else "❌"
apify_ok  = "✅ configured" if "APIFY_TOKEN=" in env_text else "❌"


# ── SANITY GUARD ────────────────────────────────────────────
if not obs_count:
    log("⚠️  ABORT — obs=0 (repo unreadable). CURSOR left untouched.")
    HEARTBEAT.write_text(f"{TS} UNREADABLE")
    raise SystemExit(0)


# ── Build the auto-managed block ────────────────────────────
block = f"""<!-- AUTO:START — refreshed by memory_keeper.py every 6h. Do not edit by hand. -->
## SYSTEM STATE (auto-refreshed {TS})

**API keys:** OpenAI {openai_ok} | Apify {apify_ok}

**OGZ Knowledge** (`~/Desktop/ogz-knowledge/`)
- Last commit: `{ogz_commit}`
- Tag: {ogz_tag} | Uncommitted files: {ogz_dirty}
- Brain v{brain_version} | {obs_count} obs | {template_count} templates
- API: {api_status}

**Daemons:** enricher {enricher} | abraham_os {abraham}

**Play Room** (`~/war-room/`): {war_dirty} uncommitted files
<!-- AUTO:END -->"""

# ── Splice into CURSOR.md (preserve narrative half) ─────────
if CURSOR.exists() and "AUTO:START" in CURSOR.read_text():
    content = CURSOR.read_text()
    new = re.sub(r"<!-- AUTO:START.*?AUTO:END -->", block, content, flags=re.DOTALL)
    CURSOR.write_text(new)
else:
    with CURSOR.open("a") as f:
        f.write("\n" + block + "\n")

HEARTBEAT.write_text(TS)
log(f"ran — obs={obs_count} templates={template_count} brain=v{brain_version} api={api_status[:12]}")
