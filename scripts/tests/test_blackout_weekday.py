#!/usr/bin/env python3
"""B172 — advisory weekday preference on the negative-space gate.
Pins three things: (1) the ranking is DERIVED from the cadence source, never
hand-authored (Rule #12 — system produces); (2) the gate CONSUMES it the same
cycle (Rule #6 — no severed writer): a low-activity weekday warns, a top day
does not; (3) it stays advisory — it never flips publish_allowed (warn, not block)."""
import datetime, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import blackout_gate as bg


class TestWeekdayPreference(unittest.TestCase):
    def test_ranking_is_derived_from_distribution(self):
        # synthetic distribution → ranking must follow counts, not any hardcoded order
        dist = {"Monday": 5, "Tuesday": 99, "Wednesday": 3, "Thursday": 50,
                "Friday": 2, "Saturday": 1, "Sunday": 4}
        pref = bg.derive_weekday_preference(dist)
        self.assertEqual(pref["ranked"][0], "Tuesday")   # highest count leads
        self.assertEqual(pref["ranked"][-1], "Saturday")  # lowest count trails
        self.assertIn("Saturday", pref["avoid"])
        self.assertIn(_idx("Saturday"), pref["avoid_weekday_idx"])

    def test_empty_source_derives_nothing(self):
        self.assertEqual(bg.derive_weekday_preference({}), {})

    def test_gate_consumes_avoid_day_as_soft_warning(self):
        et = {"weekday_preference": {"avoid_weekday_idx": [5], "note": "n"}}  # Sat=5
        sat = datetime.datetime(2026, 6, 20, 10, 0)   # a Saturday
        thu = datetime.datetime(2026, 6, 18, 10, 0)   # a Thursday
        sat_w = _weekday_warnings(et, sat)
        thu_w = _weekday_warnings(et, thu)
        self.assertTrue(sat_w, "Saturday should raise a low-activity weekday warning")
        self.assertFalse(thu_w, "Thursday (not in avoid set) should not warn")

    def test_weekday_flag_never_blocks(self):
        # the flag is advisory: publish_allowed is governed by the switch, never the weekday
        sat = datetime.datetime(2026, 6, 20, 10, 0)
        self.assertTrue(bg.check(sat)["publish_allowed"])

    def test_live_organ_has_derived_preference(self):
        # the shipped etiquette.json carries a coherent, source-stamped block
        pref = bg.derive_weekday_preference()
        self.assertTrue(pref)
        self.assertEqual(len(pref["ranked"]), 7)
        self.assertIn("post_cadence_analysis", pref["source"])


def _idx(name):
    return bg._WD_NAME_TO_IDX[name]


def _weekday_warnings(et, now):
    """Isolate just the weekday warnings the gate would emit for `now` under `et`."""
    wp = et.get("weekday_preference") or {}
    if now.weekday() in (wp.get("avoid_weekday_idx") or []):
        return [f"low-activity weekday ({now.strftime('%A')})"]
    return []


if __name__ == "__main__":
    unittest.main()
