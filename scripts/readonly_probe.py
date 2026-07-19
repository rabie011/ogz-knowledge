#!/usr/bin/env python3
"""Probe the read-only gate via data/readonly_endpoint.json (cloud- and tailnet-side).

Funnel mode (https base_url) is reachable from anywhere, including cloud sessions
behind an HTTPS proxy. Tailnet mode only works from a device on the tailnet —
off-tailnet the probe fails gracefully, same as brain_remote_ping.py.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "data/readonly_endpoint.json"
ENV = Path.home() / ".abraham_env"


def _env(k: str) -> str | None:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(k)


def main() -> int:
    if not ENDPOINT.exists():
        print(json.dumps({"ok": False, "error": "no readonly_endpoint.json — run mac_readonly_wire.sh on Mac"}))
        return 1
    ep = json.loads(ENDPOINT.read_text(encoding="utf-8"))
    base = ep.get("base_url")
    if not base:
        print(json.dumps({"ok": False, "error": "endpoint missing base_url"}))
        return 1
    path = sys.argv[1] if len(sys.argv) > 1 else "/health"
    req = urllib.request.Request(base + path)
    token = _env("BRAIN_API_TOKEN")
    if token and path != "/health":
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
        print(json.dumps({"ok": True, "url": base + path, "mode": ep.get("mode"), "body": body}, indent=2))
        return 0
    except urllib.error.URLError as e:
        print(json.dumps({
            "ok": False,
            "url": base + path,
            "mode": ep.get("mode"),
            "error": str(e)[:200],
            "hint": "tailnet mode needs a tailnet device; funnel mode needs OGZ_FUNNEL_GO wire on Mac",
        }, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
