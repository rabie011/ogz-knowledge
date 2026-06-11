#!/usr/bin/env python3
"""
Calibration accuracy tester.
Compares Claude Code extractions against Mohamed's ground truth.

3 levels:
  Level 1 (CRITICAL): item_02 must trigger hard_blocks_triggered with left_hand_serving
  Level 2: field completeness across all items (target >= 80%)
  Level 3: field accuracy vs ground truth (target >= 60%)

Exit codes:
  0 = all pass
  1 = Level 1 fail (hard block not detected)
  2 = Level 2 fail (completeness below threshold)
  3 = Level 3 fail (accuracy below threshold)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CALIBRATION_DIR = REPO_ROOT / "11_who_to_learn_from" / "_calibration_set"
GROUND_TRUTH_PATH = CALIBRATION_DIR / "GROUND_TRUTH.yaml"
EXTRACTIONS_DIR = CALIBRATION_DIR / "claude_extractions"

COMPLETENESS_THRESHOLD = 0.80
ACCURACY_THRESHOLD = 0.60

REQUIRED_FIELDS = [
    "observation_ulid",
    "schema_version",
    "account_handle_normalized",
    "account_ulid",
    "sector",
    "content_ref",
    "visual_observations",
    "compliance_check",
    "cultural_notes",
    "quality_assessment",
    "provenance",
]


def load_ground_truth() -> dict | None:
    if not GROUND_TRUTH_PATH.exists():
        return None
    with open(GROUND_TRUTH_PATH) as f:
        return yaml.safe_load(f)


def load_extractions() -> dict[str, dict]:
    """Load extractions keyed by the content_ref.filename stem (e.g. 'item_02')."""
    results: dict[str, dict] = {}
    if not EXTRACTIONS_DIR.exists():
        return results
    for fp in EXTRACTIONS_DIR.glob("*.json"):
        with open(fp) as f:
            data = json.load(f)
        filename = data.get("content_ref", {}).get("filename", "")
        stem = Path(filename).stem
        if stem:
            results[stem] = data
    return results


def level_1_hard_block(ground_truth: dict, extractions: dict[str, dict]) -> bool:
    """Check that every expected hard block is detected. item_02 is critical."""
    all_pass = True

    for gt_item in ground_truth.get("items", []):
        item_id = gt_item.get("item_id", "")
        expected_blocks = gt_item.get("expected_hard_blocks") or []
        if not expected_blocks:
            continue

        extraction = extractions.get(item_id)
        if extraction is None:
            print(f"  ✗ {item_id}: no extraction found")
            all_pass = False
            continue

        triggered = extraction.get("compliance_check", {}).get("hard_blocks_triggered", [])
        triggered_names = {b.get("entry_name") for b in triggered}

        for expected in expected_blocks:
            name = expected.get("entry_name", "")
            if name in triggered_names:
                print(f"  ✓ {item_id}: '{name}' detected")
            else:
                print(f"  ✗ {item_id}: '{name}' NOT detected")
                all_pass = False

    return all_pass


def level_2_completeness(extractions: dict[str, dict]) -> float:
    """Check required fields are present and non-null across all extractions."""
    if not extractions:
        return 0.0

    total_checks = 0
    present = 0

    for item_id, data in sorted(extractions.items()):
        for field in REQUIRED_FIELDS:
            total_checks += 1
            if field in data and data[field] is not None:
                present += 1
            else:
                print(f"  - {item_id}: missing '{field}'")

    ratio = present / total_checks if total_checks > 0 else 0.0
    return ratio


def level_3_accuracy(ground_truth: dict, extractions: dict[str, dict]) -> float:
    """Compare extraction values against ground truth where ground truth is non-null."""
    checks = 0
    correct = 0

    for gt_item in ground_truth.get("items", []):
        item_id = gt_item.get("item_id", "")
        extraction = extractions.get(item_id)
        if extraction is None:
            continue

        gt_compliance = gt_item.get("expected_compliance")
        if gt_compliance is not None:
            checks += 1
            ext_compliance = extraction.get("compliance_check", {}).get("overall_compliance")
            if ext_compliance == gt_compliance:
                correct += 1
            else:
                print(f"  - {item_id}: compliance expected '{gt_compliance}', got '{ext_compliance}'")

        gt_vis = gt_item.get("key_visual_observations", {})
        ext_vis = extraction.get("visual_observations", {})

        gt_comp = gt_vis.get("composition_style")
        if gt_comp is not None:
            checks += 1
            ext_comp = ext_vis.get("composition_style", "")
            if gt_comp.lower() in ext_comp.lower() or ext_comp.lower() in gt_comp.lower():
                correct += 1
            else:
                print(f"  - {item_id}: composition expected '{gt_comp}', got '{ext_comp}'")

        gt_props = gt_vis.get("props_visible") or []
        ext_props = ext_vis.get("props_visible") or []
        if gt_props:
            checks += 1
            gt_set = {p.lower() for p in gt_props}
            ext_set = {p.lower() for p in ext_props}
            if gt_set & ext_set:
                correct += 1
            else:
                print(f"  - {item_id}: props no overlap — expected {gt_props}, got {ext_props}")

        gt_voice = gt_item.get("key_voice_observations", {})
        gt_dialect = gt_voice.get("dialect_detected")
        if gt_dialect is not None:
            checks += 1
            ext_dialect = extraction.get("voice_observations", {}).get("dialect_detected")
            if ext_dialect and gt_dialect.lower() in ext_dialect.lower():
                correct += 1
            else:
                print(f"  - {item_id}: dialect expected '{gt_dialect}', got '{ext_dialect}'")

    ratio = correct / checks if checks > 0 else 1.0
    return ratio


def main() -> int:
    ground_truth = load_ground_truth()
    extractions = load_extractions()

    if ground_truth is None:
        print("No GROUND_TRUTH.yaml found — calibration not yet set up.")
        print("See _calibration_set/CALIBRATION_SETUP_GUIDE.md to get started.")
        return 0

    if not extractions:
        print("No extractions found in _calibration_set/claude_extractions/.")
        print("Run Claude Code on the calibration set first.")
        return 0

    print(f"Found {len(extractions)} extraction(s) against "
          f"{len(ground_truth.get('items', []))} ground truth item(s).\n")

    # Level 1: Hard block detection (CRITICAL)
    print("═══ Level 1: Hard Block Detection ═══")
    l1_pass = level_1_hard_block(ground_truth, extractions)
    if not l1_pass:
        print("\n✗ LEVEL 1 FAILED — hard block not detected.")
        print("  STOP. Do not proceed to real extraction.")
        print("  Fix the extraction prompt and re-run calibration.")
        return 1
    print("✓ Level 1 passed.\n")

    # Level 2: Field completeness
    print("═══ Level 2: Field Completeness ═══")
    completeness = level_2_completeness(extractions)
    print(f"\nCompleteness: {completeness:.0%} (threshold: {COMPLETENESS_THRESHOLD:.0%})")
    if completeness < COMPLETENESS_THRESHOLD:
        print("✗ LEVEL 2 FAILED — too many missing fields.")
        return 2
    print("✓ Level 2 passed.\n")

    # Level 3: Field accuracy
    print("═══ Level 3: Field Accuracy ═══")
    accuracy = level_3_accuracy(ground_truth, extractions)
    print(f"\nAccuracy: {accuracy:.0%} (threshold: {ACCURACY_THRESHOLD:.0%})")
    if accuracy < ACCURACY_THRESHOLD:
        print("✗ LEVEL 3 FAILED — accuracy below threshold.")
        return 3
    print("✓ Level 3 passed.\n")

    print("═══ ALL LEVELS PASSED ═══")
    print("Calibration successful. Proceed to real extraction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
