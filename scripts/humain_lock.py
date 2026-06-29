#!/usr/bin/env python3
"""humain_lock — serialize ALL access to the single HUMAIN browser session (localhost:4111).

DeepSeek consult (June 29, shown live to Mohamed): humain_service is a ThreadingHTTPServer serving CONCURRENT
requests to ONE browser tab → race → null drift. The writer-pen (render_client_slot.humain) AND the judge
(humain_judge) both POST /caption to the same session. This file-lock serializes them ACROSS PROCESSES (the
produce runs as a subprocess), retries up to 3x on null, and FAILS CLOSED (raises HumainDown) after — never
letting a null silently fall through. DeepSeek's rule: 'after 3 nulls, HARD STOP — do NOT let GPT auto-proceed.'
Orchestrator-side (NOT a server lock — a server lock would block /health = SPOF in the request path).
"""
import fcntl
import json
import subprocess
import time
import urllib.request
from pathlib import Path

SVC = "http://127.0.0.1:4111"
LOCK = Path.home() / ".humain.lock"
# PROACTIVE PAGE-RECYCLE (June 29, 3-chairs consult option (b) — DeepSeek argued it, RABIE accepted, shown live):
# the persistent Playwright page DRIFTS after ~15-20 calls (/health stays logged_in:true but the scrape returns
# null). humain_watchdog restarts it for a fresh page — but only ~every 30min (launchd), so an active judging BURST
# sits in a null-window up to 30min (the posts-5/6/8 drift). FIX: recycle the page PROACTIVELY at 12 calls (before
# the 15-20 drift), in the BACKGROUND, OUTSIDE the lock hold. This is NOT the C231 in-lock restart SPOF — that was
# an UNBOUNDED restart-on-failure hang; this is a bounded (≤~60s) proactive recycle that counts only SUCCESSES.
COUNT = Path.home() / ".humain.callcount"
RECYCLE_AT = 12
_PY = "/opt/homebrew/bin/python3"
_SERVICE = str(Path.home() / "Desktop/ogz-knowledge/scripts/humain_service.py")
_LOG = str(Path.home() / "logs/humain_service.log")


class HumainDown(Exception):
    """HUMAIN gave no reply after serialized retries — fail-closed (the caller must NOT silently use GPT)."""


def _count():
    try:
        return int(COUNT.read_text().strip())
    except Exception:
        return 0


def _probe():
    """The REAL readiness test — /health logged_in LIES under drift (true even when the scrape is null), so
    probe the actual /caption path like humain_watchdog does."""
    try:
        body = json.dumps({"prompt": "رد بكلمة واحدة: تمام", "timeout_s": 30}).encode()
        rq = urllib.request.Request(f"{SVC}/caption", data=body, headers={"Content-Type": "application/json"})
        return bool(json.loads(urllib.request.urlopen(rq, timeout=40).read()).get("reply"))
    except Exception:
        return False


def _maybe_recycle():
    """≥RECYCLE_AT successful calls since the last recycle → restart the service for a FRESH page BEFORE the page
    drifts. Runs OUTSIDE the file-lock (DeepSeek: never restart inside a lock hold). Reset-counter-FIRST so two
    callers can't double-restart. The readiness wait is BOUNDED (≤~60s) → structurally cannot become the C231
    unbounded restart-loop SPOF. Cost: ~one cold-start (≤60s) per 12 calls — invisible between posts (RABIE)."""
    if _count() < RECYCLE_AT:
        return
    try:
        COUNT.write_text("0")                                   # reset first → only one caller recycles
        subprocess.run(["pkill", "-f", "humain_service.py"])
        time.sleep(2)
        subprocess.Popen([_PY, _SERVICE], stdout=open(_LOG, "a"), stderr=subprocess.STDOUT)
        for _ in range(12):                                     # bounded ≤60s — never an unbounded loop
            time.sleep(5)
            if _probe():
                break
    except Exception:
        pass


def _bump():
    try:
        COUNT.write_text(str(_count() + 1))                     # count only SUCCESSES toward the recycle threshold
    except Exception:
        pass


def call(prompt, timeout_s=45, retries=3):
    """Serialized HUMAIN /caption call: ONE request at a time across processes; retry on null; fail-closed.
    Returns the reply string, or raises HumainDown after `retries` nulls."""
    _maybe_recycle()                     # proactive fresh-page BEFORE drift (3-chairs (b)) — OUTSIDE the lock
    LOCK.touch(exist_ok=True)
    with open(LOCK, "r+") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)   # serialize: only one HUMAIN request hits the browser at a time
        try:
            last = None
            for _ in range(retries):
                try:
                    body = json.dumps({"prompt": prompt, "timeout_s": timeout_s}).encode()
                    rq = urllib.request.Request(f"{SVC}/caption", data=body,
                                                headers={"Content-Type": "application/json"})
                    reply = json.loads(urllib.request.urlopen(rq, timeout=timeout_s + 20).read()).get("reply")
                    if reply:
                        _bump()          # success → advance the recycle counter
                        return reply
                except Exception as e:
                    last = e
                time.sleep(2)   # brief settle before the next serialized attempt
            raise HumainDown(f"HUMAIN null after {retries} serialized retries "
                             f"(last: {type(last).__name__ if last else 'null-reply'}) — fail-closed")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)
