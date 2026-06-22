"""B254 — the blackout-aware render_slot decision (render_slot_gate.decide).

PURE function over blackout_gate.check(); we stub check() to exercise the three
truths: hard blackout → requeue (never render), no block → render, advisory
warnings → ride along but never block.
"""
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import render_slot_gate as g  # noqa: E402


class TestRenderSlotGate(unittest.TestCase):
    def test_hard_blackout_requeues_with_reason(self):
        fake = {"publish_allowed": False,
                "hard_block": {"reason": "وفاة — حداد وطني", "set_by": "mohamed", "since": "t"},
                "warnings": []}
        with mock.patch.object(g, "blackout_check", return_value=fake):
            d = g.decide()
        self.assertEqual(d["action"], "requeue")
        self.assertTrue(d["blackout"])
        self.assertEqual(d["reason"], "وفاة — حداد وطني")

    def test_blackout_with_no_reason_still_requeues(self):
        fake = {"publish_allowed": False, "hard_block": None, "warnings": []}
        with mock.patch.object(g, "blackout_check", return_value=fake):
            d = g.decide()
        self.assertEqual(d["action"], "requeue")
        self.assertTrue(d["reason"])  # never empty — a requeue must carry a reason

    def test_clear_renders(self):
        fake = {"publish_allowed": True, "hard_block": None, "warnings": []}
        with mock.patch.object(g, "blackout_check", return_value=fake):
            d = g.decide()
        self.assertEqual(d["action"], "render")
        self.assertFalse(d["blackout"])
        self.assertIsNone(d["reason"])

    def test_advisory_warnings_do_not_block_render(self):
        # quiet hours / maghrib are warnings, NOT a hard block — render proceeds, warnings ride along
        fake = {"publish_allowed": True, "hard_block": None,
                "warnings": ["maghrib window (~18:00 +-20min) - hold sends if possible"]}
        with mock.patch.object(g, "blackout_check", return_value=fake):
            d = g.decide()
        self.assertEqual(d["action"], "render")
        self.assertEqual(len(d["warnings"]), 1)


class TestRequeueBackoff(unittest.TestCase):
    """B254b — exponential backoff so a multi-day blackout doesn't spin every 10s."""

    def test_backoff_grows_exponentially(self):
        self.assertEqual(g.backoff_seconds(1), 60)
        self.assertEqual(g.backoff_seconds(2), 120)
        self.assertEqual(g.backoff_seconds(3), 240)
        self.assertEqual(g.backoff_seconds(4), 480)

    def test_backoff_caps_at_30min(self):
        self.assertEqual(g.backoff_seconds(6), 1800)
        self.assertEqual(g.backoff_seconds(100), 1800)  # no overflow at large counts

    def test_backoff_count_zero_or_negative_is_first_retry(self):
        self.assertEqual(g.backoff_seconds(0), 60)
        self.assertEqual(g.backoff_seconds(-5), 60)

    def test_plan_requeue_increments_and_stamps_not_before(self):
        now = datetime(2026, 6, 22, 12, 0, 0)
        task = {"task_type": "render_slot", "handle": "albaik"}
        rq = g.plan_requeue(task, {"reason": "حداد وطني"}, now=now)
        self.assertEqual(rq["requeue_count"], 1)
        self.assertEqual(rq["requeue_reason"], "حداد وطني")
        self.assertEqual(rq["not_before"], (now + timedelta(seconds=60)).isoformat(timespec="seconds"))
        # original task is not mutated
        self.assertNotIn("requeue_count", task)

    def test_plan_requeue_uses_growing_count(self):
        now = datetime(2026, 6, 22, 12, 0, 0)
        task = {"requeue_count": 3}
        rq = g.plan_requeue(task, {"reason": "x"}, now=now)
        self.assertEqual(rq["requeue_count"], 4)
        self.assertEqual(rq["not_before"], (now + timedelta(seconds=480)).isoformat(timespec="seconds"))

    def test_plan_requeue_blank_reason_never_empty(self):
        rq = g.plan_requeue({}, {}, now=datetime(2026, 6, 22, 12, 0, 0))
        self.assertTrue(rq["requeue_reason"])  # a requeue must carry a reason


class TestIsReady(unittest.TestCase):
    """B254b consumer predicate — skip a slot until its not_before passes."""

    def test_no_not_before_is_ready(self):
        self.assertTrue(g.is_ready({"task_type": "render_slot"}))

    def test_future_not_before_is_not_ready(self):
        now = datetime(2026, 6, 22, 12, 0, 0)
        future = (now + timedelta(seconds=300)).isoformat(timespec="seconds")
        self.assertFalse(g.is_ready({"not_before": future}, now=now))

    def test_past_not_before_is_ready(self):
        now = datetime(2026, 6, 22, 12, 0, 0)
        past = (now - timedelta(seconds=1)).isoformat(timespec="seconds")
        self.assertTrue(g.is_ready({"not_before": past}, now=now))

    def test_malformed_not_before_fails_open(self):
        # not_before is a spin damper, not the safety boundary — bad value must not strand a slot
        self.assertTrue(g.is_ready({"not_before": "not-a-date"}))

    def test_plan_then_is_ready_roundtrip(self):
        now = datetime(2026, 6, 22, 12, 0, 0)
        rq = g.plan_requeue({}, {"reason": "x"}, now=now)
        self.assertFalse(g.is_ready(rq, now=now))                              # just stamped → wait
        self.assertTrue(g.is_ready(rq, now=now + timedelta(seconds=61)))       # after backoff → due


if __name__ == "__main__":
    unittest.main()
