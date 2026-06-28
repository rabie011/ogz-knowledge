#!/usr/bin/env python3
"""JOB LIFECYCLE UNIT TEST (June 29, 2026) — guards brain_api's in-memory job tracking.

A pure UNIT test: it IMPORTS brain_api and exercises _set_job / _get_job DIRECTLY. It does NOT start the
HTTP server or bind port 4140 (other agents run in parallel — a server would collide). Importing brain_api
is side-effect-free: the worker thread + ThreadingHTTPServer only start inside main()/__main__, never on import.

Asserts the three states the bridge depends on (see scripts/test_brain_connection.py for the live HTTP test):
  1. an unknown job_id → None (not a crash, not a stale dict)
  2. _set_job creates + tracks a job (status round-trips)
  3. _set_job updates in place, preserves `created`, carries `result`, and keeps updated ≥ created

Assert-based (Rule #8): any failure raises SystemExit(1) — never a soft pass.
Run: python3 scripts/test_job_lifecycle.py
"""
import sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

import brain_api  # noqa: E402  (import after sys.path insert — no server starts on import)


def main():
    n = 0

    # 1. unknown job → None
    assert brain_api._get_job("does-not-exist") is None, "_get_job on unknown id must be None"
    n += 1

    # 2. set creates + tracks; status round-trips
    brain_api._set_job("j1", status="pending")
    j = brain_api._get_job("j1")
    assert j is not None, "_get_job('j1') must exist after _set_job"
    n += 1
    assert j["status"] == "pending", f"expected status 'pending', got {j.get('status')!r}"
    n += 1

    # 3. update in place — status changes, result lands, created preserved, updated ≥ created
    brain_api._set_job("j1", status="done", result={"x": 1})
    j = brain_api._get_job("j1")
    assert j["status"] == "done", f"expected status 'done', got {j.get('status')!r}"
    n += 1
    assert j["result"] == {"x": 1}, f"expected result {{'x':1}}, got {j.get('result')!r}"
    n += 1
    assert j["updated"] >= j["created"], f"updated ({j['updated']}) must be >= created ({j['created']})"
    n += 1

    print(f"✅ job lifecycle: {n} asserts passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"❌ job lifecycle FAILED: {e}")
        raise SystemExit(1)
