#!/usr/bin/env python3
"""Tests for the PUBLISH-CONFIRM WIRE (B095v STEP 2) — the go-live tap → outcome ledger.

Proves the Consumer Law end-to-end (Rule #6/#7): a 'published' tap on a card staged by
build_publish_confirm_cards routes through apply_rulings._resolve to h_publish_confirm,
which writes ONE event to data/published.jsonl in the exact shape both outcome readers
consume — and is idempotent + refuses (Rule #8) when the card/identity is missing.

Replicates main()'s exact dispatch (`fn = _resolve(key); fn(b, row)`) in a sandbox so the
test is faithful to production without main()'s unrelated pairwise/elo side-effects.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import apply_rulings as ar            # noqa: E402
import build_publish_confirm_cards as bpc  # noqa: E402
import outcome_ledger as ol          # noqa: E402

GEN, BRAND = "GEN_PUB_001", "BRAND_JUR"


class TestPublishConfirmWire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.b = Path(self.tmp.name)
        (self.b / "data").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _stage_card(self, gen=GEN, brand=BRAND, handle="eatjurisha", date="2026-09-23"):
        card = {"id": f"publish_confirm_{gen}", "kind": "buttons",
                "subject_generation_ulid": gen, "brand_ulid": brand,
                "handle": handle, "date": date}
        (self.b / "data" / "publish_confirm_staged.json").write_text(
            json.dumps({"cards": [card]}, ensure_ascii=False), encoding="utf-8")
        return card

    # ── dispatch: a 'published' tap routes to the right handler ──────────────
    def test_resolve_routes_published_tap(self):
        fn = ar._resolve((f"publish_confirm_{GEN}", "published"))
        self.assertIsNotNone(fn, "publish_confirm_* + published must resolve to a handler")
        self.assertEqual(fn.__name__, "h_publish_confirm")

    # ── end-to-end: tap → one ledger event, in the readers' schema ───────────
    def test_tap_records_one_published_event(self):
        self._stage_card()
        row = {"item_id": f"publish_confirm_{GEN}", "answer": "published",
               "ts": "2026-06-22T20:00:00+00:00"}
        fn = ar._resolve((row["item_id"], row["answer"]))
        evidence = fn(self.b, row)                       # exactly what main() does
        self.assertIn("published recorded", evidence)
        rows = ol._read_jsonl(self.b / "data" / "published.jsonl")
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), {"subject_generation_ulid", "brand_ulid", "timestamp"})
        self.assertEqual(rows[0]["subject_generation_ulid"], GEN)
        self.assertEqual(rows[0]["brand_ulid"], BRAND)

    def test_idempotent_second_tap(self):
        self._stage_card()
        row = {"item_id": f"publish_confirm_{GEN}", "answer": "published",
               "ts": "2026-06-22T20:00:00+00:00"}
        fn = ar._resolve((row["item_id"], row["answer"]))
        fn(self.b, row)
        fn(self.b, row)                                  # replay (main() also guards via applied-ledger)
        rows = ol._read_jsonl(self.b / "data" / "published.jsonl")
        self.assertEqual(len(rows), 1, "same generation must not double-append")

    # ── Rule #8 refusals — never half-record ─────────────────────────────────
    def test_refuses_when_no_staged_file(self):
        row = {"item_id": f"publish_confirm_{GEN}", "answer": "published"}
        with self.assertRaises(RuntimeError):
            ar.h_publish_confirm(self.b, row)
        self.assertFalse((self.b / "data" / "published.jsonl").exists())

    def test_refuses_unstaged_card(self):
        self._stage_card()
        row = {"item_id": "publish_confirm_UNKNOWN", "answer": "published"}
        with self.assertRaises(RuntimeError):
            ar.h_publish_confirm(self.b, row)

    def test_refuses_missing_identity(self):
        (self.b / "data" / "publish_confirm_staged.json").write_text(
            json.dumps({"cards": [{"id": "publish_confirm_X", "subject_generation_ulid": "", "brand_ulid": ""}]}),
            encoding="utf-8")
        with self.assertRaises(RuntimeError):
            ar.h_publish_confirm(self.b, {"item_id": "publish_confirm_X", "answer": "published"})

    # ── the builder (producer half) ──────────────────────────────────────────
    def test_builder_stages_one_card_per_post(self):
        man = {"posts": [
            {"subject_generation_ulid": GEN, "brand_ulid": BRAND, "handle": "eatjurisha", "date": "2026-09-23"},
            {"subject_generation_ulid": GEN, "brand_ulid": BRAND, "handle": "eatjurisha", "date": "2026-09-23"},  # dup gen
            {"subject_generation_ulid": "GEN2", "brand_ulid": BRAND, "handle": "albaik", "date": "2026-11-27"},
        ]}
        (self.b / "data" / "batch_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        r = bpc.build(write=True, b=self.b)
        self.assertEqual(r["staged"], 2, "two distinct generations → two cards (dup collapsed)")
        staged = json.loads((self.b / "data" / "publish_confirm_staged.json").read_text())
        ids = {c["id"] for c in staged["cards"]}
        self.assertIn(f"publish_confirm_{GEN}", ids)
        self.assertTrue(all(c["options"][0]["value"] == "published" for c in staged["cards"]))

    def test_builder_skips_post_without_identity(self):
        man = {"posts": [{"handle": "x", "date": "d"}, {"subject_generation_ulid": GEN, "brand_ulid": BRAND}]}
        (self.b / "data" / "batch_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        r = bpc.build(write=True, b=self.b)
        self.assertEqual(r["staged"], 1)
        self.assertEqual(r["skipped"], 1)

    def test_builder_honest_empty_no_manifest(self):
        r = bpc.build(write=True, b=self.b)
        self.assertEqual(r["staged"], 0)

    # ── Rule #7: the builder asserts a consumer exists before staging ────────
    def test_assert_handler_wired_passes(self):
        bpc.assert_handler_wired()  # must not raise — h_publish_confirm is registered

    # ── full round-trip: builder → tap → both readers see it (Rule #6) ───────
    def test_builder_then_tap_then_readers(self):
        man = {"posts": [{"subject_generation_ulid": GEN, "brand_ulid": BRAND,
                          "handle": "eatjurisha", "date": "2026-09-23"}]}
        (self.b / "data" / "batch_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        bpc.build(write=True, b=self.b)
        row = {"item_id": f"publish_confirm_{GEN}", "answer": "published",
               "ts": "2026-06-22T20:00:00+00:00"}
        ar._resolve((row["item_id"], row["answer"]))(self.b, row)
        s = ol.status(path=self.b / "data" / "published.jsonl")
        self.assertEqual(s["n_published"], 1)
        self.assertEqual(s["by_brand"], {BRAND: 1})


if __name__ == "__main__":
    unittest.main()
