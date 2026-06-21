#!/usr/bin/env python3
"""B186d — v3.7 visual_dna free-text cards: the writer→reader wire is whole (Rule #6/#7).

Proves: (1) Mohamed's tap on a v37 card writes his answer into visual_dna.json at the exact
fields the converter reads, flips them GREEN + confirmer=mohamed (on disk); (2) the router
dispatches v37_* free-text to h_v37_visual while the v37_alignment_summary button card still
routes to its own exact handler; (3) openclaw_convert._sf surfaces his confirmed answer to the
render; (4) bridge_drain now finds a consumer, so the 10 held cards can land on his portal."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import apply_rulings
import openclaw_convert
import bridge_drain


def _visual_dna():
    """Minimal v3.7 organ: a colour group, one product (physical + identity fields)."""
    return {
        "schema_version": "brand_visual_dna_v37_v1",
        "brand": {
            "palette": {
                "primary": {"value": "crimson red candidate", "status": "YELLOW",
                            "provenance": {"confirmer": "agent_derived", "confidence": "candidate"}},
                "background_tone": {"value": "warm cream candidate", "status": "YELLOW",
                                    "provenance": {"confirmer": "agent_derived"}},
            },
            "color_field_palette": {"value": "red/gold/cream candidate", "status": "YELLOW",
                                    "provenance": {"confirmer": "agent_derived"}},
        },
        "products": [
            {"name": "جريش",
             "material_finish": {"value": "matte grain candidate", "status": "YELLOW",
                                 "provenance": {"confirmer": "agent_derived"}},
             "material_texture": {"value": "coarse porridge", "status": "YELLOW", "provenance": {}},
             "silhouette_description": {"value": "mounded form", "status": "YELLOW", "provenance": {}},
             "dimensions": {"value": "single-serve cup", "status": "YELLOW", "provenance": {}},
             "identity_dna": {"value": None, "status": "RED",
                              "provenance": {"confirmer": "", "confidence": "experimental"}},
             "label_text_arabic": {"value": "جريش الرياض", "status": "RED", "provenance": {}},
             "label_text_latin": {"value": None, "status": "RED", "provenance": {}}},
        ],
    }


def _staged_cards():
    return {"cards": [
        {"id": "v37_albaik_palette", "handle": "albaik", "group": "colour", "organ": "visual_dna"},
        {"id": "v37_albaik_products_phys", "handle": "albaik", "group": "product_physical", "organ": "visual_dna"},
        {"id": "v37_albaik_identity_ref", "handle": "albaik", "group": "identity_lock", "organ": "visual_dna"},
    ]}


class V37VisualConfirm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        prof = self.base / "clients" / "albaik" / "profile"
        prof.mkdir(parents=True)
        (prof / "visual_dna.json").write_text(json.dumps(_visual_dna(), ensure_ascii=False), encoding="utf-8")
        (self.base / "data").mkdir()
        (self.base / "data" / "v37_confirm_staged.json").write_text(
            json.dumps(_staged_cards(), ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _vd(self):
        return json.loads((self.base / "clients/albaik/profile/visual_dna.json").read_text())

    def test_colour_confirm_flips_palette_green_on_disk(self):
        msg = apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_palette",
                                                     "answer": "#9E1B1B exactly, gold #C9971F"})
        prim = self._vd()["brand"]["palette"]["primary"]
        self.assertEqual(prim["status"], "GREEN")
        self.assertEqual(prim["provenance"]["confirmer"], "mohamed")
        self.assertEqual(prim["client_confirmed"]["answer"], "#9E1B1B exactly, gold #C9971F")
        # all three colour targets stamped
        self.assertEqual(self._vd()["brand"]["color_field_palette"]["status"], "GREEN")
        self.assertEqual(self._vd()["brand"]["palette"]["background_tone"]["status"], "GREEN")
        self.assertIn("albaik", msg)

    def test_product_physical_stamps_every_product(self):
        apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_products_phys",
                                               "answer": "glossy lid, matte cup"})
        prod = self._vd()["products"][0]
        for k in ("material_finish", "material_texture", "silhouette_description", "dimensions"):
            self.assertEqual(prod[k]["status"], "GREEN", k)
            self.assertEqual(prod[k]["client_confirmed"]["answer"], "glossy lid, matte cup")
        # colour group untouched by a physical tap
        self.assertEqual(self._vd()["brand"]["palette"]["primary"]["status"], "YELLOW")

    def test_identity_lock_fills_red_client_only_field(self):
        apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_identity_ref",
                                               "answer": "logo: البيك, ref img attached"})
        idd = self._vd()["products"][0]["identity_dna"]
        self.assertEqual(idd["status"], "GREEN")
        self.assertEqual(idd["client_confirmed"]["answer"], "logo: البيك, ref img attached")

    def test_audit_record_at_organ_top_level(self):
        apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_palette", "answer": "صح"})
        cc = self._vd()["client_confirmed"]["colour"]
        self.assertEqual(cc["answer"], "صح")
        self.assertEqual(cc["confirmer"], "mohamed")
        self.assertGreater(cc["fields_stamped"], 0)

    def test_idempotent_replay(self):
        for _ in range(2):
            apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_palette", "answer": "صح"})
        # a ledger replay must not corrupt — still exactly one confirmation, status GREEN
        self.assertEqual(self._vd()["brand"]["palette"]["primary"]["status"], "GREEN")

    def test_empty_answer_refuses(self):
        with self.assertRaises(RuntimeError):
            apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_palette", "answer": "   "})

    def test_unknown_card_raises(self):
        with self.assertRaises(RuntimeError):
            apply_rulings.h_v37_visual(self.base, {"item_id": "v37_ghost_palette", "answer": "x"})

    def test_router_dispatches_v37_freetext_but_not_the_button_card(self):
        # free-text v37 confirm cards → h_v37_visual (item-prefix, any answer)
        for ans in ("صح", "#9E1B1B", "any free text"):
            self.assertIs(apply_rulings._resolve(("v37_albaik_palette", ans)), apply_rulings.h_v37_visual)
        # the directional button card keeps its own exact handler (resolved before the prefix)
        self.assertIs(apply_rulings._resolve(("v37_alignment_summary", "phoneshoot_batch")),
                      apply_rulings.h_v37_direction)

    def test_converter_surfaces_confirmed_answer(self):
        # before: candidate value, derived source
        before = openclaw_convert._sf(self._vd()["brand"]["palette"]["primary"], "fallback")
        self.assertEqual(before["src"], "derived")
        self.assertNotIn("client-confirmed", before["value"])
        # after his tap: value carries his confirmed truth, source becomes organ
        apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_palette", "answer": "#9E1B1B"})
        after = openclaw_convert._sf(self._vd()["brand"]["palette"]["primary"], "fallback")
        self.assertEqual(after["src"], "organ")
        self.assertIn("#9E1B1B", after["value"])

    def test_converter_uses_answer_when_value_was_empty(self):
        # a RED client-only field (no value) → his answer becomes the value, source organ
        apply_rulings.h_v37_visual(self.base, {"item_id": "v37_albaik_identity_ref",
                                               "answer": "the locked البيك identity"})
        f = openclaw_convert._sf(self._vd()["products"][0]["identity_dna"], "fallback")
        self.assertEqual(f["src"], "organ")
        self.assertEqual(f["value"], "the locked البيك identity")

    def test_bridge_drain_now_finds_a_consumer(self):
        # Rule #7: bridge_drain HELD these cards while no handler resolved. Now one does.
        resolve = bridge_drain._resolver()
        card = {"id": "v37_albaik_palette"}
        self.assertTrue(bridge_drain.consumer_ok(card, resolve))


if __name__ == "__main__":
    unittest.main()
