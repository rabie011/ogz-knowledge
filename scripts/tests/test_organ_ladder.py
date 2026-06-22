#!/usr/bin/env python3
"""Tests for the ORGAN LADDER mechanics (B087) — promotion/demotion as replay.

Seeded event lists only: no live client ledger is read (events are injected via
the `events=` arg), so the invariants are pinned against synthetic streams. The
laws under test:
  - a real human (mohamed/client) organ event → confirmed
  - rabie_provisional never reaches confirmed; ≥3 evidences → inferred
  - a contradiction (breach reason_code) INSTANTLY demotes (counter reset)
  - a fresh clean evidence after a contradiction clears it
  - pending_moves only surfaces a delta vs the current fingerprint rung
"""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import organ_ladder as ol  # noqa: E402


def ev(t, confirmer="rabie_provisional", rc=None):
    e = {"ts": "2026-06-22", "type": t, "confirmer": confirmer, "stamp": "x"}
    if rc is not None:
        e["reason_code"] = rc
    return e


class TestEarnedRungs(unittest.TestCase):
    def test_human_word_confirms(self):
        r = ol.earned_rungs("x", [ev("red_line_added", confirmer="mohamed")])
        self.assertEqual(r["RED LINES"]["rung"], "confirmed")
        self.assertEqual(r["RED LINES"]["human"], 1)

    def test_client_confirmer_also_confirms(self):
        r = ol.earned_rungs("x", [ev("goal_declared", confirmer="client")])
        self.assertEqual(r["GOALS"]["rung"], "confirmed")

    def test_provisional_never_confirms_but_reaches_inferred(self):
        # 3 provisional voice ratings → inferred, never confirmed
        r = ol.earned_rungs("x", [ev("voice_rating")] * 3)
        self.assertEqual(r["VOICE"]["rung"], "inferred")
        self.assertEqual(r["VOICE"]["human"], 0)

    def test_one_provisional_is_default(self):
        r = ol.earned_rungs("x", [ev("voice_rating")])
        self.assertEqual(r["VOICE"]["rung"], "default")

    def test_two_provisional_still_default(self):
        r = ol.earned_rungs("x", [ev("voice_rating")] * 2)
        self.assertEqual(r["VOICE"]["rung"], "default")

    def test_contradiction_instantly_demotes(self):
        # two clean, then a breach → reset to default, contradicted flagged
        stream = [ev("voice_rating"), ev("voice_rating"), ev("voice_rating", rc="factual_error")]
        r = ol.earned_rungs("x", stream)
        self.assertEqual(r["VOICE"]["rung"], "default")
        self.assertTrue(r["VOICE"]["contradicted"])
        self.assertEqual(r["VOICE"]["evidence"], 0)
        self.assertEqual(r["VOICE"]["reason"], "factual_error")

    def test_contradiction_drops_a_prior_human_confirm(self):
        # human confirm then a later breach → no longer confirmed (instant demote)
        stream = [ev("voice_rating", confirmer="mohamed"), ev("voice_rating", rc="off_voice")]
        r = ol.earned_rungs("x", stream)
        self.assertEqual(r["VOICE"]["rung"], "default")
        self.assertTrue(r["VOICE"]["contradicted"])

    def test_clean_evidence_after_contradiction_clears_it(self):
        stream = [ev("voice_rating", rc="too_generic"), ev("voice_rating", confirmer="mohamed")]
        r = ol.earned_rungs("x", stream)
        self.assertFalse(r["VOICE"]["contradicted"])
        self.assertEqual(r["VOICE"]["rung"], "confirmed")

    def test_unmapped_event_is_ignored(self):
        # occasion_gold / intake_answer / client_approved carry no fingerprint row
        r = ol.earned_rungs("x", [ev("occasion_gold", confirmer="mohamed"),
                                   ev("client_approved", confirmer="mohamed"),
                                   ev("intake_answer", confirmer="mohamed")])
        self.assertEqual(r, {})

    def test_payment_events_map_to_payment_organ(self):
        r = ol.earned_rungs("x", [ev("payment_received", confirmer="client")])
        self.assertEqual(r["PAYMENT"]["rung"], "confirmed")


class TestPendingMoves(unittest.TestCase):
    def _patch_current(self, rungs):
        light = {"confirmed": ol.G, "inferred": ol.Y, "default": ol.R}
        rows = [(organ, light[r], "") for organ, r in rungs.items()]
        return lambda h: {"rows": rows}

    def test_promote_surfaced_when_file_lags_evidence(self):
        orig = ol.status
        ol.status = self._patch_current({"RED LINES": "default"})
        try:
            moves = ol.pending_moves("x", [ev("red_line_added", confirmer="mohamed")])
        finally:
            ol.status = orig
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0]["organ"], "RED LINES")
        self.assertEqual(moves[0]["direction"], "promote")
        self.assertEqual((moves[0]["current"], moves[0]["earned"]), ("default", "confirmed"))

    def test_equal_rung_not_surfaced(self):
        orig = ol.status
        ol.status = self._patch_current({"VOICE": "inferred"})
        try:
            moves = ol.pending_moves("x", [ev("voice_rating")] * 3)
        finally:
            ol.status = orig
        self.assertEqual(moves, [])

    def test_demote_surfaced_on_contradiction(self):
        orig = ol.status
        ol.status = self._patch_current({"VOICE": "confirmed"})
        try:
            moves = ol.pending_moves("x", [ev("voice_rating", confirmer="mohamed"),
                                            ev("voice_rating", rc="culture_breach")])
        finally:
            ol.status = orig
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0]["direction"], "demote")
        self.assertTrue(moves[0]["contradicted"])


class TestLiveSmoke(unittest.TestCase):
    """The engine must run clean on the real pilots (no crash, sane shape)."""

    def test_runs_on_live_pilots(self):
        for h in ("albaik", "eatjurisha", "myfitness.sa"):
            if not (ol.BASE / "clients" / h / "events" / "ledger.jsonl").exists():
                continue
            earned = ol.earned_rungs(h)
            for organ, d in earned.items():
                self.assertIn(d["rung"], ("confirmed", "inferred", "default"))
                self.assertIn(organ, set(ol.ORGAN_EVENTS.values()))
            self.assertIsInstance(ol.pending_moves(h), list)


if __name__ == "__main__":
    unittest.main()
