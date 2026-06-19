#!/usr/bin/env python3
"""Locks the B143 slice (June 19) — the visual-gate verdict now has a CONSUMER (Rule #6).
The checklist WROTE verdict.all_clear but nothing read it; a card a human explicitly REJECTED
(all_clear == False) could re-enter the judging batch that reaches Mohamed (Rule #13 chokepoint).
These tests lock: (1) human_rejected is True ONLY for an explicit False verdict, (2) unchecked
(None) / cleared (True) / no-gate cards are NOT rejections, (3) build_judging_batch.candidates()
excludes a human-rejected card — the writer→reader wire is asserted end-to-end."""
import sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import visual_gate_checklist as vg
import build_judging_batch as bjb


def _card(all_clear, **extra):
    c = {"captions": ["مشهد دافئ في صباح العيد"],
         "idea": {"scene_ar": "مشهد"},
         "visual": {"phone_shoot_card": ["لقطة 1", "لقطة 2", "لقطة 3"]}}
    if all_clear is not vg:  # sentinel: vg means "attach NO gate at all"
        c["visual_gate"] = {"verdict": {"checked_by": "human", "date": "2026-06-19",
                                         "all_clear": all_clear}}
    c.update(extra)
    return c


class TestVisualGateConsumer(unittest.TestCase):
    def test_explicit_reject_is_rejected(self):
        self.assertTrue(vg.human_rejected(_card(False)))

    def test_unchecked_not_rejected(self):
        self.assertFalse(vg.human_rejected(_card(None)))

    def test_cleared_not_rejected(self):
        self.assertFalse(vg.human_rejected(_card(True)))

    def test_no_gate_not_rejected(self):
        self.assertFalse(vg.human_rejected(_card(vg)))  # no visual_gate attached

    def test_candidates_excludes_human_rejected(self):
        """End-to-end: a human-rejected card on disk must NOT enter the judging batch."""
        with tempfile.TemporaryDirectory() as td:
            posts = Path(td) / "clients" / "t___gate" / "posts"
            posts.mkdir(parents=True)
            (posts / "2026-07-01__evergreen__ok.json").write_text(
                json.dumps(_card(True), ensure_ascii=False))
            (posts / "2026-07-02__evergreen__rejected.json").write_text(
                json.dumps(_card(False), ensure_ascii=False))
            orig = bjb.BASE
            try:
                bjb.BASE = Path(td)
                names = {Path(c["path"]).name for c in bjb.candidates("t___gate")}
            finally:
                bjb.BASE = orig
        self.assertIn("2026-07-01__evergreen__ok.json", names)
        self.assertNotIn("2026-07-02__evergreen__rejected.json", names)


if __name__ == "__main__":
    unittest.main()
