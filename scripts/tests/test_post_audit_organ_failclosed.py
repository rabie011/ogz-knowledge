#!/usr/bin/env python3
"""Pins post_audit's organ/cultural checks as FAIL-CLOSED (2026-06-22 audit, Rule #8/#13).

Scar: the per-post `client_rules.violations()` block (and the batch
`batch_trope_overconcentration()` block) wrapped their organ checks in `except Exception: pass`.
A crashed cultural check (torn organ file, malformed post, a future client_rules bug) silently
DROPPED its block-severity findings — real-person/face/family, cloud-kitchen, cross-brand
(RABIE's June-14 24-issue net) — and the batch reported '🟢 ZERO ISSUES — ship-ready' while a
blocked post sat in it. main() gates on `ok = total_issues == 0 and not dchk['violations']`.

The fix fails CLOSED: a crashed per-post check appends a HARD `organ_check_error` issue; a crashed
batch trope check appends a diversity violation. Either path marks the batch NOT ship-ready.
A crashed cultural check can never green-light a batch again."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import post_audit as pa
import client_rules as cr


def _kinds(d, handle="albaik"):
    return [k for k, _ in pa.audit_post(d, handle)]


class TestOrganCheckFailClosed(unittest.TestCase):
    POST = {"slot": {"angle_theme": "daily: post"},
            "captions": ["برجر دجاج لذيذ"],
            "corpus_text": "برجر دجاج بطاطس"}

    def test_per_post_clean_when_organ_check_passes(self):
        """Sanity: with the real (non-raising) client_rules, a clean post has no error issue."""
        self.assertNotIn("organ_check_error", _kinds(self.POST))

    def test_per_post_crashed_organ_check_becomes_hard_issue(self):
        """If client_rules.violations() raises, a HARD organ_check_error issue is appended
        (kind does NOT end in _warn, so main() counts it in total_issues)."""
        orig = cr.violations
        cr.violations = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("organ file torn"))
        try:
            kinds = _kinds(self.POST)
        finally:
            cr.violations = orig
        self.assertIn("organ_check_error", kinds)
        self.assertFalse(
            any(k == "organ_check_error" and k.endswith("_warn") for k in kinds),
            "organ_check_error must be HARD, not a soft _warn")

    def test_per_post_error_message_names_the_exception(self):
        orig = cr.violations
        cr.violations = lambda *a, **k: (_ for _ in ()).throw(ValueError("bad organ"))
        try:
            iss = pa.audit_post(self.POST, "albaik")
        finally:
            cr.violations = orig
        err = [why for kind, why in iss if kind == "organ_check_error"]
        self.assertTrue(err and "ValueError" in err[0] and "bad organ" in err[0])

    def test_source_batch_trope_fails_closed_not_pass(self):
        """The batch `batch_trope_overconcentration` except must append to dchk['violations']
        (fail closed), never `pass` it away (which would keep the batch ship-ready)."""
        src = (Path(pa.__file__)).read_text()
        # locate the batch trope try/except and assert it no longer swallows with bare pass
        self.assertIn("batch_trope_overconcentration", src)
        self.assertIn('"kind": "device", "key": f"trope_check_error', src,
                      "batch trope check must record a violation on error (fail closed)")
        self.assertNotRegex(
            src,
            r"batch_trope_overconcentration[\s\S]{0,400}?except Exception:\s*\n\s*pass",
            "batch trope check still swallows errors with `except: pass` (fail open)")

    def test_source_per_post_organ_fails_closed_not_pass(self):
        src = (Path(pa.__file__)).read_text()
        self.assertIn('issues.append(("organ_check_error"', src)
        self.assertNotRegex(
            src,
            r"client_rules as _cr\s*\n\s*for kind[\s\S]{0,300}?except Exception:\s*\n\s*pass",
            "per-post client_rules check still swallows errors with `except: pass`")


if __name__ == "__main__":
    unittest.main()
