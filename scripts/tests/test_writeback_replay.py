#!/usr/bin/env python3
"""B082 — writeback_replay synthetic tests. Pure-core (derive) only: no IO, no clock,
fully deterministic. Proves the four properties RABIE demanded:
  - truth_confirmed promotes a candidate's provenance AND lifts it to `confirmed`
  - a known founder-kill reason_code propagates to client taste.kills
  - it NEVER invents a kill (unknown reason_code is ignored)
  - provisional / machine verdicts move NOTHING (human hands only)
  - IDEMPOTENT: a second derive() over the same events makes zero further changes
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import writeback_replay  # noqa: E402
from writeback_replay import derive  # noqa: E402

FOUNDER_KILLS = {"weak_tail", "not_saudi", "very_normal"}


def _tp():
    return {
        "confirmed": [],
        "product_candidates": [
            {"name": "جريش", "provenance": {"confidence": "candidate"}},
            {"name": "رز كابلي", "provenance": {"confidence": "candidate"}},
        ],
    }


def _taste():
    return {"kills": ["generic_celebration_template"]}


class TestTruthPromotion(unittest.TestCase):
    def test_truth_confirmed_promotes_and_confirms(self):
        events = [{"type": "truth_confirmed", "subject": "جريش",
                   "confirmer": "mohamed", "stamp": "CONFIRMED BY MOHAMED"}]
        tp, _, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        cand = next(c for c in tp["product_candidates"] if c["name"] == "جريش")
        self.assertEqual(cand["provenance"]["confidence"], "confirmed")
        self.assertIn("جريش", {c["name"] for c in tp["confirmed"]})
        kinds = {c["kind"] for c in ch}
        self.assertEqual(kinds, {"provenance_promoted", "truth_confirmed"})

    def test_untouched_candidate_stays_candidate(self):
        events = [{"type": "truth_confirmed", "subject": "جريش", "confirmer": "mohamed"}]
        tp, _, _ = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        other = next(c for c in tp["product_candidates"] if c["name"] == "رز كابلي")
        self.assertEqual(other["provenance"]["confidence"], "candidate")


class TestTasteKills(unittest.TestCase):
    def test_known_kill_propagates(self):
        events = [{"type": "batch_rating", "reason_code": "weak_tail",
                   "confirmer": "mohamed", "rating": 2}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        self.assertIn("weak_tail", taste["kills"])
        self.assertEqual([c["kind"] for c in ch], ["kill_propagated"])

    def test_unknown_kill_never_invented(self):
        events = [{"type": "batch_rating", "reason_code": "i_just_dont_like_it",
                   "confirmer": "mohamed"}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        self.assertNotIn("i_just_dont_like_it", taste["kills"])
        self.assertEqual(ch, [])

    def test_existing_kill_not_duplicated(self):
        events = [{"type": "batch_rating", "reason_code": "generic_celebration_template",
                   "confirmer": "mohamed"}]
        _, taste, ch = derive(events, _tp(), _taste(),
                              FOUNDER_KILLS | {"generic_celebration_template"})
        self.assertEqual(taste["kills"].count("generic_celebration_template"), 1)
        self.assertEqual(ch, [])


class TestHumanHandsOnly(unittest.TestCase):
    def test_provisional_moves_nothing(self):
        events = [
            {"type": "truth_confirmed", "subject": "جريش",
             "confirmer": "rabie_provisional", "stamp": "PROVISIONAL — pending Mohamed"},
            {"type": "batch_rating", "reason_code": "weak_tail",
             "confirmer": "rabie_provisional", "stamp": "PROVISIONAL"},
        ]
        tp, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        self.assertEqual(ch, [])
        self.assertEqual(tp["confirmed"], [])
        self.assertNotIn("weak_tail", taste["kills"])


class TestIdempotency(unittest.TestCase):
    def test_second_pass_is_a_noop(self):
        events = [
            {"type": "truth_confirmed", "subject": "جريش", "confirmer": "mohamed"},
            {"type": "compare_verdict", "reason_code": "not_saudi", "confirmer": "mohamed"},
        ]
        tp1, taste1, ch1 = derive(events, _tp(), _taste(), FOUNDER_KILLS)
        self.assertTrue(ch1)                      # first pass changes things
        tp2, taste2, ch2 = derive(events, tp1, taste1, FOUNDER_KILLS)
        self.assertEqual(ch2, [])                 # second pass: nothing left to do
        self.assertEqual(tp2, tp1)
        self.assertEqual(taste2, taste1)


class TestReplayClientIO(unittest.TestCase):
    """End-to-end on disk: real write_organ + writeback.jsonl + dedup, idempotent twice."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self._orig_base = writeback_replay.BASE
        writeback_replay.BASE = base
        # founder vocab (needed by _founder_kill_vocab)
        (base / "data").mkdir(parents=True)
        (base / "data/founder_taste.json").write_text(json.dumps(
            {"kills": [{"name": "weak_tail"}, {"name": "not_saudi"}]}))
        # organ_write is imported lazily inside replay_client; it uses its own BASE only
        # for nothing we touch here (it writes to the absolute paths we pass), so it's fine.
        pdir = base / "clients/acme/profile"
        pdir.mkdir(parents=True)
        (pdir / "truth_pack.json").write_text(json.dumps(
            {"confirmed": [], "product_candidates": [
                {"name": "X", "provenance": {"confidence": "candidate"}}]}))
        (pdir / "taste.json").write_text(json.dumps({"kills": []}))
        ledger = base / "clients/acme/events/ledger.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(
            json.dumps({"type": "truth_confirmed", "subject": "X", "confirmer": "mohamed"}) + "\n"
            + json.dumps({"type": "batch_rating", "reason_code": "weak_tail",
                          "confirmer": "mohamed"}) + "\n")

    def tearDown(self):
        writeback_replay.BASE = self._orig_base
        self.tmp.cleanup()

    def test_writes_then_idempotent(self):
        base = writeback_replay.BASE
        r1 = writeback_replay.replay_client("acme")
        self.assertTrue(r1["wrote"])
        self.assertEqual(r1["events_appended"], 3)   # promoted + confirmed + kill
        tp = json.loads((base / "clients/acme/profile/truth_pack.json").read_text())
        self.assertEqual(tp["product_candidates"][0]["provenance"]["confidence"], "confirmed")
        taste = json.loads((base / "clients/acme/profile/taste.json").read_text())
        self.assertIn("weak_tail", taste["kills"])

        # second run: organs already derived → no new changes, no duplicate events
        r2 = writeback_replay.replay_client("acme")
        self.assertEqual(r2["changes"], [])
        wb = (base / "clients/acme/events/writeback.jsonl").read_text().splitlines()
        self.assertEqual(len(wb), 3)                  # not 6 — deduped


if __name__ == "__main__":
    unittest.main()
