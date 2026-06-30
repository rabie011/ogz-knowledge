#!/usr/bin/env python3
"""B149 — the PAYMENT row of fingerprint_status. The commercial pulse must be INDEPENDENT
of approval activity: a client who keeps approving content but stopped paying must show RED
even while the approval rows stay green. RED on invoice-past-due / payment-late / renewal-
lapsed; GREEN when a payment is on record and clean; YELLOW for a pre-commercial pilot.
Append-only: the most recent payment-relevant event is the live state.
"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from fingerprint_status import payment_status, G, Y, R  # noqa: E402


class TestPaymentRow(unittest.TestCase):
    def test_payment_late_is_red(self):
        # the headline assertion of the step: seed a late payment, demand RED
        events = [
            {"ts": "2026-05-01", "type": "payment_received"},
            {"ts": "2026-06-01", "type": "invoice_overdue"},
        ]
        light, note = payment_status(events)
        self.assertEqual(light, R, f"payment_late must be RED, got {light} ({note})")

    def test_status_field_late_is_red(self):
        events = [{"ts": "2026-06-01", "type": "payment_received", "status": "past_due"}]
        self.assertEqual(payment_status(events)[0], R)

    def test_renewal_lapsed_is_red(self):
        events = [{"ts": "2026-06-01", "type": "renewal", "lapsed": True}]
        light, note = payment_status(events)
        self.assertEqual(light, R)
        self.assertIn("renewal", note.lower())

    def test_recent_payment_clears_earlier_late(self):
        # append-only: a payment AFTER the overdue mark restores GREEN
        events = [
            {"ts": "2026-06-01", "type": "invoice_overdue"},
            {"ts": "2026-06-10", "type": "payment_received"},
        ]
        self.assertEqual(payment_status(events)[0], G)

    def test_clean_payment_is_green(self):
        events = [{"ts": "2026-06-15", "type": "payment_received"}]
        self.assertEqual(payment_status(events)[0], G)

    def test_no_ledger_is_yellow_not_green_not_red(self):
        # pre-commercial pilot: never mistaken for paying, never falsely alarmed
        light, note = payment_status([])
        self.assertEqual(light, Y)
        self.assertIn("pre-commercial", note)

    def test_approval_events_do_not_make_it_green(self):
        # the core distinction: approving-non-paying != healthy. Approvals are not payments.
        events = [
            {"ts": "2026-06-01", "type": "client_approved"},
            {"ts": "2026-06-02", "type": "client_approved"},
            {"ts": "2026-06-03", "type": "batch_rating", "rating": 5},
        ]
        self.assertEqual(payment_status(events)[0], Y,
                         "approvals alone must never light PAYMENT green")

    def test_invoice_pending_is_yellow(self):
        events = [{"ts": "2026-06-12", "type": "invoice_sent"}]
        self.assertEqual(payment_status(events)[0], Y)

    def test_row_is_wired_and_light_is_valid(self):
        # consumer check: the row appears in status() output with a ladder-legal light
        import fingerprint_status as fs
        clients = fs.real_clients()  # canonical real-client list (Rule #3), not inline glob
        self.assertTrue(clients)
        for h in clients:
            rows = {r[0]: r[1] for r in fs.status(h)["rows"]}
            self.assertIn("PAYMENT", rows, f"{h}: PAYMENT row missing")
            self.assertIn(rows["PAYMENT"], (G, Y, R),
                          f"{h}: PAYMENT light {rows['PAYMENT']!r} not ladder-legal")


if __name__ == "__main__":
    unittest.main()
