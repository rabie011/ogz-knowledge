#!/usr/bin/env python3
"""Guards the client communication contract organ (B158, Flanks). Proves the wire is whole
(Rule #6): the schema validates, the writer's inferred stubs are well-formed and bidirectional,
the reader REFUSES an invalid organ (Rule #8), and a stub never falsely claims Mohamed's
confirmation (Rules #11/#13 — confirmer='inferred', not 'mohamed')."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import comm_contract as cc


class TestCommContract(unittest.TestCase):

    def test_inferred_defaults_validate_for_all_pilots(self):
        for h in cc.CLIENTS:
            c = cc.infer_defaults(h)
            self.assertEqual(cc.validate(c), [], f"{h} inferred contract should be valid")

    def test_contract_is_bidirectional(self):
        c = cc.infer_defaults("eatjurisha")
        for field in ("ping_budget_per_week", "response_sla_hours"):
            self.assertIn("us_to_client", c[field])
            self.assertIn("client_to_us", c[field])

    def test_validate_catches_missing_keys(self):
        self.assertTrue(cc.validate({}))                       # empty → faults
        c = cc.infer_defaults("albaik")
        del c["channel"]
        self.assertTrue(any("channel" in e for e in cc.validate(c)))

    def test_validate_catches_bad_enum(self):
        c = cc.infer_defaults("albaik")
        c["channel"]["primary"] = "carrier_pigeon"
        self.assertTrue(any("channel.primary" in e for e in cc.validate(c)))
        c2 = cc.infer_defaults("albaik")
        c2["language"] = "klingon"
        self.assertTrue(any("language" in e for e in cc.validate(c2)))

    def test_validate_catches_one_missing_direction(self):
        c = cc.infer_defaults("eatjurisha")
        del c["response_sla_hours"]["client_to_us"]
        self.assertTrue(any("client_to_us" in e for e in cc.validate(c)))

    def test_budget_null_means_unbounded_is_valid(self):
        c = cc.infer_defaults("eatjurisha")
        self.assertIsNone(c["ping_budget_per_week"]["client_to_us"])  # null inbound = unbounded
        self.assertEqual(cc.validate(c), [])

    def test_stub_never_claims_mohamed_confirmation(self):
        # Rules #11/#13: an inferred stub must NEVER stamp his confirmation.
        for h in cc.CLIENTS:
            c = cc.infer_defaults(h)
            self.assertEqual(c["provenance"]["confirmer"], "inferred")
            self.assertEqual(c["status"], "inferred_unconfirmed")

    def test_loader_refuses_invalid_organ(self, ):
        # The reader half (Rule #8): a present-but-invalid contract is REFUSED, not served.
        import json, tempfile, os
        c = cc.infer_defaults("eatjurisha")
        c["language"] = "nope"
        # write to a temp handle path under a temp clients tree
        orig_B = cc.B
        try:
            with tempfile.TemporaryDirectory() as d:
                cc.B = Path(d)
                p = Path(d) / "clients" / "eatjurisha" / "profile" / "comm_contract.json"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(c, ensure_ascii=False))
                with self.assertRaises(ValueError):
                    cc.load("eatjurisha")
        finally:
            cc.B = orig_B

    def test_persisted_pilot_stubs_exist_and_validate(self):
        # The writer actually laid the organs down this cycle and they load clean.
        for h in cc.CLIENTS:
            loaded = cc.load(h)
            self.assertIsNotNone(loaded, f"{h} comm_contract.json should exist")
            self.assertEqual(cc.validate(loaded), [])


if __name__ == "__main__":
    unittest.main()
