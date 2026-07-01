#!/usr/bin/env python3
"""build_brand_observations.py — aggregate 6,888 real observations -> Weiblocks §5.7 brand_observation
(NDJSON) + back-populate reference_accounts.observation_ids (Rule #6: writer + reader, same step).

DeepSeek-reasoner ruled (W2 Step 2, stamped consults b827dd30 / 8f17b7a1):
  1. GRAIN = per-brand aggregate (~110 records). The shape's plural fields (occasions_seen[],
     recurring_phrases_ar[], example_captions[]) require aggregation; a single raw obs can't fill them.
  2. PERFORMANCE = avg_likes:null, verified:false, metrics_source:"qualitative_inference" (we have NO
     numeric likes — only quality_assessment.engagement_potential low/med/high) + best_content_types
     computed from content_pillar frequency.
  3. PRIVACY — drop source_url, provenance.source (real handle), filename, capture_date. Only the anon
     brand_code + observation_ulids identify.
  4. example_captions = verbatim real caption_text (the core tone/occasion signal), cap 12/brand.
  5. confidence = "inferred" (claude_code_extraction; not human/metric-verified).
  recurring_phrases_ar = top-5 aggregated notable_phrases. reference_account.observation_ids = grouped
  raw observation_ulids per brand.

Dialect folded to spec's 4 (Mohamed's ruling): eastern→Khaleeji, msa→Fusha; dominant is picked among
FOLD-MAPPABLE tokens only (non_arabic/unknown/mixed/saudi never outvote a real dialect); a brand with
NO mappable token is held (dialect=null, full dist in extra). Native Arabic raw (ensure_ascii=False).
"""
import glob
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from occasion_keys import normalize as occ_normalize, normalize_list as occ_normalize_list  # THE shared join module — never a local map

ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "11_who_to_learn_from" / "observations"
ACC = ROOT / "11_who_to_learn_from" / "accounts"
OUT = ROOT / "exports" / "weiblocks_v1"
ENRICH = ROOT / "data" / "weiblocks_enrichment" / "shortcode_enrichment.jsonl"
DATE_ADDED = "2026-07-01"
# full slug map (observations use granular slugs). Anything NOT here — fashion, healthcare_wellness,
# real_estate (unshipped/held) — retags to Other, flagged provisional (panel-ruled: real market
# observations, kept but not pretending to be a baselined sector).
SECTOR_MAP = {"f_and_b": "F&B", "beauty_personal_care": "Beauty_Wellness", "beauty": "Beauty_Wellness",
              "retail_lifestyle": "Retail", "retail": "Retail"}
SECTOR_ABBR = {"f_and_b": "FB", "beauty": "BEAUTY", "retail": "RETAIL"}
_ANON_RE = re.compile(r"^OGZ-.+-Reference-\d+$")


