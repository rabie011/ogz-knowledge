#!/usr/bin/env python3
"""Guards the MONTHLY OWNER-OUTCOME QUESTION GENERATOR (B095) — the qualitative half of the full circle.

Locks:
  1. Monthly cadence — a brand live >= PERIOD_DAYS gets exactly one staged card; the card is
     pending_mohamed_approval (NEVER auto-sent — Rule #7).
  2. Idempotent — a second run in the same period emits 0 new cards (deterministic event_ulid).
  3. Too-new gating — a brand live < PERIOD_DAYS is skipped, not asked.
  4. The instrument is fixed — exactly the three allowed options (more/same/less) on every card.
  5. CONSUMER exists (Rule #6) — record_answer accepts the three options and appends an event.
  6. REFUSE (Rule #8) — record_answer rejects any answer outside the allowed set, no silent coercion.
  7. Empty inputs → honest 0/0, no crash (Pre-Build Q2).
"""
import importlib.util
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
_spec = importlib.util.spec_from_file_location("outcome_question", ROOT / "scripts/outcome_question.py")
oq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oq)

NOW = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)


def _write_jsonl(path: Path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


class TestOutcomeQuestion(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(self.id().split(".")[-1] + "_tmp_b095")
        self.tmp.mkdir(exist_ok=True)
        self._orig = {k: getattr(oq, k) for k in ("PUBLISHED_LEDGER", "QUESTIONS_LEDGER", "ANSWERS_LEDGER")}
        oq.PUBLISHED_LEDGER = self.tmp / "published.jsonl"
        oq.QUESTIONS_LEDGER = self.tmp / "outcome_questions.jsonl"
        oq.ANSWERS_LEDGER = self.tmp / "owner_outcomes.jsonl"

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(oq, k, v)
        for p in self.tmp.glob("*"):
            p.unlink()
        self.tmp.rmdir()

    def _publish(self, brand, days_ago):
        _write_jsonl(oq.PUBLISHED_LEDGER, [{
            "subject_generation_ulid": f"gen_{brand}",
            "brand_ulid": brand,
            "timestamp": (NOW - timedelta(days=days_ago)).isoformat(),
        }])

    def test_monthly_card_staged_pending_approval(self):
        self._publish("eatjurisha", days_ago=40)
        rep = oq.generate_questions(now=NOW)
        self.assertEqual(rep["new_cards"], 1)
        card = rep["cards"][0]
        self.assertEqual(card["status"], "pending_mohamed_approval")   # never auto-sent (Rule #7)
        self.assertEqual(card["audience"], "client_owner")
        self.assertEqual(card["question"], oq.QUESTION_TEXT)

    def test_idempotent_same_period(self):
        self._publish("albaik", days_ago=40)
        oq.generate_questions(now=NOW)
        rep2 = oq.generate_questions(now=NOW)
        self.assertEqual(rep2["new_cards"], 0)   # deterministic id → not re-staged

    def test_too_new_brand_skipped(self):
        self._publish("myfitness.sa", days_ago=10)   # live < PERIOD_DAYS
        rep = oq.generate_questions(now=NOW)
        self.assertEqual(rep["new_cards"], 0)
        self.assertTrue(any(s["reason"] == "not_live_a_month" for s in rep["skipped"]))

    def test_exactly_three_fixed_options(self):
        self._publish("eatjurisha", days_ago=40)
        card = oq.generate_questions(now=NOW)["cards"][0]
        vs = {o["v"] for o in card["options"]}
        self.assertEqual(vs, {"more", "same", "less"})

    def test_record_answer_consumer_exists(self):
        ev = oq.record_answer("eatjurisha", period_idx=1, answer="more", now=NOW)
        self.assertEqual(ev["event_type"], "owner_felt_outcome")
        self.assertEqual(ev["answer_label"], "أكثر")
        self.assertEqual(len(oq._read_jsonl(oq.ANSWERS_LEDGER)), 1)

    def test_record_answer_refuses_unknown(self):
        with self.assertRaises(ValueError):
            oq.record_answer("eatjurisha", period_idx=1, answer="maybe", now=NOW)
        self.assertEqual(oq._read_jsonl(oq.ANSWERS_LEDGER), [])   # nothing written on refuse

    def test_record_answer_idempotent(self):
        oq.record_answer("albaik", period_idx=2, answer="same", now=NOW)
        oq.record_answer("albaik", period_idx=2, answer="same", now=NOW)
        self.assertEqual(len(oq._read_jsonl(oq.ANSWERS_LEDGER)), 1)

    def test_empty_inputs_no_crash(self):
        rep = oq.generate_questions(now=NOW)
        self.assertEqual((rep["brands_live"], rep["new_cards"]), (0, 0))


if __name__ == "__main__":
    unittest.main()
