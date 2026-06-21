#!/usr/bin/env python3
"""Guards the OUTCOME RECEIPT COLLECTOR (B094) — the reader that closes the full circle.

The collector turns matured published pieces into schema-valid `metric_recorded` outcome events,
compares each to the BRAND'S OWN baseline only, and flags silent posts. These tests lock:
  1. A matured (T+7d) piece with countables → exactly one receipt, VALID against outcome_event_v1.
  2. Idempotent — a second run emits 0 new receipts (deterministic event_ulid).
  3. T+7d gating — a piece published <7d ago yields NO receipt.
  4. Own-baseline law — the vs-baseline delta is computed from the SAME brand's priors only;
     another brand's numbers never leak in; <MIN_BASELINE_N priors → INSUFFICIENT, no number (Rule #9).
  5. no-outcome-30d — a piece published >30d ago with no metrics is flagged, not silently dropped.
  6. Empty inputs → honest 0/0/0, no crash (Pre-Build Q2).
"""
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema

import importlib.util

ROOT = Path(__file__).parent.parent.parent
SCHEMA_DIR = ROOT / "12_data_shapes"
OUTCOME_SCHEMA = json.loads((SCHEMA_DIR / "outcome_event_v1.schema.json").read_text(encoding="utf-8"))

# load the module under test
_spec = importlib.util.spec_from_file_location("outcome_receipt", ROOT / "scripts/outcome_receipt.py")
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

NOW = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)


def _validator():
    """Validator with the provenance_mixin $ref resolved from the schema dir."""
    prov = json.loads((SCHEMA_DIR / "provenance_mixin_v1.schema.json").read_text(encoding="utf-8"))
    registry = jsonschema.validators.Draft202012Validator
    resolver = jsonschema.RefResolver(
        base_uri="", referrer=OUTCOME_SCHEMA,
        store={"provenance_mixin_v1.schema.json": prov})
    return jsonschema.Draft202012Validator(OUTCOME_SCHEMA, resolver=resolver)


