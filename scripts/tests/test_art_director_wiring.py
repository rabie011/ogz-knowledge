"""ART-DIRECTOR WIRING (June 22) — prove the AD stage is consumed by the live producer.

The AD stage itself is proven in test_art_director.py. THIS proves the WIRING:
  • render_client_slot.resolve_visual — the producer's decision from an AD brief:
      clean brief → the AD's deliberate chain becomes the card's pro_chain;
      a cultural BLOCK → HOLD (pro_chain None, Rule #8 — never the mechanical chain on a red line);
      no chain but clean → the mechanical pick is the FALLBACK;
      a reel / no brief → the mechanical chain stands (existing path untouched).
  • render_via_master.resolve_card_chain / card_scene — the renderer READS the AD brief:
      a clean brief's chain + composed_scene REPLACE the mechanical pick + bare scene_ar;
      a refused brief carries pro_chain=None so the render REFUSES (the slot HOLDS);
      a legacy card with no art_brief still resolves via pro_chain (back-compat).
  • END-TO-END: an angle → AD brief → resolve_visual → card → render_via_master, proving the
    producer consumes the AD brief for a photo slot, and that a refused brief holds the slot.

$0 — the AD runs organ-derived (no LLM) or with a stubbed pen; no fal, no real API call.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import art_director as ad
import render_client_slot as rcs
import render_via_master as rvm


# a stubbed pen so the LLM path is exercised at $0 (the real gpt-4o caller is never imported here)
def _fake_pen(messages):
    return ('{"subjects":"modest figure, role only","setting":"home kitchen at dusk",'
            '"props":"the box and a serving tray","composition":"hero centred, honest scale",'
            '"light":"warm low key","mood":"calm, appetite-forward"}')


# a clean photo scene that yields a chosen chain (same fixture the AD stage tests use)
CLEAN = "منتج حقيقي: بوكس البيك على الصينية"
# proven-blocking scenes (test_art_director.py): a named real person / a gym frame on a food brand
BLOCK_PERSON = "الكابتن عادل يقدّم بوكس البيك للعائلة"
BLOCK_GYM = "بوكس البيك في صالة الجيم بعد رفع الأوزان"
# a deliberately bogus mechanical pick — if anything falls back to it, resolve_chain would raise
BOGUS_MECH = {"chain_id_short": "tf99_99_bogus", "name_ar": "x", "family": "TF99"}
REAL_MECH = {"chain_id_short": "tf02_01", "name_ar": "ميكانيكي", "family": "TF02"}


class TestResolveVisualProducer(unittest.TestCase):
    """render_client_slot.resolve_visual — the producer's pro_chain/art_brief/hold decision."""

    def test_clean_brief_uses_the_ad_chain_not_the_mechanical(self):
        brief = ad.art_direct(CLEAN, "albaik", "image")
        self.assertTrue(brief["chain"]["id"], "fixture must yield a chosen chain")
        pro, stored, hold = rcs.resolve_visual(brief, BOGUS_MECH)
        self.assertIsNone(hold)
        self.assertIs(stored, brief)                 # the AD brief is stored on the card
        self.assertEqual(pro["id"], brief["chain"]["id"])   # the AD's chain, NOT the mechanical
        self.assertEqual(pro["family"], brief["chain"]["family"])

    def test_cultural_block_holds_never_falls_back_to_mechanical(self):
        brief = ad.art_direct(BLOCK_PERSON, "albaik", "image")
        self.assertTrue(brief["gate"]["refused"])
        self.assertTrue(brief["gate"]["blocking"])
        pro, stored, hold = rcs.resolve_visual(brief, REAL_MECH)
        self.assertIsNone(pro, "a red-line visual must HOLD (pro_chain None), never the mechanical chain")
        self.assertIs(stored, brief)                 # the refused brief is still stored (gate visible)
        self.assertTrue(hold)                         # a loud reason for the producer log

    def test_no_chain_but_clean_falls_back_to_mechanical(self):
        # a culturally-clean brief that simply produced no chain → the mechanical pick is the FALLBACK
        synthetic = {"kind": "photo_brief", "chain": {"id": None},
                     "gate": {"blocking": [], "refused": True, "reason": "no eligible chain — held"}}
        pro, stored, hold = rcs.resolve_visual(synthetic, REAL_MECH)
        self.assertIsNone(hold)
        self.assertIs(stored, synthetic)
        self.assertEqual(pro, {"id": "tf02_01", "name_ar": "ميكانيكي", "family": "TF02"})

    def test_reel_or_no_brief_keeps_mechanical_untouched(self):
        for brief in (None, ad.art_direct("family: لمة العشا", "albaik", "reel")):
            pro, stored, hold = rcs.resolve_visual(brief, REAL_MECH)
            self.assertEqual(pro["id"], "tf02_01")    # existing path untouched
            self.assertIsNone(stored)                 # no art_brief stored for a reel
            self.assertIsNone(hold)


