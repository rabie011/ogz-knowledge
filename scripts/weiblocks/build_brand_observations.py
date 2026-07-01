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

Dialect folded to spec's 4 (Mohamed's ruling): eastern→Khaleeji, msa→Fusha, mixed/saudi/other→held
(dialect=null, original dist in extra). Native Arabic raw (NDJSON, ensure_ascii=False per line).
"""
import glob
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "11_who_to_learn_from" / "observations"
ACC = ROOT / "11_who_to_learn_from" / "accounts"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"
SECTOR_MAP = {"f_and_b": "F&B", "beauty": "Beauty_Wellness", "retail": "Retail"}
SECTOR_ABBR = {"f_and_b": "FB", "beauty": "BEAUTY", "retail": "RETAIL"}
_ANON_RE = re.compile(r"^OGZ-.+-Reference-\d+$")


def load_handle_map():
    """real IG handle -> existing anon code (from the 110 account records). Covers ~15 of the
    45 real-handle observation brands; the rest get a deterministic hash code."""
    m = {}
    for f in glob.glob(str(ACC / "*" / "account_*.json")):
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
DIALECT_FOLD = {"najdi": "Najdi", "hijazi": "Hejazi", "hejazi": "Hejazi", "khaleeji": "Khaleeji",
                "eastern": "Khaleeji", "khaleeji_neutral": "Khaleeji", "msa": "Fusha (MSA)",
                "fusha": "Fusha (MSA)", "standard": "Fusha (MSA)"}
CAP_CAPTIONS = 12
TOP_PHRASES = 5


def _top(counter, n, min_len=0):
    return [k for k, _ in counter.most_common() if k and len(str(k)) >= min_len][:n]


def spread_captions(rows):
    """up to 12 captions spread across occasions (round-robin by occasion)."""
    by_occ = {}
    for cap, occ, perf in rows:
        by_occ.setdefault(occ or "evergreen", []).append((cap, perf))
    out, i = [], 0
    while len(out) < CAP_CAPTIONS and any(by_occ.values()):
        for occ in list(by_occ):
            if by_occ[occ]:
                cap, perf = by_occ[occ].pop(0)
                out.append({"text_ar": cap, "occasion": occ, "performed": perf or "unknown"})
                if len(out) >= CAP_CAPTIONS:
                    break
        i += 1
        if i > 50:
            break
    return out


def build():
    handle_map = load_handle_map()
    brands = {}  # ANON brand_code -> aggregation buckets
    for fp in glob.glob(str(OBS / "*" / "*.json")):
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
        })
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
        dom_dialect_raw = b["dialects"].most_common(1)[0][0] if b["dialects"] else None
        dialect = DIALECT_FOLD.get(dom_dialect_raw)  # None => held (mixed/saudi/other)
        emoji_ratio = (sum(b["emoji"]) / len(b["emoji"])) if b["emoji"] else 0
        emoji = "frequent" if emoji_ratio > 0.6 else ("moderate" if emoji_ratio > 0.2 else "sparing")
        rh = b["raw_handles"]
        ex_caps = spread_captions(b["caps"])
        for c in ex_caps:
            c["text_ar"] = scrub(c["text_ar"], rh)   # residual-leak guard: strip own handle from captions
        phrases = [scrub(p, rh) for p in _top(b["phrases"], TOP_PHRASES)]
        records.append({
            "id": f"bobs_{bc}",
            "entity": "brand_observation",
            "brand_code": bc,
            "sector_key": SECTOR_MAP.get(b["sector"], b["sector"]),
            "dialect": dialect,
            "voice_signals": {
                "tone": _top(b["tones"], 3),
                "recurring_phrases_ar": phrases,
                "emoji": emoji,
            },
            "visual_signals": {
                "palette": _top(b["palette"], 6),
                "composition": _top(b["composition"], 4),
                "lighting": (b["lighting"].most_common(1)[0][0] if b["lighting"] else None),
            },
            "performance": {
                "metrics_source": "qualitative_inference",
                "avg_likes": None,               # NO numeric engagement in source — honest null
                "best_content_types": _top(b["pillars"], 3),
                "verified": False,
                "qualitative_engagement": (b["engagement"].most_common(1)[0][0] if b["engagement"] else None),
            },
            "occasions_seen": sorted(b["occasions"]),
            "example_captions": ex_caps,
            "provenance": {
                "source": "apify_scrape",          # underlying content scraped; extraction by claude
                "confidence": "inferred",           # claude_code_extraction, not human/metric-verified
                "observed_count": n,                # REAL count of observations aggregated (honest)
                "date_added": DATE_ADDED,
                "scope": f"sector:{SECTOR_MAP.get(b['sector'], b['sector'])}+brand:{bc}",
            },
            "extra": {
                "source_label": b["sector"],
                "dialect_source": dom_dialect_raw,               # original before fold
                "dialect_distribution": dict(b["dialects"]),
                "occasion_distribution": dict(b["occasions"]),
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
