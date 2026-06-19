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

    def test_handle_filter_restricts_to_one_pilot(self):
        """--handle albaik must yield ONLY albaik bridges (so a stranded pilot gets connected
        without re-flooding one that already has bridges, Rule #10). The filtered set must be a
        strict same-brand subset of the unfiltered set."""
        allps = pw.bridge_pairs(12)
        if not allps:
            self.skipTest("no live picks to bridge yet")
        brands = {p["handle"] for p in allps}
        target = sorted(brands)[0]
        only = pw.bridge_pairs(12, handle=target)
        self.assertTrue(all(p["handle"] == target for p in only),
                        f"--handle {target} leaked other brands")
        self.assertTrue({p["id"] for p in only}.issubset({p["id"] for p in allps}),
                        "handle-filtered bridges are not a subset of the unfiltered set")
        if len(brands) > 1:
            self.assertLess(len(only), len(allps), "filter did not drop the other brands' bridges")

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

    def test_bridge_status_is_honest_and_monotonic(self):
        """bridge_status (Step 5d) surfaces the gated-on-taps wait as a verified number so a
        one-tap-away HOLD never reads as a stall. Locks: (1) the three-key contract, (2) staging
        bridges never REDUCES testability (after >= now)."""
        st = pw.bridge_status()
        for k in ("staged", "n_testable_now", "n_testable_after"):
            self.assertIn(k, st)
        self.assertGreaterEqual(st["n_testable_after"], st["n_testable_now"],
                                "staging bridges reduced testability — a bridge must never disconnect")
        self.assertGreaterEqual(st["staged"], 0)

    def test_bridge_status_reports_bt_true_not_degree(self):
        """CONSUMER LAW LOCK (Rule #6/#9, June 19). The founder-facing `after taps=N` must equal what
        the real consumer (taste_elo.held_out_live, Bradley-Terry) delivers once he taps — his picks
        PLUS the bridge taps, both real choices — NOT the cheap structural degree-count, which
        over-states it (degree>=2 is necessary but not sufficient; June 19 it diverged 11 vs 13). This
        locks the wire so the proxy can never silently return to his phone."""
        prefs_file = Path(__file__).parent.parent.parent / "data/pairwise_prefs.jsonl"
        if not prefs_file.exists():
            self.skipTest("no prefs ledger")
        prefs = [json.loads(l) for l in prefs_file.read_text().splitlines() if l.strip()]
        if len([p for p in prefs if p.get("source") != "seed_from_ratings"]) < 2:
            self.skipTest("need >=2 live picks")
        st = pw.bridge_status()
        # rebuild the staged bridge edges exactly as bridge_status sees them
        from pathlib import Path as _P
        import json as _j
        q = _j.loads((_P(__file__).parent.parent.parent / "data/decision_queue.json").read_text())
        live_caps = set()
        for p in prefs:
            if p.get("source") != "seed_from_ratings":
                live_caps.add(p.get("winner_caption", "")); live_caps.add(p.get("loser_caption", ""))
        live_caps.discard("")
        staged = []
        for c in (q.get("items", []) if isinstance(q, dict) else q):
            if not str(c.get("id", "")).startswith("pw_") or c.get("status") != "open":
                continue
            o = {x.get("v"): x.get("label") for x in (c.get("options") or [])}
            a, b = o.get("a", ""), o.get("b", "")
            if a and b and (a in live_caps or b in live_caps):
                staged.append((a, b))

        def _pairs(rows):
            return [(r.get("winner_caption", ""), r.get("loser_caption", "")) for r in rows]
        after_rows = prefs + [{"winner_caption": a, "loser_caption": b, "source": "live_bridge"}
                              for a, b in staged]
        _, bt_after = te.held_out_live(_pairs(after_rows), after_rows)
        self.assertEqual(st["n_testable_after"], bt_after or 0,
                         "bridge_status.after != BT-true taps-as-live total — the degree proxy is back")
        # and it must be <= the structural upper bound that USED to be reported (sanity on the bound)
        self.assertLessEqual(te.held_out_live(_pairs(prefs), prefs)[1] or 0, pw.structural_testable(prefs))

    def test_structural_testable_is_winner_independent(self):
        """The winner-independence the docstring claims, now ASSERTED (it was promised but never
        checked — a docstring that lied about its own coverage). Swapping winner<->loser on every
        staged bridge edge must leave the structural `after` count unchanged: testability is a pure
        graph-degree property, so who he ends up picking can never move the number we show him."""
        prefs_file = Path(__file__).parent.parent.parent / "data/pairwise_prefs.jsonl"
        if not prefs_file.exists():
            self.skipTest("no prefs ledger")
        prefs = [json.loads(l) for l in prefs_file.read_text().splitlines() if l.strip()]
        ps = pw.bridge_pairs(12)
        if not ps:
            self.skipTest("no bridges proposed")
        edges = [(p["a"]["caption"], p["b"]["caption"]) for p in ps]
        swapped = [(b, a) for a, b in edges]
        self.assertEqual(pw.structural_testable(prefs, edges),
                         pw.structural_testable(prefs, swapped),
                         "swapping winner/loser changed the testability count — it is NOT winner-independent")

    def test_structural_is_upper_bound_on_bt_rankable(self):
        """CONSUMER LAW (Rule #6 + Rule #9). bridge_status shows him `after taps=N` from the cheap
        STRUCTURAL degree-count; the REAL eye-measure is taste_elo.held_out_live (Bradley-Terry).
        degree>=2 is NECESSARY for BT to rank a pick but NOT sufficient — the two captions must also
        land in the same connected component, untied. So over the SAME live set, BT-rankable can only
        be <= structural. This locks that bound: structural must never UNDER-count what BT needs (a
        logical impossibility that would mean a regression in either function). We tag the bridge
        edges as seed so they add connectivity WITHOUT entering the live set — measuring how many of
        his ORIGINAL picks BT can rank, against the structural bound on that same set.

        NOTE (June 19): the degree proxy used to BE the portal number and the "coincidentally equal"
        defense DRIFTED — late June 19 structural=11 while the consumer delivered 13 (taps-as-live),
        so the proxy matched neither true value (5 existing, 13 total). bridge_status now reports the
        BT-true consumer number directly (see test_bridge_status_reports_bt_true_not_degree). This test
        keeps ONLY the always-true bound: BT-rankable over the SAME live set <= structural (degree is
        necessary, not sufficient — disjoint BT components tie). structural under-counting BT would be
        a real regression in either function."""
        prefs_file = Path(__file__).parent.parent.parent / "data/pairwise_prefs.jsonl"
        if not prefs_file.exists():
            self.skipTest("no prefs ledger")
        prefs = [json.loads(l) for l in prefs_file.read_text().splitlines() if l.strip()]
        if len([p for p in prefs if p.get("source") != "seed_from_ratings"]) < 2:
            self.skipTest("need >=2 live picks")
        ps = pw.bridge_pairs(12)
        if not ps:
            self.skipTest("no bridges proposed")
        edges = [(p["a"]["caption"], p["b"]["caption"]) for p in ps]

        def to_pairs(rows):
            caps = {}
            def cid(c):
                return caps.setdefault(c, len(caps))
            return [(cid(r["winner_caption"]), cid(r["loser_caption"])) for r in rows]

        # bridge edges as SEED → connectivity only, original picks stay the measured live set
        sim = list(prefs) + [{"winner_caption": a, "loser_caption": b, "source": "seed_from_ratings"}
                             for a, b in edges]
        _, bt_now = te.held_out_live(to_pairs(prefs), prefs)
        _, bt_after = te.held_out_live(to_pairs(sim), sim)
        struct_now = pw.structural_testable(prefs)
        struct_after = pw.structural_testable(prefs, edges)
        self.assertLessEqual(bt_now, struct_now,
                             "BT ranked more 'now' than degree allows — structural under-counts (regression)")
        self.assertLessEqual(bt_after, struct_after,
                             "BT ranked more 'after' than degree allows — structural under-counts (regression)")
        # and the structural count must move the right way once bridges connect the graph
        self.assertGreaterEqual(struct_after, struct_now)


