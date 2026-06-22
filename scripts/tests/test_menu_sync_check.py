"""B174 — menu_sync_check: a scraped menu price that drifts from the CONFIRMED
truth_pack must surface as a PROPOSAL (human confirms), and must NEVER overwrite
truth_pack (One Write Path). These tests pin the pure diff and assert the two
laws: (1) a seeded price change produces a proposal, (2) truth_pack is untouched.
No live network is exercised — fetch_live_menu is never called; a seeded menu is
injected, and ledger_write is captured in-memory so no real client ledger is hit.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import menu_sync_check as msc


class TestDiffMenu(unittest.TestCase):
    def test_changed_price_is_a_delta(self):
        truth = [{"name": "بروست", "price": 15}]
        live = {"بروست": 18}
        d = msc.diff_menu(truth, live)
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["kind"], "changed")
        self.assertEqual(d[0]["from"], 15.0)
        self.assertEqual(d[0]["to"], 18.0)

    def test_added_and_removed(self):
        truth = {"بروست": 15, "فيليه": 20}
        live = {"بروست": 15, "ساندويتش": 12}
        kinds = {x["item"]: x["kind"] for x in msc.diff_menu(truth, live)}
        self.assertEqual(kinds, {"ساندويتش": "added", "فيليه": "removed"})

    def test_no_drift_no_deltas(self):
        truth = {"بروست": 15.0}
        live = {"بروست": 15.0}
        self.assertEqual(msc.diff_menu(truth, live), [])

    def test_malformed_rows_dropped_not_crashed(self):
        truth = [{"name": "بروست", "price": "not-a-number"}, {"no_name": 1}, "junk"]
        live = {"بروست": 15}
        # truth side fully dropped → the live price reads as an addition, no crash
        d = msc.diff_menu(truth, live)
        self.assertEqual([x["kind"] for x in d], ["added"])


class TestProposalAndOneWritePath(unittest.TestCase):
    def setUp(self):
        # Use a real on-disk truth_pack (read-only) to prove it is untouched.
        self.tp = msc._truth_pack_path("albaik")
        self.assertTrue(self.tp.exists(), "albaik truth_pack must exist for this test")
        self.before = self.tp.read_bytes()

    def test_seeded_change_emits_proposal_and_leaves_truth_pack_untouched(self):
        # Seed albaik truth_pack's first confirmed product with a price, then feed
        # a live menu where that price changed — assert a PROPOSAL is emitted.
        seeded_truth = [{"name": "البيك اكسبرس", "price": 25}]
        live = {"البيك اكسبرس": 29}

        captured = []
        with mock.patch.object(msc, "ledger_write", side_effect=lambda h, ev: captured.append((h, ev))):
            with mock.patch.object(msc, "diff_menu", wraps=msc.diff_menu):
                n = msc.emit_proposals("albaik", msc.diff_menu(seeded_truth, live), day_key="2026-06-22")

        self.assertEqual(n, 1)
        self.assertEqual(len(captured), 1)
        handle, ev = captured[0]
        self.assertEqual(handle, "albaik")
        self.assertEqual(ev["type"], "intake_answer")
        self.assertEqual(ev["confirmer"], "menu_sync")
        self.assertIn("PROPOSAL", ev["stamp"])
        self.assertIn("البيك اكسبرس", ev["subject"])

        # THE LAW: truth_pack on disk is byte-identical — a scraper never writes it.
        self.assertEqual(self.tp.read_bytes(), self.before)

    def test_check_with_no_live_source_arms_and_waits(self):
        # fetch_live_menu returns None today → check must arm-and-wait, emit nothing,
        # and never touch truth_pack.
        with mock.patch.object(msc, "ledger_write", side_effect=AssertionError("must not write")):
            deltas = msc.check("albaik", live_menu=None)
        self.assertEqual(deltas, [])
        self.assertEqual(self.tp.read_bytes(), self.before)


if __name__ == "__main__":
    unittest.main()
