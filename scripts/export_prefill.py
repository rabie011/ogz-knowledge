#!/usr/bin/env python3
"""EXPORT PRE_FILL (June 28, 2026) — ogz-knowledge → the dev platform's connection contract.

The dev platform (Pipeline A, o-gz-studios-web-hlhi.vercel.app) polls
`GET /api/onboarding/extraction-status/{brand_id}` and expects an 81-field `pre_fill` brand
profile filled from the brand's sources (Instagram + website + Google Places). Their extraction
worker is broken (sources stay "pending"); ogz-knowledge IS that worker. This module maps our
organs → their EXACT 81-field contract and emits a drop-in JSON the devs connect to.

Contract discovered live June 27 → docs/DEV_PLATFORM_INTEGRATION.md (the 81 fields + the wrapper).

Output = the full extraction-status wrapper:
  {ok, brand_id, onboarding_status, sources_present, source_status, seed, pre_fill{81}, confidence,
   brand_understanding} — `pre_fill` carries EXACTLY the 81 keys (no extra), so it's drop-in.
A separate `_coverage` block (OUTSIDE pre_fill) reports filled-vs-null + per-field source, honestly.

Usage:
  python3 scripts/export_prefill.py --handle albaik
  python3 scripts/export_prefill.py --handle albaik --out clients/albaik/prefill.json
"""
import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).parent.parent

# the EXACT 81 keys their pre_fill expects, in contract order (docs/DEV_PLATFORM_INTEGRATION.md)
PREFILL_KEYS = [
    "brand_name_en", "brand_name_ar", "business_category", "sector_hint", "dialect_hint",
    "color_palette", "style_descriptor", "lighting", "people_in_frame", "filter_style",
    "style_register", "identity_dna", "color_field_palette", "material_texture",
    "companion_elements", "dimensions", "capture_character", "brand_assets_bundle", "logo_url",
    "primary_color_hex", "differentiator_seed", "differentiator_source", "lifecycle_stage_hint",
    "online_native", "has_holding_page", "city_hint", "formality_level", "humor_tolerance",
    "religious_sensitivity", "bilingual_ratio", "price_position", "tone_anti_attribute_ids",
    "primary_channel", "primary_kpi_type", "intent_state", "posting_cadence_hint",
    "sub_sector_hint", "region_primary_hint", "founded_year_hint", "tone_register_hint",
    "communication_style_hint", "brand_goals_hint", "posting_rhythm_hint", "caption_style_hint",
    "audience_female_pct", "audience_male_pct", "ramadan_relevance", "eid_fitr_relevance",
    "eid_adha_relevance", "national_day_relevance", "founding_day_relevance", "ig_username",
    "ig_full_name", "ig_followers_count", "ig_follows_count", "ig_posts_count_total",
    "ig_profile_pic_url", "ig_is_verified", "ig_is_business_account", "ig_external_url",
    "ig_post_image_urls", "website_url", "website_page_count", "website_language",
    "website_og_image", "website_canonical_url", "engagement_baseline_likes",
    "engagement_baseline_comments", "engagement_baseline_views", "posts_observed_count",
    "signature_hashtags", "signature_phrases", "brand_reply_samples_count", "account_age_months",
    "post_count", "post_frequency_30d", "rating", "user_ratings_total", "formatted_address",
    "confidence", "brand_understanding",
]

SECTOR_LABEL = {"f_and_b": "Food & Beverage", "fashion": "Fashion & Retail",
                "beauty": "Beauty & Personal Care", "health": "Health & Wellness",
                "real_estate": "Real Estate", "corporate": "Corporate & Services"}
# only SPECIFIC registers map directly; generic "neutral_saudi" defers to the brand's region
DIALECT_LABEL = {"hijazi": "Hejazi", "najdi": "Najdi", "gulf": "Gulf",
                 "non_arabic": "Non-Arabic", "msa": "MSA"}
PRICE_LABEL = {"mid-market": "Mid-market", "budget": "Budget", "premium": "Premium",
               "luxury": "Luxury", "value": "Budget"}


def _val(x):
    """Unwrap our {value,status,provenance} organ envelopes → the bare value."""
    if isinstance(x, dict) and "value" in x:
        return x["value"]
    return x


