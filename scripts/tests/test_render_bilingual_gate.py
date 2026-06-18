"""B044 — the EN-hook+AR-idea bilingual bar is correctly GATED on en_led.

A CONFIRMED taste reward (RABIE's law: 'the validated bilingual pattern: EN hook + AR idea,
not translation'). The producing pen (render_client_slot) must give en_led brands the bilingual
instruction WITH the validated bar example + the fitness-filler ban, and hold every other brand
to Saudi Arabic only. The string used to live inline in render_captions and was untestable — this
locks the gate so a refactor can't silently force EN hooks on Arabic-first brands (or drop them
from English-led ones)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from render_client_slot import _bilingual_clause


class TestBilingualGate(unittest.TestCase):
    def test_en_led_gets_bilingual_bar(self):
        s = _bilingual_clause(True)
        self.assertIn("EN hook", s)
        self.assertIn("NOT translation", s)
        # the validated bar example must survive (it IS the pattern, not decoration)
        self.assertIn("تحرّك مع لياقتي", s)

    def test_en_led_bans_influencer_filler(self):
        s = _bilingual_clause(True)
        self.assertIn("never fitness-influencer filler", s)
        self.assertIn("Feeling strong!", s)  # the named anti-example

    def test_arabic_first_brand_is_arabic_only(self):
        s = _bilingual_clause(False)
        self.assertEqual(s, "Write Saudi Arabic only.")

    def test_arabic_first_never_gets_en_hook(self):
        # the gate's whole job: an Arabic-first brand is NEVER told to write an EN hook
        s = _bilingual_clause(False)
        self.assertNotIn("EN hook", s)
        self.assertNotIn("bilingual", s)


if __name__ == "__main__":
    unittest.main()
