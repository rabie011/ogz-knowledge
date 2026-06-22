"""
B253 — orchestrator client task types: client_intake, client_profile, client_year_map.

The daemon's queue loop is guarded by `if __name__ == "__main__"`, and every run_*
helper is a local def with stdlib-only module imports, so importing the module is
side-effect-free. We import it, stub out the external surface (subprocess.run, mira,
log_step) and assert each new task_type dispatches to the right machine and returns
True. No live daemon is touched; no real subprocess runs.
"""
import json
import unittest
from pathlib import Path
from unittest import mock

import sys
AGENTS = Path.home() / "agents"
sys.path.insert(0, str(AGENTS))
# B254: render_slot_gate lives in ogz-knowledge/scripts — on path for the dispatch tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import orchestrator_daemon as od  # noqa: E402


class _FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestClientTaskTypes(unittest.TestCase):
    def setUp(self):
        # capture mira messages, silence log_step
        self.mira_msgs = []
        self._patches = [
            mock.patch.object(od, "mira", side_effect=lambda m: self.mira_msgs.append(m)),
            mock.patch.object(od, "log_step", lambda *a, **k: None),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _run(self, task, subproc_side_effect):
        with mock.patch.object(od.subprocess, "run", side_effect=subproc_side_effect) as m:
            ok = od.execute_task(task)
        return ok, m

    def test_client_intake_clean(self):
        calls = []

        def side(cmd, *a, **k):
            calls.append(cmd)
            return _FakeProc(0, "intake ok")

        # handle that has no manifest.json on disk → warnings read falls to [] → "clean"
        ok, _ = self._run(
            {"client": "albaik", "request": "intake", "task_type": "client_intake",
             "handle": "__nonexistent_test_handle__"},
            side)
        self.assertTrue(ok)
        self.assertTrue(any("scripts/client_intake.py" in " ".join(c) for c in calls))
        self.assertTrue(any("client_intake" in msg and "clean" in msg for msg in self.mira_msgs))

    def test_client_intake_failure_returns_false(self):
        def side(cmd, *a, **k):
            return _FakeProc(1, "", "scrape blew up")

        ok, _ = self._run(
            {"client": "albaik", "request": "intake", "task_type": "client_intake"},
            side)
        self.assertFalse(ok)
        self.assertTrue(any("FAILED: client_intake" in m for m in self.mira_msgs))

    def test_client_profile_reports_fingerprint(self):
        def side(cmd, *a, **k):
            # the fingerprint subprocess is the `python3 -c ...` call
            if any("fingerprint_status" in part for part in cmd):
                return _FakeProc(0, json.dumps({"state": "GREEN"}))
            return _FakeProc(0, "profile built")

        ok, _ = self._run(
            {"client": "albaik", "request": "profile", "task_type": "client_profile",
             "handle": "albaik"},
            side)
        self.assertTrue(ok)
        self.assertTrue(any("client_profile" in m and "GREEN" in m for m in self.mira_msgs))

    def test_client_year_map_reports_slots(self):
        report_line = "  120 slots over 12 months · 9 anchors · cadence 3/wk · state GREEN"

        def side(cmd, *a, **k):
            calls_join = " ".join(cmd)
            self.assertIn("year_map.py", calls_join)
            return _FakeProc(0, "✓ year map\n" + report_line)

        ok, _ = self._run(
            {"client": "myfitness", "request": "ymap", "task_type": "client_year_map",
             "handle": "myfitness.sa", "sector": "fitness", "start": "2026-07-01"},
            side)
        self.assertTrue(ok)
        self.assertTrue(any("client_year_map" in m and "slots" in m for m in self.mira_msgs))

    def test_render_slot_blackout_requeues_no_render(self):
        # B254: hard blackout → the handler requeues the slot (writes a new PENDING
        # file with the reason) and NEVER calls render_client_slot.py.
        import tempfile
        import render_slot_gate as rsg
        calls = []

        def side(cmd, *a, **k):
            calls.append(cmd)
            return _FakeProc(0, "should not be called")

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(od, "PENDING", Path(td)), \
                 mock.patch.object(rsg, "decide",
                                   return_value={"action": "requeue", "reason": "حداد وطني",
                                                 "blackout": True, "warnings": []}):
                ok, _ = self._run(
                    {"client": "albaik", "request": "slot", "task_type": "render_slot",
                     "handle": "albaik", "date": "2026-09-23"},
                    side)
                requeued = list(Path(td).glob("*.json"))
            self.assertTrue(ok)
            # render was NOT invoked, and a requeue file landed with the reason + count
            self.assertFalse(any("render_client_slot.py" in " ".join(c) for c in calls))
            self.assertEqual(len(requeued), 1)
            rq = json.loads(requeued[0].read_text())
            self.assertEqual(rq["requeue_reason"], "حداد وطني")
            self.assertEqual(rq["requeue_count"], 1)
            self.assertTrue(any("BLACKOUT: render_slot" in m for m in self.mira_msgs))

    def test_render_slot_clear_renders(self):
        # B254: no blackout → render_client_slot.py runs with handle + date.
        import render_slot_gate as rsg
        calls = []

        def side(cmd, *a, **k):
            calls.append(cmd)
            return _FakeProc(0, "✓ rendered 3 captions")

        with mock.patch.object(rsg, "decide",
                               return_value={"action": "render", "reason": None,
                                             "blackout": False, "warnings": []}):
            ok, _ = self._run(
                {"client": "albaik", "request": "slot", "task_type": "render_slot",
                 "handle": "albaik", "date": "2026-09-23"},
                side)
        self.assertTrue(ok)
        joined = [" ".join(c) for c in calls]
        self.assertTrue(any("render_client_slot.py" in j and "albaik" in j and "2026-09-23" in j
                            for j in joined))
        self.assertTrue(any("DONE: render_slot albaik" in m for m in self.mira_msgs))

    def test_unknown_task_type_still_rejected(self):
        # guard: our additions didn't swallow the unknown-type fall-through
        def side(cmd, *a, **k):
            return _FakeProc(0, "")

        ok, _ = self._run(
            {"client": "x", "request": "y", "task_type": "totally_made_up"},
            side)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