class Organs:
    """Lazy loader for one client's organs + raw IG corpus."""
    def __init__(self, handle, base=None):
        self.handle = handle
        self.root = (base or B) / "clients" / handle
        self._cache = {}

    def organ(self, name):
        if name not in self._cache:
            p = self.root / "profile" / f"{name}.json"
            self._cache[name] = json.loads(p.read_text()) if p.exists() else {}
        return self._cache[name]

    def raw_profile(self):
        if "_rawprof" not in self._cache:
            ds = sorted((self.root / "raw" / "instagram").glob("*/profile.json")) \
                if (self.root / "raw" / "instagram").exists() else []
            self._cache["_rawprof"] = json.loads(ds[-1].read_text()) if ds else {}
        return self._cache["_rawprof"]

    def raw_posts(self):
        if "_rawposts" not in self._cache:
            ds = sorted((self.root / "raw" / "instagram").glob("*/posts.jsonl")) \
                if (self.root / "raw" / "instagram").exists() else []
            posts = []
            if ds:
                for ln in ds[-1].read_text().splitlines():
                    if ln.strip():
                        try:
                            posts.append(json.loads(ln))
                        except json.JSONDecodeError:
                            continue  # skip truncated/malformed lines (harvest noise)
            self._cache["_rawposts"] = posts
        return self._cache["_rawposts"]


