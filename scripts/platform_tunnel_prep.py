#!/usr/bin/env python3
"""Platform brain tunnel prep — local checklist for Vercel → Mac Mini brain."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/artifacts/platform_tunnel_checklist.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    platform = Path.home() / "ogz-platform"
    checklist = {
        "ts": _now(),
        "mohamed_gate": "wire to production",
        "local_wire_done": (ROOT / "data/cursor_missions/artifacts/wire_complete.json").exists(),
        "platform_exists": platform.exists(),
        "brain_client": (platform / "lib/brain/client.ts").exists() if platform.exists() else False,
        "steps": [
            "Install cloudflared or ngrok on Mac Mini",
            "Tunnel https://localhost:4140 → public URL",
            "Set BRAIN_API_URL on Vercel to tunnel URL",
            "Set BRAIN_API_TOKEN on Vercel (sync from ~/.abraham_env)",
            "Test POST /extract from Vercel preview",
            "Mohamed says wire — then promote",
        ],
        "commands_hint": [
            "cloudflared tunnel --url http://127.0.0.1:4140",
            "python3 scripts/sync_brain_token_to_platform.py",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(checklist, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(checklist, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
