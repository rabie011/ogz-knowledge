"""B166 — the Maps-reviews CONSUMER is wired into the audience mirror (Rule #6).
fetch_delivery_reviews.py writes raw/maps_reviews/<date>/reviews.jsonl; build_audience_mirror
must READ it (a fetcher with no reader is a severed wire). These tests exercise the pure reader
offline — no LLM, no network, no money."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from build_audience_mirror import latest_maps_reviews


class TestMapsReviewsConsumer(unittest.TestCase):
    def test_reads_newest_day_both_keys_drops_blanks(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = Path(td)
            old = cdir / "raw/maps_reviews/2026-05-01"
            new = cdir / "raw/maps_reviews/2026-06-01"
            old.mkdir(parents=True)
            new.mkdir(parents=True)
            (old / "reviews.jsonl").write_text(
                json.dumps({"text": "قديم لا يُقرأ"}, ensure_ascii=False) + "\n", encoding="utf-8")
            (new / "reviews.jsonl").write_text(
                json.dumps({"text": "لذيذ جدا"}, ensure_ascii=False) + "\n"
                + json.dumps({"reviewText": "خدمة بطيئة"}, ensure_ascii=False) + "\n"
                + json.dumps({"text": "   "}, ensure_ascii=False) + "\n",  # blank dropped
                encoding="utf-8")
            got = latest_maps_reviews(cdir)
            # newest day only, both key variants, blank dropped, order preserved
            self.assertEqual(got, ["لذيذ جدا", "خدمة بطيئة"])

    def test_missing_surface_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(latest_maps_reviews(Path(td)), [])

    def test_empty_dir_no_jsonl_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "raw/maps_reviews/2026-06-01").mkdir(parents=True)
            self.assertEqual(latest_maps_reviews(Path(td)), [])


if __name__ == "__main__":
    unittest.main()
