#!/usr/bin/env python3
"""Locks B143 — the publish BLOCK (Rule #8) that turns the moonsighting/person FLAG
into a refusal. HUMAN EYES ARE THE VISUAL GATE: a card carrying a REQUIRES-HUMAN-VERIFY
item may publish ONLY if a human recorded all_clear=True (record_tick). Unchecked or
rejected → BLOCK. The sharp case (RABIE's demand): a STALE cached visual_gate must NOT
be trusted — publish_blocked re-derives verify items fresh from the slot, the source of
truth, so a moonsighting land-mine can't slip through a gate attached before B048."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import visual_gate_checklist as vg

HANDLE = "eatjurisha"  # has profile/red_lines.json, state.json, year_map.json

MOON_SLOT = {"occasion": "eid_al_fitr", "date": "2027-03-09", "moonsighting_check": True}


def _moon_card():
    return {"captions": ["لقمة دافية"], "idea": {"scene_ar": "مشهد عيد"},
            "slot": dict(MOON_SLOT)}


def _daily_card():
    return {"captions": ["لقمة دافية"], "idea": {"scene_ar": "مشهد يومي"},
            "slot": {"occasion": "evergreen", "date": "2026-07-01", "moonsighting_check": False}}


class TestVerifyItems(unittest.TestCase):
    def test_moon_card_has_verify_item(self):
        items = vg.verify_items(HANDLE, _moon_card())
        self.assertTrue(any(it["id"] == "moonsighting_recheck" for it in items))

    def test_daily_card_has_none(self):
        self.assertEqual(vg.verify_items(HANDLE, _daily_card()), [])


class TestRecordTick(unittest.TestCase):
    def test_records_who_when_verdict(self):
        card = _moon_card()
        vg.record_tick(card, "mohamed", True, "moon confirmed", now="2026-06-19T07:00:00Z")
        v = card["visual_gate"]["verdict"]
        self.assertEqual(v["checked_by"], "mohamed")
        self.assertEqual(v["date"], "2026-06-19T07:00:00Z")
        self.assertTrue(v["all_clear"])

    def test_refuses_empty_checker(self):
        # human eyes ARE the gate — a tick with no human id is meaningless (the +0.08 scar)
        with self.assertRaises(ValueError):
            vg.record_tick(_moon_card(), "", True)


class TestPublishBlocked(unittest.TestCase):
    def test_unchecked_moon_card_is_blocked(self):
        blocked, reason = vg.publish_blocked(HANDLE, _moon_card())
        self.assertTrue(blocked)
        self.assertIn("moonsighting_recheck", reason)

    def test_human_cleared_unblocks(self):
        card = _moon_card()
        vg.record_tick(card, "mohamed", True, now="2026-06-19T07:00:00Z")
        blocked, reason = vg.publish_blocked(HANDLE, card)
        self.assertFalse(blocked)
        self.assertIn("cleared by mohamed", reason)

    def test_human_rejected_is_blocked(self):
        card = _moon_card()
        vg.record_tick(card, "mohamed", False, now="2026-06-19T07:00:00Z")
        blocked, reason = vg.publish_blocked(HANDLE, card)
        self.assertTrue(blocked)
        self.assertIn("REJECTED", reason)

    def test_daily_card_not_this_gates_call(self):
        blocked, reason = vg.publish_blocked(HANDLE, _daily_card())
        self.assertFalse(blocked)
        self.assertIn("no human-verify", reason)

    def test_stale_cached_gate_does_not_hide_landmine(self):
        """RABIE's demand: a card whose slot says moonsighting_check=true but whose CACHED
        visual_gate (attached before B048) has NO moonsighting item must STILL block. We do
        NOT trust the stale blob — verify items are re-derived fresh from the slot."""
        card = _moon_card()
        # simulate a stale gate: real-looking blob, no moon item, unchecked verdict
        card["visual_gate"] = {"items": [{"id": "faces", "check": "لا وجوه"}],
                               "verdict": {"checked_by": None, "date": None, "all_clear": None}}
        blocked, reason = vg.publish_blocked(HANDLE, card)
        self.assertTrue(blocked, "stale cache must not let a moonsighting card publish")
        self.assertIn("moonsighting_recheck", reason)


class TestPublishGateScript(unittest.TestCase):
    def test_no_publish_marked_card_is_blocked_today(self):
        """The corpus has no publish-marked cards yet → --enforce must be green now
        (and bite the moment one is marked without a tick)."""
        import importlib
        g = importlib.import_module("visual_gate_publish_gate")
        marked, audit, total = g.scan()
        self.assertEqual(marked, [], f"unexpected publish-marked blocked cards: {marked[:3]}")
        self.assertGreater(total, 0)

    def test_marked_moon_card_is_classified_as_hard_block(self):
        import importlib
        g = importlib.import_module("visual_gate_publish_gate")
        card = _moon_card()
        card["status"] = "ready_to_publish"
        self.assertTrue(g.is_publish_marked(card))


if __name__ == "__main__":
    unittest.main()
