"""Tests for B173 format-fit gap (deterministic classifier + Rule #8 refuse-guard).

Synthetic fixtures only (no LLM, no live-data dependence beyond a smoke pass).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import format_fit_gap as ff  # noqa: E402


CHAINS = [
    {"output_type": "image"},
    {"output_type": "image"},
    {"output_type": "carousel"},
    {"output_type": "video"},
    {"output_type": "IMAGE"},          # case-insensitive
    {"output_type": "hologram"},       # unknown -> uncredited
]
# 3 single-visual feed posts, 1 multi-frame carousel, 1 visual-less (uncountable)
POSTS = [
    {"visual": {"pro_chain": "x"}},
    {"visual": {"phone_shoot_card": "y"}},
    {"visual": "single-string-asset"},
    {"visual": {"frames": [1, 2, 3]}},
    {"visual": None},
]


class TestFormatFitGap(unittest.TestCase):
    def test_classify_chain(self):
        self.assertEqual(ff.classify_chain("image"), "feed_single")
        self.assertEqual(ff.classify_chain("IMAGE"), "feed_single")
        self.assertEqual(ff.classify_chain("carousel"), "carousel")
        self.assertEqual(ff.classify_chain("video"), "reel")
        self.assertIsNone(ff.classify_chain("hologram"))
        self.assertIsNone(ff.classify_chain(None))

    def test_classify_post_structural(self):
        self.assertEqual(ff.classify_post({"visual": {"pro_chain": "x"}}), "feed_single")
        self.assertEqual(ff.classify_post({"visual": "s"}), "feed_single")
        self.assertEqual(ff.classify_post({"visual": {"frames": [1, 2]}}), "carousel")
        self.assertEqual(ff.classify_post({"visual": [1, 2]}), "carousel")
        self.assertIsNone(ff.classify_post({"visual": None}))
        # a single-frame "frames" list is NOT a carousel
        self.assertEqual(ff.classify_post({"visual": {"frames": [1]}}), "feed_single")

    def test_build_gap_counts(self):
        r = ff.build_gap(chains=CHAINS, posts=POSTS)
        s = r["surfaces"]
        self.assertEqual(s["feed_single"]["supply_chains"], 3)   # image,image,IMAGE
        self.assertEqual(s["carousel"]["supply_chains"], 1)
        self.assertEqual(s["reel"]["supply_chains"], 1)
        self.assertEqual(s["story"]["supply_chains"], 0)
        self.assertEqual(r["totals"]["uncredited_chains"], 1)    # hologram
        self.assertEqual(s["feed_single"]["produced_posts"], 3)
        self.assertEqual(s["carousel"]["produced_posts"], 1)
        self.assertEqual(r["totals"]["uncountable_posts"], 1)    # visual None

    def test_status_verdicts(self):
        r = ff.build_gap(chains=CHAINS, posts=POSTS)
        s = r["surfaces"]
        self.assertEqual(s["feed_single"]["status"], "LIVE")     # supply>0, produced>0
        self.assertEqual(s["carousel"]["status"], "LIVE")        # supply 1, produced 1
        self.assertEqual(s["reel"]["status"], "DARK")            # supply 1, produced 0
        self.assertEqual(s["story"]["status"], "STARVED")        # supply 0
        self.assertIn("reel", r["dark"])
        self.assertIn("story", r["starved"])

    def test_verify_clean_on_fixture(self):
        r = ff.build_gap(chains=CHAINS, posts=POSTS)
        self.assertEqual(ff.verify(r), [])

    def test_verify_catches_impossible_production(self):
        bad = ff.build_gap(chains=CHAINS, posts=POSTS)
        # forge a surface that ships posts with zero supply
        bad["surfaces"]["story"] = {"supply_chains": 0, "produced_posts": 5, "status": "STARVED"}
        errs = ff.verify(bad)
        self.assertTrue(any("ZERO supply" in e for e in errs), errs)

    def test_verify_catches_count_mismatch(self):
        bad = ff.build_gap(chains=CHAINS, posts=POSTS)
        bad["totals"]["chains"] = 999
        self.assertTrue(ff.verify(bad), "should catch supply/total mismatch")

    def test_live_data_smoke(self):
        # the real organ must build and self-verify clean on live data
        r = ff.build_gap()
        self.assertEqual(ff.verify(r), [], "live format-fit report is inconsistent")
        self.assertGreater(r["totals"]["chains"], 0)
        self.assertGreater(r["totals"]["posts"], 0)


if __name__ == "__main__":
    unittest.main()
