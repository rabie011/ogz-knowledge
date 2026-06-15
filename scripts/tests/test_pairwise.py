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

    def test_writer_and_reader_same_file(self):
        """Consumer Law (June 15 severed-wire scar): the file the PORTAL writes taps to MUST be the
        file consume() reads, or every live pick is silently lost."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("portal_mini", Path(__file__).parent.parent.parent / "api/portal_mini.py")
        # read the portal's ANSWERS path textually (avoid importing the FastAPI app)
        psrc = (Path(__file__).parent.parent.parent / "api/portal_mini.py").read_text()
        self.assertIn("mohamed_answers.jsonl", psrc, "portal answer file changed")
        self.assertTrue(pw.ANSWERS.name == "mohamed_answers.jsonl",
                        f"consume() reads {pw.ANSWERS.name} but the portal writes mohamed_answers.jsonl — severed wire")


if __name__ == "__main__":
    unittest.main()
