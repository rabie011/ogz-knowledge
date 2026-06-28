#!/usr/bin/env python3
"""`*_fork` decision-card handler tests (June 22, RABIE's pick).

ROOT: two decision forks were live on Mohamed's portal — B057c_thinbrain_primary_fork
(rewire vs strip the orphaned brief-engine intel reads) and B095t_publish_trigger_fork
(our side vs Hesham's platform) — with NO handler. The instant he tapped either, his A/B
choice would trip a red `pending_unhandled` alarm and fail to land (Rule #7: never put a
card on his phone whose answer has nowhere to land). h_fork_decision is the generic
landing — every present + future `*_fork` card resolves to it, no per-fork wiring.

These tests prove END-TO-END:
  - 'A' / 'B' land the confirmed choice (+ its label) in mohamed_rulings_live.json
  - the answer is validated against the card's OWN declared options (Rule #8: an
    undeclared answer is REFUSED, never silently stored)
  - a fork card missing from the queue raises (no guessing)
  - the (item_id, answer) pair resolves to the handler via apply_rulings dispatch, so
    pending_unhandled now sees a handler (the red alarm is pre-empted)
  - it does NOT execute follow-on work — only the decision record is written (Rule #11/#12)
  - the landing is consumer-readable: a second fork coexists, neither clobbers the other
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import apply_rulings  # noqa: E402

B057C = "B057c_thinbrain_primary_fork"
B095T = "B095t_publish_trigger_fork"

QUEUE = {
    "items": [
        {"id": B057C, "kind": "buttons", "status": "open",
         "title": "Brief engine's PRIMARY block went empty — rewire or strip?",
         "options": [
             {"v": "A", "label": "🔌 Rewire the manual brief engine to new keys"},
             {"v": "B", "label": "🗑️ Strip dead reads + guard (produce_batch superseded it)"},
         ]},
        {"id": B095T, "kind": "buttons", "status": "open",
         "title": "Where does 'a piece went live' get confirmed?",
         "options": [
             {"v": "A", "label": "🖐️ Our side — I tap 'published'"},
             {"v": "B", "label": "🔗 Hesham's platform feeds it"},
         ]},
    ]
}


def _sandbox(d, queue=None):
    tmp = Path(d)
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    (tmp / "data" / "decision_queue.json").write_text(
        json.dumps(queue if queue is not None else QUEUE, ensure_ascii=False))
    return tmp


def _rulings(tmp):
    p = tmp / "data" / "mohamed_rulings_live.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


class TestLands(unittest.TestCase):
    def test_answer_A_lands_with_label(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            msg = apply_rulings.h_fork_decision(
                tmp, {"item_id": B057C, "answer": "A", "ts": "2026-06-22T09:00"})
            fd = _rulings(tmp)["fork_decisions"][B057C]
            self.assertEqual(fd["answer"], "A")
            self.assertIn("Rewire", fd["choice"])
            self.assertEqual(fd["confirmer"], "mohamed")
            self.assertEqual(fd["source"], f"portal:{B057C}")
            self.assertIn("landed", msg)

    def test_answer_B_lands(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            apply_rulings.h_fork_decision(
                tmp, {"item_id": B057C, "answer": "B", "ts": "2026-06-22T09:00"})
            fd = _rulings(tmp)["fork_decisions"][B057C]
            self.assertEqual(fd["answer"], "B")
            self.assertIn("Strip", fd["choice"])

    def test_two_forks_coexist(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            apply_rulings.h_fork_decision(tmp, {"item_id": B057C, "answer": "A", "ts": "t"})
            apply_rulings.h_fork_decision(tmp, {"item_id": B095T, "answer": "A", "ts": "t"})
            fds = _rulings(tmp)["fork_decisions"]
            self.assertEqual(set(fds), {B057C, B095T})
            self.assertEqual(fds[B057C]["answer"], "A")
            self.assertEqual(fds[B095T]["answer"], "A")


class TestRefuses(unittest.TestCase):
    def test_undeclared_answer_raises(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            with self.assertRaises(RuntimeError):
                apply_rulings.h_fork_decision(
                    tmp, {"item_id": B057C, "answer": "C", "ts": "t"})
            # nothing written on refusal
            self.assertNotIn("fork_decisions", _rulings(tmp))

    def test_unknown_card_raises(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            with self.assertRaises(RuntimeError):
                apply_rulings.h_fork_decision(
                    tmp, {"item_id": "B999z_made_up_fork", "answer": "A", "ts": "t"})


class TestDispatch(unittest.TestCase):
    def test_fork_suffix_resolves_to_handler(self):
        # any *_fork id, any answer → the generic handler (pre-empts pending_unhandled red)
        for ans in ("A", "B"):
            self.assertIs(apply_rulings._resolve((B057C, ans)),
                          apply_rulings.h_fork_decision)
            self.assertIs(apply_rulings._resolve((B095T, ans)),
                          apply_rulings.h_fork_decision)

    def test_non_fork_unaffected(self):
        self.assertIsNone(apply_rulings._resolve(("some_random_card", "A")))


# A *system* rescope decision (card_hygiene + issue_pulse → machine-defects only) is also a
# fork. The June 28 shift staged it as `gate_rescope_founder_away` (NO _fork suffix) → it
# resolved to None → his A/B rescope ruling would have vanished (Rule #7 dead-end, the exact
# scar this handler exists to close). Renamed to `..._fork` so it auto-lands. This guards the
# rename + proves the rescope DECISION is recorded WITHOUT pre-executing the gate redefinition
# (that is B289's dependent step, his ruling first — Rule #11/#12).
GATE_RESCOPE = "gate_rescope_founder_away_fork"
RESCOPE_QUEUE = {
    "items": [
        {"id": GATE_RESCOPE, "kind": "buttons", "status": "open",
         "title": "Health-gate rescope — 2 reds are founder-away, not defects",
         "options": [
             {"v": "A", "label": "✅ A — rescope (recommended)"},
             {"v": "B", "label": "⏸️ B — keep biting as honest debt"},
         ]},
    ]
}


class TestGateRescopeFork(unittest.TestCase):
    def test_rescope_card_resolves_to_handler(self):
        for ans in ("A", "B"):
            self.assertIs(apply_rulings._resolve((GATE_RESCOPE, ans)),
                          apply_rulings.h_fork_decision)

    def test_rescope_A_lands_without_executing(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, queue=RESCOPE_QUEUE)
            apply_rulings.h_fork_decision(
                tmp, {"item_id": GATE_RESCOPE, "answer": "A", "ts": "2026-06-28T21:45"})
            fd = _rulings(tmp)["fork_decisions"][GATE_RESCOPE]
            self.assertEqual(fd["answer"], "A")
            self.assertIn("rescope", fd["choice"])
            self.assertEqual(fd["confirmer"], "mohamed")
            # the DECISION is recorded; the gate redefinition itself is NOT executed here
            self.assertEqual(set(_rulings(tmp)), {"fork_decisions"})


# B291 — the Rule#7 dead-end SWEEP. The prior shift fixed gate_rescope (above) but left two
# siblings (B157_veto_authority_rule + infra_session_leak_reap), and two MORE A/B-direction
# cards were staged dead-end by system:orchestra later the same night (devs_integration_spec —
# THE connection-contract TOP — + myfitness_thin_reharvest). Every one was a card on his phone
# whose tap had nowhere to land. The three forward-DIRECTION cards were renamed to `_fork`
# (auto-land via h_fork_decision; the pair executes his recorded direction — Rule #11/#12);
# the stale infra alarm self-closed on machine evidence (Rule #10). These guard the renames.
B291_FORKS = (
    ("B157_veto_authority_fork", "any_veto"),
    ("devs_integration_spec_fork", "rest"),
    ("myfitness_thin_reharvest_fork", "reharvest"),
)


class TestB291DeadEndSweep(unittest.TestCase):
    def test_renamed_forks_resolve_to_handler(self):
        for cid, ans in B291_FORKS:
            self.assertIs(apply_rulings._resolve((cid, ans)),
                          apply_rulings.h_fork_decision, f"{cid} must auto-land")

    def test_devs_contract_fork_lands_the_choice(self):
        # the most important card: how the dev platform calls the brain (THE TOP)
        queue = {"items": [{"id": "devs_integration_spec_fork", "kind": "buttons", "status": "open",
                            "title": "How will the dev platform CALL the brain?",
                            "options": [{"v": "rest", "label": "REST service (we host)"},
                                        {"v": "package", "label": "Python package (they import)"},
                                        {"v": "queue", "label": "Job queue (they drop tasks)"},
                                        {"v": "other", "label": "Other — I'll explain"}]}]}
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, queue=queue)
            apply_rulings.h_fork_decision(
                tmp, {"item_id": "devs_integration_spec_fork", "answer": "rest", "ts": "2026-06-28T23:45"})
            fd = _rulings(tmp)["fork_decisions"]["devs_integration_spec_fork"]
            self.assertEqual(fd["answer"], "rest")
            self.assertEqual(fd["confirmer"], "mohamed")
            # decision recorded only — no follow-on executed (Rule #11/#12)
            self.assertEqual(set(_rulings(tmp)), {"fork_decisions"})

    def test_live_queue_has_no_open_AB_dead_ends(self):
        # the SWEEP invariant: no live open buttons card (outside the judge lanes + the
        # closures/reopen_one note-path, which B292 owns) may have an unresolvable option.
        b = Path(__file__).parent.parent.parent
        q = json.loads((b / "data" / "decision_queue.json").read_text())["items"]
        dead = []
        for it in q:
            if it.get("status") == "answered" or it.get("kind") != "buttons":
                continue
            iid = it["id"]
            if iid.startswith(("judge_", "judge2_", "ratify_", "closures_")):
                continue
            for o in it.get("options", []):
                v = o.get("v", "")
                if v in apply_rulings.ACK_ANSWERS:
                    continue
                if apply_rulings._resolve((iid, v)) is None:
                    dead.append((iid, v))
        self.assertEqual(dead, [], f"live A/B dead-end cards remain: {dead}")


if __name__ == "__main__":
    unittest.main()
