#!/usr/bin/env python3
"""B045 — every system-produced v6 result carries the PROVISIONAL provenance stamp.

Rule #12: the SYSTEM produces; nothing reaches Mohamed unstamped.
Rule #6: a writer needs a reader — this test IS the reader/guard on the provenance
contract, so the wire (api/server._provenance_block → v6 response) cannot be silently
re-severed. The shape matches the post-card in render_client_slot.py.

Run: python3 -m unittest discover -s scripts/tests -q
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
from server import _provenance_block


class TestV6Provenance(unittest.TestCase):
    REQUIRED = {"source", "rendered", "confirmer", "stamp"}

    def test_block_has_all_four_fields(self):
        p = _provenance_block()
        self.assertEqual(self.REQUIRED, set(p), p)

    def test_stamp_is_provisional(self):
        # the kill: anything reaching Mohamed must read PROVISIONAL until he confirms
        self.assertIn("PROVISIONAL", _provenance_block()["stamp"])

    def test_confirmer_starts_pending(self):
        # confirmer flips only on his real tap, never by the system
        self.assertEqual("pending", _provenance_block()["confirmer"])

    def test_rendered_is_iso_today(self):
        import datetime
        self.assertEqual(datetime.date.today().isoformat(), _provenance_block()["rendered"])

    def test_source_is_carried_through(self):
        self.assertEqual("dna_v6_feed", _provenance_block("dna_v6_feed")["source"])


if __name__ == "__main__":
    unittest.main()
