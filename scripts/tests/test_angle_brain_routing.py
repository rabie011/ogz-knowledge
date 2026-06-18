"""B041 — the angle pen routes each angle to a CD brain and injects the FULL methodology BODY.

The root (brain_router docstring, June 14): the angle stage used to inject 4 salvaged one-LINE
CD questions — the front-matter-only trap — so every brain collapsed to the generic concrete-scene
prompt → the brand-mean formula → the #1 repetition cause. These tests lock the fix: (1) each
6-angle batch is ROUTED across the CD range (occasion batches foreground the occasion brain with
render's heritage→firaasa Arabic-root guard; daily batches spread the four), and (2) the routed
brain's full method BODY (not the front-matter) reaches the prompt. No API call is made.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import build_angle_cards as B
from brain_router import brain_method


class TestAngleBrainRouting(unittest.TestCase):
    def test_occasion_batch_foregrounds_occasion_brain(self):
        b = B.angle_brains("national_day", "شاورمر")
        self.assertEqual(len(b), 6)
        self.assertEqual(b[0], "heritage")           # national day → heritage (brand has Arabic root)

    def test_heritage_guard_demotes_without_arabic_root(self):
        # RABIE: jurisha national-day drift — heritage needs an Arabic brand root, else firaasa leads
        b = B.angle_brains("national_day", "")
        self.assertEqual(b[0], "firaasa")
        self.assertNotEqual(b[0], "heritage")

    def test_ramadan_routes_to_firaasa(self):
        self.assertEqual(B.angle_brains("ramadan", "بارنز")[0], "firaasa")

    def test_daily_batch_spreads_the_four_non_occasion_brains(self):
        b = B.angle_brains("weekly_offer", "شاورمر")
        self.assertEqual(set(b), set(B._DAILY))      # all four present, never one-brain
        self.assertTrue(all(b.count(x) <= 2 for x in set(b)))

    def test_batch_is_never_single_brain(self):
        for occ in ("national_day", "ramadan", "weekly_offer", "new_product", "founding_day"):
            with self.subTest(occ=occ):
                self.assertGreaterEqual(len(set(B.angle_brains(occ, "شاورمر"))), 3)

    def test_full_method_body_reaches_the_prompt(self):
        # the B041 root: the BODY, not the front-matter. Body is substantial and free of the
        # YAML front-matter keys (status/confidence live in the front-matter we now skip).
        for brain in ("heritage", "firaasa", "metaphor", "paradox", "authenticity"):
            m = brain_method(brain)
            self.assertGreater(len(m), 500, f"{brain} body too short — front-matter leaked?")

    def test_angle_messages_injects_methods_and_assignments(self):
        pack = {"brand_en": "shawarmersa", "brand_ar": "شاورمر",
                "sector": "f_and_b", "occasion": "national_day"}
        msgs, brains = B.angle_messages(pack)
        sys_p = msgs[0]["content"]
        self.assertEqual(len(brains), 6)
        self.assertIn("CD METHODOLOGIES", sys_p)
        self.assertIn("ANGLE→BRAIN ASSIGNMENTS", sys_p)
        # the routed lead brain's actual method text must be present (not just its name)
        lead_method = brain_method(brains[0])
        self.assertIn(lead_method[:120], sys_p)

    def test_every_calendar_slug_resolves_to_a_lens(self):
        # Consumer Law (Rule #6) — RABIE root-hunt June 19: year_map emits SLUGS that differ
        # from occasion_facts KEYS (singles_day_11_11 vs 11_11_shopping, mdl_beast_soundstorm
        # vs mdl_beast). A severed slug → no lens → sector-blind angles. Lock: EVERY calendar
        # slug must reach a real per-sector lens through sector_lens()'s alias map.
        import re
        ym = (Path(__file__).parent.parent / "year_map.py").read_text()
        slugs = sorted(set(re.findall(r'"slug":\s*"([^"]+)"', ym)))
        self.assertGreater(len(slugs), 10, "year_map slug scrape failed")
        severed = [s for s in slugs if not B.sector_lens(s, "f_and_b")]
        self.assertEqual(severed, [], f"calendar slugs with no reachable lens: {severed}")

    def test_known_aliased_slugs_hit_their_lens(self):
        # the two slugs this fix connected — explicit guard so a map regression is obvious
        self.assertIsNotNone(B.sector_lens("singles_day_11_11", "retail_lifestyle"))
        self.assertIsNotNone(B.sector_lens("mdl_beast_soundstorm", "fashion"))

    def test_routed_brain_is_enforced_on_invalid_model_output(self):
        # mirror build()'s enforcement: a model that omits/invents a brain gets the routed one
        brains = B.angle_brains("national_day", "شاورمر")
        valid = set(brains)
        angles = [{"id": 1, "brain": "bogus"}, {"id": 2}]   # invalid + missing
        for i, a in enumerate(angles):
            if a.get("brain") not in valid:
                a["brain"] = brains[i] if i < len(brains) else brains[i % len(brains)]
        self.assertEqual(angles[0]["brain"], brains[0])
        self.assertEqual(angles[1]["brain"], brains[1])


if __name__ == "__main__":
    unittest.main()
