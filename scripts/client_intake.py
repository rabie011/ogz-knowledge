#!/usr/bin/env python3
"""ONE-SHOT CLIENT INTAKE (June 12, 2026) — the product's onboarding backend.

When a client shares their links we get ONE clean extraction moment. This captures
EVERYTHING extractable in one run, raw-first and immutable, verified, and ends with
a GAP REPORT whose items become the only questions we ask the client.

Surfaces: IG profile → posts (full raw) → comments on top posts (audience voice)
          → media files (the visual archive) → bio link (website, if any).
Layout (clients/ is ISOLATED from benchmark brands — conventions rule #9):
  clients/{handle}/raw/instagram/{date}/profile.json|posts.jsonl|comments.jsonl
  clients/{handle}/media/{shortcode}.jpg
  clients/{handle}/manifest.json      ← the client file: what we hold, counts, provenance
  clients/{handle}/gap_report.json    ← what links can't tell us → the intake questions

Usage: python3 scripts/client_intake.py --handle eatjurisha
Integrity law: counts verified vs profile claims; 0-results = WARNING never success.
"""
import argparse, datetime, json, os, sys, urllib.request
from pathlib import Path

from apify_client import ApifyClient

BASE = Path(__file__).parent.parent
TODAY = datetime.date.today().isoformat()


def env(k):
    v = os.environ.get(k, "")
    if v:
        return v
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {k}")


def jdump(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2))


def identity_check(profile: dict, handle: str) -> dict:
    """GAP-07 (B020): never build a pyramid on an unconfirmed identity. The lnasser→
    alnasser mangling nearly profiled the WRONG brand — this block makes the question
    explicit on every manifest. Verdict 'confirmed' needs the verified badge OR
    (bio-URL domain match + name match); anything else stays unconfirmed until the
    client confirms in writing (written_confirmation is filled by a human, never code)."""
    import re as _re
    root = _re.sub(r"[._\d]", "", handle).lower()
    url = (profile.get("externalUrl") or "").lower()
    url_match = bool(root) and root[:10] in _re.sub(r"[^a-z]", "", url)
    name = _re.sub(r"[^a-zA-Z\u0600-\u06FF]", "", profile.get("fullName") or "").lower()
    name_match = bool(root) and (root[:8] in name or name[:8] in root if name else False)
    verified = bool(profile.get("verified"))
    verdict = "confirmed" if (verified or (url_match and name_match)) else "UNCONFIRMED"
    return {"verified_badge": verified, "bio_url_domain_match": url_match,
            "name_match": name_match, "written_confirmation": None,
            "verdict": verdict,
            "rule": "no pyramid/year-map/outbound work on UNCONFIRMED identity without "
                    "written confirmation (GAP-07; the lnasser scar)"}


