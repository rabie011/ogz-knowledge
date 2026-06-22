"""B157: post-publish veto / approver-conflict takedown play must exist with required structure.

The play designs the *mechanism* (detect -> freeze -> ping -> takedown -> confirm -> prevent)
while deferring the numbered decisions (takedown SLA, account owner, authority rule) to Mohamed.
It must NOT pre-judge whose authority wins, and must NOT quote an SLA number it hasn't been given.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(ROOT, "clients", "_plays", "approver_conflict.md")


class TestApproverConflict(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exists = os.path.exists(ARTIFACT)
        cls.text = ""
        if cls.exists:
            with open(ARTIFACT, encoding="utf-8") as f:
                cls.text = f.read()

    def test_artifact_exists(self):
        self.assertTrue(self.exists, f"missing veto play: {ARTIFACT}")

    def test_full_takedown_sequence_present(self):
        # the mechanism must name every stage of the protocol, in order
        lower = self.text.lower()
        for stage in ("detect", "freeze", "ping", "take down", "confirm", "prevent"):
            self.assertIn(stage, lower, f"takedown stage missing: {stage}")

    def test_capture_before_delete(self):
        # never destroy the as-published evidence before it is archived
        self.assertRegex(self.text.lower(), r"capture before delete")

    def test_defers_rulings_to_mohamed(self):
        # SLA, account owner, and authority rule are his fork (Rule #11 / #1)
        self.assertRegex(self.text.lower(), r"mohamed'?s? (fork|ruling)")
        self.assertIn("B159", self.text)  # takedown SLA fork
        self.assertIn("B161", self.text)  # account-owner fork

    def test_does_not_quote_an_sla_number(self):
        # Rule #9: no SLA number is asserted before Mohamed sets it.
        # Guard against a stray "<n> minutes/hours/min" appearing as a takedown target.
        self.assertNotRegex(
            self.text.lower(),
            r"\b\d+\s*(minutes?|mins?|hours?|hrs?)\b",
            "no time-target number may be asserted before Mohamed sets the SLA (Rule #9)",
        )

    def test_does_not_rewrite_content(self):
        # Rule #12: a veto is a publish-authority event, not a content-quality re-run
        self.assertRegex(self.text.lower(), r"rule #12")

    def test_routes_conflict_back_to_prevent_recurrence(self):
        # the root fix: next batch needs the primary approver before publish
        self.assertRegex(self.text.lower(), r"primary approver")


if __name__ == "__main__":
    unittest.main()
