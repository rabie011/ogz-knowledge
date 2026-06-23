import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import reap_leaked_shifts as r  # noqa: E402


class TestEtimeParse(unittest.TestCase):
    def test_mm_ss(self):
        self.assertEqual(r._parse_etime("04:50"), 290)

    def test_hh_mm_ss(self):
        self.assertEqual(r._parse_etime("12:39:40"), 12 * 3600 + 39 * 60 + 40)

    def test_days(self):
        self.assertEqual(r._parse_etime("01-16:00:38"), 86400 + 16 * 3600 + 38)


def _app_tree():
    """Claude.app (651) -> disclaimer (helper) -> claude-code child."""
    app = "/Applications/Claude.app/Contents/MacOS/Claude"
    cc = "/Users/x/Library/Application Support/Claude/claude-code/2.1/claude.app/.../claude"
    disc = "/Applications/Claude.app/Contents/Helpers/disclaimer /Users/x/.../claude"
    return app, cc, disc


class TestSelectLeaked(unittest.TestCase):
    def setUp(self):
        self.app, self.cc, self.disc = _app_tree()
        # 651 app; 700/701 = leaked old fire; 800/801 = MY live chain (young);
        # 900 = old but a real-tty interactive claude; 1000 = unrelated python.
        self.procs = [
            {"pid": 651, "ppid": 1, "etime_s": 600000, "tty": "??", "command": self.app},
            {"pid": 700, "ppid": 651, "etime_s": 7200, "tty": "??", "command": self.disc},
            {"pid": 701, "ppid": 700, "etime_s": 7200, "tty": "??", "command": self.cc},
            {"pid": 800, "ppid": 651, "etime_s": 120, "tty": "??", "command": self.disc},
            {"pid": 801, "ppid": 800, "etime_s": 120, "tty": "??", "command": self.cc},
            {"pid": 900, "ppid": 651, "etime_s": 9000, "tty": "s001", "command": self.cc},
            {"pid": 1000, "ppid": 1, "etime_s": 9000, "tty": "??", "command": "python3 foo.py"},
        ]
        self.app_pid = r.find_app_pid(self.procs)

    def test_finds_app_root(self):
        self.assertEqual(self.app_pid, 651)

    def test_reaps_old_leaked_pair(self):
        my_chain = r.ancestry_chain(801, self.procs)  # 801->800->651
        leaked = {p["pid"] for p in r.select_leaked(self.procs, my_chain, self.app_pid, 3600)}
        self.assertIn(701, leaked)
        self.assertIn(700, leaked)

    def test_never_reaps_my_chain(self):
        my_chain = r.ancestry_chain(801, self.procs)
        leaked = {p["pid"] for p in r.select_leaked(self.procs, my_chain, self.app_pid, 3600)}
        self.assertNotIn(800, leaked)
        self.assertNotIn(801, leaked)
        self.assertFalse(leaked & my_chain)

    def test_never_reaps_app_root(self):
        my_chain = r.ancestry_chain(801, self.procs)
        leaked = {p["pid"] for p in r.select_leaked(self.procs, my_chain, self.app_pid, 3600)}
        self.assertNotIn(651, leaked)

    def test_never_reaps_real_tty(self):
        my_chain = r.ancestry_chain(801, self.procs)
        leaked = {p["pid"] for p in r.select_leaked(self.procs, my_chain, self.app_pid, 3600)}
        self.assertNotIn(900, leaked)  # interactive human session

    def test_ignores_non_claude_and_non_descendants(self):
        my_chain = r.ancestry_chain(801, self.procs)
        leaked = {p["pid"] for p in r.select_leaked(self.procs, my_chain, self.app_pid, 3600)}
        self.assertNotIn(1000, leaked)

    def test_age_threshold_respected(self):
        my_chain = r.ancestry_chain(801, self.procs)
        # threshold above the leaked pair's age -> nothing reaped
        leaked = r.select_leaked(self.procs, my_chain, self.app_pid, 8000)
        self.assertEqual(leaked, [])


if __name__ == "__main__":
    unittest.main()
