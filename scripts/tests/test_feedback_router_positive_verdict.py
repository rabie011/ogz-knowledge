#!/usr/bin/env python3
"""Locks the positive-verdict classification: an explicit 'approved'/'accepted' verdict must NEVER
be read as a rejection, so it can never open a DEFECT-ISSUE against the mind whose work Mohamed
APPROVED.

Root scar (June 28): judge2 second-vote APPROVAL cards submit answer="approved" WITH a spurious
rating=2 UI artifact. feedback_router._is_reject read rating<=2 as a kill -> opened
iss_20260614_3f3092bb9bb8 / _8961663403e6 against mind:metaphor / mind:firaasa for work he had
APPROVED. That (a) poisons the Rule #14 learning loop (the mind is taught to avoid its approved
output) and (b) inflates issue_pulse with non-defects. The explicit verdict wins over the rating."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import feedback_router as fr


class TestPositiveVerdictNeverReject(unittest.TestCase):

    def test_approved_with_spurious_low_rating_is_not_reject(self):
        # the exact production row shape (answer approved, rating 2) — must NOT be a reject
        self.assertFalse(fr._is_reject({"answer": "approved", "rating": 2}))
        self.assertFalse(fr._is_reject({"answer": "Approved", "rating": 1}))
        self.assertFalse(fr._is_reject({"answer": "accepted", "rating": 0}))

    def test_explicit_reject_still_trips(self):
        self.assertTrue(fr._is_reject({"answer": "rejected", "rating": 5}))
        self.assertTrue(fr._is_reject({"answer": "flagged"}))

    def test_low_rating_without_positive_answer_still_trips(self):
        # a genuine kill (no positive verdict, rating<=2) must STILL open an issue — fix is surgical
        self.assertTrue(fr._is_reject({"answer": "", "rating": 2}))
        self.assertTrue(fr._is_reject({"rating": 1}))

    def test_high_rating_neutral_answer_is_not_reject(self):
        self.assertFalse(fr._is_reject({"answer": "", "rating": 5}))
        self.assertFalse(fr._is_reject({"answer": "noted"}))


if __name__ == "__main__":
    unittest.main()
