#!/usr/bin/env python3
"""THE YEAR MAP (3-client pilot, June 11) — 12-month content spine from REAL data.
Every slot: a real date (Umm al-Qura for hijri occasions), a real occasion or an
evergreen theme from the client's own moments/sector lens, a formula, an angle theme.
ANCHORS (major occasions + month 1) get full post cards rendered; the rest render
on-approach — freshness law (truth TTLs) forbids writing February's caption in June.

RABIE's ruling (provisional, logged): spine full, anchors rendered, quality over quantity.

Usage: python3 scripts/year_map.py --handle eatjurisha [--sector f_and_b] [--start 2026-07-01]
"""
import argparse, datetime, hashlib, json, sys
from pathlib import Path
from hijridate import Hijri
from hijri_util import in_ramadan

BASE = Path(__file__).parent.parent

# the real Saudi year, window 2026-07-01 → 2027-06-30 (Umm al-Qura via hijridate for hijri)
def real_occasions() -> list[dict]:
    H = lambda y, m, d: Hijri(y, m, d).to_gregorian()
    occ = [
        {"slug": "esports_world_cup", "start": "2026-07-08", "days": 45, "major": False},
        {"slug": "saudi_national_day", "start": "2026-09-23", "days": 1, "major": True},
        {"slug": "riyadh_season", "start": "2026-10-10", "days": 150, "major": False},
        {"slug": "singles_day_11_11", "start": "2026-11-11", "days": 1, "major": False},
        {"slug": "white_friday", "start": "2026-11-27", "days": 4, "major": True},
        {"slug": "mdl_beast_soundstorm", "start": "2026-12-10", "days": 4, "major": False},
        {"slug": "leap_conference", "start": "2027-02-01", "days": 4, "major": False},
        {"slug": "saudi_founding_day", "start": "2027-02-22", "days": 1, "major": True},
        {"slug": "ramadan", "start": str(H(1448, 9, 1)), "days": 29, "major": True},
        {"slug": "arab_mothers_day", "start": "2027-03-21", "days": 1, "major": False},
        {"slug": "eid_al_fitr", "start": str(H(1448, 10, 1)), "days": 3, "major": True},
        {"slug": "hajj_season", "start": str(H(1448, 12, 1)), "days": 13, "major": False},
        {"slug": "eid_al_adha", "start": str(H(1448, 12, 10)), "days": 3, "major": True},
        {"slug": "jeddah_season", "start": "2027-05-20", "days": 40, "major": False},
    ]
    for o in occ:
        o["moonsighting"] = o["slug"] in ("ramadan", "eid_al_fitr", "eid_al_adha", "hajj_season")
    return occ

CADENCE = {"newborn": 7, "newborn-dormant": 7, "active_dormant": 7, "active_unclassified": 7, "active": 7}  # Mohamed June 12: 7 posts every week, full calendar
FORMULAS = ["CF_01", "CF_02", "CF_03", "CF_04", "CF_05", "CF_06", "CF_07"]

# PER-SLOT FORMAT (June 18, Rule #12): a slot's media format ('image' | 'reel') is COMPUTED from
# real_winning_formula.json — never a hand-authored list of which posts are reels. The reel cell is
# the 2.85x Reels-placement lever, but it's a THIN sample (n=31), so it's gated + share-capped.
# Constants are derived from the WF file, not hand-picked per client.
REEL_SHARE_FLOOR, REEL_SHARE_CAP, MIN_N = 0.10, 0.25, 8  # ~1-in-10 floor, 1-in-4 cap, builder n-floor
_WF = BASE / "data/real_winning_formula.json"


def _wf() -> dict:
    try:
        return json.loads(_WF.read_text()).get("trait_lift", {})
    except Exception:
        return {}


def _occ_lift(slug) -> float:
    # the occasion the slot reliably carries — used as the reel-propensity score (matches the
    # media_type lever to the occasion lever). Unknown slug → 1.0 (stable, never crashes).
    return _wf().get("occasion", {}).get(slug or "evergreen", {}).get("lift", 1.0)


def reel_share() -> float:
    """Deterministic target reel-share of slots, derived from the WF media_type table.
    GATE (Rule #9, thin-n safe): treat reel as a lever only if reel.n >= MIN_N AND reel_lift >
    image_lift; else 0.0 → no reels ever emitted (safe no-op). Else clamp raw frequency between
    FLOOR and CAP so a 31-obs cell can't dominate a year (live: 31/6309 → clamp to FLOOR=0.10)."""
    mt = _wf().get("media_type", {})
    reel, img = mt.get("reel", {}), mt.get("image", {})
    if reel.get("n", 0) < MIN_N or reel.get("lift", 0) <= img.get("lift", 1.0):
        return 0.0
    tot = sum(v.get("n", 0) for v in mt.values()) or 1
    return max(REEL_SHARE_FLOOR, min(REEL_SHARE_CAP, round(reel.get("n", 0) / tot, 3)))


