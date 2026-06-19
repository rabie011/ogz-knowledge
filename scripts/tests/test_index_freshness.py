#!/usr/bin/env python3
"""B261 — staleness checks for the 4 live learn-from indexes.

Locks: (1) each timestamp-extraction path (embedded key, nested _meta/meta key,
date-only string, file-mtime fallback) is parsed correctly; (2) >30d flags and
<=30d does not; (3) a MISSING file is flagged; (4) the check is WARN-only —
calling it never raises and never exits."""
import json
import datetime
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import index_freshness as ifr

NOW = datetime.datetime(2026, 6, 19)  # fixed "today" so the test is deterministic


def _iso_days_ago(n, suffix="Z"):
    return (NOW - datetime.timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%S") + suffix


class TestParseTs(unittest.TestCase):
    def test_iso_with_z(self):
        self.assertEqual(ifr._parse_ts("2026-06-04T20:27:51Z"),
                         datetime.datetime(2026, 6, 4, 20, 27, 51))

    def test_iso_with_offset_micros(self):
        # +00:00 offset with microseconds normalizes to naive UTC
        self.assertEqual(ifr._parse_ts("2026-06-06T01:34:28.575170+00:00"),
                         datetime.datetime(2026, 6, 6, 1, 34, 28, 575170))

    def test_date_only(self):
        self.assertEqual(ifr._parse_ts("2026-06-11"),
                         datetime.datetime(2026, 6, 11, 0, 0, 0))

    def test_garbage_and_empty(self):
        self.assertIsNone(ifr._parse_ts("not-a-date"))
        self.assertIsNone(ifr._parse_ts(""))
        self.assertIsNone(ifr._parse_ts(None))

    def test_offset_converts_to_utc(self):
        # +03:00 (Riyadh) at 03:00 == 00:00 UTC
        self.assertEqual(ifr._parse_ts("2026-06-10T03:00:00+03:00"),
                         datetime.datetime(2026, 6, 10, 0, 0, 0))


class TestDig(unittest.TestCase):
    def test_nested_hit_and_miss(self):
        d = {"meta": {"updated_at": "x"}}
        self.assertEqual(ifr._dig(d, "meta.updated_at"), "x")
        self.assertIsNone(ifr._dig(d, "meta.missing"))
        self.assertIsNone(ifr._dig(d, "nope.deeper"))


class TestStaleness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "11_who_to_learn_from").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, obj):
        p = self.base / rel
        p.write_text(json.dumps(obj))
        return p

    def test_all_fresh(self):
        self._write("11_who_to_learn_from/target_accounts.json",
                    {"updated_at": _iso_days_ago(5)})
        self._write("11_who_to_learn_from/intelligence_layer.json",
                    {"meta": {"updated_at": _iso_days_ago(10, "+00:00")}})
        self._write("11_who_to_learn_from/content_types_canonical_index.json",
                    {"_meta": {"built": (NOW - datetime.timedelta(days=3)).strftime("%Y-%m-%d")}})
        # accounts_index has no embedded ts -> file mtime (just written = fresh)
        self._write("11_who_to_learn_from/accounts_index.json", {"a": 1})
        stale = ifr.check_index_staleness(base=self.base, now=NOW)
        self.assertEqual(stale, [], f"expected all fresh, got {stale}")

    def test_embedded_key_stale(self):
        self._write("11_who_to_learn_from/target_accounts.json",
                    {"updated_at": _iso_days_ago(45)})
        stale = ifr.check_index_staleness(
            base=self.base, now=NOW,
            indexes=[("target_accounts",
                      "11_who_to_learn_from/target_accounts.json", ["updated_at"])])
        self.assertEqual(len(stale), 1)
        name, age, src = stale[0]
        self.assertEqual(name, "target_accounts")
        self.assertEqual(age, 45)
        self.assertEqual(src, "updated_at")

    def test_nested_meta_stale(self):
        self._write("11_who_to_learn_from/intelligence_layer.json",
                    {"meta": {"updated_at": _iso_days_ago(60, "+00:00")}})
        stale = ifr.check_index_staleness(
            base=self.base, now=NOW,
            indexes=[("intelligence_layer",
                      "11_who_to_learn_from/intelligence_layer.json",
                      ["meta.updated_at", "meta.generated_at"])])
        self.assertEqual(stale[0][2], "meta.updated_at")
        self.assertEqual(stale[0][1], 60)

    def test_fallback_to_second_key(self):
        # first key absent -> uses generated_at
        self._write("11_who_to_learn_from/intelligence_layer.json",
                    {"meta": {"generated_at": _iso_days_ago(40)}})
        stale = ifr.check_index_staleness(
            base=self.base, now=NOW,
            indexes=[("intelligence_layer",
                      "11_who_to_learn_from/intelligence_layer.json",
                      ["meta.updated_at", "meta.generated_at"])])
        self.assertEqual(stale[0][2], "meta.generated_at")

    def test_date_only_threshold_boundary(self):
        # exactly 30 days -> NOT stale (> not >=)
        self._write("11_who_to_learn_from/content_types_canonical_index.json",
                    {"_meta": {"built": (NOW - datetime.timedelta(days=30)).strftime("%Y-%m-%d")}})
        idx = [("content_types_canonical_index",
                "11_who_to_learn_from/content_types_canonical_index.json", ["_meta.built"])]
        self.assertEqual(ifr.check_index_staleness(base=self.base, now=NOW, indexes=idx), [])
        # 31 days -> stale
        self._write("11_who_to_learn_from/content_types_canonical_index.json",
                    {"_meta": {"built": (NOW - datetime.timedelta(days=31)).strftime("%Y-%m-%d")}})
        self.assertEqual(len(ifr.check_index_staleness(base=self.base, now=NOW, indexes=idx)), 1)

    def test_missing_file_flagged(self):
        idx = [("ghost_index", "11_who_to_learn_from/does_not_exist.json", ["updated_at"])]
        stale = ifr.check_index_staleness(base=self.base, now=NOW, indexes=idx)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0][2], "MISSING")
        self.assertIsNone(stale[0][1])

    def test_warn_only_never_raises(self):
        # malformed JSON -> falls back to file mtime, does not raise
        p = self.base / "11_who_to_learn_from/accounts_index.json"
        p.write_text("{ this is not json")
        idx = [("accounts_index", "11_who_to_learn_from/accounts_index.json", [])]
        stale = ifr.check_index_staleness(base=self.base, now=NOW, indexes=idx)
        # freshly written -> mtime fresh -> no stale entry, and crucially no exception
        self.assertEqual(stale, [])

    def test_format_warnings_shapes(self):
        lines = ifr.format_warnings([
            ("target_accounts", 45, "updated_at"),
            ("ghost", None, "MISSING"),
        ])
        self.assertTrue(any("45d old" in l and "target_accounts" in l for l in lines))
        self.assertTrue(any("MISSING" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
