#!/usr/bin/env python3
"""
Validate JSON records against their schemas.
Handles cross-schema $ref resolution for the provenance_mixin pattern.
"""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "12_data_shapes"

def load_registry():
    """Load all schemas into a referencing Registry for cross-file $ref."""
    registry = Registry()
    for schema_file in SCHEMA_DIR.glob("*.schema.json"):
        with open(schema_file) as f:
            schema = json.load(f)
        # Register by filename so relative $ref works
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(schema_file.name, resource)
    return registry

def validate_file(record_path, schema_path):
    """Validate one record against one schema."""
    with open(schema_path) as f:
        schema = json.load(f)
    with open(record_path) as f:
        record = json.load(f)
    # Strip the local $schema field — it's an editor hint, not part of validation
    record_for_validation = {k: v for k, v in record.items() if k != "$schema"}
    registry = load_registry()
    validator = Draft202012Validator(schema, registry=registry)
    errors = list(validator.iter_errors(record_for_validation))
    return errors

if __name__ == "__main__":
    record_path = sys.argv[1]
    schema_path = sys.argv[2]
    errors = validate_file(record_path, schema_path)
    if errors:
        print(f"✗ {record_path}")
        for e in errors:
            path = ".".join(str(p) for p in e.absolute_path) or "<root>"
            print(f"  [{path}] {e.message}")
        sys.exit(1)
    else:
        print(f"✓ {record_path}")
        sys.exit(0)
