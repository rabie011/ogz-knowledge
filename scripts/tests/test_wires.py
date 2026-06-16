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
]


class TestCriticalWires(unittest.TestCase):
    def test_critical_wires_connected(self):
        for fname, consumer in CONNECTED:
            key = fname.split("/")[-1]
            src = (R / consumer).read_text()
            self.assertIn(key, src,
                          f"SEVERED WIRE: {key} is written but {Path(consumer).name} no longer reads it (Rule #6)")

    def test_taste_elo_now_surfaced_to_mohamed(self):
        """taste_elo.json graduated from write-only to CONSUMED (June 16): the portal reads its
        last_pick_feedback to show an instant nudge after each tap. (Steering CREATION from the elo
        is still the separate, gated wire — RABIE's flag — to build once the calibration is real.)"""
        src = (R / "api/portal_mini.py").read_text()
        self.assertIn("taste_elo.json", src, "portal no longer reads taste_elo.json — feedback wire severed")
        self.assertIn("last_pick_feedback", src, "portal reads the file but not the feedback field")


if __name__ == "__main__":
    unittest.main()
