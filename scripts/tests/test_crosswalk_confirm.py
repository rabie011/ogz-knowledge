#!/usr/bin/env python3
"""B083c — crosswalk-confirm tap handler tests (June 19, RABIE's pick).

ROOT: B083b shipped the crosswalk organ ALL-PROPOSED — load_crosswalk() propagates an
honest 0 until Mohamed confirms. But the consumer that flips proposed→confirmed on his tap
did not exist, so A-47 could not go to the portal (Rule #7: never put a card on his phone
whose answer has nowhere to land). This is that consumer. The tests prove END-TO-END:
  - 'confirm_all' flips every proposed entry that carries a real proposed_kill
  - null-target codes (tone_off/off_brief/too_long/cultural_red_line) NEVER confirm
  - after the flip, load_crosswalk() returns the mappings AND derive() propagates a kill
    for a live-vocab ledger event (the severed wire is now closed by his tap, not by us)
  - 'reject' confirms nothing — propagation stays 0, his call recorded
  - the handler is idempotent (a replay confirms nothing new)
  - row['confirm_codes'] confirms only the named subset (granular taste)
  - the (item_id, answer) pairs resolve to the handler through apply_rulings dispatch
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import apply_rulings  # noqa: E402
import writeback_replay  # noqa: E402
from writeback_replay import derive, load_crosswalk  # noqa: E402

FOUNDER_KILLS = {"weak_tail", "not_saudi", "very_normal", "service_claim_unverified",
                 "generic_celebration_template"}

# the shipped organ's real shape: 4 mappable proposals + 4 null-target proposals
SHIPPED_MAP = [
    {"code": "too_generic", "source": "ledger", "proposed_kill": "very_normal",
     "status": "proposed", "confirmer": None, "ts": None},
    {"code": "factual_error", "source": "ledger", "proposed_kill": "service_claim_unverified",
     "status": "proposed", "confirmer": None, "ts": None},
    {"code": "cliche", "source": "portal", "proposed_kill": "generic_celebration_template",
     "status": "proposed", "confirmer": None, "ts": None},
    {"code": "weak_hook", "source": "portal", "proposed_kill": "weak_tail",
     "status": "proposed", "confirmer": None, "ts": None},
    {"code": "tone_off", "source": "portal", "proposed_kill": None, "status": "proposed",
     "confirmer": None, "ts": None},
    {"code": "off_brief", "source": "portal", "proposed_kill": None, "status": "proposed",
     "confirmer": None, "ts": None},
]


def _sandbox(d, rows=None):
    tmp = Path(d)
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    (tmp / "data" / "reason_code_crosswalk.json").write_text(
        json.dumps({"_meta": {"stamp": "PROVISIONAL"},
                    "map": json.loads(json.dumps(rows if rows is not None else SHIPPED_MAP))}))
    return tmp


def _load_map(tmp):
    return json.loads((tmp / "data" / "reason_code_crosswalk.json").read_text())["map"]


class TestConfirmAll(unittest.TestCase):
    def test_flips_only_mappable_proposals(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            msg = apply_rulings.h_crosswalk_confirm(
                tmp, {"item_id": "reason_code_crosswalk_0619", "answer": "confirm_all",
                      "ts": "2026-06-19T15:00"})
            m = {r["code"]: r for r in _load_map(tmp)}
            # the 4 with a real kill flip; the 2 null-target stay proposed
            for code in ("too_generic", "factual_error", "cliche", "weak_hook"):
                self.assertEqual(m[code]["status"], "confirmed", code)
                self.assertEqual(m[code]["confirmer"], "mohamed", code)
                self.assertEqual(m[code]["ts"], "2026-06-19T15:00", code)
            for code in ("tone_off", "off_brief"):
                self.assertEqual(m[code]["status"], "proposed", code)
                self.assertIsNone(m[code]["confirmer"], code)
            self.assertIn("4 mappings", msg)

    def test_endtoend_propagation_after_confirm(self):
        # the whole point: his tap closes the severed wire — a live-vocab event now kills
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            apply_rulings.h_crosswalk_confirm(
                tmp, {"item_id": "reason_code_crosswalk_0619", "answer": "confirm_all"})
            orig = writeback_replay.BASE
            writeback_replay.BASE = tmp
            try:
                cw = load_crosswalk(FOUNDER_KILLS)
            finally:
                writeback_replay.BASE = orig
            self.assertEqual(cw["too_generic"], "very_normal")
            self.assertEqual(cw["cliche"], "generic_celebration_template")
            events = [{"type": "version_verdict", "reason_code": "cliche",
                       "confirmer": "mohamed", "rating": 2}]
            _, taste, ch = derive(events, {"confirmed": [], "product_candidates": []},
                                  {"kills": []}, FOUNDER_KILLS, crosswalk=cw)
            self.assertIn("generic_celebration_template", taste["kills"])
            self.assertEqual(ch[0]["via"], "crosswalk:cliche")


class TestReject(unittest.TestCase):
    def test_reject_confirms_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            msg = apply_rulings.h_crosswalk_confirm(
                tmp, {"item_id": "reason_code_crosswalk_0619", "answer": "reject"})
            for r in _load_map(tmp):
                self.assertEqual(r["status"], "proposed")
            orig = writeback_replay.BASE
            writeback_replay.BASE = tmp
            try:
                self.assertEqual(load_crosswalk(FOUNDER_KILLS), {})
            finally:
                writeback_replay.BASE = orig
            self.assertIn("honest 0", msg)


class TestIdempotent(unittest.TestCase):
    def test_replay_confirms_nothing_new(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            row = {"item_id": "reason_code_crosswalk_0619", "answer": "confirm_all"}
            apply_rulings.h_crosswalk_confirm(tmp, row)
            before = json.dumps(_load_map(tmp), sort_keys=True)
            msg2 = apply_rulings.h_crosswalk_confirm(tmp, row)
            after = json.dumps(_load_map(tmp), sort_keys=True)
            self.assertEqual(before, after)  # no churn on replay
            self.assertIn("0 mappings", msg2)


class TestGranularSubset(unittest.TestCase):
    def test_confirm_codes_restricts(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)
            apply_rulings.h_crosswalk_confirm(
                tmp, {"item_id": "reason_code_crosswalk_0619", "answer": "confirm_all",
                      "confirm_codes": ["too_generic"]})
            m = {r["code"]: r for r in _load_map(tmp)}
            self.assertEqual(m["too_generic"]["status"], "confirmed")
            for code in ("factual_error", "cliche", "weak_hook"):
                self.assertEqual(m[code]["status"], "proposed", code)


class TestDispatchResolves(unittest.TestCase):
    def test_both_answers_route_to_handler(self):
        for ans in ("confirm_all", "reject"):
            fn = apply_rulings._resolve(("reason_code_crosswalk_0619", ans))
            self.assertIs(fn, apply_rulings.h_crosswalk_confirm, ans)


if __name__ == "__main__":
    unittest.main()
