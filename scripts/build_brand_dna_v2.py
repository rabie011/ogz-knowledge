#!/usr/bin/env python3
"""Brand DNA v2 — KNOW WHAT WE'RE WRITING before any brain writes (Mohamed's law, June 10).

GPT-4o reads the brand's REAL archive (top-engagement + recent posts) and returns
structured DNA: voice, openers, signature phrases, emoji style, post-type mix,
top exemplars tagged by post type. File-first, idempotent (skips if fresh DNA exists
unless --force). Output: logs/brand_dna/{brand}_dna_v2.json

Usage: python3 scripts/build_brand_dna_v2.py --brand albaik [--force]
"""
import argparse, glob, json, os, re, sys, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT  = BASE / "logs" / "brand_dna"


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
        if len(cap) < 4:
            continue
        posts.append({"caption": cap[:300], "likes": int(p.get("likesCount") or 0),
                      "comments": int(p.get("commentsCount") or 0), "ts": p.get("timestamp", "")})
    return posts


def openai_key() -> str:
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith("OPENAI_API_KEY"):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit("no OPENAI_API_KEY")


DNA_SPEC = """You are a brand-voice analyst for Saudi social media. Below are REAL Instagram posts
from one brand, with engagement. Build the brand's DNA as STRICT JSON (no markdown) with keys:
- voice_summary_en: 2 sentences, what this feed actually sounds like
- dialect: e.g. "saudi", "gulf", "MSA-leaning"
- tone: list of 3-5 adjectives (English)
- proven_openers_ar: list of the ACTUAL opening words/phrases their high-engagement posts use (Arabic, from the data only)
- signature_phrases_ar: recurring branded phrases/hashtags (Arabic, from the data only)
- emoji_style: {density: none|light|medium|heavy, favorites: [list]}
- post_type_mix: {announcement_pct, offer_pct, occasion_greeting_pct, product_showcase_pct, community_pct} (estimate, sums ~100)
- length_profile: {typical_chars: int, style: "one-liner"|"two-liner"|"paragraph"}
- exemplars: list of 10 objects {caption, likes, post_type} — the strongest VOICE-DEFINING posts across different post types (not just top likes; pick what teaches the voice)
- always_does_en: list of 4-6 positive patterns this feed always does (POSITIVE framing only)
Return JSON only."""


def build_dna(brand: str) -> dict:
    posts = load_posts(brand)
    posts.sort(key=lambda x: x["likes"], reverse=True)
    sample = posts[:60] + posts[60::4][:40]  # engagement-first + spread for recency/diversity
    corpus = "\n".join(f"[{p['likes']} likes] {p['caption']}" for p in sample)
    body = {"model": "gpt-4o", "temperature": 0.2, "max_tokens": 2200,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": DNA_SPEC},
                          {"role": "user", "content": f"BRAND: {brand}\nPOSTS ({len(sample)}):\n{corpus}"}]}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {openai_key()}",
                                          "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    dna = json.loads(r["choices"][0]["message"]["content"])
    dna["_meta"] = {"brand": brand, "posts_analyzed": len(sample), "archive_posts": len(posts),
                    "built": "2026-06-10", "builder": "build_brand_dna_v2.py", "model": "gpt-4o"}
    return dna


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{a.brand}_dna_v2.json"
    if out.exists() and not a.force:
        print(f"exists: {out} (use --force)")
        return
    dna = build_dna(a.brand)
    # verification before claiming done (the law): required keys + exemplar count
    missing = [k for k in ("voice_summary_en", "proven_openers_ar", "exemplars", "always_does_en") if k not in dna]
    if missing or len(dna.get("exemplars", [])) < 6:
        sys.exit(f"DNA INCOMPLETE for {a.brand}: missing={missing} exemplars={len(dna.get('exemplars', []))}")
    out.write_text(json.dumps(dna, ensure_ascii=False, indent=2))
    print(f"✓ {a.brand}: {len(dna['exemplars'])} exemplars · openers={dna['proven_openers_ar'][:4]} · {out.name}")


if __name__ == "__main__":
    main()
