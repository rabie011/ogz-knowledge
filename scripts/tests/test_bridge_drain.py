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
    # kind text, organ visual_dna — h_v37_visual is its consumer (B186d), so it DRAINS.
    return {"id": f"v37_{handle}_palette{i}", "kind": "text", "lane": "strategy", "group": "colour",
            "organ": "visual_dna", "handle": handle, "title": "🎨 colour", "why": "brand colour?"}


def _orphan_card(i):
    # an id matching NO handler prefix — the refuse-no-consumer path must still HOLD it (Rule #7/#8)
    return {"id": f"noconsumer_{i}", "kind": "text", "lane": "strategy", "title": "orphan", "why": "?"}


def _sandbox(d, *, open_nonpw=0, open_pw=0, truth=2, v37=1, orphan=0, dead=0, answered=0):
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
        json.dumps({"cards": [_v37_card(i) for i in range(v37)] +
                             [_orphan_card(i) for i in range(orphan)]}, ensure_ascii=False),
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
        """Low load -> truth + v37 cards drain (both have consumers; v37 via h_v37_visual, B186d),
        while a genuinely consumer-less card is HELD, never drained (Rule #7/#8)."""
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=1, truth=1, v37=1, orphan=1)
            rep = bd.drain(base=base)
            # both wired card types drain; the orphan is refused
            self.assertIn("truth_confirm_testbrand_0", rep["drained"])
            self.assertIn("v37_testbrand_palette0", rep["drained"])
            held = [h["id"] for h in rep["held_no_consumer"]]
            self.assertEqual(held, ["noconsumer_0"])
            # the orphan is NOT on the queue — its tap had nowhere to land (Rule #7/#8)
            ids = {c["id"] for c in _queue(base)}
            self.assertNotIn("noconsumer_0", ids)
            self.assertIn("v37_testbrand_palette0", ids)

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


def _fake_taste_card(base):
    """A stand-in bridge taste pair (id 'pw_*' so apply_rulings routes it via h_pairwise_noop →
    consumer_ok passes). Keeps the reservation test sandbox-pure: no real PREFS/produced needed."""
    return {"id": "pw_faketestbridge01", "kind": "caption_pick", "lane": "creative",
            "handle": "testbrand", "pw_rank": 0, "status": "open",
            "options": [{"label": "A", "v": "a"}, {"label": "B", "v": "b"}]}


def _no_taste_card(base):
    return None   # nothing formable


class TestB186fTasteLaneReservation(unittest.TestCase):
    """Locks B186f — reserve the first free slot for ONE pairwise bridge taste pair so the held-out
    LIVE agreement (the TOP metric) can connect. Default OFF; bounded by Rule #10; consumer-asserted."""

    def test_default_off_changes_nothing(self):
        # reserve_taste_lane defaults False → no taste card, even with a free slot + formable bridge.
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=2, v37=0)
            rep = bd.drain(base=base, taste_card=_fake_taste_card)
            self.assertIsNone(rep["taste_reserved"])
            self.assertFalse(any(c["id"].startswith("pw_faketest") for c in _queue(base)))

    def test_reserves_one_taste_card_before_confirm_cards(self):
        # ON + slot free + no pw open + formable → exactly ONE taste card, and it EATS one slot
        # (confirm cards fill only the rest). low_water=8, visible=0 → slots=4 (max_batch); the taste
        # reservation spends 1 → at most 3 confirm cards drain.
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=10, v37=0)
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_fake_taste_card)
            self.assertEqual(rep["taste_reserved"], "pw_faketestbridge01")
            q = _queue(base)
            self.assertEqual(sum(c["id"].startswith("pw_faketest") for c in q), 1)
            self.assertEqual(len(rep["drained"]), bd.MAX_BATCH - 1)   # one slot reserved for taste

    def test_never_stacks_when_a_pw_card_is_open(self):
        # a pw card already occupies his single collapsed pw slot → do NOT add another (Rule #10).
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=1, truth=4, v37=0)
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_fake_taste_card)
            self.assertIsNone(rep["taste_reserved"])

    def test_no_reservation_when_his_queue_is_full(self):
        # his load already at low-water → 0 slots → no taste card forced on (Rule #10 don't-flood).
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=bd.LOW_WATER, open_pw=0, truth=4, v37=0)
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_fake_taste_card)
            self.assertEqual(rep["slots"], 0)
            self.assertIsNone(rep["taste_reserved"])

    def test_honest_noop_when_no_bridge_formable(self):
        # ON but nothing formable → no taste card, confirm cards drain normally (no crash, no lie).
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=4, v37=0)
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_no_taste_card)
            self.assertIsNone(rep["taste_reserved"])
            self.assertEqual(len(rep["drained"]), bd.MAX_BATCH)   # full batch, lane took nothing

    def test_dry_run_reserves_in_report_but_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=2, v37=0)
            before = json.dumps(_queue(base))
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_fake_taste_card,
                           dry_run=True)
            self.assertEqual(rep["taste_reserved"], "pw_faketestbridge01")
            self.assertEqual(json.dumps(_queue(base)), before)   # disk untouched

    def test_reserved_taste_card_has_a_real_consumer(self):
        # Rule #7: the reserved card's tap must LAND. apply_rulings routes 'pw_' → a handler.
        self.assertIsNotNone(apply_rulings._resolve(("pw_faketestbridge01", "")))

    def test_taste_card_persists_when_no_confirm_cards_drain(self):
        # Rule #6 severed-wire regression: the taste lane fires when his queue is LOW — exactly the
        # moment the confirm staging can be empty (truth=0, v37=0). The reservation must reach DISK,
        # not just the report. Bug (found 2026-06-21): the write was gated on `drained` being
        # non-empty, so the lone taste card was reported staged but never persisted — his one bridge
        # pair (the TOP metric's only connector) silently vanished.
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=0, v37=0)
            rep = bd.drain(base=base, reserve_taste_lane=True, taste_card=_fake_taste_card)
            self.assertEqual(rep["taste_reserved"], "pw_faketestbridge01")
            self.assertEqual(rep["drained"], [])                 # nothing else drained
            on_disk = {c["id"] for c in _queue(base)}
            self.assertIn("pw_faketestbridge01", on_disk)        # the report's claim is TRUE on disk

    def test_REAL_default_taste_card_reserves_and_persists_under_truth0(self):
        # The end-to-end claim RABIE demanded (18:20 shift whats_missing[1]): every test above injects
        # a FAKE taste_card, so the verdict-4 persistence fix was only ever proven against the stub.
        # This exercises the REAL _default_taste_card -> pairwise.bridge_pairs -> live PREFS/produced
        # path under the exact gate condition (truth=0, queue empty), where the lane actually fires.
        # If the real source ever stops forming a card, or its real pw_ id stops persisting, this bites
        # — not the fake. (Rule #6 consumer law on the TOP metric's only connector; Rule #9 real path.)
        import pairwise as pw
        capA = "كابتشن ألف — لقطة دافئة في المطبخ"
        capB = "كابتشن باء — عرض واضح بالسعر"
        capC = "كابتشن جيم — مشهد العائلة بعد يوم طويل"
        pool = [{"handle": "testbrand", "caption": c, "occasion": "يومي",
                 "scene": "مشهد", "date": f"2026-01-0{i}", "brain": "cd_01"}
                for i, c in enumerate([capA, capB, capC], 1)]
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=0, v37=0)
            prefs = base / "data" / "prefs_fixture.jsonl"
            prefs.write_text(json.dumps(
                {"source": "live", "winner_caption": capA, "loser_caption": capB,
                 "pair_id": "pw_alreadyjudged01"}, ensure_ascii=False) + "\n", encoding="utf-8")
            # monkeypatch the live globals the REAL bridge path reads (produced pool + PREFS + QUEUE)
            orig = (pw._produced, pw.PREFS, pw.QUEUE)
            try:
                pw._produced = lambda: pool
                pw.PREFS = prefs
                pw.QUEUE = base / "data" / "decision_queue.json"
                expected = pw.bridge_pairs(n=1)
                self.assertEqual(len(expected), 1)               # the fixture forms exactly one bridge
                expected_id = expected[0]["id"]
                # default taste_card == the REAL _default_taste_card (no injection)
                rep = bd.drain(base=base, reserve_taste_lane=True)
            finally:
                pw._produced, pw.PREFS, pw.QUEUE = orig
            self.assertEqual(rep["taste_reserved"], expected_id)  # real source's id, not a stub's
            self.assertTrue(expected_id.startswith("pw_"))
            on_disk = {c["id"] for c in _queue(base)}
            self.assertIn(expected_id, on_disk)                   # real card reached DISK, not just report
            self.assertIsNotNone(apply_rulings._resolve((expected_id, "")))  # Rule #7: real tap lands


