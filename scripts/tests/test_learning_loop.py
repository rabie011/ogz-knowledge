#!/usr/bin/env python3
"""Guards that THE SYSTEM learns from Mohamed's verdicts BY ITSELF (2026-06-14 directive:
"make sure THEY learn, not you only"). Prevents the write-only-verdict regression:
  - a consumer for his judge verdicts EXISTS and runs (quality_verdict is not write-only).
  - the loop is WIRED: learn_from_verdict writes the same learned-rules file pre_ship_gate reads.
  - a learned phrase-ban actually reaches the gate (his "no" → a rule → caught next time)."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import learn_from_verdict as lfv
import pre_ship_gate as gate


class TestLearningLoopClosed(unittest.TestCase):

    def test_verdict_consumer_exists_and_runs(self):
        """His judge verdicts have a reader that runs without error (not write-only)."""
        out = lfv.run(dry=True)
        self.assertIn("consumed", out)
        self.assertIsInstance(out["consumed"], int)

    def test_loop_is_wired(self):
        """learn_from_verdict WRITES the exact file pre_ship_gate READS — the wire is connected."""
        self.assertEqual(lfv.LEARNED.resolve(), gate._LF.resolve(),
                         "BROKEN LOOP: learner and gate point at different learned-rules files")

    def test_never_bans_a_product_name(self):
        """Rule #9: the learner once banned 'رز الكابلي' (a product). It must NEVER ban a product."""
        import glob
        prods = set()
        for f in glob.glob(str(Path(__file__).parent.parent.parent / "clients/*/profile/truth_pack.json")):
            for c in json.loads(open(f).read()).get("product_candidates", []):
                n = (c.get("name") or "").strip()
                if n:
                    prods.add(n)
                    prods.add(" ".join(n.split()[:2]))
        bans = gate.LEARNED.get("phrase_bans", [])
        bad = [b for b in bans if b in prods]
        self.assertEqual(bad, [], f"learner banned product name(s): {bad}")

    def test_learned_ban_BLOCKS_shipping(self):
        """A phrase Mohamed rejected must BLOCK shipping next time — not just soft-flag
        (zoom-out 2026-06-14 gap #2: learned bans were REVIEW-only and still shipped)."""
        banned = gate.LEARNED_BANS
        if not banned:
            self.skipTest("no learned bans yet")
        post = {"captions": [banned[0] + " وبقية الجملة"], "idea": {"scene_ar": ""},
                "slot": {"occasion": "evergreen"}}
        v = gate.gate(post, "eatjurisha")
        self.assertTrue(v["block"], "learned ban did NOT block shipping — loop still leaky")
        self.assertTrue(any(banned[0] in f for f in v["soft_flags"]))


if __name__ == "__main__":
    unittest.main()
