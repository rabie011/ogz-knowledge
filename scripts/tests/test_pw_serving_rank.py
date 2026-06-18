#!/usr/bin/env python3
"""Locks the pairwise SERVING-RANK wire (Rule #6, June 18). The active/bridge selectors compute an
information-gain ranking of which pair teaches the model most, but the portal served ONE open pw_
card at a time by `created` order — throwing that ranking away at the serving layer (a producer's
ranking the consumer ignored), so Mohamed's scarce taps (the 60-sec gate) drained in push-order, not
value-order. Fix: each pw_ card carries `pw_rank` (bridge=0 unlocks held-out testability, active=1
information gain, random=2) and the portal surfaces the lowest-rank open card, ties → earliest
created. These tests lock both ends of the wire."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))            # scripts/  → pairwise
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))  # api/   → portal_mini
import pairwise as pw
import portal_mini as pm


def _pair(pid, handle, ca, cb, pw_rank=None):
    p = {"id": pid, "handle": handle,
         "a": {"caption": ca}, "b": {"caption": cb}}
    if pw_rank is not None:
        p["pw_rank"] = pw_rank
    return p


class TestCardCarriesRank(unittest.TestCase):
    def test_card_for_stamps_pw_rank(self):
        card = pw._card_for(_pair("pw_x", "albaik", "A", "B", pw_rank=0))
        self.assertEqual(card.get("pw_rank"), 0, "_card_for dropped the producer's pw_rank")

    def test_card_for_defaults_rank_to_random(self):
        card = pw._card_for(_pair("pw_x", "albaik", "A", "B"))  # no rank → random tier
        self.assertEqual(card.get("pw_rank"), 2, "missing pw_rank must default to 2 (random tier)")


class TestPortalServesByRank(unittest.TestCase):
    def _queue(self):
        # created-order would surface pw_random first; rank-order must surface the bridge card.
        return [
            {"id": "pw_random", "status": "open", "created": "1", "pw_rank": 2},
            {"id": "pw_active", "status": "open", "created": "2", "pw_rank": 1},
            {"id": "pw_bridge", "status": "open", "created": "3", "pw_rank": 0},
            {"id": "card_x",    "status": "open", "created": "1"},
            {"id": "pw_done",   "status": "answered", "created": "0"},
        ]

    def test_lowest_rank_surfaces_not_earliest_created(self):
        kept = pm._single_open_pw(self._queue())
        open_pw = [c for c in kept if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(len(open_pw), 1, "more than one open pw_ served — the gate broke")
        self.assertEqual(open_pw[0]["id"], "pw_bridge",
                         "served by created-order, not by pw_rank — the ranking is still thrown away")

    def test_non_pw_and_answered_untouched(self):
        kept = {c["id"] for c in pm._single_open_pw(self._queue())}
        self.assertIn("card_x", kept, "a non-pw open card was hidden")
        self.assertIn("pw_done", kept, "an answered card was hidden — a recorded pick vanished")

    def test_ties_break_by_earliest_created(self):
        q = [
            {"id": "pw_late",  "status": "open", "created": "5", "pw_rank": 0},
            {"id": "pw_early", "status": "open", "created": "2", "pw_rank": 0},
        ]
        open_pw = [c for c in pm._single_open_pw(q)
                   if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(open_pw[0]["id"], "pw_early", "tie not broken by earliest created")

    def test_next_best_surfaces_after_a_tap(self):
        """Bridge tapped → the next-best open pw_ (active, rank 1) surfaces, not the random one."""
        q = self._queue()
        q[2]["status"] = "answered"   # pw_bridge tapped
        open_pw = [c for c in pm._single_open_pw(q)
                   if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(open_pw[0]["id"], "pw_active",
                         "after the bridge tap the next-best (active) pair didn't surface")

    def test_legacy_cards_without_rank_still_served_by_created(self):
        """The live 11 bridge cards predate pw_rank; with no rank field all tie at 2 → created order
        is preserved (no regression for cards already on his portal)."""
        q = [
            {"id": "pw_old_a", "status": "open", "created": "1"},
            {"id": "pw_old_b", "status": "open", "created": "2"},
        ]
        open_pw = [c for c in pm._single_open_pw(q)
                   if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(open_pw[0]["id"], "pw_old_a", "legacy created-order regressed")


if __name__ == "__main__":
    unittest.main()
