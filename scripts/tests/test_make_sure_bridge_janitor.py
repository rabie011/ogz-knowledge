#!/usr/bin/env python3
"""Locks B186c — make_sure runs bridge_drain as a STANDING janitor every cadence.

Before B186c the drainer was a one-shot: his portal silently re-cluttered with superseded (dead)
cards and freshly-staged confirm cards never reached him between hand-runs — the bedrock reason his
picks stopped flowing (zoom-out, June 21). make_sure already fires deterministically every cadence,
so it is the standing host. The contracts that must never break:
  1. one cadence retires dead cards AND tops up staged confirm cards onto his queue (end-to-end),
  2. it is IDEMPOTENT — a second cadence with nothing new drains 0, retires 0 (Rule #10 no-flood),
  3. a janitor FAILURE is captured into the surface, never raised (the self-check stays unbreakable).
Uses the REAL bridge_drain.drain against a sandbox base — no mocks on the wire under test."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms
import bridge_drain as bd


def _truth_card(i, handle="testbrand", cand="testprod"):
    return {"id": f"truth_confirm_{handle}_{i}", "kind": "buttons", "lane": "strategy",
            "organ": "truth_pack", "handle": handle, "candidate": cand,
            "title": f"✅ {handle} — تأكيد منتج", "why": "real product?",
            "buttons": [{"value": "confirm", "label": "✅ نعم"},
                        {"value": "reject", "label": "❌ لا"}]}


def _v37_card(i, handle="testbrand"):
    # v37_* free-text has a consumer (h_v37_visual, B186d) — it DRAINS.
    return {"id": f"v37_{handle}_palette{i}", "kind": "text", "lane": "strategy", "group": "colour",
            "organ": "visual_dna", "handle": handle, "title": "🎨 colour", "why": "brand colour?"}


def _orphan_card(i):
    # an id matching NO handler prefix — must be HELD, never drained, never retired (Rule #7/#8).
    return {"id": f"noconsumer_{i}", "kind": "text", "lane": "strategy", "title": "orphan", "why": "?"}


def _sandbox(d, *, dead=0, truth=2, v37=1, orphan=0):
    base = Path(d)
    (base / "data").mkdir(parents=True, exist_ok=True)
    items = [{"id": f"superseded_corpse_{j}", "status": "superseded_v6fix", "title": "dead"}
             for j in range(dead)]
    (base / "data" / "decision_queue.json").write_text(
        json.dumps({"items": items}, ensure_ascii=False), encoding="utf-8")
    (base / "data" / "truth_confirm_staged.json").write_text(
        json.dumps({"cards": [_truth_card(i) for i in range(truth)]}, ensure_ascii=False),
        encoding="utf-8")
    (base / "data" / "v37_confirm_staged.json").write_text(
        json.dumps({"cards": [_v37_card(i) for i in range(v37)] +
                             [_orphan_card(i) for i in range(orphan)]}, ensure_ascii=False),
        encoding="utf-8")
    return base


def _queue_ids(base):
    return {c["id"] for c in json.loads((base / "data" / "decision_queue.json").read_text())["items"]}


class TestMakeSureBridgeJanitor(unittest.TestCase):

    def test_one_cadence_retires_dead_and_drains_confirm(self):
        """End-to-end in a single make_sure cadence: dead cards leave his portal, consumer-backed
        confirm cards land, the consumer-less v37 card is HELD (counted, not drained)."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, dead=3, truth=2, v37=1, orphan=1)
            surf = ms.standing_janitor(base)
            self.assertEqual(surf["_bridge_retired"], 3)
            self.assertEqual(set(surf["_bridge_drained"]),
                             {"truth_confirm_testbrand_0", "truth_confirm_testbrand_1",
                              "v37_testbrand_palette0"})
            self.assertEqual(surf["_bridge_held"], 1)  # the orphan, refused
            self.assertNotIn("_bridge_error", surf)
            ids = _queue_ids(base)
            # dead corpses gone, confirm + v37 cards landed, orphan (no consumer) never on the queue
            self.assertFalse(any(i.startswith("superseded_corpse_") for i in ids))
            self.assertIn("truth_confirm_testbrand_0", ids)
            self.assertIn("v37_testbrand_palette0", ids)
            self.assertNotIn("noconsumer_0", ids)

    def test_idempotent_second_cadence_is_a_noop(self):
        """Rule #10: re-running with nothing new retires 0 and drains 0 — his queue does not re-clutter
        and is not re-flooded with the same cards."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, dead=2, truth=2, v37=1)
            ms.standing_janitor(base)
            second = ms.standing_janitor(base)
            self.assertEqual(second["_bridge_retired"], 0)
            self.assertEqual(second["_bridge_drained"], [])

    def test_janitor_failure_is_captured_never_raised(self):
        """The self-check must stay unbreakable: a drainer blow-up surfaces as `_bridge_error`,
        not an exception that aborts make_sure (June 20 lesson — one organ must never blind the rest)."""
        orig = bd.drain
        try:
            bd.drain = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
            surf = ms.standing_janitor(Path("/nonexistent"))
            self.assertIn("_bridge_error", surf)
            self.assertIn("boom", surf["_bridge_error"])
        finally:
            bd.drain = orig


if __name__ == "__main__":
    unittest.main()
