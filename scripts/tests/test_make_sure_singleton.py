#!/usr/bin/env python3
"""Locks B284 — make_sure is a SINGLETON: only ONE instance runs at a time.

Root scar (June 23): under sustained box load every heavy subprocess check times out, so one
make_sure run lasts 20+ min. The next :13/:43 fire (plus orchestrator re-spawns) then start
CONCURRENT make_sure instances; each fans out ~8 python subprocesses and the macOS security
daemons (trustd/tccd/syspolicyd) thrash on the spawn storm -> load climbs to 60+ (a compounding
loop). settle_load_spike only defers a bounded 60s then runs anyway — it cannot stop the PILE-UP.
The singleton guard caps concurrency at one. Contracts that must never break:
  1. a LIVE holder -> the new run does NOT acquire (it will exit cleanly, never run the checks),
  2. a STALE lock (holder dead) -> reclaimed; the new run acquires and writes its own pid,
  3. missing / garbage lock -> reclaimed (never crash the self-check on a bad lock file),
  4. release removes our lock but NEVER another live holder's lock,
  5. a skip is healthy (exit 0), never an alarm — verified by the acquire contract above.
Pure: pid-liveness is injected, so no real processes are spawned."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms


class AcquireSingletonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = Path(self.tmp.name) / "make_sure.lock"

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_lock_acquires_and_writes_pid(self):
        acquired, holder = ms.acquire_singleton(self.lock, 4242, pid_alive=lambda p: True)
        self.assertTrue(acquired)
        self.assertIsNone(holder)
        self.assertEqual(self.lock.read_text().strip(), "4242")

    def test_live_holder_blocks_new_run(self):
        self.lock.write_text("999")
        acquired, holder = ms.acquire_singleton(self.lock, 4242, pid_alive=lambda p: True)
        self.assertFalse(acquired)
        self.assertEqual(holder, 999)
        # the live holder's pid must survive — we never stomp it
        self.assertEqual(self.lock.read_text().strip(), "999")

    def test_stale_lock_is_reclaimed(self):
        self.lock.write_text("999")                       # holder 999 is DEAD
        acquired, holder = ms.acquire_singleton(self.lock, 4242, pid_alive=lambda p: False)
        self.assertTrue(acquired)
        self.assertIsNone(holder)
        self.assertEqual(self.lock.read_text().strip(), "4242")

    def test_garbage_lock_is_reclaimed(self):
        self.lock.write_text("not-a-pid")
        acquired, holder = ms.acquire_singleton(self.lock, 4242, pid_alive=lambda p: True)
        self.assertTrue(acquired)
        self.assertEqual(self.lock.read_text().strip(), "4242")

    def test_own_pid_in_lock_acquires(self):
        # our own pid already in the lock (a re-entrant read) must NOT block us
        self.lock.write_text("4242")
        acquired, holder = ms.acquire_singleton(self.lock, 4242, pid_alive=lambda p: True)
        self.assertTrue(acquired)
        self.assertIsNone(holder)


class ReleaseSingletonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = Path(self.tmp.name) / "make_sure.lock"

    def tearDown(self):
        self.tmp.cleanup()

    def test_release_removes_our_own_lock(self):
        self.lock.write_text("4242")
        ms.release_singleton(self.lock, 4242)
        self.assertFalse(self.lock.exists())

    def test_release_never_deletes_another_holders_lock(self):
        self.lock.write_text("999")                       # someone else holds it
        ms.release_singleton(self.lock, 4242)             # we are 4242 — not ours
        self.assertTrue(self.lock.exists())
        self.assertEqual(self.lock.read_text().strip(), "999")

    def test_release_on_missing_lock_is_noop(self):
        ms.release_singleton(self.lock, 4242)             # never raises
        self.assertFalse(self.lock.exists())


class PidAliveTest(unittest.TestCase):
    def test_current_process_is_alive(self):
        import os
        self.assertTrue(ms._pid_alive(os.getpid()))

    def test_absurd_pid_is_dead(self):
        self.assertFalse(ms._pid_alive(2_000_000_000))    # no such pid

    def test_bad_input_never_raises(self):
        self.assertFalse(ms._pid_alive(None))
        self.assertFalse(ms._pid_alive("x"))


if __name__ == "__main__":
    unittest.main()
