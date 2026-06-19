#!/usr/bin/env python3
"""B121 — orphaned-send / events-integrity audit (verify_events_wired.audit).

Locks the four DANGEROUS classes that must REFUSE shipping (Rule #8), and proves legacy schema
gaps stay non-blocking WARNs (no false alarms on the documented pre-schema line). Also asserts
the real live ledgers pass with zero ERRORs so this guard does not break the ship gate."""
import json, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import verify_events_wired as V  # noqa: E402


def _write_ledger(root, client, events):
    d = Path(root) / "clients" / client / "events"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "ledger.jsonl", "w", encoding="utf-8") as fh:
        for e in events:
            fh.write((e if isinstance(e, str) else json.dumps(e, ensure_ascii=False)) + "\n")


def _errs(findings):
    return [f for f in findings if f[0] == "ERROR"]


def _warns(findings):
    return [f for f in findings if f[0] == "WARN"]


GOOD = {"ts": "2026-06-12", "type": "voice_rating", "subject": "v_A",
        "rating": 5, "confirmer": "rabie_provisional", "stamp": "PROVISIONAL — pending Mohamed"}


class TestEventsWired(unittest.TestCase):
    def _audit(self, events):
        with tempfile.TemporaryDirectory() as tmp:
            _write_ledger(tmp, "acme", events)
            return V.audit(repo=tmp)

    def test_clean_ledger_passes(self):
        f, s = self._audit([GOOD,
            {"ts": "2026-06-12", "type": "pick_selected", "subject": "x→y", "line": "the line",
             "confirmer": "mohamed", "stamp": "CONFIRMED BY MOHAMED (decision portal)"}])
        self.assertEqual(_errs(f), [], f"clean ledger should not error: {f}")
        self.assertEqual(s["picks"], 1)
        self.assertEqual(s["mohamed_terminals"], 1)

    def test_unparseable_line_errors(self):
        f, _ = self._audit([GOOD, "{not valid json,,,"])
        self.assertTrue(any("unparseable" in m for _, _, _, m in _errs(f)))

    def test_mohamed_not_confirmed_errors(self):
        # his decision left on a PROVISIONAL stamp = revertible/lost tap
        f, _ = self._audit([{"ts": "2026-06-12", "type": "red_line_added", "subject": "z",
                             "confirmer": "mohamed", "stamp": "PROVISIONAL — pending Mohamed"}])
        self.assertTrue(any("not CONFIRMED-stamped" in m for _, _, _, m in _errs(f)))

    def test_pick_selected_selecting_nothing_errors(self):
        f, _ = self._audit([{"ts": "2026-06-12", "type": "pick_selected",
                             "confirmer": "mohamed", "stamp": "CONFIRMED BY MOHAMED"}])
        self.assertTrue(any("selected nothing" in m for _, _, _, m in _errs(f)))

    def test_orphaned_send_errors(self):
        # a send with no terminal event resolving its id = severed wire
        f, s = self._audit([
            {"ts": "2026-06-12", "type": "send", "send_id": "card_42",
             "confirmer": "claude", "stamp": "PROVISIONAL"}])
        self.assertEqual(s["orphans"], 1)
        self.assertTrue(any("orphaned send" in m for _, _, _, m in _errs(f)))

    def test_resolved_send_passes(self):
        # same send, but a later terminal event resolves it → no orphan
        f, s = self._audit([
            {"ts": "2026-06-12", "type": "send", "send_id": "card_42",
             "confirmer": "claude", "stamp": "PROVISIONAL"},
            {"ts": "2026-06-13", "type": "pick_selected", "subject": "x", "line": "L",
             "resolves": "card_42", "confirmer": "mohamed", "stamp": "CONFIRMED"}])
        self.assertEqual(s["orphans"], 0)
        self.assertEqual(_errs(f), [])

    def test_send_without_id_errors(self):
        f, _ = self._audit([{"ts": "2026-06-12", "type": "send",
                             "confirmer": "claude", "stamp": "PROVISIONAL"}])
        self.assertTrue(any("no send_id" in m for _, _, _, m in _errs(f)))

    def test_legacy_missing_field_is_warn_not_error(self):
        # the documented pre-schema line shape (no confirmer) must NOT block shipping
        f, _ = self._audit([{"ts": "2026-06-11", "type": "competitor_reference",
                             "competitor": "x", "stamp": "PROVISIONAL — pending Mohamed"}])
        self.assertEqual(_errs(f), [], "legacy missing-field must be WARN, not ERROR")
        self.assertTrue(any("missing required field 'confirmer'" in m for _, _, _, m in _warns(f)))

    def test_live_ledgers_have_zero_errors(self):
        """Guard must not break the real ship gate: live clients/*/events pass with 0 ERRORs."""
        f, s = V.audit()  # default REPO
        self.assertGreaterEqual(s["ledgers"], 3)
        self.assertEqual(_errs(f), [], f"live ledgers must be ERROR-free: {_errs(f)}")


if __name__ == "__main__":
    unittest.main()
