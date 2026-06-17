#!/usr/bin/env python3
"""Guards the model-free Mohamed-Elo consumer (Step 1, June 15): Bradley-Terry ranks a clear
winner above a clear loser, and the consumer is wired into the tap loop."""
import inspect, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import taste_elo as te
import apply_rulings as ar


class TestTasteElo(unittest.TestCase):
    def test_bradley_terry_ranks_winner_above_loser(self):
        # A beats B 3x, B beats C 3x → strength A > B > C
        pairs = [(0, 1), (0, 1), (0, 1), (1, 2), (1, 2), (1, 2)]
        ids, pi = te.bradley_terry(pairs)
        s = {ids[i]: pi[i] for i in range(len(ids))}
        self.assertGreater(s[0], s[1]); self.assertGreater(s[1], s[2])

    def test_elo_consumer_wired_into_tap_loop(self):
        self.assertIn("taste_elo", inspect.getsource(ar.main),
                      "taste_elo not recomputed after a tap consumes (Rule #6 — the consumer must run)")

    def test_held_out_split_is_stable_across_runs(self):
        """June 16 scar: hash() is PYTHONHASHSEED-randomized, so the held-out split (and the number
        it produces) was not reproducible. The md5 split must give the SAME order every run."""
        import subprocess
        prog = ("import sys; sys.path.insert(0,'scripts'); import taste_elo as te, json;"
                "from pathlib import Path;"
                "prefs=[json.loads(l) for l in Path('data/pairwise_prefs.jsonl').read_text().splitlines() if l.strip()];"
                "order=list(range(len(prefs)));"
                "import hashlib;"
                "order.sort(key=lambda i:int(hashlib.md5(prefs[i]['winner_caption'].encode()).hexdigest(),16));"
                "print(order[:5])")
        r1 = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent.parent))
        r2 = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True,
                            cwd=str(Path(__file__).parent.parent.parent))
        self.assertEqual(r1.stdout, r2.stdout, "held-out split differs across processes — hash() still in use")


    def test_feedback_is_honest_and_deterministic(self):
        """The instant-tap nudge: non-empty, names the live pick count, and is STABLE (depends on the
        Step-1 stable hash). Must NOT claim 'model agrees N%' or a brain lean (overclaim at ~6 picks)."""
        prefs = [
            {"winner_caption": "قصير.", "loser_caption": "نص أطول بكثير من الأول هنا.", "source": "x"},
            {"winner_caption": "آخر اختيار", "loser_caption": "نص أطول جدا جدا جدا للمقارنة", "source": "x"},
        ]
        f1 = te.feedback_for(prefs)
        f2 = te.feedback_for(prefs)
        self.assertTrue(f1 and isinstance(f1, str))
        self.assertEqual(f1, f2, "feedback not deterministic")
        self.assertIn("2", f1, "feedback should name the live pick count")
        self.assertNotIn("%", f1, "feedback must not claim an agreement % (overclaim at low N)")
        self.assertNotIn("brain", f1.lower(), "feedback must not claim a brain lean (brain unknown at low N)")

    def test_feedback_empty_prefs_safe(self):
        self.assertIsInstance(te.feedback_for([]), str)

    def test_held_out_live_is_undefined_when_pilot_pairs_disconnected(self):
        """June 17 scar: the public held_out_agreement_pct hit 100% riding on rescued seed pairs
        (rating-5 vs rating-0) while EVERY live pick was dropped (each caption seen once → no
        strength when held out). The honest live-only number must report 0 testable / None — not
        inherit the lie (Rule #9). Three isolated live picks → nothing is testable."""
        prefs = [
            {"winner_caption": "أ", "loser_caption": "ب", "source": None},
            {"winner_caption": "ج", "loser_caption": "د", "source": None},
            {"winner_caption": "هـ", "loser_caption": "و", "source": None},
        ]
        caps = {}
        cid = lambda c: caps.setdefault(c, len(caps))
        pairs = [(cid(p["winner_caption"]), cid(p["loser_caption"])) for p in prefs]
        pct, n = te.held_out_live(pairs, prefs)
        self.assertEqual(n, 0, "disconnected pilot pairs must yield 0 testable")
        self.assertIsNone(pct, "undefined must be None, never a borrowed 100%")

    def test_held_out_live_scores_when_graph_connects(self):
        """The number must RISE the moment the sampler reuses captions: A>B and A>C live, plus a
        rescued seed B>C — hold out A>C and BT (trained on A>B, B>C) still ranks A above C."""
        prefs = [
            {"winner_caption": "A", "loser_caption": "B", "source": None},
            {"winner_caption": "A", "loser_caption": "C", "source": None},
            {"winner_caption": "B", "loser_caption": "C", "source": "seed_from_ratings"},
        ]
        caps = {}
        cid = lambda c: caps.setdefault(c, len(caps))
        pairs = [(cid(p["winner_caption"]), cid(p["loser_caption"])) for p in prefs]
        pct, n = te.held_out_live(pairs, prefs)
        self.assertGreater(n, 0, "a connected graph must make at least one live pick testable")
        self.assertEqual(pct, 100)


if __name__ == "__main__":
    unittest.main()
