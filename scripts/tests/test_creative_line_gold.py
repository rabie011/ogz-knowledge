"""B040 — creative_line render() must lead the voice few-shot with founder gold (Rule #6).

Before this, render() built the voice reference from dna.exemplars ONLY; the founder's
rating>=4 captions (his strongest taste signal) never reached the angle-render pen. These
tests pin the gold-first behaviour, the rating>=4 filter, dedup, and v5_prompt-matching
occasion rotation — without touching any LLM.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from creative_line import gold_lead_voice


class TestGoldLeadVoice(unittest.TestCase):
    def _base(self, brand, gold):
        d = Path(tempfile.mkdtemp())
        (d / "logs" / "brand_gold").mkdir(parents=True)
        (d / "logs" / "brand_gold" / f"{brand}_gold.json").write_text(
            json.dumps(gold, ensure_ascii=False))
        return d

    def test_gold_leads_and_exemplars_fill(self):
        base = self._base("acme", [
            {"caption": "GOLD-A", "occasion": "national_day", "rating": 5},
            {"caption": "GOLD-B", "occasion": "national_day", "rating": 4},
        ])
        dna = {"exemplars": [{"caption": "EX-1"}, {"caption": "EX-2"}, {"caption": "EX-3"}]}
        out = gold_lead_voice("acme", "national_day", dna, base=base, n=5)
        self.assertEqual(out[:2], ["GOLD-A", "GOLD-B"])   # gold leads
        self.assertEqual(out, ["GOLD-A", "GOLD-B", "EX-1", "EX-2", "EX-3"])

    def test_rating_below_4_excluded(self):
        base = self._base("acme", [
            {"caption": "GOLD-A", "occasion": "x", "rating": 5},
            {"caption": "WEAK", "occasion": "x", "rating": 3},
        ])
        out = gold_lead_voice("acme", "x", {"exemplars": [{"caption": "EX-1"}]}, base=base, n=5)
        self.assertIn("GOLD-A", out)
        self.assertNotIn("WEAK", out)

    def test_no_gold_file_falls_back_to_exemplars(self):
        base = Path(tempfile.mkdtemp())  # no gold file
        dna = {"exemplars": [{"caption": "EX-1"}, {"caption": "EX-2"}]}
        out = gold_lead_voice("nobody", "x", dna, base=base, n=5)
        self.assertEqual(out, ["EX-1", "EX-2"])

    def test_dedup_gold_not_repeated_from_exemplars(self):
        base = self._base("acme", [{"caption": "DUP", "occasion": "x", "rating": 5}])
        dna = {"exemplars": [{"caption": "DUP"}, {"caption": "EX-2"}]}
        out = gold_lead_voice("acme", "x", dna, base=base, n=5)
        self.assertEqual(out.count("DUP"), 1)
        self.assertEqual(out, ["DUP", "EX-2"])

    def test_rotation_matches_v5_prompt_when_more_than_three_gold(self):
        gold = [{"caption": f"G{i}", "occasion": "x", "rating": 5} for i in range(5)]
        base = self._base("acme", gold)
        out = gold_lead_voice("acme", "national_day", {"exemplars": []}, base=base, n=3)
        h = sum(ord(c) for c in "national_day")
        expected = [f"G{(h + j) % 5}" for j in range(3)]
        self.assertEqual(out, expected)
        self.assertEqual(len(out), 3)


if __name__ == "__main__":
    unittest.main()
