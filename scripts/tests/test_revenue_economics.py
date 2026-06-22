#!/usr/bin/env python3
"""Guards the REVENUE SIDE of unit economics (B091). All on synthetic fixtures in a tempdir
(no live data). The contracts that matter:
(1) revenue is REAL only for a CONFIRMED tier; an unconfirmed/missing organ → UNKNOWN, never guessed (Rule #9);
(2) a missing commercial_terms organ surfaces as 'no_organ', not a silent zero (Rule #6);
(3) the two truth-views split correctly: produced-work-but-no-confirmed-terms = approving_but_not_paying;
(4) cost_per_yes is UNKNOWN over zero YES (a ratio over zero approvals is a lie, not a big number);
(5) the pinned tiers load as REAL numbers."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import revenue_economics as rev


def _tiers(base: Path):
    (base / "data").mkdir(parents=True, exist_ok=True)
    (base / "data/commercial_tiers.json").write_text(json.dumps(
        {"tiers": {"starter": 700, "growth": 2650, "enterprise": 9000}}), encoding="utf-8")


def _terms(base: Path, h: str, **fields):
    d = base / "clients" / h / "profile"
    d.mkdir(parents=True, exist_ok=True)
    (d / "commercial_terms.json").write_text(json.dumps(fields), encoding="utf-8")


def _posts(base: Path, h: str, n: int):
    d = base / "clients" / h / "posts"
    d.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (d / f"p{i}.json").write_text("{}", encoding="utf-8")


class TestRevenueEconomics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        _tiers(self.base)
        self.tpath = self.base / "data/commercial_tiers.json"
        self.cdir = self.base / "clients"

    def tearDown(self):
        self.tmp.cleanup()

    def test_pinned_tiers_load_real(self):
        self.assertEqual(rev.load_tiers(self.tpath),
                         {"starter": 700, "growth": 2650, "enterprise": 9000})

    def test_confirmed_tier_is_real_revenue(self):
        _terms(self.base, "alpha", tier="growth", status="confirmed", monthly_sar=None)
        r = rev.revenue_per_client(self.cdir, self.tpath, pilots=["alpha"])["alpha"]
        self.assertEqual(r["honesty"], "REAL")
        self.assertEqual(r["monthly_sar"], 2650)

    def test_unconfirmed_tier_is_unknown_not_guessed(self):
        _terms(self.base, "beta", tier="growth", status="no_terms_confirmed", monthly_sar=None)
        r = rev.revenue_per_client(self.cdir, self.tpath, pilots=["beta"])["beta"]
        self.assertEqual(r["honesty"], "UNKNOWN")
        self.assertIsNone(r["monthly_sar"])

    def test_missing_organ_flagged_not_silent_zero(self):
        # client dir exists but no commercial_terms.json
        (self.cdir / "gamma" / "profile").mkdir(parents=True, exist_ok=True)
        t = rev.client_terms(self.cdir, pilots=["gamma"])["gamma"]
        self.assertEqual(t["status"], "no_organ")

    def test_views_split_approving_but_not_paying(self):
        # produced work, but terms unconfirmed → approving_but_not_paying
        _terms(self.base, "beta", tier="growth", status="no_terms_confirmed", monthly_sar=None)
        _posts(self.base, "beta", 3)
        v = rev.views(self.cdir, self.tpath, pilots=["beta"])
        self.assertIn("beta", v["approving_but_not_paying"])
        self.assertNotIn("beta", v["paying_but_silent"])

    def test_views_paying_but_silent(self):
        # confirmed terms, no produced work → paying_but_silent
        _terms(self.base, "alpha", tier="starter", status="confirmed", monthly_sar=None)
        v = rev.views(self.cdir, self.tpath, pilots=["alpha"])
        self.assertIn("alpha", v["paying_but_silent"])
        self.assertNotIn("alpha", v["approving_but_not_paying"])

    def test_cost_per_yes_unknown_over_zero_yes(self):
        # no unit_economics.json + no answers → UNKNOWN, never a divide-by-zero or fake ratio
        cpy = rev.cost_per_yes(unit_econ_path=self.base / "data/none.json",
                               answers_path=self.base / "data/none.jsonl")
        self.assertEqual(cpy["honesty"], "UNKNOWN")
        self.assertIsNone(cpy["usd_per_yes"])

    def test_build_report_shape(self):
        _terms(self.base, "beta", tier=None, status="no_terms_confirmed", monthly_sar=None)
        _posts(self.base, "beta", 1)
        rep = rev.build_report(self.cdir, self.tpath,
                               unit_econ_path=self.base / "data/none.json",
                               answers_path=self.base / "data/none.jsonl", pilots=["beta"])
        self.assertIn("revenue_per_client", rep)
        self.assertIn("views", rep)
        self.assertIn("cost_per_yes", rep)
        self.assertEqual(rep["views"]["approving_but_not_paying"], ["beta"])


if __name__ == "__main__":
    unittest.main()
