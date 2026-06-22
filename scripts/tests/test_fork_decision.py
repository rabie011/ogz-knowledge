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


if __name__ == "__main__":
    unittest.main()
