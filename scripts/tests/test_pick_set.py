#!/usr/bin/env python3
"""Tests for pick_set_v1 schema + reader (B079, MAJORS LAW)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pick_set  # noqa: E402


def _prov():
    return {
        "source": "test:pick_set",
        "date_added": "2026-06-18T00:00:00Z",
        "confirmer": "Mohamed",
        "confidence": "confirmed",
        "scope": "brand:eatjurisha",
    }


def _cands(n=3):
    return [{"option_id": k, "source": f"cd_0{i}"} for i, k in enumerate(["A", "B", "C"][:n], 1)]


def _open():
    return {
        "pick_set_ulid": "01HXYOPEN0000000000000000",
        "kind": "major_post",
        "slot": "2026-09-23__saudi_national_day",
        "candidates": _cands(),
        "status": "open",
        "picked": None,
        "picker": None,
        "resulting_event_ulid": None,
        "provenance": _prov(),
    }


def _picked():
    r = _open()
    r.update(pick_set_ulid="01HXYPICK0000000000000000", status="picked",
             picked="B", picker="mohamed",
             resulting_event_ulid="01HXYEVT00000000000000000")
    return r


class TestPickSet(unittest.TestCase):
    def test_open_is_valid(self):
        self.assertTrue(pick_set.is_valid(_open()))

    def test_picked_is_valid(self):
        self.assertTrue(pick_set.is_valid(_picked()))

    def test_needs_exactly_three_candidates(self):
        r = _open(); r["candidates"] = _cands(2)
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_picked_must_match_a_candidate(self):
        r = _picked(); r["picked"] = "Z"
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_picked_requires_picker(self):
        r = _picked(); r["picker"] = None
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_picked_requires_resulting_event(self):
        r = _picked(); r["resulting_event_ulid"] = None
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_open_cannot_carry_pick_fields(self):
        r = _open(); r["picked"] = "A"
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_bad_picker_enum_rejected(self):
        r = _picked(); r["picker"] = "rabie"
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_duplicate_option_ids_rejected(self):
        r = _open()
        r["candidates"] = [{"option_id": "A", "source": "cd_01"},
                           {"option_id": "A", "source": "cd_02"},
                           {"option_id": "C", "source": "cd_03"}]
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_converged_set_cannot_be_picked(self):
        r = _picked(); r["diversity_ok"] = False
        with self.assertRaises(pick_set.PickSetError):
            pick_set.validate(r)

    def test_converged_set_may_be_voided(self):
        r = _open(); r["diversity_ok"] = False; r["status"] = "voided"
        self.assertTrue(pick_set.is_valid(r))


if __name__ == "__main__":
    unittest.main()
