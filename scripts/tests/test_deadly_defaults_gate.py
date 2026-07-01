#!/usr/bin/env python3
"""Locks the DEADLY-DEFAULTS gate (B106) — and the June-30 false-positive fix.

The gate blocks release when a deadly cultural field runs LESS strict than its strictest
default without a client red_line_relaxed event. The fix (June 30): a total-prohibition
value (boolean False / 'none' / 'never' / 'off' ...) is no-less-strict than ANY deadly
field's default, so it can never be a relaxation — flagging it was a false positive
(alnasserjewelry encoded mixed_gender_scenes=false, stricter than the 'family-only-mixing'
string default, yet str(False) != the string flagged it). These tests lock BOTH directions:
(1) provably-conservative values are SAFE, and critically (2) a real relaxation is STILL
flagged — the gate must not fail-open (the C221w scar)."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import deadly_defaults_gate as g

# the one deadly field whose strict default is a non-trivial string (the fix's real target)
DEADLY = {"mixed_gender_scenes": {"field": "mixed_gender_scenes",
                                  "strictest_default": "family-only-mixing",
                                  "deadly_if_wrong": True}}


class TestDeadlyDefaultsGate(unittest.TestCase):
    def setUp(self):
        self._orig_base = g.BASE
        self._tmp = Path(tempfile.mkdtemp())
        g.BASE = self._tmp

    def tearDown(self):
        g.BASE = self._orig_base

    def _client(self, handle, mixed_val, event=False):
        pdir = self._tmp / "clients" / handle / "profile"
        pdir.mkdir(parents=True)
        (pdir / "cultural_overrides.json").write_text(
            json.dumps({"mixed_gender_scenes": mixed_val}))
        if event:
            ev = self._tmp / "clients" / handle / "events"
            ev.mkdir(parents=True)
            (ev / "ledger.jsonl").write_text(
                json.dumps({"type": "red_line_relaxed", "field": "mixed_gender_scenes"}) + "\n")

    def _violations(self, handle):
        return g.check_client(handle, DEADLY)

    # ---- SAFE: conservative / total-prohibition values must NOT block ----
    def test_equal_to_strict_is_safe(self):
        self._client("a", "family-only-mixing")
        self.assertEqual(self._violations("a"), [])

    def test_boolean_false_is_safe(self):
        # the alnasserjewelry case: no mixing at all is STRICTER than family-only-mixing
        self._client("a", False)
        self.assertEqual(self._violations("a"), [])

    def test_string_negation_sentinels_are_safe(self):
        for v in ("false", "none", "no", "never", "off", "segregated", "no-mixing"):
            with self.subTest(v=v):
                self._client(f"c_{v}", v)
                self.assertEqual(self._violations(f"c_{v}"), [], f"{v!r} should be safe")

    def test_absent_field_is_safe(self):
        pdir = self._tmp / "clients" / "a" / "profile"
        pdir.mkdir(parents=True)
        (pdir / "cultural_overrides.json").write_text(json.dumps({}))
        self.assertEqual(self._violations("a"), [])

    # ---- BLOCKED: a real relaxation must STILL be flagged (no fail-open) ----
    def test_boolean_true_is_flagged(self):
        self._client("a", True)
        self.assertEqual(len(self._violations("a")), 1)

    def test_permissive_string_is_flagged(self):
        for v in ("all", "all-mixing", "allowed", "mixed", "on"):
            with self.subTest(v=v):
                self._client(f"c_{v}", v)
                self.assertEqual(len(self._violations(f"c_{v}")), 1, f"{v!r} must be flagged")

    def test_relaxation_with_event_is_safe(self):
        # a genuine relaxation is legal ONLY with a client red_line_relaxed event
        self._client("a", "all-mixing", event=True)
        self.assertEqual(self._violations("a"), [])


# the July-1 second proven-strict value: face_visibility='faceless' (zero faces shown) is a
# total prohibition on the risky direction (a SHOWN face), no-less-strict than the 'never'
# default — yet str('faceless')!='never' flagged it. The consumer render_image.py:60 already
# buckets faceless==never; the gate was the only place out of step. Locks both directions.
FACE_DEADLY = {"face_visibility": {"field": "face_visibility",
                                   "strictest_default": "never",
                                   "deadly_if_wrong": True}}


class TestFaceVisibilityFaceless(unittest.TestCase):
    def setUp(self):
        self._orig_base = g.BASE
        self._tmp = Path(tempfile.mkdtemp())
        g.BASE = self._tmp

    def tearDown(self):
        g.BASE = self._orig_base

    def _client(self, handle, face_val, event=False):
        pdir = self._tmp / "clients" / handle / "profile"
        pdir.mkdir(parents=True)
        (pdir / "cultural_overrides.json").write_text(
            json.dumps({"face_visibility": face_val}))
        if event:
            ev = self._tmp / "clients" / handle / "events"
            ev.mkdir(parents=True)
            (ev / "ledger.jsonl").write_text(
                json.dumps({"type": "red_line_relaxed", "field": "face_visibility"}) + "\n")

    def _violations(self, handle):
        return g.check_client(handle, FACE_DEADLY)

    # ---- SAFE: 'faceless' (and 'never') are total prohibitions, must NOT block ----
    def test_faceless_is_safe(self):
        # the myfitness.sa case: 'faceless' == no faces = as strict as 'never'
        self._client("a", "faceless")
        self.assertEqual(self._violations("a"), [])

    def test_never_is_safe(self):
        self._client("a", "never")
        self.assertEqual(self._violations("a"), [])

    # ---- BLOCKED: a real relaxation (a shown face) must STILL be flagged (no fail-open) ----
    def test_permissive_face_values_are_flagged(self):
        for v in ("visible", "shown", "all", "allowed", "always"):
            with self.subTest(v=v):
                self._client(f"c_{v}", v)
                self.assertEqual(len(self._violations(f"c_{v}")), 1, f"{v!r} must be flagged")

    def test_relaxation_with_event_is_safe(self):
        self._client("a", "visible", event=True)
        self.assertEqual(self._violations("a"), [])


if __name__ == "__main__":
    unittest.main()
