#!/usr/bin/env python3
"""THE COMPOSER (pyramid GAP-08, June 11) — raw intake + corpus → the 10 profile organs.
clients/{handle}/profile/ per THE_CLIENT_PYRAMID.md Layer 2. Honest by design:
- every fact carries provenance; inferred NEVER claims confirmed
- identity organs that need the client stay EMPTY (red, visible) — the albaik
  lesson: 164 observations cannot produce one red line
- no AI judges anything here; this is countables + verbatim mining only

Usage: python3 scripts/build_brand_profile.py --handle eatjurisha [--brand-key albaik]
  --brand-key links a corpus DNA file (logs/brand_dna/{key}.json) when the corpus
  knows the brand under a different key than the IG handle.
"""
import argparse, collections, datetime, json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
TODAY = datetime.date.today()

KNOWN_CHANNELS = {"jahez": "جاهز", "hungerstation": "هنقرستيشن", "toyou": "تويو", "mrsool": "مرسول",
                  "keeta": "كيتا", "linktr.ee": "linktree", "wa.me": "whatsapp", "whatsapp": "whatsapp",
                  "maps.app": "google_maps", "calendly": "booking", "classpass": "booking"}

PROV = lambda src, conf="inferred": {"source": src, "date_added": str(TODAY),
                                      "confirmer": "pending_client", "confidence": conf,
                                      "scope": "brand"}


def load_raw(cdir: Path) -> tuple[dict, list, list]:
    days = sorted((cdir / "raw/instagram").iterdir())
    raw = days[-1]
    profile = json.loads((raw / "profile.json").read_text())
    posts = [json.loads(l) for l in (raw / "posts.jsonl").read_text().strip().split("\n") if l.strip()]
    cf = raw / "comments.jsonl"
    comments = [json.loads(l) for l in cf.read_text().strip().split("\n") if l.strip()] if cf.exists() else []
    return profile, posts, comments


def diagnose_state(profile: dict, posts: list) -> dict:
    """Countables only (posts, dates, followers). Voice-quality routing needs a human."""
    n = profile.get("postsCount") or len(posts)
    last = None
    for p in posts:
        ts = p.get("timestamp", "")
        if ts:
            d = datetime.date.fromisoformat(ts[:10])
            last = max(last, d) if last else d
    silent_days = (TODAY - last).days if last else None
    state = "newborn" if (n or 0) < 30 else "active"
    if silent_days and silent_days > 90:
        state += "-dormant" if state == "newborn" else "_dormant"
    elif state == "active":
        state = "active_unclassified"  # messy-vs-strong needs the human checkpoint (pyramid §3)
    return {"state": state, "posts_count": n, "followers": profile.get("followersCount"),
            "last_post": str(last) if last else None, "silent_days": silent_days,
            "method": "countables_only", "human_checkpoint": "pending",
            "provenance": PROV("intake_countables", "confirmed")}


