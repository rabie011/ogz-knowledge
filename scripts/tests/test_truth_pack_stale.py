"""B270 — ensure_assets must auto-heal STALE truth packs, not just missing ones.

Before this, creative_line.ensure_assets() rebuilt a truth pack only when the file was
ABSENT. A pack written before the pack shape changed (no '_schema', or a stale signature)
existed on disk, so it was read as-is and its pre-schema-change brief was fed straight to
the render pen — a silent staleness consumption (Rule #6 consumer law; the truth-pack mirror
of B065's _angle_card_stale). These tests pin the staleness detector and the rebuild trigger
WITHOUT touching any LLM (subprocess.run is mocked, so build_truth_pack.py never runs).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import creative_line as cl

CUR = cl.TRUTH_PACK_SCHEMA_VERSION


def _fresh_card():
    return {"angles": [{"id": 1, "brain": "metaphor"}], "_brand": "acme", "_occasion": "national_day"}


class TestTruthPackStaleDetector(unittest.TestCase):
    def _write(self, obj):
        d = Path(tempfile.mkdtemp())
        f = d / "acme__national_day.json"
        f.write_text(json.dumps(obj, ensure_ascii=False) if obj is not None else "{ not json")
        return f

    def test_no_schema_field_is_stale(self):
        # all 20 pre-B270 packs on disk carry no '_schema'
        f = self._write({"brand_en": "acme", "real_products": ["x"], "_built": "2026-06-11"})
        self.assertTrue(cl._truth_pack_stale(f))

    def test_old_schema_signature_is_stale(self):
        f = self._write({"_schema": "tp-v0", "real_products": ["x"]})
        self.assertTrue(cl._truth_pack_stale(f))

    def test_current_schema_signature_is_fresh(self):
        f = self._write({"_schema": CUR, "real_products": ["x"]})
        self.assertFalse(cl._truth_pack_stale(f))

    def test_corrupt_pack_is_stale(self):
        self.assertTrue(cl._truth_pack_stale(self._write(None)))

    def test_build_truth_pack_stamps_current_schema(self):
        # the writer and the reader must agree on the signature (Rule #6 single source)
        import build_truth_pack as btp
        self.assertEqual(btp.SCHEMA_VERSION, CUR)


class TestEnsureAssetsTruthPackRebuild(unittest.TestCase):
    """ensure_assets rebuilds on missing OR stale truth pack; skips when fresh."""

    def _layout(self, truth_pack):
        base = Path(tempfile.mkdtemp())
        (base / "data" / "truth_packs").mkdir(parents=True)
        (base / "data" / "angle_cards").mkdir(parents=True)
        (base / "scripts").mkdir(parents=True)
        # angle card always present + fresh so only the truth pack drives behaviour
        (base / "data" / "angle_cards" / "acme__national_day.json").write_text(
            json.dumps(_fresh_card(), ensure_ascii=False))
        if truth_pack is not None:
            (base / "data" / "truth_packs" / "acme__national_day.json").write_text(
                json.dumps(truth_pack, ensure_ascii=False))
        return base

    def _run(self, base):
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            # simulate the builder writing a fresh, current-schema pack
            (base / "data" / "truth_packs" / "acme__national_day.json").write_text(
                json.dumps({"truth": 1, "_schema": CUR}, ensure_ascii=False))
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(cl, "BASE", base), \
             mock.patch.object(cl.subprocess, "run", side_effect=fake_run):
            cl.ensure_assets("acme", "national_day")
        return [Path(c[1]).name for c in calls]

    def test_stale_pack_triggers_truth_rebuild(self):
        base = self._layout({"truth": 1})            # no _schema → stale
        scripts = self._run(base)
        self.assertIn("build_truth_pack.py", scripts)       # stale → rebuilt
        self.assertNotIn("build_angle_cards.py", scripts)   # fresh card → untouched

    def test_fresh_pack_skips_rebuild(self):
        base = self._layout({"truth": 1, "_schema": CUR})
        scripts = self._run(base)
        self.assertEqual(scripts, [])                        # nothing rebuilt

    def test_missing_pack_triggers_rebuild(self):
        base = self._layout(None)
        scripts = self._run(base)
        self.assertIn("build_truth_pack.py", scripts)


class TestSelfInvalidatingSignature(unittest.TestCase):
    """B270b — the signature is DERIVED from build()'s key-shape: it must MOVE when a key is
    added / removed / renamed, and HOLD STEADY when only values change, so no human has to
    remember to bump a constant (the omission behind B057's silent schema drift)."""

    def setUp(self):
        import build_truth_pack as btp
        self.btp = btp

    def test_value_change_does_not_move_signature(self):
        a = {"brand_en": "x", "voice": {"openers": ["a"]}, "real_products": ["p"]}
        b = {"brand_en": "y", "voice": {"openers": ["b", "c"]}, "real_products": []}
        self.assertEqual(self.btp.schema_signature(a), self.btp.schema_signature(b))

    def test_added_top_key_moves_signature(self):
        a = {"brand_en": "x", "voice": {"openers": []}}
        b = {"brand_en": "x", "voice": {"openers": []}, "new_key": 1}
        self.assertNotEqual(self.btp.schema_signature(a), self.btp.schema_signature(b))

    def test_added_voice_key_moves_signature(self):
        a = {"brand_en": "x", "voice": {"openers": []}}
        b = {"brand_en": "x", "voice": {"openers": [], "tone": "warm"}}
        self.assertNotEqual(self.btp.schema_signature(a), self.btp.schema_signature(b))

    def test_schema_key_excluded_from_its_own_signature(self):
        # the stamped '_schema' must not feed back into the signature (no self-dependence)
        a = {"brand_en": "x", "voice": {}}
        b = {"brand_en": "x", "voice": {}, "_schema": "anything"}
        self.assertEqual(self.btp.schema_signature(a), self.btp.schema_signature(b))

    def test_live_build_stamps_the_constant(self):
        # writer (build) and reader (SCHEMA_VERSION constant) agree by construction (Rule #6)
        p = self.btp.build("__shape__", "__shape__", "__shape__", "__shape__")
        self.assertEqual(p["_schema"], self.btp.SCHEMA_VERSION)

    def test_signature_is_not_the_fallback(self):
        # the import-time probe succeeded; we are running on a real derived signature
        self.assertNotEqual(self.btp.SCHEMA_VERSION, self.btp._FALLBACK_SHAPE)
        self.assertTrue(self.btp.SCHEMA_VERSION.startswith("tp-"))


if __name__ == "__main__":
    unittest.main()
