#!/usr/bin/env python3
"""Locks B186b — the stage->portal drainer for confirm cards (the low-queue bridge).

The four laws this drainer must enforce STRUCTURALLY (not by comment):
  Rule #10 don't-flood : drains only when his VISIBLE load is low, in a small batch.
  Rule #7  pre-wire     : asserts a consumer resolves for every answer BEFORE draining.
  Rule #8  refuse       : a consumer-less card is HELD + reported, never drained.
  Rule #6  severed wire : buttons:[{value,label}] -> options:[{v,label}] (or the card is untappable).
And the end-to-end claim RABIE demanded: a drained card's TAP actually LANDS — apply_rulings
consumes it and the truth_pack flips on disk. The test uses the REAL _resolve, never a mock."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bridge_drain as bd
import apply_rulings


def _truth_card(i, handle="testbrand", cand="testprod"):
    return {"id": f"truth_confirm_{handle}_{i}", "kind": "buttons", "lane": "strategy",
            "organ": "truth_pack", "handle": handle, "candidate": cand,
            "title": f"✅ {handle} — تأكيد منتج", "why": "real product?",
            "buttons": [{"value": "confirm", "label": "✅ نعم"},
                        {"value": "reject", "label": "❌ لا"}]}


def _v37_card(i, handle="testbrand"):
    # kind text, organ visual_dna — NO handler exists for v37_* free-text (Rule #7 must catch this)
    return {"id": f"v37_{handle}_palette{i}", "kind": "text", "lane": "strategy",
            "organ": "visual_dna", "handle": handle, "title": "🎨 colour", "why": "brand colour?"}


def _sandbox(d, *, open_nonpw=0, open_pw=0, truth=2, v37=1, dead=0, answered=0):
    base = Path(d)
    (base / "data").mkdir(parents=True, exist_ok=True)
    items = []
    for j in range(open_nonpw):
        items.append({"id": f"organ_{j}", "status": "open", "kind": "text", "title": "x"})
    for j in range(open_pw):
        items.append({"id": f"pw_{j}", "status": "open", "kind": "buttons",
                      "options": [{"v": "a", "label": "A"}, {"v": "b", "label": "B"}]})
    for j in range(dead):
        items.append({"id": f"judge2_x_{j}", "status": "superseded_v6fix", "title": "dead"})
    for j in range(answered):
        items.append({"id": f"ans_{j}", "status": "answered", "title": "done"})
    (base / "data" / "decision_queue.json").write_text(
        json.dumps({"items": items}, ensure_ascii=False), encoding="utf-8")
    (base / "data" / "truth_confirm_staged.json").write_text(
        json.dumps({"cards": [_truth_card(i) for i in range(truth)]}, ensure_ascii=False),
        encoding="utf-8")
    (base / "data" / "v37_confirm_staged.json").write_text(
        json.dumps({"cards": [_v37_card(i) for i in range(v37)]}, ensure_ascii=False),
        encoding="utf-8")
    return base


def _queue(base):
    return json.loads((base / "data" / "decision_queue.json").read_text())["items"]


class TestBridgeDrain(unittest.TestCase):

    def test_normalize_makes_card_tappable(self):
        """Rule #6: staged buttons:[{value,label}] -> options:[{v,label}], 'buttons' removed,
        status open — the exact shape approvals.html renders and sends options[choice].v."""
        out = bd.normalize(_truth_card(0))
        self.assertNotIn("buttons", out)
        self.assertEqual([o["v"] for o in out["options"]], ["confirm", "reject"])
        self.assertEqual(out["status"], "open")
        self.assertEqual(out["kind"], "buttons")

    def test_drains_when_low_and_refuses_no_consumer(self):
        """Low load -> truth cards drain (consumer h_truth_confirm), v37 card HELD (no handler)."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=1, truth=2, v37=1)
            rep = bd.drain(base=base)
            self.assertEqual(set(rep["drained"]),
                             {"truth_confirm_testbrand_0", "truth_confirm_testbrand_1"})
            held = [h["id"] for h in rep["held_no_consumer"]]
            self.assertEqual(held, ["v37_testbrand_palette0"])
            # the v37 card is NOT on the queue — its tap had nowhere to land (Rule #7/#8)
            ids = {c["id"] for c in _queue(base)}
            self.assertNotIn("v37_testbrand_palette0", ids)
            self.assertIn("truth_confirm_testbrand_0", ids)

    def test_pw_stack_counts_as_one_not_eighteen(self):
        """Rule #10 sizing: 18 open pw_ collapse to 1 visible (portal shows one at a time),
        so the drainer is NOT starved by his pairwise backlog."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=18, truth=4, v37=0)
            rep = bd.drain(base=base)
            self.assertEqual(rep["visible_before"], 1)        # not 18
            self.assertEqual(len(rep["drained"]), bd.MAX_BATCH)

    def test_does_not_flood(self):
        """Visible load already at LOW_WATER -> zero slots -> nothing drains."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=bd.LOW_WATER, open_pw=0, truth=4, v37=0)
            rep = bd.drain(base=base)
            self.assertEqual(rep["slots"], 0)
            self.assertEqual(rep["drained"], [])

    def test_batch_capped(self):
        """Even at zero load the batch is capped (never dump the whole staged file at once)."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=20, v37=0)
            rep = bd.drain(base=base)
            self.assertEqual(len(rep["drained"]), bd.MAX_BATCH)

    def test_idempotent(self):
        """Second drain re-adds nothing already on the queue."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=1, truth=2, v37=0)
            bd.drain(base=base)
            n1 = len(_queue(base))
            rep2 = bd.drain(base=base)
            self.assertEqual(rep2["drained"], [])
            self.assertEqual(len(_queue(base)), n1)

    def test_dry_run_touches_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=2, v37=0)
            before = (base / "data" / "decision_queue.json").read_text()
            rep = bd.drain(base=base, dry_run=True)
            self.assertTrue(rep["drained"])                   # it WOULD drain
            self.assertEqual((base / "data" / "decision_queue.json").read_text(), before)

    def test_retires_dead_but_keeps_answered_and_unknown(self):
        """The bedrock fix: superseded cards (no reader) leave the active queue for the archive;
        answered (powers the done-list) and unknown statuses STAY. They were burying his pairwise tap."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_pw=1, dead=52, answered=3, truth=0, v37=0)
            # an unknown-status card must be preserved (kept = safe)
            qf = base / "data" / "decision_queue.json"
            q = json.loads(qf.read_text()); q["items"].append({"id": "mystery", "status": "?"})
            qf.write_text(json.dumps(q, ensure_ascii=False))
            rep = bd.drain(base=base)
            self.assertEqual(len(rep["retired_dead"]), 52)
            ids = {c["id"]: c["status"] for c in _queue(base)}
            self.assertTrue(all(not k.startswith("judge2_x_") for k in ids))   # dead gone
            self.assertIn("ans_0", ids)        # answered kept (done-list)
            self.assertIn("mystery", ids)      # unknown kept (safe)
            # the dead cards are recoverable in the archive (reversible, never deleted)
            arch = json.loads((base / "data" / "decision_queue_archive.json").read_text())["items"]
            self.assertEqual(len([c for c in arch if c["id"].startswith("judge2_x_")]), 52)

    def test_retire_dead_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, dead=10, truth=0, v37=0)
            bd.retire_dead(base)
            r2 = bd.retire_dead(base)
            self.assertEqual(r2["retired"], [])

    def test_drained_tap_lands_end_to_end(self):
        """RABIE's demand: prove a drained card's TAP actually LANDS. Drain a truth card, then
        route his 'confirm' through the REAL apply_rulings._resolve and assert the truth_pack
        provenance flips on disk — the full wire card->queue->resolve->consume."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=1, v37=0)
            # the consumer reads clients/<handle>/profile/truth_pack.json
            tp = base / "clients" / "testbrand" / "profile"
            tp.mkdir(parents=True, exist_ok=True)
            (tp / "truth_pack.json").write_text(json.dumps({"product_candidates": [
                {"name": "testprod",
                 "provenance": {"confirmer": "data_diagnosis", "confidence": "experimental"}}]}),
                encoding="utf-8")
            rep = bd.drain(base=base)
            cid = rep["drained"][0]
            # the card is on the queue as a tappable buttons card
            card = next(c for c in _queue(base) if c["id"] == cid)
            self.assertEqual(card["options"][0]["v"], "confirm")
            # his tap: resolve the (id, "confirm") through the SAME dispatcher the portal uses
            handler = apply_rulings._resolve((cid, "confirm"))
            self.assertIsNotNone(handler, "drained card has NO consumer — Rule #7 breach")
            handler(base, {"item_id": cid, "answer": "confirm"})
            on_disk = json.loads((tp / "truth_pack.json").read_text())["product_candidates"][0]
            self.assertEqual(on_disk["provenance"]["confidence"], "confirmed")
            self.assertEqual(on_disk["provenance"]["confirmer"], "mohamed")


if __name__ == "__main__":
    unittest.main()
