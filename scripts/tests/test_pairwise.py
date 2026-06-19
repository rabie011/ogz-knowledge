#!/usr/bin/env python3
"""Guards the pairwise taste-calibration loop (the moat, 2026-06-14). Locks: pairs form with stable
ids from real pilot output; the A/B pick has a HANDLER in apply_rulings so it can never sit
UNCONSUMED (Rule #6/#7); and the pairwise consumer is wired into apply_rulings.main()."""
import inspect, json, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import pairwise as pw
import apply_rulings as ar


class TestPairwiseLoop(unittest.TestCase):

    def test_pairs_form_with_stable_ids(self):
        pairs = pw.form_pairs(2)
        if not pairs:
            self.skipTest("no produced captions to pair")
        p = pairs[0]
        self.assertTrue(p["id"].startswith("pw_"))
        self.assertIn("caption", p["a"])
        self.assertIn("caption", p["b"])
        self.assertNotEqual(p["a"]["caption"], p["b"]["caption"])  # a real A-vs-B
        # id is deterministic (same pair → same id)
        self.assertEqual(p["id"], pw._pid(p["a"], p["b"]))

    def test_pick_has_a_handler_never_unconsumed(self):
        """Rule #6/#7: a pw_ pick must resolve to a handler so apply_rulings doesn't flag UNCONSUMED."""
        fn = ar._resolve(("pw_abc123", "A"))
        self.assertIsNotNone(fn, "pairwise pick has NO handler — it would sit UNCONSUMED")

    def test_consumer_wired_into_apply_rulings(self):
        src = inspect.getsource(ar.main)
        self.assertIn("pairwise", src, "pairwise.consume() not wired into apply_rulings.main()")

    def test_writer_and_reader_same_file(self):
        """Consumer Law (June 15 severed-wire scar): the file the PORTAL writes taps to MUST be the
        file consume() reads, or every live pick is silently lost."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("portal_mini", Path(__file__).parent.parent.parent / "api/portal_mini.py")
        # read the portal's ANSWERS path textually (avoid importing the FastAPI app)
        psrc = (Path(__file__).parent.parent.parent / "api/portal_mini.py").read_text()
        self.assertIn("mohamed_answers.jsonl", psrc, "portal answer file changed")
        self.assertTrue(pw.ANSWERS.name == "mohamed_answers.jsonl",
                        f"consume() reads {pw.ANSWERS.name} but the portal writes mohamed_answers.jsonl — severed wire")



    def test_new_pairs_carry_scene_context(self):
        """June 16: a freshly-formed pair's candidates must carry occasion+scene so push_cards can
        stamp per-option context — and _pid must stay a pure function of the captions (id stability)."""
        pairs = pw.form_pairs(2)
        if not pairs:
            self.skipTest("no produced captions")
        p = pairs[0]
        self.assertIn("occasion", p["a"], "candidate lost occasion context")
        self.assertEqual(p["id"], pw._pid(p["a"], p["b"]), "id derivation drifted from the caption pair")
        self.assertIsInstance(pw._scene_line(p["a"]), str)

    def test_tap_resolves_from_durable_card_not_overwritable_file(self):
        """June 15 severed-surface scar: form_pairs() overwrites pairwise_pairs.json, so a tap on a
        live card whose pair was overwritten would vanish. consume() must resolve from the DURABLE
        card (queue), which embeds both captions. Locks that every pushed pw_ card stays resolvable."""
        import json
        from_cards = pw._pairs_from_cards()
        q = json.loads((Path(__file__).parent.parent.parent / "data/decision_queue.json").read_text())
        open_pw = [c for c in q.get("items", []) if str(c.get("id","")).startswith("pw_") and c.get("status","open")=="open"]
        if not open_pw:
            self.skipTest("no open pairwise cards")
        missing = [c["id"] for c in open_pw if c["id"] not in from_cards]
        self.assertEqual(missing, [], f"{len(missing)} live cards unresolvable from the durable card — his taps would vanish")


class TestConsumeRoundTrip(unittest.TestCase):
    """END-TO-END parse guard (the gap the plumbing tests missed): a real A/B tap must round-trip
    through consume() into a CORRECT preference record. The plumbing tests lock the file name and
    card-resolvability; NONE exercised consume()'s actual parse — `ans.startswith` → winner →
    p[winner]['caption'] — the single most load-bearing line of the taste-capture loop. If that
    parse drifted (e.g. resolved 'b'→a, or matched on the caption label instead of the option `v`),
    his taps would silently invert and corrupt the moat with zero test failure. Fully isolated:
    swaps the module's file globals to a tmpdir, never touches real data."""

    def setUp(self):
        import tempfile
        self._saved = {k: getattr(pw, k) for k in ("ANSWERS", "PREFS", "PAIRS", "QUEUE")}
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)
        pw.ANSWERS, pw.PREFS, pw.PAIRS, pw.QUEUE = d / "ans.jsonl", d / "prefs.jsonl", d / "pairs.json", d / "queue.json"
        pw.QUEUE.write_text(json.dumps({"items": []}))  # no durable cards by default

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(pw, k, v)
        self._tmp.cleanup()

    def _pair(self):
        return {"id": "pw_rt001", "handle": "albaik",
                "a": {"caption": "CAP-ALPHA", "brain": "firaasa"},
                "b": {"caption": "CAP-BETA", "brain": "paradox"}}

    def test_tap_a_resolves_to_a_caption(self):
        pw.PAIRS.write_text(json.dumps([self._pair()]))
        pw.ANSWERS.write_text(json.dumps({"item_id": "pw_rt001", "answer": "a", "judge": "mohamed", "ts": 1}) + "\n")
        self.assertEqual(pw.consume(), 1)
        rec = json.loads(pw.PREFS.read_text().splitlines()[0])
        self.assertEqual(rec["winner"], "a")
        self.assertEqual(rec["winner_caption"], "CAP-ALPHA")
        self.assertEqual(rec["loser_caption"], "CAP-BETA")
        self.assertEqual(rec["winner_brain"], "firaasa")

    def test_tap_b_resolves_to_b_caption(self):
        pw.PAIRS.write_text(json.dumps([self._pair()]))
        pw.ANSWERS.write_text(json.dumps({"item_id": "pw_rt001", "answer": "b"}) + "\n")
        self.assertEqual(pw.consume(), 1)
        rec = json.loads(pw.PREFS.read_text().splitlines()[0])
        self.assertEqual(rec["winner"], "b")
        self.assertEqual(rec["winner_caption"], "CAP-BETA")
        self.assertEqual(rec["loser_caption"], "CAP-ALPHA")

    def test_resolves_from_durable_card_when_side_file_gone(self):
        # the June-15 scar in behavior: pair only in the durable card, side-file overwritten/empty
        card = {"id": "pw_rt001", "handle": "albaik", "options": [
            {"v": "a", "label": "CAP-ALPHA"}, {"v": "b", "label": "CAP-BETA"}]}
        pw.QUEUE.write_text(json.dumps({"items": [card]}))
        pw.ANSWERS.write_text(json.dumps({"item_id": "pw_rt001", "answer": "a"}) + "\n")
        self.assertEqual(pw.consume(), 1)
        rec = json.loads(pw.PREFS.read_text().splitlines()[0])
        self.assertEqual(rec["winner_caption"], "CAP-ALPHA")

    def test_non_ab_answer_is_skipped_not_corrupted(self):
        pw.PAIRS.write_text(json.dumps([self._pair()]))
        pw.ANSWERS.write_text(json.dumps({"item_id": "pw_rt001", "answer": "skip"}) + "\n")
        self.assertEqual(pw.consume(), 0)
        self.assertFalse(pw.PREFS.exists() and pw.PREFS.read_text().strip())

    def test_already_seen_pid_not_double_counted(self):
        pw.PAIRS.write_text(json.dumps([self._pair()]))
        pw.ANSWERS.write_text(json.dumps({"item_id": "pw_rt001", "answer": "a"}) + "\n")
        self.assertEqual(pw.consume(), 1)
        self.assertEqual(pw.consume(), 0)  # second run: pid already in prefs → no duplicate
        self.assertEqual(len(pw.PREFS.read_text().splitlines()), 1)


