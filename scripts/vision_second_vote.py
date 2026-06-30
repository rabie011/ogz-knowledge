#!/usr/bin/env python3
"""
vision_second_vote.py — B125: Claude-vision SECOND VOTE on hand-on-food compliance.

A second, INDEPENDENT vision vote (Anthropic Claude vision) layered on top of the
single-model (GPT-4o) compliance result produced by extract_calibration_item.py.
Its job: catch a left_hand_serving violation the first model graded "clean"
(the L1-FAIL root in BASELINE_RESULTS.md — item_02 missed).

DESIGN — consult-before-build, RABIE + DeepSeek panel, 2026-06-30 (Rule #19/#20).
DeepSeek caught the SPOF trap and the design was amended:

  - The single model ALREADY has a conservative fail-safe (left OR uncertain hand
    in contact with food -> hard_block; see extract_calibration_item.py build_prompt).
  - This second vote is an ADDITIONAL safety net, NOT a single point of failure.
  - FAIL-SAFE != fail-OPEN.  If the second vote is UNAVAILABLE (no Anthropic credits,
    API error, timeout, network) we DO NOT block — we return the single-model result
    unchanged (which is itself conservative).  Blocking-on-unavailable would DoS the
    whole brain on any API hiccup — the trap DeepSeek refused.
  - The second vote can only ESCALATE, never DOWNGRADE: it may turn a single-model
    "clean" into "hard_blocked" on an explicit disagreement, but it never clears a
    block the single model already raised.

`reconcile()` is a PURE function (no I/O) — that is where the safety logic lives and
where the unit tests bite.  The live Anthropic call (`_call_anthropic_vision`) is the
only impure edge and is mocked in tests; the real 10-item agreement matrix run is
gated on Anthropic credits (DRY since 2026-06-12) and staged for when they return.

Verdict labels returned alongside the result: "agree" | "disagree" | "unavailable".
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Optional

ENV_FILE = Path.home() / ".abraham_env"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # vision-capable; cheapest tier (money discipline)

LEFT_HAND_RULE = "left_hand_serving"


# ─────────────────────────────────────────────────────────────────────────────
# PURE CORE — the safety logic.  No network, fully unit-tested.
# ─────────────────────────────────────────────────────────────────────────────
def _single_is_blocked(single_result: dict) -> bool:
    """True if the single-model result already hard-blocks (any reason)."""
    if (single_result.get("overall_compliance") or "").lower() == "hard_blocked":
        return True
    return bool(single_result.get("hard_blocks_triggered"))


def _second_sees_violation(second_read: dict) -> bool:
    """True if the second vote sees a left/uncertain hand in contact with food."""
    if (second_read.get("overall_compliance") or "").lower() == "hard_blocked":
        return True
    # explicit left/uncertain hand-on-food signal
    if second_read.get("left_hand_on_food") is True:
        return True
    if second_read.get("hand_on_food") and (second_read.get("which_hand") or "").lower() in (
        "left",
        "uncertain",
    ):
        return True
    return False


def reconcile(single_result: dict, second_read: Optional[dict]) -> tuple[dict, str]:
    """
    Combine the single-model compliance result with the second vote.  PURE.

    Returns (final_result, verdict) where verdict in {agree, disagree, unavailable}.

      - second_read is None  -> UNAVAILABLE -> return single_result UNCHANGED (fail-safe).
      - single already blocked -> AGREE on the safe side; never downgrade.
      - second sees a violation single missed -> DISAGREE -> ESCALATE to hard_block.
      - otherwise -> AGREE -> single_result unchanged.
    """
    result = dict(single_result)  # never mutate the caller's dict

    if second_read is None:
        return result, "unavailable"

    if _single_is_blocked(single_result):
        # Both effectively block (or single already does) — agree on the safe side.
        return result, "agree"

    if _second_sees_violation(second_read):
        # Second vote disagrees with a "clean" single read -> escalate (Rule #8).
        result["overall_compliance"] = "hard_blocked"
        blocks = list(result.get("hard_blocks_triggered") or [])
        if not any((b.get("entry_name") == LEFT_HAND_RULE) for b in blocks if isinstance(b, dict)):
            blocks.append(
                {
                    "entry_name": LEFT_HAND_RULE,
                    "severity": "severe",
                    "raised_by": "vision_second_vote",
                }
            )
        result["hard_blocks_triggered"] = blocks
        result["second_vote"] = "disagree_escalated"
        return result, "disagree"

    return result, "agree"


# ─────────────────────────────────────────────────────────────────────────────
# IMPURE EDGE — the live Anthropic vision call.  Mocked in tests; gated on credits.
# ─────────────────────────────────────────────────────────────────────────────
def _load_anthropic_key() -> Optional[str]:
    """Read ANTHROPIC_API_KEY straight from ~/.abraham_env (shell does not source it)."""
    try:
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


_VOTE_PROMPT = (
    "You are a SECOND, independent reviewer for Saudi cultural compliance. Look ONLY at "
    "human hands touching, dipping, holding, or serving food. For each such hand decide "
    "left vs right forensically (wrist entry side, thumb position, palm vs dorsal). If a "
    "bare hand in direct contact with food is LEFT or you are UNCERTAIN, that is a "
    "left_hand_serving violation. Reply with ONLY this JSON: "
    '{"hand_on_food": true|false, "which_hand": "left"|"right"|"uncertain"|"none", '
    '"overall_compliance": "clean"|"hard_blocked"}'
)


def _call_anthropic_vision(image_path: Path) -> dict:
    """Live second-vote call. Raises on any problem so second_vote_read maps it to None."""
    import anthropic  # imported lazily so the module loads without the dep present

    key = _load_anthropic_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not available")
    b64 = base64.standard_b64encode(image_path.read_bytes()).decode()
    media = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                    {"type": "text", "text": _VOTE_PROMPT},
                ],
            }
        ],
    )
    text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("second vote returned no JSON")
    read = json.loads(text[start : end + 1])
    read["left_hand_on_food"] = bool(read.get("hand_on_food")) and (
        (read.get("which_hand") or "").lower() in ("left", "uncertain")
    )
    return read


def second_vote_read(image_path: Path) -> Optional[dict]:
    """
    Run the second vote.  Returns the read dict, or None if UNAVAILABLE (any failure).
    None is the fail-safe signal — reconcile() falls back to the single model on None.
    """
    try:
        return _call_anthropic_vision(Path(image_path))
    except Exception:
        return None  # credits dry / API error / no dep / bad image -> unavailable, never block


def apply_second_vote(single_result: dict, image_path) -> tuple[dict, str]:
    """Convenience orchestrator: read the second vote and reconcile it. Returns (result, verdict)."""
    return reconcile(single_result, second_vote_read(Path(image_path)))
