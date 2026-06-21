#!/usr/bin/env python3
"""Guards the SECTOR-PRIOR AGGREGATOR (B096). The contracts that matter, all on synthetic fixtures
(no live data): (1) Rule #8 gate — n≥3 distinct brands promotes, n=2 HOLDs; (2) Rule #9 no-inflation
— one brand confirming 3× is still ONE brand → no promotion; (3) unconfirmed records are dropped;
(4) anonymization — drafts carry no raw brand name; (5) Rule #6 — staged draft reads back end-to-end."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import sector_prior_aggregator as spa


def _rec(brand, value, sector="f_and_b", field="serving_etiquette", confirmer="mohamed"):
    return {"brand": brand, "sector": sector, "field": field, "value": value, "confirmer": confirmer}


class TestSectorPriorAggregator(unittest.TestCase):
    def test_three_distinct_brands_promote(self):
        recs = [_rec("a", "right_hand"), _rec("b", "right_hand"), _rec("c", "right_hand")]
        drafts = spa.draft_prs(recs)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["n_brands"], 3)
        self.assertEqual(drafts[0]["sector"], "f_and_b")
        self.assertEqual(drafts[0]["status"], "PROVISIONAL")

    def test_two_brands_held_below_floor(self):
        recs = [_rec("a", "right_hand"), _rec("b", "right_hand")]
        self.assertEqual(spa.draft_prs(recs), [])               # Rule #8 — the gate bites
        buckets = spa.aggregate(recs)
        self.assertEqual(len(buckets), 1)
        self.assertFalse(buckets[0]["promoted"])
        self.assertEqual(buckets[0]["n_brands"], 2)

    def test_one_brand_repeated_does_not_inflate(self):
        # same brand confirming the SAME value three times is still ONE brand (Rule #9, fresh-batch scar)
        recs = [_rec("a", "right_hand"), _rec("a", "right_hand"), _rec("a", "right_hand")]
        self.assertEqual(spa.draft_prs(recs), [])
        self.assertEqual(spa.aggregate(recs)[0]["n_brands"], 1)

    def test_unconfirmed_records_dropped(self):
        # 2 confirmed + 1 machine-guessed → only 2 count → HELD
        recs = [_rec("a", "right_hand"), _rec("b", "right_hand"),
                _rec("c", "right_hand", confirmer="machine")]
        self.assertEqual(spa.draft_prs(recs), [])
        self.assertEqual(spa.aggregate(recs)[0]["n_brands"], 2)

    def test_disagreement_splits_buckets(self):
        # 2 say right_hand, 2 say left_hand → two buckets, neither reaches 3 → no promotion
        recs = [_rec("a", "right_hand"), _rec("b", "right_hand"),
                _rec("c", "left_hand"), _rec("d", "left_hand")]
        self.assertEqual(spa.draft_prs(recs), [])
        self.assertEqual(len(spa.aggregate(recs)), 2)

    def test_value_normalization_agrees(self):
        # casefold + trim: 'Right_Hand', ' right_hand ', 'right_hand' are the SAME value
        recs = [_rec("a", "Right_Hand"), _rec("b", " right_hand "), _rec("c", "right_hand")]
        drafts = spa.draft_prs(recs)
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["n_brands"], 3)

    def test_anonymization_hides_brand(self):
        recs = [_rec("albaik", "right_hand"), _rec("jurisha", "right_hand"), _rec("kudu", "right_hand")]
        blob = json.dumps(spa.draft_prs(recs), ensure_ascii=False)
        for raw in ("albaik", "jurisha", "kudu"):
            self.assertNotIn(raw, blob)                          # no raw brand leaks
        self.assertTrue(all(t.startswith("b_") for t in spa.draft_prs(recs)[0]["brands_anon"]))

    def test_write_and_read_back_end_to_end(self):
        # Rule #6 — the writer's output is a real consumable artifact
        recs = [_rec("a", "right_hand"), _rec("b", "right_hand"), _rec("c", "right_hand")]
        drafts = spa.draft_prs(recs)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "drafts.json"
            spa.write_drafts(drafts, path=p)
            back = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(back["n_drafts"], 1)
        self.assertEqual(back["min_brands"], spa.MIN_BRANDS)
        self.assertEqual(back["drafts"][0]["value"], "right_hand")

    def test_scan_clients_is_safe_and_honest(self):
        # the real scanner never crashes and (on prose-only pilot passports) yields no promotions
        recs = spa.scan_clients()
        self.assertIsInstance(recs, list)
        self.assertEqual(spa.draft_prs(recs), [])               # 2-3 pilots, prose answers → 0


if __name__ == "__main__":
    unittest.main()
