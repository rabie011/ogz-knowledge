#!/usr/bin/env python3
"""Tests for the PUBLISH-LEDGER WRITER (B095w) — the missing producer of data/published.jsonl.

Asserts the Consumer Law end-to-end (Rule #6): an event written by outcome_ledger.record_published
is SEEN by BOTH starved readers — outcome_receipt (collector) and outcome_question (live-since) —
in the exact shape they consume. Plus the Rule #8 refusal guards and idempotency. All writes go to
a temp ledger; the readers' module-level paths are monkeypatched, so no real data file is touched."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import outcome_ledger as ol          # noqa: E402
import outcome_receipt as orc        # noqa: E402
import outcome_question as oq         # noqa: E402


class TestOutcomeLedgerWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "published.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    # ---- the writer itself -------------------------------------------------
    def test_writes_exact_reader_schema(self):
        ev = ol.record_published("GEN001", "BRAND_A", "2026-06-01T08:00:00+00:00", path=self.ledger)
        self.assertEqual(set(ev), {"subject_generation_ulid", "brand_ulid", "timestamp"})
        rows = [json.loads(l) for l in self.ledger.read_text().splitlines() if l.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["subject_generation_ulid"], "GEN001")
        self.assertEqual(rows[0]["brand_ulid"], "BRAND_A")

    def test_default_timestamp_is_parseable(self):
        ev = ol.record_published("GEN002", "BRAND_A", path=self.ledger)
        # must round-trip through the readers' own parser
        self.assertIsNotNone(ol._parse_ts(ev["timestamp"]))

    def test_idempotent_same_generation(self):
        ol.record_published("GEN003", "BRAND_A", "2026-06-01T08:00:00+00:00", path=self.ledger)
        ol.record_published("GEN003", "BRAND_A", "2026-06-09T08:00:00+00:00", path=self.ledger)
        rows = [json.loads(l) for l in self.ledger.read_text().splitlines() if l.strip()]
        self.assertEqual(len(rows), 1, "same generation must not double-append")
        self.assertEqual(rows[0]["timestamp"], "2026-06-01T08:00:00+00:00", "first write wins")

    # ---- Rule #8 refusal guards -------------------------------------------
    def test_refuses_empty_gen(self):
        with self.assertRaises(ValueError):
            ol.record_published("", "BRAND_A", path=self.ledger)
        self.assertFalse(self.ledger.exists(), "no row may be written on refusal")

    def test_refuses_empty_brand(self):
        with self.assertRaises(ValueError):
            ol.record_published("GEN004", "  ", path=self.ledger)

    def test_refuses_unparseable_timestamp(self):
        with self.assertRaises(ValueError):
            ol.record_published("GEN005", "BRAND_A", "not-a-date", path=self.ledger)
        self.assertFalse(self.ledger.exists(), "bad timestamp must refuse before write")

    def test_status_empty_then_counts(self):
        self.assertEqual(ol.status(path=self.ledger)["n_published"], 0)
        ol.record_published("GEN006", "BRAND_A", path=self.ledger)
        ol.record_published("GEN007", "BRAND_B", path=self.ledger)
        s = ol.status(path=self.ledger)
        self.assertEqual(s["n_published"], 2)
        self.assertEqual(s["by_brand"], {"BRAND_A": 1, "BRAND_B": 1})

    # ---- Rule #6 end-to-end: both readers now SEE the written event --------
    def test_outcome_receipt_consumes_written_event(self):
        ol.record_published("GENX", "BRAND_A", "2026-06-01T08:00:00+00:00", path=self.ledger)
        orig = orc.PUBLISHED_LEDGER
        try:
            orc.PUBLISHED_LEDGER = self.ledger
            report = orc.collect(dry_run=True)
        finally:
            orc.PUBLISHED_LEDGER = orig
        # the collector saw exactly the one published piece (published_seen was 0 when honest-empty;
        # no receipt is emitted yet because the piece has no metrics — that part is B094's job)
        self.assertEqual(report.get("published_seen"), 1,
                         "outcome_receipt must now see the written publish event")

    def test_outcome_question_live_since_uses_written_event(self):
        ol.record_published("GENY", "BRAND_A", "2026-06-01T08:00:00+00:00", path=self.ledger)
        orig = oq.PUBLISHED_LEDGER
        try:
            oq.PUBLISHED_LEDGER = self.ledger
            report = oq.generate_questions(dry_run=True)
        finally:
            oq.PUBLISHED_LEDGER = orig
        # before the writer there were 0 eligible brands (empty ledger). Now BRAND_A has a live-since.
        seen = json.dumps(report, default=str)
        self.assertIn("BRAND_A", seen, "outcome_question must now compute live-since from the event")


if __name__ == "__main__":
    unittest.main()