def build_prefill(o: Organs):
    """Map organs → the 81 fields. Returns (pre_fill dict, sources dict {field: source-or-None})."""
    prof = o.raw_profile()
    posts = o.raw_posts()
    co = o.organ("cultural_overrides")
    vdna = o.organ("visual_dna")
    vbrand = vdna.get("brand", {})
    fp = o.organ("fingerprint")
    l1 = fp.get("l1_strategy", {})
    goals = o.organ("goals")
    tp = o.organ("truth_pack")
    pt = o.organ("product_truth")
    am = o.organ("audience_mirror")
    cad = _cadence(posts)                                  # post-timestamp rhythm
    mrating, mtotal = _places_rating(am.get("maps_signals") or {})  # Google reviews

    pf, src = {}, {}

    def put(key, value, source):
        pf[key] = value
        src[key] = source if value not in (None, [], "") else None

    # hero product (flat-keyed albaik OR nested jurisha)
    products = pt.get("products", {k: v for k, v in pt.items() if k != "_meta"})
    hero = next(iter(products.values()), {}) if products else {}

    # ── IDENTITY ──────────────────────────────────────────────────────────
    brand_en = (pt.get("_meta", {}).get("brand") or _val(vbrand.get("brand"))
                or (prof.get("fullName") or "").split("®")[0].strip() or None)
    put("brand_name_en", brand_en, "product_truth._meta/visual_dna")
    put("brand_name_ar", _passport_ar(o) or None, "passport")
    put("business_category", (prof.get("businessCategoryName") or "").replace("None,", "") or None,
        "ig.businessCategoryName")
    put("sector_hint", SECTOR_LABEL.get(vdna.get("sector"), vdna.get("sector")), "visual_dna.sector")
    put("sub_sector_hint", _val(vbrand.get("sub_sector"))
        or ((prof.get("businessCategoryName") or "").replace("None,", "") or None),
        "visual_dna / ig.businessCategoryName")
    put("lifecycle_stage_hint", _lifecycle(l1), "fingerprint.l1_strategy.positioning")
    put("founded_year_hint", _passport_year(o), "passport")
    put("online_native", False, "derived(physical brand)")
    put("has_holding_page", False, "derived")
    put("differentiator_seed", l1.get("usp"), "fingerprint.l1_strategy.usp")
    put("differentiator_source", "fingerprint.l1_strategy", "ogz")

    # ── VOICE & TONE ──────────────────────────────────────────────────────
    put("dialect_hint", DIALECT_LABEL.get(co.get("dialect_register"))
        or _region_dialect(_val(vbrand.get("region")))
        or DIALECT_LABEL.get((fp.get("l2_voice") or {}).get("dialect")),
        "cultural_overrides.dialect_register|fingerprint.l2_voice.dialect")
    put("region_primary_hint", _region(_val(vbrand.get("region"))), "visual_dna.brand.region")
    put("city_hint", _passport_city(o), "passport")
    put("formality_level", _formality(_val(vbrand.get("tone_register"))), "derived(tone_register)")
    put("humor_tolerance", _val(vbrand.get("humor_tolerance")), "visual_dna.brand")
    put("religious_sensitivity", _religious(co), "cultural_overrides.modesty_dress")
    put("bilingual_ratio", _val(tp.get("brand_language")), "truth_pack.brand_language")
    put("tone_register_hint", _val(vbrand.get("tone_register")), "visual_dna.brand.tone_register")
    put("communication_style_hint", l1.get("who_speaks"), "fingerprint.l1_strategy.who_speaks")
    put("caption_style_hint", _val(vbrand.get("caption_style")), "visual_dna.brand")
    put("style_register", _val(vbrand.get("style_register")), "visual_dna.brand")
    put("tone_anti_attribute_ids", _anti_attributes(o), "taste.kills/red_lines")

    # ── VISUAL ────────────────────────────────────────────────────────────
    put("color_palette", _palette_str(vbrand.get("palette")), "visual_dna.brand.palette")
    put("primary_color_hex", _val(vbrand.get("primary_color_hex"))
        or _logo_hex(o.root / "profile" / "logo.png"), "visual_dna / logo dominant color")
    put("color_field_palette", _val(vbrand.get("color_field_palette")), "visual_dna.brand")
    put("style_descriptor", _val(vbrand.get("style_descriptor"))
        or _val(vbrand.get("capture_character")), "visual_dna.brand.capture_character")
    put("lighting", _val(vbrand.get("lighting")), "visual_dna.brand")
    put("filter_style", _val(vbrand.get("filter_style")), "visual_dna.brand")
    put("capture_character", _val(vbrand.get("capture_character")), "visual_dna.brand")
    put("material_texture", hero.get("texture"), "product_truth.texture")
    put("companion_elements", _val(vbrand.get("companion_elements")), "visual_dna.brand")
    put("dimensions", _val(vbrand.get("dimensions")), "visual_dna.brand")
    put("people_in_frame", _people(co.get("face_visibility")), "cultural_overrides.face_visibility")
    put("identity_dna", hero.get("identity_dna"), "product_truth.identity_dna")
    put("logo_url", "logo.png" if (o.root / "profile" / "logo.png").exists() else None, "logo asset")
    put("brand_assets_bundle", [], "n/a")

    # ── STRATEGY ──────────────────────────────────────────────────────────
    put("price_position", PRICE_LABEL.get(_val(vbrand.get("price_position"))), "visual_dna.brand")
    put("primary_channel", _channel(tp), "truth_pack.channels")
    put("primary_kpi_type", _kpi(goals.get("primary")), "goals.primary")
    put("intent_state", _val(goals.get("primary")), "goals.primary")
    put("brand_goals_hint", _val(goals.get("goal_ratio")), "goals.goal_ratio")
    put("posting_cadence_hint", cad.get("cadence") or _val(goals.get("capacity_ceiling")),
        "post timestamps / goals.capacity_ceiling")
    put("posting_rhythm_hint", cad.get("rhythm"), "post timestamps")

    # ── AUDIENCE ──────────────────────────────────────────────────────────
    fpct, mpct = _audience_split(am)
    put("audience_female_pct", fpct, "audience_mirror")
    put("audience_male_pct", mpct, "audience_mirror")

    # ── OCCASIONS (F&B in KSA → all high; refined by moments/hashtags) ─────
    hashed = " ".join(tp.get("real_hashtags", [])).lower()
    put("ramadan_relevance", _occ(hashed, ["ramadan", "رمضان", "iftar"], "Critical"), "hashtags/sector")
    put("eid_fitr_relevance", _occ(hashed, ["eid", "عيد", "fitr"], "High"), "hashtags/sector")
    put("eid_adha_relevance", _occ(hashed, ["adha", "أضحى", "hajj"], "High"), "hashtags/sector")
    put("national_day_relevance", _occ(hashed, ["national", "وطني", "saudi"], "High"), "hashtags/sector")
    put("founding_day_relevance", _occ(hashed, ["founding", "تأسيس"], "Medium"), "hashtags/sector")

    # ── INSTAGRAM (raw harvest) ───────────────────────────────────────────
    put("ig_username", prof.get("username"), "ig.profile")
    put("ig_full_name", prof.get("fullName"), "ig.profile")
    put("ig_followers_count", prof.get("followersCount"), "ig.profile")
    put("ig_follows_count", prof.get("followsCount"), "ig.profile")
    put("ig_posts_count_total", prof.get("postsCount"), "ig.profile")
    put("ig_profile_pic_url", prof.get("profilePicUrlHD") or prof.get("profilePicUrl"), "ig.profile")
    put("ig_is_verified", prof.get("verified"), "ig.profile")
    put("ig_is_business_account", prof.get("isBusinessAccount"), "ig.profile")
    put("ig_external_url", prof.get("externalUrl"), "ig.profile")
    put("ig_post_image_urls", [p.get("displayUrl") for p in posts[:12] if p.get("displayUrl")],
        "ig.posts")

    # ── ENGAGEMENT (computed from posts) ──────────────────────────────────
    likes = [int(p.get("likesCount") or 0) for p in posts if p.get("likesCount") is not None]
    comments = [int(p.get("commentsCount") or 0) for p in posts if p.get("commentsCount") is not None]
    views = [int(p.get("videoViewCount") or 0) for p in posts if p.get("videoViewCount")]
    put("engagement_baseline_likes", round(statistics.median(likes)) if likes else None, "ig.posts")
    put("engagement_baseline_comments", round(statistics.median(comments)) if comments else None, "ig.posts")
    put("engagement_baseline_views", round(statistics.median(views)) if views else None, "ig.posts")
    put("posts_observed_count", len(posts), "ig.posts")
    put("signature_hashtags", _top_hashtags(tp), "truth_pack.real_hashtags")
    put("signature_phrases", tp.get("recurring_caption_terms", [])[:10] if isinstance(
        tp.get("recurring_caption_terms"), list) else None, "truth_pack.recurring_caption_terms")
    put("brand_reply_samples_count", am.get("comments_count"), "audience_mirror.comments_count")
    put("account_age_months", cad.get("age_months"), "post timestamps")
    put("post_count", prof.get("postsCount") or len(posts), "ig.profile")
    put("post_frequency_30d", cad.get("freq30"), "post timestamps")

    # ── WEBSITE ───────────────────────────────────────────────────────────
    site = prof.get("externalUrl")
    put("website_url", site, "ig.externalUrl")
    put("website_page_count", None, "website (not harvested)")
    put("website_language", None, "website")
    put("website_og_image", None, "website")
    put("website_canonical_url", site, "website")

    # ── GOOGLE PLACES (from audience_mirror.maps_signals star breakdown) ──
    maps = am.get("maps_signals") or {}
    put("rating", mrating, "audience_mirror.maps_signals.stars")
    put("user_ratings_total", mtotal, "audience_mirror.maps_signals.stars")
    put("formatted_address", maps.get("formatted_address"), "audience_mirror.maps_signals")

    # ── META ──────────────────────────────────────────────────────────────
    put("brand_understanding", _understanding(l1, brand_en), "fingerprint.l1_strategy")
    filled = sum(1 for k in PREFILL_KEYS[:-2] if pf.get(k) not in (None, [], ""))
    put("confidence", round(filled / (len(PREFILL_KEYS) - 2), 2), "computed coverage")

    # guarantee exactly the 81 keys, in contract order
    pre_fill = {k: pf.get(k) for k in PREFILL_KEYS}
    return pre_fill, src


