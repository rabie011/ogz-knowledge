"""B065 — ensure_assets must auto-heal STALE angle cards, not just missing ones.

Before this, creative_line.ensure_assets() rebuilt an angle card only when the file was
ABSENT. A pre-B041 card (June 11 schema: every angle brain=None, old one-line lens labels)
existed on disk, so it was read as-is and its dead ideation lenses were fed straight to the
render pen — a silent staleness consumption (Rule #6 consumer law; root deeper than B065's
"just re-run it"). These tests pin the staleness detector and the rebuild trigger WITHOUT
touching any LLM (subprocess.run is mocked, so build_angle_cards.py never actually runs).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import creative_line as cl


def _card(angles):
    return {"angles": angles, "_brand": "acme", "_occasion": "national_day"}


class TestAngleCardStaleDetector(unittest.TestCase):
    def _write(self, obj):
        d = Path(tempfile.mkdtemp())
        f = d / "acme__national_day.json"
        f.write_text(json.dumps(obj, ensure_ascii=False) if obj is not None else "{ not json")
        return f

    def test_pre_b041_brain_none_is_stale(self):
        f = self._write(_card([{"id": 1, "brain": None, "lens": "paradox_hunter"},
                               {"id": 2, "brain": None, "lens": "firaasa"}]))
        self.assertTrue(cl._angle_card_stale(f))

    def test_missing_brain_key_is_stale(self):
        f = self._write(_card([{"id": 1, "lens": "firaasa"}]))
        self.assertTrue(cl._angle_card_stale(f))

    def test_any_brainless_angle_makes_card_stale(self):
        f = self._write(_card([{"id": 1, "brain": "metaphor"},
                               {"id": 2, "brain": None}]))   # one bad angle is enough
        self.assertTrue(cl._angle_card_stale(f))

    def test_fresh_routed_card_is_not_stale(self):
        f = self._write(_card([{"id": 1, "brain": "saudi_national_day", "lens": "saudi_national_day"},
                               {"id": 2, "brain": "metaphor", "lens": "metaphor"}]))
        self.assertFalse(cl._angle_card_stale(f))

    def test_empty_or_corrupt_is_stale(self):
        self.assertTrue(cl._angle_card_stale(self._write(_card([]))))      # no angles
        self.assertTrue(cl._angle_card_stale(self._write(None)))           # corrupt json


class TestEnsureAssetsRebuildTrigger(unittest.TestCase):
    """ensure_assets rebuilds on missing OR stale angle card; skips when fresh."""

    def _layout(self, angle_card):
        base = Path(tempfile.mkdtemp())
        (base / "data" / "truth_packs").mkdir(parents=True)
        (base / "data" / "angle_cards").mkdir(parents=True)
        (base / "scripts").mkdir(parents=True)
        # truth pack always present + fresh so only the angle card drives behaviour
        (base / "data" / "truth_packs" / "acme__national_day.json").write_text('{"truth": 1}')
        if angle_card is not None:
            (base / "data" / "angle_cards" / "acme__national_day.json").write_text(
                json.dumps(angle_card, ensure_ascii=False))
        return base

    def _run(self, base):
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            # simulate the builder writing a fresh routed card
            (base / "data" / "angle_cards" / "acme__national_day.json").write_text(
                json.dumps(_card([{"id": 1, "brain": "metaphor"}]), ensure_ascii=False))
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(cl, "BASE", base), \
             mock.patch.object(cl.subprocess, "run", side_effect=fake_run):
            cl.ensure_assets("acme", "national_day")
        # which scripts were invoked
        return [Path(c[1]).name for c in calls]

    def test_stale_card_triggers_angle_rebuild(self):
        base = self._layout(_card([{"id": 1, "brain": None, "lens": "firaasa"}]))
        scripts = self._run(base)
        self.assertIn("build_angle_cards.py", scripts)        # stale → rebuilt
        self.assertNotIn("build_truth_pack.py", scripts)      # fresh pack → untouched

    def test_fresh_card_skips_rebuild(self):
        base = self._layout(_card([{"id": 1, "brain": "metaphor"},
                                   {"id": 2, "brain": "paradox"}]))
        scripts = self._run(base)
        self.assertEqual(scripts, [])                         # nothing rebuilt

    def test_missing_card_triggers_rebuild(self):
        base = self._layout(None)
        scripts = self._run(base)
        self.assertIn("build_angle_cards.py", scripts)


if __name__ == "__main__":
    unittest.main()
