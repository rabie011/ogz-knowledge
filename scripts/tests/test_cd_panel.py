"""W1/W3 (June 23) — the 5 CD brains RUN as a multi-model panel and feed the produce path.

The brainstorm found only the CEO actually ran; the 5 CD brains were applied one-at-a-time on
ONE model. cd_panel.run_panel makes them a PANEL: route the slot to its CD-brain spread, build
the SAME concrete-scene prompt per brain, run each brain on a DIFFERENT model (GPT/Gemini/Groq),
return the lead brain's angle with the rivals attached. These tests lock the WIRE with zero
network: the model dispatch (`ask`) and the prompt builder are injected, so we exercise the real
routing, model-spread, dead-model fallback, and never-stuck contract deterministically.

Laws under test:
- Rule #8 / never-stuck: a dead model FALLS BACK to a live one (never blocks); all-dead → None
  so make_angle uses its single-pen path (the pipeline never stalls on the minds).
- "the minds on DIFFERENT models": brains are spread across the model ring, not all on one model.
- W3: the lead brain's angle is returned with `panel_alts` (rivals) so the producer is seeded by
  the minds, not by a single mechanical pen.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import cd_panel


def _fake_prompt(client, slot, sector, brain=None):
    # pure stand-in for render_client_slot.angle_prompt — returns (sys_p, user, brain) with NO
    # heavy imports / organ reads. The Arabic-root guard etc. is tested in test_angle_brain_routing;
    # here we only verify the panel machinery, so the prompt content is a marker.
    return (f"SYS::{brain}", f"USER::{brain}::{slot.get('date','')}", brain)


def _scene(brain, model):
    return json.dumps({"scene_ar": f"مشهد {brain}", "why_it_lands": f"{brain} lands",
                       "post_type": "moment"}, ensure_ascii=False)


class TestCdPanel(unittest.TestCase):
    CLIENT = {"brand_ar": "بارنز"}
    SLOT = {"occasion": "ramadan", "date": "2026-03-10", "sector": "f_and_b"}

    def test_panel_returns_lead_angle_with_rivals(self):
        # every model answers — the lead brain's angle is returned with the rivals as panel_alts
        seen = []

        def ask(model, sys_p, user):
            seen.append((model, sys_p))
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  ask=ask, prompt_builder=_fake_prompt)
        self.assertIsNotNone(lead)
        # ramadan leads with authenticity (route_decision YAML), so the lead angle is authenticity's
        self.assertEqual(lead["brain"], "authenticity")
        self.assertTrue(lead["scene_ar"])
        # rivals are present → the producer is SEEDED by the other minds (W3)
        self.assertGreaterEqual(len(lead["panel_alts"]), 1)
        self.assertEqual(len(lead["panel_brains"]), 1 + len(lead["panel_alts"]))

    def test_minds_run_on_different_models(self):
        # the brains are spread across the model ring — not all funneled to one model
        def ask(model, sys_p, user):
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  ask=ask, prompt_builder=_fake_prompt)
        self.assertGreaterEqual(len(set(lead["panel_models"])), 2,
                                "the minds must run on DIFFERENT models, not one")

    def test_dead_model_falls_back_never_blocks(self):
        # gpt is dead (consult returns an '(... error ...)' string with no JSON); the brain must
        # fall back to the next live model in the ring — never drop the angle, never raise (Rule #8)
        def ask(model, sys_p, user):
            if model == "gpt":
                return "(gpt error: AuthError: invalid key)"
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  ask=ask, prompt_builder=_fake_prompt)
        self.assertIsNotNone(lead)
        self.assertNotIn("gpt", lead["panel_models"])   # gpt was dead → never used
        self.assertTrue(lead["scene_ar"])

    def test_all_models_dead_returns_none(self):
        # every model dead → run_panel returns None so make_angle uses its single-pen path.
        # The pipeline is NEVER stuck on the minds.
        def ask(model, sys_p, user):
            return f"(no {model.upper()}_API_KEY)"

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  ask=ask, prompt_builder=_fake_prompt)
        self.assertIsNone(lead)

    def test_lead_brain_override_foregrounds_routed_primary(self):
        # when the caller already routed a brain (render's route_decision), it leads the panel
        def ask(model, sys_p, user):
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  lead_brain="paradox", ask=ask, prompt_builder=_fake_prompt)
        self.assertEqual(lead["brain"], "paradox")

    def test_explicit_brains_run_each_distinct_methodology(self):
        # given an explicit brain list, each runs once (a 5-mind panel = 5 different methods)
        def ask(model, sys_p, user):
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b", ask=ask,
                                  prompt_builder=_fake_prompt,
                                  brains=["firaasa", "metaphor", "paradox"])
        self.assertEqual(lead["panel_brains"], ["firaasa", "metaphor", "paradox"])

    def test_empty_json_reply_is_not_a_valid_angle(self):
        # a model that returns a degenerate '{}' (observed live from gemini on a trivial prompt)
        # must NOT count as an angle — the brain falls over to the next model with real content.
        def ask(model, sys_p, user):
            if model == "gpt":
                return "{}"            # empty object — no scene
            brain = sys_p.split("::", 1)[1]
            return _scene(brain, model)

        lead = cd_panel.run_panel(self.CLIENT, self.SLOT, "f_and_b",
                                  ask=ask, prompt_builder=_fake_prompt)
        self.assertIsNotNone(lead)
        self.assertTrue(lead["scene_ar"])     # every returned angle has a real scene
        self.assertNotIn("gpt", lead["panel_models"])

    def test_consult_panel_is_the_model_wire(self):
        # the default dispatch is consult.py's _PANEL (RABIE=GPT + the minds on Gemini/Groq).
        # Confirm the ring maps onto consult's helpers (the multi-model wire is real, not invented).
        import consult
        for m in cd_panel.MODEL_RING:
            self.assertIn(m, consult._PANEL)


if __name__ == "__main__":
    unittest.main()
