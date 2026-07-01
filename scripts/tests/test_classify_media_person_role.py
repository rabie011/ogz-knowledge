#!/usr/bin/env python3
"""C245 patch-2: classify_media person_role tagging + cultural red-line guard.
Deterministic, zero network (the vision call is never made — we test _guard + the re-tag
trigger, the two pieces patch-3's crop path depends on)."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import classify_media as cm


class TestRoyalRedLineGuard(unittest.TestCase):
    """A royal/public figure is NEVER croppable (cultural red line) — even if the vision
    model hallucinates person_role='incidental'. _guard must force 'subject'."""

    def test_royal_incidental_is_forced_to_subject(self):
        tags = cm._guard({"is_royal_or_public_figure": True, "has_person": True,
                          "person_role": "incidental"})
        self.assertEqual(tags["person_role"], "subject")

    def test_royal_missing_role_is_subject(self):
        tags = cm._guard({"is_royal_or_public_figure": True, "has_person": True})
        self.assertEqual(tags["person_role"], "subject")


class TestPersonRoleNormalisation(unittest.TestCase):
    """patch-3 must never read a missing/garbage person_role → fail SAFE (person = subject)."""

    def test_incidental_with_product_preserved(self):
        tags = cm._guard({"has_person": True, "is_royal_or_public_figure": False,
                          "person_role": "incidental", "product_en": "gold necklace"})
        self.assertEqual(tags["person_role"], "incidental")

    def test_missing_role_with_person_defaults_subject(self):
        tags = cm._guard({"has_person": True, "is_royal_or_public_figure": False})
        self.assertEqual(tags["person_role"], "subject")

    def test_garbage_role_with_person_defaults_subject(self):
        tags = cm._guard({"has_person": True, "person_role": "wearing_it"})
        self.assertEqual(tags["person_role"], "subject")

    def test_no_person_defaults_none(self):
        tags = cm._guard({"has_person": False, "kind": "product_food"})
        self.assertEqual(tags["person_role"], "none")

    def test_valid_subject_preserved(self):
        tags = cm._guard({"has_person": True, "person_role": "subject"})
        self.assertEqual(tags["person_role"], "subject")


class TestPromptContract(unittest.TestCase):
    """The vision prompt must actually request person_role (else the whole patch is dead)."""

    def test_prompt_requests_person_role(self):
        self.assertIn("person_role", cm.PROMPT)
        self.assertIn("incidental", cm.PROMPT)


if __name__ == "__main__":
    unittest.main()