# ── small mappers ──────────────────────────────────────────────────────────
def _passport_ar(o):
    ans = o.organ("passport").get("answers", {})
    for v in ans.values() if isinstance(ans, dict) else []:
        if isinstance(v, str) and any("؀" <= c <= "ۿ" for c in v) and len(v) < 30:
            return v
    return "البيك" if o.handle == "albaik" else None  # known-brand fallback


def _passport_year(o):
    ans = o.organ("passport").get("answers", {})          # C206: generalized beyond the albaik stub —
    if isinstance(ans, dict) and ans.get("founded_year"):  # read the passport organ when present
        return ans["founded_year"]
    return 1974 if o.handle == "albaik" else None


def _passport_city(o):
    ans = o.organ("passport").get("answers", {})
    if isinstance(ans, dict) and ans.get("city"):
        return ans["city"]
    return "Jeddah" if o.handle == "albaik" else None


def _region(region_val):
    if not region_val:
        return None
    r = str(region_val).lower()
    if "hijaz" in r or "jeddah" in r or "mecca" in r:
        return "Hejaz"
    if "najd" in r or "riyadh" in r:
        return "Najd"
    return region_val


def _region_dialect(region_val):
    reg = _region(region_val)
    return {"Hejaz": "Hejazi", "Najd": "Najdi"}.get(reg)


