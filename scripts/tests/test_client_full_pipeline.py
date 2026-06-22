#!/usr/bin/env python3
"""Locks B255 — the five-stage client pipeline chainer (client_full_pipeline.py).

The contract under test (NOT the stage scripts themselves — those have their own tests):
  1. The spine is the five stages in order: intake→profile→year_map→render→visual_gate,
     and every stage script it names actually exists on disk.
  2. FAIL-STOP (Rule #8): a non-zero stage halts the chain — downstream stages NEVER run.
  3. A clean pass runs all five and reports ok=True.
  4. Each stage's command carries --handle (the shared key) so no stage is invoked blind.

The runner is injected (a fake), so these tests drive the chain WITHOUT executing the
heavy real stage scripts. That is the whole point of the injectable runner."""
import sys
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import client_full_pipeline as cfp


def _ns(**kw):
    base = dict(handle="albaik", sector="f_and_b", start="2026-07-01",
                anchor_date=None, dry_run=False)
    base.update(kw)
    return Namespace(**base)


class FakeResult:
    def __init__(self, rc, stdout="ok\n", stderr=""):
        self.returncode = rc
        self.stdout = stdout
        self.stderr = stderr


class TestSpineDefinition(unittest.TestCase):
    def test_five_stages_in_order(self):
        names = [s[0] for s in cfp.STAGES]
        self.assertEqual(
            names,
            ["intake", "profile", "year_map", "render_anchors", "visual_gate"],
        )

    def test_every_stage_script_exists(self):
        for name, script, _ in cfp.STAGES:
            self.assertTrue(
                (cfp.SCRIPTS / script).exists(),
                f"stage '{name}' points at missing script {script}",
            )

    def test_every_stage_passes_handle(self):
        ns = _ns()
        for name, _script, args_fn in cfp.STAGES:
            args = args_fn("albaik", ns)
            self.assertIn("--handle", args, f"stage '{name}' invoked without --handle")
            self.assertEqual(args[args.index("--handle") + 1], "albaik")


class TestFailStop(unittest.TestCase):
    def test_failure_halts_chain_downstream_never_runs(self):
        """The core safety: if stage 3 (year_map) fails, render + visual_gate must NOT run."""
        calls = []

        def runner(cmd):
            calls.append(cmd)
            # cmd[1] is the script path; fail when year_map runs
            script = Path(cmd[1]).name
            return FakeResult(1 if script == "year_map.py" else 0)

        ok, results = cfp.run_pipeline("albaik", _ns(), runner=runner)

        self.assertFalse(ok)
        ran = [Path(c[1]).name for c in calls]
        self.assertEqual(ran, ["client_intake.py", "build_brand_profile.py", "year_map.py"])
        self.assertNotIn("render_client_slot.py", ran)
        self.assertNotIn("visual_gate_checklist.py", ran)
        # last result is the failing stage, marked FAIL
        self.assertEqual(results[-1]["stage"], "year_map")
        self.assertEqual(results[-1]["status"], "FAIL")

    def test_first_stage_failure_runs_only_one(self):
        calls = []

        def runner(cmd):
            calls.append(cmd)
            return FakeResult(2)  # everything fails

        ok, results = cfp.run_pipeline("albaik", _ns(), runner=runner)
        self.assertFalse(ok)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(results), 1)

    def test_clean_pass_runs_all_five(self):
        calls = []

        def runner(cmd):
            calls.append(cmd)
            return FakeResult(0)

        ok, results = cfp.run_pipeline("albaik", _ns(), runner=runner)
        self.assertTrue(ok)
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(r["status"] == "OK" for r in results))


class TestDryRun(unittest.TestCase):
    def test_dry_run_executes_nothing_and_exits_zero(self):
        # if main() tried to run real stages with a fake handle it would error;
        # dry-run must short-circuit cleanly.
        rc = cfp.main(["--handle", "nonexistent_handle_xyz", "--dry-run"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
