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
import time
import urllib.request
from pathlib import Path

SVC = "http://127.0.0.1:4111"
LOCK = Path.home() / ".humain.lock"


class HumainDown(Exception):
    """HUMAIN gave no reply after serialized retries — fail-closed (the caller must NOT silently use GPT)."""


def call(prompt, timeout_s=45, retries=3):
    """Serialized HUMAIN /caption call: ONE request at a time across processes; retry on null; fail-closed.
    Returns the reply string, or raises HumainDown after `retries` nulls."""
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
                        return reply
                except Exception as e:
                    last = e
                time.sleep(2)   # brief settle before the next serialized attempt
            raise HumainDown(f"HUMAIN null after {retries} serialized retries "
                             f"(last: {type(last).__name__ if last else 'null-reply'}) — fail-closed")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)