class TestPerOrganCap(unittest.TestCase):
    """Rule #10 STANDING cap — one organ's confirm cards can't monopolize his queue ACROSS drains.
    MAX_BATCH bounds a single drain; this bounds the cumulative standing load so the taste-bridge
    lane (and every other lane) always keeps headroom — gate 1 of the TOP metric (his queue must
    drop below LOW_WATER for a bridge pair to win a slot)."""

    def test_one_organ_never_exceeds_cap_across_drains(self):
        # 10 truth_pack cards, empty queue: successive drains must plateau at PER_ORGAN_CAP, not 8.
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=10, v37=0)
            bd.drain(base=base)                                   # tops up to MAX_BATCH truth cards
            rep2 = bd.drain(base=base)                            # organ already at cap → blocked
            truth_open = sum(c.get("organ") == "truth_pack" for c in _queue(base))
            self.assertEqual(truth_open, bd.PER_ORGAN_CAP)        # capped — not the full 8 slots
            self.assertEqual(rep2["drained"], [])                 # nothing more of that organ drained
            self.assertTrue(rep2["held_organ_cap"])               # Rule #8 — held + reported, not silent

    def test_cap_leaves_headroom_no_organ_monopolizes(self):
        # 10 truth + 4 v37 staged, cap=2: each organ plateaus at its cap, so the queue settles well
        # BELOW LOW_WATER (2+2=4 of 8) — 4 slots stay free for the taste lane. Before the cap, the
        # 10 truth cards would have eaten every slot over successive drains and starved the bridge.
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=10, v37=4)
            bd.drain(base=base, per_organ_cap=2)
            rep2 = bd.drain(base=base, per_organ_cap=2)
            q = _queue(base)
            self.assertEqual(sum(c.get("organ") == "truth_pack" for c in q), 2)   # not 8 — capped
            self.assertEqual(sum(c.get("organ") == "visual_dna" for c in q), 2)   # got its fair share
            self.assertLess(bd.visible_open(q), bd.LOW_WATER)                     # headroom for taste
            self.assertTrue(rep2["held_organ_cap"])                              # surplus held, reported

    def test_cap_does_not_change_a_single_cold_drain(self):
        # Regression guard: from an empty queue one drain still fills MAX_BATCH (cap >= MAX_BATCH).
        with tempfile.TemporaryDirectory() as d:
            base = _sandbox(d, open_nonpw=0, open_pw=0, truth=20, v37=0)
            rep = bd.drain(base=base)
            self.assertEqual(len(rep["drained"]), bd.MAX_BATCH)


if __name__ == "__main__":
    unittest.main()
