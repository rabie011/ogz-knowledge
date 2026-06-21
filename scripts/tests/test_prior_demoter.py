#!/usr/bin/env python3
"""Guards the PRIOR DEMOTER (B098) — the inverse of B096 that keeps sector priors ALIVE. All on
synthetic fixtures (no live data). The contracts that matter: (1) Rule #8 gate — 3 distinct
consecutive confirmed overrides demote, 2 HOLD; (2) Rule #9 no-inflation — one brand overriding 3×
is still ONE brand → no demotion; (3) a confirmed `accept` BREAKS the streak; (4) unconfirmed events
are dropped (neither extend nor break); (5) a prior already at the floor is never demoted; (6) the
draft anonymizes brands and demotes to `experimental`; (7) Rule #6 — staged draft reads back."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import prior_demoter as pd


def _prior(value="left_hand", confidence="confirmed", sector="f_and_b", field="serving_etiquette"):
    return {"sector": sector, "field": field, "value": value, "confidence": confidence}


def _ov(brand, action="override", value="left_hand", confirmer="mohamed",
        sector="f_and_b", field="serving_etiquette"):
    return {"brand": brand, "action": action, "value": value, "confirmer": confirmer,
            "sector": sector, "field": field}


class TestPriorDemoter(unittest.TestCase):
    def test_three_distinct_consecutive_overrides_demote(self):
        events = [_ov("a"), _ov("b"), _ov("c")]
        d = pd.demote(_prior(), events)
        self.assertIsNotNone(d)
        self.assertEqual(d["n_overrides"], 3)
        self.assertEqual(d["to_confidence"], "experimental")
        self.assertEqual(d["from_confidence"], "confirmed")
        self.assertEqual(d["status"], "PROVISIONAL")

    def test_two_overrides_held_below_floor(self):
        events = [_ov("a"), _ov("b")]
        self.assertIsNone(pd.demote(_prior(), events))          # Rule #8 — the gate bites

    def test_one_brand_repeated_does_not_inflate(self):
        # same brand overriding the prior three times is still ONE brand (Rule #9, fresh-batch scar)
        events = [_ov("a"), _ov("a"), _ov("a")]
        self.assertIsNone(pd.demote(_prior(), events))
        self.assertEqual(pd.consecutive_override_brands(events), ["a"])

    def test_confirmed_accept_breaks_the_streak(self):
        # a, b override; c ACCEPTS (resets); d, e override → trailing run is only d,e (2) → HOLD
        events = [_ov("a"), _ov("b"), _ov("c", action="accept"), _ov("d"), _ov("e")]
        self.assertIsNone(pd.demote(_prior(), events))
        self.assertEqual(pd.consecutive_override_brands(events), ["d", "e"])

    def test_accept_then_three_fresh_overrides_demote(self):
        # an early accept is forgotten once 3 fresh distinct overrides follow it
        events = [_ov("a", action="accept"), _ov("b"), _ov("c"), _ov("d")]
        d = pd.demote(_prior(), events)
        self.assertIsNotNone(d)
        self.assertEqual(d["n_overrides"], 3)

    def test_unconfirmed_events_are_dropped(self):
        # 2 confirmed + 1 machine-guessed override → only 2 count → HELD; the unconfirmed one
        # neither extends NOR breaks the run
        events = [_ov("a"), _ov("b"), _ov("c", confirmer="machine")]
        self.assertIsNone(pd.demote(_prior(), events))
        self.assertEqual(pd.consecutive_override_brands(events), ["a", "b"])

    def test_prior_already_at_floor_never_demoted(self):
        events = [_ov("a"), _ov("b"), _ov("c")]
        self.assertIsNone(pd.demote(_prior(confidence="experimental"), events))

    def test_anonymization_hides_brand(self):
        events = [_ov("albaik"), _ov("jurisha"), _ov("kudu")]
        d = pd.demote(_prior(), events)
        blob = json.dumps(d, ensure_ascii=False)
        for raw in ("albaik", "jurisha", "kudu"):
            self.assertNotIn(raw, blob)                         # no raw brand leaks
        self.assertTrue(all(t.startswith("b_") for t in d["brands_anon"]))

    def test_no_events_holds(self):
        self.assertIsNone(pd.demote(_prior(), []))

    def test_demote_all_keys_events_to_their_prior(self):
        priors = [_prior(value="left_hand"), _prior(value="no_music", field="ambience")]
        events_by_key = {
            ("f_and_b", "serving_etiquette", "left_hand"): [_ov("a"), _ov("b"), _ov("c")],
            ("f_and_b", "ambience", "no_music"): [_ov("a", value="no_music", field="ambience")],
        }
        drafts = pd.demote_all(priors, events_by_key)
        self.assertEqual(len(drafts), 1)                        # only the left_hand prior demotes
        self.assertEqual(drafts[0]["value"], "left_hand")

    def test_write_and_read_back_end_to_end(self):
        # Rule #6 — the writer's output is a real consumable artifact
        priors = [_prior()]
        events_by_key = {("f_and_b", "serving_etiquette", "left_hand"): [_ov("a"), _ov("b"), _ov("c")]}
        drafts = pd.demote_all(priors, events_by_key)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "demotions.json"
            pd.write_demotions(drafts, path=p)
            back = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(back["n_demotions"], 1)
        self.assertEqual(back["threshold"], pd.DEMOTE_THRESHOLD)
        self.assertEqual(back["demotions"][0]["to_confidence"], "experimental")

    def test_loaders_are_safe_and_honest(self):
        # the real loaders never crash and (on a pilot with no events/priors) yield empty
        self.assertIsInstance(pd.load_events(), dict)
        self.assertIsInstance(pd.load_priors(), list)
        # end-to-end on real (empty) sources → no demotions, no crash
        self.assertEqual(pd.demote_all(pd.load_priors(), pd.load_events()), [])


if __name__ == "__main__":
    unittest.main()
