#!/usr/bin/env python3
"""COLD CONSULT (June 12 — Mohamed: "do search and consult — not the LLM fucking
you up"). The echo-breaker: a FRESH-CONTEXT outside reviewer (no session history,
no shared assumptions, adversarial prompt) reads a random sample of recent cards
and hunts for what the in-context pair can no longer see. Findings are logged and
anything systemic gets pushed to the crystallize path.

Usage: python3 scripts/cold_consult.py [--n 3]
"""
import argparse, glob, json, os, random, time, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
LOG = BASE / "data/cold_consult_log.jsonl"


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    a = ap.parse_args()
    cards = glob.glob(str(BASE / "clients/*/posts/*__v5.json"))
    if not cards:
        cards = glob.glob(str(BASE / "clients/*/posts/*.json"))
    sample = random.sample(cards, min(a.n, len(cards)))
    payload = []
    for f in sample:
        c = json.loads(open(f).read())
        payload.append({"client": c.get("handle"), "occasion": (c.get("slot") or {}).get("occasion") or "evergreen",
                         "idea": (c.get("idea") or {}).get("scene_ar", "")[:200],
                         "captions": (c.get("captions") or [])[:3]})
    body = {"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 900,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content":
                 "You are a COLD OUTSIDE REVIEWER with zero context — hired to find what an in-house team "
                 "can no longer see in their own Saudi Instagram content. Be adversarial and specific. "
                 "Hunt: invented facts, cultural missteps, sameness across posts (template smell), "
                 "weak Arabic, claims a client would object to, anything that would embarrass a brand. "
                 'Return JSON: {"findings": [{"client": "...", "severity": "high|medium|low", '
                 '"issue": "...", "evidence": "exact phrase"}], "systemic_pattern": "one line or null"}'},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    out = json.loads(json.loads(urllib.request.urlopen(rq, timeout=90).read())["choices"][0]["message"]["content"])
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "sampled": [Path(f).name for f in sample],
              "findings": out.get("findings", []), "systemic": out.get("systemic_pattern")}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    high = [x for x in entry["findings"] if x.get("severity") == "high"]
    print(f"cold eyes: {len(entry['findings'])} findings ({len(high)} high) on {len(sample)} cards")
    for x in entry["findings"][:5]:
        print(f"  [{x.get('severity')}] {x.get('client')}: {x.get('issue')[:80]} — «{x.get('evidence','')[:50]}»")
    if entry["systemic"]:
        print(f"  ⚠ SYSTEMIC: {entry['systemic'][:120]}")
    raise SystemExit(1 if high else 0)


if __name__ == "__main__":
    main()
