#!/usr/bin/env python3
"""
compliance_read.py — B125f: the FIRST VOTE — a GPT-4o forbidden-list COMPLIANCE
vision read on a RENDERED image.

This is the WRITER that vision_second_vote.py (B125, the second vote / reader) was
built to consume. The severed-wire root, found by the RABIE+DeepSeek panel on
2026-06-30 (Rule #6 / consult-before-build): apply_second_vote() expected a
single_result shaped {overall_compliance, hard_blocks_triggered} on a RENDERED
image, but NO live producer emitted that shape — only the offline extraction path
(extract_calibration_item.py) did, on reference content. B125f is that producer for
the live produce/publish path.

  single-model FIRST vote  =  compliance_read()        (here, GPT-4o — OpenAI FUNDED)
  optional SECOND vote     =  apply_second_vote()      (Anthropic — DRY, fail-safe no-op)

DESIGN (mirrors vision_second_vote.py):
  - PURE CORE: normalize() turns a raw GPT JSON reply into the canonical
    {overall_compliance, hard_blocks_triggered, raised_by} shape. No I/O. Unit-tested.
    It is CONSERVATIVE: any hard_blocks_triggered forces overall_compliance="hard_blocked"
    (the two can never disagree), and an unrecognised compliance label is treated as a
    NON-pass ("soft_flagged") rather than silently cleared.
  - IMPURE EDGE: _call_gpt_vision() — the single live OpenAI vision call. Mocked in tests.
  - compliance_read() — orchestrates: call the edge, normalize. On API failure it RAISES
    (Rule #8 REFUSE-don't-warn — a read that cannot read must never pass silently); the
    caller/wire decides the fallback, it is not hidden here.

The forbidden-gesture rubric prompt + OpenAI key + image encoding are REUSED verbatim
from extract_calibration_item.py (DRY — the model must read the EXACT rubric the
calibration negative-control used; left_hand_serving / alcohol / pork / gambling / kaaba …).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# DRY: the rubric prompt, key loader, image encoder, and model name are owned by the
# calibration extractor (import-safe — functions + constants only, main() guarded).
import extract_calibration_item as _calib

VALID_COMPLIANCE = ("clean", "soft_flagged", "hard_blocked")


# ─────────────────────────────────────────────────────────────────────────────
# PURE CORE — no network, fully unit-tested.
# ─────────────────────────────────────────────────────────────────────────────
def normalize(model_out: dict, *, raised_by: str = "compliance_read") -> dict:
    """
    Turn a raw GPT JSON reply into the canonical compliance shape consumed by
    vision_second_vote.reconcile():  {overall_compliance, hard_blocks_triggered}.

    PURE + CONSERVATIVE:
      - the model may return the compliance fields at the top level OR nested under
        "compliance_check" (the extract_calibration_item rubric nests them) — accept both.
      - any hard_blocks_triggered forces overall_compliance="hard_blocked" (they can
        never disagree — a block with a "clean" label would be a silent fail-open).
      - an unrecognised / missing compliance label with no blocks is a NON-pass
        ("soft_flagged"), never silently "clean".
      - every hard block dict is stamped with raised_by if it carries no source.
    """
    if not isinstance(model_out, dict):
        model_out = {}
    # accept either nested (rubric) or flat shape
    cc = model_out.get("compliance_check")
    src = cc if isinstance(cc, dict) else model_out

    blocks = src.get("hard_blocks_triggered") or []
    if not isinstance(blocks, list):
        blocks = []
    clean_blocks = []
    for b in blocks:
        if isinstance(b, dict) and b.get("entry_name"):
            b = dict(b)
            b.setdefault("raised_by", raised_by)
            clean_blocks.append(b)

    label = (src.get("overall_compliance") or "").lower().strip()
    if clean_blocks:
        # a block ALWAYS means hard_blocked — the label can never override evidence.
        label = "hard_blocked"
    elif label not in VALID_COMPLIANCE:
        # unknown/missing with no blocks -> conservative non-pass, never silent clean.
        label = "soft_flagged"

    return {
        "overall_compliance": label,
        "hard_blocks_triggered": clean_blocks,
        "raised_by": raised_by,
    }


# ─────────────────────────────────────────────────────────────────────────────
# IMPURE EDGE — the single live GPT-4o vision call. Mocked in tests.
# ─────────────────────────────────────────────────────────────────────────────
def _call_gpt_vision(image_path: Path) -> dict:
    """Live FIRST-vote call. Raises on any problem (key/network/non-JSON) — never swallows."""
    from openai import OpenAI

    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"image not found: {image_path}")

    client = OpenAI(api_key=_calib.load_key(), timeout=90.0, max_retries=2)
    prompt = _calib.build_prompt()
    resp = client.chat.completions.create(
        model=_calib.MODEL,
        max_tokens=1200,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You return only valid JSON."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": _calib.b64_data_url(img), "detail": "high"}},
            ]},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    return json.loads(raw)


def compliance_read(image_path, handle: Optional[str] = None) -> dict:
    """
    FIRST vote: run the GPT-4o forbidden-list compliance read on a rendered image and
    return the canonical {overall_compliance, hard_blocks_triggered, raised_by} shape —
    exactly what vision_second_vote.apply_second_vote(single_result, image_path) consumes.

    Raises on API failure (Rule #8): a compliance read that cannot read must not pass
    silently. handle is accepted for a future per-client rubric; the universal forbidden
    rubric applies to every brand today.
    """
    return normalize(_call_gpt_vision(Path(image_path)), raised_by="compliance_read")


def main() -> int:
    import sys
    if len(sys.argv) < 2:
        print("usage: compliance_read.py <image_path> [handle]", file=sys.stderr)
        return 2
    out = compliance_read(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["overall_compliance"] != "hard_blocked" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
