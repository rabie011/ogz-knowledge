#!/usr/bin/env python3
"""Pins make_sure's TWO-STRIKE phone gate (June 20 false-ALARM scar, third strike in one morning).

Root scar: the orchestra's session-start fire collided with the enricher+hook stampede; portal_*/
armor_tests timed out on HEALTHY services (every one returned 200 in <0.4s, the suite was green 12
min later) yet a SINGLE red fire instantly paged Mohamed with the urgent alarm card. _probe/_safe_run
retry WITHIN a fire, but a heavy stampede outlasts both tries, so the false RED still reached his
phone — an ADHD-contract / Rule #10 breach (cry-wolf erodes every real alarm).

The fix lives one layer ABOVE the probe: _phone_dead requires a LOAD-SENSITIVE red to PERSIST across
two consecutive fires before it pages him. A real outage stays red on the next fire -> still alarms
(never masked). A transient clears -> never floods him. HARD checks page immediately (no transient
mode). These tests pin that contract."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms


class TestPhoneDead(unittest.TestCase):
    def test_load_sensitive_first_strike_is_suppressed(self):
        """portal red NOW but green (or absent) on the prev fire -> transient -> NOT paged."""
        checks = {"portal_mini": False, "guards_gauntlet": True}
        self.assertEqual(ms._phone_dead(checks, {"portal_mini": True}), [])

    def test_load_sensitive_first_strike_no_prev_history_suppressed(self):
        """First-ever run (no prev entry) -> a load-sensitive red is unconfirmed -> suppressed.
        A genuine outage simply confirms on the very next fire."""
        checks = {"armor_tests": False, "portal_public": False}
        self.assertEqual(ms._phone_dead(checks, {}), [])

    def test_load_sensitive_second_strike_pages(self):
        """Red on BOTH consecutive fires -> a real outage, never masked -> paged."""
        checks = {"portal_public": False, "guards_gauntlet": True}
        self.assertEqual(ms._phone_dead(checks, {"portal_public": False}), ["portal_public"])

    def test_hard_check_pages_immediately_no_second_strike(self):
        """A guards/immune/law red has no transient mode -> pages on the first strike."""
        checks = {"guards_gauntlet": False, "portal_mini": True}
        self.assertEqual(ms._phone_dead(checks, {}), ["guards_gauntlet"])

    def test_mixed_only_confirmed_and_hard_reach_phone(self):
        """A realistic stampede fire: a transient portal red (suppressed) alongside a persisted
        armor red (paged) and a hard immune red (paged). Only the latter two reach him."""
        checks = {"portal_mini": False,    # first strike -> suppress
                  "armor_tests": False,    # persisted -> page
                  "immune_suite": False,   # hard -> page
                  "guards_gauntlet": True}
        prev = {"armor_tests": False, "portal_mini": True}
        self.assertEqual(sorted(ms._phone_dead(checks, prev)), ["armor_tests", "immune_suite"])

    def test_all_green_pages_nothing(self):
        self.assertEqual(ms._phone_dead({"portal_mini": True, "guards_gauntlet": True}, {}), [])

    def test_non_bool_values_never_page(self):
        """The checks dict carries non-bool fields (counts, strings); only literal False pages."""
        checks = {"cards_total": 0, "_taste_gap_days": 4, "portal_mini": True}
        self.assertEqual(ms._phone_dead(checks, {}), [])

    def test_underscore_diagnostic_false_never_pages(self):
        """Scar (June 21): `_`-prefixed diagnostics use INVERTED semantics — the key names a problem
        so False == HEALTHY (e.g. _taste_bridge_starved=False means NOT starved). _phone_dead must
        never page on them, or a healthy state pins a permanent false 🚨 on his phone (Rule #10)."""
        checks = {"_taste_bridge_starved": False,   # healthy (not starved) -> must NOT page
                  "_some_future_flag": False,        # any future inverted diagnostic -> must NOT page
                  "guards_gauntlet": True}
        self.assertEqual(ms._phone_dead(checks, {}), [])

    def test_underscore_diagnostic_does_not_mask_real_hard_red(self):
        """Excluding `_` diagnostics never masks a genuine gate red firing in the same cycle."""
        checks = {"_taste_bridge_starved": False, "immune_suite": False, "guards_gauntlet": True}
        self.assertEqual(ms._phone_dead(checks, {}), ["immune_suite"])


if __name__ == "__main__":
    unittest.main()
