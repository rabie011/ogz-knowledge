#!/usr/bin/env python3
"""B101 — RABIE's 2/5 C-rating + regeneration must live as a LEDGER EVENT, not an inline note.

Rule #5-amendment ("events first, notes never") + Rule #6 (Consumer Law): the voice_C truth-error
ruling that drove the persona-C regeneration was, per THE_CLIENT_PYRAMID.md, surviving "only as an
inline note in voice_birth_week.json". It was in fact already written to the jurisha ledger on
2026-06-11 — but with NO reader guarding it, a future ledger rewrite could silently drop it and the
backlog would never notice. This test IS that reader: it pins the event's existence + shape against
the REAL client_event_v1 contract, so the ruling can never regress back to a bare note.
"""
import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER = BASE / "clients/eatjurisha/events/ledger.jsonl"
SCHEMA = json.loads((BASE / "12_data_shapes/client_event_v1.schema.json").read_text())


def _events():
    out = []
    for line in LEDGER.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


class TestB101VoiceCRegenerationLogged(unittest.TestCase):
    def setUp(self):
        self.events = _events()
        # The persona-C truth-error rating: a voice_rating event scoring the ORIGINAL C low.
        self.c_ratings = [
            e for e in self.events
            if e.get("type") == "voice_rating"
            and "voice_C" in str(e.get("subject", ""))
            and "original" in str(e.get("subject", ""))
        ]

    def test_event_exists(self):
        self.assertTrue(
            self.c_ratings,
            "B101 regression: RABIE's persona-C truth-error rating is missing from the jurisha "
            "ledger — the ruling must live as an event, never only as an inline note.",
        )

    def test_event_is_the_2of5_truth_error(self):
        ev = self.c_ratings[0]
        self.assertEqual(ev.get("rating"), 2, "C-rating must record the 2/5 score")
        self.assertEqual(ev.get("reason_code"), "factual_error",
                         "the kill reason was a truth/factual error (delivery-only brand)")
        self.assertEqual(ev.get("confirmer"), "rabie_provisional",
                         "the rating is RABIE-provisional, pending Mohamed")

    def test_event_is_schema_valid(self):
        import jsonschema
        for ev in self.c_ratings:
            jsonschema.validate(ev, SCHEMA)  # raises on any contract breach


if __name__ == "__main__":
    unittest.main()
