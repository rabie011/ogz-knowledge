#!/usr/bin/env python3
"""HUMAIN caption SERVICE — one long-lived process that holds the chat.humain.ai browser (and
Mohamed's login) OPEN, and answers caption requests over localhost HTTP. This is the seam that
makes HUMAIN usable as the orchestra's caption pen: the many short-lived produce_complete_post
subprocesses each POST a prompt here instead of launching their own browser (slow + would
re-trigger login every time).

  GET  /health            → {"logged_in": bool, "enabled": bool}
  POST /caption {prompt}  → {"reply": "<raw model text>"}  (reply=null on failure/not-logged-in)

Start it ONCE in the background; it opens the browser visible and waits for Mohamed to log in:
  python3 scripts/humain_service.py            # port 4111, waits up to 20 min for login

NEVER blocks a caller: /caption returns reply=null on any failure → the caption pipeline falls
back to GPT (Rule: never get stuck). Set HUMAIN_PEN=0 to disable HUMAIN entirely.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import humain_pen as hp

PORT = 4111


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # quiet

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"logged_in": bool(hp._logged_in), "enabled": hp.humain_available()})
        elif self.path == "/debug":
            self._json(200, hp.debug_dump())
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/caption":
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            prompt = data.get("prompt", "")
            timeout = int(data.get("timeout_s", 180))
        except Exception as e:
            self._json(400, {"error": f"bad request: {e}"})
            return
        if not prompt:
            self._json(400, {"error": "no prompt"})
            return
        reply = hp.humain_pen(prompt, timeout_s=timeout)
        self._json(200, {"reply": reply})


def main():
    print(f"🌐 HUMAIN service starting on http://localhost:{PORT}")
    print("   Opening browser — log in to chat.humain.ai if prompted (up to 20 min)...")
    # warm up in a thread so the HTTP server can start serving /health immediately
    def _warm():
        ok = hp.warm_up(login_wait_minutes=20)
        print(f"   HUMAIN login state: {'✅ logged in' if ok else '❌ not logged in'}", flush=True)
    threading.Thread(target=_warm, daemon=True).start()

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"   serving /health and POST /caption", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
