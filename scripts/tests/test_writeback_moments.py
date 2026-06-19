#!/usr/bin/env python3
"""B084 — writeback_moments synthetic tests. Pure-core (derive_moments) only: no IO, no clock,
fully deterministic. Proves the properties RABIE demanded:
  - a HUMAN-confirmed pick_selected rated >=4 becomes a moment (occasion + evidence parsed)
  - a PROVISIONAL (rabie_provisional) rating, even rating 5, moves NOTHING (human hands only, B156)
  - a sub-threshold human rating (<4) moves nothing
  - an event with no derivable evidence moves nothing
  - provenance cites the originating event by content key, confidence=confirmed, date=event ts
  - the produced bank validates against client_moments_bank_v1
  - IDEMPOTENT: a second derive over the same events makes zero further changes
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import writeback_moments  # noqa: E402
from writeback_moments import derive_moments  # noqa: E402

BASE = Path(__file__).parent.parent.parent
H = "testclient"


def _bank(moments=None):
    return {"moments": list(moments or [])}


def _ev(**kw):
    base = {"ts": "2026-06-12", "confirmer": "mohamed", "stamp": "x"}
    base.update(kw)
    return base


class TestWritebackMoments(unittest.TestCase):
    def test_human_pick_selected_becomes_moment(self):
        events = [_ev(type="pick_selected", subject="2027-02-08__ramadan → authenticity",
                      rating=5, note="الجريش، حكايته ما تنتهي مع الوقت.")]
        new_bank, changes = derive_moments(H, events, _bank())
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(new_bank["moments"]), 1)
        m = new_bank["moments"][0]
        self.assertEqual(m["occasion"], "ramadan")           # parsed from DATE__occasion → angle
        self.assertEqual(m["evidence"], "الجريش، حكايته ما تنتهي مع الوقت.")
        self.assertTrue(m["provenance"]["source"].startswith("approved_angle:"))
        self.assertEqual(m["provenance"]["confidence"], "confirmed")
        self.assertEqual(m["provenance"]["confirmer"], "mohamed")
        self.assertEqual(m["provenance"]["date_added"], "2026-06-12")  # the EVENT's ts, clock-free

    def test_provisional_rating_moves_nothing(self):
        # occasion_gold rating 4 but confirmer is rabie_provisional → NEVER compounds (B156)
        events = [_ev(type="occasion_gold", subject="ramadan", rating=5,
                      line="سحور النجدي في الليل.", confirmer="rabie_provisional")]
        new_bank, changes = derive_moments(H, events, _bank())
        self.assertEqual(changes, [])
        self.assertEqual(new_bank["moments"], [])

    def test_human_occasion_gold_does_compound(self):
        # same shape, but a HUMAN confirmer → it should write back
        events = [_ev(type="occasion_gold", subject="eid", rating=4,
                      line="جمعة العيد ما تكمل بدونها.", confirmer="mohamed")]
        new_bank, changes = derive_moments(H, events, _bank())
        self.assertEqual(len(changes), 1)
        self.assertEqual(new_bank["moments"][0]["occasion"], "eid")

    def test_sub_threshold_moves_nothing(self):
        events = [_ev(type="pick_selected", subject="2027-01-01__eid → warmth",
                      rating=3, note="نص عادي")]
        _, changes = derive_moments(H, events, _bank())
        self.assertEqual(changes, [])

    def test_no_evidence_moves_nothing(self):
        events = [_ev(type="pick_selected", subject="2027-01-01__eid → warmth", rating=5, note="")]
        _, changes = derive_moments(H, events, _bank())
        self.assertEqual(changes, [])

    def test_bool_rating_is_not_numeric(self):
        # guard: True is an int in Python; it must not be treated as rating>=4
        events = [_ev(type="pick_selected", subject="2027-01-01__eid → x", rating=True, note="x")]
        _, changes = derive_moments(H, events, _bank())
        self.assertEqual(changes, [])

    def test_idempotent(self):
        events = [_ev(type="pick_selected", subject="2027-02-08__ramadan → authenticity",
                      rating=5, note="الجريش، حكايته ما تنتهي مع الوقت.")]
        new_bank, _ = derive_moments(H, events, _bank())
        new_bank2, changes2 = derive_moments(H, events, new_bank)
        self.assertEqual(changes2, [])                       # second pass adds nothing
        self.assertEqual(len(new_bank2["moments"]), 1)

    def test_dedup_by_existing_evidence(self):
        # a moment already mined with the same evidence text must not be re-added
        existing = [{"occasion": "ramadan", "evidence": "الجريش، حكايته ما تنتهي مع الوقت.",
                     "provenance": {"source": "mined:x", "date_added": "2026-06-11",
                                    "confirmer": "pending_client", "confidence": "inferred", "scope": "brand"}}]
        events = [_ev(type="pick_selected", subject="2027-02-08__ramadan → authenticity",
                      rating=5, note="الجريش، حكايته ما تنتهي مع الوقت.")]
        _, changes = derive_moments(H, events, _bank(existing))
        self.assertEqual(changes, [])

    def test_output_validates_against_schema(self):
        import jsonschema
        schema = json.loads((BASE / "12_data_shapes/client_moments_bank_v1.schema.json").read_text())
        events = [_ev(type="pick_selected", subject="2027-03-09__eid_al_fitr → firaasa",
                      rating=5, note="الابتسامة تبدأ مع كيس البيك ❤️")]
        new_bank, _ = derive_moments(H, events, _bank())
        jsonschema.validate(new_bank, schema)                # raises on contract breach


if __name__ == "__main__":
    unittest.main()
