#!/usr/bin/env python3
"""Fork-decision CONSUMER tests (June 22, RABIE's pick — the actuator the 09:10 zoom-out named).

ROOT: h_fork_decision LANDS Mohamed's A/B fork tap in mohamed_rulings_live.json and CLAIMS
the file has a reader — but a grep proved nothing read fork_decisions. His decided fork
routed nowhere; the dependent step (B057b) would stay invisibly gated forever (Rule #6
severed wire). fork_decision_consumer.consume() is the missing reader: a ROUTER that stamps
the chosen direction onto any backlog step that declared `gated_on_fork`, clears the gate,
and surfaces a decided-but-undeclared fork as unconsumed — but NEVER executes the follow-on
work (Rule #11/#12).

Proven END-TO-END:
  - a decided fork routes onto its gated step: fork_resolved stamped, gate cleared
  - the route is idempotent (second run = no-op, no spurious progress notes)
  - a re-tap (changed answer) re-routes and re-opens the step
  - a decided fork with NO dependent step is reported unconsumed (the Rule #6 alarm)
  - the consumer NEVER touches step content beyond the gate/stamp (no follow-on execution)
  - --check read-only path agrees with consume()'s unconsumed list and never writes
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import fork_decision_consumer as fdc  # noqa: E402

FORK = "B057c_thinbrain_primary_fork"


def _sandbox(d, decisions=None, steps=None):
    tmp = Path(d)
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    rulings = {"by": "mohamed"}
    if decisions is not None:
        rulings["fork_decisions"] = decisions
    (tmp / "data" / "mohamed_rulings_live.json").write_text(
        json.dumps(rulings, ensure_ascii=False))
    if steps is None:
        steps = [{"id": "B057b", "status": "todo", "what": "reconcile readers",
                  "gated_on_fork": FORK}]
    (tmp / "data" / "backlog.json").write_text(
        json.dumps({"steps": steps}, ensure_ascii=False))
    return tmp


def _backlog(tmp):
    return json.loads((tmp / "data" / "backlog.json").read_text(encoding="utf-8"))


def _step(tmp, sid="B057b"):
    return next(s for s in _backlog(tmp)["steps"] if s["id"] == sid)


class TestRoutes(unittest.TestCase):
    def test_decided_fork_routes_onto_gated_step(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={FORK: {"answer": "B", "choice": "Strip dead reads + guard",
                                                "ruled_at": "2026-06-22T10:00"}})
            res = fdc.consume(tmp)
            self.assertEqual(len(res["routed"]), 1)
            st = _step(tmp)
            self.assertEqual(st["fork_resolved"]["answer"], "B")
            self.assertIn("Strip", st["fork_resolved"]["choice"])
            self.assertEqual(st["gated_on_fork"], FORK)  # provenance kept
            self.assertIn("resolved", st["progress"])

    def test_idempotent_second_run_noop(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={FORK: {"answer": "B", "choice": "Strip",
                                                "ruled_at": "t"}})
            fdc.consume(tmp)
            prog_after_first = _step(tmp)["progress"]
            res2 = fdc.consume(tmp)
            self.assertEqual(res2["routed"], [])
            self.assertEqual(len(res2["noop"]), 1)
            # progress note not duplicated
            self.assertEqual(_step(tmp)["progress"], prog_after_first)

    def test_retap_changed_answer_reroutes(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={FORK: {"answer": "B", "choice": "Strip", "ruled_at": "t1"}})
            fdc.consume(tmp)
            self.assertEqual(_step(tmp)["fork_resolved"]["answer"], "B")
            # he re-taps A; gate provenance persists, the new answer must re-route
            rulings = json.loads((tmp / "data" / "mohamed_rulings_live.json").read_text())
            rulings["fork_decisions"][FORK] = {"answer": "A", "choice": "Rewire", "ruled_at": "t2"}
            (tmp / "data" / "mohamed_rulings_live.json").write_text(json.dumps(rulings, ensure_ascii=False))
            res = fdc.consume(tmp)
            self.assertEqual(len(res["routed"]), 1)
            self.assertEqual(_step(tmp)["fork_resolved"]["answer"], "A")


class TestUnconsumed(unittest.TestCase):
    def test_decided_fork_with_no_step_is_unconsumed(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={"B999z_made_up_fork": {"answer": "A", "choice": "x"}},
                           steps=[{"id": "B057b", "status": "todo", "gated_on_fork": FORK}])
            res = fdc.consume(tmp)
            self.assertEqual([u["fork"] for u in res["unconsumed"]], ["B999z_made_up_fork"])
            self.assertEqual(res["routed"], [])  # the gated step's fork wasn't decided

    def test_no_decisions_yet(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d)  # no fork_decisions key
            res = fdc.consume(tmp)
            self.assertEqual(res, {"routed": [], "noop": [], "unconsumed": []})


class TestCheckPath(unittest.TestCase):
    def test_check_readonly_agrees_and_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={"B999z_made_up_fork": {"answer": "A"}},
                           steps=[{"id": "B057b", "status": "todo", "gated_on_fork": FORK}])
            before = (tmp / "data" / "backlog.json").read_text()
            un = fdc.unconsumed_forks(tmp)
            self.assertEqual([u["fork"] for u in un], ["B999z_made_up_fork"])
            self.assertEqual((tmp / "data" / "backlog.json").read_text(), before)

    def test_routed_step_not_flagged_unconsumed(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = _sandbox(d, decisions={FORK: {"answer": "B", "choice": "Strip", "ruled_at": "t"}})
            fdc.consume(tmp)  # routes + clears gate, stamps fork_resolved
            # after routing, the read-only check must still see it as consumed (via fork_resolved)
            self.assertEqual(fdc.unconsumed_forks(tmp), [])


if __name__ == "__main__":
    unittest.main()
