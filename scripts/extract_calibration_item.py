#!/usr/bin/env python3
"""
extract_calibration_item.py
Runs the REAL vision compliance pipeline (GPT-4o vision) on a single
calibration image and writes a claude_extractions/<item>_extraction.json.

This is the negative-control path for item_02 (left-hand serving violation).
The model is given the universal forbidden-gesture rubric (exactly what the
CCO QC agent reads at compliance time) but is NEVER told the expected answer.
It must perceive hand-handedness itself and decide whether a hard block fires.

Usage:
    python3 scripts/extract_calibration_item.py item_02

Key is read from ~/.abraham_env as a FILE (shell does not auto-source it).
"""
from __future__ import annotations

import base64
import json
import os
import random
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI

REPO = Path(__file__).resolve().parent.parent
CALIB = REPO / "11_who_to_learn_from" / "_calibration_set"
CONTENT = CALIB / "content"
OUT = CALIB / "claude_extractions"
FORBIDDEN = REPO / "15_cultural_specs" / "forbidden_lists" / "universal_gestures_forbidden.yaml"
ENV_FILE = Path.home() / ".abraham_env"

MODEL = "gpt-4o"  # full GPT-4o vision, per calibration spec
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def load_key() -> str:
    """Read OPENAI_API_KEY straight from ~/.abraham_env (not os.environ)."""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if line.startswith("OPENAI_API_KEY="):
            val = line.split("=", 1)[1].strip()
            return val.strip('"').strip("'")
    raise RuntimeError("OPENAI_API_KEY not found in ~/.abraham_env")


def make_ulid() -> str:
    ts = int(time.time() * 1000)
    ts_part, t = "", ts
    for _ in range(10):
        ts_part = CROCKFORD[t % 32] + ts_part
        t //= 32
    rand_part = "".join(random.choice(CROCKFORD) for _ in range(16))
    return ts_part + rand_part


def b64_data_url(path: Path) -> str:
    raw = path.read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def build_prompt() -> str:
    forbidden = yaml.safe_load(FORBIDDEN.read_text())
    rubric_lines = []
    for e in forbidden["entries"]:
        rubric_lines.append(
            f'  - name: {e["name"]} | severity: {e["severity"]} | {e["description"]}'
        )
    rubric = "\n".join(rubric_lines)
    return f"""You are the CCO compliance vision analyst for a Saudi-native creative
intelligence platform. Analyse the attached branded-content image and return a
SINGLE JSON object (no markdown fences) with EXACTLY these keys:

{{
  "visual_observations": {{
    "composition_style": str,
    "lighting": str,
    "color_palette_dominant": [str, ...],
    "props_visible": [str, ...],
    "setting": str,
    "characters_visible": {{
      "count": int,
      "gender_presentation": str|null,
      "wardrobe_notes": str|null,
      "gesture_notes": str|null
    }},
    "hands_analysis": [
      {{"which_hand": "left"|"right"|"uncertain", "action": str, "reasoning": str}}
    ],
    "text_overlays": str,
    "notable_visual_elements": str
  }},
  "voice_observations": {{
    "language": str, "dialect_detected": str|null, "register": str,
    "tone": str, "notable_phrases": [str, ...], "call_to_action_present": bool
  }},
  "compliance_check": {{
    "hard_blocks_triggered": [
      {{"entry_name": str, "severity": str, "evidence": str}}
    ],
    "soft_flags": [str, ...],
    "overall_compliance": "clean"|"soft_flagged"|"hard_blocked"
  }},
  "cultural_notes": {{
    "regional_orientation_detected": str,
    "occasion_relevance": str,
    "hospitality_cues": [str, ...]
  }},
  "quality_assessment": {{
    "production_quality": str,
    "brand_consistency_with_account": str,
    "engagement_potential": str
  }}
}}

COMPLIANCE RUBRIC — universal forbidden gestures (hard_block). For ANY visible
human hand, first determine left vs right (state your reasoning in
hands_analysis), then check it against these rules. If a rule is matched, add it
to hard_blocks_triggered using the EXACT name below and set overall_compliance
to "hard_blocked":
{rubric}

Be rigorous and literal about hand-handedness — examine thumb position, finger
order, and the back-vs-palm of the hand. Report exactly what you observe. Do not
assume content is clean; do not assume it is a violation. Return ONLY the JSON.
"""


def main() -> int:
    item = sys.argv[1] if len(sys.argv) > 1 else "item_02"
    img = CONTENT / f"{item}.jpg"
    if not img.exists():
        print(f"ERROR: {img} not found", file=sys.stderr)
        return 2

    client = OpenAI(api_key=load_key(), timeout=90.0, max_retries=2)
    prompt = build_prompt()

    print(f"→ Sending {item}.jpg to {MODEL} (detail=high, temperature=0)…", flush=True)
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=1200,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You return only valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": b64_data_url(img), "detail": "high"}},
            ]},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    print("═══ RAW GPT-4o RESPONSE ═══")
    print(raw)
    print("═══════════════════════════\n")

    model_out = json.loads(raw)

    extraction = {
        "observation_ulid": make_ulid(),
        "schema_version": 1,
        "account_handle_normalized": "OGZ-F-AND-B-Calibration-Violation-002",
        "account_ulid": "01KRKHS8R8SNJ8VJ56WKSQTS28",
        "sector": "f_and_b",
        "calibration_item": item,
        "content_ref": {
            "filename": f"{item}.jpg",
            "platform": "instagram",
            "content_type": "image",
            "capture_date": "calibration",
            "source_url": None,
            "day_of_week": None,
        },
        "visual_observations": model_out.get("visual_observations", {}),
        "voice_observations": model_out.get("voice_observations", {}),
        "compliance_check": model_out.get("compliance_check", {}),
        "cultural_notes": model_out.get("cultural_notes", {}),
        "pattern_matches": [],
        "quality_assessment": model_out.get("quality_assessment", {}),
        "provenance": {
            "source": "calibration_extraction:vision_api",
            "extraction_method": "gpt-4o_vision",
            "model": MODEL,
            "date_extracted": "2026-06-11",
            "confidence": "experimental",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{item}_extraction.json"
    out_path.write_text(json.dumps(extraction, indent=2, ensure_ascii=False))
    print(f"✓ Written: {out_path}")

    cc = extraction["compliance_check"]
    print("\n── COMPLIANCE SUMMARY ──")
    print(f"  overall_compliance: {cc.get('overall_compliance')}")
    print(f"  hard_blocks_triggered: "
          f"{[b.get('entry_name') for b in cc.get('hard_blocks_triggered', [])]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
