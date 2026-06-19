#!/usr/bin/env python3
"""Consumer-Law guard (Rule #6, June 15): the CRITICAL pipeline wires must stay connected — a
producer's output file MUST be read by its named consumer. Born from the severed pairwise wire
(picks written to one file, read from another — every live tap would have been lost). Locks the
wires that matter so none can silently sever again."""
import unittest
from pathlib import Path

R = Path(__file__).parent.parent.parent
# (producer→) output-file basename → consumer script that MUST read it
CONNECTED = [
    ("data/pairwise_prefs.jsonl", "scripts/taste_elo.py"),       # picks → Mohamed-Elo
    ("mohamed_answers.jsonl",     "scripts/pairwise.py"),        # portal taps → consume
    ("strategy_brief.json",       "scripts/render_client_slot.py"),  # CEO strategy → the brains
    ("learned_gate_rules.json",   "scripts/pre_ship_gate.py"),   # his rulings → the gate
    ("taste_elo.json",            "api/portal_mini.py"),         # Mohamed-Elo → instant tap feedback (June 16)
    ("founder_taste.json",        "scripts/render_client_slot.py"),  # his taste law → the producing pen (June 18)
    ("verify_events_wired.py",    "scripts/verify_ship_ready.py"),   # orphaned-send audit → the ship gate (B121, June 19)
]


class TestCriticalWires(unittest.TestCase):
    def test_critical_wires_connected(self):
        for fname, consumer in CONNECTED:
            key = fname.split("/")[-1]
            src = (R / consumer).read_text()
            self.assertIn(key, src,
                          f"SEVERED WIRE: {key} is written but {Path(consumer).name} no longer reads it (Rule #6)")

    def test_founder_taste_reaches_the_producing_pen(self):
        """STRONGER than the basename check (June 18): render_client_slot.py LOADED founder_taste.json
        and threw the variable away — a dead read that the CONNECTED basename test would pass while his
        taste law never reached the pen. This asserts the load is actually CONSUMED: the founder kills/
        rewards are built into `taste_clause` AND that clause is concatenated into the `sys_p` prompt."""
        src = (R / "scripts/render_client_slot.py").read_text()
        self.assertIn("taste_clause", src, "founder taste no longer woven into a clause (dead read returned)")
        self.assertRegex(src, r'taste\.get\(\s*["\']kills',
                         msg="taste_clause not built from founder_taste kills")
        # the clause must actually be concatenated INTO the caption pen's prompt (the renderer has
        # two sys_p blocks — the angle generator and the caption pen; the taste law belongs in the
        # pen that writes the caption). Anchor on the concatenation, not a fragile block index.
        self.assertIn("taste_clause +", src,
                      "taste_clause built but NOT concatenated into the pen's sys_p (Rule #6 — dead read)")

    def test_taste_clause_has_measurement_toggle(self):
        """The eyes-test instrument (taste_clause_ab.py, June 18) needs to render the pen WITHOUT his
        law as the 'before' arm. The OGZ_TASTE_OFF toggle must stay wired (default OFF = law ON, zero
        production change) so connected-vs-better can be re-measured any time without editing the pen."""
        src = (R / "scripts/render_client_slot.py").read_text()
        self.assertIn("OGZ_TASTE_OFF", src, "measurement toggle removed — can't run the before/after eyes-test")
        # the toggle must BLANK the clause (the 'before' arm), not just exist as a dead string
        self.assertRegex(src, r'OGZ_TASTE_OFF.*?\n\s*taste_clause\s*=\s*""',
                         msg="OGZ_TASTE_OFF present but does not blank taste_clause")
        self.assertTrue((R / "scripts/taste_clause_ab.py").exists(),
                        "the A/B eyes-test harness is gone")

    def test_taste_elo_now_surfaced_to_mohamed(self):
        """taste_elo.json graduated from write-only to CONSUMED (June 16): the portal reads its
        last_pick_feedback to show an instant nudge after each tap. (Steering CREATION from the elo
        is still the separate, gated wire — RABIE's flag — to build once the calibration is real.)"""
        src = (R / "api/portal_mini.py").read_text()
        self.assertIn("taste_elo.json", src, "portal no longer reads taste_elo.json — feedback wire severed")
        self.assertIn("last_pick_feedback", src, "portal reads the file but not the feedback field")


if __name__ == "__main__":
    unittest.main()
