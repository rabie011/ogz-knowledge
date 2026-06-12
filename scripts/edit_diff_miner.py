#!/usr/bin/env python3
"""B089 — EDIT-DIFF MINER: distill Mohamed's verdict stream into PROPOSED organ updates.

THE TOP this serves: his taste is the moat; every note he types is taste leaking into
text. This miner reads the answers ledger (notes + ratings — only 1 fix-text exists,
so edits are not the signal yet), clusters REPEATED same-direction corrections, and
writes data/taste_distillation.json: each cluster carries his verbatim quotes as
evidence, a target organ, and a PROPOSED update. NOTHING auto-applies — proposals
wait for his tap (or feed the morning brief). RABIE's caveat honored: a signal needs
n>=2 independent rows to become a proposal; singletons are listed as 'weak_signals'
so nothing is invented from one offhand line.

Deterministic, zero-LLM, idempotent (full recompute each run).
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base

OUT = "data/taste_distillation.json"

# Signal registry: (slug, regex over note text, target organ/file, proposed update).
# Patterns are matched on the RAW note (Arabic + his English-with-typos) — these are
# his recurring correction THEMES, each born from a real quote, never invented.
SIGNALS = [
    ("family_scene_fatigue",
     r"family|عائل|أهل",
     "clients/<handle>/profile/taste.json kill_patterns",
     "family scene is worn — demand scene diversity per week (no repeated emotional core)"),
    ("scene_diversity",
     r"different|repeat|same idea|كرر|نفس الفكر",
     "render: angle stage",
     "enforce per-week idea-core diversity: consecutive slots must not share emotional core"),
    ("app_cta_fatigue",
     r"\bapp\b|التطبيق",
     "clients/<handle>/profile/taste.json kill_patterns",
     "delivery-app CTAs fatigued — cap app mentions per week"),
    ("religion_play_safe",
     r"religion|دين|الله|اللهم",
     "data/law_registry.json prayer_as_commercial_backdrop",
     "religious surfaces: people-first framing, never product-first (his words: «about the people not the product»)"),
    ("too_safe_no_creativity",
     r"to safe|too safe|مفيش ابداع|not creative|to small",
     "20_cd_brains prompts",
     "safe-but-flat is a REJECTION class — brains must take one concrete creative risk per caption (his bar: safe ≠ approved)"),
    ("worn_phrase",
     r"احلي مع|أحلى مع|لحظة|يجمعنا|تجمعنا",
     "scripts/render_client_slot.py STANDING_WORN",
     "extend the standing worn list when he names a phrase (already: لحظة/يجمعنا/احلي مع …)"),
    ("full_post_context",
     r"full post|الفكرة كاملة|breif|brief|image and story|client and what is the detail",
     "scripts/seed_judge_cards.py",
     "judge cards must carry the FULL post (occasion/idea/visual/reasoning) — bare captions are unjudgeable"),
    ("client_name_visible",
     r"client name|اسم العميل",
     "scripts/seed_judge_cards.py post_idea",
     "client name leads every judged card"),
    ("brand_dna_first",
     r"brand dna|strategy before|الهوية",
     "pipeline order",
     "deepen brand DNA + strategy organs BEFORE caption/idea work — creative quality is downstream of profile depth (his ruling: 3 pilot clients only)"),
    ("cultural_word_risk",
     r"سدر|means.*culture|بالعامية",
     "scripts/caption_filter.py _CULTURAL_TERMS",
     "dialect double-meaning screen: when he flags a word, it enters the cultural gate same-day"),
    ("audience_fit_over_art",
     r"للشريحه|الشريحة|audience",
     "clients/<handle>/profile/audience_mirror.json",
     "audience-fit is rated separately from creativity in his notes — track both axes"),
    ("invented_product",
     r"falafel|فلافل|dose albaik have|منتج",
     "scripts/caption_filter.py (deferred product-noun entailment)",
     "captions may only name products in the client's truth pack — his falafel catch is the standing evidence"),
    ("saudi_dialect_authenticity",
     r"مش سعودي|الكتبابه غلط|الكتابه غلط|عدل الكابشن",
     "scripts/caption_filter.py dialect_check",
     "captions for Saudi clients must read SAUDI — Egyptian/Levantine markers "
     "(مش/عايز/ازاي/كده/بتاع/دلوقتي) are a hard flag (his: «عدل الكابشن … ومش سعودي»)"),
    ("scene_brand_coherence",
     r"العلاقه بين|تعني في السياق|ليه حارات",
     "render: angle stage",
     "every scene element must have a stated link to the brand — he asks «what's the "
     "relation between X and the brand» when a prop is decorative"),
    ("safe_tier_labeling",
     r"safe side|^Safe$",
     "data/pattern_cards_v1.json tiers",
     "«good for safe side content» is a TIER, not a rejection — label safe-lane recipes "
     "so the mix is deliberate (safe posts have a place, never the whole week)"),
    ("cliche_flat_tone",
     r"clishy|cliché|كليشيه|dosent feel good|يرفع المعنويات",
     "20_cd_brains prompts + STANDING_WORN",
     "corporate-positivity phrases (يرفع المعنويات) and cliché imagery read FLAT to him — "
     "same rejection class as too-safe"),
    ("audience_price_age_fit",
     r"oudunace|oduance|by age by price|who can",
     "clients/<handle>/profile/audience_mirror.json",
     "connect to the target audience by AGE and PRICE BAND — he needs the audience organ "
     "to say who can afford the client before judging fit"),
    ("no_comparison_evidence",
     r"who is better|no comparing|يقارن",
     "data/law_registry.json brand_never_invites_comparison",
     "evidence row for the standing law (already enforced)"),
    ("no_sexual_double_meaning_evidence",
     r"sexual|humiliation|double meaning|duoble meaning",
     "data/law_registry.json no_sexual_innuendo_or_humiliation",
     "evidence row for the standing law (already enforced)"),
    ("emotional_trigger_quality",
     r"trigger emotion|بذات التجربه|تحفيز",
     "20_cd_brains prompts",
     "find emotion triggers WITHOUT manufactured sentimentality (his: «better way to trigger emotions»)"),
]


def main():
    b = base()
    rows = [json.loads(l) for l in (b / "data/mohamed_answers.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    mo = [r for r in rows if r.get("judge") == "mohamed" and (r.get("note") or "").strip()]

    clusters = defaultdict(list)
    for r in mo:
        note = r["note"].strip()
        for slug, pat, target, proposal in SIGNALS:
            if re.search(pat, note, re.IGNORECASE):
                clusters[slug].append({
                    "quote": note[:160], "item": r.get("item_id"),
                    "rating": r.get("rating"), "ts": (r.get("client_ts") or r.get("ts", ""))[:16]})

    sig_meta = {s[0]: s for s in SIGNALS}
    proposals, weak = [], []
    for slug, hits in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        # n>=2 independent rows (distinct item_ids) — RABIE's anti-invention bar
        distinct = {h["item"] for h in hits}
        rec = {"signal": slug, "n_rows": len(hits), "n_items": len(distinct),
               "target": sig_meta[slug][2], "proposed": sig_meta[slug][3],
               "his_words": [h["quote"] for h in hits[:6]],
               "avg_rating_when_noted": round(sum(h["rating"] for h in hits if h["rating"] is not None)
                                              / max(1, sum(1 for h in hits if h["rating"] is not None)), 2)
                                        if any(h["rating"] is not None for h in hits) else None}
        (proposals if len(distinct) >= 2 else weak).append(rec)

    matched_rows = {h["item"] for hs in clusters.values() for h in hs}
    unmatched = [r["note"][:120] for r in mo
                 if r.get("item_id") not in matched_rows
                 and not any(re.search(p, r["note"], re.IGNORECASE) for _, p, _, _ in SIGNALS)]

    out = {"generated": datetime.now().isoformat(timespec="seconds"),
           "doc": "PROPOSED taste distillations from Mohamed's verdict stream — nothing "
                  "here auto-applies; n_items>=2 bar per RABIE; unmatched notes listed "
                  "so no founder word is silently outside the analysis",
           "source_rows": len(mo), "proposals": proposals,
           "weak_signals_n1": weak, "unmatched_notes": unmatched}
    (b / OUT).write_text(json.dumps(out, ensure_ascii=False, indent=1))

    print(f"mined {len(mo)} noted rows → {len(proposals)} proposals (n≥2) · "
          f"{len(weak)} weak (n=1) · {len(unmatched)} unmatched")
    for p in proposals:
        print(f"  ★ {p['signal']} (n={p['n_items']}): {p['proposed'][:80]}")
    if unmatched:
        print("  unmatched (no signal pattern — read by hand):")
        for u in unmatched[:8]:
            print(f"    · {u}")


if __name__ == "__main__":
    main()
