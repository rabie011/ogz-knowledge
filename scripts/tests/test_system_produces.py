#!/usr/bin/env python3
"""Enforces Rule #12 (THE SYSTEM PRODUCES): the sanctioned production path must contain NO
hand-authored output — no hardcoded slot-date lists that curate the batch, no DROP/selection
sets, no Arabic caption literals. Output comes from a RUN, not from Claude's hand. The old
hand-curation scripts (gen_aligned20/stage_aligned20/gen_new20/stage_fresh20) are DEPRECATED and
must not be the path that reaches the feedback system."""
import re, unittest
from pathlib import Path

S = Path(__file__).parent.parent
SANCTIONED = ["produce_batch.py", "stage_from_manifest.py"]
DATE = re.compile(r"\"\d{4}-\d{2}-\d{2}\"")
ARABIC_LITERAL = re.compile(r"\"[^\"]*[ء-ي]{4,}[^\"]*\"")


class TestSystemProduces(unittest.TestCase):

    def test_sanctioned_scripts_have_no_hardcoded_dates(self):
        for name in SANCTIONED:
            src = (S / name).read_text()
            dates = DATE.findall(src)
            self.assertEqual(dates, [], f"{name} hardcodes slot dates {dates} — Rule #12: the system picks, not the hand")

    def test_sanctioned_scripts_have_no_drop_or_select_set(self):
        for name in SANCTIONED:
            src = (S / name).read_text()
            self.assertNotIn("DROP =", src, f"{name} has a hardcoded DROP set — Rule #12 forbids hand-curation")
            self.assertNotIn("DROP=", src)

    def test_sanctioned_scripts_have_no_caption_literals(self):
        """No long Arabic string literal (a hand-written caption) in the production path."""
        for name in SANCTIONED:
            src = (S / name).read_text()
            # allow short Arabic in comments; flag long Arabic STRING literals (caption text)
            lits = [s for s in ARABIC_LITERAL.findall(src) if len(s) > 25]
            self.assertEqual(lits, [], f"{name} contains a hand-written caption literal {lits[:1]} — Rule #12")


if __name__ == "__main__":
    unittest.main()