def _write_jsonl(path: Path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


class TestOutcomeReceipt(unittest.TestCase):

    def setUp(self):
        # redirect every module path to a per-test tmp area; restore in tearDown
        self.tmp = Path(self.id().split(".")[-1] + "_tmp_b094")
        self.tmp.mkdir(exist_ok=True)
        self._orig = {k: getattr(oc, k) for k in
                      ("PUBLISHED_LEDGER", "METRICS_FEED", "RECEIPTS_LEDGER", "RECEIPTS_SUMMARY")}
        oc.PUBLISHED_LEDGER = self.tmp / "published.jsonl"
        oc.METRICS_FEED = self.tmp / "post_metrics.jsonl"
        oc.RECEIPTS_LEDGER = self.tmp / "receipts.jsonl"
        oc.RECEIPTS_SUMMARY = self.tmp / "receipts_summary.json"

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(oc, k, v)
        for f in self.tmp.glob("*"):
            f.unlink()
        self.tmp.rmdir()

    def _publish(self, gen, brand, days_ago):
        return {"event_type": "published", "subject_generation_ulid": gen, "brand_ulid": brand,
                "timestamp": (NOW - timedelta(days=days_ago)).isoformat()}

    def _metric(self, gen, er):
        return {"subject_generation_ulid": gen, "engagement_rate": er, "reach": 1000,
                "platform": "instagram", "metrics_source": "test"}

    def test_empty_inputs_honest(self):
        rep = oc.collect(now=NOW)
        self.assertEqual((rep["published_seen"], rep["new_receipts"]), (0, 0))
        self.assertFalse(oc.RECEIPTS_LEDGER.exists())  # wrote nothing

    def test_matured_piece_emits_valid_receipt(self):
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000001", "BRANDA", 8)])
        _write_jsonl(oc.METRICS_FEED, [self._metric("GEN0000000000000000000001", 0.05)])
        rep = oc.collect(now=NOW)
        self.assertEqual(rep["new_receipts"], 1)
        rows = [json.loads(l) for l in oc.RECEIPTS_LEDGER.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        _validator().validate(rows[0])  # must satisfy outcome_event_v1 (raises on failure)
        self.assertEqual(rows[0]["event_type"], "metric_recorded")
        self.assertEqual(rows[0]["performance_metrics"]["engagement_rate"], 0.05)

    def test_idempotent_second_run(self):
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000001", "BRANDA", 8)])
        _write_jsonl(oc.METRICS_FEED, [self._metric("GEN0000000000000000000001", 0.05)])
        oc.collect(now=NOW)
        rep2 = oc.collect(now=NOW)
        self.assertEqual(rep2["new_receipts"], 0)
        self.assertEqual(len(oc.RECEIPTS_LEDGER.read_text().splitlines()), 1)

    def test_window_gating_under_7d(self):
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000002", "BRANDA", 3)])
        _write_jsonl(oc.METRICS_FEED, [self._metric("GEN0000000000000000000002", 0.05)])
        rep = oc.collect(now=NOW)
        self.assertEqual(rep["new_receipts"], 0)  # not matured to T+7d

    def test_no_outcome_30d_flagged(self):
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000003", "BRANDA", 40)])
        # no metrics for this piece
        rep = oc.collect(now=NOW)
        self.assertEqual(rep["new_receipts"], 0)
        self.assertEqual(len(rep["no_outcome_30d"]), 1)
        self.assertEqual(rep["no_outcome_30d"][0]["subject_generation_ulid"],
                         "GEN0000000000000000000003")

    def test_own_baseline_no_cross_brand_leak(self):
        # BRANDA has 3 prior receipts (baseline established); BRANDB has its own high numbers.
        # A new BRANDA piece must be compared to BRANDA's median ONLY — never BRANDB's.
        priors = []
        for i, er in enumerate([0.04, 0.05, 0.06], start=1):
            priors.append({"event_ulid": f"PRIOR000000000000000000000{i}", "event_type": "metric_recorded",
                           "timestamp": NOW.isoformat(), "brand_ulid": "BRANDA",
                           "subject_generation_ulid": f"OLDGEN0000000000000000000{i}",
                           "schema_version": 1, "performance_metrics": {"engagement_rate": er},
                           "actor": "system",
                           "provenance": {"source": "test", "date_added": "2026-06-22",
                                          "confirmer": "t", "confidence": "experimental", "scope": "brand"}})
        # a BRANDB prior with a wildly different number that must NOT pollute BRANDA's baseline
        priors.append({"event_ulid": "PRIORB00000000000000000000B", "event_type": "metric_recorded",
                       "timestamp": NOW.isoformat(), "brand_ulid": "BRANDB",
                       "subject_generation_ulid": "BGEN00000000000000000000B1",
                       "schema_version": 1, "performance_metrics": {"engagement_rate": 0.99},
                       "actor": "system",
                       "provenance": {"source": "test", "date_added": "2026-06-22",
                                      "confirmer": "t", "confidence": "experimental", "scope": "brand"}})
        _write_jsonl(oc.RECEIPTS_LEDGER, priors)
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000004", "BRANDA", 8)])
        _write_jsonl(oc.METRICS_FEED, [self._metric("GEN0000000000000000000004", 0.10)])
        rep = oc.collect(now=NOW)
        comp = next(c for c in rep["comparisons"]
                    if c["subject_generation_ulid"] == "GEN0000000000000000000004")
        self.assertEqual(comp["own_baseline"], 0.05)   # median(0.04,0.05,0.06) — BRANDB's 0.99 excluded
        self.assertEqual(comp["baseline_n"], 3)
        self.assertEqual(comp["delta_pct"], 100.0)     # 0.10 vs 0.05 = +100%

    def test_insufficient_baseline_no_number(self):
        # only 1 prior for the brand → below MIN_BASELINE_N → INSUFFICIENT, no delta quoted
        _write_jsonl(oc.RECEIPTS_LEDGER, [
            {"event_ulid": "PRIOR000000000000000000000X", "event_type": "metric_recorded",
             "timestamp": NOW.isoformat(), "brand_ulid": "BRANDC",
             "subject_generation_ulid": "OLDGENC000000000000000000X", "schema_version": 1,
             "performance_metrics": {"engagement_rate": 0.04}, "actor": "system",
             "provenance": {"source": "test", "date_added": "2026-06-22", "confirmer": "t",
                            "confidence": "experimental", "scope": "brand"}}])
        _write_jsonl(oc.PUBLISHED_LEDGER, [self._publish("GEN0000000000000000000005", "BRANDC", 8)])
        _write_jsonl(oc.METRICS_FEED, [self._metric("GEN0000000000000000000005", 0.10)])
        rep = oc.collect(now=NOW)
        comp = next(c for c in rep["comparisons"]
                    if c["subject_generation_ulid"] == "GEN0000000000000000000005")
        self.assertEqual(comp.get("status"), "INSUFFICIENT_BASELINE")
        self.assertIsNone(comp["own_baseline"])
        self.assertIsNone(comp["delta_pct"])


if __name__ == "__main__":
    unittest.main()
