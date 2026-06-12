#!/usr/bin/env python3
"""THE IDEA WELL (June 12 — RABIE's zoom-out #1 ruling: moments_bank 10x or the
week becomes a template farm). Mines CONCRETE MOMENTS from the client's whole
caption corpus via cheap mini-batches: who+when scenes, customer language,
product rituals — appended to moments_bank with provenance, deduped. The
renderer's variety ceiling = the size of this well.

Usage: python3 scripts/mine_moments.py --handle albaik
"""
import argparse, json, os, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
BATCH = 40
MODEL = "gpt-4o-mini"  # money discipline: pennies per client


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def mine_batch(captions: list[str], brand: str) -> list[dict]:
    body = {"model": MODEL, "temperature": 0.4, "max_tokens": 1500,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content":
                 "From these REAL brand captions, extract CONCRETE MOMENTS a creative team can reuse: "
                 "a specific person/role + a specific time/beat + a gesture/ritual involving the product. "
                 "Also extract recurring CUSTOMER LANGUAGE (phrases the brand's world actually uses). "
                 "Skip generic celebration lines. "
                 'Return JSON: {"moments": [{"theme": "short tag", "evidence": "the concrete moment in one line (Arabic)", '
                 '"source_quote": "exact phrase from a caption"}]}'},
                {"role": "user", "content": f"البراند: {brand}\n" + "\n---\n".join(captions)}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    return json.loads(json.loads(urllib.request.urlopen(rq, timeout=120).read())
                      ["choices"][0]["message"]["content"]).get("moments", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    a = ap.parse_args()
    raw = sorted((BASE / "clients" / a.handle / "raw/instagram").iterdir())[-1]
    posts = [json.loads(l) for l in (raw / "posts.jsonl").read_text().strip().split("\n") if l.strip()]
    caps = [p["caption"][:280] for p in posts if p.get("caption")]
    mf = BASE / "clients" / a.handle / "profile/moments_bank.json"
    bank = json.loads(mf.read_text())
    seen = {m["evidence"][:50] for m in bank["moments"]}
    added = 0
    for i in range(0, len(caps), BATCH):
        chunk = caps[i:i + BATCH]
        try:
            mined = mine_batch(chunk, a.handle)
        except Exception as e:
            print(f"  batch {i//BATCH}: failed ({e}) — continuing")
            continue
        for m in mined:
            ev = (m.get("evidence") or "")[:200]
            if not ev or ev[:50] in seen:
                continue
            seen.add(ev[:50])
            bank["moments"].append({"occasion": m.get("theme", "evergreen")[:40], "evidence": ev,
                                      "provenance": {"source": f"mined:{m.get('source_quote','')[:60]}",
                                                      "date_added": __import__("datetime").date.today().isoformat(), "confirmer": "pending_client",
                                                      "confidence": "inferred", "scope": "brand"}})
            added += 1
        mf.write_text(json.dumps(bank, ensure_ascii=False, indent=2))  # checkpoint
        print(f"  batch {i//BATCH + 1}/{(len(caps)-1)//BATCH + 1}: +{added} total")
    print(f"\n✓ {a.handle}: well grew to {len(bank['moments'])} moments (+{added})")


if __name__ == "__main__":
    main()