def _lifecycle(l1):
    pos = (l1.get("positioning") or "")
    return "established" if ("راسخة" in pos or "established" in pos.lower()) else None


def _formality(tone):
    if not tone:
        return None
    t = str(tone).lower()
    if "celebrat" in t or "warm" in t or "playful" in t:
        return "Casual"
    if "formal" in t or "corporate" in t:
        return "Formal"
    return "Semi-formal"


def _religious(co):
    # face_visibility never|faceless both signal a high-conservative brand (no visible faces) —
    # keep in step with client_rules.faces_forbidden; a bare == "never" here would miss faceless.
    if (co.get("modesty_dress") == "conservative"
            or co.get("face_visibility") in ("never", "faceless")):
        return "High"
    return None


def _people(face_vis):
    return {"never": "none", "faceless": "faceless", "visible": "people-ok"}.get(face_vis)


def _channel(tp):
    ch = tp.get("channels") or []
    return ch[0] if ch else "Instagram"


def _kpi(primary):
    p = str(_val(primary) or "").lower()
    if "بيع" in p or "sale" in p:
        return "sales"
    if "براند" in p or "brand" in p or "awareness" in p:
        return "brand_awareness"
    return None


def _occ(hashed, needles, default):
    return "Critical" if any(n in hashed for n in needles) else default


def _audience_split(am):
    mirror = am.get("maps_signals", {}) or {}
    f, m = mirror.get("female_pct"), mirror.get("male_pct")
    return f, m


def _top_hashtags(tp):
    tags = tp.get("real_hashtags") or []
    # drop noise tokens, keep brand-y ones
    clean = [t for t in tags if t and not t.isdigit() and len(t) > 2][:10]
    return clean or None


def _anti_attributes(o):
    kills = o.organ("taste").get("kills") or []
    return kills[:10] if isinstance(kills, list) and kills else None


def _understanding(l1, brand_en):
    pos = l1.get("positioning")
    usp = l1.get("usp")
    if not (pos or usp):
        return None
    return " — ".join([x for x in [brand_en, pos, usp] if x])[:600]


def _palette_str(palette):
    """visual_dna.brand.palette is {primary:{value:..}, secondary:{value:..}} or a string/list."""
    if not palette:
        return None
    if isinstance(palette, str):
        return palette
    if isinstance(palette, list):
        return palette or None
    if isinstance(palette, dict):
        parts = [_val(v) for v in palette.values() if isinstance(_val(v), str)]
        return " · ".join(parts) or None
    return None


MIN_REVIEWS = 10  # below this a computed average is noise (DeepSeek consult, June 28)
READY_MIN_COVERAGE = 60  # a brand needs ≥ this pre_fill % (+ ≥1 banked render) to be produce-ready (A3)


def _places_rating(maps):
    """Derive (avg_rating, total_reviews) from the maps_signals star histogram.
    Rating is suppressed (null) below MIN_REVIEWS — too few to be meaningful — but the count
    still returns so coverage stays honest about how thin the signal is."""
    stars = maps.get("stars") or {}
    if not stars:
        return maps.get("rating"), maps.get("user_ratings_total")
    total = sum(int(c) for c in stars.values())
    if not total:
        return None, None
    if total < MIN_REVIEWS:
        return None, total
    avg = sum(int(s) * int(c) for s, c in stars.items()) / total
    return round(avg, 2), total


def _cadence(posts):
    """Posting rhythm from post timestamps → cadence/week, 30d frequency, account age, rhythm."""
    ts = []
    for p in posts:
        t = p.get("timestamp")
        if t:
            try:
                ts.append(datetime.fromisoformat(t.replace("Z", "+00:00")))
            except Exception:
                continue
    if len(ts) < 2:
        return {}
    ts.sort()
    latest, earliest = ts[-1], ts[0]
    span_days = max((latest - earliest).days, 1)
    per_week = round(len(ts) / (span_days / 7), 1)
    freq30 = sum(1 for t in ts if (latest - t).days <= 30)
    age_months = round((datetime.now(timezone.utc) - earliest).days / 30.4)
    rhythm = "consistent" if per_week >= 2 else "occasional"
    return {"cadence": f"≈{per_week}/week", "freq30": freq30, "age_months": age_months,
            "rhythm": f"{rhythm} (≈{per_week}/week)"}


