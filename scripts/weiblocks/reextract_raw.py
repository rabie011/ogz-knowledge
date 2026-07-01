#!/usr/bin/env python3
"""reextract_raw.py — deterministic re-extraction from the TRUE RAW SOURCE (Mohamed's order:
"look in the main source, extract and filter more").

The extracted-observation layer (6,888 obs) was built by an LLM extractor whose occasion vocabulary
missed real events (measured: mothers_day 14 real posts -> ~0 extracted; esports_world_cup 5 -> 0) and
which carried NO engagement numbers or hashtags — both of which EXIST in the raw Apify JSONL archive
(5,744 posts with numeric likesCount, 6,140 with timestamps, hashtags[] on every real row).

DeepSeek-ruled design (stamped b79a9974), with two disputed-and-corrected filters:
  - Output: ONE append-only enrichment overlay keyed by shortCode (source obs files never mutated).
  - Occasion detection: deterministic keyword banks (AR+EN+hashtags), NO timestamp gate (false-negative
    risk beats false-positive cost), occasion_method recorded.
  - Engagement: real likesCount/commentsCount coerced to int; -1/None = unavailable. Giveaway posts are
    FLAGGED (not dropped) and excluded from avg_likes only (they inflate it) — dispute of DeepSeek's
    drop-rule: giveaways are real brand behavior.
  - Carousels (Sidecar) are KEPT — dispute of DeepSeek's Image/Video-only rule: carousels are a huge
    share of real brand posts with real captions + likes.
  - Filtered OUT (junk only): error rows, rows with no caption AND no engagement, duplicate shortCodes
    (first wins in sorted-walk order), rows whose ownerUsername differs from the archive brand dir
    (coauthor/tagged-user noise; counted in the report).

Outputs (deterministic, sorted):
  data/weiblocks_enrichment/shortcode_enrichment.jsonl   one row per kept raw post
  data/weiblocks_enrichment/REEXTRACT_REPORT.json        totals, filters, occasion diff, per-sector hashtags
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "11_who_to_learn_from" / "_raw_archive"
OBS = ROOT / "11_who_to_learn_from" / "observations"
OUTDIR = ROOT / "data" / "weiblocks_enrichment"

# ── occasion keyword banks (conservative: explicit-name matches; generic words excluded) ──
BANKS = {
    "ramadan": [r"رمضان", r"\bramadan\b", r"إفطار", r"سحور", r"\biftar\b", r"\bsuhoor\b"],
    "eid_fitr": [r"عيد\s*الفطر", r"eid\s*al[- ]?fitr"],
    "eid_adha": [r"عيد\s*الأضحى", r"الأضحى", r"eid\s*al[- ]?adha", r"أضاحي"],
    "hajj_season": [r"\bالحج\b", r"حجاج", r"\bhajj\b", r"يوم\s*عرفة", r"arafah"],
    "national_day": [r"اليوم\s*الوطني", r"national\s*day", r"#اليوم_الوطني"],
    "founding_day": [r"يوم\s*التأسيس", r"#يوم_التأسيس", r"founding\s*day"],
    "mothers_day": [r"عيد\s*الأم", r"يوم\s*الأم", r"mother'?s\s*day", r"#عيد_الأم"],
    "white_friday": [r"الجمعة\s*البيضاء", r"white\s*friday", r"بلاك\s*فرايدي", r"black\s*friday"],
    "riyadh_season": [r"موسم\s*الرياض", r"riyadh\s*season", r"#موسم_الرياض"],
    "jeddah_season": [r"موسم\s*جدة", r"jeddah\s*season"],
    "esports_world_cup": [r"كأس\s*العالم\s*للرياضات", r"esports\s*world\s*cup", r"#esports\b", r"الرياضات\s*الإلكترونية"],
    "soundstorm": [r"ساوند\s*ستورم", r"soundstorm", r"mdl\s*beast", r"ميدل\s*بيست"],
    "singles_day": [r"11\.11", r"١١[.٫]١١", r"يوم\s*العزاب", r"singles.?\s*day"],
    "leap_conference": [r"مؤتمر\s*ليب", r"#leap\d*\b", r"leap\s*conference"],
}
COMPILED = {k: [re.compile(p, re.I) for p in pats] for k, pats in BANKS.items()}
GIVEAWAY = re.compile(r"giveaway|سحب\s*على|اسحب|راففل|raffle|تابع\s*وفز|شارك\s*واربح|win\s*a\b", re.I)
AR_TOKEN = re.compile(r"[؀-ۿ]")


def _int(v):
    try:
        n = int(str(v))
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def detect_occasions(text):
    hits = []
    for k in sorted(COMPILED):
        if any(p.search(text) for p in COMPILED[k]):
            hits.append(k)
    return hits


def obs_index():
    """shortCode -> (observation_ulid, sector, old_occasion) from the extracted layer."""
    idx = {}
    for fp in sorted(glob.glob(str(OBS / "*" / "*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        fn = (d.get("content_ref") or {}).get("filename") or ""
        sc = fn.rsplit(".", 1)[0]
        if sc:
            idx[sc] = (d.get("observation_ulid"), d.get("sector"), d.get("occasion"))
    return idx


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    idx = obs_index()
    rows, seen = [], set()
    filtered = Counter()
    for fp in sorted(glob.glob(str(RAW / "*" / "*" / "*_apify_raw.jsonl"))):
        brand_dir = Path(fp).parts[-3]
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                filtered["unparseable"] += 1
                continue
            if d.get("error"):
                filtered["error_row"] += 1
                continue
            sc = d.get("shortCode")
            if not sc:
                filtered["no_shortcode"] += 1
                continue
            if sc in seen:
                filtered["duplicate_shortcode"] += 1
                continue
            owner = (d.get("ownerUsername") or "").lower()
            if owner and owner != brand_dir.lower():
                filtered["owner_mismatch"] += 1
                continue
            cap = d.get("caption") or ""
            likes, comments = _int(d.get("likesCount")), _int(d.get("commentsCount"))
            if not cap and likes is None and comments is None:
                filtered["dead_row"] += 1
                continue
            seen.add(sc)
            o_ulid, o_sector, o_occ = idx.get(sc, (None, None, None))
            rows.append({
                "shortCode": sc, "brand": brand_dir,
                "timestamp": d.get("timestamp"),
                "likesCount": likes, "commentsCount": comments,
                "hashtags": sorted(set(h for h in (d.get("hashtags") or []) if h)),
                "occasions_detected": detect_occasions(cap),
                "is_giveaway": bool(GIVEAWAY.search(cap)),
                "observation_ulid": o_ulid, "obs_sector": o_sector, "obs_occasion_old": o_occ,
            })
    rows.sort(key=lambda r: (r["brand"], r["shortCode"]))
    with open(OUTDIR / "shortcode_enrichment.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    # ── report: occasion recovery diff + per-sector REAL hashtags ──
    joined = [r for r in rows if r["observation_ulid"]]
    recovery = Counter()
    for r in joined:
        for k in r["occasions_detected"]:
            if (r["obs_occasion_old"] or "").lower() not in (k, k.replace("_", " ")):
                recovery[k] += 1
    sector_tags = {}
    for r in joined:
        sec = r["obs_sector"]
        if not sec:
            continue
        bag = sector_tags.setdefault(sec, Counter())
        for h in r["hashtags"]:
            if AR_TOKEN.search(h):
                bag["#" + h.lstrip("#")] += 1
    report = {
        "raw_files": len(sorted(glob.glob(str(RAW / "*" / "*" / "*_apify_raw.jsonl")))),
        "kept": len(rows), "joined_to_observations": len(joined),
        "filtered": dict(sorted(filtered.items())),
        "with_numeric_likes": sum(1 for r in rows if r["likesCount"] is not None),
        "giveaways_flagged": sum(1 for r in rows if r["is_giveaway"]),
        "occasion_posts_detected": dict(sorted(Counter(k for r in rows for k in r["occasions_detected"]).items())),
        "occasion_recovered_vs_old_extraction": dict(sorted(recovery.items())),
        "sector_real_hashtags_top12": {
            s: [{"tag": t, "count": n} for t, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:12]]
            for s, c in sorted(sector_tags.items())},
    }
    json.dump(report, open(OUTDIR / "REEXTRACT_REPORT.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2, sort_keys=True)
    print(f"kept {len(rows)} raw posts ({len(joined)} join to observations) · filtered {dict(filtered)}")
    print(f"occasions detected: {report['occasion_posts_detected']}")
    print(f"RECOVERED vs old extraction: {report['occasion_recovered_vs_old_extraction']}")


if __name__ == "__main__":
    main()
