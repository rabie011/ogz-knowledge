#!/usr/bin/env python3
"""B186 — truth-confirm cards: synthetic round-trip (generate → tap → writeback).

Proves the writer+reader pair is whole (Rule #6): a generated card's tap actually
flips the mined candidate on disk, and a reject is recorded (never deleted)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import apply_rulings
import build_truth_confirm_cards as gen


def _fixture(base: Path):
    """A minimal 1-client truth_pack with two unconfirmed candidates + one already-confirmed."""
    prof = base / "clients" / "albaik" / "profile"
    prof.mkdir(parents=True)
    tp = {
        "confirmed": [],
        "product_candidates": [
            {"name": "التوأم", "evidence": "8 own captions",
             "provenance": {"confirmer": "pending_client", "confidence": "experimental"}},
            {"name": "فيليه", "evidence": "5 own captions",
             "provenance": {"confirmer": "pending_client", "confidence": "experimental"}},
            {"name": "بروست (مؤكد)", "evidence": "ratified",
             "provenance": {"confirmer": "mohamed", "confidence": "confirmed"}},
        ],
        "prices": [],
    }
    (prof / "truth_pack.json").write_text(json.dumps(tp, ensure_ascii=False), encoding="utf-8")
    (base / "data").mkdir()


class TruthConfirmRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        _fixture(self.base)
        # generator runs against the temp base
        self.doc = gen.build(self.base)
        (self.base / "data" / "truth_confirm_staged.json").write_text(
            json.dumps(self.doc, ensure_ascii=False), encoding="utf-8")
        self.cards = {c["id"]: c for c in self.doc["cards"]}

    def tearDown(self):
        self.tmp.cleanup()

    def _tp(self):
        return json.loads((self.base / "clients/albaik/profile/truth_pack.json").read_text())

    def _cand(self, name):
        return next(c for c in self._tp()["product_candidates"] if c["name"] == name)

    def test_only_unconfirmed_get_cards(self):
        # 2 unconfirmed candidates → 2 cards; the already-confirmed one gets none.
        names = {c["candidate"] for c in self.doc["cards"]}
        self.assertIn("التوأم", names)
        self.assertIn("فيليه", names)
        self.assertNotIn("بروست (مؤكد)", names)

    def test_confirm_flips_on_disk(self):
        cid = next(c["id"] for c in self.doc["cards"] if c["candidate"] == "التوأم")
        msg = apply_rulings.h_truth_confirm(self.base, {"item_id": cid, "answer": "confirm"})
        prov = self._cand("التوأم")["provenance"]
        self.assertEqual(prov["confirmer"], "mohamed")
        self.assertEqual(prov["confidence"], "confirmed")
        self.assertIn("ratified", msg)

    def test_reject_is_recorded_not_deleted(self):
        cid = next(c["id"] for c in self.doc["cards"] if c["candidate"] == "فيليه")
        apply_rulings.h_truth_confirm(self.base, {"item_id": cid, "answer": "reject"})
        cand = self._cand("فيليه")  # raises if it was deleted
        self.assertEqual(cand["provenance"]["confidence"], "rejected")
        self.assertEqual(cand["provenance"]["confirmer"], "mohamed")

    def test_resolve_routes_truth_confirm(self):
        # the router must dispatch truth_confirm_* (confirm AND reject AND free-text) to the handler
        for ans in ("confirm", "reject", "جريش فردي 18"):
            self.assertIs(apply_rulings._resolve(("truth_confirm_albaik_0", ans)),
                          apply_rulings.h_truth_confirm)

    def test_unknown_card_raises(self):
        with self.assertRaises(RuntimeError):
            apply_rulings.h_truth_confirm(self.base, {"item_id": "truth_confirm_ghost_9", "answer": "confirm"})


if __name__ == "__main__":
    unittest.main()
