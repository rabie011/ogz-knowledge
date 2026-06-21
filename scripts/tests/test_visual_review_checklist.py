"""Tests for build_visual_review_checklist.py (B142) — the deterministic per-client human-eyes
visual gate (Rule #13). Asserts the three properties that make the checklist trustworthy:

1. COVERAGE — every visual dimension (faces, family, mixed_gender, modesty, music, product_truth)
   gets a row for every client with a profile. A dropped row = a blind spot the June-14 batch
   exploited; the test refuses it.
2. DETERMINISM — generating twice yields byte-identical output (no clock/random in the body), so
   --check can detect drift and the file is reproducible from the organs (Rule #12).
3. GATE-CONSISTENCY — the human row's verdict matches deadly_defaults_gate's source logic: a
   strictest/absent value reads `strict`; a non-strict override with NO ledger event reads
   `needs_event` (the same condition the machine gate BLOCKS on). Human eye and machine can't
   disagree.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_visual_review_checklist as b  # noqa: E402
import deadly_defaults_gate as gate  # noqa: E402
import yaml  # noqa: E402

# the six dimensions B142 names (face/modesty/mixed_gender/family/product-truth) + music
EXPECTED_GATE_IDS = {"faces", "family_visibility", "mixed_gender", "modesty",
                     "music_context", "product_truth"}


def _table():
    return yaml.safe_load(b.TABLE.read_text(encoding="utf-8"))


def _mk_client(base: Path, handle: str, overrides: dict, ledger_lines=None):
    p = base / "clients" / handle / "profile"
    p.mkdir(parents=True, exist_ok=True)
    (p / "cultural_overrides.json").write_text(json.dumps(overrides), encoding="utf-8")
    if ledger_lines is not None:
        ev = base / "clients" / handle / "events"
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "ledger.jsonl").write_text("\n".join(ledger_lines), encoding="utf-8")


class TestVisualFields(unittest.TestCase):
    def test_canonical_dimensions_present(self):
        ids = {f["visual_gate_id"] for f in b.visual_fields(_table())}
        self.assertEqual(EXPECTED_GATE_IDS, ids,
                         f"visual dimension set drifted: {ids ^ EXPECTED_GATE_IDS}")

    def test_product_truth_synthesized(self):
        # ai_imagery_of_real_products has no native visual_gate_id — generator must supply one
        fields = {f["field"]: f for f in b.visual_fields(_table())}
        self.assertIn("ai_imagery_of_real_products", fields)
        self.assertEqual(fields["ai_imagery_of_real_products"]["visual_gate_id"], "product_truth")


class TestCoverageLive(unittest.TestCase):
    """Against the real repo: every pilot client gets every visual row."""
    def test_every_client_full_coverage(self):
        handles = b.clients_with_profile(b.BASE)
        self.assertGreaterEqual(len(handles), 3, "expected the 3 pilots at least")
        vfields = b.visual_fields(_table())
        for h in handles:
            rows = b.client_rows(h, vfields, b.BASE)
            ids = {r["gate_id"] for r in rows}
            self.assertEqual(ids, EXPECTED_GATE_IDS, f"{h} missing rows: {EXPECTED_GATE_IDS ^ ids}")

    def test_live_file_is_fresh(self):
        # the committed file must match a fresh generation (the --check contract)
        if b.OUT.exists():
            self.assertEqual(b.OUT.read_text(encoding="utf-8"), b.build_checklist(b.BASE),
                             "on-disk checklist is stale — re-run build_visual_review_checklist.py")


class TestDeterminism(unittest.TestCase):
    def test_two_builds_identical(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            _mk_client(base, "acme", {"face_visibility": "never"})
            _mk_client(base, "beta", {"modesty_dress": "conservative"})
            # patch table path is shared (real table); only client dir is synthetic
            first = b.build_checklist(base)
            second = b.build_checklist(base)
            self.assertEqual(first, second)
            self.assertIn("## acme", first)
            self.assertIn("## beta", first)


class TestGateConsistency(unittest.TestCase):
    def test_strict_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            _mk_client(base, "acme", {})  # all absent → strictest governs
            rows = {r["field"]: r for r in
                    b.client_rows("acme", b.visual_fields(_table()), base)}
            self.assertEqual(rows["face_visibility"]["status"], "strict")

    def test_needs_event_matches_machine_block(self):
        """A non-strict override with no ledger event: the human row reads needs_event AND the
        machine gate reports a violation — proving one boundary, all doors."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            _mk_client(base, "acme", {"face_visibility": "always"}, ledger_lines=[])
            row = next(r for r in b.client_rows("acme", b.visual_fields(_table()), base)
                       if r["field"] == "face_visibility")
            self.assertEqual(row["status"], "needs_event")
            # cross-check the actual machine gate on the same fixture
            table = _table()
            deadly = {r["field"]: r for r in table["fields"] if r.get("deadly_if_wrong")}
            # point the gate at our temp base
            orig = gate.BASE
            try:
                gate.BASE = base
                violations = gate.check_client("acme", deadly)
            finally:
                gate.BASE = orig
            self.assertTrue(any("face_visibility" in v for v in violations),
                            "machine gate did not block what the human row flagged")

    def test_relaxed_when_event_present(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            _mk_client(base, "acme", {"face_visibility": "always"},
                       ledger_lines=['{"type":"red_line_relaxed","field":"face_visibility"}'])
            row = next(r for r in b.client_rows("acme", b.visual_fields(_table()), base)
                       if r["field"] == "face_visibility")
            self.assertEqual(row["status"], "relaxed")


if __name__ == "__main__":
    unittest.main()