def _slot_hash(handle: str, date: str) -> int:
    # stable tiebreak so the reel set is byte-reproducible (NOT date order, NOT a hand list)
    return int(hashlib.sha1(f"{handle}|{date}".encode()).hexdigest(), 16)


# face-directing seed words (June 30 — Rule #8 root fix): a sector-lens moment that
# depicts human faces/expressions/gatherings makes the Art-Director HOLD the image for a
# face_visibility=never brand (the gate correctly refuses). A no-face brand must never be
# SEEDED with a face-directing angle_theme in the first place — fix the input, not the
# gate (RABIE + DeepSeek converged 2026-06-30, verified against render_client_slot HOLD).
_FACE_SEED_WORDS = ("famil", "grandparent", "gather", "sharing storie", "faces",
                    "children", "kids", "friends meeting", "friends gathering",
                    "loved ones", "smiling", "expressions", "people enjoying")


def _directs_faces(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in _FACE_SEED_WORDS)


def lens_theme(sector: str, occ_slug: str, face_free: bool = False) -> str | None:
    facts = json.loads((BASE / "data/occasion_facts.json").read_text())
    key = {"saudi_national_day": "saudi_national_day"}.get(occ_slug, occ_slug)
    lens = (facts.get(key, {}).get("sector_lenses") or {}).get(sector) or {}
    m = lens.get("moments") or []
    if not m:
        return None
    if face_free:
        # prefer the first moment that does NOT direct faces; if every moment does,
        # return None so build() falls back to the face-neutral generic theme.
        clean = [x for x in m if not _directs_faces(x)]
        return clean[0][:100] if clean else None
    return m[0][:100]


