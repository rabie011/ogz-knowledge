#!/usr/bin/env python3
"""
fill_visual_complexity.py
Derive visual_complexity_score from existing filled fields — no new data needed.

Score = props_count + character_count + text_overlay_count
Label:
  0–1  → minimal
  2–3  → simple
  4–6  → moderate
  7+   → complex

Adds visual_complexity_score (int) + visual_complexity (string label) to schema + obs.
Output: logs/fill_visual_complexity_report.json
"""
import json
from collections import Counter
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"
LOGS        = BASE / "logs"

LABELS = ["minimal", "simple", "moderate", "complex"]

def _ensure_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    vo_props = schema["properties"]["visual_observations"]["properties"]
    changed = False
    if "visual_complexity_score" not in vo_props:
        vo_props["visual_complexity_score"] = {
            "type": ["integer", "null"],
            "description": "props_count + character_count + text_overlay_count"
        }
        changed = True
    if "visual_complexity" not in vo_props:
        vo_props["visual_complexity"] = {
            "type": ["string", "null"],
            "enum": LABELS + [None],
            "description": "minimal (0-1) / simple (2-3) / moderate (4-6) / complex (7+)"
        }
        changed = True
    if changed:
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added visual_complexity_score, visual_complexity")

def _score(d) -> int:
    vis = d.get("visual_observations", {})
    props      = len(vis.get("props_visible", []) or [])
    chars      = (vis.get("characters_visible", {}) or {}).get("count", 0) or 0
    overlays   = len(vis.get("text_overlays", []) or [])
    return props + chars + overlays

def _label(score: int) -> str:
    if score <= 1: return "minimal"
    if score <= 3: return "simple"
    if score <= 6: return "moderate"
    return "complex"

def main():
    _ensure_schema()
    updated = skipped = 0
    dist = Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        vo = d.get("visual_observations", {})
        if vo.get("visual_complexity") is not None:
            skipped += 1
            continue
        score = _score(d)
        label = _label(score)
        vo["visual_complexity_score"] = score
        vo["visual_complexity"] = label
        d["visual_observations"] = vo
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        dist[label] += 1

    print(f"visual_complexity filled: {updated}  |  skipped: {skipped}")
    print("Distribution:")
    for lbl in LABELS:
        print(f"  {lbl:<10}  {dist[lbl]}")

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_visual_complexity_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "distribution": dict(dist)},
                   ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
