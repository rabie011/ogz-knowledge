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
]


class TestCriticalWires(unittest.TestCase):
    def test_critical_wires_connected(self):
        for fname, consumer in CONNECTED:
            key = fname.split("/")[-1]
            src = (R / consumer).read_text()
            self.assertIn(key, src,
                          f"SEVERED WIRE: {key} is written but {Path(consumer).name} no longer reads it (Rule #6)")

    def test_taste_elo_consumer_is_tracked(self):
        """taste_elo.json has NO creation-consumer yet (RABIE's flag: elo must change the next
        batch or it's a dashboard). This test documents the known-pending wire — when the
        elo→creation wire is built post-calibration, add it to CONNECTED and this stays a marker."""
        self.assertTrue((R / "scripts/taste_elo.py").exists(), "taste_elo producer missing")


if __name__ == "__main__":
    unittest.main()
