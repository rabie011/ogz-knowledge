#!/usr/bin/env python3
"""Cold-start contract test for the PERFORMANCE INGESTOR (C212).

THE DANGER (DeepSeek ranked this #1): perf_ingestor's `_baseline` returns (None, None, n)
when a brand has fewer than 2 PRIOR posts in history — so z MUST be None and NO action may
fire. This branch had zero coverage. If it ever regressed to compute a bogus z on 0–1 history,
it would FALSE-KILL a brand's setup forever (a killed setup gets no new reach to re-test, so the
exile is permanent). This locks the cold-start branch shut.

Self-contained — runnable as `python3 scripts/tests/test_perf_ingestor_coldstart.py`
(exit 0 = pass, non-zero on any assert fail). No live server. Each test points
`pi.OUTCOMES` and `pi.COUNTERS` at a UNIQUE temp file (so the real data/ ledgers are never
touched) and stubs `kill_registry.add_perf_kill` with a recording fake to PROVE it is never
called on cold start (a kill here would be the catastrophic false-kill)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import perf_ingestor as pi          # noqa: E402
import kill_registry as kr          # noqa: E402


class TestPerfIngestorColdStart(unittest.TestCase):
    def setUp(self):
        # Isolate state: unique temp ledger + counters so the real data/ files are untouched.
        self.tmp = Path(tempfile.mkdtemp())
        self._orig_outcomes = pi.OUTCOMES
        self._orig_counters = pi.COUNTERS
        pi.OUTCOMES = self.tmp / "outcome_events.jsonl"
        pi.COUNTERS = self.tmp / "perf_counters.json"

        # Recording fake for the kill wire: ingest() does `import kill_registry as kr` and calls
        # kr.add_perf_kill, so patching the attribute on the module object is what it resolves to.
        self.kill_calls = []
        self._orig_add_perf_kill = kr.add_perf_kill
        kr.add_perf_kill = lambda *a, **k: self.kill_calls.append((a, k))

    def tearDown(self):
        pi.OUTCOMES = self._orig_outcomes
        pi.COUNTERS = self._orig_counters
        kr.add_perf_kill = self._orig_add_perf_kill

    def _ledger_rows(self):
        if not pi.OUTCOMES.exists():
            return []
        return [json.loads(l) for l in pi.OUTCOMES.read_text().splitlines() if l.strip()]

    # ---- (1) first-ever post for a brand → z None, action None -------------
    def test_first_post_z_none_action_none(self):
        rec = pi.ingest("newbrand|burger|studio",
                        {"likes": 10, "comments": 2, "saves": 1, "reach": 500})
        self.assertIsNone(rec["z_score"],
                          f"cold start (0 prior posts) must yield z None, got {rec['z_score']!r}")
        self.assertIsNone(rec["action"],
                          f"cold start must take NO action, got {rec['action']!r}")
        # the _baseline contract: (None, None, n=0) → n recorded as 0 in the event
        self.assertEqual(rec["brand_baseline"]["n"], 0,
                         "first post has 0 prior posts in baseline window")

    # ---- (2) the event is STILL durably appended (Rule #6 writer) ----------
    def test_first_post_still_appended_to_ledger(self):
        pi.ingest("newbrand|burger|studio",
                  {"likes": 10, "comments": 2, "saves": 1, "reach": 500})
        rows = self._ledger_rows()
        self.assertEqual(len(rows), 1,
                         f"exactly one JSON line must be appended on cold start, got {len(rows)}")
        self.assertEqual(rows[0]["schema_version"], "outcome_event_v1",
                         "ledger line must carry schema_version outcome_event_v1")
        self.assertIsNone(rows[0]["z_score"], "the appended event records z None on cold start")

    # ---- (3) the kill wire was NEVER touched on cold start -----------------
    def test_no_kill_on_cold_start(self):
        pi.ingest("newbrand|burger|studio",
                  {"likes": 10, "comments": 2, "saves": 1, "reach": 500})
        self.assertEqual(len(self.kill_calls), 0,
                         f"kill_registry.add_perf_kill must NOT be called on cold start — a kill here "
                         f"is the permanent false-kill; got {len(self.kill_calls)} call(s)")

    # ---- (4) the exact off-by-one: need >=2 PRIOR posts before a baseline ---
    def test_second_post_same_brand_still_z_none(self):
        # `_baseline` reads the brand's PRIOR posts (history is loaded BEFORE the current append).
        # n<2 prior → (None, None, n). So:
        #   post 1 → 0 prior → z None
        #   post 2 → 1 prior → z None   (still cold — this is the off-by-one the spec pins)
        #   post 3 → 2 prior → first real baseline → z computed
        r1 = pi.ingest("newbrand|burger|studio",
                       {"likes": 10, "comments": 2, "saves": 1, "reach": 500})
        r2 = pi.ingest("newbrand|burger|studio",
                       {"likes": 12, "comments": 2, "saves": 1, "reach": 500})
        self.assertIsNone(r1["z_score"], "post 1 (0 prior) must be z None")
        self.assertIsNone(r2["z_score"],
                          "post 2 (only 1 PRIOR post) must STILL be z None — _baseline needs n>=2 prior")
        self.assertEqual(r2["brand_baseline"]["n"], 1,
                         "the 2nd post sees exactly 1 prior post (n=1 < 2 guard)")
        self.assertEqual(len(self.kill_calls), 0,
                         "no kill may fire across the cold-start window")

        # the 3rd post is the FIRST with a real baseline (2 prior posts) → z is no longer None
        r3 = pi.ingest("newbrand|burger|studio",
                       {"likes": 14, "comments": 2, "saves": 1, "reach": 500})
        self.assertEqual(r3["brand_baseline"]["n"], 2,
                         "the 3rd post is the first to see 2 prior posts")
        self.assertIsNotNone(r3["z_score"],
                             "the 3rd post (>=2 prior) is the first with a real baseline → z computed")


if __name__ == "__main__":
    unittest.main()
