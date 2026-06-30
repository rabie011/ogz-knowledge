#!/usr/bin/env python3
"""Fake platform client — simulates dev-platform wiring against brain_api WITHOUT real UI.

Mimics what o-gz-studios-web would do:
  1. User enters IG handle at onboarding
  2. Poll GET /extract (stands in for extraction-status)
  3. Map pre_fill into "form state"
  4. If ready → POST /produce → poll /job
  5. After "publish" → POST /performance

Run:
  python3 scripts/fake_platform_client.py              # core + sector scenarios
  python3 scripts/fake_platform_client.py --core-only
  python3 scripts/fake_platform_client.py --all-sectors
  python3 scripts/fake_platform_client.py --scenario onboarding_albaik
  python3 scripts/fake_platform_client.py --json       # machine report only

Writes: data/cursor_missions/done/fake-platform-test.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/done/fake-platform-test.json"
MANIFEST = ROOT / "data/fake_clients/manifest.yaml"
BASE = os.environ.get("BRAIN_BASE", "http://127.0.0.1:4140")


def _load_fake_manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data.get("clients") or {}


def _token() -> str:
    p = Path.home() / ".abraham_env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("BRAIN_API_TOKEN", "")


def _req(method: str, path: str, body: dict | None = None, timeout: int = 60) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    tok = _token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def _platform_wrap_extract(handle: str, brain: dict, brand_id: str) -> dict:
    """Shape brain /extract response like platform extraction-status."""
    cov = brain.get("_coverage", {})
    sources = brain.get("sources_present") or {
        "instagram": bool(brain.get("pre_fill", {}).get("ig_username")),
        "website": bool(brain.get("pre_fill", {}).get("website_url")),
        "places": cov.get("filled", 0) > 40,
    }
    status = "extraction_complete" if cov.get("pct", 0) >= 50 else "extraction_partial"
    return {
        "ok": brain.get("ok", True),
        "brand_id": brand_id,
        "onboarding_status": status,
        "sources_present": sources,
        "source_status": brain.get("source_status") or {
            k: ("done" if v else "unavailable") for k, v in sources.items()
        },
        "seed": brain.get("seed", {}),
        "pre_fill": brain.get("pre_fill", {}),
        "confidence": brain.get("confidence"),
        "brand_understanding": brain.get("brand_understanding"),
        "_brain_ready": brain.get("ready"),
        "_coverage": cov,
    }


def _poll_job(job_id: str, timeout: int = 180) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        st, j = _req("GET", f"/job/{job_id}")
        if j.get("status") in ("done", "failed", "refused"):
            return j
        time.sleep(3)
    return {"status": "timeout"}


def scenario_onboarding_albaik() -> dict:
    """Happy path: signup → extract → form filled."""
    brand_id = str(uuid.uuid4())
    handle = "albaik"
    st, brain = _req("GET", f"/extract?handle={handle}")
    wrapped = _platform_wrap_extract(handle, brain, brand_id)
    pre_fill = wrapped.get("pre_fill") or {}
    filled = sum(1 for v in pre_fill.values() if v is not None)
    ok = (
        st == 200
        and len(pre_fill) == 81
        and filled >= 50
        and wrapped.get("_brain_ready") is True
        and wrapped.get("onboarding_status") != "extraction_pending"
    )
    return {
        "name": "onboarding_albaik",
        "pass": ok,
        "status": st,
        "filled": filled,
        "ready": wrapped.get("_brain_ready"),
        "onboarding_status": wrapped.get("onboarding_status"),
    }


def scenario_sparse_myfitness() -> dict:
    """Sparse brand: extract works, ready=false, produce must refuse."""
    handle = "myfitness.sa"
    st, brain = _req("GET", f"/extract?handle={handle}")
    wrapped = _platform_wrap_extract(handle, brain, str(uuid.uuid4()))
    ready = brain.get("ready")
    st2, prod = _req(
        "POST",
        "/produce",
        {"handle": handle, "product": "منتج", "chain": "U01", "produce": False},
    )
    job = _poll_job(prod.get("job_id", "")) if st2 == 202 else {}
    rec = job.get("result") or {}
    refused = rec.get("status") == "refused" or rec.get("ok") is False
    ok = st == 200 and ready is False and job.get("status") == "done" and refused
    return {
        "name": "sparse_myfitness",
        "pass": ok,
        "extract_ready": ready,
        "produce_refused": refused,
        "detail": rec.get("reason") or prod.get("error"),
    }


def scenario_unknown_brand() -> dict:
    handle = "intake_probe_unknown_brand"
    st, body = _req("GET", f"/extract?handle={handle}")
    ok = (
        st == 200
        and body.get("ok") is True
        and body.get("onboarding_status") in ("extraction_pending", "extraction_failed")
        and body.get("ready") is False
        and len(body.get("pre_fill") or {}) == 81
        and bool((body.get("intake_job") or {}).get("status"))
    )
    return {"name": "unknown_brand_pending", "pass": ok, "status": st, "onboarding_status": body.get("onboarding_status")}


def scenario_no_auth() -> dict:
    """Platform forgot token → must get 401."""
    req = urllib.request.Request(f"{BASE}/extract?handle=albaik")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return {"name": "no_auth_rejected", "pass": False, "status": r.status}
    except urllib.error.HTTPError as e:
        return {"name": "no_auth_rejected", "pass": e.code == 401, "status": e.code}


def scenario_produce_eatjurisha() -> dict:
    """Banked produce path — platform generates content."""
    st, brain = _req("GET", "/extract?handle=eatjurisha")
    if not brain.get("ready"):
        return {"name": "produce_eatjurisha", "pass": False, "error": "not ready"}
    st2, prod = _req(
        "POST",
        "/produce",
        {"handle": "eatjurisha", "product": "جريش", "chain": "G03", "produce": False},
    )
    if st2 != 202:
        return {"name": "produce_eatjurisha", "pass": False, "status": st2, "body": prod}
    job = _poll_job(prod.get("job_id", ""))
    rec = job.get("result") or {}
    image_url = (rec.get("content") or {}).get("image_url")
    ok = job.get("status") == "done" and bool(image_url)
    return {
        "name": "produce_eatjurisha",
        "pass": ok,
        "job_status": job.get("status"),
        "image_url": image_url,
    }


def scenario_performance_loop() -> dict:
    """Simulate post-publish engagement → learning."""
    body = {
        "post_id": "eatjurisha__جريش__G03",
        "likes": 10,
        "saves": 2,
        "comments": 1,
        "shares": 0,
        "reach": 5000,
    }
    st, res = _req("POST", "/performance", body)
    ok = st == 200 and "z_score" in res
    return {"name": "performance_loop", "pass": ok, "status": st, "action": res.get("action")}


def scenario_extract_fake(handle: str, spec: dict) -> dict:
    st, brain = _req("GET", f"/extract?handle={handle}")
    pre_fill = brain.get("pre_fill") or {}
    filled = sum(1 for v in pre_fill.values() if v is not None)
    ok = (
        st == 200
        and len(pre_fill) == 81
        and filled >= 45
        and brain.get("ready") is True
        and bool(spec.get("sector"))
    )
    return {
        "name": f"extract_{handle}",
        "pass": ok,
        "status": st,
        "sector": spec.get("sector"),
        "filled": filled,
        "ready": brain.get("ready"),
        "sector_hint": pre_fill.get("sector_hint"),
    }


def scenario_produce_fake(handle: str, spec: dict) -> dict:
    product = spec.get("product", "منتج")
    chain = spec.get("chain", "U01")
    st, brain = _req("GET", f"/extract?handle={handle}")
    if not brain.get("ready"):
        return {"name": f"produce_{handle}", "pass": False, "error": "not ready"}
    st2, prod = _req(
        "POST",
        "/produce",
        {"handle": handle, "product": product, "chain": chain, "produce": False},
    )
    if st2 != 202:
        return {"name": f"produce_{handle}", "pass": False, "status": st2, "body": prod}
    job = _poll_job(prod.get("job_id", ""))
    rec = job.get("result") or {}
    image_url = (rec.get("content") or {}).get("image_url")
    ok = job.get("status") == "done" and bool(image_url)
    return {
        "name": f"produce_{handle}",
        "pass": ok,
        "job_status": job.get("status"),
        "image_url": image_url,
    }


def scenario_refuse_fake_sparse(handle: str, spec: dict) -> dict:
    st, brain = _req("GET", f"/extract?handle={handle}")
    ready = brain.get("ready")
    product = spec.get("product", "منتج")
    chain = spec.get("chain", "U01")
    st2, prod = _req(
        "POST",
        "/produce",
        {"handle": handle, "product": product, "chain": chain, "produce": False},
    )
    job = _poll_job(prod.get("job_id", "")) if st2 == 202 else {}
    rec = job.get("result") or {}
    refused = rec.get("status") == "refused" or rec.get("ok") is False
    ok = st == 200 and ready is False and job.get("status") == "done" and refused
    return {
        "name": f"refuse_{handle}",
        "pass": ok,
        "extract_ready": ready,
        "produce_refused": refused,
        "detail": rec.get("reason"),
    }


def _sector_scenarios() -> dict:
    out = {}
    manifest = _load_fake_manifest()
    for handle, spec in manifest.items():
        tier = spec.get("tier", "ready")
        if tier == "ready":
            out[f"extract_{handle}"] = lambda h=handle, s=spec: scenario_extract_fake(h, s)
            out[f"produce_{handle}"] = lambda h=handle, s=spec: scenario_produce_fake(h, s)
        else:
            out[f"refuse_{handle}"] = lambda h=handle, s=spec: scenario_refuse_fake_sparse(h, s)
    return out


CORE_SCENARIOS = {
    "onboarding_albaik": scenario_onboarding_albaik,
    "sparse_myfitness": scenario_sparse_myfitness,
    "unknown_brand_pending": scenario_unknown_brand,
    "no_auth_rejected": scenario_no_auth,
    "produce_eatjurisha": scenario_produce_eatjurisha,
    "performance_loop": scenario_performance_loop,
}

SCENARIOS = {**CORE_SCENARIOS, **_sector_scenarios()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=list(SCENARIOS.keys()))
    ap.add_argument("--core-only", action="store_true")
    ap.add_argument("--all-sectors", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.scenario:
        names = [args.scenario]
    elif args.core_only:
        names = list(CORE_SCENARIOS.keys())
    elif args.all_sectors:
        names = [k for k in SCENARIOS if k not in CORE_SCENARIOS]
    else:
        names = list(SCENARIOS.keys())
    results = [SCENARIOS[n]() for n in names]
    passed = sum(1 for r in results if r.get("pass"))
    report = {
        "id": "fake-platform-test",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulates": "o-gz-studios-web onboarding + produce + performance",
        "brain_base": BASE,
        "scenarios": results,
        "summary": f"{passed}/{len(results)} pass",
        "wire_ready_simulation": passed == len(results),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.json:
        print(json.dumps(report, indent=2))
    else:
        print(OUT)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
