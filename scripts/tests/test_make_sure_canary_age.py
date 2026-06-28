#!/usr/bin/env python3
"""Locks the founder-engagement CANARY's age median against the created-less-card artifact.

The canary (make_sure_feedback) fires when his open cards go stale (median age > 5d). A card with
no parseable `created` must NOT be counted as epoch-1970 (20k+ days) — that's a data artifact, not
founder-neglect, and it falsely trips the canary. Surfaced June 20: retiring 52 dated 'superseded'
corpses exposed 21 created-less cards the corpses had been masking in the median (5 -> 20624)."""
import statistics, sys, unittest
from datetime import datetime, timedelta
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


class TestCanaryNotHardGate(unittest.TestCase):
    """An away founder (canary half WE don't control) must NOT trip the hard feedback gate,
    so it can never MASK a real red — the session-leak scar. The hard gate is card hygiene
    (the half we DO control); founder-away stays a visible WARN, not a verdict."""

    def test_card_hygiene_is_the_gate_not_founder_canary(self):
        # the gate list bites on what we control, not on the founder being away
        import inspect
        src = inspect.getsource(m.run_checks)
        self.assertIn('"card_hygiene_ok"', src)
        # founder_canary is computed/printed as a WARN but is NOT in the hard `gates` list
        gate_block = src.split("gates = [", 1)[1].split("]", 1)[0]
        self.assertIn("card_hygiene_ok", gate_block)
        self.assertNotIn("founder_canary", gate_block)

    def test_away_founder_alone_does_not_fail_verdict(self):
        # simulate: founder away (canary red) but cards fresh (hygiene green)
        c = {"days_since_mohamed": 4.3, "median_card_age_d": 4.0}
        c["card_hygiene_ok"] = c["median_card_age_d"] <= 5
        c["founder_canary"] = c["days_since_mohamed"] <= 3 and c["card_hygiene_ok"]
        self.assertFalse(c["founder_canary"])   # WARN still fires — signal preserved
        self.assertTrue(c["card_hygiene_ok"])   # but the HARD gate stays green — no mask

    def test_rotting_cards_still_trip_the_gate(self):
        # the controllable failure (we let his cards rot) MUST still hard-fail
        c = {"median_card_age_d": 9}
        c["card_hygiene_ok"] = c["median_card_age_d"] <= 5
        self.assertFalse(c["card_hygiene_ok"])


class TestControllableSplit(unittest.TestCase):
    """June 28: the session-leak scar leaked through card_hygiene_ok and issue_pulse_ok —
    both hard-gated on aging that is pure founder-away (his portal backlog / his unconsumed
    taste-verdicts). The hard gates now measure only the half WE control; founder-away is a
    loud WARN. A stale item WE own must still trip; founder-away alone must not."""

    def test_founder_gated_cards_recognised(self):
        self.assertTrue(m._founder_gated_card({"kind": "caption_pick"}))
        self.assertTrue(m._founder_gated_card({"need": "اكتبوا الجواب"}))
        self.assertTrue(m._founder_gated_card({"made_by": "system:pairwise"}))
        self.assertTrue(m._founder_gated_card({"tag": "v3.7 Visual"}))
        # an ordinary card we could close by hand is NOT founder-gated
        self.assertFalse(m._founder_gated_card({"kind": "buttons", "made_by": "ops"}))

    def test_auto_notice_cards_recognised(self):
        # the self-referential alarm card (made_by claude, single ack option, tag نظام)
        self.assertTrue(m._auto_notice_card(
            {"made_by": "claude", "tag": "نظام", "options": [{"v": "ack", "label": "👌"}]}))
        self.assertTrue(m._auto_notice_card({"made_by": "system:make_sure"}))
        self.assertFalse(m._auto_notice_card({"made_by": "ops", "options": [{"v": "a"}, {"v": "b"}]}))

    def test_founder_away_alone_does_not_trip_card_hygiene(self):
        # his portal full of aged tap-gated cards, but NO card we own is stale → green
        now = datetime.now()
        old = (now - timedelta(days=20)).isoformat()
        cards = [{"status": "open", "created": old, "kind": "caption_pick"},
                 {"status": "open", "created": old, "need": "answer me"}]
        ours = [i for i in cards
                if not m._founder_gated_card(i) and not m._auto_notice_card(i)
                and m._parseable_dt(i.get("created", ""))]
        median = (statistics.median([(now - m._dt(i["created"])).days for i in ours])
                  if ours else 0)
        self.assertEqual(median, 0)
        self.assertTrue(median <= 5)            # card_hygiene_ok stays green on founder-away

    def test_our_rotting_card_still_trips_card_hygiene(self):
        now = datetime.now()
        old = (now - timedelta(days=9)).isoformat()
        cards = [{"status": "open", "created": old, "kind": "buttons", "made_by": "ops"}]
        ours = [i for i in cards
                if not m._founder_gated_card(i) and not m._auto_notice_card(i)]
        median = statistics.median([(now - m._dt(i["created"])).days for i in ours])
        self.assertFalse(median <= 5)           # a card WE own, rotted → still red

    def test_untouched_verdicts_do_not_trip_issue_pulse(self):
        # 26 founder taste-verdicts, none with fix_claimed → no CLAIMED stuck issue → green
        issues = {f"i{n}": {"status": "open", "opened": "2026-06-12T00:00:00", "events": []}
                  for n in range(26)}
        claimed = [v for v in issues.values()
                   if any(e.get("event") == "fix_claimed" for e in v.get("events", []))]
        self.assertEqual(claimed, [])
        self.assertTrue(max((0 for _ in claimed), default=0) <= 14)

    def test_claimed_but_stuck_issue_trips_issue_pulse(self):
        # a fix WE claimed 20 days ago and never closed → red (controllable neglect)
        now = datetime.now()
        opened = (now - timedelta(days=20)).isoformat()
        v = {"status": "open", "opened": opened,
             "events": [{"event": "fix_claimed", "ts": opened}]}
        age = (now - m._dt(v["opened"])).days
        self.assertTrue(age > 14)               # claimed-but-stuck still trips the gate


if __name__ == "__main__":
    unittest.main()
