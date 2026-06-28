#!/usr/bin/env python3
"""B291 — Rule#7 dead-end decision-card sweep (idempotent migration).

Two live OPEN buttons cards resolve to NO handler (apply_rulings._resolve == None) →
the instant Mohamed taps, his decision lands in mohamed_answers.jsonl with no actuator
and VANISHES (the exact Rule#7 scar). Both verified untapped (0 rows in mohamed_answers).

PART A  B157_veto_authority_rule  → rename id to B157_veto_authority_fork.
        Pure governance A/B → the `_fork` suffix auto-lands via h_fork_decision
        (records to mohamed_rulings_live.json[fork_decisions], surfaced as an
        unconsumed_fork for the pair's follow-on). Attribution is keyed by card id,
        so a rename ORPHANS it → attribute(new) + retire(old), append-only (the
        half-wire the gate_rescope rename hit 2026-06-28T21:55 and fixed the same way).

PART B  infra_session_leak_reap  → self-close on MACHINE EVIDENCE (Rule#10).
        Born 2026-06-23 at load 84 / 170 leaked sessions. NOW: com.abraham.reaper
        auto-runs every 300s + orchestra_self_terminate.py landed (the root fix) →
        leak 170→30, load 3.10. Nothing re-raises this card (grep: 0 pushers). A
        speculative h_infra_reap handler writing an unread infra_actions.jsonl would
        be a write-only organ (Rule#6 scar) — so we CLOSE, not build dead code. The
        B292 door-check is the safety net that forces proper wiring IF an infra card
        class is ever genuinely needed again. Uses the in-codebase self-close
        convention (make_sure_feedback.py:253-255: status=answered + answered_by=system).

Idempotent: re-running is a no-op (checks current state before each change).
"""
import json
import sys
from pathlib import Path

B = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(B / "scripts"))
import attribute as attr

# Every live A/B-style dead-end buttons card whose tap = a forward DIRECTION the pair
# executes later → rename to the `_fork` convention so h_fork_decision lands it.
# B157 was B291's named card; devs_integration_spec (THE connection-contract TOP) and
# myfitness_thin_reharvest were staged by system:orchestra LATER TONIGHT (23:21/23:30) —
# the live recurrence the B292 door-check will prevent. All verified untapped + no readers.
RENAMES = [
    ("B157_veto_authority_rule", "B157_veto_authority_fork",
     "his A/B veto-authority tap"),
    ("devs_integration_spec", "devs_integration_spec_fork",
     "his REST/package/queue connection-contract choice (THE TOP)"),
    ("myfitness_thin_reharvest", "myfitness_thin_reharvest_fork",
     "his reharvest/hold money decision on the thin myfitness pilot"),
]
INFRA_ID = "infra_session_leak_reap"
MACHINE_NOTE = ("machine-resolved (Rule#10): leak now machine-handled — com.abraham.reaper "
                "auto-runs every 300s + orchestra_self_terminate.py landed; leak 170→30 procs, "
                "load 3.10; nothing re-raises this card. Stale Jun-23 alarm, never tapped.")

qp = B / "data/decision_queue.json"
q = json.loads(qp.read_text())
items = q["items"]
by_id = {it["id"]: it for it in items}
changed = []

# ── PART A — rename every live A/B dead-end to the _fork convention ───────────
for OLD_ID, NEW_ID, what in RENAMES:
    if OLD_ID in by_id and NEW_ID not in by_id:
        card = by_id[OLD_ID]
        # attribute the new id, then retire the old (append-only, matches gate_rescope fix)
        if not attr.is_retired(f"card:{OLD_ID}"):
            attr.attribute(f"card:{NEW_ID}", "card", "claude",
                           via="scripts/queue_decision.py",
                           reason=(f"Rule#7 rename: {OLD_ID} -> _fork so {what} auto-lands "
                                   "via h_fork_decision (was a dead-end)"))
            attr.retire(f"card:{OLD_ID}",
                        reason=f"renamed to card:{NEW_ID} (Rule#7 _fork landing convention)")
        card["id"] = NEW_ID
        card["artifact_version"] = attr.latest_version(f"card:{NEW_ID}")
        changed.append(f"A: renamed {OLD_ID} -> {NEW_ID} (attr v{card['artifact_version']}, old retired)")
    elif NEW_ID in by_id:
        changed.append(f"A: already renamed ({NEW_ID} present) — no-op")
    else:
        changed.append(f"A: {OLD_ID} not found — no-op")

# ── PART B ──────────────────────────────────────────────────────────────────
if INFRA_ID in by_id and by_id[INFRA_ID].get("status") != "answered":
    c = by_id[INFRA_ID]
    c["status"] = "answered"
    c["answered"] = MACHINE_NOTE
    c["answered_by"] = "system:machine_evidence"
    changed.append(f"B: self-closed {INFRA_ID} on machine evidence")
elif INFRA_ID in by_id:
    changed.append(f"B: {INFRA_ID} already answered — no-op")
else:
    changed.append(f"B: {INFRA_ID} not found — no-op")

qp.write_text(json.dumps(q, ensure_ascii=False, indent=1))
for line in changed:
    print("  •", line)
print("✓ B291 migration applied")
