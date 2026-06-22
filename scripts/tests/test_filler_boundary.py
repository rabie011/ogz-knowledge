#!/usr/bin/env python3
"""Boundary guard for the canonical FILLER «رحلة» branch (B196 follow-up, 2026-06-22).

The bilingual filler ban used the bare substring «رحلة», which is the جري-in-جريشة class of
bug (Rule #9, verify-substring-before-reporting) firing in TWO wrong directions, both
eyeballed against the live regex before this fix:

  FALSE POSITIVE — «مرحلة/المرحلة» (phase/stage) contains «رحلة» as a substring, so a perfectly
  legitimate caption about a new PHASE was killed as filler. A guard that kills good captions
  injects a NEW mistake (Rule #13: zero old mistakes — false kills count).

  FALSE NEGATIVE — «رحلتك/رحلتنا/رحلتي» (journey + possessive suffix, ة→ت) leaked the exact
  fitness-filler the ban exists to stop. «بل رحلة» was caught; «رحلتك نحو القوة» was not.

FILLER is the one-module canonical guard (B038) consumed by every writing door (render_client_
slot, creative_line, post_audit caption + visual scans, killchain). Fixing it here fixes all
doors (the one-enforced-boundary scar). These tests keep the boundary honest both ways.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from truth_guards import FILLER  # noqa: E402


class TestFillerBoundary(unittest.TestCase):

    def test_phase_word_not_flagged(self):
        # «مرحلة» (phase/stage) must pass — bare-substring «رحلة» used to fire inside it.
        for legit in ("مرحلة جديدة من القوة", "المرحلة الأولى من التحدي",
                      "في كل مرحلة نتقدم", "بمرحلتك القادمة"):
            self.assertIsNone(FILLER.search(legit),
                              f"false kill: «{legit}» wrongly flagged as filler")

    def test_trip_to_market_exception_preserved(self):
        # the pre-existing «رحلة لسوق» (a real trip to market) exception must still hold.
        self.assertIsNone(FILLER.search("رحلة لسوق الخضار"),
                          "«رحلة لسوق» exception lost in the rewrite")

    def test_bare_journey_still_caught(self):
        # the original catches must not regress.
        for filler in ("إنها ليست مجرد خطوة، بل رحلة", "رحلة القوة تبدأ الآن", "this journey"):
            self.assertIsNotNone(FILLER.search(filler),
                                 f"regression: «{filler}» no longer caught")

    def test_suffixed_journey_now_caught(self):
        # the leak this fix closes: journey + possessive suffix.
        for filler in ("رحلتك نحو القوة", "رحلتنا تبدأ من هنا", "رحلتي مع اللياقة",
                       "رحلتها الملهمة"):
            self.assertIsNotNone(FILLER.search(filler),
                                 f"leak: suffixed filler «{filler}» still escapes")


if __name__ == "__main__":
    unittest.main()