def mine_truth_candidates(profile: dict, posts: list) -> dict:
    """Bio + captions → product/channel CANDIDATES with verbatim evidence. Never confirmed."""
    bio = profile.get("biography", "") or ""
    ext = " ".join(filter(None, [profile.get("externalUrl") or ""] +
                          [u if isinstance(u, str) else (u.get("url") or "") for u in (profile.get("externalUrls") or [])]))
    channels = []
    for key, name in KNOWN_CHANNELS.items():
        if key in (bio + " " + ext).lower() or name in bio:
            channels.append({"name": name, "evidence": "bio/links", "provenance": PROV("bio", "confirmed")})
    # product candidates: bio segments + recurring caption n-grams (Arabic + Latin), hashtags EXCLUDED from products
    seg = [s.strip() for s in re.split(r"[\n•·|,;:/–—-]+", bio) if 2 < len(s.strip()) < 40]
    seg = [s for s in seg if not s.startswith(("http", "@", "#", "📍")) and "تطبيق" not in s]
    cap_text = " ".join((p.get("caption") or "") for p in posts)
    words = re.findall(r"[؀-ۿ]{3,}|[A-Za-z]{4,}", cap_text)
    counts = collections.Counter(w for w in words if w not in {"على", "الآن", "متوفر", "with", "your", "this"})
    recurring = [w for w, c in counts.most_common(30) if c >= max(2, len(posts) // 4)]
    products = [{"name": s, "evidence": "bio", "provenance": PROV("bio")} for s in seg]
    real_tags = sorted({t for p in posts for t in (p.get("hashtags") or [])})
    return {"confirmed": [], "product_candidates": products,
            "recurring_caption_terms": recurring[:15], "channels": channels,
            "real_hashtags": real_tags, "prices": [],
            "note": "candidates await client confirm — a guessed price is a lie with confidence"}


def build(handle: str, brand_key: str | None):
    cdir = BASE / "clients" / handle
    if not (cdir / "raw").exists():
        sys.exit(f"no intake at clients/{handle}/raw — run client_intake.py first")
    profile, posts, comments = load_raw(cdir)
    pdir = cdir / "profile"
    pdir.mkdir(exist_ok=True)
    (cdir / "events").mkdir(exist_ok=True)

    organs = {}
    organs["state"] = diagnose_state(profile, posts)
    organs["truth_pack"] = mine_truth_candidates(profile, posts)

    # fingerprint: voice stats from corpus DNA if linked; identity ALWAYS starts red
    dna = {}
    dkey = brand_key or handle
    df = BASE / "logs/brand_dna" / f"{dkey}.json"
    if df.exists():
        dna = json.loads(df.read_text())
    organs["fingerprint"] = {
        "l1_strategy": {"contrarian_belief": None, "positioning": None, "who_speaks": None,
                         "_status": "RED — client-only, cannot be inferred"},
        "l2_voice": {"dialect": dna.get("dominant_dialect"), "register": dna.get("dominant_register"),
                      "tone": dna.get("dominant_tone"),
                      "love_lines": [], "hate_lines": [],
                      "_status": "YELLOW — stats describe the past; client pick makes it law" if dna else
                                 "RED — newborn: voice must be BORN (voice birth week)",
                      "provenance": PROV(f"brand_dna/{dkey}" if dna else "none")},
        "l3_visual": {k: dna.get(k) for k in ("visual_palette", "setting", "format_mix") if dna.get(k)},
    }
    organs["red_lines"] = {"lines": [], "defaults_pinned": "STRICTEST (cultural_spec_v1 ~10 override fields)",
                            "note": "cannot exist without the client — richest profile lies loudest"}
    organs["goals"] = {"goal_ratio": None, "capacity_ceiling": None, "forward_calendar": [],
                        "usp_his_words": None, "answered": 0, "of": 5}
    # moments: occasion mentions in real captions
    occ_terms = {"ramadan": ["رمضان"], "eid": ["العيد", "عيد"], "national_day": ["اليوم الوطني", "وطني"],
                 "founding_day": ["التأسيس"], "winter": ["شتاء"], "summer": ["صيف"], "family": ["عائل", "أهل", "بيت"]}
    moments = []
    for p in posts:
        cap = p.get("caption") or ""
        for occ, terms in occ_terms.items():
            if any(t in cap for t in terms):
                moments.append({"occasion": occ, "evidence": cap[:90],
                                 "engagement": p.get("likesCount"), "provenance": PROV("real_post", "confirmed")})
    organs["moments_bank"] = {"moments": moments}
    organs["audience_mirror"] = {"comments_count": len(comments),
                                   "sample": [c.get("text", "")[:80] for c in comments[:10]],
                                   "note": "delivery-app reviews NOT read (FLANK-05 open)"}
    taste = json.loads((BASE / "data/founder_taste.json").read_text())
    raw_kills = taste.get("kills", [])
    kill_names = (list(raw_kills)[:12] if isinstance(raw_kills, dict)
                  else [k.get("name", str(k)) if isinstance(k, dict) else str(k) for k in raw_kills][:12])
    organs["taste"] = {"floor": "founder_taste.json (inherited)",
                        "kills": kill_names, "client_calibration": []}
    # gap report: every empty organ → a question
    gaps = []
    if not organs["red_lines"]["lines"]:
        gaps.append("الخطوط الحمراء: وش ما ننشر أبداً؟")
    if not organs["goals"]["goal_ratio"]:
        gaps.append("الهدف: مبيعات مباشرة، بناء براند، ولا الاثنين؟ كم نسبة العروض؟")
    if not organs["goals"]["capacity_ceiling"]:
        gaps.append("كم طلب باليوم تقدرون تستوعبون؟")
    if organs["fingerprint"]["l1_strategy"]["who_speaks"] is None:
        gaps.append("مين يتكلم باسم البراند؟")
    if not organs["truth_pack"]["confirmed"]:
        gaps.append("تأكيد المنتجات والأسعار (المرشّحين مرفقين)")
    organs["gap_report"] = {"questions": gaps, "organs_red": ["red_lines", "goals", "l1_strategy"],
                             "organs_yellow": ["truth_pack(candidates)", "l2_voice(stats)" if dna else "l2_voice(birth needed)"]}

    for name, data in organs.items():
        (pdir / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return organs


def status_line(organs: dict) -> str:
    s = organs["state"]
    fp = organs["fingerprint"]
    tp = organs["truth_pack"]
    return (f"state={s['state']} posts={s['posts_count']} followers={s['followers']} "
            f"silent={s['silent_days']}d | voice={'GREEN' if fp['l2_voice']['love_lines'] else ('YELLOW' if fp['l2_voice'].get('dialect') else 'RED')} "
            f"identity=RED | products: {len(tp['product_candidates'])} candidates/0 confirmed, "
            f"channels: {len(tp['channels'])} | moments: {len(organs['moments_bank']['moments'])} | "
            f"gaps: {len(organs['gap_report']['questions'])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--brand-key", default=None)
    a = ap.parse_args()
    organs = build(a.handle, a.brand_key)
    print(f"✓ 10 organs → clients/{a.handle}/profile/")
    print(status_line(organs))
