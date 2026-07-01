#!/usr/bin/env python3
"""B_gate_state tests — the machine-autonomy substrate.

Asserts the load-bearing invariants: computed-from-ledger, FAIL-CLOSED to SAMPLED,
AI-never-auto-advances, MAJOR-occasions-never-relax, and the live produce_batch wire.
"""
import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gate_state


class GateStateReplay(unittest.TestCase):
    def test_family_parse(self):
        self.assertEqual(gate_state._family_of("2027-02-05__occasion → كابتشن"), "occasion")
        self.assertEqual(gate_state._family_of("2027-02-08__ramadan_evergreen → x"), "ramadan_evergreen")
        self.assertIsNone(gate_state._family_of("no-family-token"))
        self.assertIsNone(gate_state._family_of(""))

    def test_approvals_build_clean_batch_but_stay_blocked(self):
        # Five clean approvals PROPOSE full, but active_level must stay BLOCKED — AI never advances.
        fam = gate_state.MAJOR_FAMILIES  # sanity: constant is a set
        self.assertIsInstance(fam, set)
        # Synthesize a ledger via replay on a fake handle by monkeypatching the file read path.
        entries = [{"type": "client_approved", "confirmer": "mohamed",
                    "subject": f"2027-01-0{i}__evergreen → c", "ts": f"2027-01-0{i}"} for i in range(1, 7)]
        out = _replay_synthetic(entries)
        ev = out["evergreen"]
        self.assertEqual(ev["clean_batch"], 6)
        self.assertEqual(ev["proposed_level"], "FULL")      # earned the proposal
        self.assertEqual(ev["active_level"], "BLOCKED")     # but NOT granted — AI never advances

    def test_breach_zeroes_clean_batch(self):
        entries = [
            {"type": "client_approved", "confirmer": "mohamed", "subject": "d__occasion → a", "ts": "1"},
            {"type": "client_approved", "confirmer": "mohamed", "subject": "d__occasion → b", "ts": "2"},
            {"type": "version_verdict", "confirmer": "mohamed", "reason_code": "factual_error",
             "subject": "d__occasion → c", "ts": "3"},
        ]
        occ = _replay_synthetic(entries)["occasion"]
        self.assertEqual(occ["clean_batch"], 0)             # breach reset it
        self.assertEqual(occ["breaches"], 1)
        self.assertEqual(occ["last_breach"]["reason"], "factual_error")

    def test_major_family_never_proposes_full(self):
        entries = [{"type": "client_approved", "confirmer": "mohamed",
                    "subject": f"d{i}__ramadan → c", "ts": str(i)} for i in range(10)]
        ram = _replay_synthetic(entries)["ramadan"]
        self.assertGreaterEqual(ram["clean_batch"], gate_state.CLEAN_BATCH_TO_PROPOSE)
        self.assertTrue(ram["major"])
        self.assertEqual(ram["proposed_level"], "SAMPLED")  # MAJOR never relaxes, even fully clean

    def test_corrupt_ledger_line_pins_proposal_to_sampled(self):
        # A torn line could hide a breach -> never PROPOSE relaxation off a ledger we can't fully read.
        entries = [{"type": "client_approved", "confirmer": "mohamed",
                    "subject": f"d{i}__evergreen → c", "ts": str(i)} for i in range(8)]
        out = _replay_synthetic(entries, corrupt_line="{ this is not json")
        ev = out["evergreen"]
        self.assertGreaterEqual(ev["clean_batch"], gate_state.CLEAN_BATCH_TO_PROPOSE)
        self.assertEqual(ev["ledger_corrupt"], 1)
        self.assertEqual(ev["proposed_level"], "SAMPLED")   # pinned despite a clean-looking count

    def test_non_human_verdicts_ignored(self):
        entries = [{"type": "client_approved", "confirmer": "system",
                    "subject": "d__evergreen → c", "ts": "1"}]
        self.assertEqual(_replay_synthetic(entries), {})    # only mohamed/client move autonomy


class GateModeFailClosed(unittest.TestCase):
    def test_missing_file_is_sampled(self):
        orig = gate_state.GATE_PATH
        try:
            gate_state.GATE_PATH = Path("/nonexistent/gate_state.json")
            self.assertEqual(gate_state.gate_mode("albaik", "evergreen"), "SAMPLED")
            self.assertTrue(gate_state.autonomy_for("albaik", "evergreen")["fail_closed"])
        finally:
            gate_state.GATE_PATH = orig

    def test_major_family_always_sampled_even_if_active_full(self):
        # Even a (hypothetical) human-granted FULL cannot relax a MAJOR occasion.
        doc = {"clients": {"albaik": {"ramadan": {"active_level": "FULL", "major": True}}}}
        _with_doc(self, doc, lambda: self.assertEqual(gate_state.gate_mode("albaik", "ramadan"), "SAMPLED"))

    def test_full_only_when_human_set_active_full(self):
        doc = {"clients": {"albaik": {"evergreen": {"active_level": "FULL", "major": False}}}}
        _with_doc(self, doc, lambda: self.assertEqual(gate_state.gate_mode("albaik", "evergreen"), "FULL"))
        doc2 = {"clients": {"albaik": {"evergreen": {"active_level": "BLOCKED", "major": False}}}}
        _with_doc(self, doc2, lambda: self.assertEqual(gate_state.gate_mode("albaik", "evergreen"), "SAMPLED"))

    def test_empty_family_is_sampled(self):
        self.assertEqual(gate_state.gate_mode("albaik", ""), "SAMPLED")


class LiveWire(unittest.TestCase):
    def test_produce_batch_imports_and_stamps_gate_mode(self):
        # Rule #6: the reader is wired into the real producer, not severed.
        src = (Path(gate_state.BASE) / "scripts/produce_batch.py").read_text(encoding="utf-8")
        self.assertIn("import gate_state", src)
        self.assertIn("gate_state.gate_mode(", src)


def _replay_synthetic(entries, corrupt_line=None):
    """Run gate_state.replay against an in-memory ledger by pointing it at a temp file."""
    import tempfile
    d = tempfile.mkdtemp()
    handle = "synthtest"
    ledir = Path(d) / "clients" / handle / "events"
    ledir.mkdir(parents=True)
    lines = [json.dumps(e, ensure_ascii=False) for e in entries]
    if corrupt_line is not None:
        lines.append(corrupt_line)
    (ledir / "ledger.jsonl").write_text("\n".join(lines), encoding="utf-8")
    orig = gate_state.BASE
    try:
        gate_state.BASE = Path(d)
        return gate_state.replay(handle)
    finally:
        gate_state.BASE = orig


def _with_doc(tc, doc, fn):
    """Temporarily install an in-memory gate_state doc on disk, run fn, restore."""
    import tempfile
    p = Path(tempfile.mkstemp(suffix=".json")[1])
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    orig = gate_state.GATE_PATH
    try:
        gate_state.GATE_PATH = p
        fn()
    finally:
        gate_state.GATE_PATH = orig
        p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
