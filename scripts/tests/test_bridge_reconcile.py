#!/usr/bin/env python3
"""Locks B281 — the STAGING-AWARE bridge reconcile (June 20). The improved maximum-matcher (B280)
proposes a bridge set that beats the staged one (12/12 vs 11/12) but partly disjoint from it; pushing
it blind would FLOOD his portal with two competing bridge sets (Rule #10). reconcile_bridges must
instead: KEEP the open bridges the matcher still wants, CLOSE (status→superseded) the ones it no longer
wants, PUSH ONLY the delta, and NEVER close a card he has already tapped (Consumer Law). These tests
lock that contract hermetically (temp queue + monkeypatched matcher), independent of the live data."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pairwise as pw


def _bridge_card(pid):
    return {"id": pid, "kind": "caption_pick", "status": "open", "pw_rank": 0,
            "options": [{"label": f"{pid}-A", "v": "a"}, {"label": f"{pid}-B", "v": "b"}]}


class TestBridgeReconcile(unittest.TestCase):
    def setUp(self):
        # 3 open bridge cards on the portal: K (matcher still wants), C (superseded), M (he tapped it)
        self.tmpdir = Path(tempfile.mkdtemp())
        self.queue = self.tmpdir / "decision_queue.json"
        self.answers = self.tmpdir / "mohamed_answers.jsonl"
        self.queue.write_text(json.dumps(
            {"items": [_bridge_card("pw_keep"), _bridge_card("pw_close"), _bridge_card("pw_midtap"),
                       # a non-bridge (rank 2) open pw card must be left ENTIRELY alone
                       {"id": "pw_random", "status": "open", "pw_rank": 2,
                        "options": [{"label": "r-A", "v": "a"}, {"label": "r-B", "v": "b"}]}]},
            ensure_ascii=False))
        self.answers.write_text(json.dumps({"item_id": "pw_midtap", "answer": "a"}) + "\n")
        # matcher target (clean-slate): wants pw_keep (already open) + pw_new (the delta). NOT close/midtap.
        self._target = [{"id": "pw_keep", "handle": "A", "a": {"caption": "k-A"}, "b": {"caption": "k-B"}},
                        {"id": "pw_new", "handle": "A", "a": {"caption": "n-A"}, "b": {"caption": "n-B"}}]
        self._orig = (pw.QUEUE, pw.ANSWERS, pw.bridge_pairs, pw._push)
        pw.QUEUE = self.queue
        pw.ANSWERS = self.answers
        pw.bridge_pairs = lambda n=8, handle=None, exclude=None: list(self._target)
        # hermetic push: append the delta as open rank-0 cards (skip attribution/bench side effects)
        def _fake_push(pairs, rank=2):
            q = json.loads(self.queue.read_text())
            for p in pairs:
                c = _bridge_card(p["id"]); c["pw_rank"] = rank
                q["items"].append(c)
            self.queue.write_text(json.dumps(q, ensure_ascii=False))
            return len(pairs)
        pw._push = _fake_push

    def tearDown(self):
        pw.QUEUE, pw.ANSWERS, pw.bridge_pairs, pw._push = self._orig
        for f in (self.queue, self.answers):
            if f.exists():
                f.unlink()
        self.tmpdir.rmdir()

    def test_preview_plan_is_correct(self):
        r = pw.reconcile_bridges(apply=False)
        self.assertEqual(r["target"], 2)
        self.assertEqual(r["keep"], 1)            # pw_keep
        self.assertEqual(r["close"], 1)           # pw_close (superseded, not tapped)
        self.assertEqual(r["push"], 1)            # pw_new (the delta)
        self.assertEqual(r["skipped_midtap"], 1)  # pw_midtap protected

    def test_preview_does_not_mutate_queue(self):
        before = self.queue.read_text()
        pw.reconcile_bridges(apply=False)
        self.assertEqual(self.queue.read_text(), before, "preview must be read-only")

    def test_apply_supersedes_not_stacks(self):
        pw.reconcile_bridges(apply=True)
        q = json.loads(self.queue.read_text())
        by = {c["id"]: c for c in q["items"]}
        # KEEP stays open; DELTA pushed open rank-0; SUPERSEDED closed; MID-TAP protected; RANDOM untouched
        self.assertEqual(by["pw_keep"]["status"], "open")
        self.assertEqual(by["pw_new"]["status"], "open")
        self.assertEqual(by["pw_new"]["pw_rank"], 0)
        self.assertEqual(by["pw_close"]["status"], "superseded")
        self.assertIn("superseded_reason", by["pw_close"])
        self.assertEqual(by["pw_midtap"]["status"], "open", "a tapped card must never be closed (Consumer Law)")
        self.assertEqual(by["pw_random"]["status"], "open", "a non-bridge pw card must be left alone")
        # END STATE = the target's OPEN bridges + the protected mid-tap (no two competing sets — Rule #10).
        # pw_midtap stays open ONLY because he tapped it; consume() banks it, then the next run reconciles it.
        open_bridges = {c["id"] for c in q["items"] if c.get("pw_rank") == 0 and c["status"] == "open"}
        self.assertEqual(open_bridges, {"pw_keep", "pw_new", "pw_midtap"},
                         "open bridge set is not target + protected mid-tap")

    def test_apply_is_idempotent(self):
        pw.reconcile_bridges(apply=True)
        r2 = pw.reconcile_bridges(apply=True)   # second run: nothing left to change
        self.assertEqual(r2["close"], 0)
        self.assertEqual(r2["push"], 0)
        self.assertEqual(r2["keep"], 2)         # both target bridges now open & wanted


if __name__ == "__main__":
    unittest.main()
