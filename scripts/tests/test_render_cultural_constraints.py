"""B145 — the client's cultural red-line organ is injected as HARD render-prompt constraints
pre-fal.ai, and the face_visibility:never line actually lands in the prompt.

A CONFIRMED cultural kill enforced by Rule #6 (consumer law): a red_line written with no reader
is a lie that looks like safety. Before this, render_image's chain_image_prompt carried a generic
'no faces unless scene demands' — which PERMITTED faces for a brand whose organ says
face_visibility:'never' (all 3 pilots). This locks the wire from clients/<h>/profile/
cultural_overrides.json → the prompt, and honors the organ law 'absent field = strictest governs'."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from render_image import (
    BASE,
    chain_image_prompt,
    cultural_constraint_clause,
    _load_cultural_overrides,
)


class TestCulturalConstraints(unittest.TestCase):
    def test_face_never_yields_no_human_faces(self):
        s = cultural_constraint_clause({"face_visibility": "never"})
        self.assertIn("no human faces", s)

    def test_face_faceless_yields_no_human_faces(self):
        # 'faceless' (enum never|faceless|visible) forbids a VISIBLE face just like 'never'.
        # Regression lock: a scattered `== "never"` silently permitted faces for a faceless
        # brand (myfitness.sa) across render + gate + strategy — this is the 3rd-miss guard.
        s = cultural_constraint_clause({"face_visibility": "faceless"})
        self.assertIn("no human faces", s)

    def test_faces_forbidden_predicate_covers_the_enum(self):
        # THE single boundary (Rule #3): client_rules.faces_forbidden is what every gate asks.
        import client_rules as cr
        self.assertTrue(cr.faces_forbidden({"face_visibility": "never"}))
        self.assertTrue(cr.faces_forbidden({"face_visibility": "faceless"}))
        self.assertTrue(cr.faces_forbidden({}))  # absent = strictest governs
        self.assertFalse(cr.faces_forbidden({"face_visibility": "visible"}))

    def test_face_allowed_drops_the_face_constraint(self):
        s = cultural_constraint_clause({"face_visibility": "allowed", "modesty_dress": "relaxed"})
        self.assertNotIn("no human faces", s)

    def test_absent_field_governs_strictest(self):
        # the organ law: a missing value is read as the MOST conservative option
        s = cultural_constraint_clause({})
        self.assertIn("no human faces", s)
        self.assertIn("conservative modest dress", s)

    def test_eatjurisha_real_organ_lands_in_prompt(self):
        # end-to-end against the REAL client organ on disk (face_visibility: "never")
        ov = _load_cultural_overrides("eatjurisha")
        self.assertEqual(ov.get("face_visibility"), "never")  # guard the fixture
        prompt = chain_image_prompt({"idea": {"scene_ar": "صحن"}}, ov)
        self.assertIn("CULTURAL CONSTRAINTS", prompt)
        self.assertIn("no human faces", prompt)
        self.assertIn("no unrelated mixed-gender interaction", prompt)

    def test_all_three_pilots_forbid_faces(self):
        # the constraint must be live for every pilot, not just eatjurisha
        for h in ("eatjurisha", "albaik", "myfitness.sa"):
            f = BASE / "clients" / h / "profile/cultural_overrides.json"
            if not f.exists():
                continue
            prompt = chain_image_prompt({"idea": {"scene_ar": "x"}}, _load_cultural_overrides(h))
            self.assertIn("no human faces", prompt, f"{h} render prompt permits faces")

    def test_default_no_longer_permits_faces(self):
        # the old leak: chain_image_prompt() with no overrides used to allow faces
        prompt = chain_image_prompt({"idea": {"scene_ar": "x"}})
        self.assertNotIn("no faces unless scene demands", prompt)
        self.assertIn("no human faces", prompt)


if __name__ == "__main__":
    unittest.main()
