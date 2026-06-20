#!/usr/bin/env python3
"""Tests for the judge2→ledger WRITER (B282) — his judge2 batch approvals become human-confirmed
`client_approved` client events so writeback_moments (the reader) stops starving (Rule #6).

Injected writer + temp base: no real client ledger is touched. The injected writer mimics
ledger_write (schema-validate + B156 confirmer gate + append) so the path is exercised against the
REAL contract its readers depend on, while writing only under the temp base."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import judge2_ledger_writer as jlw  # noqa: E402
from approvers_registry import check_confirmer  # noqa: E402
from intel_consumer_health import judge2_positive_approvals  # noqa: E402

import jsonschema  # noqa: E402
_SCHEMA = json.loads((SCRIPTS.parent / "12_data_shapes" / "client_event_v1.schema.json").read_text())


def _answer(item_id, answer="approved", rating=None, judge="mohamed", ts="2026-06-12T20:17:26"):
    r = {"item_id": item_id, "answer": answer, "judge": judge, "ts": ts}
    if rating is not None:
        r["rating"] = rating
    return r


class TestJudge2LedgerWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        for h in ("eatjurisha", "albaik", "myfitness.sa"):
            (self.base / "clients" / h / "posts").mkdir(parents=True)
        (self.base / "data").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _post(self, handle, date, captions, occasion="evergreen", version="v5"):
        fn = f"{date}__{occasion}__{version}.json" if version else f"{date}__{occasion}.json"
        (self.base / "clients" / handle / "posts" / fn).write_text(json.dumps({
            "handle": handle, "date": date, "slot": {"date": date, "type": occasion},
            "captions": captions,
        }, ensure_ascii=False))

    def _answers(self, rows):
        p = self.base / "data/mohamed_answers.jsonl"
        p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
        return p

    def _ledger_writer(self, handle, ev):
        """Mimics ledger_write: validate + B156 gate, then append under the TEMP base."""
        jsonschema.validate(ev, _SCHEMA)
        check_confirmer(ev)
        lf = self.base / "clients" / handle / "events/ledger.jsonl"
        lf.parent.mkdir(parents=True, exist_ok=True)
        with open(lf, "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # ---- parsing --------------------------------------------------------------
    def test_parse_plain_handle_and_date(self):
        self.assertEqual(jlw.parse_item_id("judge2_eatjurisha_2027-06-30"),
                         ("eatjurisha", "2027-06-30", None))

    def test_parse_dotted_handle_and_variant(self):
        self.assertEqual(jlw.parse_item_id("judge2_myfitness.sa_2026-07-24_b"),
                         ("myfitness.sa", "2026-07-24", "b"))

    def test_parse_non_judge2_returns_none(self):
        self.assertEqual(jlw.parse_item_id("voice_albaik_2026"), (None, None, None))

    # ---- predicate parity with the detector (Rule #3 / #9) --------------------
    def test_predicate_matches_detector_count(self):
        rows = [
            _answer("judge2_eatjurisha_2027-06-30", "approved", None),     # +
            _answer("judge2_albaik_2027-06-29", "comment", 5),             # + (rating>=4)
            _answer("judge2_albaik_2027-02-05", "approved", 2),            # + (approved)
            _answer("judge2_eatjurisha_2026-08-24", "rejected", 1),        # -
            _answer("judge2_albaik_2027-03-06", "comment", 3),             # -
            _answer("voice_albaik_2026", "approved", 5),                   # - (not judge2)
            _answer("judge2_albaik_2027-05-07", "approved", 5, judge="rabie"),  # - (not mohamed)
        ]
        p = self._answers(rows)
        mine = sum(1 for r in rows if jlw.is_positive_judge2(r))
        self.assertEqual(mine, judge2_positive_approvals(p))
        self.assertEqual(mine, 3)

    # ---- happy path -----------------------------------------------------------
    def test_happy_path_writes_client_approved_with_caption(self):
        self._post("eatjurisha", "2027-06-30", ["الحكايات تتجدد مع كل ملعقة 🌿", "ثاني"])
        p = self._answers([_answer("judge2_eatjurisha_2027-06-30", "approved", 5)])
        res = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        self.assertEqual(res["written"], 1)
        ev = json.loads((self.base / "clients/eatjurisha/events/ledger.jsonl").read_text().strip())
        self.assertEqual(ev["type"], "client_approved")
        self.assertEqual(ev["confirmer"], "mohamed")
        self.assertEqual(ev["note"], "الحكايات تتجدد مع كل ملعقة 🌿")   # lead caption = evidence
        self.assertEqual(ev["rating"], 5)
        self.assertIn("src_key", ev)
        check_confirmer(ev)
        jsonschema.validate(ev, _SCHEMA)

    def test_picks_latest_version_caption(self):
        self._post("albaik", "2027-06-29", ["قديم"], version="v2")
        self._post("albaik", "2027-06-29", ["الأحدث"], version="v5")
        p = self._answers([_answer("judge2_albaik_2027-06-29", "approved", 5)])
        jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        ev = json.loads((self.base / "clients/albaik/events/ledger.jsonl").read_text().strip())
        self.assertEqual(ev["note"], "الأحدث")

    # ---- idempotency ----------------------------------------------------------
    def test_idempotent_second_run_is_noop(self):
        self._post("eatjurisha", "2027-06-30", ["كابشن"])
        p = self._answers([_answer("judge2_eatjurisha_2027-06-30", "approved", 5)])
        r1 = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        r2 = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        self.assertEqual(r1["written"], 1)
        self.assertEqual(r2["written"], 0)
        self.assertEqual(r2["skipped_dup"], 1)
        lines = (self.base / "clients/eatjurisha/events/ledger.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)   # exactly one event, never duplicated

    # ---- skips ----------------------------------------------------------------
    def test_non_positive_and_non_mohamed_skipped(self):
        self._post("eatjurisha", "2027-06-30", ["x"])
        p = self._answers([
            _answer("judge2_eatjurisha_2027-06-30", "rejected", 1),
            _answer("judge2_eatjurisha_2027-06-30", "approved", 5, judge="rabie"),
        ])
        res = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        self.assertEqual(res["written"], 0)
        self.assertFalse((self.base / "clients/eatjurisha/events/ledger.jsonl").exists())

    def test_phantom_client_skipped(self):
        p = self._answers([_answer("judge2_ghostbrand_2027-06-30", "approved", 5)])
        res = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        self.assertEqual(res["written"], 0)
        self.assertEqual(res["skipped_phantom"], 1)

    def test_no_caption_event_still_lands_without_note(self):
        # positive approval but NO post on disk → event lands (trust moved), no fabricated caption
        p = self._answers([_answer("judge2_albaik_2027-12-25", "approved", 5)])
        res = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer)
        self.assertEqual(res["written"], 1)
        self.assertEqual(res["no_caption"], 1)
        ev = json.loads((self.base / "clients/albaik/events/ledger.jsonl").read_text().strip())
        self.assertNotIn("note", ev)

    def test_dry_run_writes_nothing(self):
        self._post("eatjurisha", "2027-06-30", ["x"])
        p = self._answers([_answer("judge2_eatjurisha_2027-06-30", "approved", 5)])
        res = jlw.run(answers_path=p, base=self.base, writer=self._ledger_writer, dry_run=True)
        self.assertEqual(res["written"], 1)         # counted as would-write
        self.assertFalse((self.base / "clients/eatjurisha/events/ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