class TestLivePortalBridgeCardsLand(unittest.TestCase):
    """Rule #7 on the LIVE surface: the cards already on his phone must have a landing handler.
    TestConsumeRoundTrip proves consume() works on SYNTHETIC cards; this proves it works on the
    REAL open pw_ cards in decision_queue.json RIGHT NOW — the exact thing the June-15 severance
    broke (11 real staged taps would have vanished). It copies the real queue into a tmpdir, fires
    a synthetic tap at every open pw_ card through the full consume() pipeline, and asserts each
    one resolves into a correct preference. If a future form_pairs()/push ever re-severs a live
    card's pair, this FAILS naming the orphaned card — instead of his tap landing in the void."""

    def setUp(self):
        import tempfile
        self._real_queue = Path(pw.__file__).parent.parent / "data/decision_queue.json"
        self._saved = {k: getattr(pw, k) for k in ("ANSWERS", "PREFS", "PAIRS", "QUEUE")}
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)
        pw.ANSWERS, pw.PREFS, pw.PAIRS, pw.QUEUE = d / "ans.jsonl", d / "prefs.jsonl", d / "pairs.json", d / "queue.json"
        # copy the REAL portal queue in verbatim — the durable card is the only pair source
        pw.QUEUE.write_text(self._real_queue.read_text() if self._real_queue.exists() else json.dumps({"items": []}))

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(pw, k, v)
        self._tmp.cleanup()

    def _open_pw_cards(self):
        q = json.loads(pw.QUEUE.read_text())
        items = q.get("items", []) if isinstance(q, dict) else q
        return [c for c in items if str(c.get("id", "")).startswith("pw_") and c.get("status") == "open"]

    def test_every_live_pw_card_is_resolvable(self):
        """Precondition for landing: each open pw_ card must carry both option labels, or
        _pairs_from_cards() can't reconstruct its pair and the tap is silently dropped."""
        cards = self._open_pw_cards()
        if not cards:
            self.skipTest("no open pw_ cards on the portal right now")
        resolvable = pw._pairs_from_cards()
        orphans = [c.get("id") for c in cards if c.get("id") not in resolvable]
        self.assertEqual(orphans, [], f"open pw_ cards with no landing handler (Rule #7 severed): {orphans}")

    def test_a_tap_on_every_live_card_lands_as_a_preference(self):
        """End-to-end: fire one synthetic tap at each open pw_ card and assert consume() turns
        ALL of them into preference records — the whole batch his phone could send must land."""
        cards = self._open_pw_cards()
        if not cards:
            self.skipTest("no open pw_ cards on the portal right now")
        with pw.ANSWERS.open("w") as f:
            for i, c in enumerate(cards):
                f.write(json.dumps({"item_id": c["id"], "answer": "a" if i % 2 == 0 else "b",
                                    "judge": "mohamed_sim", "ts": i}) + "\n")
        n = pw.consume()
        self.assertEqual(n, len(cards), f"only {n}/{len(cards)} live taps landed — the rest vanished")
        self.assertEqual(len(pw.PREFS.read_text().splitlines()), len(cards))
        for line in pw.PREFS.read_text().splitlines():
            rec = json.loads(line)
            self.assertTrue(rec.get("winner_caption"), "landed pref has empty winner_caption")
            self.assertTrue(rec.get("loser_caption"), "landed pref has empty loser_caption")


if __name__ == "__main__":
    unittest.main()
