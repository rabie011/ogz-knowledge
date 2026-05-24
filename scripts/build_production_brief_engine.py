#!/usr/bin/env python3
"""
build_production_brief_engine.py
Agency production brief generator — the output tool.
Reads all analytical logs and generates a complete shoot + caption brief
for a given client sector + occasion + content goal.

Usage:
  python3 scripts/build_production_brief_engine.py \
    --sector food_and_beverage \
    --occasion ramadan \
    --goal brand_building \
    --account barnscoffee          (optional — adds competitor gap data)

Or interactive mode:
  python3 scripts/build_production_brief_engine.py --interactive

Output: prints full production brief to stdout + saves to logs/production_briefs/{timestamp}.json
"""
import json
import argparse
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
LOGS = BASE / "logs"

CORPUS_BASELINE = 0.54

SECTOR_ALIASES = {
    "fb": "food_and_beverage", "f&b": "food_and_beverage",
    "food": "food_and_beverage", "food_and_beverage": "food_and_beverage",
    "beauty": "beauty_personal_care", "personal_care": "beauty_personal_care",
    "retail": "retail_lifestyle", "lifestyle": "retail_lifestyle",
}

GOAL_DESCRIPTIONS = {
    "brand_building":    "Build emotional brand equity — no hard sell",
    "product_launch":    "Introduce a new product or menu item",
    "occasion_content":  "Celebrate a cultural or seasonal moment",
    "offer_promotion":   "Drive immediate purchase with price or offer",
    "awareness":         "Reach new audiences, build recognition",
    "community":         "Foster loyalty with existing customers",
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except:
        return {}


def generate_brief(sector: str, occasion: str, goal: str, account: str = None) -> dict:
    """Core brief generation logic."""

    # Load all relevant analytical logs
    vdt     = load_json(LOGS / "visual_decision_tree.json")
    opp     = load_json(LOGS / "occasion_playbook.json")
    signals = load_json(LOGS / "engagement_signal_table.json")
    comp_an = load_json(LOGS / "composition_analysis.json")
    cta_lan = load_json(LOGS / "cta_language_signals.json")
    fmt_occ = load_json(LOGS / "format_occasion_matrix.json")
    gap     = load_json(LOGS / "competitive_gap.json") if account else {}
    patterns = load_json(LOGS / "pattern_cooccurrence_matrix.json") if (LOGS / "pattern_cooccurrence_matrix.json").exists() else {}

    # 1. OCCASION RECIPE from playbook
    playbook_entry = None
    for entry in (opp.get("playbook") or []):
        if entry.get("occasion","").lower() == occasion.lower():
            playbook_entry = entry
            break

    # 2. VISUAL PRODUCTION from decision tree
    prod_rec = None
    sector_tree = (vdt.get("sector_occasion_decision_tree") or {}).get(sector, {})
    occ_node = sector_tree.get(occasion)
    if occ_node:
        prod_rec = occ_node.get("recommended_production")

    # 3. FORMAT recommendation
    best_fmt_info = (fmt_occ.get("best_format_per_occasion") or {}).get(occasion)

    # 4. COMPOSITION agency verdict
    comp_verdicts = comp_an.get("agency_verdicts", {})
    comp_table    = comp_an.get("composition_engagement_table", [])
    best_comp_for_sector = (comp_an.get("best_composition_per_sector") or {}).get(sector)

    # 5. LANGUAGE & CTA rules
    lang_by_occ = {}
    for row in (cta_lan.get("language_by_occasion") or []):
        if row.get("occasion") == occasion and row.get("count",0) >= 2:
            if row["language"] not in lang_by_occ or row["high_eng_rate"] > lang_by_occ[row["language"]]["rate"]:
                lang_by_occ[row["language"]] = {"rate": row["high_eng_rate"], "count": row["count"]}
    best_lang_for_occ = max(lang_by_occ.items(), key=lambda x: x[1]["rate"], default=(None,{}))[0] if lang_by_occ else None

    cta_rows = cta_lan.get("cta_engagement_table", [])
    best_cta = cta_rows[0]["cta"] if cta_rows else None

    # 6. TOP ENGAGEMENT SIGNALS for this occasion (from signals table)
    occ_signals = []
    for sig in (signals.get("signal_table") or []):
        if sig.get("signal_type") == "occasion" and sig.get("signal_value") == occasion:
            occ_signals.append(sig)

    # 7. COMPETITOR GAP for specific account
    account_gaps = []
    if account and gap:
        for report in (gap.get("account_gap_reports") or []):
            if report.get("account","").lower() == account.lower():
                account_gaps = report.get("high_value_gaps",[])[:5]
                break

    # 8. RECOMMENDED PATTERNS (from occasion playbook elite recipe + high-eng signals)
    rec_patterns = []
    if playbook_entry:
        elite = playbook_entry.get("elite_recipe") or {}
        rec_patterns = elite.get("top_patterns") or playbook_entry.get("top_patterns") or []

    # Build the brief
    brief = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input": {
            "sector": sector,
            "occasion": occasion,
            "content_goal": goal,
            "account": account,
        },
        "predicted_engagement": _predict_eng(playbook_entry, occ_node),
        "campaign_context": {
            "occasion_verdict": playbook_entry.get("engagement_verdict") if playbook_entry else "insufficient_data",
            "goal_description": GOAL_DESCRIPTIONS.get(goal, goal),
        },
        "production_spec": {
            "format":      (best_fmt_info or {}).get("format") or (prod_rec or {}).get("format"),
            "setting":     (prod_rec or {}).get("setting") or (playbook_entry or {}).get("overall_recipe",{}).get("setting"),
            "lighting":    (prod_rec or {}).get("lighting") or (playbook_entry or {}).get("overall_recipe",{}).get("lighting"),
            "composition": (prod_rec or {}).get("composition") or (playbook_entry or {}).get("overall_recipe",{}).get("composition"),
            "composition_verdict": comp_verdicts.get(
                (prod_rec or {}).get("composition") or ""
            ),
        },
        "caption_spec": {
            "register":    (prod_rec or {}).get("register") or (playbook_entry or {}).get("overall_recipe",{}).get("register"),
            "tone":        (prod_rec or {}).get("tone") or (playbook_entry or {}).get("overall_recipe",{}).get("tone"),
            "language":    best_lang_for_occ or (playbook_entry or {}).get("overall_recipe",{}).get("language"),
            "add_cta":     best_cta == "cta_present",
            "heritage_vs_modern": (playbook_entry or {}).get("overall_recipe",{}).get("heritage_vs_modern"),
        },
        "cultural_spec": {
            "hospitality_cues_target": _hosp_target(playbook_entry),
            "hospitality_cue_examples": ["traditional_coffee_service","date_offering","incense_bakhoor"],
        },
        "content_patterns": {
            "recommended": rec_patterns[:5],
            "avoid_for_this_goal": _get_avoid_patterns(goal),
        },
        "competitive_gaps": account_gaps if account_gaps else None,
        "data_sources": {
            "occasion_obs": playbook_entry.get("obs_count") if playbook_entry else 0,
            "sector_occ_obs": (occ_node or {}).get("obs_count", 0),
        },
    }

    return brief


