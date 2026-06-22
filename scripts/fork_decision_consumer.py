#!/usr/bin/env python3
"""Fork-decision CONSUMER — the reader that closes the h_fork_decision wire (June 22).

ROOT (RABIE's pick, this shift): h_fork_decision (apply_rulings.py) LANDS Mohamed's A/B
fork tap into data/mohamed_rulings_live.json["fork_decisions"], and its docstring claims
that file "is already CONSUMED ... next-shift backlog, so the write has a reader (Rule #6)".
That claim was a LIE: a grep proved only the WRITER (apply_rulings.py) and its test ever
referenced fork_decisions. Nothing read the decided fork to ROUTE it into the work queue.
So the instant Mohamed tapped B057c (rewire vs strip the orphaned brief-engine intel reads),
his choice would sit in the ledger and B057b — the dependent fix — would stay invisibly
gated forever. The exact severed-wire scar Rule #6 exists to kill.

THIS is the actuator the 2026-06-22T09:10 zoom-out named as "next-shift work". It is a
ROUTER, not a doer (Rule #11/#12): it reads each decided fork, finds the backlog step(s)
that declared `gated_on_fork: <card_id>`, and stamps the chosen direction onto the step
(`fork_resolved`) + clears the gate so the next RABIE pick sees it as actionable. It NEVER
executes the follow-on rewire/strip itself — the pair does that, by hand, per his recorded
direction.

Linkage is declared on the WORK side: a backlog step opts in with
    "gated_on_fork": "<fork card id in decision_queue.json>"
so a fork with no dependent step is surfaced (unconsumed_forks) rather than silently lost.

Idempotent: re-running with the same decision is a no-op. If Mohamed CHANGES his answer
(re-tap), the new direction overwrites the stamp and the step re-opens for the pair.

Zero-LLM, pure file I/O. CLI:
    python3 scripts/fork_decision_consumer.py            # consume + print summary
    python3 scripts/fork_decision_consumer.py --check    # report unconsumed forks, exit 1 if any
"""
import json
import sys
from pathlib import Path

B = Path(__file__).parent.parent


def _load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _decisions(base: Path) -> dict:
    r = _load(base / "data/mohamed_rulings_live.json") or {}
    fd = r.get("fork_decisions") or {}
    return fd if isinstance(fd, dict) else {}


def consume(base: Path = B) -> dict:
    """Route every decided fork onto its dependent backlog step(s).

    Returns {"routed": [...], "noop": [...], "unconsumed": [...]} where each routed entry
    is {fork, answer, choice, step}. Writes backlog.json only when something changed."""
    fd = _decisions(base)
    bl_p = base / "data/backlog.json"
    bl = _load(bl_p)
    if not bl or "steps" not in bl:
        raise RuntimeError("no data/backlog.json with steps — cannot route fork decisions")
    steps = bl["steps"]

    routed, noop, unconsumed = [], [], []
    changed = False
    decided_forks = set(fd)
    forks_with_step = set()

    for step in steps:
        gate = step.get("gated_on_fork")
        if not gate:
            continue
        if gate not in fd:
            continue  # step still legitimately waiting on his tap
        forks_with_step.add(gate)
        dec = fd[gate]
        ans = dec.get("answer")
        existing = step.get("fork_resolved") or {}
        record = {
            "fork": gate,
            "answer": ans,
            "choice": dec.get("choice", ""),
            "ruled_at": dec.get("ruled_at"),
        }
        if existing.get("answer") == ans:
            noop.append({"fork": gate, "answer": ans, "step": step.get("id")})
            continue
        # route: stamp the chosen direction. `gated_on_fork` stays as permanent provenance
        # (which fork this step came from); `fork_resolved` IS the actionable signal RABIE
        # reads — a step carrying it is no longer waiting on his tap.
        step["fork_resolved"] = record
        note = (f"fork {gate} resolved → «{ans}: {record['choice'][:50]}» "
                f"(consumed {dec.get('ruled_at','?')}); now actionable for the pair.")
        prev = step.get("progress", "")
        step["progress"] = (prev + " | " + note) if prev else note
        routed.append({**record, "step": step.get("id")})
        changed = True

    # a decided fork that no live step declared a gate on = a lost decision (Rule #6 alarm)
    for f in sorted(decided_forks - forks_with_step):
        unconsumed.append({"fork": f, "answer": fd[f].get("answer")})

    if changed:
        bl_p.write_text(json.dumps(bl, ensure_ascii=False, indent=1))
        # assert on disk (Rule #11)
        back = _load(bl_p)
        for r in routed:
            st = next((s for s in back["steps"] if s.get("id") == r["step"]), {})
            assert (st.get("fork_resolved") or {}).get("answer") == r["answer"], \
                f"fork route for {r['step']} not on disk"

    return {"routed": routed, "noop": noop, "unconsumed": unconsumed}


def unconsumed_forks(base: Path = B) -> list:
    """Decided forks with NO live backlog step gated on them — a landed-but-lost decision.
    Read-only (never writes backlog.json). Used by make_sure as a Rule #6 reader-side check:
    an unconsumed fork is a severed wire."""
    fd = _decisions(base)
    bl = _load(base / "data/backlog.json") or {"steps": []}
    gated = {s.get("fork_resolved", {}).get("fork") for s in bl["steps"]} | \
            {s.get("gated_on_fork") for s in bl["steps"]}
    return [{"fork": f, "answer": fd[f].get("answer")}
            for f in sorted(set(fd) - {g for g in gated if g})]


def main(argv):
    base = B
    if "--check" in argv:
        un = unconsumed_forks(base)
        if un:
            print(f"🔴 {len(un)} decided fork(s) with NO dependent step (landed-but-lost):")
            for u in un:
                print(f"   {u['fork']} → «{u['answer']}»")
            return 1
        print("✅ fork decisions: every decided fork is routed (no severed wire)")
        return 0
    res = consume(base)
    if res["routed"]:
        print(f"✅ routed {len(res['routed'])} fork decision(s) onto dependent step(s):")
        for r in res["routed"]:
            print(f"   {r['fork']} → «{r['answer']}: {r['choice'][:50]}» → {r['step']} (gate cleared)")
    if res["noop"]:
        print(f"   {len(res['noop'])} already-routed (no change)")
    if res["unconsumed"]:
        print(f"🔴 {len(res['unconsumed'])} decided fork(s) with no dependent step (lost):")
        for u in res["unconsumed"]:
            print(f"   {u['fork']} → «{u['answer']}»")
    if not (res["routed"] or res["noop"] or res["unconsumed"]):
        print("✅ no fork decisions pending (nothing tapped yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
