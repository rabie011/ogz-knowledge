#!/usr/bin/env python3
"""Guards the QUARTERLY PRIOR CARDS GENERATOR (B099). All on synthetic fixtures (no live data):
(1) Rule #11 — at most 5 cards, strongest first; (2) Rule #10 — overflow carried, not dropped;
(3) Rule #7 — every button value has a consumer; an unhandled value is REFUSED; (4) Rule #12 —
approve_prior records 'awaiting_pr' and NEVER applies; (5) Rule #6 — staged batch reads back end-to-
end; (6) Rule #9 — 0 drafts → 0 cards (HOLD, not a crash); (7) quarter_key is correct + idempotent."""
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import quarterly_prior_cards as qpc


def _draft(sector, field, value, n):
    return {"sector": sector, "field": field, "value": value, "n_brands": n,
            "target_sector_default": f"05_sector_defaults/{sector}.yaml"}


class TestQuarterlyPriorCards(unittest.TestCase):
    def test_cap_at_five_strongest_first(self):
        drafts = [_draft("f_and_b", f"field_{i}", "v", n) for i, n in enumerate([3, 9, 4, 7, 5, 6, 8])]
        cards, dropped = qpc.build_cards(drafts)
        self.assertEqual(len(cards), 5)                         # Rule #11
        ns = [c["source_draft"]["n_brands"] for c in cards]
        self.assertEqual(ns, sorted(ns, reverse=True))          # strongest first
        self.assertEqual(ns, [9, 8, 7, 6, 5])
        self.assertEqual(len(dropped), 2)                       # Rule #10 — carried, not vanished
        self.assertEqual({d["source_draft"]["n_brands"] for d in dropped}, {3, 4})

    def test_every_button_value_has_a_handler(self):
        cards, _ = qpc.build_cards([_draft("f_and_b", "serving", "right_hand", 3)])
        for btn in cards[0]["buttons"]:
            self.assertIn(btn["value"], qpc.ANSWER_HANDLERS)    # Rule #7

    def test_consume_approve_awaits_pr_never_applies(self):
        out = qpc.consume_answers([{"id": "prior_x", "value": "approve_prior"}],
                                  now=datetime.datetime(2026, 6, 23))
        self.assertEqual(out[0]["outcome"], "awaiting_pr")
        self.assertFalse(out[0]["applied"])                     # Rule #12 — never auto-applied

    def test_consume_reject_recorded(self):
        out = qpc.consume_answers([{"id": "prior_x", "value": "reject_prior"}],
                                  now=datetime.datetime(2026, 6, 23))
        self.assertEqual(out[0]["outcome"], "rejected")
        self.assertFalse(out[0]["applied"])

    def test_consume_unhandled_value_refused(self):
        with self.assertRaises(ValueError):                     # Rule #7/#8 — the gate bites
            qpc.consume_answers([{"id": "prior_x", "value": "maybe_later"}])

    def test_zero_drafts_holds_not_crashes(self):
        cards, dropped = qpc.build_cards([])                    # Rule #9 — no manufactured work
        self.assertEqual(cards, [])
        self.assertEqual(dropped, [])

    def test_staged_batch_reads_back(self):
        cards, dropped = qpc.build_cards([_draft("f_and_b", "serving", "right_hand", 4)])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prior_cards.json"
            qpc.stage_cards(cards, dropped, "2026-Q2", path=p,
                            now=datetime.datetime(2026, 6, 23))
            back = json.loads(p.read_text(encoding="utf-8"))    # Rule #6 — end-to-end
        self.assertEqual(back["quarter"], "2026-Q2")
        self.assertEqual(back["n_cards"], 1)
        self.assertEqual(back["cards"][0]["source_draft"]["n_brands"], 4)
        self.assertEqual(back["cards"][0]["status"], "STAGED")

    def test_quarter_key(self):
        self.assertEqual(qpc.quarter_key(datetime.datetime(2026, 1, 5)), "2026-Q1")
        self.assertEqual(qpc.quarter_key(datetime.datetime(2026, 6, 23)), "2026-Q2")
        self.assertEqual(qpc.quarter_key(datetime.datetime(2026, 9, 30)), "2026-Q3")
        self.assertEqual(qpc.quarter_key(datetime.datetime(2026, 12, 31)), "2026-Q4")


if __name__ == "__main__":
    unittest.main()
