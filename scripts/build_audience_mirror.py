#!/usr/bin/env python3
"""AUDIENCE MIRROR BUILDER (B012, June 12) — mechanize what was hand-mined once:
the customer's own words become a tallied organ. Reads the latest raw comments,
tallies THEMES (cheap model — money law), and fills customer_language/pains ONLY
where no human already curated them. Curated keys are never overwritten — the
machine adds, humans rule (One Write Path).

Usage: python3 scripts/build_audience_mirror.py [--handle X]
"""
import argparse, json, os, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
MODEL = "gpt-4o-mini"          # money law: tallying is a cheap-model job


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def llm_tally(comments: list[str]) -> dict:
    body = {"model": MODEL, "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content":
                "هذه تعليقات حقيقية من عملاء على حساب براند سعودي. رجّع JSON فقط:\n"
                '{"themes":[{"theme":"...","count":N,"example":"تعليق حرفي"}],'
                '"customer_language":["8 تعليقات حرفية تلخص صوت العميل"],'
                '"pains_aggregate":["3-5 أوجاع مجمعة بدون هويات"]}\n'
                "العد صادق: count = كم تعليق يلمس الثيم فعلاً. التعليقات:\n"
                + "\n".join(f"- {c[:200]}" for c in comments[:200])}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=120).read())
    return json.loads(out["choices"][0]["message"]["content"])


def build(handle: str):
    raw_root = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw_root.iterdir() if d.is_dir())
    cf = days[-1] / "comments.jsonl"
    comments = []
    if cf.exists():
        comments = [json.loads(l).get("text", "") for l in cf.read_text().strip().split("\n")
                    if l.strip() and json.loads(l).get("text")]
    mf = BASE / "clients" / handle / "profile/audience_mirror.json"
    mirror = json.loads(mf.read_text()) if mf.exists() else {}
    before_curated = {k: mirror.get(k) for k in ("customer_language", "pains_aggregate", "note")}

    mirror.setdefault("comments_count", len(comments))
    mirror.setdefault("sample", comments[:10])
    mirror.setdefault("note", f"machine-built {days[-1].name} from {len(comments)} comments")
    if not comments:
        mirror["machine_note"] = "no comments in latest extraction — mirror is blind, ask the client"
        mf.write_text(json.dumps(mirror, ensure_ascii=False, indent=2))
        print(f"  ⚠ {handle}: 0 comments — blind mirror noted")
        return
    tally = llm_tally(comments)
    mirror["theme_tally"] = tally.get("themes", [])
    thin = " · THIN CORPUS (<30) — tallies indicative only" if len(comments) < 30 else ""
    mirror["machine_note"] = f"theme tally {days[-1].name} · {len(comments)} comments · {MODEL}{thin}"
    # the machine adds, humans rule: curated keys only filled where EMPTY
    if not mirror.get("customer_language"):
        mirror["customer_language"] = tally.get("customer_language", [])[:8]
    if not mirror.get("pains_aggregate"):
        mirror["pains_aggregate"] = tally.get("pains_aggregate", [])[:5]
    for k, v in before_curated.items():
        if v is not None:
            assert mirror[k] == v, f"CURATED KEY '{k}' CHANGED — refusing to write"
    mf.write_text(json.dumps(mirror, ensure_ascii=False, indent=2))
    print(f"  ✓ {handle}: {len(mirror['theme_tally'])} themes tallied from {len(comments)} comments{thin}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               sorted(d.name for d in (BASE / "clients").iterdir() if (d / "raw/instagram").is_dir()))
    for h in clients:
        build(h)


if __name__ == "__main__":
    main()
