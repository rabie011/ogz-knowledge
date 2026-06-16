#!/usr/bin/env python3
"""Locks the scene-context back-patch (Step 3a, June 16): adding context to the 11 live pairwise
cards must NEVER change an id or an options[i].v / options[i].label — that's the durable-card wire
pairwise._pairs_from_cards reads (the June-15 severed-surface scar). Operates on a deep COPY of the
live queue, so the test never mutates production data."""
import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import backpatch_pw_context as bp
import pairwise as pw

R = Path(__file__).parent.parent.parent


class TestBackpatchContext(unittest.TestCase):
    def setUp(self):
        self.q = json.loads((R / "data/decision_queue.json").read_text())
        self.open_pw = [c for c in self.q.get("items", [])
                        if str(c.get("id", "")).startswith("pw_") and c.get("status") != "answered"]

    def test_ids_and_option_values_preserved(self):
        if not self.open_pw:
            self.skipTest("no open pw_ cards")
        before = {c["id"]: [(o.get("v"), o.get("label")) for o in c.get("options", [])] for c in self.open_pw}
        q2 = copy.deepcopy(self.q)
        bp.transform(q2, bp._post_index())
        after = {c["id"]: [(o.get("v"), o.get("label")) for o in c.get("options", [])]
                 for c in q2.get("items", []) if str(c.get("id", "")).startswith("pw_") and c.get("status") != "answered"}
        self.assertEqual(set(before), set(after), "a pw_ card id changed — taps would orphan")
        for cid in before:
            self.assertEqual(before[cid], after[cid], f"options v/label changed on {cid} — durable wire broken")

    def test_matched_cards_gain_context(self):
        q2 = copy.deepcopy(self.q)
        stats = bp.transform(q2, bp._post_index())
        if stats["matched"] == 0:
            self.skipTest("no posts matched")
        # every matched card has at least one option with a scene, or a card-level occasion
        for c in q2.get("items", []):
            if not (str(c.get("id", "")).startswith("pw_") and c.get("status") != "answered"):
                continue
            opts = c.get("options", [])
            has_ctx = c.get("post_occasion") or any(o.get("scene") for o in opts)
            # only assert on cards whose captions matched a post (unmatched stay bare, allowed)
            if any(o.get("label") in bp._post_index() for o in opts):
                self.assertTrue(has_ctx, f"matched card {c['id']} gained no context")

    def test_durable_backstop_still_resolves_after_transform(self):
        """The Rule #6 wire: _pairs_from_cards must still reconstruct every open pw_ pair post-context."""
        q2 = copy.deepcopy(self.q)
        bp.transform(q2, bp._post_index())
        # simulate the durable reader over the transformed cards
        cards = {str(c["id"]): c for c in q2.get("items", []) if str(c.get("id", "")).startswith("pw_")}
        for cid, c in cards.items():
            if c.get("status") == "answered":
                continue
            opts = {o.get("v"): o.get("label") for o in (c.get("options") or [])}
            self.assertIn("a", opts); self.assertIn("b", opts)
            self.assertTrue(opts["a"] and opts["b"], f"{cid} lost a caption — pair unresolvable")


if __name__ == "__main__":
    unittest.main()