class TestRenderViaMasterReadsTheBrief(unittest.TestCase):
    """render_via_master — the renderer consumes the AD brief instead of recomputing."""

    def test_resolve_card_chain_prefers_the_ad_chain(self):
        brief = ad.art_direct(CLEAN, "albaik", "image")
        # the pro_chain is deliberately bogus — if resolve_card_chain fell back to it, resolve_chain
        # would raise SystemExit. Reaching a real v3.7 id proves the AD chain was used.
        card = {"handle": "albaik", "visual": {"art_brief": brief, "pro_chain": {"id": "tf99_99_bogus"}}}
        self.assertEqual(rvm.resolve_card_chain(card), ad.oc.resolve_chain(brief["chain"]["id"]))

    def test_card_scene_uses_the_composed_scene(self):
        brief = ad.art_direct(CLEAN, "albaik", "image", llm=_fake_pen)
        card = {"visual": {"art_brief": brief}, "idea": {"scene_ar": "SOMETHING ELSE ENTIRELY"}}
        scene = rvm.card_scene(card)
        self.assertEqual(scene, brief["composed_scene"])         # the DESIGNED photo, not the bare line
        self.assertIn("home kitchen at dusk", scene)             # the pen's setting is woven in
        self.assertNotIn("SOMETHING ELSE ENTIRELY", scene)       # the bare scene_ar is NOT used

    def test_refused_brief_holds_the_render(self):
        brief = ad.art_direct(BLOCK_GYM, "albaik", "image")
        self.assertTrue(brief["gate"]["refused"])
        # the producer set pro_chain=None on a held card → the renderer REFUSES (Rule #8)
        card = {"visual": {"art_brief": brief, "pro_chain": None}}
        with self.assertRaises(SystemExit):
            rvm.resolve_card_chain(card)

    def test_card_scene_falls_back_when_brief_refused(self):
        brief = ad.art_direct(BLOCK_GYM, "albaik", "image")
        card = {"visual": {"art_brief": brief, "pro_chain": None},
                "idea": {"scene_ar": "بوكس البيك على صينية"}}
        scene = rvm.card_scene(card)
        self.assertEqual(scene, "بوكس البيك على صينية")          # the refused composed_scene is NOT used
        self.assertNotIn("الجيم", scene)

    def test_legacy_card_without_art_brief_still_uses_pro_chain(self):
        # back-compat: a card produced before the AD wiring (no art_brief) resolves via pro_chain
        sid = ad.art_direct(CLEAN, "albaik", "image")["chain"]["id"]
        card = {"visual": {"pro_chain": {"id": sid}}}
        self.assertEqual(rvm.resolve_card_chain(card), ad.oc.resolve_chain(sid))

    def test_no_chain_at_all_still_refuses(self):
        with self.assertRaises(SystemExit):
            rvm.resolve_card_chain({"visual": {"pro_chain": None}})


class TestEndToEndProducerConsumesBrief(unittest.TestCase):
    """END-TO-END — an angle → AD brief → resolve_visual → card → render_via_master."""

    def test_photo_slot_producer_consumes_the_ad_brief(self):
        angle_scene = CLEAN
        brief = ad.art_direct(angle_scene, "albaik", "image")
        # producer side: the bogus mechanical proves the AD chain wins
        chain_card, art_brief, hold = rcs.resolve_visual(brief, BOGUS_MECH)
        self.assertIsNone(hold)
        card = {"handle": "albaik", "idea": {"scene_ar": angle_scene},
                "visual": {"phone_shoot_card": [], "pro_chain": chain_card, "art_brief": art_brief}}
        # renderer side: it consumes the AD's chain + composed scene
        self.assertEqual(rvm.resolve_card_chain(card), ad.oc.resolve_chain(brief["chain"]["id"]))
        self.assertEqual(rvm.card_scene(card), brief["composed_scene"])

    def test_refused_photo_slot_holds_end_to_end(self):
        brief = ad.art_direct(BLOCK_GYM, "albaik", "image")
        chain_card, art_brief, hold = rcs.resolve_visual(brief, REAL_MECH)
        self.assertIsNone(chain_card)            # producer HELD (no chain on the card)
        self.assertTrue(hold)
        card = {"handle": "albaik", "visual": {"pro_chain": chain_card, "art_brief": art_brief}}
        with self.assertRaises(SystemExit):       # renderer REFUSES — the slot holds
            rvm.resolve_card_chain(card)


if __name__ == "__main__":
    unittest.main()
