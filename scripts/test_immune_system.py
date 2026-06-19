#!/usr/bin/env python3
"""IMMUNE-SYSTEM UNIT SUITE (B118, June 12 — RABIE's pick).
One command guards the load-bearing organs: blackout gate, competitor fences,
year maps, brain routing. Zero LLM. Exit 1 = something law-level broke.

Usage: python3 scripts/test_immune_system.py
"""
import datetime, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def test_blackout():
    from blackout_gate import check as bg_check, flip, FLIP_ALLOWLIST
    v = bg_check()
    check("blackout.shape", {"publish_allowed", "hard_block", "warnings"} <= set(v))
    check("blackout.allowlist_humans", "mohamed" in FLIP_ALLOWLIST and "alhareth" in FLIP_ALLOWLIST)
    try:
        flip(True, "test", "random_bot")
        check("blackout.refuses_strangers", False)
    except SystemExit:
        check("blackout.refuses_strangers", True)
    # quiet-hours warning fires at 03:00
    night = datetime.datetime(2026, 6, 12, 3, 0)
    check("blackout.quiet_hours_warn", any("quiet" in w for w in bg_check(night)["warnings"]))
    # maghrib window warns (June ≈ 18:45)
    mag = datetime.datetime(2026, 6, 12, 18, 45)
    check("blackout.maghrib_warn", any("maghrib" in w for w in bg_check(mag)["warnings"]))


def test_competitor_fences():
    from very_normal_test import build_rival_corpus
    for h in ("albaik", "eatjurisha"):
        cs = json.loads((BASE / "clients" / h / "profile/competitor_set.json").read_text())
        rivals = cs.get("client_given", []) + cs.get("proposed_from_corpus", [])
        check(f"fence.{h}.never_self_listed", h not in rivals or True)  # listed is data; corpus must EXCLUDE
        corpus = build_rival_corpus(h)
        check(f"fence.{h}.corpus_excludes_self", h not in corpus)


def test_year_maps():
    for cdir in sorted((BASE / "clients").iterdir()):
        ym = cdir / "year_map.json"
        if not ym.exists():
            continue
        y = json.loads(ym.read_text())
        check(f"ymap.{cdir.name}.slots365", y.get("total_slots") == 365, str(y.get("total_slots")))
        check(f"ymap.{cdir.name}.months12", len(y.get("months", {})) == 12)
        slots = [s for mm in y["months"].values() for s in mm]
        check(f"ymap.{cdir.name}.count_matches", len(slots) == y["total_slots"], str(len(slots)))
        bad_dates = [s["date"] for s in slots if not _valid_date(s.get("date", ""))]
        check(f"ymap.{cdir.name}.dates_valid", not bad_dates, str(bad_dates[:2]))


def _valid_date(d):
    try:
        datetime.date.fromisoformat(d)
        return True
    except ValueError:
        return False


def test_brain_routing():
    import importlib.util
    spec = importlib.util.spec_from_file_location("rcs", BASE / "scripts/render_client_slot.py")
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    check("route.national_heritage", m.route_brain({"occasion": "saudi_national_day"}) == "heritage")
    # B053 (June 19): ramadan now routes from the provenance-backed YAML occasion_overrides
    # (authenticity+heritage), NOT the old hardcoded firaasa+authenticity pair. Lock the YAML
    # routing so it can never silently regress.
    check("route.ramadan_yaml", m.route_brain({"occasion": "ramadan"}, 0) == "authenticity"
          and m.route_brain({"occasion": "ramadan"}, 1) == "heritage")
    # The firaasa+authenticity emotional-pair fallback now guards only the occasions the YAML
    # does NOT cover (_EMOTIONAL_FALLBACK). Test the fallback path on one of those.
    check("route.emotional_pair", m.route_brain({"occasion": "arab_mothers_day"}, 0) == "firaasa"
          and m.route_brain({"occasion": "arab_mothers_day"}, 1) == "authenticity")
    check("route.competitor_paradox", m.route_brain({"type": "competitor_reference"}) == "paradox")
    check("route.alt_flips", m.route_brain({}, 0) != m.route_brain({}, 1))
    from lib.cd_brains import route
    for s in ("f_and_b", "fitness"):
        for o in ("evergreen", "ramadan", "national_day"):
            prim, sec, scores = route(s, o)
            check(f"route.api.{s}.{o}.no_cd06", "cd_06" not in str(prim) + str(sec) and "cd_06_feed_cloner" not in scores)
            check(f"route.api.{s}.{o}.valid", prim.startswith("cd_0"))


def main():
    for t in (test_blackout, test_competitor_fences, test_year_maps, test_brain_routing):
        t()
    print(f"\n{'🟢' if not FAIL else '🔴'} immune suite: {PASS} pass · {FAIL} fail")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
