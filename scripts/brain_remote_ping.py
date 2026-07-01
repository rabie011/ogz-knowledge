#!/usr/bin/env python3
"""Ping brain via data/brain_remote_endpoint.json (Tailscale). Fails gracefully off-tailnet."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "data/brain_remote_endpoint.json"
ENV = Path.home() / ".abraham_env"


def _env(k: str) -> str | None:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(k)


def main() -> int:
    if not ENDPOINT.exists():
        print(json.dumps({"ok": False, "error": "no brain_remote_endpoint.json — run mac_tailscale_wire.sh on Mac"}))
        return 1
    ep = json.loads(ENDPOINT.read_text(encoding="utf-8"))
    host = ep.get("host")
    port = ep.get("port", 4140)
    if not host:
        print(json.dumps({"ok": False, "error": "endpoint missing host"}))
        return 1
    token = _env("BRAIN_API_TOKEN")
    url = f"http://{host}:{port}/health"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read().decode())
        print(json.dumps({"ok": True, "url": url, "health": body}, indent=2))
        return 0
    except urllib.error.URLError as e:
        print(json.dumps({
            "ok": False,
            "url": url,
            "error": str(e)[:200],
            "hint": "Cloud agent is not on tailnet — use GitHub sync; or join tailnet with TS auth key",
        }, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
