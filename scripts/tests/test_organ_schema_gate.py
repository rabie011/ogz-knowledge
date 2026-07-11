#!/usr/bin/env python3
"""Regression guards for the wake63 production/fixture organ boundary."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "migrations"))

import fingerprint_status  # noqa: E402
import generate_organ_schemas as gate  # noqa: E402
import mark_rfp_synthetic_fixtures as marker_migration  # noqa: E402
from test_immune_system import _rolling_window_contract  # noqa: E402


class TestOrganSchemaGate(unittest.TestCase):
    RFP = marker_migration.EXPECTED_HANDLES

    def test_production_census_is_named_and_excludes_rfp_fixtures(self):
        self.assertEqual(
            fingerprint_status.real_clients(),
            ["albaik", "alnasserjewelry", "eatjurisha", "myfitness.sa"],
        )
        self.assertTrue(self.RFP.isdisjoint(fingerprint_status.real_clients()))

    def test_rfp_markers_match_contract_and_validate(self):
        marker_migration.migrate(check=True)
        result = gate.validate_synthetic_fixtures()
        self.assertEqual(result["fixture_invalid"], 0)
        self.assertTrue(self.RFP <= set(result["synthetic_fixtures"]))

    def test_rfp_year_maps_remain_live_immune_fixtures(self):
        for handle in self.RFP:
            path = ROOT / "clients" / handle / "year_map.json"
            self.assertTrue(path.exists(), f"{handle}: year-map fixture missing")
            valid, detail = _rolling_window_contract(json.loads(path.read_text()))
            self.assertTrue(valid, f"{handle}: {detail}")

    def test_additive_fields_are_named_without_blanket_loosening(self):
        required = {
            "client_state_v1": {"outreach_ruling", "archive_claim_poor"},
            "client_truth_pack_v1": {"_diagnosis_note", "format"},
            "client_red_lines_v1": {"_research", "_meta"},
            "client_goals_v1": {"_passport", "capacity", "primary", "_counter_fix"},
            "client_audience_mirror_v1": {"_status", "segments", "sources_enum"},
            "client_taste_v1": {"kill_patterns"},
            "client_gap_report_v1": {"auto_filled", "established_research", "v37_visual"},
        }
        for schema_name, fields in required.items():
            schema = json.loads((ROOT / "12_data_shapes" / f"{schema_name}.schema.json").read_text())
            self.assertFalse(schema["additionalProperties"], schema_name)
            self.assertTrue(fields <= set(schema["properties"]), schema_name)

    def test_only_fable_gated_real_data_findings_may_remain(self):
        result = gate.validate_all()
        actual = {(f["handle"], f["organ"], f["kind"]) for f in result["findings"]}
        gated = {
            ("alnasserjewelry", "competitor_set", "missing"),
            ("alnasserjewelry", "trust", "missing"),
            ("myfitness.sa", "red_lines", "invalid"),
        }
        self.assertTrue(actual <= gated, actual - gated)

    def test_validate_only_is_byte_read_only_and_direct_counted(self):
        paths = sorted((ROOT / "12_data_shapes").glob("client_*_v1.schema.json"))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        run = subprocess.run(
            [sys.executable, str(SCRIPTS / "generate_organ_schemas.py"),
             "--validate-only", "--json-summary"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.assertEqual(before, after)
        prefix = gate.SUMMARY_PREFIX
        line = next(line for line in run.stdout.splitlines() if line.startswith(prefix))
        summary = json.loads(line[len(prefix):])
        self.assertEqual(summary["total_findings"],
                         summary["invalid_files"] + summary["missing_files"]
                         + summary["fixture_invalid"] + summary["inference_findings"])
        self.assertEqual(summary["production_clients"], fingerprint_status.real_clients())


if __name__ == "__main__":
    unittest.main()
