"""B204/B205 occasion-gold minting — pure-logic tests, no LLM (money-discipline).

Proves the machine (not any hand-written line): idempotency, seed shape, product-preference,
never-block on a dead producer, and the write-gate. The producer is injected/faked."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import seed_occasion_gold as sog  # noqa: E402


class TestSelectLine(unittest.TestCase):
    def test_prefers_line_naming_product(self):
        caps = ["عرض رمضان يبدأ الآن", "جرب زنجر البيك هذا الشهر", "أهلاً رمضان"]
        self.assertEqual(sog.select_line(caps, "زنجر البيك"), "جرب زنجر البيك هذا الشهر")

    def test_falls_back_to_first_when_no_product(self):
        caps = ["عرض رمضان", "أهلاً رمضان"]
        self.assertEqual(sog.select_line(caps, "زنجر"), "عرض رمضان")

    def test_handles_dict_options_shape(self):
        caps = {"options": [{"caption": "  "}, {"caption": "زنجر البيك اليوم"}]}
        self.assertEqual(sog.select_line(caps, "زنجر البيك"), "زنجر البيك اليوم")

    def test_empty_returns_empty(self):
        self.assertEqual(sog.select_line([], "x"), "")
        self.assertEqual(sog.select_line(["", "  "], "x"), "")


class TestIdempotency(unittest.TestCase):
    def test_already_seeded_true_for_existing_source(self):
        gold = {"seed_unconfirmed": [{"occasion": "ramadan", "source": "occasion_gold_ramadan"}], "gold": []}
        self.assertTrue(sog.already_seeded(gold, "ramadan"))
        self.assertFalse(sog.already_seeded(gold, "white_friday"))

    def test_merge_seed_skips_duplicate(self):
        gold = {"seed_unconfirmed": [{"occasion": "ramadan", "source": "occasion_gold_ramadan"}], "gold": []}
        entry = sog.make_seed_entry("ramadan", "line", "p", "2026-07-01T00:00:00")
        self.assertFalse(sog.merge_seed(gold, entry))
        self.assertEqual(len(gold["seed_unconfirmed"]), 1)

    def test_merge_seed_adds_new(self):
        gold = {"seed_unconfirmed": [], "gold": []}
        entry = sog.make_seed_entry("eid_al_fitr", "line", "p", "2026-07-01T00:00:00")
        self.assertTrue(sog.merge_seed(gold, entry))
        self.assertEqual(len(gold["seed_unconfirmed"]), 1)


class TestSeedShape(unittest.TestCase):
    def test_seed_entry_is_unconfirmed_and_traceable(self):
        e = sog.make_seed_entry("white_friday", "عرض الجمعة البيضاء", "زنجر", "2026-07-01T12:00:00")
        self.assertEqual(e["source"], "occasion_gold_white_friday")
        self.assertEqual(e["occasion"], "white_friday")
        self.assertFalse(e["rated"])       # RABIE hasn't judged it (his eye is the only judge)
        self.assertFalse(e["confirmed"])
        self.assertEqual(e["ts"], "2026-07-01T12:00:00")


class TestMintLoop(unittest.TestCase):
    TS = "2026-07-01T00:00:00"

    def test_mints_each_fresh_occasion_and_skips_existing(self):
        gold = {"seed_unconfirmed": [{"occasion": "ramadan", "source": "occasion_gold_ramadan"}], "gold": []}
        produce = lambda h, occ, p: [f"{p} — احتفل بـ {occ}"]
        gold, results = sog.mint_occasions("albaik", ["ramadan", "eid_al_fitr", "eid_al_adha"],
                                           "زنجر", produce, self.TS, gold)
        by = {r["occasion"]: r["status"] for r in results}
        self.assertEqual(by["ramadan"], "skipped_exists")
        self.assertEqual(by["eid_al_fitr"], "minted")
        self.assertEqual(by["eid_al_adha"], "minted")
        self.assertEqual(len([x for x in gold["seed_unconfirmed"] if x.get("rated") is False]), 2)

    def test_dead_producer_does_not_abort_batch(self):
        def flaky(h, occ, p):
            if occ == "boom":
                raise RuntimeError("model down")
            return [f"{p} {occ}"]
        gold, results = sog.mint_occasions("albaik", ["boom", "founding_day"], "زنجر", flaky, self.TS,
                                           {"seed_unconfirmed": [], "gold": []})
        by = {r["occasion"]: r["status"] for r in results}
        self.assertEqual(by["boom"], "produce_error")
        self.assertEqual(by["founding_day"], "minted")   # batch survived the dead one

    def test_empty_product_is_not_falsely_flagged_as_named(self):
        # a service brand with no product_candidates yields product='' — '' in line is always True,
        # so named_product must be guarded to False, not a false ✓product (Rule #9).
        gold, results = sog.mint_occasions("myfitness.sa", ["ramadan"], "", lambda h, o, p: ["صوت الضحكات يملأ الحديقة"],
                                           self.TS, {"seed_unconfirmed": [], "gold": []})
        self.assertEqual(results[0]["status"], "minted")
        self.assertFalse(results[0]["named_product"])

    def test_no_line_when_producer_returns_empty(self):
        gold, results = sog.mint_occasions("albaik", ["ramadan"], "زنجر", lambda h, o, p: [],
                                           self.TS, {"seed_unconfirmed": [], "gold": []})
        self.assertEqual(results[0]["status"], "no_line")
        self.assertEqual(gold["seed_unconfirmed"], [])


if __name__ == "__main__":
    unittest.main()
