#!/usr/bin/env python3
"""B160 — ogz_account_owner field in the client-state organ.

Mohamed fork B093: the red-client alert must drop a human-touch task that NAMES the account owner.
That requires the owner to live in the client-state organ. This adds the field (null until Mohamed
names names) and locks it with a test — a field with no contract is a Rule #6 lie waiting to happen.

What this guards:
  1. EVERY pilot's state.json carries ogz_account_owner, typed str-or-null (the B093 consumer can
     .get() it safely and branch on null = "owner not yet named").
  2. The schema declares the field with the right type, and ACCEPTS both a name and null while
     REFUSING a wrong type (Rule #8 — the contract bites, it doesn't whisper).

Note: we validate a constructed minimal instance against the schema, NOT the live files wholesale —
albaik/myfitness already carry pre-B160 top-level keys (outreach_ruling, archive_claim_poor) that
predate this change and are out of scope here."""
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).parent.parent.parent
SCHEMA = json.loads((ROOT / "12_data_shapes/client_state_v1.schema.json").read_text(encoding="utf-8"))
STATE_FILES = sorted((ROOT / "clients").glob("*/profile/state.json"))


def _minimal_valid(owner):
    """Smallest instance the schema accepts, with ogz_account_owner set to `owner`."""
    return {
        "state": "newborn",
        "posts_count": 0,
        "followers": 0,
        "last_post": None,
        "silent_days": 0,
        "method": "countables_only",
        "human_checkpoint": "pending",
        "ogz_account_owner": owner,
        "provenance": {
            "source": "test", "date_added": "2026-06-22",
            "confirmer": "test", "confidence": "experimental", "scope": "brand",
        },
    }


class TestAccountOwnerOrgan(unittest.TestCase):

    def test_pilot_states_discovered(self):
        # guard against a glob that silently finds nothing and passes everything below
        self.assertGreaterEqual(len(STATE_FILES), 3, "expected at least the 3 pilots' state.json")

    def test_every_state_has_typed_owner(self):
        for f in STATE_FILES:
            d = json.loads(f.read_text(encoding="utf-8"))
            self.assertIn("ogz_account_owner", d, f"{f.parent.parent.name} missing ogz_account_owner")
            self.assertIsInstance(d["ogz_account_owner"], (str, type(None)),
                                  f"{f.parent.parent.name} owner must be str or null")

    def test_schema_declares_owner(self):
        prop = SCHEMA["properties"].get("ogz_account_owner")
        self.assertIsNotNone(prop, "schema must declare ogz_account_owner")
        self.assertEqual(set(prop["type"]), {"string", "null"})

    def test_schema_accepts_name_and_null(self):
        jsonschema.validate(_minimal_valid("Mohamed"), SCHEMA)  # a named owner validates
        jsonschema.validate(_minimal_valid(None), SCHEMA)        # null (unnamed) validates

    def test_schema_refuses_wrong_type(self):
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(_minimal_valid(123), SCHEMA)     # a number is not an owner


if __name__ == "__main__":
    unittest.main()
