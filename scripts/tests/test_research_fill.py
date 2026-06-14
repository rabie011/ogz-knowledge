#!/usr/bin/env python3
"""Guards the auto_research reader (Mohamed's 6× order: established brands are RESEARCHED, not
asked). Prevents the write-only-flag regression: extraction_mode=auto_research MUST have a
reader that fills the organs and stops the gap_report from asking the forbidden new-brand Qs."""
import json, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import research_fill_established as rf

B = Path(__file__).parent.parent.parent


class TestAutoResearchReader(unittest.TestCase):

    def test_albaik_forbidden_questions_gone(self):
        """albaik is auto_research → its gap_report must NOT ask the new-brand Qs he forbade."""
        gr = B / "clients/albaik/profile/gap_report.json"
        if not gr.exists():
            self.skipTest("no albaik gap_report")
        qs = json.loads(gr.read_text()).get("questions", [])
        for forbidden in ("ينطق باسم البراند", "الخطوط الحمراء", "وش يميزكم"):
            self.assertFalse(any(forbidden in q for q in qs),
                             f"established albaik still asked the forbidden Q: {forbidden}")

    def test_albaik_organs_research_filled(self):
        """The RED organs the reader fills must actually be filled (not write-only flag)."""
        fp = json.loads((B / "clients/albaik/profile/fingerprint.json").read_text())
        l1 = fp.get("l1_strategy", {})
        self.assertTrue(l1.get("who_speaks") and l1.get("usp"),
                        "auto_research flag set but l1_strategy still empty — reader didn't fire")

    def test_research_fills_are_experimental_never_confirmed(self):
        """Research-derived facts must be confidence:experimental until Mohamed taps (anti-self-audit-lie)."""
        fp = json.loads((B / "clients/albaik/profile/fingerprint.json").read_text())
        r = (fp.get("l1_strategy", {}) or {}).get("_research", {})
        if r:
            self.assertEqual(r.get("confidence"), "experimental",
                             "research fill claimed non-experimental confidence")


if __name__ == "__main__":
    unittest.main()
