import os
import sys
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


if __name__ == "__main__":
    unittest.main()
