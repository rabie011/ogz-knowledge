#!/usr/bin/env python3
"""Guards that post_audit scans the VISUAL door (idea.scene_ar + shoot-card) for bilingual
filler with the SAME canonical FILLER, not just captions (B196 root, 2026-06-22).

The regression this kills: the bilingual filler ban guarded the CAPTION door only. The
myfitness 2026-09-10 post leaked «بل رحلة» (journey=رحلة, the G4 twin) inside its
idea.scene_ar — the brief the system renders the shoot from — and the caption-only FILLER
scan structurally could not see it, so a caption-clean post stamped "CLEAN" while directing
a filler scene. Same shared rule, all doors (the one-enforced-boundary scar). The new
'filler_visual' issue is NOT _warn-suffixed, so it REFUSES (Rule #8): a re-render carrying
filler in its scene can never ship."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import post_audit as pa


def _filler_vis(d, handle="myfitness.sa"):
    return [x for x in pa.audit_post(d, handle) if x[0] == "filler_visual"]


class TestPostAuditFillerVisualDoor(unittest.TestCase):

    def test_filler_in_scene_ar_flagged(self):
        """The exact 2026-09-10 leak: «بل رحلة» in idea.scene_ar, captions clean → flagged."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["تمرين اليوم في تبوك"],
             "idea": {"scene_ar": "إنه ليس مجرد تمرين، بل رحلة موثقة تشاركها مع العالم."},
             "corpus_text": "لياقة تمرين تبوك"}
        self.assertTrue(_filler_vis(d), "filler in scene_ar not flagged (visual door open)")

    def test_clean_scene_ar_not_flagged(self):
        """A concrete, filler-free scene must pass — no false positive on the visual door."""
        d = {"slot": {"angle_theme": "daily: post"},
             "captions": ["تمرين اليوم في تبوك"],
             "idea": {"scene_ar": "الكابتن يصعد جبلاً غرب تبوك عند الفجر والندى على الزجاج."},
             "corpus_text": "لياقة تمرين تبوك"}
        self.assertFalse(_filler_vis(d), "clean scene_ar wrongly flagged as filler")

    def test_filler_visual_refuses_not_warns(self):
        """'filler_visual' must be a HARD issue (Rule #8): not _warn-suffixed, not the soft
        occasion_missing — so post_audit's gate exits non-zero on it."""
        self.assertFalse("filler_visual".endswith("_warn"))
        self.assertNotEqual("filler_visual", "occasion_missing")


if __name__ == "__main__":
    unittest.main()
