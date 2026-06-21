#!/usr/bin/env python3
"""Guards the judge-loop verifier + the F1/F2/F3 wiring it asserts (June 21).

The verifier is the $0 gate that proves the moat's feedback circuit is wired end-to-end and BITES
(exit non-zero) on any severed wire. These tests lock its two non-negotiable behaviours:
  1. On the REAL repo it is ALL-GREEN and exits 0 (the loop is closed, taste SHADOW + honest).
  2. It actually BITES — when a wire is severed or the gate fires on an unvalidated model, the named
     RED appears and main() exits 1 (Rule #8). A gate that only ever passes is worse than none.
Plus the F1 refuse-don't-warn contract (consume refuses a corrupt line; the typed pref contract) and
the F2 honesty contract (no simulation number is ever labelled live)."""
import io
import contextlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import verify_judge_loop as v
import pairwise as pw
import taste_rank as tr


class TestVerifierAllGreenOnRealRepo(unittest.TestCase):
    def test_real_repo_loop_is_closed(self):
        """The whole loop must be intact on disk right now — zero reds, exit 0."""
        # fresh state per run (the module accumulates into globals)
        v.REDS.clear(); v.GREENS.clear()
        reds, greens = v.run()
        self.assertEqual(reds, [], f"the judge loop is severed: {reds}")
        self.assertTrue(greens, "no wires were even checked")

    def test_main_exits_zero_when_intact(self):
        v.REDS.clear(); v.GREENS.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                v.main()
        self.assertEqual(cm.exception.code, 0)


class TestVerifierBites(unittest.TestCase):
    """A gate that never fails is theatre. Prove each guard reds when its wire is cut."""

    def setUp(self):
        v.REDS.clear(); v.GREENS.clear()

    def test_w5_reds_when_taste_elo_missing(self):
        saved = v.TASTE_ELO
        try:
            v.TASTE_ELO = Path("/tmp/__no_such_taste_elo__.json")
            t = v.w5_taste_elo()
        finally:
            v.TASTE_ELO = saved
        self.assertIsNone(t)
        self.assertTrue(any(w == "W5" for w, _ in v.REDS))

    def test_w6_reds_on_sim_labelled_live(self):
        """The exact forbidden state: a degenerate (sim) number with live_validated true."""
        v.w6_honest_elo({"held_out_agreement_degenerate": True, "live_validated": True})
        self.assertTrue(any(w == "W6" for w, _ in v.REDS))

    def test_w6_reds_on_fabricated_live_pct(self):
        v.w6_honest_elo({"held_out_live_n_testable": 0, "held_out_live_pct": 88,
                         "held_out_agreement_degenerate": True})
        self.assertTrue(any(w == "W6" for w, _ in v.REDS))

    def test_w9_reds_when_gate_fires_unvalidated(self):
        saved = tr.gate_status
        try:
            tr.gate_status = lambda t=None: {"wire_live": True, "reason": "forced"}
            v.w9_gate_honest(tr, {"held_out_agreement_degenerate": True, "live_validated": False,
                                  "held_out_live_n_testable": 0, "held_out_live_pct": None})
        finally:
            tr.gate_status = saved
        self.assertTrue(any(w == "W9" for w, _ in v.REDS),
                        "gate fired on an unvalidated model but the verifier stayed green (Rule #9)")

    def test_main_exits_one_on_severed_wire(self):
        saved = v.TASTE_ELO
        try:
            v.TASTE_ELO = Path("/tmp/__no_such_taste_elo__.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    v.main()
        finally:
            v.TASTE_ELO = saved
        self.assertEqual(cm.exception.code, 1)


class TestF1ConsumeContract(unittest.TestCase):
    """F1: refuse-don't-warn + the typed pref contract."""

    def test_valid_pref_contract(self):
        ok = {"pair_id": "pw_1", "handle": "h", "winner": "a",
              "winner_caption": "A", "loser_caption": "B"}
        self.assertTrue(pw.valid_pref(ok))
        self.assertFalse(pw.valid_pref({**ok, "winner": "c"}))      # bad winner
        self.assertFalse(pw.valid_pref({**ok, "loser_caption": "A"}))  # identical captions
        self.assertFalse(pw.valid_pref({k: ok[k] for k in list(ok)[:-1]}))  # missing field
        self.assertFalse(pw.valid_pref("not a dict"))

    def test_read_answers_refuses_corrupt_line(self):
        saved = pw.ANSWERS
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
                f.write('{"item_id":"pw_1","answer":"a"}\nNOT-JSON\n')
                tmp = f.name
            pw.ANSWERS = Path(tmp)
            with self.assertRaises(pw.ConsumeError):
                pw._read_answers_strict()
        finally:
            pw.ANSWERS = saved
            Path(tmp).unlink(missing_ok=True)

    def test_read_answers_tolerates_blank_lines(self):
        saved = pw.ANSWERS
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
                f.write('{"item_id":"pw_1","answer":"a"}\n\n')
                tmp = f.name
            pw.ANSWERS = Path(tmp)
            rows = pw._read_answers_strict()
            self.assertEqual(len(rows), 1)
        finally:
            pw.ANSWERS = saved
            Path(tmp).unlink(missing_ok=True)

    def test_consume_verdicts_routes_both_wires(self):
        import inspect
        src = inspect.getsource(pw.consume_verdicts)
        self.assertIn("gold_mint", src)
        self.assertIn("judge2_ledger_writer", src)


class TestF2HonestElo(unittest.TestCase):
    """F2: the real taste_elo.json never labels a simulation number as his live eye."""

    def test_real_taste_elo_is_honest(self):
        import json
        t = json.loads((Path(__file__).parent.parent.parent / "data/taste_elo.json").read_text())
        # if the live eye is untested, live_validated must be False and live_pct must be None
        if (t.get("held_out_live_n_testable", 0) or 0) == 0:
            self.assertFalse(t.get("live_validated"))
            self.assertIsNone(t.get("held_out_live_pct"))
        # the mixed number is always flagged as simulation
        self.assertTrue(t.get("held_out_agreement_is_simulation"))


if __name__ == "__main__":
    unittest.main()
