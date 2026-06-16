#!/usr/bin/env python3
"""Locks the one-at-a-time pairwise surface (June 16): the portal must serve only ONE open pw_ card
at a time (not the 15-card wall), while never hiding an answered card or a non-pw open card."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
import portal_mini as pm


class TestOneAtATime(unittest.TestCase):
    def _queue(self):
        # 3 open pw_ + 2 non-pw open + 2 answered (answered pw_ is slimmed, keeps status)
        return [
            {"id": "pw_a", "status": "open", "created": "1"},
            {"id": "pw_b", "status": "open", "created": "2"},
            {"id": "pw_c", "status": "open", "created": "3"},
            {"id": "card_x", "status": "open", "created": "1"},
            {"id": "card_y", "status": "open", "created": "2"},
            {"id": "pw_done", "status": "answered", "created": "0"},
            {"id": "card_done", "status": "answered", "created": "0"},
        ]

    def test_only_one_open_pw_surfaces(self):
        kept = pm._single_open_pw(self._queue())
        open_pw = [c for c in kept if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(len(open_pw), 1, "more than one open pw_ card served — the wall is back")
        self.assertEqual(open_pw[0]["id"], "pw_a", "surfaced pw_ is not the sort-first")

    def test_non_pw_open_cards_all_preserved(self):
        kept = {c["id"] for c in pm._single_open_pw(self._queue())}
        self.assertIn("card_x", kept); self.assertIn("card_y", kept)

    def test_answered_cards_never_hidden(self):
        kept = {c["id"] for c in pm._single_open_pw(self._queue())}
        self.assertIn("pw_done", kept, "answered pw_ card was hidden — a recorded pick vanished")
        self.assertIn("card_done", kept)

    def test_next_pw_surfaces_after_a_tap(self):
        """Flip the surfaced card to answered → the NEXT open pw_ becomes the one served."""
        q = self._queue()
        q[0]["status"] = "answered"   # pw_a tapped
        kept = pm._single_open_pw(q)
        open_pw = [c for c in kept if c["id"].startswith("pw_") and c["status"] != "answered"]
        self.assertEqual(open_pw[0]["id"], "pw_b", "next pair didn't surface after a tap")


if __name__ == "__main__":
    unittest.main()
