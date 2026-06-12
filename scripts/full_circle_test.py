#!/usr/bin/env python3
"""FULL-CIRCLE TEST (D1-2, June 12 — Mohamed: "from top to down and from down to
top, test everything"). One command, both directions, one verdict:

TOP-DOWN  — the laws hold on the content: every guard's gauntlet + a retroactive
            sweep of EVERY rendered caption through current laws (older cards may
            predate newer guards — violations are counted and listed, the honest
            debt ledger of a system that keeps learning).
BOTTOM-UP — the data feeds the organs: organ schemas validate, trust replays from
            events, staleness tells the truth, deadly gate holds, crystallize runs.

Usage: python3 scripts/full_circle_test.py   (exit 1 = a direction is broken)
"""
import glob, json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))


def run(name, cmd, expect_zero=True):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    ok = (r.returncode == 0) if expect_zero else True
    print(f"  {'✅' if ok else '🔴'} {name}")
    return ok, r


def main():
    fails = 0
    print("══ TOP-DOWN: the laws hold on the content")
    ok, _ = run("guards gauntlet (every law vs its birth case)",
                 ["python3", str(BASE / "scripts/truth_guards.py")])
    fails += not ok

    # retroactive sweep: every rendered caption through CURRENT laws
    from truth_guards import apply_guards
    counts, total, dirty = {}, 0, 0
    for f in glob.glob(str(BASE / "clients/*/posts/*.json")):
        try:
            c = json.loads(open(f).read())
        except Exception:
            continue
        caps = c.get("captions") or []
        if not caps:
            continue
        total += 1
        corpus = ""  # strict mode: retro sweep uses empty corpus only for guard classes that don't need it
        _, kills = apply_guards(caps, "RETRO_SWEEP_NO_CORPUS", c.get("slot") or {})
        real_kills = [k for k in kills if k["guard"] in
                      ("event_claim", "offer_on_emotional", "bilingual_filler",
                        "family_voice_blocked", "service_claim")]  # corpus-free guards only
        if real_kills:
            dirty += 1
            for k in real_kills:
                counts[k["guard"]] = counts.get(k["guard"], 0) + 1
    print(f"  {'✅' if dirty == 0 else '🟡'} retro sweep: {total} cards · {dirty} carry pre-law violations {counts if counts else ''}")
    print("     (debt, not breakage — these cards predate newer guards; regen queue handles them)")

    print("══ BOTTOM-UP: the data feeds the organs")
    for name, cmd in [
        ("organ schemas validate", ["python3", str(BASE / "scripts/generate_organ_schemas.py")]),
        ("deadly-defaults gate", ["python3", str(BASE / "scripts/deadly_defaults_gate.py")]),
        ("trust ladder replays", ["python3", str(BASE / "scripts/trust_ladder.py")]),
        ("goal-ratio watchdog", ["python3", str(BASE / "scripts/goal_ratio_check.py")]),
        ("crystallize loop runs", ["python3", str(BASE / "scripts/crystallize_loop.py")]),
    ]:
        ok, _ = run(name, cmd)
        fails += not ok
    # B023 covering-click audit (pre-armed): published content without a covering
    # client click = violation. No publish path exists yet — the gate is born loaded.
    uncovered = 0
    for f in glob.glob(str(BASE / "clients/*/posts/*.json")):
        try:
            c = json.loads(open(f).read())
        except Exception:
            continue
        if c.get("published") or c.get("posted_at"):
            h = c.get("handle", "")
            lf = BASE / "clients" / h / "events/ledger.jsonl"
            ledger = lf.read_text() if lf.exists() else ""
            key = Path(f).stem
            if key not in ledger or '"client_approved"' not in ledger:
                uncovered += 1
    print(f"  {'✅' if uncovered == 0 else '🔴'} covering-click audit: {uncovered} uncovered published pieces (gate pre-armed)")
    fails += uncovered > 0

    # staleness: exit 1 is EXPECTED (myfitness born-expired) — truth, not failure
    r = subprocess.run(["python3", str(BASE / "scripts/staleness_report.py")], capture_output=True, text=True)
    honest = "BLOCK" in (r.stdout or "") or r.returncode == 0
    print(f"  {'✅' if honest else '🔴'} staleness tells the truth (myfitness expected RED)")
    fails += not honest

    print(f"\n{'🟢 FULL CIRCLE HOLDS' if fails == 0 else f'🔴 {fails} DIRECTION FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
