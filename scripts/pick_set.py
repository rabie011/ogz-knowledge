#!/usr/bin/env python3
"""READER for pick_set_v1 records (B079, MAJORS LAW).

A schema with no reader is a write-only organ (Rule #6 — Consumer Law). This module
IS the reader: it validates a pick-set against 12_data_shapes/pick_set_v1.schema.json
AND enforces the cross-field invariants JSON Schema can't express on its own:

  - status=picked  → picked is set, equals one candidate's option_id, picker is set,
                      and resulting_event_ulid is present (no orphan picks).
  - status=open    → picked / picker / resulting_event_ulid are all null/absent.
  - diversity_ok is False  → REFUSE (Rule #8): a converged set must never carry a
                      real pick; it has to be re-rendered, not picked.

REFUSE, DON'T WARN (Rule #8): every failure raises PickSetError; nothing returns a
soft pass. Mirrors ledger_write's validate-before-write contract.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
SCHEMA_DIR = BASE / "12_data_shapes"
_VALIDATOR = None


class PickSetError(ValueError):
    """A pick-set that breaks the contract. Raised, never warned."""


def _validator():
    """Build a validator with a registry over 12_data_shapes/ so $ref (e.g. the
    provenance mixin) resolves by filename — the house $id convention."""
    global _VALIDATOR
    if _VALIDATOR is None:
        import jsonschema
        from referencing import Registry, Resource
        resources = []
        for f in SCHEMA_DIR.glob("*.schema.json"):
            doc = json.loads(f.read_text())
            resources.append((f.name, Resource.from_contents(doc)))
        registry = Registry().with_resources(resources)
        schema = json.loads((SCHEMA_DIR / "pick_set_v1.schema.json").read_text())
        _VALIDATOR = jsonschema.Draft202012Validator(schema, registry=registry)
    return _VALIDATOR


def validate(rec: dict) -> dict:
    """Validate a pick_set record. Returns it on success; raises PickSetError otherwise."""
    import jsonschema
    try:
        self_v = _validator()
        errors = sorted(self_v.iter_errors(rec), key=lambda e: e.path)
        if errors:
            raise PickSetError(f"schema: {errors[0].message}")
    except jsonschema.exceptions.ValidationError as e:
        raise PickSetError(f"schema: {e.message}") from e

    status = rec.get("status")
    cand_ids = [c["option_id"] for c in rec.get("candidates", [])]
    if len(set(cand_ids)) != len(cand_ids):
        raise PickSetError(f"candidate option_ids must be unique: {cand_ids}")

    if status == "picked":
        picked = rec.get("picked")
        if not picked:
            raise PickSetError("status=picked but no `picked` option_id")
        if picked not in cand_ids:
            raise PickSetError(f"`picked`={picked!r} is not one of the candidates {cand_ids}")
        if not rec.get("picker"):
            raise PickSetError("status=picked but no `picker` (mohamed|client)")
        if not rec.get("resulting_event_ulid"):
            raise PickSetError("status=picked but no `resulting_event_ulid` — orphan pick (Consumer Law)")
    elif status == "open":
        if rec.get("picked") or rec.get("picker") or rec.get("resulting_event_ulid"):
            raise PickSetError("status=open but pick fields are already set")

    if rec.get("diversity_ok") is False and status not in ("voided", "expired"):
        raise PickSetError("diversity_ok=False must be voided/expired, never picked (Rule #8)")

    return rec


def is_valid(rec: dict) -> bool:
    try:
        validate(rec)
        return True
    except PickSetError:
        return False


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        rec = json.loads(Path(p).read_text())
        validate(rec)
        print(f"✅ {p}: valid pick_set ({rec.get('status')})")
