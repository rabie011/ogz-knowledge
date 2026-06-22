#!/usr/bin/env python3
"""Tests for the GENERATION IDENTITY LAYER (B095v step 1) — produce-time id minting.

Asserts the bedrock contract end-to-end (Rule #6): an identity minted by gen_identity at produce
time flows through outcome_ledger.record_published and is SEEN by BOTH outcome readers
(outcome_receipt, outcome_question) in the shape they consume. Plus determinism/idempotency
(CLAUDE.md "deterministic where possible") and the Rule #8 refusal guards. All ledger writes go to
a temp file; the readers' module paths are monkeypatched, so no real data file is touched."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import gen_identity as gi            # noqa: E402
import outcome_ledger as ol          # noqa: E402
import outcome_receipt as orc        # noqa: E402
import outcome_question as oq         # noqa: E402

CROCKFORD = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")  # 26-char Crockford base32 (no I,L,O,U)


class TestGenIdentity(unittest.TestCase):
    # ---- shape: same 26-char Crockford-base32 as the ledger ecosystem ------
    def test_brand_ulid_shape(self):
        self.assertRegex(gi.brand_ulid("eatjurisha"), CROCKFORD)

    def test_subject_generation_ulid_shape(self):
        self.assertRegex(
            gi.subject_generation_ulid("albaik", "2026-07-01", "2026-07-01__x.json"), CROCKFORD)

    def test_matches_reader_algorithm(self):
        # the producer mints with the EXACT algorithm the readers use (Rule #3 — one scheme)
        self.assertEqual(gi.deterministic_ulid("brand:eatjurisha"),
                         orc.deterministic_ulid("brand:eatjurisha"))

    # ---- determinism + idempotency (re-running produce keeps the id) -------
    def test_brand_ulid_deterministic(self):
        self.assertEqual(gi.brand_ulid("albaik"), gi.brand_ulid("albaik"))

    def test_gen_ulid_deterministic(self):
        a = gi.subject_generation_ulid("albaik", "2026-07-01", "f.json")
        b = gi.subject_generation_ulid("albaik", "2026-07-01", "f.json")
        self.assertEqual(a, b, "same piece must mint the same id across runs")

    def test_distinct_pieces_distinct_ids(self):
        ids = {
            gi.subject_generation_ulid("albaik", "2026-07-01", "f.json"),
            gi.subject_generation_ulid("albaik", "2026-07-02", "f.json"),
            gi.subject_generation_ulid("eatjurisha", "2026-07-01", "f.json"),
            gi.subject_generation_ulid("albaik", "2026-07-01", "g.json"),
        }
        self.assertEqual(len(ids), 4, "handle/date/file each change the identity")

    def test_distinct_brands_distinct_ulids(self):
        self.assertNotEqual(gi.brand_ulid("albaik"), gi.brand_ulid("eatjurisha"))

    # ---- Rule #8 refusal guards (never mint an empty identity) -------------
    def test_brand_ulid_refuses_empty(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                gi.brand_ulid(bad)

    def test_gen_ulid_refuses_empty_component(self):
        with self.assertRaises(ValueError):
            gi.subject_generation_ulid("albaik", "", "f.json")
        with self.assertRaises(ValueError):
            gi.subject_generation_ulid("", "2026-07-01", "f.json")
        with self.assertRaises(ValueError):
            gi.subject_generation_ulid("albaik", "2026-07-01", "")

    # ---- Rule #6 end-to-end: produced identity → ledger → BOTH readers -----
    def test_produced_identity_flows_to_both_readers(self):
        gen = gi.subject_generation_ulid("eatjurisha", "2026-06-01", "2026-06-01__a.json")
        brand = gi.brand_ulid("eatjurisha")
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "published.jsonl"
            ev = ol.record_published(gen, brand, "2026-06-01T08:00:00+00:00", path=ledger)
            self.assertEqual(ev["subject_generation_ulid"], gen)
            self.assertEqual(ev["brand_ulid"], brand)

            # reader 1 — outcome_receipt sees exactly the one published piece
            o1 = orc.PUBLISHED_LEDGER
            try:
                orc.PUBLISHED_LEDGER = ledger
                rep = orc.collect(dry_run=True)
            finally:
                orc.PUBLISHED_LEDGER = o1
            self.assertEqual(rep.get("published_seen"), 1)

            # reader 2 — outcome_question's live-since consumes the same event
            o2 = oq.PUBLISHED_LEDGER
            try:
                oq.PUBLISHED_LEDGER = ledger
                rep2 = oq.generate_questions(dry_run=True)
            finally:
                oq.PUBLISHED_LEDGER = o2
            # the brand is now "live since" the published timestamp (was 0 eligible when empty)
            self.assertIn(brand, json.dumps(rep2),
                          "outcome_question must see the produced brand_ulid in the ledger")


if __name__ == "__main__":
    unittest.main()
