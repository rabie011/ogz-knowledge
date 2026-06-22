#!/usr/bin/env python3
"""Pins the judge-lane seams as FAIL-CLOSED (2026-06-22 audit, Rule #8/#13).

Three swallow-and-proceed bugs at the boundary where a post reaches Mohamed's judge lane:

1. make_sure.py re-gate (`judge_cards_gated`): on any exception it set the check to True —
   a torn decision_queue or crashed gate reported GREEN while a gate-BLOCKED post sat live in
   his judge lane. `judge_cards_gated` feeds the master `ok = all(...)` gate. Fixed: on
   exception it sets the check to False and records the cause in `_blocked_live`.

2. seed_judge_cards.py pick: if the pre-ship gate raised, `except: pass` fell through to
   picked.append(...) — an UN-GATED post shipped to his judge lane. Fixed: the except prints a
   skip and `continue`s, never admitting an un-gateable post.

3. complaint_ping.py docstring claimed data/service_pings.json is "read by the morning brief".
   grep proves no such reader exists (only the writer). Fixed: the docstring now states it is an
   internal artifact with no current reader (Rule #6 doc honesty / self-audit law).

These are source-contract tests: the fail-closed blocks live inline in main()/pick_posts() and
read live state from disk, so the regression is pinned at the source seam (matching the
test_post_audit_truth source-assertion precedent)."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent


class TestMakeSureRegateFailsClosed(unittest.TestCase):
    SRC = (SCRIPTS / "make_sure.py").read_text()

    def test_regate_except_sets_false_not_true(self):
        """The re-gate except must set judge_cards_gated = False (alarm), never True (green)."""
        src = self.SRC
        idx = src.index('checks["judge_cards_gated"] = not blocked_live')
        tail = src[idx:idx + 700]
        self.assertIn('checks["judge_cards_gated"] = False', tail,
                      "re-gate except must fail CLOSED (False), not green-by-default")
        self.assertNotIn('checks["judge_cards_gated"] = True', tail,
                         "re-gate except still fails OPEN (True) — a blocked post can go live green")

    def test_regate_except_records_blocked_cause(self):
        idx = self.SRC.index('checks["judge_cards_gated"] = not blocked_live')
        tail = self.SRC[idx:idx + 700]
        self.assertIn("re-gate raised", tail,
                      "the failure cause must be surfaced in _blocked_live (evidence, not silence)")


class TestSeedJudgeGateFailsClosed(unittest.TestCase):
    SRC = (SCRIPTS / "seed_judge_cards.py").read_text()

    def test_pre_ship_gate_except_continues_not_pass(self):
        """If the pre-ship gate raises, the loop must `continue` (skip the un-gateable post),
        never `pass` and fall through to picked.append (an un-gated post in the judge lane)."""
        src = self.SRC
        # the pick_posts gate block: import pre_ship_gate -> gate -> except
        idx = src.index("import pre_ship_gate as _g")
        tail = src[idx:idx + 600]
        self.assertNotRegex(tail, r"except Exception:\s*\n\s*pass",
                            "pre-ship gate still swallows errors with `except: pass` (admits post)")
        self.assertIn("pre-ship gate raised", tail,
                      "the gate-error skip must announce itself")
        # a continue must appear in the except so we never fall through to append
        self.assertEqual(tail.count("continue"), tail[:tail.index("except")].count("continue") + 1,
                         "the gate-error except must end in `continue`")


class TestComplaintPingDocHonest(unittest.TestCase):
    SRC = (SCRIPTS / "complaint_ping.py").read_text()

    def test_no_false_morning_brief_reader_claim(self):
        """The docstring must not claim service_pings.json is read by a non-existent morning brief."""
        self.assertNotIn("read by the morning brief", self.SRC,
                         "false reader claim still present (Rule #6 doc honesty)")

    def test_no_reader_exists_for_service_pings(self):
        """Proof for the doc correction: complaint_ping.py (the writer) is the ONLY production
        file referencing service_pings across scripts/ — there is genuinely no reader. (tests/
        are excluded: this file names service_pings as documentation of the scan.)"""
        readers = [p.name for p in SCRIPTS.rglob("*.py")
                   if "tests" not in p.relative_to(SCRIPTS).parts
                   and p.name != "complaint_ping.py"
                   and "service_pings" in p.read_text()]
        self.assertEqual(readers, [],
                         f"a reader DOES exist {readers} — name it in the docstring instead")


if __name__ == "__main__":
    unittest.main()
