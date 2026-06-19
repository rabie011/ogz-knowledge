#!/usr/bin/env python3
"""B083b — reason_code crosswalk tests (June 19, RABIE's pick).

ROOT: the writeback kill-wire was SEVERED (B083: all 3 pilots) not for a missing pipe but a
missing TRANSLATION — three disjoint reason_code vocabularies (portal answers, client-ledger
events, founder kills) never meet, so a kill can never propagate by raw-name match. The
crosswalk is the confirmed translation. These tests prove:
  - load_crosswalk consumes ONLY confirmed entries whose target is a real founder kill
  - a ledger event in the LIVE vocab (too_generic) propagates a kill via a CONFIRMED entry
  - a PROPOSED (un-confirmed) entry propagates NOTHING — Rule #12, his tap is the gate
  - a confirmed entry to a NON-founder slug is refused (no inventing kills off-vocab)
  - B083's detector flips severed→feedable on the SAME rule (no drifting definition)
  - the SHIPPED crosswalk organ is all-proposed → honest 0 on real data until he taps
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import writeback_replay  # noqa: E402
from writeback_replay import derive, load_crosswalk  # noqa: E402
import writeback_metrics  # noqa: E402
from writeback_metrics import _is_feedable, diagnose  # noqa: E402

FOUNDER_KILLS = {"weak_tail", "not_saudi", "very_normal", "service_claim_unverified"}


def _tp():
    return {"confirmed": [], "product_candidates": []}


def _taste():
    return {"kills": []}


class TestCrosswalkLoader(unittest.TestCase):
    def _write(self, tmp_path, rows):
        (tmp_path / "data").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "reason_code_crosswalk.json").write_text(
            json.dumps({"map": rows}))

    def test_only_confirmed_valid_entries_load(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, [
                {"code": "too_generic", "proposed_kill": "very_normal", "status": "confirmed"},
                {"code": "cliche", "proposed_kill": "weak_tail", "status": "proposed"},
                {"code": "factual_error", "proposed_kill": "not_a_real_kill", "status": "confirmed"},
                {"code": "off_brief", "proposed_kill": None, "status": "confirmed"},
            ])
            orig = writeback_replay.BASE
            writeback_replay.BASE = tmp
            try:
                cw = load_crosswalk(FOUNDER_KILLS)
            finally:
                writeback_replay.BASE = orig
            # only the confirmed + in-vocab + non-null entry survives
            self.assertEqual(cw, {"too_generic": "very_normal"})

    def test_missing_file_is_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            orig = writeback_replay.BASE
            writeback_replay.BASE = Path(d)
            try:
                self.assertEqual(load_crosswalk(FOUNDER_KILLS), {})
            finally:
                writeback_replay.BASE = orig


class TestCrosswalkPropagation(unittest.TestCase):
    def test_live_vocab_propagates_via_confirmed_crosswalk(self):
        events = [{"type": "version_verdict", "reason_code": "too_generic",
                   "confirmer": "mohamed", "rating": 2}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS,
                              crosswalk={"too_generic": "very_normal"})
        self.assertIn("very_normal", taste["kills"])
        self.assertEqual(len(ch), 1)
        self.assertEqual(ch[0]["kind"], "kill_propagated")
        self.assertEqual(ch[0]["subject"], "very_normal")
        self.assertEqual(ch[0]["via"], "crosswalk:too_generic")

    def test_no_crosswalk_means_severed(self):
        # the exact severed-wire state: live vocab, NO confirmed crosswalk → nothing moves
        events = [{"type": "version_verdict", "reason_code": "too_generic",
                   "confirmer": "mohamed"}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS, crosswalk={})
        self.assertEqual(taste["kills"], [])
        self.assertEqual(ch, [])

    def test_direct_founder_vocab_still_works(self):
        # regression: a raw founder-kill reason_code still propagates with via='direct'
        events = [{"type": "batch_rating", "reason_code": "weak_tail", "confirmer": "mohamed"}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS, crosswalk={})
        self.assertIn("weak_tail", taste["kills"])
        self.assertEqual(ch[0]["via"], "direct")

    def test_crosswalk_to_offvocab_kill_refused(self):
        # even a crosswalk dict cannot smuggle a non-founder slug into kills
        events = [{"type": "version_verdict", "reason_code": "too_generic", "confirmer": "mohamed"}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS,
                              crosswalk={"too_generic": "not_a_real_kill"})
        self.assertEqual(taste["kills"], [])
        self.assertEqual(ch, [])

    def test_provisional_event_still_moves_nothing(self):
        events = [{"type": "version_verdict", "reason_code": "too_generic",
                   "confirmer": "rabie_provisional", "stamp": "PROVISIONAL"}]
        _, taste, ch = derive(events, _tp(), _taste(), FOUNDER_KILLS,
                              crosswalk={"too_generic": "very_normal"})
        self.assertEqual(ch, [])


class TestDetectorMirrorsRule(unittest.TestCase):
    def test_feedable_flips_with_crosswalk(self):
        ev = {"type": "version_verdict", "reason_code": "too_generic", "confirmer": "mohamed"}
        self.assertFalse(_is_feedable(ev, FOUNDER_KILLS, {}))
        self.assertTrue(_is_feedable(ev, FOUNDER_KILLS, {"too_generic": "very_normal"}))

    def test_diagnose_severed_without_crosswalk_feedable_with(self):
        ledger = [{"type": "version_verdict", "reason_code": "too_generic", "confirmer": "mohamed"}]
        sev = diagnose(ledger, [], FOUNDER_KILLS, crosswalk={})
        self.assertEqual(sev["status"], "severed")
        self.assertEqual(sev["feedable_now"], 0)
        fed = diagnose(ledger, [], FOUNDER_KILLS, crosswalk={"too_generic": "very_normal"})
        self.assertEqual(fed["feedable_now"], 1)
        self.assertEqual(fed["status"], "stalled")  # feedable but no promotion yet = wire to fire


class TestShippedOrganIsHonestZero(unittest.TestCase):
    def test_real_crosswalk_all_proposed(self):
        # the organ we ship must propagate NOTHING on real data until Mohamed taps (Rule #9/#12)
        fk = writeback_replay._founder_kill_vocab()
        cw = load_crosswalk(fk)
        self.assertEqual(cw, {}, f"shipped crosswalk must be all-proposed, got live map: {cw}")


if __name__ == "__main__":
    unittest.main()
