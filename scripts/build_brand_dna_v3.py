#!/usr/bin/env python3
"""Brand DNA v3 — THE JOIN (June 11, 2026, founder-approved plan).

v2 asked GPT to re-derive what the Brain already mined. v3 JOINS three sources:
  RAW      — real posts + engagement (from raw archive)
  MINED    — the Brain's own pattern library: which of the 13 caption structures
             this brand uses (GPT classifies the brand's real posts against the
             library), + account-level traits (high/low engagement themes,
             distinctive_voice_traits, anti_patterns_observed)
  DERIVED  — the v2 GPT fingerprint (voice, openers, signatures, emoji)

Output: logs/brand_dna/{brand}_dna_v3.json (v2 stays untouched).
Usage: python3 scripts/build_brand_dna_v3.py --brand albaik [--force]
"""
import argparse, glob, json, os, re, statistics, sys, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT  = BASE / "logs" / "brand_dna"


def _key() -> str:
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith("OPENAI_API_KEY"):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit("no OPENAI_API_KEY")


def load_posts(brand: str) -> list[dict]:
    files = sorted(glob.glob(str(BASE / "11_who_to_learn_from/_raw_archive" / brand / "*" / "*apify_raw.jsonl")), reverse=True)
    if not files:
        sys.exit(f"no raw archive for {brand}")
    posts = []
    for line in open(files[0], encoding="utf-8"):
        try:
            p = json.loads(line)
        except Exception:
            continue
        cap = (p.get("caption") or "").strip()
        if len(cap) >= 4:
            posts.append({"caption": cap[:400], "likes": int(p.get("likesCount") or 0)})
    return posts


def pattern_library() -> list[dict]:
    pats = []
    for f in sorted(glob.glob(str(BASE / "11_who_to_learn_from/patterns/caption_structure/*.json"))):
        d = json.loads(open(f).read())
        pats.append({"slug": d.get("pattern_slug"), "name": d.get("pattern_name"),
                     "description": (d.get("description") or "")[:200]})
    return pats


def account_traits(brand: str) -> dict:
    for f in glob.glob(str(BASE / "11_who_to_learn_from/accounts/*/account_*.json")):
        d = json.loads(open(f).read())
        if brand in str(d.get("account_handle_normalized", "")) or brand in str(d.get("account_handle_internal", "")):
            return {k: d.get(k) for k in
                    ("high_engagement_themes", "low_engagement_themes",
                     "distinctive_voice_traits", "anti_patterns_observed")}
    return {}


def classify_patterns(brand: str, posts: list[dict], pats: list[dict]) -> dict:
    """GPT maps the brand's top 30 real posts onto the Brain's structure library."""
    top = sorted(posts, key=lambda x: x["likes"], reverse=True)[:30]
    corpus = "\n".join(f"{i+1}. [{p['likes']}] {p['caption'][:180]}" for i, p in enumerate(top))
    lib = "\n".join(f"- {p['slug']}: {p['description']}" for p in pats)
    body = {"model": "gpt-4o", "temperature": 0.1, "max_tokens": 1200,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You classify Instagram captions against a pattern library. Return STRICT JSON: {\"patterns_used\": [{\"slug\":..., \"count\":..., \"example_indices\":[...]}], \"unmatched_count\": int}. Use ONLY slugs from the library."},
                {"role": "user", "content": f"LIBRARY:\n{lib}\n\nPOSTS from {brand}:\n{corpus}"}]}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return json.loads(r["choices"][0]["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = OUT / f"{a.brand}_dna_v3.json"
    if out.exists() and not a.force:
        print(f"exists: {out}")
        return
    v2f = OUT / f"{a.brand}_dna_v2.json"
    if not v2f.exists():
        sys.exit(f"build v2 first: python3 scripts/build_brand_dna_v2.py --brand {a.brand}")
    dna = json.loads(v2f.read_text())  # DERIVED layer

    posts = load_posts(a.brand)        # RAW layer
    lens = sorted(len(p["caption"]) for p in posts)
    if lens:
        dna["length_distribution"] = {"p25": lens[len(lens)//4], "p50": lens[len(lens)//2],
                                       "p90": lens[int(len(lens)*0.9)], "n": len(lens)}
    else:
        dna["length_distribution"] = {"p25": 0, "p50": 0, "p90": 0, "n": 0, "note": "thin captions"}

    pats = pattern_library()           # MINED layer
    cls = classify_patterns(a.brand, posts, pats)
    dna["patterns_used"] = [p["slug"] for p in cls.get("patterns_used", []) if p.get("count", 0) >= 2]
    dna["patterns_detail"] = cls.get("patterns_used", [])
    dna["account_traits"] = account_traits(a.brand)

    dna["_meta"]["version"] = "v3-join"
    dna["_meta"]["joined"] = "raw+mined+derived"
    out.write_text(json.dumps(dna, ensure_ascii=False, indent=2))
    print(f"✓ {a.brand} v3: patterns={dna['patterns_used']} · lengths p50={dna['length_distribution']['p50']} p90={dna['length_distribution']['p90']} · traits={'yes' if dna['account_traits'] else 'none-found'}")


if __name__ == "__main__":
    main()
