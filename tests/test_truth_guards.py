#!/usr/bin/env python3
"""GATE0 anti-hallucination guard — product_is_real (truth_guards.py).

Born June 30 (DeepSeek+RABIE consult, Rule #19) after two PROVEN fail-opens let a hallucinated
product clear the gate that guards FAL spend (Rule #12):
  (1) a raw substring over every profile/*.json passed «عيد أضحى مبارك» (a greeting in
      moments_bank.json) as a 'product';
  (2) a single ≥4-char token in captions passed «أي منتج وهمي» for alnasserjewelry because the
      common word «منتج»=product appears in its captions.

This asserts the fix END-TO-END against the 3 LIVE clients' real on-disk data:
  • real products (from each client's product_truth.json) PASS
  • fakes («أي منتج وهمي», «تشكن بيك») REFUSE
Run:  python3 tests/test_truth_guards.py   (exit 0 = all hold, non-zero = a gate broke)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from truth_guards import product_is_real, product_truth_names  # noqa: E402

BASE = str(ROOT)

# (handle, product, expected_is_real)  — real names lifted verbatim from each product_truth.json
CASES = [
    # albaik — real (must PASS)
    ("albaik", "سوبر رول", True),
    ("albaik", "كرسبي بيك", True),
    ("albaik", "دبل بيك", True),
    ("albaik", "بيكيز", True),              # single-token real product → must be confirmed structurally
    # eatjurisha — real (must PASS)
    ("eatjurisha", "جريش", True),           # the brand's signature dish, single token, in product_truth
    ("eatjurisha", "رز كابلي", True),
    ("eatjurisha", "قرصان", True),
    # alnasserjewelry — real (must PASS)
    ("alnasserjewelry", "عقد ألماس", True),
    ("alnasserjewelry", "خاتم ألماس", True),
    ("alnasserjewelry", "دبلة", True),

    # FAKES — must REFUSE for EVERY client (the exact exploits the fix closes)
    ("albaik", "أي منتج وهمي", False),
    ("eatjurisha", "أي منتج وهمي", False),
    ("alnasserjewelry", "أي منتج وهمي", False),   # the «منتج» common-token fail-open
    ("albaik", "تشكن بيك", False),                 # the June 29 birth case
    ("eatjurisha", "تشكن بيك", False),
    ("alnasserjewelry", "تشكن بيك", False),
    # the moments_bank greeting that step1's raw substring used to pass
    ("alnasserjewelry", "عيد أضحى مبارك", False),
    # degenerate inputs
    ("albaik", "", False),
    ("albaik", "منتج", False),                     # a lone common word is never a product
]


def main():
    # sanity: the structured reader sees real products under BOTH on-disk shapes
    assert "سوبر رول" in product_truth_names("albaik", base_dir=BASE), "albaik top-level-key shape not read"
    assert "جريش" in product_truth_names("eatjurisha", base_dir=BASE), "eatjurisha products-dict shape not read"
    assert "عقد ألماس" in product_truth_names("alnasserjewelry", base_dir=BASE), "alnasser products-dict shape not read"

    fails = 0
    for handle, product, expect in CASES:
        ok, why = product_is_real(handle, product, base_dir=BASE)
        good = (ok == expect)
        fails += not good
        verdict = "PASS" if ok else "REFUSE"
        mark = "✅" if good else "❌"
        want = "PASS" if expect else "REFUSE"
        print(f"  {mark} [{verdict:6}] {handle:16} {product!r:20} (want {want}) — {why}")

    print(f"\n{'✅ GATE0 HOLDS — real pass, fakes refuse' if not fails else f'❌ {fails} GATE0 failure(s)'}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
