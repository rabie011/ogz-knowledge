#!/usr/bin/env python3
"""Read-only gate for the Mac brain — GET-only proxy on 127.0.0.1:4160.

RO1 (Mohamed 2026-07-19: "Read only"): cloud/tailnet devices may READ brain state,
never mutate it. This gate is the only surface they see:

    GET /health     open (liveness) — gate + brain status, no secrets
    GET /status     Bearer token — serves data/unified_status.json from disk
    GET /job/<id>   Bearer token — proxied to brain :4140 (job status is read-only)

Everything else — every POST/PUT/DELETE/PATCH, /produce, /performance, /extract
(/extract can trigger intake work, so it is NOT read-only) — is refused here,
regardless of token. Exposure (tailscale serve/funnel) is mac_readonly_wire.sh's
job; this process must stay bound to 127.0.0.1.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = Path.home() / ".abraham_env"
BIND = "127.0.0.1"  # never widen — tailscale serve/funnel is the only exposure path
PORT = 4160
BRAIN = "http://127.0.0.1:4140"
STATUS_FILE = ROOT / "data/unified_status.json"
JOB_ID_RE = re.compile(r"^[A-Za-z0-9]{1,32}$")


def _env(k: str) -> str | None:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(k)


TOKEN = _env("BRAIN_API_TOKEN") or uuid.uuid4().hex  # A7 pattern: NEVER open — random token if unset


class Gate(BaseHTTPRequestHandler):
    server_version = "OGZReadonlyGate/1.0"

    def _send(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self) -> bool:
        return self.headers.get("Authorization", "") == f"Bearer {TOKEN}"

    def _brain_get(self, path: str, forward_auth: bool) -> tuple[int, dict]:
        req = urllib.request.Request(BRAIN + path)
        if forward_auth:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode())
            except Exception:
                return e.code, {"ok": False, "error": f"brain HTTP {e.code}"}
        except Exception as e:
            return 502, {"ok": False, "error": f"brain unreachable: {type(e).__name__}"}

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/health":
            code, brain = self._brain_get("/health", forward_auth=False)
            return self._send(200, {"ok": True, "readonly_gate": True,
                                    "brain_ok": code == 200 and bool(brain.get("ok")),
                                    "brain": brain if code == 200 else {"ok": False}})
        if not self._authed():
            return self._send(401, {"ok": False, "error": "unauthorized"})
        if path == "/status":
            if not STATUS_FILE.exists():
                return self._send(404, {"ok": False, "error": "no unified_status.json — run mac_sync"})
            try:
                return self._send(200, json.loads(STATUS_FILE.read_text(encoding="utf-8")))
            except Exception as e:
                return self._send(500, {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
        if path.startswith("/job/"):
            job_id = path[len("/job/"):]
            if not JOB_ID_RE.match(job_id):
                return self._send(400, {"ok": False, "error": "bad job id"})
            code, body = self._brain_get(f"/job/{job_id}", forward_auth=True)
            return self._send(code, body)
        return self._send(404, {"ok": False, "error": "not found — read-only gate serves /health, /status, /job/<id>"})

    def _refuse_write(self):
        self._send(405, {"ok": False, "error": "read-only gate — writes are refused here; use brain :4140 locally"})

    do_POST = do_PUT = do_DELETE = do_PATCH = _refuse_write  # noqa: N815

    def log_message(self, fmt, *args):  # quiet; LaunchAgent captures stderr anyway
        pass


def main() -> None:
    if not _env("BRAIN_API_TOKEN"):
        print("WARN: BRAIN_API_TOKEN unset — gate fails closed (random token, authed routes unusable)")
    ThreadingHTTPServer((BIND, PORT), Gate).serve_forever()


if __name__ == "__main__":
    main()
