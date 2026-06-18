#!/usr/bin/env python3
"""Guards the TASTE→CREATION wire — the reader for taste_elo's write-only strengths (Rule #6,
June 18). The contract that matters: the gate stays CLOSED while his picks are unverified, so an
untrusted signal never steers what Mohamed sees (Rules #9/#12/#13); and it OPENS only when the
held-out LIVE test proves out. Also a live end-to-end check against the real taste_elo.json."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import taste_rank as tr


# A clearly-separated taste signal: caption A strong, B weak.
STRONG = {"strengths": {"A his eye loves": 1.4, "B he rejects": -1.2},
          "n_comparisons": {"A his eye loves": 4, "B he rejects": 4}}


class TestTasteRank(unittest.TestCase):
    def test_gate_closed_while_degenerate(self):
        """The live scar: held-out LIVE undefined (0 testable, degenerate). Gate MUST be closed —
        no unverified number steers production (Rule #9)."""
        t = {**STRONG, "held_out_live_n_testable": 0, "held_out_live_pct": None,
             "held_out_agreement_degenerate": True}
        self.assertFalse(tr.wire_live(t))

    def test_gate_closed_below_thresholds(self):
        t = {**STRONG, "held_out_live_n_testable": 3, "held_out_live_pct": 55,
             "held_out_agreement_degenerate": False}
        self.assertFalse(tr.wire_live(t))  # 3 < MIN_TESTABLE and 55 < MIN_LIVE_PCT

    def test_gate_opens_when_proven(self):
        t = {**STRONG, "held_out_live_n_testable": 6, "held_out_live_pct": 70,
             "held_out_agreement_degenerate": False}
        self.assertTrue(tr.wire_live(t))

    def test_closed_gate_does_not_reorder(self):
        """Below the gate, candidates ship in ORIGINAL order — taste steers nothing (Rule #8:
        the influence path is closed, not whispering)."""
        t = {**STRONG, "held_out_live_n_testable": 0, "held_out_live_pct": None,
             "held_out_agreement_degenerate": True}
        cands = ["B he rejects", "A his eye loves"]  # weak first on purpose
        ordered, meta = tr.select(cands, t)
        self.assertEqual(ordered, cands)            # untouched
        self.assertFalse(meta["wire_live"])
        self.assertEqual(meta["advisory_rank"][0], "A his eye loves")  # advisory still ranks correctly

    def test_open_gate_reorders_by_strength(self):
        t = {**STRONG, "held_out_live_n_testable": 6, "held_out_live_pct": 70,
             "held_out_agreement_degenerate": False}
        ordered, meta = tr.select(["B he rejects", "A his eye loves"], t)
        self.assertEqual(ordered[0], "A his eye loves")  # the system selects by computed rule
        self.assertTrue(meta["wire_live"])

    def test_unseen_caption_sorts_after_known(self):
        t = {**STRONG, "held_out_live_n_testable": 6, "held_out_live_pct": 70,
             "held_out_agreement_degenerate": False}
        rows = tr.rank_candidates(["never seen", "A his eye loves"], t)
        self.assertEqual(rows[0]["caption"], "A his eye loves")
        self.assertIsNone(rows[1]["strength"])  # unknown is None, not zero

    def test_live_end_to_end_gate_is_closed_today(self):
        """Reads the REAL taste_elo.json on disk. Today the bridge taps are still staged, so the
        wire MUST report SHADOW — proves the organ is read and the gate honestly reflects reality."""
        t = tr.load_taste()
        if not t:
            self.skipTest("taste_elo.json not computed")
        self.assertEqual(tr.wire_live(t), tr.MIN_TESTABLE <= (t.get("held_out_live_n_testable", 0) or 0)
                         and (t.get("held_out_live_pct") or 0) >= tr.MIN_LIVE_PCT
                         and not t.get("held_out_agreement_degenerate"))


if __name__ == "__main__":
    unittest.main()
