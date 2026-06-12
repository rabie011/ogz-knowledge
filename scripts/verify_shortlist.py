#!/usr/bin/env python3
"""Shortlist integrity: every candidate must be live-verified (the Excel-handle scar,
June 12: 5/5 candidates failed live checks — mangled/foreign/restricted)."""
import json
from pathlib import Path
sl = json.loads((Path(__file__).parent.parent / "data/pilot_shortlist.json").read_text())
entries = sl.get("shortlist", [])
assert entries, "shortlist empty"
for e in entries:
    assert e.get("verified_live") is True, f"{e.get('handle')}: not live-verified"
    v = e.get("verification") or {}
    assert v.get("date") and v.get("followers"), f"{e.get('handle')}: verification record incomplete"
print(f"ok: {len(entries)} candidates, all live-verified with records")
