#!/usr/bin/env python3
"""VERY-NORMAL KILL TEST (B167+B168, June 12 — RABIE-confirmed).
Mohamed's too_generic essence in code: «زاوية لا يمكن لأي براند آخر نشرها» —
a caption with ZERO client-unique anchors that any rival on HIS street could
post is very_normal. Verbatim 3-gram overlap with a rival caption = instant flag.
TAG, never kill — his taste is the moat; the judging batch excludes flagged.

Usage: python3 scripts/very_normal_test.py --handle eatjurisha [--tag]
"""
import argparse, json, re
from pathlib import Path

BASE = Path(__file__).parent.parent
ARCHIVE = BASE / "11_who_to_learn_from/_raw_archive"
_JUNK = re.compile(r"حساب|account|snapchat|@|^على$|^في$", re.I)


def build_rival_corpus(handle: str) -> dict:
    """B167: the rival corpus already lives in the archive — pull, never re-scrape."""
    cs = json.loads((BASE / "clients" / handle / "profile/competitor_set.json").read_text())
    rivals = [r for r in dict.fromkeys(cs.get("client_given", []) + cs.get("proposed_from_corpus", []))
              if r != handle]          # a brand is never its own rival
    corpus = {}
    for r in rivals:
        rd = ARCHIVE / r
        if not rd.is_dir():
            continue
        latest = sorted(d for d in rd.iterdir() if d.is_dir())[-1]
        caps = []
        for f in latest.glob("*.jsonl"):
            for l in f.read_text().strip().split("\n"):
                try:
                    c = json.loads(l).get("caption")
                except Exception:
                    continue
                if c:
                    caps.append(c)
        if caps:
            corpus[r] = caps
    out = BASE / "clients" / handle / "derived/rival_corpus.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"rivals": {k: len(v) for k, v in corpus.items()},
                                 "pulled": "2026-06-12"}, ensure_ascii=False, indent=1))
    return corpus


def client_anchors(handle: str) -> list[str]:
    tp = json.loads((BASE / "clients" / handle / "profile/truth_pack.json").read_text())
    anchors = [p["name"] for p in tp.get("product_candidates", [])
               if p.get("name") and len(p["name"]) >= 3 and not _JUNK.search(p["name"])]
    raw = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw.iterdir() if d.is_dir())
    prof = json.loads((days[-1] / "profile.json").read_text())
    name = prof.get("fullName") or ""
    if name:
        anchors.append(name)
    # brand tokens: arabic pieces of the name AND the bio (English-named brands like
    # ALBAIK carry their arabic token «البيك» in the bio, not the fullName)
    bio = prof.get("biography") or ""
    anchors += re.findall(r"[؀-ۿ]{3,}", name)
    anchors += [w.strip("#") for w in re.findall(r"#?[؀-ۿ]{4,}", bio)]
    return [a for a in dict.fromkeys(anchors) if len(a) >= 3]


def distinctive_anchors(handle: str, rival_text: str) -> list[str]:
    """The client's own voice is the richest anchor source the truth pack misses:
    tokens frequent in HIS captions but absent from the rival street are HIS
    (e.g. «بيك», «كرسبي» for albaik — junk truth-packs never carry them)."""
    import collections
    raw = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw.iterdir() if d.is_dir())
    counts = collections.Counter()
    pf = days[-1] / "posts.jsonl"
    if pf.exists():
        # split on real newlines ONLY — captions carry U+2028 separators that
        # splitlines() shatters, silently dropping lines (the التوأم undercount)
        for l in pf.read_text().strip().split('\n'):
            try:
                cap = json.loads(l).get("caption") or ""
            except Exception:
                continue
            for w in set(re.findall(r"[؀-ۿ]{3,}", cap)):
                counts[w] += 1
    import re as _re
    rival_counts = collections.Counter(_re.findall(r"[؀-ۿ]{3,}", rival_text))
    # distinctive = lives in HIS mouth (>=5 captions), rare on the street (<3 rival uses)
    # no rank cutoff — a 7-mention product (التوأم) ranks below 60 in a 521-caption
    # feed full of filler; frequency + street-rarity are the only honest filters
    return [w for w, n in counts.items() if n >= 3 and rival_counts[w] < 3][:300]


def grams3(text: str) -> set:
    w = re.sub(r"[^؀-ۿ\s]", " ", text).split()
    return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}


def very_normal(caption: str, anchors: list[str], rival_grams: set) -> str | None:
    """Returns the reason if very_normal, else None."""
    shared = grams3(caption) & rival_grams
    if shared:
        return f"verbatim rival overlap: «{next(iter(shared))}»"
    if not any(a in caption for a in anchors):
        return "zero client anchors — any rival could post it"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--tag", action="store_true", help="write very_normal flags into cards")
    a = ap.parse_args()
    corpus = build_rival_corpus(a.handle)
    rg = set()
    for caps in corpus.values():
        for c in caps:
            rg |= grams3(c)
    rival_text = " ".join(" ".join(v) for v in corpus.values())
    anchors = client_anchors(a.handle) + distinctive_anchors(a.handle, rival_text)
    print(f"rivals: {len(corpus)} with captions · rival 3-grams: {len(rg)} · anchors: {anchors[:5]}")
    flagged = cleared = scanned = 0
    for f in sorted((BASE / "clients" / a.handle / "posts").glob("*.json")):
        try:
            card = json.loads(f.read_text())
        except Exception:
            continue
        caps = card.get("captions") or []
        if not caps:
            continue
        scanned += 1
        reasons = [r for r in (very_normal(c, anchors, rg) for c in caps) if r]
        is_vn = len(reasons) == len(caps)        # very_normal only if EVERY option is
        if is_vn and not card.get("very_normal"):
            flagged += 1
            if a.tag:
                card["very_normal"] = reasons[0]
                f.write_text(json.dumps(card, ensure_ascii=False, indent=2))
        elif not is_vn and card.get("very_normal"):
            if a.tag:
                card.pop("very_normal")
                f.write_text(json.dumps(card, ensure_ascii=False, indent=2))
                cleared += 1
    print(f"{'tagged' if a.tag else 'would flag'} {flagged}/{scanned} very_normal · cleared {cleared}")


if __name__ == "__main__":
    main()
