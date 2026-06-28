#!/usr/bin/env python3
"""BRAIN API (June 28, 2026) — the thin HTTP layer exposing ogz-knowledge's 3 contracts to the devs.

The reference bridge the dev platform calls. Wraps the 3 working functions behind HTTP:
  GET  /extract?handle=albaik                  → export_prefill.export()      (profile IN, fast sync)
  POST /produce  {handle,product,chain,...}    → export_produce_post.build()  (content OUT, slow → async)
  GET  /job/<job_id>                           → poll a produce job
  POST /performance {post_id, ...engagement}   → perf_ingestor.ingest()       (performance BACK, sync)
  GET  /health                                 → liveness + queue depth + HUMAIN state

DESIGNED WITH DeepSeek (reasoner, June 28). Its rulings, honored:
- /extract + /performance are FAST + SYNC. /produce is SLOW (caption gen + 2 judges, 30-180s) and is
  SERIALIZED by the single HUMAIN browser → async: 202 + job_id, ONE background worker drains a queue,
  devs poll /job/<id>. Queue full (backpressure) → 429 (never pile up concurrent produces).
- Single process, FILE-BASED state → one WRITE_LOCK guards every ledger mutation (produce + ingest) so
  concurrent requests can't corrupt the JSON ledgers.
- Idempotency: export_produce_post keys by post_id=(brand,product,slot) → a repeat returns the existing post.
- Auth: optional bearer token (BRAIN_API_TOKEN in ~/.abraham_env). Set it for real traffic; unset = open
  dev mode (logged warning). This is a reference bridge on the Mac Mini, not the devs' production runtime.

Run:  python3 scripts/brain_api.py            # port 4140
      BRAIN_API_TOKEN=... in ~/.abraham_env to require auth
"""
import json
import os
import queue
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

PORT = int(os.environ.get("BRAIN_API_PORT", "4140"))
QUEUE_MAX = 4                       # pending produce jobs before 429 (backpressure)
PER_JOB_SECONDS = 10                # conservative per-job drain estimate for Retry-After / ETA (C203);
# banked serves are ~0s, a cache-miss queues instantly — 10s is a safe upper bound for the dev's retry.
WRITE_LOCK = threading.Lock()       # serialize ALL ledger mutations (produce + ingest)
_JOBS = {}                          # job_id → {status, result, error, ts}  (ephemeral, fine for a bridge)
_JOBS_LOCK = threading.Lock()
_Q = queue.Queue(maxsize=QUEUE_MAX)


def _env(k):
    f = os.path.expanduser("~/.abraham_env")
    if os.path.exists(f):
        for l in open(f):
            if l.startswith(k + "="):
                return l.split("=", 1)[1].strip().strip('"')
    return os.environ.get(k)


_ENV_TOKEN = _env("BRAIN_API_TOKEN")
TOKEN = _ENV_TOKEN or uuid.uuid4().hex   # A7 (DeepSeek audit): NEVER open — generate a token if unset
# (/produce costs money + the ledger is writable; an open bridge is a DoS/exfil hole). Printed at startup.


# ── the produce worker: ONE thread, drains the queue, owns the HUMAIN browser serialization ──────
def _produce_worker():
    import export_produce_post as epp
    while True:
        job_id, args = _Q.get()
        _set_job(job_id, status="running")
        try:
            with WRITE_LOCK:        # produce writes produced_posts.jsonl + reads/writes kill_registry
                rec = epp.build(args["handle"], args["product"], args["chain"],
                                occasion=args.get("occasion", "everyday"),
                                produce=args.get("produce", True),
                                regenerate=args.get("regenerate", False))
            _set_job(job_id, status="done", result=rec)
        except Exception as e:
            _set_job(job_id, status="failed", error=f"{type(e).__name__}: {str(e)[:200]}")
        finally:
            _Q.task_done()


def _set_job(job_id, **kw):
    with _JOBS_LOCK:
        j = _JOBS.setdefault(job_id, {"created": int(time.time())})
        j.update(kw)
        j["updated"] = int(time.time())


