"""B239b — lovable_inbox_reader.py: the Rule #6 reader for the write-only lovable harvest inbox.
Verifies it consumes what lovable_watch wrote, surfaces the pending queue, and auto-closes
(Rule #10) when the harvest cursor is advanced. No network, no keys — pure file logic."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lovable_inbox_reader as lir
import lovable_watch as lw


def _write_inbox(path, commits, head="abcd1234", ref="origin/main"):
    """Drive the REAL sensor writer so the reader is tested against the actual on-disk format."""
    lw._append_inbox(Path(path), commits, head, ref, baseline=False, now="2026-06-22T00:00:00")


class TestLovableInboxReader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.inbox = Path(self.tmp.name) / "lovable-commits.md"
        self.cursor = Path(self.tmp.name) / "cursor.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_inbox_is_clean_zero(self):
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st, {"total": 0, "harvested": 0, "pending": 0, "commits": []})
        self.assertIn("empty", lir.summary_line(self.inbox, self.cursor))

    def test_reads_what_the_sensor_wrote(self):
        _write_inbox(self.inbox, [
            {"short": "aaaa111", "subject": "feat: new hero", "date": "2026-06-22"},
            {"short": "bbbb222", "subject": "fix: token contrast", "date": "2026-06-22"},
        ])
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st["total"], 2)
        self.assertEqual(st["pending"], 2)
        self.assertEqual([c["short"] for c in st["commits"]], ["aaaa111", "bbbb222"])
        self.assertIn("2 Lovable commit(s) awaiting design-harvest", lir.summary_line(self.inbox, self.cursor))

    def test_baseline_marker_is_not_counted_as_a_commit(self):
        # A cold-start baseline header (no bullets) must read as zero pending — not a phantom commit.
        lw._append_inbox(self.inbox, [], "deadbeef", "origin/main", baseline=True, now="2026-06-22T00:00:00")
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st["total"], 0)
        self.assertEqual(st["pending"], 0)

    def test_mark_harvested_auto_closes_the_queue(self):
        _write_inbox(self.inbox, [
            {"short": "aaaa111", "subject": "feat: a", "date": "2026-06-22"},
            {"short": "bbbb222", "subject": "feat: b", "date": "2026-06-22"},
        ])
        n = lir.mark_harvested(self.inbox, self.cursor, now="2026-06-22T00:00:00")
        self.assertEqual(n, 2)
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st["pending"], 0)
        self.assertIn("clean", lir.summary_line(self.inbox, self.cursor))

    def test_new_commits_after_harvest_reopen_only_the_delta(self):
        _write_inbox(self.inbox, [{"short": "aaaa111", "subject": "feat: a", "date": "2026-06-22"}])
        lir.mark_harvested(self.inbox, self.cursor, now="2026-06-22T00:00:00")
        _write_inbox(self.inbox, [{"short": "cccc333", "subject": "feat: c", "date": "2026-06-23"}])
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st["pending"], 1)               # only the new one
        self.assertEqual(st["commits"][0]["short"], "cccc333")

    def test_cursor_never_exceeds_landed(self):
        # A stale cursor (e.g. inbox file reset) must not produce a negative pending count.
        self.cursor.write_text('{"harvested_count": 99}')
        _write_inbox(self.inbox, [{"short": "aaaa111", "subject": "feat: a", "date": "2026-06-22"}])
        st = lir.pending(self.inbox, self.cursor)
        self.assertEqual(st["harvested"], 1)
        self.assertEqual(st["pending"], 0)


if __name__ == "__main__":
    unittest.main()
