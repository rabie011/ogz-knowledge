#!/usr/bin/env python3
"""CREATIVE agent loop — prep concepts + judge path. NO autonomous FAL (Mohamed gate: render go)."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/creative_outputs"
PYTHON = "/opt/homebrew/bin/python3"
PILOTS = ("albaik", "eatjurisha", "myfitness.sa")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _pilot_ready(client: str) -> dict | None:
    handoff = ROOT / "data/cursor_missions/artifacts/handoff/README.json"
    if handoff.exists():
        try:
            pilots = json.loads(handoff.read_text(encoding="utf-8")).get("pilots", {})
            if client in pilots:
                return pilots[client]
        except Exception:
            pass
    p = ROOT / f"data/clients/{client}/readiness.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_cycle(*, dry_run: bool = True) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    proposals = []
    for client in PILOTS:
        ready = _pilot_ready(client)
        if not ready:
            proposals.append({"client": client, "status": "no_readiness_file"})
            continue
        proposals.append({
            "client": client,
            "ready": ready.get("ready", False),
            "coverage": ready.get("coverage_pct"),
            "banked_renders": ready.get("banked_renders", 0),
            "next_action": "await_mohamed_render_go" if dry_run else "render_pipeline",
        })
    result = {
        "ts": _now(),
        "dry_run": dry_run,
        "mohamed_gate": "render go required for FAL",
        "proposals": proposals,
        "rabie_available": (ROOT / "scripts/rabie_judge.py").exists(),
        "humain_port": 4111,
    }
    path = OUT / f"cycle_{_now()[:19].replace(':', '')}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Non-spend: refresh taste rank if available
    if (ROOT / "scripts/taste_rank.py").exists():
        subprocess.run([PYTHON, str(ROOT / "scripts/taste_rank.py")], cwd=str(ROOT), check=False, capture_output=True)

    subprocess.run(
        [PYTHON, str(ROOT / "scripts/live_feed.py"), "creative", "cycle", f"Creative loop — {len(proposals)} pilots reviewed (no FAL)"],
        cwd=str(ROOT),
        check=False,
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="Mohamed authorized render go — still requires explicit render script")
    args = ap.parse_args()
    result = run_cycle(dry_run=not args.go)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