def load_enrichment():
    """shortCode -> RAW-LAYER truth re-extracted from _raw_archive (reextract_raw.py, DeepSeek-ruled
    b79a9974): real likesCount/commentsCount, real hashtags[], deterministically keyword-detected
    occasions, giveaway flag. The extracted-obs layer missed these; the raw layer carries them."""
    m = {}
    if ENRICH.exists():
        for line in open(ENRICH, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                m[r["shortCode"]] = r
    return m


def load_handle_map():
    """real IG handle -> existing anon code (from the 110 account records). Covers ~15 of the
    45 real-handle observation brands; the rest get a deterministic hash code."""
    m = {}
    for f in sorted(glob.glob(str(ACC / "*" / "account_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        hi, an = d.get("account_handle_internal"), d.get("account_handle_normalized")
        if hi and an:
            m[hi] = an
    return m


def anonymize(raw_code, sector, handle_map):
    """DeepSeek W2S2-privacy: (1) already-anon stays; (2) real handle with a reference mapping uses
    that anon code (graph joins reference_account); (3) unmapped real handle -> deterministic one-way
    hash. The real handle is NEVER stored or emitted."""
    if _ANON_RE.match(raw_code):
        return raw_code
    if raw_code in handle_map:
        return handle_map[raw_code]
    h = hashlib.sha256(raw_code.lower().encode()).hexdigest()[:8].upper()
    return f"OGZ-{SECTOR_ABBR.get(sector, str(sector).upper())}-OBS-{h}"


def scrub(text, handles):
    """strip a brand's own real handle token from its caption (residual-leak guard). Replaces @handle
    and word-boundary handle occurrences (case-insensitive) with [brand]."""
    if not text:
        return text
    for h in handles:
        if not h or _ANON_RE.match(h):
            continue
        text = re.sub(r"@?" + re.escape(h), "[brand]", text, flags=re.IGNORECASE)
    return text


# P0 PRIVACY (audit worst finding): 73 distinct THIRD-PARTY @handles — real private individuals —
# leaked verbatim inside example_captions after the own-handle scrub. Strip ALL remaining @-mentions.
_MENTION_RE = re.compile(r"@[A-Za-z0-9_.]{2,30}")   # the IG-handle charset (all measured leaks match)
_MENTION_ANY_RE = re.compile(r"@[\w.]+")            # unicode catch-all guard (DeepSeek C-consult: future-proof)


def scrub_mentions(text):
    """replace every remaining @-mention with [mention] (applied AFTER own-handle scrub)."""
    if not text:
        return text
    text = _MENTION_RE.sub("[mention]", text)
    return _MENTION_ANY_RE.sub("[mention]", text)


# extractor-prose artifacts: the phrase extractor sometimes emitted its own narration
# ("Two key Arabic phrases: …" — 525 distinct in the raw corpus) instead of caption content.
_AR_SCRIPT_RE = re.compile(r"[؀-ۿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_PROSE_COLON_RE = re.compile(r"^[A-Za-z]+(?: [A-Za-z]+){2,}\s*:")  # >=3 English words then a colon


def is_extractor_prose(p):
    """True = extractor narration / non-phrase junk — filtered from the phrase counter at ingest.
    Patterns (panel-ruled): contains 'arabic phrase' (525 real artifacts); English-prose-colon prefix
    before Arabic (0 extra hits today, guards the shape); len>60 mixed-script (sentence-length
    bilingual copy — not a recurring PHRASE; 48 real hits, eyeballed)."""
    if not p:
        return True
    if "arabic phrase" in p.lower():
        return True
    if _PROSE_COLON_RE.match(p) and _AR_SCRIPT_RE.search(p):
        return True
    if len(p) > 60 and _AR_SCRIPT_RE.search(p) and _LATIN_RE.search(p):
        return True
    return False


DIALECT_FOLD = {"najdi": "Najdi", "hijazi": "Hejazi", "hejazi": "Hejazi", "khaleeji": "Khaleeji",
                "eastern": "Khaleeji", "khaleeji_neutral": "Khaleeji", "msa": "Fusha (MSA)",
                "fusha": "Fusha (MSA)", "standard": "Fusha (MSA)"}
CAP_CAPTIONS = 12
TOP_PHRASES = 5


def _top(counter, n, min_len=0):
    # deterministic tie-break: count desc, then key asc (ties never depend on insertion order)
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return [k for k, _ in ranked if k and len(str(k)) >= min_len][:n]


def _dom(counter):
    """deterministic single most-common (count desc, key asc). None if empty."""
    if not counter:
        return None
    return sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))[0][0]


def spread_captions(rows):
    """up to 12 captions spread across occasions (round-robin by raw occasion for balance).
    Emitted occasion = shared occasion_keys.normalize key or null; unresolved raw token kept
    honest in sibling occasion_source (never a fabricated 'evergreen' when the source had none)."""
    by_occ = {}
    for cap, occ, perf in rows:
        by_occ.setdefault(occ or "evergreen", []).append((cap, occ, perf))
    out, i = [], 0
    while len(out) < CAP_CAPTIONS and any(by_occ.values()):
        for group in list(by_occ):
            if by_occ[group]:
                cap, raw_occ, perf = by_occ[group].pop(0)
                key, orig = occ_normalize(raw_occ)
                entry = {"text_ar": cap, "occasion": key, "performed": perf or "unknown"}
                if key is None and orig is not None and str(orig).strip():
                    entry["occasion_source"] = orig    # unresolved raw token, kept for provenance
                out.append(entry)
                if len(out) >= CAP_CAPTIONS:
                    break
        i += 1
        if i > 50:
            break
    return out


def build():
    handle_map = load_handle_map()
    enrich = load_enrichment()
    brands = {}  # ANON brand_code -> aggregation buckets
    for fp in sorted(glob.glob(str(OBS / "*" / "*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        raw = d.get("account_handle_normalized")
        if not raw:
            continue
        sector = d.get("sector")
        bc = anonymize(raw, sector, handle_map)  # group by ANON code (merges dup real/anon of same brand)
        b = brands.setdefault(bc, {
            "sector": sector, "ulids": [], "occasions": Counter(), "tones": Counter(),
            "phrases": Counter(), "dialects": Counter(), "palette": Counter(), "composition": Counter(),
            "lighting": Counter(), "pillars": Counter(), "engagement": Counter(), "emoji": [], "caps": [],
            "raw_handles": set(),
            "raw_likes": [], "raw_hashtags": Counter(), "occ_detected": Counter(), "raw_joined": 0,
        })
        # ── RAW-LAYER JOIN (shortCode) — real engagement + detected occasions + real hashtags ──
        _sc = ((d.get("content_ref") or {}).get("filename") or "").rsplit(".", 1)[0]
        _er = enrich.get(_sc)
        if _er:
            b["raw_joined"] += 1
            if _er.get("likesCount") is not None and not _er.get("is_giveaway"):
                b["raw_likes"].append(_er["likesCount"])   # giveaways excluded: they inflate avg_likes
            for _h in (_er.get("hashtags") or []):
                b["raw_hashtags"]["#" + _h.lstrip("#")] += 1
            for _k in (_er.get("occasions_detected") or []):
                b["occ_detected"][_k] += 1
        if not _ANON_RE.match(raw):
            b["raw_handles"].add(raw)
        vo = d.get("voice_observations") or {}
        vi = d.get("visual_observations") or {}
        qa = d.get("quality_assessment") or {}
        b["ulids"].append(d.get("observation_ulid"))
        if d.get("occasion"):
            b["occasions"][d["occasion"]] += 1
        if vo.get("tone"):
            b["tones"][vo["tone"]] += 1
        for p in (vo.get("notable_phrases") or []):
            if is_extractor_prose(p):    # extractor narration never enters the counter
                continue
            b["phrases"][p] += 1
        if vo.get("dialect_detected"):
            b["dialects"][vo["dialect_detected"]] += 1
        for c in (vi.get("color_palette_dominant") or []):
            b["palette"][c] += 1
        if vi.get("composition_style"):
            b["composition"][vi["composition_style"]] += 1
        if vi.get("lighting"):
            b["lighting"][vi["lighting"]] += 1
        if d.get("content_pillar"):
            b["pillars"][d["content_pillar"]] += 1
        if qa.get("engagement_potential"):
            b["engagement"][qa["engagement_potential"]] += 1
        b["emoji"].append(bool(vo.get("has_emoji")))
        cap = vo.get("caption_text")
        if cap:
            b["caps"].append((cap, d.get("occasion"), qa.get("engagement_potential")))

    records, brand_ulids = [], {}
    for bc, b in sorted(brands.items()):
        n = len(b["ulids"])
        brand_ulids[bc] = b["ulids"]
        # dialect-null bug fix: pick dominant among FOLD-MAPPABLE keys only — non_arabic/unknown/mixed
        # counts must never outvote a real dialect (najdi:17 was folding to null under non_arabic:58).
        mappable = Counter({k: v for k, v in b["dialects"].items() if k in DIALECT_FOLD})
        dom_dialect_raw = _dom(mappable)
        dialect = DIALECT_FOLD.get(dom_dialect_raw)  # None => NO mappable dialect observed (saudi/mixed/non_arabic-only held)
        emoji_ratio = (sum(b["emoji"]) / len(b["emoji"])) if b["emoji"] else 0
        emoji = "frequent" if emoji_ratio > 0.6 else ("moderate" if emoji_ratio > 0.2 else "sparing")
        rh = b["raw_handles"]
        sk = SECTOR_MAP.get(b["sector"], "Other")   # unshipped/held raw slug -> Other (graph stays consistent)
        provisional = sk == "Other"                 # True = observed brand, sector not baselined
        ex_caps = spread_captions(b["caps"])
        for c in ex_caps:
            # own-handle scrub first ([brand]), then ALL third-party @-mentions ([mention]) — P0 privacy
            c["text_ar"] = scrub_mentions(scrub(c["text_ar"], rh))
        phrases = [scrub_mentions(scrub(p, rh)) for p in _top(b["phrases"], TOP_PHRASES)]
        # occasion keys via THE shared module: resolved spec keys only; unresolved originals -> extra
        occ_keys, occ_unresolved = occ_normalize_list(sorted(b["occasions"]))
        # RAW-RECOVERED occasions (deterministic keyword detection over raw captions) union in;
        # detector bank keys ARE spec occasion_keys. Recovered-only keys reported in extra.
        occ_recovered = sorted(set(b["occ_detected"]) - set(occ_keys))
        occ_keys = sorted(set(occ_keys) | set(b["occ_detected"]))
        # REAL engagement from the raw layer: mean likes over non-giveaway numeric posts; verified
        # becomes TRUE only with a real sample (>=5 posts) — DeepSeek-ruled b79a9974.
        _likes = b["raw_likes"]
        _has_real = len(_likes) >= 5
        records.append({
            "id": f"bobs_{bc}",
            "entity": "brand_observation",
            "brand_code": bc,
            "sector_key": sk,
            "dialect": dialect,
            "voice_signals": {
                "tone": _top(b["tones"], 3),
                "recurring_phrases_ar": phrases,
                "emoji": emoji,
            },
            "visual_signals": {
                "palette": _top(b["palette"], 6),
                "composition": _top(b["composition"], 4),
                "lighting": _dom(b["lighting"]),
            },
            "performance": {
                "metrics_source": "apify_scrape" if _has_real else "qualitative_inference",
                "avg_likes": (round(sum(_likes) / len(_likes)) if _has_real else None),
                "best_content_types": _top(b["pillars"], 3),
                "verified": _has_real,           # TRUE only when backed by >=5 real scraped like-counts
                "qualitative_engagement": _dom(b["engagement"]),
                "engagement_sample_size": (len(_likes) if _has_real else None),
            },
            "occasions_seen": occ_keys,              # spec occasion_key values only (joins resolve)
            "example_captions": ex_caps,
            "provenance": {
                "source": "apify_scrape",          # underlying content scraped; extraction by claude
                "confidence": "inferred",           # claude_code_extraction, not human/metric-verified
                "observed_count": n,                # REAL count of observations aggregated (honest)
                "date_added": DATE_ADDED,
                "scope": f"sector:{sk}+brand:{bc}",
            },
            "extra": {
                "source_label": b["sector"],
                "provisional_sector": provisional,  # True => raw sector not shipped, retagged Other
                "dialect_source": dom_dialect_raw,               # dominant MAPPABLE raw token before fold (None = held)
                "dialect_distribution": dict(b["dialects"]),     # full raw distribution, nothing hidden
                "occasion_distribution": dict(b["occasions"]),   # full raw token distribution
                "occasions_unresolved": occ_unresolved,          # raw tokens that map to no shipped occasion_key
                "performed_basis": "engagement_potential_inference",  # 'performed' = qualitative inference, NOT a measured metric
                "raw_posts_joined": b["raw_joined"],             # raw-archive posts joined by shortCode
                "occasions_recovered_from_raw": occ_recovered,   # keys the old extraction missed entirely
                "top_hashtags": [h for h, _ in sorted(b["raw_hashtags"].items(), key=lambda kv: (-kv[1], kv[0]))[:8]],
                "observation_ulids": b["ulids"],                 # drill-down (also feeds reference_account)
                # PRIVACY: source_url, real handle, filename, capture_date DELIBERATELY EXCLUDED.
            },
        })

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "brand_observations.ndjson", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} brand_observations (NDJSON) from {sum(len(v) for v in brand_ulids.values())} obs")

    # Rule #6 — back-populate the reader (reference_account.observation_ids) in the same step
    refp = OUT / "reference_accounts.json"
    if refp.exists():
        refs = json.load(open(refp, encoding="utf-8"))
        linked = 0
        for r in refs:
            ids = brand_ulids.get(r.get("brand_code"))
            if ids:
                r["observation_ids"] = ids
                linked += 1
        json.dump(refs, open(refp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"back-populated observation_ids on {linked}/{len(refs)} reference_accounts")
    return records


if __name__ == "__main__":
    build()
