#!/usr/bin/env python3
"""Guards the HUMAN-VERDICT STARVATION detector (verified June 20, Rule #6).

THE SEVERANCE this detector exposes: Mohamed taps APPROVE / rating>=4 on the portal, but no consumer
turns a positive verdict into a HUMAN-confirmed client-ledger event — every ledger verdict is
rabie_provisional, so B082 writeback_replay and B084 writeback_moments (human-hands-only) replay
NOTHING. The loops read as "built" while make_sure stayed all-green. The detector makes the starvation
machine-visible. The contracts that must never break:
  1. starved=True ONLY when there IS positive input AND none of it landed as a human-confirmed verdict
     — never merely "no taps yet" (no input ⇒ not starved, just idle).
  2. rabie_provisional ledger verdicts do NOT count as fed (they never move trust).
  3. one human-confirmed verdict auto-closes the signal (starved=False).
Fixture-driven so no live ledger/answers state is touched."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import intel_consumer_health as ich


def _write_jsonl(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def _ledger(root: Path, handle: str, events):
    _write_jsonl(root / handle / "events" / "ledger.jsonl", events)


class TestHumanVerdictStarvation(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.answers = self.root / "mohamed_answers.jsonl"
        self.clients = self.root / "clients"
        self.pilots = ("eatjurisha",)

    def tearDown(self):
        self._td.cleanup()

    def _starv(self):
        return ich.human_verdict_starvation(self.answers, self.clients, self.pilots)

    def test_judge2_approvals_with_only_provisional_ledger_is_starved(self):
        """His judge2 YESes exist, every ledger verdict is rabie_provisional → STARVED (the real bug)."""
        _write_jsonl(self.answers, [
            {"judge": "mohamed", "item_id": "judge2_eatjurisha_2026-11-27", "answer": "approved"},
            {"judge": "mohamed", "item_id": "judge2_eatjurisha_2027-05-16", "answer": "approved", "rating": 5},
        ])
        _ledger(self.clients, "eatjurisha", [
            {"ts": "2026-06-19", "type": "batch_rating", "confirmer": "rabie_provisional", "stamp": "P"},
        ])
        s = self._starv()
        self.assertEqual(s["judge2_positive"], 2)
        self.assertEqual(s["judge2_human_confirmed_ledger"], 0)  # provisional never counts
        self.assertTrue(s["starved"])

    def test_unrelated_pick_lane_does_NOT_greenwash(self):
        """THE RABIE CATCH: the pairwise PICK lane (pick_selected, mohamed) is fed, but that must NOT
        clear the judge2-lane starvation — a fed lane can't hide a severed lane (lane-aware contract)."""
        _write_jsonl(self.answers, [
            {"judge": "mohamed", "item_id": "judge2_albaik_2027-06-29", "answer": "approved", "rating": 5},
        ])
        _ledger(self.clients, "eatjurisha", [
            {"ts": "2026-06-15", "type": "pick_selected", "confirmer": "mohamed", "stamp": "C",
             "subject": "2027-02-08__ramadan → authenticity"},
        ])
        s = self._starv()
        self.assertEqual(s["human_confirmed_ledger_verdicts"], 1)   # pick lane IS fed (context)
        self.assertEqual(s["judge2_human_confirmed_ledger"], 0)     # judge2 lane is NOT
        self.assertTrue(s["starved"])                               # still starved — no green-wash

    def test_no_judge2_taps_is_not_starved_only_idle(self):
        """No positive judge2 input ⇒ NOT starved (never cry wire-break on an empty queue)."""
        _write_jsonl(self.answers, [
            {"judge": "mohamed", "item_id": "judge2_x", "answer": "rejected", "rating": 2},
        ])
        _ledger(self.clients, "eatjurisha", [])
        s = self._starv()
        self.assertEqual(s["judge2_positive"], 0)
        self.assertFalse(s["starved"])

    def test_one_judge2_human_confirmed_event_auto_closes(self):
        """One mohamed-confirmed client_approved on the ledger ⇒ starved=False (the wire is feeding)."""
        _write_jsonl(self.answers, [
            {"judge": "mohamed", "item_id": "judge2_eatjurisha_2026-11-27", "answer": "approved", "rating": 4},
        ])
        _ledger(self.clients, "eatjurisha", [
            {"ts": "2026-06-20", "type": "client_approved", "confirmer": "mohamed", "stamp": "C"},
        ])
        s = self._starv()
        self.assertEqual(s["judge2_human_confirmed_ledger"], 1)
        self.assertFalse(s["starved"])

    def test_missing_files_never_crash(self):
        """Detectors must be crash-proof on absent state (no answers file, no ledgers)."""
        s = self._starv()  # nothing written
        self.assertEqual(s["judge2_positive"], 0)
        self.assertEqual(s["judge2_human_confirmed_ledger"], 0)
        self.assertFalse(s["starved"])

    def test_torn_jsonl_line_is_skipped_not_fatal(self):
        """A half-written last line is tolerated (never crash the heartbeat)."""
        self.answers.write_text(
            json.dumps({"judge": "mohamed", "item_id": "judge2_albaik_2027-05-13", "answer": "approved"})
            + "\n{bad json\n", encoding="utf-8")
        _ledger(self.clients, "eatjurisha", [])
        s = self._starv()
        self.assertEqual(s["judge2_positive"], 1)
        self.assertTrue(s["starved"])


if __name__ == "__main__":
    unittest.main()
