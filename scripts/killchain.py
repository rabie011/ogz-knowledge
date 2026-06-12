#!/usr/bin/env python3
"""OFFLINE KILLCHAIN (B120, June 12 — RABIE-ratified).
Run any caption through the FULL kill-chain with ZERO LLM calls: truth guards,
very_normal anchors, CTA-day law, worn grams. Prints which law kills and why.
Every future guard debate settles in one command.

Usage:
  python3 scripts/killchain.py --text "..." [--handle albaik] [--date 2026-08-02] [--occasion eid_al_fitr]
  echo "caption" | python3 scripts/killchain.py --handle albaik
"""
import argparse, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None)
    ap.add_argument("--handle", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--occasion", default=None)
    a = ap.parse_args()
    text = a.text if a.text is not None else sys.stdin.read().strip()
    if not text:
        sys.exit("no caption given")
    verdicts = []

    # 1. truth guards (G1-G8 + family/service)
    from truth_guards import apply_guards
    corpus = ""
    if a.handle:
        tpf = BASE / "clients" / a.handle / "profile/truth_pack.json"
        if tpf.exists():
            corpus = json.dumps(json.loads(tpf.read_text()), ensure_ascii=False)
    # the never-zero-survivors fallback is PRODUCTION safety — in a tester it lies:
    # a lone killed caption gets resurrected into surv. Judge by the kill RECORD.
    surv, kills = apply_guards([text, "سطر محايد للمقارنة فقط"], corpus, {"occasion": a.occasion})
    my_kill = next((k for k in kills if (k[0] if isinstance(k, (list, tuple)) else str(k)) == text
                     or text[:30] in str(k)), None)
    if my_kill or text not in surv:
        verdicts.append(("TRUTH GUARDS", f"killed — {str(my_kill)[:80] if my_kill else 'not among survivors'}"))
    else:
        verdicts.append(("TRUTH GUARDS", "survives"))

    # 2. very_normal (needs a client street)
    if a.handle:
        try:
            from very_normal_test import build_rival_corpus, client_anchors, distinctive_anchors, grams3, very_normal
            corpus_r = build_rival_corpus(a.handle)
            rg = set()
            for caps in corpus_r.values():
                for c in caps:
                    rg |= grams3(c)
            rt = " ".join(" ".join(v) for v in corpus_r.values())
            anchors = client_anchors(a.handle) + distinctive_anchors(a.handle, rt)
            r = very_normal(text, anchors, rg)
            verdicts.append(("VERY_NORMAL", r or "survives (anchored)"))
        except Exception as e:
            verdicts.append(("VERY_NORMAL", f"skipped: {str(e)[:60]}"))

    # 3. CTA-day law
    if a.handle and a.date:
        from render_client_slot import cta_allowed, CTA_EMOTIONAL
        from truth_guards import CTA
        sells = bool(CTA.search(text))
        allowed = cta_allowed(a.handle, {"date": a.date, "occasion": a.occasion})
        if sells and not allowed:
            why = "emotional occasion never sells" if (a.occasion in CTA_EMOTIONAL) else "brand-build day (date-hash)"
            verdicts.append(("CTA-DAY LAW", f"killed — sells on a no-sell day ({why})"))
        else:
            verdicts.append(("CTA-DAY LAW", "survives" + (" (sell-day)" if sells else " (no CTA present)")))

    # 4. worn grams (client recent renders)
    if a.handle:
        try:
            from render_client_slot import load_client
            c = load_client(a.handle)
            worn = c.get("worn_phrases") or []
            hit = next((w for w in worn if w in text), None)
            verdicts.append(("WORN GRAMS", f"killed — worn tic «{hit}»" if hit else "survives"))
        except SystemExit:
            verdicts.append(("WORN GRAMS", "skipped (client load)"))

    killed = [v for v in verdicts if v[1].startswith("killed")]
    print(f"\n«{text[:70]}»")
    for law, verdict in verdicts:
        print(f"  {'🔴' if verdict.startswith('killed') else '🟢'} {law}: {verdict}")
    print(f"\n{'🔴 DEAD — ' + killed[0][0] if killed else '🟢 SURVIVES the full chain'}")
    sys.exit(1 if killed else 0)


if __name__ == "__main__":
    main()
