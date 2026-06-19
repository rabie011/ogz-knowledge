"""B043 — is_en_led() is the ONE shared EN-led boundary (Rule #6 / "one boundary, all doors").

Before this, "does this brand lead in English?" was decided two different ways in two files:
  • render_client_slot.load_client: fingerprint.l2_voice.dialect == "non_arabic"
  • creative_line.render: majority of exemplars >50% Latin
Two doors on one boundary drift apart. These tests pin the unified helper AND assert it
reproduces BOTH legacy implementations exactly on representative inputs — zero LLM, zero IO.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from truth_guards import is_en_led, en_share


# the two legacy implementations, inlined verbatim, as the parity oracle
def _legacy_client(fingerprint):
    return fingerprint["l2_voice"].get("dialect") == "non_arabic"


def _legacy_matrix(exemplars):
    def _en_share(t):
        letters = [c for c in t if c.isalpha()]
        return sum(c.isascii() for c in letters) / max(len(letters), 1)
    exs = [e.get("caption", "") for e in exemplars[:6]]
    return sum(_en_share(e) > 0.5 for e in exs) >= 3


AR = "أهلين فيكم اليوم نقدم لكم الأفضل دائماً"          # pure Arabic body
EN = "Today we bring you the very best there is around"  # pure English body
AR_TAG = AR + " #McDonalds #Saudi"                       # Arabic body, Latin hashtag (must stay AR)


class TestFingerprintDoor(unittest.TestCase):
    def test_non_arabic_is_en_led(self):
        self.assertTrue(is_en_led(fingerprint={"l2_voice": {"dialect": "non_arabic"}}))

    def test_saudi_is_not_en_led(self):
        self.assertFalse(is_en_led(fingerprint={"l2_voice": {"dialect": "saudi"}}))

    def test_missing_l2_voice_is_safe_false(self):
        # the legacy line would KeyError here; the shared helper defaults to False, never crashes
        self.assertFalse(is_en_led(fingerprint={}))
        self.assertFalse(is_en_led(fingerprint={"l2_voice": None}))


class TestExemplarDoor(unittest.TestCase):
    def test_majority_latin_is_en_led(self):
        exs = [{"caption": EN}] * 3 + [{"caption": AR}] * 3
        self.assertTrue(is_en_led(exemplars=exs))

    def test_minority_latin_is_not(self):
        exs = [{"caption": EN}] * 2 + [{"caption": AR}] * 4
        self.assertFalse(is_en_led(exemplars=exs))

    def test_arabic_body_with_latin_hashtag_stays_arabic(self):
        # the mcdonalds case the comment calls out: a Latin hashtag must NOT flip the brand
        self.assertFalse(is_en_led(exemplars=[{"caption": AR_TAG}] * 6))

    def test_plain_string_exemplars_accepted(self):
        self.assertTrue(is_en_led(exemplars=[EN, EN, EN, AR, AR, AR]))


class TestNoSignal(unittest.TestCase):
    def test_no_inputs_defaults_arabic(self):
        self.assertFalse(is_en_led())

    def test_empty_exemplars_defaults_arabic(self):
        self.assertFalse(is_en_led(exemplars=[]))

    def test_fingerprint_wins_over_exemplars(self):
        # a client with a fingerprint never falls through to the exemplar heuristic
        self.assertTrue(is_en_led(fingerprint={"l2_voice": {"dialect": "non_arabic"}},
                                  exemplars=[{"caption": AR}] * 6))


class TestParityWithLegacy(unittest.TestCase):
    def test_client_door_matches_legacy(self):
        for dialect in ("non_arabic", "saudi", "khaleeji", "msa"):
            fp = {"l2_voice": {"dialect": dialect}}
            self.assertEqual(is_en_led(fingerprint=fp), _legacy_client(fp), dialect)

    def test_matrix_door_matches_legacy(self):
        cases = [
            [{"caption": EN}] * 6,
            [{"caption": AR}] * 6,
            [{"caption": EN}] * 3 + [{"caption": AR}] * 3,   # exactly majority
            [{"caption": EN}] * 2 + [{"caption": AR}] * 4,
            [{"caption": AR_TAG}] * 6,
            [{"caption": EN}] * 10,                            # >6: only first 6 count
        ]
        for exs in cases:
            self.assertEqual(is_en_led(exemplars=exs), _legacy_matrix(exs), exs[:1])


class TestEnShare(unittest.TestCase):
    def test_pure_english_high(self):
        self.assertGreater(en_share(EN), 0.9)

    def test_pure_arabic_zero(self):
        self.assertEqual(en_share(AR), 0.0)

    def test_no_letters_is_zero_not_crash(self):
        self.assertEqual(en_share("123 !! ٢٠٢٤"), 0.0)


if __name__ == "__main__":
    unittest.main()
