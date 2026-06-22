#!/usr/bin/env python3
"""B284 (June 22) — the headless producer must survive a hung slot.

The 2026-06-22 orchestra stall: produce_batch's per-slot render child blocked at ~0 CPU for
5+min with no output, freezing the WHOLE unattended batch and starving the taste→creation wire.
Root: render() called subprocess.run with NO timeout. These tests lock the fix — the slot render
is bounded, a timed-out child fails the slot LOUDLY and returns None (is_clean→False, round-robin
continues), and the ceiling is honestly wired (real timeout kwarg, env-overridable, 0 = no cap)."""
import sys, subprocess, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import produce_batch as pb


class TestProduceSlotTimeout(unittest.TestCase):
    def test_timeout_kwarg_is_actually_passed(self):
        """The ceiling must reach subprocess.run — not a dead constant (Rule #6: writer needs a reader)."""
        with mock.patch.object(pb, "SLOT_TIMEOUT", 137), \
             mock.patch.object(pb.subprocess, "run") as run:
            pb.render("eatjurisha", "2026-06-25", "__test_noexist")
            self.assertTrue(run.called)
            self.assertEqual(run.call_args.kwargs.get("timeout"), 137)

    def test_zero_means_no_cap(self):
        """Escape hatch: PRODUCE_SLOT_TIMEOUT=0 → timeout=None (uncapped), never timeout=0 (instant kill)."""
        with mock.patch.object(pb, "SLOT_TIMEOUT", 0), \
             mock.patch.object(pb.subprocess, "run") as run:
            pb.render("eatjurisha", "2026-06-25", "__test_noexist")
            self.assertIsNone(run.call_args.kwargs.get("timeout"))

    def test_hung_slot_returns_none_not_hang(self):
        """A child that blows the ceiling is killed; render returns None so the batch continues.
        Before the fix this call hung forever; now it must return promptly with None."""
        def _boom(*a, **k):
            raise subprocess.TimeoutExpired(cmd="render_client_slot.py", timeout=k.get("timeout") or 300)
        with mock.patch.object(pb, "SLOT_TIMEOUT", 1), \
             mock.patch.object(pb.subprocess, "run", side_effect=_boom):
            self.assertIsNone(pb.render("eatjurisha", "2026-06-25", "__test_noexist"))

    def test_timed_out_slot_is_clean_false(self):
        """The downstream contract: a dropped slot is never mistaken for a clean card."""
        self.assertFalse(pb.is_clean(None, "eatjurisha"))


if __name__ == "__main__":
    unittest.main()
