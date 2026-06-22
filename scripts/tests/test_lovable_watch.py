"""B239 — lovable_watch.py idempotency + new-commit detection (no network: do_fetch=False)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lovable_watch as lw


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _commit(repo, fname, body, msg):
    (Path(repo) / fname).write_text(body)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", msg)


class TestLovableWatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        _commit(self.repo, "a.txt", "1", "c1: first")
        self.state = Path(self.tmp.name) / "state.json"
        self.inbox = Path(self.tmp.name) / "inbox.md"

    def tearDown(self):
        self.tmp.cleanup()

    def _watch(self):
        return lw.watch(repo=self.repo, state_path=self.state, inbox_path=self.inbox,
                        do_fetch=False, ref="HEAD", notify=False, now="2026-06-22T00:00:00")

    def test_cold_start_is_baseline_not_history_flood(self):
        res = self._watch()
        self.assertTrue(res["baseline"])
        self.assertEqual(res["new"], 0)
        self.assertTrue(self.state.exists())
        self.assertEqual(json.loads(self.state.read_text())["last_seen_sha"], res["head"])
        self.assertIn("baseline", self.inbox.read_text())

    def test_second_run_is_noop(self):
        self._watch()
        inbox_after_baseline = self.inbox.read_text()
        res = self._watch()
        self.assertEqual(res["new"], 0)
        self.assertNotIn("baseline", res)  # not a re-baseline, a clean no-op
        self.assertEqual(self.inbox.read_text(), inbox_after_baseline)  # appended nothing

    def test_new_commit_detected_then_idempotent(self):
        self._watch()  # baseline at c1
        _commit(self.repo, "b.txt", "2", "c2: the new one")
        res = self._watch()
        self.assertEqual(res["new"], 1)
        self.assertEqual(res["commits"][0]["subject"], "c2: the new one")
        self.assertIn("c2: the new one", self.inbox.read_text())
        # state advanced to c2 → running again appends nothing
        before = self.inbox.read_text()
        res2 = self._watch()
        self.assertEqual(res2["new"], 0)
        self.assertEqual(self.inbox.read_text(), before)

    def test_two_new_commits_both_reported(self):
        self._watch()
        _commit(self.repo, "b.txt", "2", "c2")
        _commit(self.repo, "c.txt", "3", "c3")
        res = self._watch()
        self.assertEqual(res["new"], 2)
        subjects = {c["subject"] for c in res["commits"]}
        self.assertEqual(subjects, {"c2", "c3"})

    def test_not_a_git_repo_is_graceful(self):
        res = lw.watch(repo=Path(self.tmp.name) / "nope", state_path=self.state,
                       inbox_path=self.inbox, do_fetch=False, ref="HEAD", notify=False)
        self.assertEqual(res["new"], 0)
        self.assertIn("not a git repo", res["reason"])


if __name__ == "__main__":
    unittest.main()
