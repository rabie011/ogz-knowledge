#!/usr/bin/env python3
"""Unknown-handle intake — async extraction_pending responses for new platform signups.

When GET /extract?handle= is called for a handle with no clients/{handle}/ folder yet,
return HTTP 200 + extraction_pending (not 404) and kick harvest in the background.

State: data/intake_jobs/{handle}.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

B = Path(__file__).resolve().parents[1]
JOBS = B / "data/intake_jobs"
CLIENTS = B / "clients"
_LOCK = threading.Lock()
_RUNNING: set[str] = set()

sys.path.insert(0, str(B / "scripts"))
from export_prefill import PREFILL_KEYS, READY_MIN_COVERAGE, export as export_prefill


def _job_path(handle: str) -> Path:
    return JOBS / f"{handle}.json"


def _read_job(handle: str) -> dict | None:
    p = _job_path(handle)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_job(handle: str, **kw) -> dict:
    JOBS.mkdir(parents=True, exist_ok=True)
    job = _read_job(handle) or {
        "handle": handle,
        "status": "pending",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    job.update(kw)
    job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _job_path(handle).write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    return job


PROBE_PREFIXES = ("intake_probe_", "__intake_test_")


def is_probe_handle(handle: str) -> bool:
    return any(handle.startswith(p) for p in PROBE_PREFIXES)


def client_exists(handle: str) -> bool:
    if is_probe_handle(handle):
        return False
    return (CLIENTS / handle).is_dir()


def pending_export(handle: str, job: dict | None = None) -> dict:
    """Platform-shaped wrapper while harvest runs — honest nulls, not fake data."""
    job = job or _read_job(handle) or {}
    status = job.get("status", "pending")
    if status == "failed":
        onboarding = "extraction_failed"
        ig_status = "failed"
    elif status == "running":
        onboarding = "extraction_pending"
        ig_status = "pending"
    else:
        onboarding = "extraction_pending"
        ig_status = "pending"

    pre_fill = {k: None for k in PREFILL_KEYS}
    pre_fill["ig_username"] = handle
    pre_fill["confidence"] = 0.0
    pre_fill["brand_understanding"] = None

    return {
        "ok": True,
        "schema_version": "ogz-prefill-1.0",
        "brand_id": f"ogz:{handle}",
        "onboarding_status": onboarding,
        "ready": False,
        "readiness": {
            "ready": False,
            "coverage_pct": 0,
            "banked_renders": 0,
            "min_coverage": READY_MIN_COVERAGE,
            "blocking_reasons": ["intake in progress — poll again"],
        },
        "intake_job": {
            "handle": handle,
            "status": status,
            "started_at": job.get("started_at"),
            "error": job.get("error"),
        },
        "sources_present": {"instagram": False, "website": False, "places": False},
        "source_status": {
            "instagram": ig_status,
            "website": "unavailable",
            "places": "unavailable",
        },
        "seed": {"brand_name_ar": None, "sector": None, "city_primary": None},
        "pre_fill": pre_fill,
        "confidence": 0.0,
        "brand_understanding": None,
        "_coverage": {
            "filled": 1,
            "total": len(PREFILL_KEYS),
            "pct": 0,
            "null_fields": [k for k in PREFILL_KEYS if k != "ig_username"],
            "low_confidence_fields": [],
            "field_sources": {},
        },
    }


def _harvest_worker(handle: str) -> None:
    _write_job(handle, status="running")
    try:
        r = subprocess.run(
            [sys.executable, str(B / "scripts/client_intake.py"), "--handle", handle, "--harvest-only"],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(B),
        )
        if r.returncode == 0 and client_exists(handle):
            _write_job(handle, status="done", harvest_rc=0)
        else:
            err = (r.stderr or r.stdout or f"rc={r.returncode}")[:300]
            _write_job(handle, status="failed", error=err, harvest_rc=r.returncode)
    except Exception as e:
        _write_job(handle, status="failed", error=f"{type(e).__name__}: {str(e)[:200]}")
    finally:
        with _LOCK:
            _RUNNING.discard(handle)


def ensure_intake_started(handle: str) -> dict:
    """Idempotent: start background harvest once per handle."""
    if is_probe_handle(handle):
        return {"handle": handle, "status": "pending"}
    with _LOCK:
        if handle in _RUNNING:
            return _read_job(handle) or _write_job(handle, status="running")
        job = _read_job(handle)
        if job and job.get("status") in ("running", "done"):
            return job
        _RUNNING.add(handle)
    _write_job(handle, status="pending")
    threading.Thread(target=_harvest_worker, args=(handle,), daemon=True).start()
    return _read_job(handle) or {}


def handle_extract(handle: str) -> tuple[int, dict]:
    """Brain /extract logic: existing client → full export; unknown → pending + async harvest."""
    if is_probe_handle(handle):
        return 200, pending_export(handle, {"status": "pending"})

    if client_exists(handle):
        raw = CLIENTS / handle / "raw" / "instagram"
        has_raw = raw.exists() and any(raw.glob("*/profile.json"))
        if has_raw or any((CLIENTS / handle / "profile").glob("*.json")):
            try:
                return 200, export_prefill(handle)
            except Exception as e:
                return 500, {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}

    job = ensure_intake_started(handle)
    if client_exists(handle):
        try:
            return 200, export_prefill(handle)
        except Exception:
            pass
    return 200, pending_export(handle, job)
