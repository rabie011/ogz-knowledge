#!/usr/bin/env python3
"""LEDGER WRITE GATE (B081, June 12 — RABIE's pick).
The ledgers feed the trust engine and the crystallize loop; a malformed event
poisons both silently. Every writer now appends through here — the event is
validated against client_event_v1 BEFORE it touches the file. Invalid = raise
(assert law: refuse loudly, never half-write).
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads((BASE / "12_data_shapes/client_event_v1.schema.json").read_text())
    return _SCHEMA


def ledger_write(handle: str, event: dict):
    import jsonschema
    jsonschema.validate(event, _schema())          # raises on contract breach
    from approvers_registry import check_confirmer
    check_confirmer(event)                          # B156: trust moves on human hands only
    lf = BASE / "clients" / handle / "events/ledger.jsonl"
    lf.parent.mkdir(parents=True, exist_ok=True)
    with open(lf, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
