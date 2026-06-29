#!/usr/bin/env python3
"""C213 (June 29) — brain_api in-process job store: lifecycle + unknown-id 404 + growth pin.

DeepSeek audit #2 of the brain bridge: `_JOBS` is an in-memory dict that is NEVER expired
or evicted (unbounded growth), and the unknown-id 404 path the dev platform hits while
polling `GET /job/<id>` was untested. These tests exercise the job store DIRECTLY via its
helpers — NO HTTP server is booted — to:

  1. LOCK THE 404 CONTRACT — `_get_job('does-not-exist')` returns None, and the GET handler's
     mapping `200 if j else 404, j or {'ok':False,'error':'no such job'}` (brain_api.py:152)
     turns that None into the exact 404 body the dev platform depends on.
  2. PIN THE LIFECYCLE — pending → running → done(result) and pending → failed(error), with
     `created`/`updated` int timestamps and `updated >= created` (mtime monotonicity).
  3. PIN THE MERGE — `_set_job` MERGES (j.update), it does not replace: a field written in
     call 1 must survive call 2 (this is what lets the worker append `result`/`error` to a
     job created as `pending` without losing `created`).
  4. PIN THE (CURRENT) UNBOUNDED GROWTH — N distinct ids grow the dict by N. There is no
     eviction TODAY; this test makes the known leak a CONSCIOUS design so a future eviction
     change has to update this test deliberately, not by accident. (DeepSeek #2.)

File-independent: imports brain_api, edits no other file, mutates only its own copy of the
in-memory `_JOBS` dict (reset to {} at the start of every test for isolation).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import brain_api as ba  # noqa: E402


def _handler_job_response(job_id):
    """Replicate brain_api's GET /job/<id> mapping WITHOUT booting the server.

    The handler (brain_api.py:151-152) does:
        j = _get_job(<id>)
        return self._send(200 if j else 404, j or {"ok": False, "error": "no such job"})
    so the wire (status_code, body) is a pure function of the helper output. We assert that
    derived shape here — the dev platform's poll contract lives in this one expression."""
    j = ba._get_job(job_id)
    code = 200 if j else 404
    body = j or {"ok": False, "error": "no such job"}
    return code, body


class TestUnknownIdIs404(unittest.TestCase):
    def setUp(self):
        ba._JOBS = {}  # isolation: fresh store per test

    def test_get_job_unknown_returns_none(self):
        self.assertIsNone(ba._get_job("does-not-exist"))

    def test_handler_maps_none_to_404_body(self):
        # the contract the dev platform polls: unknown job → 404 + {ok:False, error:'no such job'}
        code, body = _handler_job_response("does-not-exist")
        self.assertEqual(code, 404)
        self.assertEqual(body, {"ok": False, "error": "no such job"})

    def test_handler_maps_known_to_200_with_record(self):
        ba._set_job("real", status="pending")
        code, body = _handler_job_response("real")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "pending")
        self.assertNotIn("error", body)  # a real job is not the 404 fallback


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        ba._JOBS = {}

    def test_pending_running_done_with_result(self):
        ba._set_job("jid", status="pending")
        self.assertEqual(ba._get_job("jid")["status"], "pending")

        ba._set_job("jid", status="running")
        self.assertEqual(ba._get_job("jid")["status"], "running")

        ba._set_job("jid", status="done", result={"post_id": "x"})
        j = ba._get_job("jid")
        self.assertEqual(j["status"], "done")
        self.assertEqual(j["result"], {"post_id": "x"})

    def test_pending_failed_with_error(self):
        ba._set_job("bad", status="pending")
        ba._set_job("bad", status="failed", error="ValueError: boom")
        j = ba._get_job("bad")
        self.assertEqual(j["status"], "failed")
        self.assertEqual(j["error"], "ValueError: boom")

    def test_timestamps_are_ints_and_updated_ge_created(self):
        ba._set_job("ts", status="pending")
        j1 = ba._get_job("ts")
        self.assertIsInstance(j1["created"], int)
        self.assertIsInstance(j1["updated"], int)
        self.assertGreaterEqual(j1["updated"], j1["created"])

        created_before = j1["created"]
        ba._set_job("ts", status="running")
        j2 = ba._get_job("ts")
        self.assertIsInstance(j2["updated"], int)
        # created is stamped once (setdefault); updated re-stamped every call, never goes back
        self.assertEqual(j2["created"], created_before)
        self.assertGreaterEqual(j2["updated"], j2["created"])


class TestMergeSemantics(unittest.TestCase):
    """`_set_job` MERGES (j.update), it does not replace — so the worker can layer
    status/result/error onto a job first created as `pending` without dropping fields."""

    def setUp(self):
        ba._JOBS = {}

    def test_second_set_merges_not_replaces(self):
        ba._set_job("merge", status="pending", queue_position=3)
        ba._set_job("merge", status="running")  # second call sets ONLY status
        j = ba._get_job("merge")
        self.assertEqual(j["status"], "running")        # call-2 field applied
        self.assertEqual(j["queue_position"], 3)        # call-1 field SURVIVED the merge

    def test_created_survives_subsequent_sets(self):
        ba._set_job("merge2", status="pending")
        created = ba._get_job("merge2")["created"]
        ba._set_job("merge2", status="done", result={"ok": True})
        self.assertEqual(ba._get_job("merge2")["created"], created)


class TestNoEvictionGrowthPin(unittest.TestCase):
    """KNOWN DESIGN (DeepSeek #2): `_JOBS` is never evicted/expired — it grows unbounded.
    Pin it: N distinct ids => dict grows by N. If an eviction policy is added later, this
    test will fail and force the change to be a deliberate, reviewed decision."""

    def setUp(self):
        ba._JOBS = {}

    def test_dict_grows_by_n_for_n_distinct_ids(self):
        N = 50
        self.assertEqual(len(ba._JOBS), 0)
        for i in range(N):
            ba._set_job(f"job-{i}", status="pending")
        self.assertEqual(len(ba._JOBS), N)  # no eviction today — every id is retained

    def test_repeated_same_id_does_not_grow(self):
        # merge, not insert: hammering one id keeps the store at size 1
        for _ in range(20):
            ba._set_job("same", status="running")
        self.assertEqual(len(ba._JOBS), 1)


if __name__ == "__main__":
    unittest.main()
