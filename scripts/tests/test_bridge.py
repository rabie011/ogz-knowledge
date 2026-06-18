#!/usr/bin/env python3
"""Locks the BRIDGE sampler (Step 5c, June 17). The honest held-out LIVE test is 0-testable while
his judged captions are singletons (taste_elo.held_out_live). bridge_pairs proposes NEW same-brand
pairs that REUSE his live-pick captions so each gains a 2nd comparison and the graph connects. These
tests lock: (1) only NEW pids (live cards untouched), (2) every pair reuses a judged caption, (3) the
mechanism actually makes the held-out test COMPUTABLE (n_testable rises above 0). The agreement % is
NOT asserted — that awaits his real taps (Rule #9)."""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pairwise as pw
import taste_elo as te


def _live_caps():
    prefs_file = Path(__file__).parent.parent.parent / "data/pairwise_prefs.jsonl"
    caps = set()
    if prefs_file.exists():
        for line in prefs_file.read_text().splitlines():
            if not line.strip():
                continue
            p = json.loads(line)
            if p.get("source") == "seed_from_ratings":
                continue
            caps.add(p.get("winner_caption", ""))
            caps.add(p.get("loser_caption", ""))
    return caps


class TestBridge(unittest.TestCase):
    def test_proposes_stable_real_new_pairs(self):
        ps = pw.bridge_pairs(12)
        if not ps:
            self.skipTest("no live picks to bridge yet")
        excluded = pw._judged_or_live_pids()
        for p in ps:
            self.assertTrue(p["id"].startswith("pw_"))
            self.assertNotEqual(p["a"]["caption"], p["b"]["caption"])     # a real A-vs-B
            self.assertEqual(p["id"], pw._pid(p["a"], p["b"]))            # stable id
            # NEW only — neither ordering already judged or live
            self.assertNotIn(p["id"], excluded)
            self.assertNotIn(pw._pid(p["b"], p["a"]), excluded)

    def test_every_pair_reuses_a_judged_caption(self):
        """The whole point: each bridge must touch a caption he already judged, else it does not
        connect his live picks (it would just be another never-compared singleton)."""
        ps = pw.bridge_pairs(12)
        if not ps:
            self.skipTest("no live picks to bridge yet")
        live = _live_caps()
        for p in ps:
            touches = p["a"]["caption"] in live or p["b"]["caption"] in live
            self.assertTrue(touches, f"bridge {p['id']} reuses no judged caption — does not connect the graph")

    def test_bridges_make_held_out_computable(self):
        """The measured guarantee (Rule #9): with his live picks all singletons the held-out test is
        0-testable; after simulating taps on the bridges it becomes computable (n_testable > 0). We
        assert ONLY that the graph connects — never the agreement %, which his real taps decide."""
        prefs_file = Path(__file__).parent.parent.parent / "data/pairwise_prefs.jsonl"
        if not prefs_file.exists():
            self.skipTest("no prefs ledger")
        prefs = [json.loads(l) for l in prefs_file.read_text().splitlines() if l.strip()]
        live = [p for p in prefs if p.get("source") != "seed_from_ratings"]
        if len(live) < 2:
            self.skipTest("need >=2 live picks to demonstrate bridging")

        def to_pairs(rows):
            caps = {}
            def cid(c):
                return caps.setdefault(c, len(caps))
            return [(cid(r["winner_caption"]), cid(r["loser_caption"])) for r in rows]

        _, base_n = te.held_out_live(to_pairs(prefs), prefs)
        ps = pw.bridge_pairs(12)
        if not ps:
            self.skipTest("no bridges proposed")
        sim = list(prefs) + [{"winner_caption": p["a"]["caption"], "loser_caption": p["b"]["caption"],
                              "source": "live_sim"} for p in ps]
        _, sim_n = te.held_out_live(to_pairs(sim), sim)
        self.assertEqual(base_n, 0, "baseline already testable — fixture changed; revisit the bridge claim")
        self.assertGreater(sim_n, 0, "bridges did not make any live pick held-out testable")


if __name__ == "__main__":
    unittest.main()
