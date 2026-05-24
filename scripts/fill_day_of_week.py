#!/usr/bin/env python3
"""
fill_day_of_week.py
Derive day_of_week from content_ref.capture_date.
Adds to schema + fills all obs that have capture_date.
"""
import json
from datetime import datetime
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"
DAYS        = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def _ensure_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    cr_props = schema["properties"]["content_ref"]["properties"]
    if "day_of_week" not in cr_props:
        cr_props["day_of_week"] = {
            "type": ["string","null"],
            "enum": DAYS + [None],
            "description": "Day of week the content was posted (derived from capture_date)"
        }
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added content_ref.day_of_week")

def main():
    _ensure_schema()
    updated = skipped = no_date = 0
    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        cr = d.get("content_ref", {})
        if cr.get("day_of_week") is not None:
            skipped += 1
            continue
        dt_str = cr.get("capture_date")
        if not dt_str:
            no_date += 1
            continue
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d")
            cr["day_of_week"] = dt.strftime("%A").lower()
            d["content_ref"] = cr
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            updated += 1
        except Exception:
            no_date += 1

    print(f"day_of_week filled: {updated}  |  skipped: {skipped}  |  no_date: {no_date}")

if __name__ == "__main__":
    main()