def _predict_eng(playbook_entry, occ_node):
    rates = []
    if playbook_entry:
        rates.append(playbook_entry.get("high_engagement_rate", 0.54))
    if occ_node:
        rates.append(occ_node.get("occasion_high_eng_rate", 0.54))
    if not rates:
        return {"predicted_rate": CORPUS_BASELINE, "confidence": "low", "grade": "C"}
    rate = round(sum(rates)/len(rates), 3)
    grade = "A" if rate >= 0.75 else "B" if rate >= 0.60 else "C" if rate >= 0.45 else "D"
    confidence = "high" if min((playbook_entry or {}).get("obs_count",0), (occ_node or {}).get("obs_count",0)) >= 8 else "medium" if rates else "low"
    return {"predicted_high_eng_rate": rate, "grade": grade, "confidence": confidence}


def _hosp_target(playbook_entry):
    if not playbook_entry:
        return 2
    avg = (playbook_entry.get("overall_recipe") or {}).get("avg_hospitality_cues", 1)
    return max(2, round(avg))


def _get_avoid_patterns(goal: str) -> list:
    if goal == "brand_building":
        return ["price_offer_graphic", "product_launch_countdown"]
    elif goal == "offer_promotion":
        return ["heritage_storytelling_hook", "documentary_bts"]
    elif goal == "community":
        return ["price_offer_graphic", "influencer_takeover_post"]
    return []


