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


def latest_maps_reviews(client_dir) -> list[str]:
    """Reader for the newest Maps-reviews surface (B166 — the customer's UNPROMPTED voice).
    fetch_delivery_reviews.py WRITES raw/maps_reviews/<date>/reviews.jsonl; this is its
    missing CONSUMER (Rule #6 — a writer with no reader is a severed wire). Returns the
    review texts of the most recent day, tolerating both 'text' and 'reviewText' keys and
    dropping blanks. Missing surface → []."""
    root = Path(client_dir) / "raw/maps_reviews"
    if not root.exists():
        return []
    days = sorted(d for d in root.iterdir() if d.is_dir())
    if not days:
        return []
    rf = days[-1] / "reviews.jsonl"
    if not rf.exists():
        return []
    texts = []
    for l in rf.read_text().strip().split("\n"):
        if not l.strip():
            continue
        it = json.loads(l)
        t = (it.get("text") or it.get("reviewText") or "").strip()
        if t:
            texts.append(t)
    return texts


def build(handle: str):
    raw_root = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw_root.iterdir() if d.is_dir())
    cf = days[-1] / "comments.jsonl"
    comments = []
    if cf.exists():
        comments = [json.loads(l).get("text", "") for l in cf.read_text().strip().split("\n")
                    if l.strip() and json.loads(l).get("text")]
    reviews = latest_maps_reviews(BASE / "clients" / handle)   # B166 — fold Maps reviews into the tally corpus
    comments = comments + reviews                              # the unprompted voice joins the comment voice
    mf = BASE / "clients" / handle / "profile/audience_mirror.json"
    mirror = json.loads(mf.read_text()) if mf.exists() else {}
    before_curated = {k: mirror.get(k) for k in ("customer_language", "pains_aggregate", "note")}

    mirror.setdefault("comments_count", len(comments))
    if reviews:
        mirror["reviews_count"] = len(reviews)   # B166 — provenance: how many of the corpus are Maps reviews
    mirror.setdefault("sample", comments[:10])
    mirror.setdefault("note", f"machine-built {days[-1].name} from {len(comments)} comments")
    if not comments:
        mirror["machine_note"] = "no comments in latest extraction — mirror is blind, ask the client"
        from organ_write import write_organ
        write_organ(mf, mirror)
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
    from organ_write import write_organ
    write_organ(mf, mirror)
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
