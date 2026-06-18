"""B064 — pick_angle must never raise on a dry key (zero-LLM-first, hard-to-break).

pick_angle() was the only unguarded LLM call in the creative_line path: it called
claude() with no fallback, so a dry Anthropic key raised at angle-selection and killed
the whole producer BEFORE the (already-guarded) render() pen could run. With OpenAI
funded and Anthropic dry — the real key state — the producer could not run end-to-end.

These tests pin the cascade Claude pen → funded GPT pen → deterministic first angle,
without making any real API call (both pens are monkeypatched).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import creative_line


CARDS = {"angles": [
    {"id": 1, "insight_ar": "a", "approach_ar": "x", "formula": "f", "lens": "l"},
    {"id": 2, "insight_ar": "b", "approach_ar": "y", "formula": "f", "lens": "l"},
    {"id": 3, "insight_ar": "c", "approach_ar": "z", "formula": "f", "lens": "l"},
]}


class TestPickAngleFallback(unittest.TestCase):
    def setUp(self):
        self._claude, self._gpt = creative_line.claude, creative_line.gpt

    def tearDown(self):
        creative_line.claude, creative_line.gpt = self._claude, self._gpt

    def _dry(self, *a, **k):
        raise RuntimeError("credit balance too low")

    def test_claude_pen_used_when_alive(self):
        creative_line.claude = lambda *a, **k: "2"
        creative_line.gpt = lambda *a, **k: self.fail("GPT must not be called when Claude alive")
        self.assertEqual(creative_line.pick_angle(CARDS, "national_day")["id"], 2)

    def test_falls_back_to_gpt_when_anthropic_dry(self):
        creative_line.claude = self._dry           # the real June key state
        creative_line.gpt = lambda *a, **k: "3"
        self.assertEqual(creative_line.pick_angle(CARDS, "national_day")["id"], 3)

    def test_deterministic_first_when_both_dry(self):
        creative_line.claude = self._dry
        creative_line.gpt = self._dry
        # must NOT raise — returns the first/highest deterministic card
        self.assertEqual(creative_line.pick_angle(CARDS, "national_day")["id"], 1)

    def test_garbage_pen_output_falls_to_first(self):
        creative_line.claude = lambda *a, **k: "no number here"
        self.assertEqual(creative_line.pick_angle(CARDS, "ramadan")["id"], 1)

    def test_no_angles_returns_none_without_calling_pens(self):
        creative_line.claude = lambda *a, **k: self.fail("no pen call when no angles")
        creative_line.gpt = lambda *a, **k: self.fail("no pen call when no angles")
        self.assertIsNone(creative_line.pick_angle({"angles": []}, "x"))


if __name__ == "__main__":
    unittest.main()
