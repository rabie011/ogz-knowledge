#!/usr/bin/env python3
"""B285 (June 22) — the produce-batch in-flight lock must stop the enricher banking a partial batch.

The 2026-06-22 scar: ogz_enricher's commit_and_sync `git add -A` fired MID-BATCH and committed 12
partial orch_shadow candidates into the pilot pool (reverted abafc540). These tests lock the guard:
an active lock makes the enricher REFUSE to commit (Rule #8), a clean exit releases it, and a stale
lock (dead PID / past TTL / unreadable) is swept so a crashed producer can never wedge the enricher
(Rule #6 — one shared source, producer writes / enricher reads)."""
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import produce_lock as pl


class TestProduceLock(unittest.TestCase):
    def setUp(self):
        # Isolate the lock file so the test never touches the real one.
        self._tmp = Path(__file__).parent / f"_lock_test_{os.getpid()}.json"
        self._orig = pl.LOCK
        pl.LOCK = self._tmp
        pl.release()

    def tearDown(self):
        pl.release()
        pl.LOCK = self._orig

    def test_acquire_release_roundtrip(self):
        self.assertFalse(pl.is_active())
        pl.acquire()
        self.assertTrue(self._tmp.exists())
        self.assertTrue(pl.is_active())          # our own PID is alive
        pl.release()
        self.assertFalse(self._tmp.exists())
        self.assertFalse(pl.is_active())

    def test_dead_pid_is_swept(self):
        # An unused PID (we pick a very high one and assert it's dead) → stale → swept.
        dead = 999_999_999
        self.assertFalse(pl._alive(dead))
        self._tmp.write_text(json.dumps({"pid": dead, "started": time.time()}))
        self.assertFalse(pl.is_active())          # swept, not honored
        self.assertFalse(self._tmp.exists())      # and removed

    def test_past_ttl_is_swept(self):
        # Live PID but the stamp is older than the TTL → orphan → swept.
        old = time.time() - (pl.STALE_TTL_S + 60)
        self._tmp.write_text(json.dumps({"pid": os.getpid(), "started": old}))
        self.assertFalse(pl.is_active())
        self.assertFalse(self._tmp.exists())

    def test_unreadable_lock_is_swept(self):
        self._tmp.write_text("not json {{{")
        self.assertFalse(pl.is_active())
        self.assertFalse(self._tmp.exists())

    def test_enricher_defers_commit_while_batch_in_flight(self):
        """The whole point: an ACTIVE lock makes commit_and_sync refuse to `git add` (Rule #8)."""
        import ogz_enricher as en
        with mock.patch.object(en, "REPO", Path(__file__).parent.parent.parent), \
             mock.patch("produce_lock.is_active", return_value=True), \
             mock.patch.object(en, "_run") as run:
            out = en.commit_and_sync({"analytics_rebuilt": True}, 0)
        self.assertFalse(out)                     # deferred → falsy
        self.assertFalse(run.called)              # NO git add / commit ran

    def test_enricher_commits_when_no_batch_in_flight(self):
        """With no lock, the guard is transparent — commit proceeds (git add reached)."""
        import ogz_enricher as en
        with mock.patch.object(en, "REPO", Path(__file__).parent.parent.parent), \
             mock.patch("produce_lock.is_active", return_value=False), \
             mock.patch.object(en, "_run", return_value=(0, "", "")) as run:
            en.commit_and_sync({"analytics_rebuilt": True}, 0)
        cmds = [c.args[0] for c in run.call_args_list if c.args]
        self.assertIn(["git", "add", "-A"], cmds)  # guard let the add through


if __name__ == "__main__":
    unittest.main()
