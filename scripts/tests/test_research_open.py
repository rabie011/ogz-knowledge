#!/usr/bin/env python3
"""Locks the research_ledger Rule #6 consumer (June 15): the audit trail Mohamed asked for was
write-only (client_strategy.py wrote it, nothing read it). research_open is its reader, and
make_sure SURFACES it every heartbeat so it can never go invisible again."""
import inspect, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import research_open as ro
import make_sure as ms


class TestResearchOpen(unittest.TestCase):
    def test_reader_surfaces_written_requests(self):
        """If any pilot has a research_ledger with content, the reader must return it (no silent loss)."""
        reqs = ro.open_requests()
        ledgers = list((Path(__file__).parent.parent.parent / "clients").glob("*/profile/research_ledger.jsonl"))
        if not ledgers:
            self.skipTest("no research ledgers yet")
        self.assertGreater(len(reqs), 0, "research_ledger has content but the reader surfaces none — write-only again")
        self.assertTrue(all("handle" in r and "request" in r for r in reqs))

    def test_make_sure_surfaces_the_audit_trail(self):
        """The write-only organ's reader must be WIRED into the heartbeat (Rule #6 consumer present)."""
        self.assertIn("research_open", inspect.getsource(ms.main),
                      "research audit trail not surfaced in make_sure — the reader is orphaned")

    def test_summary_line_never_throws(self):
        self.assertIsInstance(ro.summary_line(), str)


if __name__ == "__main__":
    unittest.main()