class TestBridgeFullCoverage(unittest.TestCase):
    """B280 (June 19): the old greedy matcher left one live pick held-out-untestable (the 11/12
    ceiling) — it consumed a caption's only free partner early and stranded a caption whose sole
    remaining partner was its own already-judged pick-mate. The fix is a MAXIMUM matching plus a
    spare/already-covered fallback. This locks the guarantee on a controlled fixture: whenever each
    brand has >=2 spare (non-live) pool partners, EVERY live caption is coverable, so after the
    proposed bridges structural_testable must equal n_live (no caption left stranded). Two brands
    exercise both paths — A: covered by live-live matching; D: a single same-pick pair (cannot bridge
    to each other) that MUST fall back to spares."""

    def _run(self, produced, live_picks):
        import tempfile
        prefs_rows = [{"winner_caption": w, "loser_caption": l, "pair_id": pw._pid({"caption": w}, {"caption": l})}
                      for w, l in live_picks]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for r in prefs_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp = Path(f.name)
        orig_prefs, orig_prod, orig_excl = pw.PREFS, pw._produced, pw._judged_or_live_pids
        try:
            pw.PREFS = tmp
            pw._produced = lambda: list(produced)
            pw._judged_or_live_pids = lambda: {r["pair_id"] for r in prefs_rows}
            ps = pw.bridge_pairs(50)
        finally:
            pw.PREFS, pw._produced, pw._judged_or_live_pids = orig_prefs, orig_prod, orig_excl
            tmp.unlink()
        edges = [(p["a"]["caption"], p["b"]["caption"]) for p in ps]
        return prefs_rows, edges

    def test_every_coverable_caption_is_bridged_when_spares_exist(self):
        produced = (
            [{"handle": "A", "caption": c} for c in ("A1", "A2", "A3", "A4", "As1", "As2")] +
            [{"handle": "D", "caption": c} for c in ("D1", "D2", "Ds1", "Ds2")]
        )
        live_picks = [("A1", "A2"), ("A3", "A4"), ("D1", "D2")]
        prefs_rows, edges = self._run(produced, live_picks)
        self.assertEqual(pw.structural_testable(prefs_rows), 0, "fixture should start fully untestable")
        self.assertEqual(pw.structural_testable(prefs_rows, edges), len(live_picks),
                         "a coverable live caption was left stranded — the 11/12-style ceiling is back")
        # every bridge stays NEW (never recreates a live pick) and reuses a judged caption
        live_caps = {c for pk in live_picks for c in pk}
        for a, b in edges:
            self.assertNotEqual(a, b)
            self.assertTrue(a in live_caps or b in live_caps)


if __name__ == "__main__":
    unittest.main()
