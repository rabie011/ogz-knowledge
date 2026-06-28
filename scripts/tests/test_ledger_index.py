#!/usr/bin/env python3
"""C204 (June 28) — the produced_posts.jsonl idempotency index.

Before this, _ledger_get re-scanned the whole append-only ledger on EVERY produce — O(n) per lookup,
O(n²) over a brand's lifetime in the long-lived brain_api process. The fix is an in-memory post_id→record
index built once and kept hot on append, with an mtime/size guard so an external writer is still seen.

These tests lock the contract that index must honor — identical to the old full-scan, just fast:
- a put is immediately gettable (hot-index update, no re-scan needed);
- duplicate post_id → LAST record wins (matches the old `found = r` scan);
- an EXTERNAL append (another process) is caught by the signature guard and rebuilt;
- a missing id → None; a torn/partial JSON line is tolerated, not fatal."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import export_produce_post as epp


class TestLedgerIndex(unittest.TestCase):
    def setUp(self):
        # Isolate the ledger so the test never touches the real produced_posts.jsonl.
        self._tmp = Path(__file__).parent / f"_ledger_test_{os.getpid()}.jsonl"
        self._orig = epp.LEDGER
        epp.LEDGER = self._tmp
        epp._LEDGER_SIG = None          # force a clean index for each test
        epp._LEDGER_INDEX = {}
        if self._tmp.exists():
            self._tmp.unlink()

    def tearDown(self):
        epp.LEDGER = self._orig
        epp._LEDGER_SIG = None
        epp._LEDGER_INDEX = {}
        if self._tmp.exists():
            self._tmp.unlink()

    def test_put_then_get_roundtrip(self):
        epp._ledger_put({"post_id": "h__p__C01", "v": 1})
        got = epp._ledger_get("h__p__C01")
        self.assertEqual(got["v"], 1)

    def test_missing_id_is_none(self):
        self.assertIsNone(epp._ledger_get("nope"))

    def test_duplicate_post_id_last_wins(self):
        epp._ledger_put({"post_id": "dup", "v": 1})
        epp._ledger_put({"post_id": "dup", "v": 2})
        self.assertEqual(epp._ledger_get("dup")["v"], 2)   # latest record, like the old scan

    def test_external_append_is_seen(self):
        """A different process appends straight to the file → the mtime/size guard must rebuild."""
        epp._ledger_put({"post_id": "owned", "v": 1})
        self.assertEqual(epp._ledger_get("owned")["v"], 1)
        with open(self._tmp, "a") as f:                     # bypass _ledger_put entirely
            f.write(json.dumps({"post_id": "external", "v": 99}) + "\n")
        self.assertEqual(epp._ledger_get("external")["v"], 99)

    def test_torn_line_is_tolerated(self):
        epp._ledger_put({"post_id": "good", "v": 1})
        with open(self._tmp, "a") as f:
            f.write("not json {{{\n")                       # a partial/torn append
        # the torn line must not crash the rebuild, and the good record still resolves
        self.assertEqual(epp._ledger_get("good")["v"], 1)
        self.assertIsNone(epp._ledger_get("nope"))

    def test_get_matches_full_scan_semantics(self):
        """Cross-check the index against a naive full scan on the same data."""
        for i in range(50):
            epp._ledger_put({"post_id": f"h__p{i}", "i": i})
        epp._ledger_put({"post_id": "h__p7", "i": 707})     # override one

        def naive(pid):
            found = None
            for ln in self._tmp.read_text().splitlines():
                if ln.strip():
                    try:
                        r = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    if r.get("post_id") == pid:
                        found = r
            return found

        for pid in ["h__p0", "h__p7", "h__p49", "absent"]:
            self.assertEqual(epp._ledger_get(pid), naive(pid), pid)

    def test_oserror_on_read_degrades_not_crashes(self):
        """C209 (DeepSeek gap #4): a whole-file read OSError (disk full, perms, file vanished after
        .exists()) must NOT crash the /produce hot path — it degrades to an empty index, idempotency
        offline for the run, and a later get still answers."""
        class _BoomLedger:
            """A Path-like that says it exists but throws OSError on read — the race we guard against."""
            def __init__(self, real): self._real = real
            def exists(self): return True
            def read_text(self, *a, **k): raise OSError("simulated disk fault")
            def __getattr__(self, n): return getattr(self._real, n)   # stat/open/parent fall through

        epp.LEDGER = _BoomLedger(self._tmp)
        epp._LEDGER_SIG = None
        epp._LEDGER_INDEX = {}
        epp._ledger_build_index()                          # must survive the OSError
        self.assertEqual(epp._LEDGER_INDEX, {})            # degraded to empty, not crashed
        self.assertIsNone(epp._ledger_get("anything"))     # hot path still answers


if __name__ == "__main__":
    unittest.main()
