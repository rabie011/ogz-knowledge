#!/usr/bin/env python3
"""B029 — presend gate under sandbox: re-ask blocked with evidence, fresh clears.

Runs in an OGZ_BASE sandbox so violation events never pollute the real trust ledger
(the eyes-test on 2026-06-13 wrote 3 synthetic violations to the real file — this
suite exists so that never repeats).
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent.parent


class TestPresendGate(unittest.TestCase):
    def setUp(self):
        self.sb = Path(tempfile.mkdtemp(prefix="ogz_presend_"))
        os.environ["OGZ_BASE"] = str(self.sb)
        (self.sb / "data").mkdir()
        (self.sb / "clients/testbrand/profile").mkdir(parents=True)
        # evidence: a founder q-card answer + a voice organ
        (self.sb / "data/mohamed_answers.jsonl").write_text(json.dumps(
            {"ts": "2026-06-13T01:00:00", "judge": "mohamed", "auth": "key",
             "item_id": "testbrand_q_products", "answer": "approved",
             "note": "الجريش والكبسة"}, ensure_ascii=False) + "\n")
        (self.sb / "clients/testbrand/profile/fingerprint.json").write_text(json.dumps(
            {"l2_voice": {"speaker": "brand",
                          "speaker_ruling": {"source": "portal:testbrand_voice"}}},
            ensure_ascii=False))
        # reload the module against the sandbox
        sys.path.insert(0, str(REPO / "scripts"))
        import importlib
        import feedback_lib
        importlib.reload(feedback_lib)
        import presend_gate
        importlib.reload(presend_gate)
        self.pg = presend_gate

    def tearDown(self):
        os.environ.pop("OGZ_BASE", None)
        import importlib
        import feedback_lib
        importlib.reload(feedback_lib)

    def test_answered_products_blocked_with_evidence(self):
        r = self.pg.check_question(self.sb, "testbrand", "وش منتجاتكم الأساسية؟")
        self.assertTrue(r["blocked"])
        self.assertIn("testbrand_q_products", r["hits"][0]["evidence"])

    def test_voice_blocked_by_organ(self):
        r = self.pg.check_question(self.sb, "testbrand", "how should the brand voice sound?")
        self.assertTrue(r["blocked"])
        self.assertIn("speaker=brand", r["hits"][0]["evidence"])

    def test_fresh_question_clears(self):
        r = self.pg.check_question(self.sb, "testbrand", "وش الباقات والأسعار الحالية؟")
        self.assertFalse(r["blocked"], r)

    def test_unknown_client_clears(self):
        r = self.pg.check_question(self.sb, "ghostbrand", "وش منتجاتكم؟")
        self.assertFalse(r["blocked"], r)


if __name__ == "__main__":
    unittest.main()
