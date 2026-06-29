#!/usr/bin/env python3
"""DOCS-vs-CODE GUARD: scripts/openapi.yaml ↔ scripts/brain_api.py contract-drift checker.

The openapi.yaml is the dev platform's integration contract — the single document the devs
build their HTTP client against. brain_api.py is what the BRAIN actually serves. The instant
those two diverge (a new route shipped, a method added, an endpoint renamed) the contract
silently lies, and the devs integrate against routes that don't exist (or miss routes that do).

This is the gate that bites (Rule #8 — REFUSE, don't warn): exit 0 iff the documented route
set and the served route set are IDENTICAL, exit 1 (with the offenders printed) otherwise — so
the next undocumented route or method is a HARD CI failure, not a "by the way" in a stale doc.

It is file-INDEPENDENT and side-effect-free: it only READS the two source files. It NEVER
imports or runs brain_api.py (which would start a server / touch ledgers) — instead it statically
extracts the routes from the source TEXT (regex over do_GET/do_POST), so the check is safe to run
anywhere, anytime, in CI.

Two sources of truth, reduced to the same shape — a set of "<path> <METHOD>" strings:
  A) openapi.yaml  → the `paths:` map, normalizing the OpenAPI path-template `/job/{job_id}`
                     to the code form `/job/<id>` (the brain's catch-all job-poll route).
  B) brain_api.py  → which `u.path == "..."` / `u.path.startswith("/job/")` branch sits inside
                     which handler (do_GET → GET, do_POST → POST); the startswith('/job/')
                     branch maps to `/job/<id> GET`.

Run:  python3 scripts/check_contract_drift.py     # exit 0 = in sync, exit 1 = drift
Today both sides MUST equal: /health GET · /extract GET · /produce POST · /job/<id> GET · /performance POST
"""
import re
import sys
from pathlib import Path

import yaml  # pyyaml — already used across the repo

REPO = Path(__file__).parent.parent
OPENAPI = REPO / "scripts" / "openapi.yaml"
BRAIN_API = REPO / "scripts" / "brain_api.py"

# The OpenAPI path-template for the job-poll route → the code form the brain actually matches.
# brain_api.py serves it via `u.path.startswith("/job/")` (a catch-all on the job_id), which we
# canonicalize to "/job/<id>"; the openapi.yaml documents it as the template "/job/{job_id}".
JOB_TEMPLATE = "/job/{job_id}"
JOB_CODE_FORM = "/job/<id>"


def normalize_path(p):
    """Map an OpenAPI path template to the brain's code form. Only /job/{job_id} differs today;
    everything else is a literal that must match byte-for-byte."""
    if p == JOB_TEMPLATE:
        return JOB_CODE_FORM
    return p


def documented_routes():
    """Source of truth A — parse openapi.yaml → set of '<path> <METHOD>' strings."""
    spec = yaml.safe_load(OPENAPI.read_text())
    routes = set()
    for path, methods in (spec.get("paths") or {}).items():
        norm = normalize_path(path)
        for method in methods:
            # a path item can carry non-method keys (parameters, summary, $ref, servers…)
            if method.lower() in ("get", "post", "put", "patch", "delete", "head", "options"):
                routes.add(f"{norm} {method.upper()}")
    return routes


# the per-handler route patterns we statically recognize in brain_api.py source text:
#   u.path == "…"                 → a literal route on that handler's method
#   u.path.startswith("/job/")    → the catch-all job-poll route → /job/<id>
_EQ_RE = re.compile(r'u\.path\s*==\s*"([^"]+)"')
_JOB_STARTSWITH_RE = re.compile(r'u\.path\.startswith\(\s*"/job/"\s*\)')


def _handler_body(src, name):
    """Slice the source of one handler method (def do_GET / def do_POST) by indentation —
    from `def <name>(` to the next top-level `def ` at the same indent depth (or EOF)."""
    lines = src.splitlines()
    start = None
    indent = None
    for i, ln in enumerate(lines):
        m = re.match(r'^(\s*)def\s+' + re.escape(name) + r'\b', ln)
        if m:
            start = i
            indent = len(m.group(1))
            break
    if start is None:
        return ""
    body = [lines[start]]
    for ln in lines[start + 1:]:
        # stop at the next def/class at the SAME indent (sibling method) — but keep deeper lines
        m = re.match(r'^(\s*)(def|class)\s', ln)
        if m and len(m.group(1)) <= indent:
            break
        body.append(ln)
    return "\n".join(body)


def served_routes():
    """Source of truth B — STATICALLY extract routes from brain_api.py WITHOUT importing it.
    Reads the do_GET / do_POST handler bodies and maps each route-branch to '<path> <METHOD>'."""
    src = BRAIN_API.read_text()
    routes = set()
    for handler, method in (("do_GET", "GET"), ("do_POST", "POST")):
        body = _handler_body(src, handler)
        for path in _EQ_RE.findall(body):
            routes.add(f"{path} {method}")
        if _JOB_STARTSWITH_RE.search(body):
            routes.add(f"{JOB_CODE_FORM} {method}")
    return routes


def main():
    if not OPENAPI.exists():
        print(f"❌ openapi.yaml not found at {OPENAPI}")
        return 1
    if not BRAIN_API.exists():
        print(f"❌ brain_api.py not found at {BRAIN_API}")
        return 1

    documented = documented_routes()
    served = served_routes()

    documented_not_served = sorted(documented - served)
    served_not_documented = sorted(served - documented)

    drift = bool(documented_not_served or served_not_documented)

    if documented_not_served:
        print("❌ DOCUMENTED but NOT SERVED (openapi.yaml promises a route brain_api.py doesn't serve):")
        for r in documented_not_served:
            print(f"   - {r}")
    if served_not_documented:
        print("❌ SERVED but NOT DOCUMENTED (brain_api.py serves a route the contract never declares):")
        for r in served_not_documented:
            print(f"   - {r}")

    if drift:
        print(f"\n🔴 CONTRACT DRIFT — openapi.yaml ↔ brain_api.py out of sync "
              f"({len(documented)} documented vs {len(served)} served). "
              f"Fix the doc OR the route, then re-run. (Rule #8: refuse, don't warn.)")
        return 1

    routes = sorted(served)
    print(f"✅ openapi ↔ brain_api in sync ({len(routes)} routes)")
    for r in routes:
        print(f"   · {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