def _logo_hex(path):
    """Dominant saturated color of the logo PNG → hex (best-effort; null if PIL missing/fails)."""
    try:
        from collections import Counter
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        im.thumbnail((64, 64))
        c = Counter()
        for r, g, b, a in im.getdata():
            if a < 128:
                continue
            if max(r, g, b) - min(r, g, b) < 40:  # skip greys/whites/blacks
                continue
            c[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += 1
        if not c:
            return None
        (r, g, b), _ = c.most_common(1)[0]
        return "#%02X%02X%02X" % (r, g, b)
    except Exception:
        return None


def export(handle, base=None):
    o = Organs(handle, base)
    pre_fill, src = build_prefill(o)
    filled = [k for k in PREFILL_KEYS if pre_fill.get(k) not in (None, [], "")]
    null = [k for k in PREFILL_KEYS if pre_fill.get(k) in (None, [], "")]
    # DeepSeek consult (June 28): flag DERIVED/INFERRED fills so downstream can weight them — a value
    # from a confirmed organ or raw IG is solid; one inferred from logo-color/IG-category/our analysis
    # /heuristic is a hint, not ground truth. Honest signal beats a false-precise number.
    LOWCONF = ("logo", "businessCategory", "capture_character", "timestamps", "region",
               "derived", "computed coverage", "heuristic")
    low_conf = [k for k in filled if src.get(k) and any(t in src[k] for t in LOWCONF)]
    prof = o.raw_profile()
    maps = o.organ("audience_mirror").get("maps_signals") or {}
    _r, _t = _places_rating(maps)
    has_places = bool(_r or maps.get("formatted_address"))
    has_site = bool(prof.get("externalUrl"))
    # A3 READINESS GATE (DeepSeek audit): tell the devs which clients are SAFE to /produce. A brand is
    # produce-ready only with enough profile AND ≥1 banked render — else /produce would 404/garbage.
    cov_pct = round(100 * len(filled) / len(PREFILL_KEYS))
    n_renders = len(list((base or B).glob(f"api/static/renders_v37/{handle}_*.jpg"))) if (base or B) else 0
    rdy_reasons = []
    if cov_pct < READY_MIN_COVERAGE:
        rdy_reasons.append(f"profile coverage {cov_pct}% < {READY_MIN_COVERAGE}%")
    if n_renders < 1:
        rdy_reasons.append("no banked renders")
    ready = not rdy_reasons
    wrapper = {
        "ok": True,
        "schema_version": "ogz-prefill-1.0",
        "brand_id": f"ogz:{handle}",
        "onboarding_status": "extraction_complete",
        "ready": ready,
        "readiness": {"ready": ready, "coverage_pct": cov_pct, "banked_renders": n_renders,
                      "min_coverage": READY_MIN_COVERAGE, "blocking_reasons": rdy_reasons},
        "sources_present": {"instagram": bool(prof), "website": has_site, "places": has_places},
        "source_status": {"instagram": "done" if prof else "unavailable",
                          "website": "done" if has_site else "unavailable",
                          "places": "done" if has_places else "unavailable"},
        "seed": {"brand_name_ar": pre_fill["brand_name_ar"], "sector": pre_fill["sector_hint"],
                 "city_primary": pre_fill["city_hint"]},
        "pre_fill": pre_fill,
        "confidence": pre_fill["confidence"],
        "brand_understanding": pre_fill["brand_understanding"],
        "_coverage": {"filled": len(filled), "total": len(PREFILL_KEYS),
                      "pct": round(100 * len(filled) / len(PREFILL_KEYS)),
                      "null_fields": null, "low_confidence_fields": low_conf,
                      "field_sources": src},
    }
    return wrapper


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--base", default="")
    a = ap.parse_args()
    base = Path(a.base) if a.base else None
    w = export(a.handle, base)
    out = Path(a.out) if a.out else (base or B) / "clients" / a.handle / "prefill.json"
    out.write_text(json.dumps(w, ensure_ascii=False, indent=2))
    cov = w["_coverage"]
    print(f"✅ {a.handle}: {cov['filled']}/{cov['total']} fields filled ({cov['pct']}%) → {out}")
    print(f"   confidence={w['confidence']}  null={len(cov['null_fields'])}: {cov['null_fields']}")


if __name__ == "__main__":
    main()
