"""B152: PDPL erasure-vs-append-only research artifact must exist with required structure.

The artifact feeds Mohamed's pending PDPL precedence ruling. It must carry the law
(anonymization carve-out), exactly the two reconciliation options, a recommendation,
and sources — and must NOT pretend to make the ruling itself.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(ROOT, "clients", "_plays", "offboarding_pdpl.md")


class TestOffboardingPDPL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exists = os.path.exists(ARTIFACT)
        cls.text = ""
        if cls.exists:
            with open(ARTIFACT, encoding="utf-8") as f:
                cls.text = f.read()

    def test_artifact_exists(self):
        self.assertTrue(self.exists, f"missing research artifact: {ARTIFACT}")

    def test_anonymization_carveout_present(self):
        # the legal hook that lets append-only learning signal survive
        self.assertRegex(self.text.lower(), r"anonymi[sz]")
        self.assertIn("Art. 18", self.text)

    def test_two_reconciliation_options(self):
        self.assertIn("Option A", self.text)
        self.assertIn("Option B", self.text)

    def test_has_recommendation(self):
        self.assertRegex(self.text, r"(?i)recommend")

    def test_does_not_usurp_mohameds_ruling(self):
        # must explicitly defer the precedence ruling to Mohamed (Rule #11 / #1)
        self.assertRegex(self.text.lower(), r"(mohamed'?s? (gate|ruling|fork)|gated on his ruling)")

    def test_carries_sources(self):
        urls = re.findall(r"https?://", self.text)
        self.assertGreaterEqual(len(urls), 3, "research must cite >=3 sources (evidence rule)")

    def test_framed_as_research_not_legal_advice(self):
        self.assertRegex(self.text.lower(), r"not legal advice")


if __name__ == "__main__":
    unittest.main()
