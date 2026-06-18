#!/usr/bin/env python3
"""Guards that post_audit's truth block CONSUMES the named-person + promo-combo guards
(2026-06-18, RABIE zoom-out). The regression this kills: post_audit imported PERSON_AR
and PROMO_AR but never SCANNED with them — a write-only door (Rule #6 broken). A caption
naming "الأمير X" in a fictional scene, or a hallucinated combo "التوأم Y", passed the
audit's truth block uncaught — exactly the hallucinated-prince (June 11) and التوأم (the
EVIDENCE-RULE scar) kills. The scan must bite the kill AND stay grounded against the
client's corpus so a REAL person/promo in the brand's own captions is not false-flagged
(must match render_client_slot.ungrounded())."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import post_audit as pa


def _truths(d, handle="albaik"):
    return [x for x in pa.audit_post(d, handle) if x[0] == "truth"]


class TestPostAuditTruthGuards(unittest.TestCase):

    def test_imported_guards_are_not_write_only(self):
        """PERSON_AR + PROMO_AR are imported AND referenced in the source (Rule #6)."""
        src = (Path(pa.__file__)).read_text()
        # both guards must be invoked (.finditer/.search), not merely imported on line 29
        self.assertGreaterEqual(src.count("PERSON_AR."), 1, "PERSON_AR imported but never scanned")
        self.assertGreaterEqual(src.count("PERSON_EN."), 1, "PERSON_EN imported but never scanned")
        self.assertGreaterEqual(src.count("PROMO_AR."), 1, "PROMO_AR imported but never scanned")

    def test_named_person_in_fictional_scene_flagged(self):
        """الأمير X in a non-documented (invented) scene = the hallucinated-prince kill."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["اليوم مع الأمير محمد في المطعم"],
             "corpus_text": "برجر دجاج بطاطس"}
        self.assertTrue(_truths(d), "fictional-scene named person not flagged")

    def test_named_person_en_in_fictional_scene_flagged(self):
        """B265: an EN-led feed naming "Prince Mohammed" in an invented scene is the SAME
        kill as الأمير in Arabic (June 14: English legal-name was 1 of RABIE's 24 mistakes).
        Proves the PERSON_EN branch of line 104 bites, not just PERSON_AR."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["Today with Prince Mohammed at the venue"],
             "corpus_text": "chicken burger fries"}
        self.assertTrue(_truths(d), "fictional-scene EN named person not flagged")

    def test_documented_grounded_en_person_not_false_flagged(self):
        """A real EN-named person in a documented moment, present in the corpus, must pass
        (no false positive) — mirrors the AR grounded case for the PERSON_EN branch."""
        d = {"slot": {"documented_moment": True, "angle_theme": "event"},
             "captions": ["Prince Mohammed visited the branch"],
             "corpus_text": "prince mohammed branch visit"}
        self.assertFalse(_truths(d), "grounded+documented EN person wrongly flagged")

    def test_ungrounded_promo_combo_flagged(self):
        """التوأم not in the client's corpus = invented product (the EVIDENCE-RULE scar)."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["جرب التوأم برجر الجديد"],
             "corpus_text": "برجر دجاج بطاطس"}
        self.assertTrue(_truths(d), "ungrounded promo-combo not flagged")

    def test_grounded_promo_combo_not_false_flagged(self):
        """التوأم that IS in the client's real captions must pass (no false positive)."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["جرب التوأم برجر الجديد"],
             "corpus_text": "التوأم برجر دجاج بطاطس"}
        self.assertFalse(_truths(d), "grounded promo-combo wrongly flagged")

    def test_documented_grounded_person_not_false_flagged(self):
        """A real person in a documented moment, present in the corpus, must pass."""
        d = {"slot": {"documented_moment": True, "angle_theme": "event"},
             "captions": ["افتتح الأمير محمد الفرع"],
             "corpus_text": "الأمير محمد الفرع الجديد"}
        self.assertFalse(_truths(d), "grounded+documented person wrongly flagged")


if __name__ == "__main__":
    unittest.main()
