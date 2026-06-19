#!/usr/bin/env python3
"""B083 — writeback_metrics synthetic tests. Pure-core (diagnose) only: no IO, no real
clock (now is injected), fully deterministic. Proves the status machine RABIE demanded:
  - live    when a promotion landed in the window
  - stalled when feedable verdicts exist but zero promotions (broken wire)
  - severed when confirmed verdicts exist but NONE are consumable
  - idle    when nothing is confirmed yet (must NEVER alarm — waits honestly)
  - the window check: an old promotion does not keep a client "live"
  - undated writeback events still count (absence of a date never fakes freshness)
  - feedable mirrors B082 exactly: only truth_confirmed+subject or a known-kill reason_code
"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from writeback_metrics import diagnose  # noqa: E402

KILLS = {"weak_tail", "not_saudi", "very_normal"}
NOW = date(2026, 6, 19)

# a human-confirmed event per B082's _is_confirmed
def _conf(**kw):
    kw.setdefault("confirmer", "mohamed")
    return kw

# a provisional/RABIE event — must move nothing, count as nothing
def _prov(**kw):
    kw.setdefault("confirmer", "rabie_provisional")
    kw.setdefault("stamp", "PROVISIONAL")
    return kw


class TestStatusMachine(unittest.TestCase):
    def test_idle_no_confirmed_never_alarms(self):
        led = [_prov(type="version_verdict"), _prov(type="batch_rating")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["status"], "idle")
        self.assertFalse(r["alarm"])
        self.assertEqual(r["confirmed_verdicts"], 0)

    def test_severed_confirmed_but_not_feedable(self):
        # 4 human-confirmed verdicts, none of a type B082 can consume → severed (the real
        # current pilot state: votes present, nothing promotable).
        led = [_conf(type="version_verdict"), _conf(type="compare_verdict"),
               _conf(type="occasion_gold"), _conf(type="red_line_added")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["status"], "severed")
        self.assertTrue(r["alarm"])
        self.assertEqual(r["confirmed_verdicts"], 4)
        self.assertEqual(r["feedable_now"], 0)

    def test_stalled_feedable_but_no_promotion(self):
        led = [_conf(type="truth_confirmed", subject="جريش")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["status"], "stalled")
        self.assertTrue(r["alarm"])
        self.assertEqual(r["feedable_now"], 1)

    def test_live_when_promotion_in_window(self):
        led = [_conf(type="truth_confirmed", subject="جريش")]
        wb = [{"type": "writeback_truth_confirmed", "subject": "جريش", "ts": "2026-06-18T10:00"}]
        r = diagnose(led, wb, KILLS, now=NOW)
        self.assertEqual(r["status"], "live")
        self.assertFalse(r["alarm"])
        self.assertEqual(r["promotions_total"], 1)
        self.assertEqual(r["promotions_in_window"], 1)

    def test_old_promotion_does_not_keep_live(self):
        led = [_conf(type="truth_confirmed", subject="جريش")]
        wb = [{"type": "writeback_truth_confirmed", "subject": "جريش", "ts": "2026-01-01T10:00"}]
        r = diagnose(led, wb, KILLS, now=NOW, window_days=60)
        self.assertEqual(r["promotions_total"], 1)
        self.assertEqual(r["promotions_in_window"], 0)
        self.assertEqual(r["status"], "stalled")   # feedable present, none recent → broken wire

    def test_undated_writeback_counts_in_window(self):
        # a legacy promotion with no ts must NOT hide from the window (no fake freshness)
        led = [_conf(type="truth_confirmed", subject="جريش")]
        wb = [{"type": "writeback_truth_confirmed", "subject": "جريش"}]
        r = diagnose(led, wb, KILLS, now=NOW)
        self.assertEqual(r["promotions_in_window"], 1)
        self.assertEqual(r["status"], "live")


class TestFeedableMirrorsB082(unittest.TestCase):
    def test_known_kill_reason_code_is_feedable(self):
        led = [_conf(type="version_verdict", reason_code="weak_tail")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["feedable_now"], 1)
        self.assertEqual(r["status"], "stalled")

    def test_unknown_reason_code_not_feedable(self):
        led = [_conf(type="version_verdict", reason_code="i_just_dont_like_it")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["feedable_now"], 0)
        self.assertEqual(r["status"], "severed")

    def test_truth_confirmed_without_subject_not_feedable(self):
        led = [_conf(type="truth_confirmed")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["feedable_now"], 0)

    def test_provisional_feedable_event_moves_nothing(self):
        # a truth_confirmed that is only PROVISIONAL is not a confirmed verdict at all
        led = [_prov(type="truth_confirmed", subject="جريش")]
        r = diagnose(led, [], KILLS, now=NOW)
        self.assertEqual(r["confirmed_verdicts"], 0)
        self.assertEqual(r["feedable_now"], 0)
        self.assertEqual(r["status"], "idle")


class TestPromotionCounter(unittest.TestCase):
    def test_counts_by_kind(self):
        led = [_conf(type="truth_confirmed", subject="جريش")]
        wb = [
            {"type": "writeback_truth_confirmed", "subject": "جريش", "ts": "2026-06-18T10:00"},
            {"type": "writeback_provenance_promoted", "subject": "جريش", "ts": "2026-06-18T10:00"},
            {"type": "writeback_kill_propagated", "subject": "weak_tail", "ts": "2026-06-18T10:00"},
        ]
        r = diagnose(led, wb, KILLS, now=NOW)
        self.assertEqual(r["promotions_total"], 3)
        self.assertEqual(r["promotions_by_kind"]["truth_confirmed"], 1)
        self.assertEqual(r["promotions_by_kind"]["provenance_promoted"], 1)
        self.assertEqual(r["promotions_by_kind"]["kill_propagated"], 1)


if __name__ == "__main__":
    unittest.main()
