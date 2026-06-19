#!/usr/bin/env python3
"""B130 — EXTRACTION RELEASE GATE (Rule #8 REFUSE-don't-warn, Rule #6 writer→reader).

THE HOLE THIS CLOSES: corpus extraction + its compliance stamps (hard_blocks/soft_flags) are what
the producer ultimately learns culture from. If the extractor cannot detect a PLANTED hard-block
(e.g. left_hand_serving — Level 1 of the calibration tester), every compliance stamp it emits is a
lie that silently pollutes the corpus. Until B130 nothing stopped run_post_extraction_pipeline.py /
batch_extract.py from running on top of a RED detector.

WRITER (the producer of the state this gate reads): scripts/test_extraction_accuracy.py persists
data/extraction_accuracy_gate.json on every run — the latest Level-1/2/3 verdict.

CONSUMER (this module): the extraction entry points call assert_release_allowed() before doing any
real work. A RED or MISSING gate EXITS non-zero (never proceeds-with-a-warning, Rule #8).

FAIL-CLOSED (Rule #8): no run on record, an unreadable artifact, or a Level-1 failure all BLOCK.
"Latest accuracy run passed Level 1" is the only state that releases.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

B = Path(__file__).resolve().parent.parent
GATE_PATH = B / "data" / "extraction_accuracy_gate.json"


def gate_state(path: Path = GATE_PATH) -> dict | None:
    """Read the persisted gate artifact. Missing or torn file → None (treated as BLOCKED upstream)."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def release_blocked(path: Path = GATE_PATH) -> tuple[bool, str]:
    """Returns (blocked, reason). Fail-CLOSED: missing/unreadable/Level-1-not-passed = blocked."""
    st = gate_state(path)
    if st is None:
        return True, ("no calibration accuracy run on record — run "
                      "scripts/test_extraction_accuracy.py and pass Level 1 first")
    if not st.get("level1_passed"):
        return True, (f"latest calibration run FAILED Level 1 hard-block detection "
                      f"(ts={st.get('ts', '?')}, exit_code={st.get('exit_code', '?')}) — "
                      f"fix the extractor before any compliance stamp")
    return False, f"Level 1 passed (ts={st.get('ts', '?')})"


def assert_release_allowed(path: Path = GATE_PATH) -> str:
    """REFUSE-don't-warn entry guard: print + sys.exit(2) when blocked, else return the reason."""
    blocked, reason = release_blocked(path)
    if blocked:
        print(f"⛔ EXTRACTION RELEASE-BLOCKED (B130, Rule #8): {reason}", file=sys.stderr)
        sys.exit(2)
    return reason


if __name__ == "__main__":
    print(assert_release_allowed())
