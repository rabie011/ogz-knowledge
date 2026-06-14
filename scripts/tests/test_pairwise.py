#!/usr/bin/env python3
"""Guards the pairwise taste-calibration loop (the moat, 2026-06-14). Locks: pairs form with stable
ids from real pilot output; the A/B pick has a HANDLER in apply_rulings so it can never sit
UNCONSUMED (Rule #6/#7); and the pairwise consumer is wired into apply_rulings.main()."""
import inspect, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pairwise as pw
import apply_rulings as ar


class TestPairwiseLoop(unittest.TestCase):

    def test_pairs_form_with_stable_ids(self):
        pairs = pw.form_pairs(2)
        if not pairs:
            self.skipTest("no produced captions to pair")
        p = pairs[0]
        self.assertTrue(p["id"].startswith("pw_"))
        self.assertIn("caption", p["a"])
        self.assertIn("caption", p["b"])
        self.assertNotEqual(p["a"]["caption"], p["b"]["caption"])  # a real A-vs-B
        # id is deterministic (same pair → same id)
        self.assertEqual(p["id"], pw._pid(p["a"], p["b"]))

    def test_pick_has_a_handler_never_unconsumed(self):
        """Rule #6/#7: a pw_ pick must resolve to a handler so apply_rulings doesn't flag UNCONSUMED."""
        fn = ar._resolve(("pw_abc123", "A"))
        self.assertIsNotNone(fn, "pairwise pick has NO handler — it would sit UNCONSUMED")

    def test_consumer_wired_into_apply_rulings(self):
        src = inspect.getsource(ar.main)
        self.assertIn("pairwise", src, "pairwise.consume() not wired into apply_rulings.main()")


if __name__ == "__main__":
    unittest.main()
