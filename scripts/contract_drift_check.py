#!/usr/bin/env python3
"""contract_drift_check.py — assert the OpenAPI spec mirrors the real API.

The connection contract for the dev platform lives in TWO hand-maintained places:
  • scripts/openapi.yaml   — the DECLARED contract the devs build against
  • scripts/brain_api.py   — the ACTUAL routes do_GET/do_POST serve

If those two drift apart, the doc becomes a lie that looks like progress
(Rule #6, the consumer law: a writer with no reader). This guard is the reader:
it compares the path SETS and REFUSES to pass (exit 1) on any mismatch.

Normalization: the spec writes the job-poll route as a templated path
`/job/{job_id}`; the code serves it as a prefix `u.path.startswith("/job/")`.
Those are the SAME route, so both collapse to the canonical key `/job/`.

Run:  python3 scripts/contract_drift_check.py
Exit: 0 = in sync, 1 = drift (with a printed diff).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ contract_drift_check: PyYAML not installed (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(1)

HERE = Path(__file__).resolve().parent
SPEC = HERE / "openapi.yaml"
API = HERE / "brain_api.py"

# Spec templated path  ↔  code prefix route: same logical route, one canonical key.
JOB_TEMPLATE = "/job/{job_id}"
JOB_PREFIX = "/job/"


def _canon(path: str) -> str:
    """Collapse the spec's templated job path and the code's prefix route to one key."""
    if path == JOB_TEMPLATE or path.startswith(JOB_PREFIX):
        return JOB_PREFIX
    return path


def spec_paths() -> set[str]:
    """The path keys declared under `paths:` in openapi.yaml."""
    if not SPEC.exists():
        print(f"❌ contract_drift_check: spec not found at {SPEC}", file=sys.stderr)
        raise SystemExit(1)
    doc = yaml.safe_load(SPEC.read_text(encoding="utf-8")) or {}
    declared = (doc.get("paths") or {}).keys()
    return {_canon(p) for p in declared}


def api_paths() -> set[str]:
    """The routes brain_api.py actually serves — from the do_GET/do_POST dispatch.

    Matches both shapes the handler uses:
      • exact   :  u.path == "/health"   /  '/extract' …
      • prefix  :  u.path.startswith("/job/")
    """
    if not API.exists():
        print(f"❌ contract_drift_check: api not found at {API}", file=sys.stderr)
        raise SystemExit(1)
    src = API.read_text(encoding="utf-8")
    found: set[str] = set()
    # u.path == "/..."   (single or double quotes)
    for m in re.finditer(r"""\.path\s*==\s*['"](/[^'"]*)['"]""", src):
        found.add(_canon(m.group(1)))
    # u.path.startswith("/job/")  (and any other startswith prefix routes)
    for m in re.finditer(r"""\.path\.startswith\(\s*['"](/[^'"]*)['"]\s*\)""", src):
        found.add(_canon(m.group(1)))
    return found


def main() -> int:
    spec = spec_paths()
    code = api_paths()

    if spec != code:
        only_spec = sorted(spec - code)
        only_code = sorted(code - spec)
        print("❌ contract_drift_check: spec ↔ api OUT OF SYNC")
        print(f"   spec paths ({len(spec)}): {sorted(spec)}")
        print(f"   api  paths ({len(code)}): {sorted(code)}")
        if only_spec:
            print(f"   📄 declared in openapi.yaml but NOT served by brain_api.py: {only_spec}")
        if only_code:
            print(f"   🔌 served by brain_api.py but NOT declared in openapi.yaml: {only_code}")
        raise SystemExit(1)

    print(f"✅ contract_drift_check: spec ↔ api in sync ({len(spec)} paths)")
    print(f"   paths: {sorted(spec)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
