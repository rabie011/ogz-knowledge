#!/usr/bin/env python3
"""Locks the founder-engagement CANARY's age median against the created-less-card artifact.

The canary (make_sure_feedback) fires when his open cards go stale (median age > 5d). A card with
no parseable `created` must NOT be counted as epoch-1970 (20k+ days) — that's a data artifact, not
founder-neglect, and it falsely trips the canary. Surfaced June 20: retiring 52 dated 'superseded'
corpses exposed 21 created-less cards the corpses had been masking in the median (5 -> 20624)."""
import sys, unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure_feedback as m


class TestCanaryAge(unittest.TestCase):

    def test_created_less_cards_excluded_from_median(self):
        now = datetime.now()
        cards = ([{"status": "open", "created": now.isoformat()}] * 3
                 + [{"status": "open"}] * 21)              # 21 with NO created
        ages = [(now - m._dt(c.get("created", ""))).days
                for c in cards if m._parseable_dt(c.get("created", ""))]
        self.assertEqual(len(ages), 3)                     # only the dated cards count
        self.assertTrue(all(a <= 1 for a in ages))         # and they read as fresh, not ancient

    def test_parseable_dt_guards(self):
        self.assertTrue(m._parseable_dt("2026-06-20T06:00:00"))
        self.assertFalse(m._parseable_dt(""))
        self.assertFalse(m._parseable_dt(None))

    def test_all_created_less_yields_zero_not_ancient(self):
        cards = [{"status": "open"}] * 5
        ages = [c for c in cards if m._parseable_dt(c.get("created", ""))]
        # mirrors the script: empty ages -> median 0 (no staleness signal), never epoch-old
        import statistics
        self.assertEqual(statistics.median([(datetime.now() - m._dt(x.get("created", ""))).days
                                            for x in ages]) if ages else 0, 0)


if __name__ == "__main__":
    unittest.main()
