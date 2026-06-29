import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import reap_leaked_shifts as r  # noqa: E402
import orchestra_self_terminate as st  # noqa: E402


def _app_tree():
    """Claude.app (651) -> disclaimer (helper) -> claude-code session -> shell."""
    app = "/Applications/Claude.app/Contents/MacOS/Claude"
    cc = "/Users/x/Library/Application Support/Claude/claude"
    disc = "/Applications/Claude.app/Contents/Helpers/disclaimer /Users/x/.../claude"
    return app, cc, disc


class TestIsClaudeSession(unittest.TestCase):
    def test_session_binary_is_session(self):
        self.assertTrue(st.is_claude_session(
            "/Users/x/Library/Application Support/Claude/claude --foo"))

    def test_desktop_app_is_not_session(self):
        self.assertFalse(st.is_claude_session(
            "/Applications/Claude.app/Contents/MacOS/Claude"))

    def test_helper_shim_is_not_session(self):
        self.assertFalse(st.is_claude_session(
            "/Applications/Claude.app/Contents/Helpers/disclaimer /Users/x/.../claude"))

    def test_non_claude_is_not_session(self):
        self.assertFalse(st.is_claude_session("/bin/zsh -c source foo"))
        self.assertFalse(st.is_claude_session("python3 foo.py"))


class TestSelectSelfSession(unittest.TestCase):
    def setUp(self):
        self.app, self.cc, self.disc = _app_tree()
        # My live fire: 651 app -> 800 disclaimer -> 801 claude session ->
        #   810 zsh -> 811 python (the caller). A SIBLING leaked fire: 700/701.
        self.procs = [
            {"pid": 651, "ppid": 1, "etime_s": 600000, "tty": "??", "command": self.app},
            {"pid": 700, "ppid": 651, "etime_s": 7200, "tty": "??", "command": self.disc},
            {"pid": 701, "ppid": 700, "etime_s": 7200, "tty": "??", "command": self.cc},
            {"pid": 800, "ppid": 651, "etime_s": 120, "tty": "??", "command": self.disc},
            {"pid": 801, "ppid": 800, "etime_s": 119, "tty": "??", "command": self.cc},
            {"pid": 810, "ppid": 801, "etime_s": 5, "tty": "??", "command": "/bin/zsh -c source foo"},
            {"pid": 811, "ppid": 810, "etime_s": 4, "tty": "??", "command": "python3 self_terminate.py"},
        ]
        self.app_pid = r.find_app_pid(self.procs)

    def test_selects_own_session(self):
        my_chain = r.ancestry_chain(811, self.procs)  # 811->810->801->800->651
        target = st.select_self_session(self.procs, my_chain, self.app_pid)
        self.assertEqual(target, 801)  # my claude-code session, not the shims

    def test_never_selects_sibling_leak(self):
        my_chain = r.ancestry_chain(811, self.procs)
        target = st.select_self_session(self.procs, my_chain, self.app_pid)
        self.assertNotEqual(target, 701)  # the OTHER fire is untouchable
        self.assertNotIn(701, my_chain)

    def test_never_selects_app_root_or_shim(self):
        my_chain = r.ancestry_chain(811, self.procs)
        target = st.select_self_session(self.procs, my_chain, self.app_pid)
        self.assertNotEqual(target, 651)  # app root
        self.assertNotEqual(target, 800)  # disclaimer shim

    def test_target_is_in_my_chain(self):
        my_chain = r.ancestry_chain(811, self.procs)
        target = st.select_self_session(self.procs, my_chain, self.app_pid)
        self.assertIn(target, my_chain)

    def test_refuses_when_no_session(self):
        # A chain with no claude session in it -> None (caller then REFUSEs).
        procs = [
            {"pid": 651, "ppid": 1, "etime_s": 600000, "tty": "??", "command": self.app},
            {"pid": 900, "ppid": 651, "etime_s": 10, "tty": "??", "command": "python3 foo.py"},
        ]
        my_chain = r.ancestry_chain(900, procs)
        self.assertIsNone(st.select_self_session(procs, my_chain, 651))


class TestSpawnWatchdog(unittest.TestCase):
    """The hang-proof watchdog actually terminates its target after the wall-clock."""

    def test_watchdog_kills_target_after_timeout(self):
        # a real child that would otherwise live 30s
        proc = subprocess.Popen(["sleep", "30"])
        try:
            st.spawn_watchdog(proc.pid, timeout=1, grace=1)
            # poll up to ~5s for the watchdog (sleep 1; SIGTERM; sleep 1; SIGKILL) to act
            deadline = time.time() + 5
            while time.time() < deadline and proc.poll() is None:
                time.sleep(0.1)
            self.assertIsNotNone(proc.poll(), "watchdog did not terminate its target")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_watchdog_noop_when_target_already_dead(self):
        proc = subprocess.Popen(["sleep", "30"])
        proc.kill()
        proc.wait()
        dead_pid = proc.pid
        # arming against an already-dead pid must not raise (kills are swallowed)
        st.spawn_watchdog(dead_pid, timeout=1, grace=1)
        time.sleep(2.5)  # let the watchdog run its course harmlessly


class TestArmGuards(unittest.TestCase):
    """arm() reuses the tested selection and adds the interactive-TTY refusal."""

    def setUp(self):
        self.app, self.cc, self.disc = _app_tree()
        # my live fire: 651 app -> 800 disclaimer -> 801 session -> 810 zsh -> 811 caller
        self.procs = [
            {"pid": 651, "ppid": 1, "etime_s": 600000, "tty": "??", "command": self.app},
            {"pid": 800, "ppid": 651, "etime_s": 120, "tty": "??", "command": self.disc},
            {"pid": 801, "ppid": 800, "etime_s": 119, "tty": "??", "command": self.cc},
            {"pid": 810, "ppid": 801, "etime_s": 5, "tty": "??", "command": "/bin/zsh -c x"},
            {"pid": 811, "ppid": 810, "etime_s": 4, "tty": "??", "command": "python3 self_terminate.py"},
        ]

    def test_arm_dry_resolves_own_detached_session(self):
        res = st.arm(dry=True, procs=self.procs, my_pid=811)
        self.assertFalse(res["armed"])         # dry-run never actually arms
        self.assertEqual(res["reason"], "dry-run")
        self.assertEqual(res["target"], 801)   # my own session, via select_self_session

    def test_arm_refuses_interactive_tty_session(self):
        for p in self.procs:
            if p["pid"] == 801:
                p["tty"] = "s001"              # a real controlling terminal
        res = st.arm(dry=False, procs=self.procs, my_pid=811)
        self.assertFalse(res["armed"])
        self.assertIn("TTY", res["reason"])

    def test_arm_refuses_when_no_own_session(self):
        procs = [
            {"pid": 651, "ppid": 1, "etime_s": 600000, "tty": "??", "command": self.app},
            {"pid": 900, "ppid": 651, "etime_s": 10, "tty": "??", "command": "python3 foo.py"},
        ]
        res = st.arm(dry=False, procs=procs, my_pid=900)
        self.assertFalse(res["armed"])
        self.assertIsNone(res["target"])


if __name__ == "__main__":
    unittest.main()
