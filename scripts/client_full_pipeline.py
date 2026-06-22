#!/usr/bin/env python3
"""
client_full_pipeline.py  (B255)
Chain the five client stages into ONE fail-stop pipeline:

    intake  →  profile  →  year_map  →  render anchors  →  visual_gate_checklist

WHY THIS EXISTS (Rule #6 — the consumer law):
The five stage scripts already existed, but nobody chained them. A severed spine:
each stage WRITES an organ the next stage is supposed to READ, but with no chain a
stage can silently produce nothing and the next stage eats the gap. This wires the
spine and asserts it end-to-end — every writer's reader runs in the same pass.

FAIL-STOP (Rule #8 — refuse, don't warn):
If any stage exits non-zero, the pipeline STOPS and exits non-zero. It never
proceeds-with-a-note to a downstream stage on top of a broken upstream one. The
later stages would only manufacture garbage from the gap.

PER-STAGE MIRA REPORT:
Each stage prints its own ✓/✗ line with elapsed seconds and a tail of its output
BEFORE the next stage runs — so the chain is legible while it runs, not just after.

Usage:
  python3 scripts/client_full_pipeline.py --handle albaik
  python3 scripts/client_full_pipeline.py --handle albaik --sector f_and_b \\
        --start 2026-07-01 --anchor-date 2026-09-23
  python3 scripts/client_full_pipeline.py --handle albaik --dry-run   # print the plan, run nothing

The pipeline produces no client content of its own (Rules #12/#13) — it only
orchestrates the stage scripts that already produce + gate. We fix the machine.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).parent
BASE = SCRIPTS.parent
PYTHON = sys.executable


def _intake_args(handle, ns):
    return ["--handle", handle]


def _profile_args(handle, ns):
    return ["--handle", handle]


def _year_map_args(handle, ns):
    a = ["--handle", handle, "--sector", ns.sector]
    if ns.start:
        a += ["--start", ns.start]
    return a


def _render_args(handle, ns):
    # render ONE anchor card for the chain's smoke pass; the full anchor set is the
    # render-batch backlog, not this spine check. --anchor-date defaults to --start.
    date = ns.anchor_date or ns.start
    return ["--handle", handle, "--date", date]


def _visual_gate_args(handle, ns):
    # --all so the gate checklist covers every card the render stage just produced,
    # not only one — the reader must read everything the writer wrote (Rule #6).
    return ["--handle", handle, "--all"]


# The five stages, in spine order. Each entry: (name, script, args_builder).
STAGES = [
    ("intake", "client_intake.py", _intake_args),
    ("profile", "build_brand_profile.py", _profile_args),
    ("year_map", "year_map.py", _year_map_args),
    ("render_anchors", "render_client_slot.py", _render_args),
    ("visual_gate", "visual_gate_checklist.py", _visual_gate_args),
]


def _default_runner(cmd):
    """Real subprocess runner. Injectable so tests can drive the chain without
    actually executing the heavy stage scripts."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE))


def run_stage(stage, handle, ns, runner=_default_runner):
    """Run one stage. Returns (status, elapsed_s, summary) where status is
    'OK' | 'FAIL' | 'MISSING'. Never raises on a stage error — the caller
    decides the fail-stop."""
    name, script, args_fn = stage
    path = SCRIPTS / script
    if not path.exists():
        return ("MISSING", 0.0, f"{script} not found")

    cmd = [PYTHON, str(path)] + args_fn(handle, ns)
    print(f"  ...   {name:<16}", end="", flush=True)
    t0 = time.time()
    r = runner(cmd)
    elapsed = round(time.time() - t0, 1)
    out = (r.stdout or "")
    err = (r.stderr or "")
    if r.returncode == 0:
        tail = out.strip().splitlines()[-1][:80] if out.strip() else ""
        print(f"\r  ✓     {name:<16} ({elapsed}s)  {tail}")
        return ("OK", elapsed, tail)
    else:
        tail = (err or out or "").strip()[-160:]
        print(f"\r  ✗     {name:<16} ({elapsed}s)")
        print(f"        ↳ {tail[:140]}")
        return ("FAIL", elapsed, tail)


def run_pipeline(handle, ns, runner=_default_runner, stages=STAGES):
    """Run the chain with FAIL-STOP. Returns (ok: bool, results: list).
    The first non-OK stage halts the chain — downstream stages do NOT run."""
    results = []
    for stage in stages:
        status, elapsed, summary = run_stage(stage, handle, ns, runner=runner)
        results.append({"stage": stage[0], "status": status,
                        "elapsed": elapsed, "summary": summary})
        if status != "OK":
            # Rule #8: refuse, don't warn. Stop here; never feed a downstream
            # stage off a broken upstream one.
            print(f"\n  ⛔ FAIL-STOP at '{stage[0]}' ({status}) — "
                  f"halting before downstream stages.")
            return (False, results)
    return (True, results)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chain the five client stages (B255).")
    parser.add_argument("--handle", required=True)
    parser.add_argument("--sector", default="f_and_b")
    parser.add_argument("--start", default="2026-07-01")
    parser.add_argument("--anchor-date", default=None,
                        help="render-anchor date (defaults to --start)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the stage plan and exit without running")
    ns = parser.parse_args(argv)

    W = 65
    print(f"\n{'═' * W}")
    print(f"  CLIENT FULL PIPELINE — {ns.handle}")
    print(f"{'═' * W}\n")

    if ns.dry_run:
        for i, (name, script, args_fn) in enumerate(STAGES, 1):
            cmd = [script] + args_fn(ns.handle, ns)
            print(f"  {i}. {name:<16} {' '.join(cmd)}")
        print("\n  (dry-run — nothing executed)")
        return 0

    ok, results = run_pipeline(ns.handle, ns)

    print(f"\n{'─' * W}")
    done = sum(1 for r in results if r["status"] == "OK")
    print(f"  {done}/{len(STAGES)} stages OK" if ok
          else f"  PIPELINE FAILED — {done}/{len(STAGES)} stages ran clean")
    print(f"{'─' * W}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
