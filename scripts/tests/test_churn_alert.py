#!/usr/bin/env python3
"""B093 — churn_alert.py: the CONSUMER of the churn-risk dashboard (Rule #6).

churn_risk.py writes data/churn_risk.json; nothing read it — a write-only organ. These tests lock
the reader: RED drops a human-touch task naming the owner, YELLOW logs only, both dedupe and
auto-close (Rule #10). Every input is injected, every side effect lands in a tmp dir — no live
queue, no live event log is ever touched by the suite.

Guards:
  1. RED  → 'fired' event + ONE queue task file naming the owners (UNASSIGNED when null, B160).
  2. YELLOW → 'fired' event, NO queue task (Rule #8 — dispatch reserved for the hard condition).
  3. DEDUPE → re-reconcile while the same level is open → zero new events, no second task.
  4. AUTO-CLOSE → open level, risk now GREEN → 'resolved' event (Rule #10, self-closing).
  5. DE-ESCALATE → open RED, risk now YELLOW → RED resolved AND YELLOW fired in one pass.
  6. dry-run (drop_task=False) on RED → event carries task_file=None and NO file is written.
  7. GREEN/INSUFFICIENT with nothing open → no events at all (never manufacture an alert).
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import churn_alert as ca


def _q(tmp):
    return Path(tmp) / "pending"


class TestChurnAlert(unittest.TestCase):
    def setUp(self):
        self.owners = {"albaik": None, "eatjurisha": "Sara", "myfitness.sa": None}
        self.now = "2026-06-22T12:00:00"

    # 1 — RED fires an event AND drops exactly one task naming the owners.
    def test_red_fires_and_drops_task(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            qd = _q(tmp)
            dash = {"risk": "RED", "reasons": ["silent 9.0d (>7)"]}
            new = ca.reconcile(dash, self.owners, self.now, [], queue_dir=qd)
            self.assertEqual(len(new), 1)
            self.assertEqual(new[0]["action"], ca.ACTION_FIRED)
            self.assertEqual(new[0]["level"], "RED")
            dropped = list(qd.glob("churn_touch_*.json"))
            self.assertEqual(len(dropped), 1, "RED must drop exactly one task")
            task = json.loads(dropped[0].read_text())
            self.assertEqual(task["task_type"], "human_touch_outreach")
            owners_by_handle = {o["handle"]: o["owner"] for o in task["owners"]}
            self.assertEqual(owners_by_handle["eatjurisha"], "Sara")
            self.assertEqual(owners_by_handle["albaik"], ca.UNASSIGNED)
            self.assertEqual(new[0]["task_file"], str(dropped[0]))

    # 2 — YELLOW logs an event but drops NO task.
    def test_yellow_logs_no_task(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            qd = _q(tmp)
            dash = {"risk": "YELLOW", "reasons": ["completion falling x0.33"]}
            new = ca.reconcile(dash, self.owners, self.now, [], queue_dir=qd)
            self.assertEqual(len(new), 1)
            self.assertEqual(new[0]["level"], "YELLOW")
            self.assertIsNone(new[0]["task_file"])
            self.assertFalse(qd.exists() and list(qd.glob("*.json")), "YELLOW must not drop a task")

    # 3 — dedupe: an already-open level does not re-fire.
    def test_dedupe_open_level(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            qd = _q(tmp)
            prior = [{"type": ca.ALERT_TYPE, "action": ca.ACTION_FIRED, "level": "RED"}]
            dash = {"risk": "RED", "reasons": ["silent 9.0d"]}
            new = ca.reconcile(dash, self.owners, self.now, prior, queue_dir=qd)
            self.assertEqual(new, [], "open RED must not re-fire")
            self.assertFalse(qd.exists() and list(qd.glob("*.json")), "no second task on dedupe")

    # 4 — auto-close: open RED, risk now GREEN → resolved.
    def test_autoclose_on_green(self):
        prior = [{"type": ca.ALERT_TYPE, "action": ca.ACTION_FIRED, "level": "RED"}]
        new = ca.reconcile({"risk": "GREEN", "reasons": []}, self.owners, self.now, prior)
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["action"], ca.ACTION_RESOLVED)
        self.assertEqual(new[0]["level"], "RED")
        self.assertEqual(new[0]["now_risk"], "GREEN")

    # 5 — de-escalation: open RED, risk now YELLOW → RED resolved + YELLOW fired.
    def test_deescalate_red_to_yellow(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            prior = [{"type": ca.ALERT_TYPE, "action": ca.ACTION_FIRED, "level": "RED"}]
            dash = {"risk": "YELLOW", "reasons": ["latency rising x1.6"]}
            new = ca.reconcile(dash, self.owners, self.now, prior, queue_dir=_q(tmp))
            actions = {(e["action"], e["level"]) for e in new}
            self.assertIn((ca.ACTION_RESOLVED, "RED"), actions)
            self.assertIn((ca.ACTION_FIRED, "YELLOW"), actions)

    # 6 — drop_task=False (dry-run path) on RED writes no file and records task_file=None.
    def test_red_dry_run_drops_nothing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            qd = _q(tmp)
            dash = {"risk": "RED", "reasons": ["silent 9.0d"]}
            new = ca.reconcile(dash, self.owners, self.now, [], queue_dir=qd, drop_task=False)
            self.assertEqual(len(new), 1)
            self.assertIsNone(new[0]["task_file"])
            self.assertFalse(qd.exists() and list(qd.glob("*.json")))

    # 7 — GREEN with nothing open → no events manufactured.
    def test_green_clean_noop(self):
        for risk in ("GREEN", "INSUFFICIENT"):
            self.assertEqual(ca.reconcile({"risk": risk}, self.owners, self.now, []), [],
                             f"{risk} with nothing open must produce no events")

    # open_levels reflects the LAST action per level (fired→resolved→open again).
    def test_open_levels_tracks_last_action(self):
        ev = [
            {"type": ca.ALERT_TYPE, "action": ca.ACTION_FIRED, "level": "YELLOW"},
            {"type": ca.ALERT_TYPE, "action": ca.ACTION_RESOLVED, "level": "YELLOW"},
            {"type": ca.ALERT_TYPE, "action": ca.ACTION_FIRED, "level": "RED"},
        ]
        ol = ca.open_levels(ev)
        self.assertFalse(ol.get("YELLOW"))
        self.assertTrue(ol.get("RED"))


if __name__ == "__main__":
    unittest.main()
