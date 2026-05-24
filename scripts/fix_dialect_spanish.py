#!/usr/bin/env python3
"""
fix_dialect_spanish.py
Rename 'spanish_colloquial' → 'unknown' in dialect_detected.
Crumbl Cookies (US brand) was mislabeled — corrupts Saudi dialect analytics.
"""
import json
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"

fixed = 0
for f in OBS_ROOT.rglob("*.json"):
    d  = json.loads(f.read_text())
    vo = d.get("voice_observations", {})
    if vo.get("dialect_detected") == "spanish_colloquial":
        vo["dialect_detected"] = "unknown"
        d["voice_observations"] = vo
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        fixed += 1

print(f"Fixed: {fixed} obs  (spanish_colloquial → unknown)")
