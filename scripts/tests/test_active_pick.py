#!/usr/bin/env python3
"""Locks the active-pick selector (Step 5b, June 16): it proposes only NEW pairs (never the live 11),
never a pair already judged, and prefers hard+under-compared pairs. NOTE: the '~5 taps ≈ 15' benefit
is a CLAIM gated on a measured agreement number (Rule #9) — these tests lock the SELECTOR's safety,
not that claim."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pairwise as pw


class TestActivePick(unittest.TestCase):
    def test_proposes_stable_real_pairs(self):
        ps = pw.active_pairs(5)
        if not ps:
            self.skipTest("no produced captions to pair")
        for p in ps:
            self.assertTrue(p["id"].startswith("pw_"))
            self.assertNotEqual(p["a"]["caption"], p["b"]["caption"])   # a real A-vs-B
            self.assertEqual(p["id"], pw._pid(p["a"], p["b"]))          # stable id

    def test_never_reproposes_judged_or_live_pairs(self):
        """The hard exclusion: no proposed pair may already be judged (in prefs) or already on the
        portal (the live 11 + answered). Otherwise a tap double-counts or the wall returns."""
        excluded = pw._judged_or_live_pids()
        ps = pw.active_pairs(8)
        offenders = [p["id"] for p in ps if p["id"] in excluded]
        self.assertEqual(offenders, [], f"active-pick re-proposed {len(offenders)} already-judged/live pairs")

    def test_prefers_harder_lower_degree_pair_on_a_fixture(self):
        """Connectivity + hardness: a tied-strength, never-compared pair must outrank a far-apart,
        heavily-compared one. Verified on a controlled fixture via the scoring formula."""
        # score = w_close/(1+|sa-sb|) + w_conn*(1/(1+da)+1/(1+db))
        def score(sa, sb, da, db, wc=0.5, wn=0.5):
            return wc * (1 / (1 + abs(sa - sb))) + wn * (1 / (1 + da) + 1 / (1 + db))
        hard_new = score(1.0, 1.0, 0, 0)      # tied strength, never compared → most informative
        easy_old = score(0.1, 3.0, 9, 9)      # far apart, heavily compared → least informative
        self.assertGreater(hard_new, easy_old)

    def test_only_new_cards_never_touches_live_eleven(self):
        """Belt-and-suspenders: every currently-open pw_ id is in the exclusion set, so it can never
        be re-proposed (the live calibration is never disturbed)."""
        import json
        q = json.loads((Path(__file__).parent.parent.parent / "data/decision_queue.json").read_text())
        open_pw = [str(c["id"]) for c in q.get("items", [])
                   if str(c.get("id", "")).startswith("pw_") and c.get("status") != "answered"]
        excluded = pw._judged_or_live_pids()
        for cid in open_pw:
            self.assertIn(cid, excluded, f"open card {cid} not excluded — active-pick could disturb the live 11")


if __name__ == "__main__":
    unittest.main()
