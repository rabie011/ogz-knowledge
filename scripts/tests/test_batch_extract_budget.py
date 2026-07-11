#!/usr/bin/env python3
"""Hermetic budget-cage tests for batch_extract.py. No provider calls or live ledgers."""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
import batch_extract as batch  # noqa: E402
import extraction_budget as budget  # noqa: E402


def jpeg(width: int = 1000, height: int = 1000) -> bytes:
    return (
        b"\xff\xd8"
        + b"\xff\xc0"
        + struct.pack(">H", 17)
        + b"\x08"
        + struct.pack(">HH", height, width)
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        + b"\xff\xd9"
    )


class StubClient:
    def __init__(self, usages=None, error=None):
        self.messages = self
        self.usages = list(usages or [])
        self.error = error
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        usage = self.usages.pop(0) if self.usages else (1000, 100)
        return SimpleNamespace(
            content=[SimpleNamespace(text="{}")],
            usage=SimpleNamespace(input_tokens=usage[0], output_tokens=usage[1]),
        )


class BatchExtractBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="batch-extract-budget-")
        self.box = Path(self.temp.name)
        self.repo = self.box / "brain"
        self.system = self.box / "system"
        self.media = self.repo / "11_who_to_learn_from/_inbox/@barnscoffee/media"
        self.obs = self.repo / "11_who_to_learn_from/observations/f_and_b"
        self.media.mkdir(parents=True)
        self.obs.mkdir(parents=True)
        for index in range(1, 3):
            (self.media / f"fresh_{index}.jpg").write_bytes(jpeg())
        self.pricing = self.system / "tools/model_router.json"
        self.pricing.parent.mkdir(parents=True)
        self.pricing.write_text(json.dumps({
            "prices_per_mtok": {
                budget.MODEL: {"in": 1.0, "out": 5.0},
            }
        }), encoding="utf-8")
        self.registry = self.system / "ledgers/REGISTRY.json"
        self.registry.parent.mkdir(parents=True)
        self._write_registry([budget.WRITER_ID])
        self.receipts = []
        self.key_reads = 0
        self.client = StubClient([(1000, 100), (1100, 120)])

    def tearDown(self):
        self.temp.cleanup()

    def _write_registry(self, writers):
        self.registry.write_text(json.dumps({
            "ledgers": [{
                "name": "spend",
                "path": "ledgers/spend.jsonl",
                "schema_v": 1,
                "schema": {
                    "id": "str", "worker": "str", "lane": "str", "calls": "num",
                    "usd": "num", "minutes": "num", "status": "str", "note": "str",
                },
                "writers": writers,
                "readers": ["fixture"],
                "append_only": True,
            }]
        }), encoding="utf-8")

    def args(self, **overrides):
        values = {
            "account": "barnscoffee",
            "batch": "B2",
            "count": 2,
            "seed": 42,
            "max_calls": 2,
            "max_usd": Decimal("0.10"),
            "max_tokens": 50000,
            "estimate_only": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def key_loader(self):
        self.key_reads += 1
        return "fixture-key-not-real"

    def run_case(self, args=None, **overrides):
        return batch.run_extraction(
            args or self.args(),
            repo=self.repo,
            system_root=self.system,
            pricing_path=self.pricing,
            registry_path=self.registry,
            receipt_writer=overrides.pop("receipt_writer", self.receipts.append),
            key_loader=overrides.pop("key_loader", self.key_loader),
            client_factory=overrides.pop("client_factory", lambda _key: self.client),
            release_check=lambda: None,
            sleep_fn=lambda _seconds: None,
            **overrides,
        )

    def events(self):
        return [json.loads(row["note"])["event"] for row in self.receipts]

    def test_01_legacy_cli_without_all_caps_refuses(self):
        with self.assertRaises(SystemExit) as raised:
            batch.parse_args(["--account", "barnscoffee"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_02_estimate_only_never_reads_key_or_writes_receipt(self):
        rc = self.run_case(self.args(estimate_only=True),
                      key_loader=lambda: self.fail("credential read in estimate-only"),
                      client_factory=lambda _key: self.fail("provider initialized in estimate-only"))
        self.assertEqual(rc, 0)
        self.assertEqual(self.receipts, [])
        self.assertEqual(list(self.obs.glob("*.json")), [])

    def test_03_call_cap_refuses_before_reserve_or_key(self):
        rc = self.run_case(self.args(max_calls=1))
        self.assertEqual(rc, 2)
        self.assertEqual(self.receipts, [])
        self.assertEqual(self.key_reads, 0)
        self.assertEqual(self.client.calls, 0)

    def test_04_token_and_usd_caps_refuse_before_provider(self):
        for values in (
            {"max_tokens": 1},
            {"max_usd": Decimal("0.000001")},
            {"max_calls": 6},
            {"max_tokens": 60001},
            {"max_usd": Decimal("0.150001")},
        ):
            with self.subTest(values=values):
                self.receipts.clear()
                self.key_reads = 0
                self.client.calls = 0
                rc = self.run_case(self.args(**values))
                self.assertEqual(rc, 2)
                self.assertEqual(self.receipts, [])
                self.assertEqual(self.key_reads, 0)
                self.assertEqual(self.client.calls, 0)

    def test_05_unregistered_writer_refuses_before_key(self):
        self._write_registry([])
        rc = self.run_case()
        self.assertEqual(rc, 2)
        self.assertEqual(self.receipts, [])
        self.assertEqual(self.key_reads, 0)
        self.assertEqual(self.client.calls, 0)

    def test_06_two_calls_reserve_settle_and_close(self):
        rc = self.run_case()
        self.assertEqual(rc, 0)
        self.assertEqual(self.client.calls, 2)
        self.assertEqual(self.events(), [
            "estimate_reserve", "call_reserve", "call_settle",
            "call_reserve", "call_settle", "reservation_close",
        ])
        settlements = [row for row in self.receipts if json.loads(row["note"])["event"] == "call_settle"]
        self.assertEqual([row["calls"] for row in settlements], [1, 1])
        self.assertAlmostEqual(sum(row["usd"] for row in settlements), 0.0032, places=6)
        self.assertEqual(len(list(self.obs.glob("*.json"))), 2)
        self.assertEqual(json.loads(self.receipts[-1]["note"])["actual_calls"], 2)

    def test_07_provider_error_is_conservatively_receipted_and_stops(self):
        self.client = StubClient(error=RuntimeError("fixture provider error"))
        rc = self.run_case()
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 1)
        self.assertEqual(self.events(), [
            "estimate_reserve", "call_reserve", "call_error_conservative_settle",
            "reservation_close",
        ])
        error_row = self.receipts[2]
        self.assertEqual(error_row["calls"], 1)
        self.assertGreater(error_row["usd"], 0)
        self.assertEqual(len(list(self.obs.glob("*.json"))), 0)

    def test_08_actual_usage_breach_receipts_then_refuses_next_call(self):
        self.client = StubClient([(60000, 100)])
        rc = self.run_case(self.args(max_tokens=50000))
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 1)
        self.assertIn("call_settle", self.events())
        self.assertEqual(len(list(self.obs.glob("*.json"))), 0)

    def test_09_missing_key_closes_reservation_without_provider(self):
        rc = self.run_case(key_loader=lambda: "")
        self.assertEqual(rc, 2)
        self.assertEqual(self.client.calls, 0)
        self.assertEqual(self.events(), ["estimate_reserve", "reservation_close"])

    def test_10_receipt_failure_before_call_stops_provider(self):
        def writer(row):
            event = json.loads(row["note"])["event"]
            if event == "call_reserve":
                raise OSError("fixture ledger failure")
            self.receipts.append(row)

        rc = self.run_case(receipt_writer=writer)
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 0)
        self.assertEqual(self.events(), ["estimate_reserve", "reservation_close"])

    def test_11_missing_price_refuses_before_key(self):
        self.pricing.write_text('{"prices_per_mtok":{}}', encoding="utf-8")
        rc = self.run_case()
        self.assertEqual(rc, 2)
        self.assertEqual(self.key_reads, 0)
        self.assertEqual(self.client.calls, 0)

    def test_12_image_token_formula_and_current_prices(self):
        image_tokens, method = budget.estimate_image_tokens(self.media / "fresh_1.jpg")
        self.assertEqual(image_tokens, 1334)
        self.assertEqual(method, "dimensions_area_div_750")
        prices = budget.load_prices(self.pricing)
        self.assertEqual(prices, {"in": Decimal("1.0"), "out": Decimal("5.0")})

    def test_13_canonical_writer_appends_valid_schema_in_jail(self):
        jail = self.box / "jail"
        (jail / "ledgers").mkdir(parents=True)
        (jail / "ledgers/REGISTRY.json").write_text(self.registry.read_text(), encoding="utf-8")
        prior = os.environ.get("OGZ_JAIL_ROOT")
        os.environ["OGZ_JAIL_ROOT"] = str(jail)
        try:
            writer = budget.canonical_receipt_writer(Path.home() / "OGZ-System")
            writer({
                "id": "fixture", "worker": "batch_extract", "lane": "brain-extraction",
                "calls": 1, "usd": 0.0015, "minutes": 0.0, "status": "done",
                "note": '{"event":"call_settle"}',
            })
        finally:
            if prior is None:
                os.environ.pop("OGZ_JAIL_ROOT", None)
            else:
                os.environ["OGZ_JAIL_ROOT"] = prior
        rows = [json.loads(line) for line in (jail / "ledgers/spend.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["actor"], "batch_extract")
        self.assertEqual(rows[0]["calls"], 1)
        self.assertIn("prev_sha", rows[0])

    def test_14_every_receipt_uses_registered_spend_schema_only(self):
        self.assertEqual(self.run_case(), 0)
        allowed = {"id", "worker", "lane", "calls", "usd", "minutes", "status", "note"}
        self.assertTrue(self.receipts)
        self.assertTrue(all(set(row) == allowed for row in self.receipts))

    def test_15_close_receipt_failure_forces_nonzero(self):
        def writer(row):
            event = json.loads(row["note"])["event"]
            if event == "reservation_close":
                raise budget.BudgetRefusal("fixture close failure")
            self.receipts.append(row)

        rc = self.run_case(receipt_writer=writer)
        self.assertEqual(rc, 2)
        self.assertEqual(self.client.calls, 2)
        self.assertNotIn("reservation_close", self.events())

    def test_16_missing_provider_usage_is_conservatively_settled(self):
        self.client = StubClient([(0, 0)])
        rc = self.run_case()
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 1)
        self.assertEqual(self.events(), [
            "estimate_reserve", "call_reserve", "call_error_conservative_settle",
            "reservation_close",
        ])
        self.assertGreater(self.receipts[2]["usd"], 0)

    def test_17_malformed_provider_usage_is_conservatively_settled(self):
        self.client = StubClient([("not-a-token-count", 5)])
        rc = self.run_case()
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 1)
        self.assertEqual(self.events(), [
            "estimate_reserve", "call_reserve", "call_error_conservative_settle",
            "reservation_close",
        ])

    def test_18_image_mutation_after_estimate_refuses_before_provider(self):
        def mutate_then_key():
            (self.media / "fresh_1.jpg").write_bytes(jpeg(200, 200))
            (self.media / "fresh_2.jpg").write_bytes(jpeg(200, 200))
            return "fixture-key-not-real"

        rc = self.run_case(key_loader=mutate_then_key)
        self.assertEqual(rc, 1)
        self.assertEqual(self.client.calls, 0)
        self.assertEqual(self.events(), ["estimate_reserve", "reservation_close"])

    def test_19_error_settlement_requires_the_authorized_call(self):
        plan = budget.build_plan(
            [self.media / "fresh_1.jpg"],
            ["fixture"],
            "system",
            10,
            budget.BudgetCaps(1, Decimal("0.15"), 60000),
            self.pricing,
        )
        run = budget.BudgetRun(plan, self.receipts.append, "fixture-run")
        run.reserve()
        with self.assertRaises(budget.BudgetRefusal):
            run.settle_error(plan.calls[0], RuntimeError("not authorized"))
        self.assertEqual(self.events(), ["estimate_reserve"])


if __name__ == "__main__":
    unittest.main()
