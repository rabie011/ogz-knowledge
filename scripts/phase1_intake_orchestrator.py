#!/usr/bin/env python3
"""PHASE 1 — the intake ORCHESTRATOR: a new brand onboards itself with ZERO manual JSON.

The Scale On-ramp's funnel-unblocker (designed + fact-checked with DeepSeek). Today a human
(Claude/Mohamed) hand-builds every client's organs — that does NOT scale to 1000 users, and it's
why myfitness.sa sits empty. This orchestrates the existing pieces into one self-service flow:

  self-service form (JSON)
    → [harvest]   client_intake.py --harvest-only   (raw IG corpus + gap_report)   [TWEAK, optional]
    → [research]  research_fill_established.fill()   (l1_strategy/red_lines/goals, experimental)
    → [form]      fill_organs_from_intake.fill_all_organs()  (product_truth/visual_dna/cultural/red_lines, CONFIRMED)
    → [verify]    readiness gate: are the produce-critical organs non-null + no human confirmer?

The verified facts this rests on: organ_write.py is the atomic+versioned+never-deletes writer (all
fills go through it); the 29 schemas are the contract; research_fill_established already fills 3
organs. Claude NEVER hand-writes a new client's organs again — only reviews flagged conflicts.

Usage:
  python3 scripts/phase1_intake_orchestrator.py --handle mynewcafe --form /tmp/intake.json
  python3 scripts/phase1_intake_orchestrator.py --handle mynewcafe --form ... --no-harvest --no-research
  python3 scripts/phase1_intake_orchestrator.py --handle mynewcafe --form ... --base /tmp/test   # sandbox
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import fill_organs_from_intake as foi

# the produce-critical organs a brand MUST have before it can generate a post
PRODUCE_CRITICAL = ("product_truth", "visual_dna", "cultural_overrides", "red_lines")


def _organ_nonempty(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        d = json.loads(path.read_text())
    except Exception:
        return False
    # non-empty beyond the _meta envelope
    body = {k: v for k, v in d.items() if k != "_meta"}
    if "products" in body:
        return bool(body["products"])
    if "lines" in body:
        return bool(body["lines"])
    return any(bool(v) for v in body.values())


def readiness(handle: str, base: Path = None) -> dict:
    """The Phase-1 gate: is this brand produce-ready from the form alone (no human hand-build)?"""
    prof = (base or B) / "clients" / handle / "profile"
    organs = {o: _organ_nonempty(prof / f"{o}.json") for o in PRODUCE_CRITICAL}
    return {"handle": handle, "organs": organs, "ready": all(organs.values()),
            "missing": [o for o, ok in organs.items() if not ok]}


def orchestrate(handle: str, form_path: str, harvest: bool = True, research: bool = True,
                base: Path = None) -> dict:
    report = {"handle": handle, "ts": time.strftime("%Y-%m-%d %H:%M"), "steps": []}
    form = json.loads(Path(form_path).read_text())
    form.setdefault("handle", handle)

    # 1) HARVEST — raw IG corpus (skippable; needs creds + a real handle)
    if harvest:
        try:
            r = subprocess.run([sys.executable, str(B / "scripts/client_intake.py"),
                                "--handle", handle, "--harvest-only"],
                               capture_output=True, text=True, timeout=600)
            report["steps"].append({"harvest": "ok" if r.returncode == 0 else f"rc={r.returncode}"})
        except Exception as e:
            report["steps"].append({"harvest": f"skipped: {type(e).__name__}"})

    # 2) RESEARCH — fill the research-derived organs (experimental; needs harvested corpus)
    if research:
        try:
            import research_fill_established as rfe
            rfe.fill(handle, quiet=True)
            report["steps"].append({"research": "ok"})
        except Exception as e:
            report["steps"].append({"research": f"skipped: {type(e).__name__}: {str(e)[:50]}"})

    # 3) FORM — the CONFIRMED organs from the client's own answers (the core of self-service)
    written = foi.fill_all_organs(form, base=base)
    report["steps"].append({"form_organs": list(written.keys())})

    # 4) VERIFY — the readiness gate
    report["readiness"] = readiness(handle, base=base)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--form", required=True)
    ap.add_argument("--no-harvest", action="store_true")
    ap.add_argument("--no-research", action="store_true")
    ap.add_argument("--base", default="")
    a = ap.parse_args()
    base = Path(a.base) if a.base else None
    rep = orchestrate(a.handle, a.form, harvest=not a.no_harvest, research=not a.no_research, base=base)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep["readiness"]["ready"]:
        print(f"\n✅ {a.handle} is produce-ready from the form — zero manual JSON.")
    else:
        print(f"\n⚠ {a.handle} missing organs: {rep['readiness']['missing']}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
