#!/usr/bin/env python3
"""
Validate every record in the repo against its schema.
Handles JSON (chains) and YAML (sectors, occasions, Saudi rules).
Exits 0 if all valid, 1 otherwise.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "12_data_shapes"


def build_registry() -> Registry:
    """Load all *.schema.json files into a Registry so cross-file $ref resolves."""
    registry = Registry()
    for sf in SCHEMA_DIR.glob("*.schema.json"):
        with open(sf) as f:
            schema = json.load(f)
        registry = registry.with_resource(sf.name, Resource.from_contents(schema))
    return registry


# folder_path → (glob_pattern, schema_filename_or_None, format)
#   format: 'json' / 'yaml' / 'md_frontmatter'
#   schema_filename of None = no formal schema; we run a lightweight provenance check instead
FOLDER_TO_SCHEMA: dict[str, tuple[str, str | None, str]] = {
    "02_what_to_build":   ("tf*.json", "chain_v1.schema.json",           "json"),
    "05_sector_defaults": ("*.yaml",   "sector_baseline_v1.schema.json", "yaml"),
    "06_saudi_calendar":  ("*.yaml",   "occasion_v1.schema.json",        "yaml"),
    "04_saudi_rules":     ("*.yaml",   None,                             "yaml"),
    "10_agent_brains":    ("*.yaml",   None,                             "yaml"),
    "20_cd_brains":       ("cd_0*.md", "cd_brain_v1.schema.json",        "md_frontmatter"),
    # Day 3 cultural specs are added below when written:
    "15_cultural_specs":  ("sector_defaults/*.yaml", "cultural_spec_v1.schema.json", "yaml"),
    "15_cultural_specs/forbidden_lists":  ("*.yaml",  None,                          "yaml"),
    "11_who_to_learn_from/accounts":      ("**/*.json", "benchmark_account_v1.schema.json", "json"),
    "11_who_to_learn_from/patterns":      ("**/*.json", "account_pattern_v1.schema.json",   "json"),
    "01_how_to_decide":                   ("*.yaml",  None,                          "yaml"),
    "21_campaign_archive/campaigns":      ("*.json",  "campaign_archive_v1.schema.json", "json"),
    "22_org_context":                     ("*.yaml",  None,                          "yaml"),
}


def load_record(path: Path, fmt: str):
    """Load a record from disk in the given format. Strips $schema editor hint if present."""
    if fmt == "json":
        with open(path) as f:
            data = json.load(f)
    elif fmt == "yaml":
        with open(path) as f:
            data = yaml.safe_load(f)
    elif fmt == "md_frontmatter":
        text = path.read_text()
        if not text.startswith("---\n"):
            raise ValueError(f"missing YAML front-matter (no leading '---')")
        end = text.find("\n---\n", 4)
        if end < 0:
            raise ValueError("unterminated YAML front-matter (no closing '---')")
        data = yaml.safe_load(text[4:end])
    else:
        raise ValueError(f"unsupported format: {fmt}")
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k != "$schema"}
    return data


def validate_provenance_only(record: dict) -> list[str]:
    """For schemaless config files, verify provenance block is present and well-formed."""
    errors: list[str] = []
    prov = record.get("provenance") if isinstance(record, dict) else None
    if not isinstance(prov, dict):
        return ["missing or non-object 'provenance' block"]
    for k in ["source", "date_added", "confirmer", "confidence", "scope"]:
        if k not in prov:
            errors.append(f"provenance missing '{k}'")
    if prov.get("confidence") not in {"confirmed", "inferred", "experimental"}:
        errors.append(f"provenance.confidence invalid: {prov.get('confidence')!r}")
    return errors


def main() -> int:
    registry = build_registry()
    total = 0
    failed = 0
    errors_by_file: dict[str, list[str]] = {}

    for folder_name, (pattern, schema_name, fmt) in FOLDER_TO_SCHEMA.items():
        folder = REPO_ROOT / folder_name
        if not folder.exists():
            continue

        validator = None
        if schema_name is not None:
            with open(SCHEMA_DIR / schema_name) as f:
                schema = json.load(f)
            validator = Draft202012Validator(schema, registry=registry)

        for record_file in folder.rglob(pattern):
            total += 1
            try:
                record = load_record(record_file, fmt)
            except Exception as e:
                failed += 1
                errors_by_file[str(record_file.relative_to(REPO_ROOT))] = [f"load failed: {e}"]
                continue

            if validator is not None:
                errs = list(validator.iter_errors(record))
                if errs:
                    failed += 1
                    errors_by_file[str(record_file.relative_to(REPO_ROOT))] = [
                        f"[{'.'.join(str(p) for p in e.absolute_path) or '<root>'}] {e.message}"
                        for e in errs
                    ]
            else:
                errs = validate_provenance_only(record)
                if errs:
                    failed += 1
                    errors_by_file[str(record_file.relative_to(REPO_ROOT))] = errs

    print(f"Validated: {total - failed}/{total}")
    if errors_by_file:
        print(f"\nFailures ({failed}):")
        for fp, msgs in list(errors_by_file.items())[:20]:
            print(f"\n  {fp}:")
            for msg in msgs[:5]:
                print(f"    {msg}")
        return 1
    print("All records valid ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
