"""THE ART-DIRECTOR — the missing VISUAL mind (June 22).

Proves the FIRST version of the Art-Director stage (scripts/art_director.py):
  A1 — art_direct(idea, handle, fmt) writes a STRUCTURED photo brief from the organs
       (chosen chain + a WHY, persona, scene staging, composition, light, mood, modesty).
  A2 — the brief feeds openclaw_convert (to_converter_args → the AD's chain + composed
       scene REPLACE the mechanical pick); a refused/reel brief yields no converter args
       (Rule #6 the writer has a reader; Rule #8 a refused brief never reaches the renderer).
  A3 — the brief is GATED against the client's CONFIRMED organs via the EXISTING cultural
       gate (client_rules.violations): a red-line brief (named real person, gym-on-food,
       dine-in-on-cloud-kitchen) is REFUSED.
  A4 — the persona/reference choice is MODEL-AGNOSTIC: a text description + which reference
       image (per the brand_visual_dna_v37 schema), never a model-locked id.
  Format-aware: a reel routes to reel_brief (the photo path is skipped, never broken).
  Consumes the existing engines: openclaw_convert (derive_visual_dna/pick_reference/
  resolve_chain) + client_rules.violations + render_client_slot.pick_pro_chain.

The LLM is STUBBED ($0) — the deterministic organ spine is asserted directly; an injected
fake pen proves the LLM path is wired without spending. No fal, no real API call.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import art_director as ad


# A fake pen so the LLM path is exercised at $0 (the real gpt-4o caller is NEVER imported here).
def _fake_pen(messages):
    # the AD pen contract: return a JSON object with the six design fields
    return ('{"subjects":"modest figure, role only","setting":"home kitchen at dusk",'
            '"props":"the box and a serving tray","composition":"hero centred, honest scale",'
            '"light":"warm low key","mood":"calm, appetite-forward"}')


class TestArtDirectorWritesBrief(unittest.TestCase):
    """A1 — the AD writes a STRUCTURED photo brief from a fixture idea + the real organs."""

    def test_photo_brief_is_structured_and_organ_sourced(self):
        b = ad.art_direct("family: الأخ الأكبر يجهّز بوكس البيك للعشا", "albaik", "image")
        self.assertEqual(b["kind"], "photo_brief")
        # the deliberate DESIGN fields all present (a brief, not a bare scene)
        for k in ("chain", "persona", "design", "modesty", "composed_scene", "brand_visual", "product"):
            self.assertIn(k, b, f"brief missing {k}")
        d = b["design"]
        for k in ("setting", "subjects", "props", "composition", "light", "mood"):
            self.assertTrue(d.get(k), f"design missing {k}")
        # the chain carries a WHY (the deliberate decision, not a mechanical pick)
        self.assertTrue(b["chain"].get("reason"))
        self.assertTrue(b["chain"].get("id"), "no chain chosen for a renderable scene")
        # organ-sourced: the product name came from visual_dna (Rule #12 — from organs)
        self.assertTrue(b["product"].get("name"))

    def test_human_scene_gets_a_lifestyle_chain_not_a_product_splash(self):
        # consumes render_client_slot's human-presence detector + no-humans veto
        import render_client_slot as rcs
        b = ad.art_direct("family: الأخ الأكبر يجهّز العشا والأم تدخل المطبخ", "albaik", "image")
        self.assertTrue(b["human_present"])
        # the chosen chain must NOT be a no-humans product family (TF01/02/03/11/12/14)
        self.assertNotIn(b["chain"].get("family"), rcs._NO_HUMANS_FAMILIES)

    def test_llm_path_is_wired_with_a_stub_zero_spend(self):
        # the injected fake pen proves the LLM path runs without spending (Prove = real, tests = stub)
        b = ad.art_direct("منتج حقيقي: بوكس البيك على صينية", "albaik", "image", llm=_fake_pen)
        self.assertEqual(b["design"].get("_source"), "llm")
        self.assertEqual(b["design"].get("setting"), "home kitchen at dusk")

    def test_organ_derived_pen_needs_no_llm(self):
        # default (no llm) → a real brief from organs alone ($0, pen dark)
        b = ad.art_direct("منتج حقيقي: بوكس البيك", "albaik", "image")
        self.assertEqual(b["design"].get("_source"), "organ_derived")


class TestArtDirectorFormatAware(unittest.TestCase):
    """Directive 1 — a photo gets a photo brief; a reel routes to the reel path (not broken)."""

    def test_reel_routes_to_reel_brief_not_photo(self):
        b = ad.art_direct("family: لمة العشا", "albaik", "reel")
        self.assertEqual(b["kind"], "reel_brief")
        self.assertNotIn("design", b)

    def test_image_and_unknown_format_take_the_photo_path(self):
        for fmt in ("image", "photo", "carousel", ""):
            b = ad.art_direct("منتج حقيقي: بوكس البيك", "albaik", fmt)
            self.assertEqual(b["kind"], "photo_brief", f"fmt={fmt!r} should be a photo brief")

    def test_is_photo_helper(self):
        self.assertTrue(ad.is_photo("image"))
        self.assertTrue(ad.is_photo(""))          # default → photo (dominant year-map format)
        self.assertFalse(ad.is_photo("reel"))
        self.assertFalse(ad.is_photo("video"))


class TestArtDirectorGated(unittest.TestCase):
    """A3 — the brief is checked against the client's CONFIRMED organs (the cultural gate).
    A red-line brief is REFUSED (Rule #8). Reuses client_rules.violations — never re-regexes."""

    def test_named_real_person_is_refused(self):
        # real_person_mentions=off (albaik organ) → a named captain in the scene is refused
        b = ad.art_direct("الكابتن عادل يقدّم بوكس البيك للعائلة", "albaik", "image")
        self.assertTrue(b["gate"]["refused"])
        kinds = {v[0] for v in b["gate"]["violations"]}
        self.assertIn("real_person", kinds)

    def test_gym_frame_on_food_brand_is_refused(self):
        # cross-brand bleed: a food brand wearing a gym SETTING (RABIE's albaik-as-gym-reward scar)
        b = ad.art_direct("بوكس البيك في صالة الجيم بعد رفع الأوزان", "albaik", "image")
        self.assertTrue(b["gate"]["refused"])
        kinds = {v[0] for v in b["gate"]["violations"]}
        self.assertIn("cross_brand", kinds)

    def test_clean_scene_passes_the_gate(self):
        b = ad.art_direct("منتج حقيقي: بوكس البيك على صينية المجلس", "albaik", "image")
        self.assertFalse(b["gate"]["refused"], f"clean scene wrongly refused: {b['gate']}")
        self.assertEqual(b["gate"]["reason"], "clean")

    def test_gate_reuses_the_existing_engine(self):
        # A3 — gate_brief delegates to client_rules.violations (no parallel red-line regexes here)
        b = {"kind": "photo_brief", "handle": "albaik",
             "idea": "الكابتن سعود يقدّم الطعام", "modesty": "",
             "design": {"setting": "", "subjects": "", "props": "",
                        "composition": "", "light": "", "mood": ""},
             "persona": {"text": ""}}
        viols = ad.gate_brief(b, "albaik")
        self.assertTrue(any(v[0] == "real_person" for v in viols))


class TestArtDirectorModelAgnosticPersona(unittest.TestCase):
    """A4 — the persona/reference is text + a reference-pack (v37 schema), never a model id."""

    def test_persona_is_text_plus_reference_image(self):
        b = ad.art_direct("family: الأم تجهّز بوكس البيك للعشا", "albaik", "image")
        p = b["persona"]
        self.assertTrue(p.get("_model_agnostic"))
        self.assertIsInstance(p.get("text"), str)
        self.assertTrue(p["text"])
        # the reference is a PATH (a real photo per the v37 schema), never a model-locked id
        ref = p.get("reference_image")
        if ref is not None:
            self.assertIsInstance(ref, str)
            self.assertNotRegex(ref, r"^(flux|seed|gen)[-_]")  # not a model artifact
        # modesty is ALWAYS baked into the brief text; the persona text carries the modest-figure
        # clause only when a human is present (a product-only persona needs no figure clause)
        self.assertIn("MODESTY", b["modesty"])
        if p.get("human_present"):
            self.assertIn("modest", p["text"].lower())

    def test_reference_is_a_confirmed_clean_product_shot(self):
        # consumes openclaw_convert.pick_reference (NEVER a person/royal portrait)
        b = ad.art_direct("منتج حقيقي: بوكس البيك", "albaik", "image")
        ref = b["persona"].get("reference_image")
        # pick_reference returns a media path under the client (or None); never a face id
        if ref:
            self.assertIn("clients/albaik", ref)


class TestArtDirectorFeedsConverter(unittest.TestCase):
    """A2 — the brief feeds openclaw_convert (Rule #6 the writer has a reader)."""

    def test_clean_brief_yields_converter_args(self):
        b = ad.art_direct("منتج حقيقي: بوكس البيك على الصينية", "albaik", "image")
        args = ad.to_converter_args(b)
        self.assertIsNotNone(args, "a clean brief must produce converter args")
        # the AD's CHOSEN chain + COMPOSED scene REPLACE the mechanical pick
        self.assertTrue(args["chain"])              # a resolved v3.7 id
        self.assertIn("composed_scene", b)          # the brief carries the composed scene
        self.assertTrue(args["scene"])
        self.assertIn(b["idea"], args["scene"])     # the idea is woven into the composed scene
        self.assertEqual(args["handle"], "albaik")

    def test_converter_args_resolve_to_a_real_v37_chain(self):
        # A2/Rule #6 end-to-end: the chain id the AD chose resolves through openclaw_convert
        b = ad.art_direct("منتج حقيقي: بوكس البيك", "albaik", "image")
        args = ad.to_converter_args(b)
        if args:  # clean brief
            # resolve_chain accepts the SHORT id and returns a v3.7 id without raising
            self.assertTrue(ad.oc.resolve_chain(b["chain"]["id"]))

    def test_refused_brief_has_no_reader(self):
        # Rule #8 — a refused brief never reaches the renderer
        b = ad.art_direct("الكابتن عادل في صالة الجيم", "albaik", "image")
        self.assertTrue(b["gate"]["refused"])
        self.assertIsNone(ad.to_converter_args(b))

    def test_reel_brief_has_no_converter_args(self):
        b = ad.art_direct("family: لمة العشا", "albaik", "reel")
        self.assertIsNone(ad.to_converter_args(b))


class TestArtDirectorConsumesEngines(unittest.TestCase):
    """The AD greenfields nothing — it imports and uses the existing engines."""

    def test_imports_the_existing_engines(self):
        import openclaw_convert
        import client_rules
        self.assertIs(ad.oc, openclaw_convert)
        self.assertIs(ad.cr, client_rules)

    def test_composed_scene_carries_the_designed_staging(self):
        # the converter scene is the DESIGNED photo (idea + setting + light + mood), not bare idea
        b = ad.art_direct("منتج حقيقي: بوكس البيك", "albaik", "image", llm=_fake_pen)
        self.assertIn("home kitchen at dusk", b["composed_scene"])   # the pen's setting is woven in
        self.assertIn(b["idea"], b["composed_scene"])


if __name__ == "__main__":
    unittest.main()