def print_brief(brief: dict):
    inp  = brief["input"]
    prod = brief["production_spec"]
    cap  = brief["caption_spec"]
    cult = brief["cultural_spec"]
    pats = brief["content_patterns"]
    pred = brief["predicted_engagement"]

    sep = "─" * 65
    print(f"\n{'═'*65}")
    print(f"  OGZ PRODUCTION BRIEF")
    print(f"  {inp['sector'].upper()} × {inp['occasion'].replace('_',' ').upper()} × {inp['content_goal'].replace('_',' ').upper()}")
    if inp.get("account"):
        print(f"  Account: @{inp['account']}")
    print(f"{'═'*65}\n")

    grade = pred.get("grade","?")
    rate  = int((pred.get("predicted_high_eng_rate",0.54))*100)
    print(f"  PREDICTED ENGAGEMENT  →  Grade {grade}  ({rate}% high eng)  [{pred.get('confidence','?')} confidence]")
    print(f"  {sep}\n")

    print(f"  ── PRODUCTION SPEC ──────────────────────────────────────────")
    print(f"  Format:      {prod.get('format') or '—'}")
    print(f"  Setting:     {prod.get('setting') or '—'}")
    print(f"  Lighting:    {prod.get('lighting') or '—'}")
    print(f"  Composition: {prod.get('composition') or '—'}  [{prod.get('composition_verdict') or '—'}]")

    print(f"\n  ── CAPTION SPEC ─────────────────────────────────────────────")
    print(f"  Register:    {cap.get('register') or '—'}")
    print(f"  Tone:        {cap.get('tone') or '—'}")
    print(f"  Language:    {cap.get('language') or '—'}")
    print(f"  Add CTA:     {'YES' if cap.get('add_cta') else 'NO'}")
    print(f"  Framing:     {cap.get('heritage_vs_modern') or '—'}")

    print(f"\n  ── CULTURAL SPEC ────────────────────────────────────────────")
    print(f"  Target hospitality cues: {cult.get('hospitality_cues_target',2)}+")
    print(f"  Example cues: {', '.join(cult.get('hospitality_cue_examples',[]))}")

    print(f"\n  ── RECOMMENDED PATTERNS ─────────────────────────────────────")
    for p in (pats.get("recommended") or []):
        print(f"    ✓ {p}")
    if pats.get("avoid_for_this_goal"):
        print(f"\n  ── AVOID FOR THIS GOAL ──────────────────────────────────────")
        for p in pats["avoid_for_this_goal"]:
            print(f"    ✗ {p}")

    if brief.get("competitive_gaps"):
        print(f"\n  ── COMPETITOR GAPS (@{inp.get('account','?')}) ───────────────────────")
        for g in brief["competitive_gaps"][:3]:
            print(f"    [{g['priority'].upper()}] {g['pattern']} — {int(g['competitor_high_eng_rate']*100)}% eng by {', '.join(g['used_by_accounts'][:2])}")

    print(f"\n{'═'*65}\n")


def main():
    parser = argparse.ArgumentParser(description="OGZ Production Brief Generator")
    parser.add_argument("--sector",    type=str, help="Sector (food_and_beverage/beauty_personal_care/retail_lifestyle)")
    parser.add_argument("--occasion",  type=str, help="Occasion (ramadan/national_day/eid_al_fitr/evergreen/etc)")
    parser.add_argument("--goal",      type=str, default="brand_building",
                        help="Content goal (brand_building/product_launch/offer_promotion/community/awareness)")
    parser.add_argument("--account",   type=str, default=None, help="Account handle (optional, for gap analysis)")
    parser.add_argument("--save",      action="store_true", help="Save brief to logs/production_briefs/")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if args.interactive or not args.sector:
        print("\nOGZ Production Brief Generator — Interactive Mode")
        print("─" * 50)
        print("Sectors: food_and_beverage | beauty_personal_care | retail_lifestyle")
        sector = input("Sector: ").strip().lower()
        sector = SECTOR_ALIASES.get(sector, sector)
        print("Occasions: ramadan | national_day | eid_al_fitr | eid_al_adha | founding_day | evergreen | ...")
        occasion = input("Occasion: ").strip().lower().replace(" ","_")
        print("Goals: brand_building | product_launch | offer_promotion | community | awareness")
        goal = input("Goal [brand_building]: ").strip().lower() or "brand_building"
        account = input("Account handle (optional): ").strip().lower() or None
    else:
        sector  = SECTOR_ALIASES.get(args.sector.lower(), args.sector.lower())
        occasion = args.occasion.lower().replace(" ","_")
        goal    = args.goal.lower()
        account = args.account

    brief = generate_brief(sector, occasion, goal, account)
    print_brief(brief)

    if args.save or (args.interactive and input("Save brief? [y/N]: ").strip().lower() == "y"):
        briefs_dir = LOGS / "production_briefs"
        briefs_dir.mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = f"brief_{sector}_{occasion}_{goal}_{ts}.json"
        (briefs_dir / fname).write_text(json.dumps(brief, ensure_ascii=False, indent=2))
        print(f"Saved: logs/production_briefs/{fname}")


if __name__ == "__main__":
    main()
