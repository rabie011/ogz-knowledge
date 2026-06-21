#!/usr/bin/env python3
"""Cultural gate (P2, June 11) — connect the 80-field moat to the live filter.
The 4 forbidden_lists (behaviors/gestures/props/visuals) + Saudi red lines were
ENFORCED NOWHERE in the caption path (the live check matched English substrings
against Arabic). This compiles them into one JSON the caption_filter consumes.
Doctrine: bans live in code/data, never in the generation prompt.
Output: data/cultural_gate.json
"""
import json, glob, sys
from pathlib import Path
import yaml

BASE = Path(__file__).parent.parent
OUT = BASE / "data" / "cultural_gate.json"


def main():
    gate = {"_meta": {"built": "2026-06-11", "source": "15_cultural_specs/forbidden_lists + 04_saudi_rules",
                       "note": "caption-relevant entries (text-detectable); visual-only entries kept for the render stage"},
            "hard_block": [], "ramadan_only": [], "red_lines": []}
    for f in glob.glob(str(BASE / "15_cultural_specs/forbidden_lists/*.yaml")):
        d = yaml.safe_load(open(f).read().split("---", 1)[-1])
        kind = d.get("list_kind", "")
        for e in d.get("entries", []):
            item = {"name": e.get("name"), "kind": kind, "severity": e.get("severity", ""),
                    "description": e.get("description", ""), "hints": e.get("detection_hints", [])}
            if any("ramadan" in str(h).lower() for h in e.get("detection_hints", [])):
                gate["ramadan_only"].append(item)
            else:
                gate["hard_block"].append(item)
    # Saudi red lines (Mohamed's hard rules) from 04_saudi_rules
    for f in glob.glob(str(BASE / "04_saudi_rules/*.yaml")) + glob.glob(str(BASE / "04_saudi_rules/*.json")):
        try:
            d = yaml.safe_load(open(f).read().split("---", 1)[-1]) if f.endswith(".yaml") else json.loads(open(f).read())
        except Exception:
            continue
        for key in ("red_lines", "forbidden", "hard_rules"):
            v = d.get(key) if isinstance(d, dict) else None
            if isinstance(v, list):
                gate["red_lines"].extend(v)
    # Rule #8 (refuse, don't warn) — the moat must never be compiled EMPTY. A build that finds
    # zero hard-blocks AND zero red-lines means the forbidden_lists / 04_saudi_rules sources are
    # missing or unparsed, and the caption_filter would consume a TOOTHLESS gate (silent severing
    # of the cultural moat — exactly the adversarial-audit hole). Refuse to write a hollow gate.
    if not gate["hard_block"] and not gate["red_lines"]:
        sys.exit("🛑 REFUSED: cultural_gate would be EMPTY (0 hard-block, 0 red-lines) — the moat "
                 "sources (15_cultural_specs/forbidden_lists + 04_saudi_rules) are missing/unparsed. "
                 "A toothless gate is worse than none; not writing it (Rule #8).")
    OUT.write_text(json.dumps(gate, ensure_ascii=False, indent=2))
    print(f"✓ cultural_gate.json: {len(gate['hard_block'])} hard-block · {len(gate['ramadan_only'])} ramadan-only · {len(gate['red_lines'])} red-lines")


if __name__ == "__main__":
    main()