def _get_job(job_id):
    with _JOBS_LOCK:
        return dict(_JOBS[job_id]) if job_id in _JOBS else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # quiet

    def _send(self, code, obj, headers=None):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self):
        # A7: auth is ALWAYS required now (TOKEN is never empty). /health stays open (liveness only).
        got = self.headers.get("Authorization", "")
        return got == f"Bearer {TOKEN}"

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return None

    # ── GET: /health, /extract, /job/<id> ──────────────────────────────────────
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            humain = False
            try:
                import humain_judge as hj
                humain = hj._humain_up()
            except Exception:
                pass
            return self._send(200, {"ok": True, "humain": humain, "queue_depth": _Q.qsize(),
                                    "auth_required": bool(TOKEN)})
        if not self._authed():
            return self._send(401, {"ok": False, "error": "unauthorized"})
        if u.path == "/extract":
            handle = (parse_qs(u.query).get("handle") or [""])[0]
            if not handle:
                return self._send(400, {"ok": False, "error": "missing ?handle="})
            if not (B / "clients" / handle).exists():   # unknown brand → 404, not an empty 200 (DeepSeek)
                return self._send(404, {"ok": False, "error": f"no client '{handle}' onboarded"})
            try:
                import export_prefill as ep
                return self._send(200, ep.export(handle))
            except Exception as e:
                return self._send(500, {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})
        if u.path.startswith("/job/"):
            j = _get_job(u.path[len("/job/"):])
            return self._send(200 if j else 404, j or {"ok": False, "error": "no such job"})
        return self._send(404, {"ok": False, "error": "not found"})

    # ── POST: /produce, /performance ───────────────────────────────────────────
    def do_POST(self):
        if not self._authed():
            return self._send(401, {"ok": False, "error": "unauthorized"})
        u = urlparse(self.path)
        data = self._body()
        if data is None:
            return self._send(400, {"ok": False, "error": "bad JSON body"})

        if u.path == "/produce":
            for k in ("handle", "product", "chain"):
                if not data.get(k):
                    return self._send(400, {"ok": False, "error": f"missing {k}"})
            job_id = uuid.uuid4().hex[:12]
            # C203 (orchestra shift 1, RABIE+DeepSeek pick): tell the dev queue depth + when to retry, so
            # the first handshake is RETRYABLE — never a blind 429→retry→429 black box.
            try:
                _Q.put_nowait((job_id, data))
            except queue.Full:
                return self._send(429, {"ok": False, "error": "produce queue full — retry shortly",
                                        "queue_depth": _Q.qsize(), "retry_after_seconds": PER_JOB_SECONDS},
                                  headers={"Retry-After": PER_JOB_SECONDS})
            _set_job(job_id, status="pending")
            pos = _Q.qsize()
            return self._send(202, {"ok": True, "job_id": job_id, "poll": f"/job/{job_id}",
                                    "queue_position": pos, "estimated_seconds": pos * PER_JOB_SECONDS})

        if u.path == "/performance":
            if not data.get("post_id"):
                return self._send(400, {"ok": False, "error": "missing post_id"})
            eng = {k: int(data.get(k, 0) or 0) for k in ("likes", "saves", "comments", "shares", "reach")}
            try:
                import perf_ingestor as pi
                with WRITE_LOCK:
                    rec = pi.ingest(data["post_id"], eng)
                return self._send(200, {"ok": True, "z_score": rec["z_score"],
                                        "action": rec["action"], "detail": rec["action_detail"]})
            except Exception as e:
                return self._send(500, {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"})

        return self._send(404, {"ok": False, "error": "not found"})


def main():
    threading.Thread(target=_produce_worker, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"🧠 brain_api on http://127.0.0.1:{PORT}  [🔒 auth required]")
    if _ENV_TOKEN:
        print("   token: from BRAIN_API_TOKEN (env)")
    else:
        print(f"   token (generated — devs use this, or set BRAIN_API_TOKEN to persist): {TOKEN}")
    print("   GET /extract?handle=  · POST /produce · GET /job/<id> · POST /performance · GET /health")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