def build(handle: str, sector: str, start: datetime.date) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    if not pdir.exists():
        sys.exit(f"no profile for {handle} — run build_brand_profile.py first")
    state = json.loads((pdir / "state.json").read_text())
    moments = json.loads((pdir / "moments_bank.json").read_text())["moments"]
    truth = json.loads((pdir / "truth_pack.json").read_text())
    # face policy (June 30): a face_visibility=never brand must not be seeded with a
    # face-directing occasion angle_theme (the Art-Director would HOLD every such slot).
    try:
        _co = json.loads((pdir / "cultural_overrides.json").read_text())
        face_free = str(_co.get("face_visibility", "")).lower() == "never"
    except Exception:
        face_free = False
    per_week = CADENCE.get(state["state"], 2)
    end = start.replace(year=start.year + 1)

    # sector fit: event-occasions only for sectors they serve (a cloud kitchen has no esports angle)
    SECTOR_FIT = {"esports_world_cup": {"retail_lifestyle", "fashion"},
                  "mdl_beast_soundstorm": {"retail_lifestyle", "fashion", "beauty_personal_care"},
                  "leap_conference": {"retail_lifestyle"},
                  "singles_day_11_11": {"retail_lifestyle", "fashion", "beauty_personal_care"}}
    occ = [o for o in real_occasions() if sector in SECTOR_FIT.get(o["slug"], {sector})]
    occ_by_date = {}
    BEAT_RANK = {"day_of": 3, "teaser": 2, "mid_season": 1}

    def put(day, entry):
        cur = occ_by_date.get(day)
        # collision rule: major beats minor, then higher beat wins (founding-day day_of > ramadan mid_season)
        if cur and (cur["major"], BEAT_RANK[cur["beat"]]) >= (entry["major"], BEAT_RANK[entry["beat"]]):
            return
        occ_by_date[day] = entry

    for o in occ:
        d0 = datetime.date.fromisoformat(o["start"])
        # teaser 3 days before majors, day-of always, mid-season beat for long seasons
        if o["major"]:
            put(d0 - datetime.timedelta(days=3), {**o, "beat": "teaser"})
        put(d0, {**o, "beat": "day_of"})
        if o["days"] > 20:
            put(d0 + datetime.timedelta(days=o["days"] // 2), {**o, "beat": "mid_season"})

    # evergreen themes rotate through the client's REAL material — but OCCASION-NEUTRAL ONLY
    # (June 14 root fix): a daily slot must never inherit an Eid/Ramadan/National-Day moment
    # hook, or its caption fabricates that holiday on a plain day. Calendar-occasion moments
    # belong only on the matching occasion slots (which use lens_theme). Also drop garbage
    # "products" (prepositions like «على», mangled Latin like «Liaqti.tu»).
    import re as _re
    from occasion_align import CALENDAR_OCC_MOMENTS, occ_hits
    _STOP = set("على عن من في إلى الى مع و أو يا هذا هذه the a an of on".split())
    _good = lambda n: bool((n or "").strip()) and (n or "").strip() not in _STOP \
        and len((n or "").strip()) > 2 and not _re.search(r"[A-Za-z]+\.[a-z]{2,}", n or "")
    # RED-LINE markers a daily theme must never carry (RABIE 2026-06-14: moment EVIDENCE texts
    # held «بحضور صاحب السمو الأمير سعود» / «معالي أمين العاصمة» — royal/official patronage that
    # red_lines.json forbids in commercial content). Filter the TEXT, not just the occasion tag.
    _ROYAL = _re.compile(r"الأمير|الأميرة|سمو|معالي|سعادة|آل ?سعود|ولي ?العهد|أمين ?العاصمة|الملك ")
    def _neutral(m):
        ev = m.get("evidence") or ""
        return (m.get("occasion") not in CALENDAR_OCC_MOMENTS
                and not occ_hits(ev)          # evidence text invents no calendar occasion
                and not _ROYAL.search(ev))     # and names no royal/official figure
    ever = ([m["occasion"] + ": " + m["evidence"][:60] for m in moments if _neutral(m)] +
            [f"منتج حقيقي: {p['name']}" for p in truth.get("product_candidates", []) if _good(p.get("name"))] +
            [f"قناة: اطلب عبر {c['name']}" for c in truth.get("channels", []) if c["name"] != "linktree"])
    if not ever:
        ever = ["voice-birth follow-up (newborn: material comes from the birth week)"]

    slots, d, i = [], start, 0
    post_days = set(range(7)) if per_week >= 7 else ({1, 4} if per_week == 2 else {0, 2, 4})
    while d < end:
        o = occ_by_date.get(d)
        if o:
            slots.append({"date": str(d), "type": "occasion", "occasion": o["slug"], "beat": o["beat"],
                          "major": o["major"], "moonsighting_check": o["moonsighting"],
                          "formula": FORMULAS[i % 7],
                          "angle_theme": lens_theme(sector, o["slug"], face_free=face_free) or f"{o['slug']} × real brand moment",
                          "format": "image",  # computed → some flip to 'reel' in the post-loop ranking pass
                          "anchor": o["major"] and o["beat"] == "day_of", "status": "planned"})
            i += 1
        elif d.weekday() in post_days:
            # ramadan posting shifts: skip daytime-energy evergreen inside ramadan window.
            # window derived from the Hijri calendar (Ramadan = Hijri month 9), correct for any
            # year — never a hardcoded Gregorian span (B047 scar). [[hijri_util]]
            is_ramadan = in_ramadan(d)
            slots.append({"date": str(d), "type": "evergreen" if not is_ramadan else "ramadan_evergreen",
                          "formula": FORMULAS[i % 7],
                          "angle_theme": ever[i % len(ever)],
                          "format": "image",  # computed → some flip to 'reel' in the post-loop ranking pass
                          "anchor": (d - start).days < 31, "status": "planned"})
            i += 1
        d += datetime.timedelta(days=1)

    # FORMAT RANKING PASS (Rule #12: computed, no hand-authored reel list). Rank every slot by
    # (occasion_lift desc, stable hash desc) and flip the top reel_share fraction to format='reel'.
    # The highest-propensity occasions become the reels (media_type lever ⨯ occasion lever), the
    # hash spreads ties evenly and makes the reel set byte-reproducible from the data + (handle,date).
    # If the gate fails (thin n / reel not a real lever) share == 0 → no reels (safe no-op).
    share = reel_share()
    if share > 0 and slots:
        ranked = sorted(slots, key=lambda s: (_occ_lift(s.get("occasion")), _slot_hash(handle, s["date"])),
                        reverse=True)
        for s in ranked[:round(share * len(slots))]:
            s["format"] = "reel"

    months = {}
    for s in slots:
        months.setdefault(s["date"][:7], []).append(s)
    ymap = {"handle": handle, "sector": sector, "state": state["state"], "cadence_per_week": per_week,
            "window": [str(start), str(end)], "built": "2026-06-11",
            "ruling": "spine full + anchors rendered now + rest on-approach (RABIE, provisional)",
            "total_slots": len(slots), "anchors": sum(1 for s in slots if s["anchor"]),
            "reel_share": share, "reels": sum(1 for s in slots if s.get("format") == "reel"),
            "months": months}
    out = BASE / "clients" / handle / "year_map.json"
    out.write_text(json.dumps(ymap, ensure_ascii=False, indent=2))
    return ymap


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--sector", default="f_and_b")
    ap.add_argument("--start", default="2026-07-01")
    a = ap.parse_args()
    m = build(a.handle, a.sector, datetime.date.fromisoformat(a.start))
    print(f"✓ year map → clients/{a.handle}/year_map.json")
    print(f"  {m['total_slots']} slots over 12 months · {m['anchors']} anchors · cadence {m['cadence_per_week']}/wk · state {m['state']}")
    print(f"  format: {m['reels']} reel ({m['reel_share']:.0%} share, computed from WF media_type lift) · rest image")
    occ_slots = [s for mm in m['months'].values() for s in mm if s['type'] == 'occasion']
    print(f"  occasion slots: {len(occ_slots)} (majors day-of: {sum(1 for s in occ_slots if s.get('major') and s['beat']=='day_of')})")
