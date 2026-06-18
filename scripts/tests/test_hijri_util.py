"""Tests for the Hijri occasion helper (B047). Asserts Ramadan is detected from the Hijri
calendar across MULTIPLE Gregorian years — the exact failure the old hardcoded 2027-only
window had (it mislabelled 2026 Ramadan days as ordinary evergreen)."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hijri_util import in_ramadan, hijri_month  # noqa: E402


class TestHijriRamadan(unittest.TestCase):
    def test_ramadan_detected_across_years(self):
        # Ramadan 1446 ~ Mar 2025, 1447 ~ Feb-Mar 2026, 1448 ~ Feb-Mar 2027.
        # One representative mid-Ramadan day per year — all must be True.
        for d in (datetime.date(2025, 3, 10),
                  datetime.date(2026, 2, 25),
                  datetime.date(2027, 2, 20)):
            self.assertTrue(in_ramadan(d), f"{d} should be in Ramadan")

    def test_non_ramadan_days(self):
        for d in (datetime.date(2025, 6, 1),
                  datetime.date(2026, 1, 1),
                  datetime.date(2026, 12, 1)):
            self.assertFalse(in_ramadan(d), f"{d} should NOT be in Ramadan")

    def test_old_hardcoded_window_was_wrong_for_2026(self):
        # The scar: old code used date(2027,2,8)..date(2027,3,8). A 2026 Ramadan day fell
        # outside it and was wrongly treated as evergreen. The Hijri helper gets it right.
        d_2026_ramadan = datetime.date(2026, 2, 25)
        old_window = datetime.date(2027, 2, 8) <= d_2026_ramadan <= datetime.date(2027, 3, 8)
        self.assertFalse(old_window)          # old logic: missed it
        self.assertTrue(in_ramadan(d_2026_ramadan))  # new logic: catches it

    def test_hijri_month_range(self):
        self.assertTrue(1 <= hijri_month(datetime.date(2026, 6, 18)) <= 12)


if __name__ == "__main__":
    unittest.main()
