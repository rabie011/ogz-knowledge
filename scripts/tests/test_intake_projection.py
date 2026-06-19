#!/usr/bin/env python3
"""Tests for B102 intake_projection — confirmed intake answers route into the right organ."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import intake_projection as ip  # noqa: E402


def _ev(target, value, confirmer="client", **extra):
    e = {"ts": "2026-06-19", "type": "intake_answer", "confirmer": confirmer,
         "stamp": "CONFIRMED BY " + confirmer, "target": target, "value": value}
    e.update(extra)
    return e


class TestIntakeProjection(unittest.TestCase):
    def test_red_line_appended(self):
        organs = {"red_lines": {"lines": []}}
        out, ch = ip.project_intake([_ev("red_lines", "لا مشاهد عائلية", question_id="q_red_line")], organs)
        self.assertEqual(len(out["red_lines"]["lines"]), 1)
        self.assertEqual(out["red_lines"]["lines"][0]["line"], "لا مشاهد عائلية")
        self.assertEqual(out["red_lines"]["lines"][0]["confirmer"], "client")
        self.assertEqual(ch[0]["kind"], "red_line_added")

    def test_goal_set_dotted(self):
        organs = {"goals": {}}
        out, ch = ip.project_intake([_ev("goals", "مبيعات", field="primary")], organs)
        self.assertEqual(out["goals"]["primary"], "مبيعات")
        out2, _ = ip.project_intake([_ev("goals", "x", field="usp_his_words.raw")], {"goals": {}})
        self.assertEqual(out2["goals"]["usp_his_words"]["raw"], "x")

    def test_fingerprint_nested_set(self):
        organs = {"fingerprint": {"l1_strategy": {"positioning": None}}}
        out, ch = ip.project_intake([_ev("fingerprint", "الجودة", field="l1_strategy.positioning")], organs)
        self.assertEqual(out["fingerprint"]["l1_strategy"]["positioning"], "الجودة")
        self.assertEqual(ch[0]["kind"], "field_set")

    def test_idempotent(self):
        organs = {"red_lines": {"lines": []}}
        ev = [_ev("red_lines", "خط أحمر", question_id="q_red_line")]
        out1, ch1 = ip.project_intake(ev, organs)
        out2, ch2 = ip.project_intake(ev, out1)  # replay over already-projected organ
        self.assertEqual(len(out2["red_lines"]["lines"]), 1)
        self.assertEqual(ch2, [])  # second pass = no change

    def test_provisional_and_machine_ignored(self):
        organs = {"red_lines": {"lines": []}}
        prov = _ev("red_lines", "x", confirmer="rabie_provisional", question_id="q")
        prov["stamp"] = "PROVISIONAL — pending Mohamed"
        machine = _ev("red_lines", "y", confirmer="staleness_report", question_id="q")
        machine["stamp"] = "PROPOSAL — pending human refresh"
        out, ch = ip.project_intake([prov, machine], organs)
        self.assertEqual(out["red_lines"]["lines"], [])
        self.assertEqual(ch, [])

    def test_untargeted_intake_answer_skipped(self):
        # legacy intake_answer with no target (e.g. staleness proposals) is not ours to project
        organs = {"red_lines": {"lines": []}}
        legacy = {"ts": "2026-06-19", "type": "intake_answer", "confirmer": "client",
                  "stamp": "CONFIRMED BY client", "subject": "no target here"}
        out, ch = ip.project_intake([legacy], organs)
        self.assertEqual(ch, [])

    def test_bad_target_refuses(self):
        with self.assertRaises(ValueError):
            ip.project_intake([_ev("competitor_set", "x", field="a")], {})

    def test_empty_value_refuses(self):
        with self.assertRaises(ValueError):
            ip.project_intake([_ev("goals", "   ", field="primary")], {"goals": {}})

    def test_event_from_template_roundtrip(self):
        templates = ip.load_templates()
        self.assertTrue(templates, "templates file should have routing rows")
        tmpl = next(t for t in templates if t["question_id"] == "q_usp")
        ev = ip.event_from_template(tmpl, "التغليف والجودة", "client", "2026-06-19", "CONFIRMED BY client")
        out, ch = ip.project_intake([ev], {"fingerprint": {"l1_strategy": {}}})
        self.assertEqual(out["fingerprint"]["l1_strategy"]["positioning"], "التغليف والجودة")
        self.assertEqual(len(ch), 1)

    def test_all_templates_route_to_allowed_targets(self):
        for t in ip.load_templates():
            self.assertIn(t["target"], ip.ALLOWED_TARGETS, f"{t['question_id']} routes off allow-list")


if __name__ == "__main__":
    unittest.main()
