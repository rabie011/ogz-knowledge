#!/usr/bin/env python3
"""REAL-ENGAGEMENT JOIN (June 18) — the bedrock. Every "engagement"/"lift" number in the system is
computed off the LLM-guessed `quality_assessment.engagement_potential` enum (ENG_MAP, 102 scripts).
But we have REAL likes/comments/views on disk. This joins them to the 6,888 observations by
shortcode, normalizes likes by the account's followers (so brands of different size compare), and
writes data/real_engagement_per_obs.json — the true target the analytics should run on.
Zero API, pure stdlib. Also reports how well the LLM enum actually predicted real engagement.
Usage: python3 scripts/build_real_engagement.py
"""
import glob, json, re
from pathlib import Path

B = Path(__file__).parent.parent
OBS = sorted(glob.glob(str(B / "11_who_to_learn_from/observations/*/*.json")))
OUT = B / "data/real_engagement_per_obs.json"
_SC = re.compile(r"/p/([^/?]+)")


def _norm(h):
    return (h or "").lower().lstrip("@").strip()


def build_engagement_lookup():
    """shortcode → {likes, comments, views, is_video, handle} from every real source on disk."""
    eng, followers = {}, {}
    # 1. full_extraction (cleanest: likes/comments_count/play_count/view_count + profile.followersCount)
    for f in glob.glob(str(B / "11_who_to_learn_from/_inbox/*/*_full_extraction.json")):
        d = json.loads(Path(f).read_text())
        h = _norm((d.get("profile") or {}).get("username") or Path(f).parent.name)
        fc = (d.get("profile") or {}).get("followersCount") or (d.get("profile") or {}).get("followers")
        if fc:
            followers[h] = fc
        for p in d.get("posts", []):
            sc = p.get("shortcode") or p.get("shortCode")
            if sc and isinstance(p.get("likes"), int):
                eng[sc] = {"likes": p["likes"], "comments": p.get("comments_count"),
                           "views": p.get("view_count") or p.get("play_count"),
                           "is_video": p.get("is_video"), "handle": h, "src": "full_extraction"}
    # 2. apify_raw + client posts.jsonl (likesCount/shortCode) — fill accounts full_extraction lacks
    for f in glob.glob(str(B / "11_who_to_learn_from/_raw_archive/*/*/*apify_raw.jsonl")) + \
             glob.glob(str(B / "clients/*/raw/instagram/*/posts.jsonl")):
        for line in Path(f).read_text().splitlines():
            try:
                p = json.loads(line)
            except Exception:
                continue
            sc = p.get("shortCode") or p.get("shortcode")
            if sc and sc not in eng and isinstance(p.get("likesCount"), int):
                eng[sc] = {"likes": p["likesCount"], "comments": p.get("commentsCount"),
                           "views": p.get("videoViewCount") or p.get("videoPlayCount"),
                           "is_video": p.get("type") == "Video", "handle": _norm(p.get("ownerUsername")),
                           "src": "apify_raw"}
    # followers from any profile.json we can find
    for f in glob.glob(str(B / "clients/*/raw/instagram/*/profile.json")):
        try:
            pr = json.loads(Path(f).read_text()); h = _norm(pr.get("username"))
            if h and pr.get("followersCount"):
                followers.setdefault(h, pr["followersCount"])
        except Exception:
            pass
    return eng, followers


def main():
    eng, followers = build_engagement_lookup()
    print(f"  real-engagement lookup: {len(eng)} posts w/ real likes · {len(followers)} accounts w/ followers")
    out, matched, enum_pairs = {}, 0, []
    for of in OBS:
        try:
            o = json.loads(Path(of).read_text())
        except Exception:
            continue
        cr = o.get("content_ref") or {}
        sc = None
        m = _SC.search(cr.get("source_url") or "")
        if m:
            sc = m.group(1)
        elif cr.get("filename"):
            sc = cr["filename"].split("_")[0].split(".")[0]
        if not sc or sc not in eng:
            continue
        e = eng[sc]
        h = e["handle"] or _norm(o.get("account_handle_normalized"))
        fol = followers.get(h)
        rate = round(e["likes"] / fol, 5) if fol else None
        ulid = o.get("observation_ulid")
        enum = (o.get("quality_assessment") or {}).get("engagement_potential")
        out[ulid] = {"shortcode": sc, "handle": h, "likes": e["likes"], "comments": e["comments"],
                     "views": e["views"], "is_video": e["is_video"], "followers": fol,
                     "eng_rate": rate, "llm_enum": enum, "src": e["src"]}
        matched += 1
        if rate is not None and enum:
            enum_pairs.append((rate, enum))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"  ✅ joined {matched}/{len(OBS)} obs to REAL engagement → {OUT.relative_to(B)}")
    # honesty check: did the LLM enum predict real engagement? (top-quartile rate vs enum=high/very_high)
    if enum_pairs:
        rates = sorted(r for r, _ in enum_pairs)
        q75 = rates[int(len(rates) * 0.75)]
        hi = [r for r, en in enum_pairs if en in ("high", "very_high")]
        hi_in_top = sum(1 for r in hi if r >= q75)
        base = sum(1 for r, _ in enum_pairs if r >= q75) / len(enum_pairs)
        prec = hi_in_top / len(hi) if hi else 0
        print(f"  ENUM vs REAL: of {len(hi)} posts the LLM called high/very_high, {round(prec*100)}% were "
              f"actually top-quartile (random baseline {round(base*100)}%) — n={len(enum_pairs)}")


if __name__ == "__main__":
    main()
