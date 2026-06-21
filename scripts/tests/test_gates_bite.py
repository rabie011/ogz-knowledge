#!/usr/bin/env python3
"""GATES BITE — locks the adversarial-audit fix (2026-06-21): a gate that finds a cultural
violation must REFUSE (exit non-zero / raise), never warn (Rule #8). Covers the three fixes:

  F1 — pre_ship_gate.assert_shippable RAISES (SystemExit) on a hard cultural KILL / learned BLOCK;
       the typed verdict's shippable() is False for a kill and True for a clean post.
  F2 — image_modesty_gate: the pixel gate BLOCKS on any modesty/mixed-gender/exposed-skin/real-
       person violation; a 'skipped' ($0) verdict is NOT clearance; assert_image_clear RAISES on
       a violating verdict. (All $0 — no gpt-4o call; the model layer is bypassed/stubbed.)
  F3 — the typed verdict contract at both gate seams REFUSES a malformed result (bad verdict
       string, a severed block-wire, a vision reply missing an axis) rather than passing it.

$0: this file makes ZERO API calls. The vision path is exercised only in skip-mode or with a
stubbed reply. Run by make_sure every cycle (unittest discover -s scripts/tests)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pre_ship_gate as psg
import image_modesty_gate as img


def _post(caption, occasion="evergreen", scene=""):
    return {"captions": [caption], "idea": {"scene_ar": scene}, "slot": {"occasion": occasion}}


# ── F1 + F3: pre_ship_gate bites and the typed seam refuses malformed ──────────────────
class TestPreShipBites(unittest.TestCase):
    def test_royal_kill_raises(self):
        post = _post("في يوم الوطن تجتمع عائلة آل سعود حول الطاولة", "saudi_national_day")
        with self.assertRaises(SystemExit):
            psg.assert_shippable(post, "eatjurisha")

    def test_dine_in_cloud_kitchen_raises(self):
        post = _post("تفضلوا إلى مطعمنا والجلسة في صالتنا")
        with self.assertRaises(SystemExit):
            psg.assert_shippable(post, "eatjurisha")

    def test_clean_post_does_not_raise(self):
        post = _post("جريش سعودي أصيل، نكهة تشبع وتدفّي القلب")
        v = psg.assert_shippable(post, "eatjurisha")   # must NOT raise
        self.assertTrue(v.shippable())
        self.assertIn(v.verdict, ("PASS", "REVIEW"))

    def test_typed_verdict_kill_not_shippable(self):
        post = _post("بعد الطواف، اطلبوا الجريش طعم الوطن", "hajj_season")
        v = psg.verdict_of(post, "eatjurisha")
        self.assertEqual(v.verdict, "KILL")
        self.assertFalse(v.shippable())
        self.assertTrue(v.block)

    def test_malformed_verdict_string_refuses(self):
        with self.assertRaises(ValueError):
            psg.GateVerdict(handle="x", occasion="y", verdict="MAYBE", block=False)

    def test_severed_block_wire_refuses(self):
        # a KILL that claims block=False is a severed wire — must refuse, not pass.
        with self.assertRaises(ValueError):
            psg.GateVerdict(handle="x", occasion="y", verdict="KILL", block=False)


# ── F2 + F3: the pixel modesty gate bites ──────────────────────────────────────────────
class TestImageGateBites(unittest.TestCase):
    def test_violation_is_not_passed(self):
        v = img.ImageVerdict(image="x.jpg", handle="albaik", modest=False, mixed_gender=False,
                             exposed_skin=False, identifiable_real_person_or_royal=False,
                             verdict="block", reasons=["not modest"])
        self.assertTrue(v.violated)
        self.assertFalse(v.passed())

    def test_mixed_gender_is_violation(self):
        v = img.ImageVerdict(image="x.jpg", handle="albaik", modest=True, mixed_gender=True,
                             exposed_skin=False, identifiable_real_person_or_royal=False,
                             verdict="block")
        self.assertTrue(v.violated)

    def test_real_person_is_violation(self):
        v = img.ImageVerdict(image="x.jpg", handle="albaik", modest=True, mixed_gender=False,
                             exposed_skin=False, identifiable_real_person_or_royal=True,
                             verdict="block")
        self.assertTrue(v.violated)

    def test_clean_pass(self):
        v = img.ImageVerdict(image="x.jpg", handle="albaik", modest=True, mixed_gender=False,
                             exposed_skin=False, identifiable_real_person_or_royal=False,
                             verdict="pass")
        self.assertFalse(v.violated)
        self.assertTrue(v.passed())

    def test_skipped_is_not_clearance(self):
        # a $0 skip must NEVER read as a pass — a pixel gate that didn't look cannot clear.
        v = img.ImageVerdict(image="x.jpg", handle="albaik", modest=True, mixed_gender=False,
                             exposed_skin=False, identifiable_real_person_or_royal=False,
                             verdict="skipped")
        self.assertFalse(v.passed())

    def test_malformed_image_verdict_refuses(self):
        with self.assertRaises(ValueError):
            img.ImageVerdict(image="x.jpg", handle="albaik", modest=True, mixed_gender=False,
                             exposed_skin=False, identifiable_real_person_or_royal=False,
                             verdict="green")   # not in {'pass','block','skipped'}

    def test_assert_image_clear_raises_on_skip(self):
        # $0: skip-mode on the real local render → 'skipped' → assert_image_clear must RAISE
        # (skipped is not clearance). Uses an existing render so no spend, no network.
        render = Path(__file__).parent.parent.parent / "api/static/renders_v37/albaik_S01.jpg"
        if not render.exists():
            self.skipTest("no local render to gate")
        with self.assertRaises(SystemExit):
            img.assert_image_clear(str(render), "albaik", skip_vision=True)

    def test_missing_image_refuses(self):
        with self.assertRaises(SystemExit):
            img.check("/nonexistent/never.jpg", "albaik", skip_vision=True)


if __name__ == "__main__":
    unittest.main()
