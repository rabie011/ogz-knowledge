#!/usr/bin/env python3
"""Locks the TASTE WRITEBACK BRIDGE (C245, June 30) — the loop that clears the B114 staleness
tripwire HONESTLY. The bridge PROPOSES kill-candidates from his own lowest-ranked captions; the
bar refreshes ONLY on his tap (apply_rulings.h_taste_refresh). These tests lock: (1) the harvester
surfaces bottom-ranked captions as candidates and never invents kills, (2) it never re-proposes an
already-killed caption, (3) prior verdicts (confirmed/rejected) survive a re-run and are not
re-surfaced (Rule #10 dedupe), (4) the confirm handler appends to founder_taste.kills + re-stamps
_meta.built so the tripwire clears, (5) confirm is idempotent, (6) reject excludes without killing."""
import json, sys, tempfile, unittest, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import taste_refresh as tr
import apply_rulings as ar


class TestTasteRefresh(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "data").mkdir()
        (self.d / "data/taste_elo.json").write_text(json.dumps({
            "n_pairs": 55,
            "bottom5_he_rejects": ["caption A bad", "caption B bad", "caption C bad"]}))
        (self.d / "data/founder_taste.json").write_text(json.dumps({
            "_meta": {"built": "2026-06-11"}, "kills": []}))
        self._orig_b = tr.B
        tr.B = self.d
        tr.ELO = self.d / "data/taste_elo.json"
        tr.TASTE = self.d / "data/founder_taste.json"
        tr.PROPOSALS = self.d / "data/taste_proposals.json"

    def tearDown(self):
        tr.B = self._orig_b
        tr.ELO = self._orig_b / "data/taste_elo.json"
        tr.TASTE = self._orig_b / "data/founder_taste.json"
        tr.PROPOSALS = self._orig_b / "data/taste_proposals.json"

    def test_harvester_surfaces_candidates_not_kills(self):
        out = tr.build_proposals()
        self.assertEqual(len(out["candidates"]), 3)
        self.assertEqual(out["_fresh_this_run"], 3)
        for c in out["candidates"].values():
            self.assertEqual(c["status"], "proposed")
            self.assertEqual(c["source"], "taste_elo.bottom5_he_rejects")
        # the bar is NOT touched by harvesting (we never author taste)
        self.assertEqual(json.loads(tr.TASTE.read_text())["kills"], [])

    def test_never_reproposes_already_killed(self):
        taste = json.loads(tr.TASTE.read_text())
        taste["kills"] = [{"caption": "caption A bad", "slug": "x"}]
        tr.TASTE.write_text(json.dumps(taste))
        out = tr.build_proposals()
        caps = {c["caption"] for c in out["candidates"].values()}
        self.assertNotIn("caption A bad", caps)
        self.assertEqual(len(out["candidates"]), 2)

    def test_prior_verdicts_survive_rerun(self):
        out = tr.build_proposals()
        slug = next(iter(out["candidates"]))
        prop = json.loads(tr.PROPOSALS.read_text())
        prop["candidates"][slug]["status"] = "rejected"
        tr.PROPOSALS.write_text(json.dumps(prop))
        out2 = tr.build_proposals()
        self.assertEqual(out2["candidates"][slug]["status"], "rejected")  # preserved
        self.assertEqual(out2["_fresh_this_run"], 0)  # nothing new — already seen
        self.assertEqual(len(tr.pending_cards(out2)), 2)  # the rejected one is no longer pending

    def test_confirm_refreshes_bar_and_clears_staleness(self):
        out = tr.build_proposals()
        slug = next(iter(out["candidates"]))
        cap = out["candidates"][slug]["caption"]
        msg = ar.h_taste_refresh(self.d, {"item_id": f"taste_kill_{slug}",
                                          "answer": "confirm", "ts": "2026-06-30T10:00"})
        taste = json.loads(tr.TASTE.read_text())
        self.assertTrue(any(k.get("slug") == slug for k in taste["kills"]))
        self.assertTrue(any(k.get("caption") == cap for k in taste["kills"]))
        self.assertEqual(taste["_meta"]["built"], datetime.date.today().isoformat())  # tripwire clears
        self.assertEqual(taste["kills"][-1]["confirmer"], "mohamed")  # never authored by us
        self.assertEqual(json.loads(tr.PROPOSALS.read_text())["candidates"][slug]["status"], "confirmed")
        self.assertIn("taste bar refreshed", msg)

    def test_confirm_is_idempotent(self):
        out = tr.build_proposals()
        slug = next(iter(out["candidates"]))
        row = {"item_id": f"taste_kill_{slug}", "answer": "confirm", "ts": "2026-06-30T10:00"}
        ar.h_taste_refresh(self.d, row)
        ar.h_taste_refresh(self.d, row)  # twice
        kills = json.loads(tr.TASTE.read_text())["kills"]
        self.assertEqual(sum(1 for k in kills if k.get("slug") == slug), 1)  # no duplicate

    def test_reject_excludes_without_killing(self):
        out = tr.build_proposals()
        slug = next(iter(out["candidates"]))
        ar.h_taste_refresh(self.d, {"item_id": f"taste_kill_{slug}",
                                    "answer": "reject", "ts": "2026-06-30T10:00"})
        self.assertEqual(json.loads(tr.TASTE.read_text())["kills"], [])  # nothing killed
        self.assertEqual(json.loads(tr.PROPOSALS.read_text())["candidates"][slug]["status"], "rejected")

    def test_unknown_candidate_refuses(self):
        tr.build_proposals()
        with self.assertRaises(RuntimeError):
            ar.h_taste_refresh(self.d, {"item_id": "taste_kill_nonexistent", "answer": "confirm"})


if __name__ == "__main__":
    unittest.main()
