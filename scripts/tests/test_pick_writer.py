#!/usr/bin/env python3
"""Tests for the post_pick WRITER (B180) — a post_pick tap becomes a pick_selected
client event so trust_ladder + approvers_registry (the readers) actually receive it.
Closes the severed wire (Rule #6). Uses an injected writer + temp base so no real
client ledger is touched."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import build_pick_item  # noqa: E402
from approvers_registry import check_confirmer  # noqa: E402

try:
    import jsonschema  # noqa: E402
    _SCHEMA = json.loads((SCRIPTS.parent / "12_data_shapes" / "client_event_v1.schema.json").read_text())
except Exception:  # jsonschema always present in this repo, but stay defensive
    jsonschema = None
    _SCHEMA = None


def _card(handle="myfitness.sa", kind="post_pick", cid=None):
    return {"id": cid or f"pick_{handle}", "kind": kind, "title": "رمضان pick-of-3",
            "options": [{"v": "cd_01", "label": "أ"}, {"v": "cd_03", "label": "ب"}]}


class TestPickWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "clients" / "myfitness.sa").mkdir(parents=True)
        self.captured = []

    def tearDown(self):
        self.tmp.cleanup()

    def _writer(self, handle, ev):
        self.captured.append((handle, ev))

    def test_happy_path_writes_valid_event(self):
        ev = build_pick_item.record_pick(_card(), "cd_03", "mohamed",
                                         writer=self._writer, base=self.base)
        self.assertIsNotNone(ev)
        self.assertEqual(len(self.captured), 1)
        handle, written = self.captured[0]
        self.assertEqual(handle, "myfitness.sa")
        self.assertEqual(written["type"], "pick_selected")
        self.assertEqual(written["confirmer"], "mohamed")
        self.assertIn("cd_03", written["subject"])
        self.assertEqual(written["pick"], "cd_03")   # structured winner, not a text blob
        self.assertTrue(written["stamp"])
        # the event must satisfy the real contract its readers depend on
        check_confirmer(written)
        if jsonschema is not None:
            jsonschema.validate(written, _SCHEMA)

    def test_non_human_judge_rejected(self):
        # B156: only human confirmers move trust — a lane teammate must not write pick_selected
        ev = build_pick_item.record_pick(_card(), "cd_01", "hesham",
                                         writer=self._writer, base=self.base)
        self.assertIsNone(ev)
        self.assertEqual(self.captured, [])

    def test_wrong_kind_ignored(self):
        ev = build_pick_item.record_pick(_card(kind="caption_pick"), "cd_01", "mohamed",
                                         writer=self._writer, base=self.base)
        self.assertIsNone(ev)
        self.assertEqual(self.captured, [])

    def test_phantom_client_not_written(self):
        # handle parsed from id has no client dir → never create a phantom ledger
        ev = build_pick_item.record_pick(_card(handle="ghostbrand"), "cd_01", "mohamed",
                                         writer=self._writer, base=self.base)
        self.assertIsNone(ev)
        self.assertEqual(self.captured, [])

    def test_bad_id_prefix_ignored(self):
        ev = build_pick_item.record_pick(_card(cid="pw_abc123"), "cd_01", "mohamed",
                                         writer=self._writer, base=self.base)
        self.assertIsNone(ev)


if __name__ == "__main__":
    unittest.main()
