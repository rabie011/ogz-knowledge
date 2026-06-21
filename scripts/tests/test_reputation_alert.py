#!/usr/bin/env python3
"""B164 — reputation_alert + warm-kitchen WARN. Tests the divergence detector and both
consumers (gap_report block + post_audit WARN). Counts, never feelings (Rule #9)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import reputation_alert as ra
import post_audit

# Synthetic digests modeled on the real shapes (albaik cold / eatjurisha clean / weak-star brand).
COLD = {"handle": "coldbrand", "total": 997, "with_text": 514,
        "stars": {"5": 641, "4": 82, "3": 35, "2": 30, "1": 209},
        "complaints": {"service": 44, "cold_food": 11}}
CLEAN = {"handle": "cleanbrand", "total": 60, "with_text": 35,
         "stars": {"5": 48, "4": 5, "3": 2, "2": 1, "1": 4},
         "complaints": {"service": 3, "cold_food": 0}}
WEAK = {"handle": "weakbrand", "total": 120, "with_text": 90,
        "stars": {"5": 10, "4": 10, "3": 20, "2": 30, "1": 50},
        "complaints": {"service": 2, "cold_food": 1}}


class TestComputeTriggers(unittest.TestCase):
    def test_avg_stars(self):
        self.assertAlmostEqual(ra.avg_stars(COLD["stars"]), 3.92, places=2)
        self.assertIsNone(ra.avg_stars({"5": 0, "1": 0}))

    def test_cold_door_triggers(self):
        a = ra.compute({"coldbrand": COLD})
        self.assertIn("coldbrand", a)
        self.assertIn("cold_door", a["coldbrand"]["triggers"])
        # avg 3.92 ≥ 3.5 → NOT a weak_star trigger, only cold_door
        self.assertNotIn("weak_star", a["coldbrand"]["triggers"])

    def test_clean_brand_no_alert(self):
        self.assertEqual(ra.compute({"cleanbrand": CLEAN}), {})

    def test_weak_star_triggers(self):
        a = ra.compute({"weakbrand": WEAK})
        self.assertIn("weak_star", a["weakbrand"]["triggers"])
        # cold_food 1 < 5 absolute → cold_door must NOT fire
        self.assertNotIn("cold_door", a["weakbrand"]["triggers"])

    def test_cold_below_threshold_no_trigger(self):
        d = dict(COLD); d["complaints"] = {"cold_food": 4}  # 4 < 5 absolute
        self.assertNotIn("coldbrand", ra.compute({"coldbrand": d}))


class TestWarmKitchenWarn(unittest.TestCase):
    def setUp(self):
        self.alerts = ra.compute({"coldbrand": COLD})  # has cold_door

    def test_warm_caption_on_cold_brand_warns(self):
        self.assertIsNotNone(
            ra.warm_kitchen_warn("coldbrand", "دجاج ساخن طازج من الفرن", self.alerts))

    def test_neutral_caption_no_warn(self):
        self.assertIsNone(
            ra.warm_kitchen_warn("coldbrand", "وجبة الغداء بنكهتها الأصيلة", self.alerts))

    def test_warm_caption_on_unalerted_brand_no_warn(self):
        self.assertIsNone(
            ra.warm_kitchen_warn("cleanbrand", "دجاج ساخن طازج من الفرن", self.alerts))

    def test_for_post_scans_all_caps(self):
        caps = ["نص عادي", "خارج الفرن مباشرة"]
        self.assertIsNotNone(ra.warm_kitchen_for_post("coldbrand", caps, self.alerts))


class TestGapReportBlock(unittest.TestCase):
    def test_block_shape(self):
        alerts = ra.compute({"coldbrand": COLD})
        b = ra.for_gap_report("coldbrand", alerts)
        self.assertEqual(b["triggers"], ["cold_door"])
        self.assertIn("وصلت باردة", b["summary_ar"])
        self.assertIsNone(ra.for_gap_report("nobody", alerts))


class TestPostAuditIntegration(unittest.TestCase):
    """The WARN must reach post_audit.audit_post AS A SOFT issue (Rule #6 end-to-end)."""
    def setUp(self):
        self._orig = ra.load_alerts
        ra.load_alerts = lambda path=None: ra.compute({"coldbrand": COLD})

    def tearDown(self):
        ra.load_alerts = self._orig

    def _post(self, caption):
        return {"slot": {}, "captions": [caption], "kill_patterns": [], "corpus_text": "",
                "brand_ar": "", "visual": {}}

    def test_warn_appears_and_is_soft(self):
        iss = post_audit.audit_post(self._post("دجاج ساخن طازج من الفرن"), "coldbrand")
        codes = [c for c, _ in iss]
        self.assertIn("reputation_warm_kitchen_warn", codes)
        # soft: post_audit treats _warn-suffixed codes as non-blocking
        hard = [c for c, _ in iss if c != "occasion_missing" and not c.endswith("_warn")]
        self.assertNotIn("reputation_warm_kitchen_warn", hard)

    def test_no_warn_on_neutral_caption(self):
        iss = post_audit.audit_post(self._post("غداء اليوم بطعمه المعروف"), "coldbrand")
        self.assertNotIn("reputation_warm_kitchen_warn", [c for c, _ in iss])


class TestIdempotentMain(unittest.TestCase):
    def test_compute_recompute_stable(self):
        a1 = ra.compute({"coldbrand": COLD, "cleanbrand": CLEAN})
        a2 = ra.compute({"coldbrand": COLD, "cleanbrand": CLEAN})
        self.assertEqual(a1, a2)
        self.assertEqual(set(a1), {"coldbrand"})


if __name__ == "__main__":
    unittest.main()
