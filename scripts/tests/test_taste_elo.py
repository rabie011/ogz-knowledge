#!/usr/bin/env python3
"""Guards the model-free Mohamed-Elo consumer (Step 1, June 15): Bradley-Terry ranks a clear
winner above a clear loser, and the consumer is wired into the tap loop."""
import inspect, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import taste_elo as te
import apply_rulings as ar


class TestTasteElo(unittest.TestCase):
    def test_bradley_terry_ranks_winner_above_loser(self):
        # A beats B 3x, B beats C 3x → strength A > B > C
        pairs = [(0, 1), (0, 1), (0, 1), (1, 2), (1, 2), (1, 2)]
        ids, pi = te.bradley_terry(pairs)
        s = {ids[i]: pi[i] for i in range(len(ids))}
        self.assertGreater(s[0], s[1]); self.assertGreater(s[1], s[2])

    def test_elo_consumer_wired_into_tap_loop(self):
        self.assertIn("taste_elo", inspect.getsource(ar.main),
                      "taste_elo not recomputed after a tap consumes (Rule #6 — the consumer must run)")


if __name__ == "__main__":
    unittest.main()
