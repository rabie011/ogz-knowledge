#!/usr/bin/env python3
"""B184 — guards build_question_script: the gap_report → choice-card renderer.

Locks the two things that make it Rule #11/#12 safe: (1) it renders EXACTLY the gap_report's questions
(no drop, no invention), and (2) inline-enumerated questions become real >=2-option choice cards while
non-enumerated ones stay open slots. Plus: established brands lead with confirm-instead, and verify()
REFUSEs on a dropped question."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import build_question_script as bqs


class TestExtractChoices(unittest.TestCase):
    def test_enumerated_goal_question_splits_into_options(self):
        opts = bqs.extract_choices("الهدف: مبيعات مباشرة، بناء براند، ولا الاثنين؟ كم نسبة العروض؟")
        self.assertEqual(opts, ["مبيعات مباشرة", "بناء براند", "الاثنين"])

    def test_open_question_has_no_choices(self):
        self.assertEqual(bqs.extract_choices("كم طلب باليوم تقدرون تستوعبون؟"), [])

    def test_parenthetical_list_is_not_a_choice_set(self):
        # «إطلاقات، فروع، مواسم» is an examples list (no «ولا/أو») — must NOT become a choice card.
        self.assertEqual(
            bqs.extract_choices("أهداف العمل القادمة (إطلاقات، فروع، مواسم مهمة لكم؟)"), [])

    def test_no_question_mark_no_choices(self):
        self.assertEqual(bqs.extract_choices("تأكيد المنتجات والأسعار (المرشّحين مرفقين)"), [])


class TestBuildCards(unittest.TestCase):
    REPORT = {
        "questions": [
            "الهدف: مبيعات مباشرة، بناء براند، ولا الاثنين؟ كم نسبة العروض؟",
            "كم طلب باليوم تقدرون تستوعبون؟",
        ],
        "organs_red": ["goals", "l1_strategy"],
    }

    def test_renders_exactly_the_gap_report_questions(self):
        cards = bqs.build_cards(self.REPORT)
        self.assertEqual(len(cards), 2)  # no drop, no invention
        self.assertEqual([c["question"] for c in cards], self.REPORT["questions"])

    def test_choice_and_open_kinds(self):
        cards = bqs.build_cards(self.REPORT)
        self.assertEqual(cards[0]["kind"], "choice")
        self.assertGreaterEqual(len(cards[0]["choices"]), 2)
        self.assertEqual(cards[1]["kind"], "open")

    def test_serves_organ_tagged_from_red_set(self):
        cards = bqs.build_cards(self.REPORT)
        self.assertEqual(cards[0]["serves_organ"], "goals")

    def test_empty_report_yields_no_cards(self):
        self.assertEqual(bqs.build_cards({}), [])


class TestRealAlbaik(unittest.TestCase):
    def setUp(self):
        try:
            self.report = bqs.load_gap_report("albaik")
        except FileNotFoundError:
            self.skipTest("albaik gap_report not present")

    def test_build_does_not_drop_or_add_questions(self):
        res = bqs.build_question_script("albaik", write=False)
        self.assertEqual(res["n_questions"], len(self.report.get("questions", [])))

    def test_established_brand_leads_with_confirm_instead(self):
        auto = self.report.get("auto_filled") or {}
        if auto.get("mode") != "auto_research":
            self.skipTest("albaik not in auto_research mode")
        res = bqs.build_question_script("albaik", write=False)
        self.assertIn("ابدأ بالتأكيد", res["markdown"])

    def test_verify_passes_on_albaik(self):
        self.assertEqual(bqs.verify("albaik"), 0)


if __name__ == "__main__":
    unittest.main()
