#!/usr/bin/env python3
"""Idempotent wake64 repair for three missing real-client scaffolds.

This migration adds system contracts only. It never nominates a competitor,
advances trust, invents an event, or changes a client-confirmed red line.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from organ_write import write_organ  # noqa: E402

STRICT_DEFAULT = "STRICTEST (cultural_spec_v1 ~10 override fields)"
STRICT_NOTE = "cannot exist without the client — richest profile lies loudest"

EMPTY_COMPETITOR_SET = {
    "client_given": [],
    "proposed_from_corpus": [],
    "note": "no competitor set recorded — client-given is law; no rival is nominated",
    "requests_log": "events/ledger.jsonl (type=competitor_reference)",
}

L0_TRUST = {
    "level": "L0",
    "ladder": {
        "L0": {
            "name": "per-piece consent",
            "rule": "every published piece needs an explicit client click — the default forever until earned",
        },
        "L1": {
            "name": "pre-approved batch",
            "rule": "PROPOSABLE (never auto-granted) after 10 consecutive unchanged approvals; requires explicit per-batch client consent; any edit/rejection resets the counter",
            "unlock_counter": 0,
            "unlock_at": 10,
            "consent_mechanics": {
                "consent_unit": "the BATCH, never the post — one explicit approval covers only the listed batch",
                "batch_manifest": "every L1 batch lists dates + ULIDs; consent binds only to that list",
                "consent_event": {
                    "type": "client_approved",
                    "subject": "batch:<batch_id>",
                    "confirmer": "client",
                    "note": "scope: the manifest as sent — additions need a new consent",
                },
                "resets": "any edit or rejection inside a consented batch resets the counter and returns it to per-piece review",
                "expiry": "consent covers one batch; the next batch asks again",
                "ceiling": "batch size <= 20; larger sets must be split",
            },
        },
        "L2": {
            "name": "managed",
            "rule": "client delegates within agreed red lines; Mohamed must co-sign the upgrade; one culture breach drops back to L0",
        },
    },
    "history": [],
    "law": "trust climbs by COUNTED approvals, never by time; AI may never advance a level",
    "provenance": {
        "source": "wake64_repair3_system_scaffold",
        "date_added": "2026-07-12",
        "confirmer": "FABLE-wake64",
        "confidence": "system_default",
        "scope": "brand",
    },
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate(root: Path, path: Path, schema_name: str) -> None:
    schema = _read(root / "12_data_shapes" / f"{schema_name}.schema.json")
    jsonschema.validate(_read(path), schema)


def _ensure_exact_file(path: Path, expected: dict, check: bool) -> bool:
    if path.exists():
        if _read(path) != expected:
            raise RuntimeError(f"{path}: existing data differs from wake64 contract")
        return False
    if check:
        raise RuntimeError(f"{path}: missing wake64 scaffold")
    write_organ(path, expected)
    return True


def migrate(root: Path = ROOT, check: bool = False) -> dict:
    changed = []

    red_path = root / "clients" / "myfitness.sa" / "profile" / "red_lines.json"
    red = _read(red_path)
    original_lines = copy.deepcopy(red.get("lines"))
    original_lines_hash = _stable_hash(original_lines)
    for key, expected in (("defaults_pinned", STRICT_DEFAULT), ("note", STRICT_NOTE)):
        current = red.get(key)
        if current is not None and current != expected:
            raise RuntimeError(f"myfitness.sa/red_lines.{key}: value differs from wake64 contract")
        if current is None:
            if check:
                raise RuntimeError(f"myfitness.sa/red_lines.{key}: missing wake64 scaffold")
            red[key] = expected
    if red != _read(red_path):
        write_organ(red_path, red)
        changed.append("myfitness.sa/red_lines")
    if _stable_hash(_read(red_path).get("lines")) != original_lines_hash:
        raise RuntimeError("myfitness.sa/red_lines: confirmed lines changed")

    competitor_path = root / "clients" / "alnasserjewelry" / "profile" / "competitor_set.json"
    if _ensure_exact_file(competitor_path, EMPTY_COMPETITOR_SET, check):
        changed.append("alnasserjewelry/competitor_set")

    trust_path = root / "clients" / "alnasserjewelry" / "profile" / "trust.json"
    if _ensure_exact_file(trust_path, L0_TRUST, check):
        changed.append("alnasserjewelry/trust")

    _validate(root, red_path, "client_red_lines_v1")
    _validate(root, competitor_path, "client_competitor_set_v1")
    _validate(root, trust_path, "client_trust_v1")
    return {
        "changed": changed,
        "total_scaffolds": 3,
        "myfitness_confirmed_lines_sha256": original_lines_hash,
        "alnasser_competitors_nominated": 0,
        "alnasser_trust_level": "L0",
        "alnasser_trust_counter": 0,
        "alnasser_trust_history_rows": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    print(json.dumps(migrate(check=args.check), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
