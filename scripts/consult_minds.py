#!/usr/bin/env python3
"""CONSULT THE MINDS on a DESIGN (not post-cards — that's cold_consult.py).

Mohamed (2026-06-13): "use him with the other minds, prove anything before go." This is
the design-fork consult: send a proposed design + the decision question to a FRESH outside
mind (GPT-4o-mini on the funded OpenAI key — a genuinely different LLM, "not cloud only"),
adversarially prompted to attack it. Logs to data/consult_log.jsonl. Exits non-zero if the
mind raises a HIGH concern (so a caller can REFUSE to proceed — prove before go).

Usage:
  python3 scripts/consult_minds.py --title "v3.7 visual-DNA schema" \\
      --file docs/PROPOSAL.md --question "Does this fully align to v3.7? What breaks?"
  echo "design text" | python3 scripts/consult_minds.py --title X --question Y
"""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
LOG = BASE / "data/consult_log.jsonl"


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def consult(title, body, question, lens):
    sysmsg = (
        f"You are a {lens}. Zero shared context with the author. You are reviewing a DESIGN "
        "proposal for a Saudi creative-AI platform. Be adversarial, specific, concrete. "
        "Find: hidden assumptions, ways it will break in production, misalignments with the "
        "stated standard, missing cases, simpler alternatives. Do NOT rubber-stamp. "
        'Return JSON: {"verdict":"sound|risky|broken", '
        '"concerns":[{"severity":"high|medium|low","issue":"...","fix":"..."}], '
        '"missing":["..."], "one_thing_to_change":"..."}'
    )
    user = f"DESIGN: {title}\n\nQUESTION: {question}\n\n----\n{body}"
    payload = {"model": "gpt-4o-mini", "temperature": 0.4, "max_tokens": 1100,
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": sysmsg},
                            {"role": "user", "content": user[:14000]}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(payload).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    raw = json.loads(urllib.request.urlopen(rq, timeout=90).read())
    return json.loads(raw["choices"][0]["message"]["content"]), raw.get("usage", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--file", default="")
    ap.add_argument("--question", required=True)
    ap.add_argument("--lens", default="COLD OUTSIDE SYSTEMS ARCHITECT, skeptical and senior")
    a = ap.parse_args()
    body = Path(a.file).read_text() if a.file else sys.stdin.read()
    out, usage = consult(a.title, body, a.question, a.lens)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "title": a.title, "lens": a.lens,
             "question": a.question, "verdict": out.get("verdict"),
             "concerns": out.get("concerns", []), "missing": out.get("missing", []),
             "one_thing": out.get("one_thing_to_change"), "usage": usage}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    high = [c for c in entry["concerns"] if c.get("severity") == "high"]
    print(f"  MIND verdict: {entry['verdict']} · {len(entry['concerns'])} concerns ({len(high)} high) · {usage.get('total_tokens','?')} tok")
    for c in entry["concerns"]:
        print(f"    [{c.get('severity')}] {c.get('issue')}\n        → fix: {c.get('fix')}")
    if entry["missing"]:
        print(f"  MISSING: {entry['missing']}")
    if entry["one_thing"]:
        print(f"  ONE THING TO CHANGE: {entry['one_thing']}")
    raise SystemExit(2 if high else 0)


if __name__ == "__main__":
    main()