def run_intake(handle: str):
    client = ApifyClient(env("APIFY_TOKEN"))
    root = BASE / "clients" / handle
    raw = root / "raw" / "instagram" / TODAY
    raw.mkdir(parents=True, exist_ok=True)
    manifest = {"handle": handle, "extracted": TODAY, "surfaces": {}, "warnings": [],
                 "referred_by": None,  # B150: the referral loop's root — filled at intake when known
                 "provenance": {"source": "apify one-shot intake", "confirmer": "pending_client",
                                 "confidence": "raw", "scope": f"brand:{handle}"}}

    # ── 1. PROFILE ────────────────────────────────────────────────────────────
    print("1/5 profile…", flush=True)
    prof_items = []
    try:
        run = client.actor("apify/instagram-profile-scraper").call(
            run_input={"usernames": [handle]})
        ds = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId", "")
        prof_items = list(client.dataset(ds).iterate_items())
    except Exception as e:
        manifest["warnings"].append(f"profile scrape failed: {str(e)[:120]}")
    profile = prof_items[0] if prof_items else {}
    jdump(raw / "profile.json", profile)
    claimed = int(profile.get("postsCount") or 0)
    manifest["surfaces"]["profile"] = {
        "ok": bool(profile), "followers": profile.get("followersCount"),
        "posts_claimed": claimed, "bio": (profile.get("biography") or "")[:200],
        "external_url": profile.get("externalUrl"), "business": profile.get("businessCategoryName"),
        "private": profile.get("private"), "verified": profile.get("verified"),
        "identity_check": identity_check(profile, handle)}
    if not profile:
        manifest["warnings"].append("PROFILE EMPTY — private account or wrong handle? STOP AND CHECK")

    # ── 2. POSTS (full raw) ───────────────────────────────────────────────────
    print("2/5 posts…", flush=True)
    posts = []
    try:
        run = client.actor("apify/instagram-post-scraper").call(
            run_input={"username": [handle], "resultsLimit": max(claimed + 20, 100)})
        ds = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId", "")
        posts = list(client.dataset(ds).iterate_items())
    except Exception as e:
        manifest["warnings"].append(f"posts scrape failed: {str(e)[:120]}")
    with open(raw / "posts.jsonl", "w") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    got = len(posts)
    manifest["surfaces"]["posts"] = {"fetched": got, "claimed": claimed,
                                       "coverage_pct": round(100 * got / claimed) if claimed else None}
    if claimed and got < claimed * 0.9:
        manifest["warnings"].append(f"posts coverage {got}/{claimed} — below 90%, investigate before calling done")
    if got == 0:
        manifest["warnings"].append("ZERO POSTS — silent-failure law: this is an ERROR, not an empty account, until proven")

    # ── 3. COMMENTS on top posts (audience voice) ────────────────────────────
    print("3/5 comments…", flush=True)
    top = sorted(posts, key=lambda p: int(p.get("likesCount") or 0), reverse=True)[:8]
    urls = [p.get("url") for p in top if p.get("url")]
    comments = []
    if urls:
        try:
            run = client.actor("apify/instagram-comment-scraper").call(
                run_input={"directUrls": urls, "resultsLimit": 30})
            ds = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId", "")
            comments = list(client.dataset(ds).iterate_items())
        except Exception as e:
            manifest["warnings"].append(f"comments scrape failed: {str(e)[:120]}")
    with open(raw / "comments.jsonl", "w") as f:
        for c in comments:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    manifest["surfaces"]["comments"] = {"fetched": len(comments), "from_posts": len(urls)}

    # ── 4. MEDIA (the visual archive — one shot, files in hand) ─────────────
    print("4/5 media…", flush=True)
    media_dir = root / "media"
    media_dir.mkdir(exist_ok=True)
    saved = 0
    for p in posts[:150]:
        url = p.get("displayUrl")
        sc = p.get("shortCode") or p.get("id") or str(saved)
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=30).read()
            (media_dir / f"{sc}.jpg").write_bytes(data)
            saved += 1
        except Exception:
            manifest["warnings"].append(f"media failed: {sc}")
    manifest["surfaces"]["media"] = {"saved": saved, "video_urls_recorded": sum(1 for p in posts if p.get("videoUrl"))}

    # ── 5. WEBSITE from bio link ─────────────────────────────────────────────
    print("5/5 website…", flush=True)
    site = profile.get("externalUrl")
    if site:
        try:
            req = urllib.request.Request(site, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=30).read()[:500_000]
            (raw / "website.html").write_bytes(html)
            manifest["surfaces"]["website"] = {"url": site, "bytes": len(html)}
        except Exception as e:
            manifest["surfaces"]["website"] = {"url": site, "error": str(e)[:80]}
    else:
        manifest["surfaces"]["website"] = {"url": None, "note": "no bio link — ask client for menu/site/WhatsApp"}

    # ── GAP REPORT: what links can never tell us → the client questions ─────
    gaps = {
        "always_ask": [
            "أهداف العمل القادمة (إطلاقات، فروع، مواسم مهمة لكم؟)",
            "الخطوط الحمراء: وش ما ننشر أبداً؟ (وجوه العائلة؟ قصة الوالدة؟ أسعار؟)",
            "مين ينطق باسم البراند: صوت البنت؟ صوت العائلة؟ صوت محايد؟",
            "وش اللي يميزكم بكلمات صاحبة المشروع نفسها؟ (USP)",
            "الهدف من المحتوى: مبيعات مباشرة ولا بناء براند ولا الاثنين؟ (نسبة العروض)",
        ],
        "from_this_extraction": [],
    }
    if not site:
        gaps["from_this_extraction"].append("لا يوجد رابط موقع/منيو في البايو — نطلب المنيو والأسعار وطرق الطلب")
    if manifest["surfaces"]["posts"]["fetched"] < 30:
        gaps["from_this_extraction"].append("الفيد صغير — نحتاج صور إضافية من الجوال (أرشيف خاص) لو متوفرة")
    # B013 boundary fix: jurisha fetched EXACTLY 10 → strict <10 never armed the ask,
    # yet only 5 carried usable text. Count USABLE comments, arm at <=10.
    usable = sum(1 for c in comments if (c.get("text") or "").strip())
    if usable <= 10:
        gaps["from_this_extraction"].append(
            f"تعليقات قليلة ({usable} نص مفيد) — نسأل: وش أكثر سؤال يجيكم من الزبائن واتساب؟")
    jdump(root / "gap_report.json", gaps)
    jdump(root / "manifest.json", manifest)

    # ── REPORT ────────────────────────────────────────────────────────────────
    print("\n══ ONE-SHOT COMPLETE ══")
    print(json.dumps(manifest["surfaces"], ensure_ascii=False, indent=1))
    if manifest["warnings"]:
        print("⚠ WARNINGS:")
        for w in manifest["warnings"][:10]:
            print("  -", w)
    print(f"client file: clients/{handle}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    a = ap.parse_args()
    run_intake(a.handle)
