#!/usr/bin/env python3
"""
build_intelligence_playbook_v2.py
Master intelligence playbook — synthesizes ALL analytics logs into a single
strategic document. Rebuilt May 2026 with 648 obs, all new dimensions included.
Output: logs/intelligence_playbook.json   (overwrites v1)
"""
import json
from pathlib import Path
from datetime import datetime

LOGS = Path(__file__).parent.parent / "logs"

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}

def _top(lst, key="avg_engagement", n=5, min_n=2):
    return sorted([x for x in lst if isinstance(x,dict) and (x.get("count") or x.get("n") or 0) >= min_n],
                  key=lambda x: -(x.get(key) or 0))[:n]


def main():
    # Load all analytics
    ct_an   = _load("content_type_analysis.json")
    dow     = _load("day_of_week_analysis.json")
    tone_r  = _load("tone_register_analysis.json")
    cult    = _load("cultural_signal_analysis.json")
    pat     = _load("pattern_engagement.json")
    set_an  = _load("setting_analysis.json")
    light   = _load("lighting_analysis.json")
    comp    = _load("composition_analysis.json")
    css     = _load("composition_setting_synergy.json")
    vc      = _load("visual_complexity_analysis.json")
    wg      = _load("wardrobe_gender_analysis.json")
    hosp    = _load("hospitality_intelligence.json")
    cap_lh  = _load("caption_length_hashtag_analysis.json")
    cap_s   = _load("caption_intelligence_by_sector.json")
    ar_s    = _load("arabic_copywriting_by_sector.json")
    hash_a  = _load("hashtag_strategy.json")
    npi     = _load("notable_phrases_intelligence.json")
    evw     = _load("elite_vs_weak_dna.json")
    toi     = _load("text_overlay_intelligence.json")
    sfp     = _load("sector_fingerprint.json")
    osf     = _load("occasion_sector_format_matrix.json")
    mst     = _load("master_signal_table.json")
    acc     = _load("account_performance_analysis.json")
    opp     = _load("occasion_playbook.json")
    wf      = _load("winning_formula_analysis.json")
    props   = _load("props_taxonomy.json")
    car     = _load("carousel_analysis.json")
    vid     = _load("video_strategy_analysis.json")
    pfa     = _load("posting_frequency_analysis.json")

    corpus_total = 648
    global_avg = ct_an.get("global_avg") or 0.65

    # ── SECTION 1: Format Intelligence ──────────────────────────────────────
    ct_by_type = ct_an.get("by_content_type") or {}
    ar_by_type = ct_an.get("by_aspect_ratio") or {}
    combos     = ct_an.get("combo_matrix") or []

    format_section = {
        "question": "What format maximises engagement?",
        "by_content_type": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted(ct_by_type.items(), key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "by_aspect_ratio": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted(ar_by_type.items(), key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "top_combos": [{
            "combo": f"{c['content_type']} + {c['aspect_ratio']}",
            "avg": c.get("avg_engagement",0), "n": c.get("count",0)
        } for c in (combos or [])[:5]],
        "occasion_sector_matrix": (osf.get("quick_ref_matrix") or {}),
        "agency_rules": ct_an.get("agency_rules") or [],
    }

    # ── SECTION 2: Visual Intelligence ──────────────────────────────────────
    set_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
              for k,v in sorted((set_an.get("by_setting") or {}).items(),
                                key=lambda x: -(x[1].get("avg_engagement") or 0))[:8]}
    lit_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
              for k,v in sorted((light.get("by_lighting") or {}).items(),
                                key=lambda x: -(x[1].get("avg_engagement") or 0))[:6]}
    comp_by= {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
              for k,v in sorted((comp.get("by_composition") or {}).items(),
                                key=lambda x: -(x[1].get("avg_engagement") or 0))[:6]}
    vc_by  = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
              for k,v in sorted((vc.get("by_complexity") or {}).items(),
                                key=lambda x: -(x[1].get("avg_engagement") or 0))}
    css_top= (css.get("all_combos_ranked") or [])[:5]

    visual_section = {
        "question": "What visual approach drives engagement?",
        "by_setting":     set_by,
        "by_lighting":    lit_by,
        "by_composition": comp_by,
        "by_complexity":  vc_by,
        "complexity_uplift": vc.get("complexity_uplift_vs_simple"),
        "best_combos":    [{"combo": c.get("combo"), "avg": c.get("avg_engagement",0), "n": c.get("count",0)}
                           for c in css_top],
        "human_presence_lift": wg.get("human_presence_lift"),
        "agency_rules":   (vc.get("agency_rules") or []) + (set_an.get("agency_rules") or []),
    }

    # ── SECTION 3: Voice Intelligence ────────────────────────────────────────
    tone_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
               for k,v in sorted((tone_r.get("by_tone") or {}).items(),
                                 key=lambda x: -(x[1].get("avg_engagement") or 0))[:6]}
    reg_by  = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
               for k,v in sorted((tone_r.get("by_register") or {}).items(),
                                 key=lambda x: -(x[1].get("avg_engagement") or 0))}
    hvm_by  = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
               for k,v in sorted((cult.get("by_heritage_vs_modern") or {}).items(),
                                 key=lambda x: -(x[1].get("avg_engagement") or 0))}
    dial_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
               for k,v in sorted((cult.get("by_dialect") or {}).items(),
                                 key=lambda x: -(x[1].get("avg_engagement") or 0))[:6]}

    voice_section = {
        "question": "What tone and voice signals drive engagement?",
        "by_tone":     tone_by,
        "by_register": reg_by,
        "heritage_vs_modern": hvm_by,
        "heritage_uplift": cult.get("heritage_uplift_vs_modern"),
        "by_dialect":  dial_by,
        "agency_rules": (tone_r.get("agency_rules") or []) + (cult.get("agency_rules") or []),
    }

    # ── SECTION 4: Caption Intelligence ──────────────────────────────────────
    wc_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
             for k,v in sorted((cap_lh.get("by_word_count") or {}).items(),
                               key=lambda x: -(x[1].get("avg_engagement") or 0))}
    hc_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
             for k,v in sorted((cap_lh.get("by_hashtag_count") or {}).items(),
                               key=lambda x: -(x[1].get("avg_engagement") or 0))}
    em_by = cap_lh.get("by_emoji") or {}
    op_by = {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
             for k,v in sorted((cap_lh.get("by_opener_formula") or {}).items(),
                               key=lambda x: -(x[1].get("avg_engagement") or 0))}

    caption_section = {
        "question": "How should captions be written?",
        "by_word_count":   wc_by,
        "by_hashtag_count":hc_by,
        "by_emoji":        {k: round((v.get("avg_engagement") or 0),3) for k,v in em_by.items()},
        "by_opener_formula": op_by,
        "agency_rules":    cap_lh.get("agency_rules") or [],
    }

    # ── SECTION 5: Notable Phrases ─────────────────────────────────────────
    phrases_section = {
        "question": "What Arabic phrases drive the highest engagement?",
        "arabic_avg": npi.get("arabic_avg"),
        "english_avg": npi.get("english_avg"),
        "by_category": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted((npi.get("by_category") or {}).items(),
                              key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "elite_phrases": [{
            "phrase": p["phrase"],
            "avg_engagement": p["avg_engagement"],
            "n": p["count"],
            "categories": p.get("categories",[]),
        } for p in (npi.get("elite_phrases") or [])[:15]],
        "avoid_phrases": [p["phrase"] for p in (npi.get("avoid_phrases") or [])[:5]],
        "agency_rules": npi.get("agency_rules") or [],
    }

    # ── SECTION 6: Occasion Intelligence ────────────────────────────────────
    occ_matrix = osf.get("quick_ref_matrix") or {}
    occ_rules  = []
    for occ in ["eid_al_fitr","ramadan","national_day","founding_day","evergreen"]:
        best_row = next((r for r in (osf.get("full_table") or [])
                         if r.get("occasion")==occ and r.get("count",0)>=3), None)
        if best_row:
            occ_rules.append(f"{occ}: use {best_row['content_type']} "
                             f"({best_row['avg_engagement']:.0%}, n={best_row['count']})")

    occasion_section = {
        "question": "What format and approach works best per occasion?",
        "occasion_sector_matrix": occ_matrix,
        "top_combos": (osf.get("full_table") or [])[:10],
        "agency_rules": occ_rules + (opp.get("agency_rules") or [])[:3],
    }

    # ── SECTION 7: Posting Day ───────────────────────────────────────────────
    dow_section = {
        "question": "Which day of the week produces the highest engagement?",
        "ranked_days": dow.get("ranked_days") or [],
        "by_day": {k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
                   for k,v in (dow.get("by_day") or {}).items()},
        "best_by_sector": dow.get("best_by_sector") or {},
        "best_by_occasion": dow.get("best_by_occasion") or {},
        "agency_rules": dow.get("agency_rules") or [],
    }

    # ── SECTION 8: Hospitality Intelligence ─────────────────────────────────
    hosp_section = {
        "question": "What hospitality cues maximise engagement?",
        "by_cue_group": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted((hosp.get("by_cue_group") or {}).items(),
                              key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "top_cues": hosp.get("top_cues_by_engagement") or [],
        "agency_rules": hosp.get("agency_rules") or [],
    }

    # ── SECTION 9: Text Overlay Intelligence ────────────────────────────────
    overlay_section = {
        "question": "Should posts include text overlays, and in what language?",
        "has_overlay_avg": toi.get("has_overlay_avg"),
        "no_overlay_avg": toi.get("no_overlay_avg"),
        "overlay_presence_lift": toi.get("overlay_presence_lift"),
        "by_language": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted((toi.get("by_language") or {}).items(),
                              key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "by_overlay_type": {
            k: {"avg": round(v.get("avg_engagement",0),3), "n": v.get("count",0)}
            for k,v in sorted((toi.get("by_overlay_type") or {}).items(),
                              key=lambda x: -(x[1].get("avg_engagement") or 0))
        },
        "agency_rules": toi.get("agency_rules") or [],
    }

    # ── SECTION 10: Sector Fingerprints ─────────────────────────────────────
    sector_section = {
        "question": "What makes each sector's content distinct?",
        "sectors": {
            k: {
                "avg_engagement": v.get("avg_engagement"),
                "lift_vs_corpus": v.get("lift_vs_corpus"),
                "obs_count": v.get("obs_count"),
                "dominant_signals": {
                    dim: {"value": (dv.get("dominant")), "pct": dv.get("dominant_pct")}
                    for dim, dv in (v.get("profile") or {}).items()
                },
            }
            for k,v in (sfp.get("sectors") or {}).items()
        },
        "differentiating_dimensions": [d["dimension"] for d in (sfp.get("differentiators") or [])],
        "agency_rules": sfp.get("agency_rules") or [],
    }

    # ── SECTION 11: Elite vs Weak DNA ───────────────────────────────────────
    dna_section = {
        "question": "What separates elite accounts from weak ones?",
        "elite_accounts": evw.get("elite_accounts") or [],
        "weak_accounts": evw.get("weak_accounts") or [],
        "elite_obs_count": evw.get("elite_obs_count"),
        "weak_obs_count": evw.get("weak_obs_count"),
        "top_elite_advantages": (evw.get("top_elite_advantages") or [])[:10],
        "top_weak_tendencies": (evw.get("top_weak_tendencies") or [])[:8],
        "agency_rules": evw.get("agency_rules") or [],
    }

    # ── SECTION 12: Master Signal Table (top boosters + killers) ────────────
    signals_section = {
        "question": "What are the single biggest engagement boosters and killers?",
        "top_boosters": (mst.get("top_boosters") or [])[:15],
        "top_killers":  (mst.get("top_killers") or [])[:15],
        "agency_rules": (mst.get("agency_rules") or [])[:5],
    }

    # ── SECTION 13: Winning Formulas ────────────────────────────────────────
    formula_section = {
        "question": "What complete content formula (multi-dim) drives the highest engagement?",
        "top_6dim_formulas": (wf.get("top_6dim_formulas") or [])[:8],
        "top_5dim_visual": (wf.get("top_5dim_visual_formulas") or [])[:5],
        "top_vc_format": (wf.get("top_vc_format_formulas") or [])[:5],
        "best_by_occasion": wf.get("best_occasion_formulas") or {},
        "best_by_sector": wf.get("sector_winning_formulas") or {},
    }

    # ── SECTION 14: Carousel Intelligence ───────────────────────────────────
    carousel_section = {
        "question": "How do carousels differ from other formats? What makes them work?",
        "carousel_obs": car.get("meta",{}).get("carousel_obs"),
        "carousel_avg": car.get("meta",{}).get("carousel_avg_engagement"),
        "carousel_lift_vs_corpus": car.get("meta",{}).get("carousel_lift_vs_corpus"),
        "format_comparison": car.get("format_comparison") or {},
        "by_aspect_ratio": car.get("by_aspect_ratio") or [],
        "by_visual_complexity": car.get("by_visual_complexity") or [],
        "by_tone": (car.get("by_tone") or [])[:5],
        "by_occasion": car.get("by_occasion") or [],
        "high_eng_signals": (car.get("high_eng_signals") or [])[:6],
        "winning_formula": car.get("winning_formula") or {},
        "agency_rules": [
            f"Carousels average {(car.get('meta',{}).get('carousel_avg_engagement') or 0):.0%} — second only to reels",
            "Portrait_4x5 appears in 72% of high-engagement carousels (vs landscape-leaning images)",
            "Complex visual_complexity in carousels: 90% engagement vs 66% moderate (+24pp)",
            "Use carousels for: product showcases, storytelling, multi-step reveals",
            "Avoid: moderate visual complexity in carousels — it underperforms every other option",
        ],
    }

    # ── SECTION 15: Video Strategy ──────────────────────────────────────────
    video_section = {
        "question": "When should we use video, and what video formula works?",
        "video_avg": vid.get("meta",{}).get("video_avg_engagement"),
        "video_lift_vs_corpus": vid.get("meta",{}).get("video_lift_vs_corpus"),
        "type_comparison": vid.get("type_comparison") or {},
        "by_duration": vid.get("by_duration") or [],
        "by_aspect_ratio": vid.get("by_aspect_ratio") or [],
        "by_tone": (vid.get("by_tone") or [])[:5],
        "video_vs_static_by_occasion": vid.get("video_vs_static_by_occasion") or [],
        "high_eng_signals": (vid.get("high_eng_signals") or [])[:5],
        "winning_formula": vid.get("winning_formula") or {},
        "agency_rules": [
            "Static content beats video on EVERY tested occasion (founding_day -17pp, national_day -12pp)",
            "Reels (short-form) outperform regular video: 81% vs 59% (-22pp for raw video)",
            "Duration paradox: longer videos (60s+) at 82% vs short (0-15s) at 53% — depth > brevity",
            "For video: landscape_16x9 is best (88%), NOT vertical_9x16 (63%)",
            "Patriotic tone is uniquely powerful in video: 84% — higher than in static content",
            "Default to static unless: brand story, occasion tribute, or product in action",
        ],
    }

    # ── SECTION 16: Posting Cadence ─────────────────────────────────────────
    cadence_section = {
        "question": "How often should accounts post, and on which days?",
        "note": "Temporal data has recency bias — May 2026 dominated (261/548 obs). Use directional only.",
        "by_day_of_week": (pfa.get("by_day_of_week") or [])[:7],
        "cadence_vs_engagement": pfa.get("cadence_vs_engagement") or [],
        "gap_days_vs_engagement": pfa.get("gap_days_vs_engagement") or [],
        "by_occasion_volume": (pfa.get("by_occasion_volume") or [])[:6],
        "sector_cadence": pfa.get("sector_cadence") or [],
        "agency_rules": [
            "Sunday is the best posting day (+4pp) — F&B rule: Sunday/Thursday/Monday",
            "Tuesday is the worst day (-13pp) — avoid for important posts",
            "CAVEAT: cadence × engagement data is confounded by extraction recency bias",
            "Conservative guidance: 3-4 posts/week is the sustainable elite cadence",
            "Post quality > post frequency — accounts posting <1/week outperform daily posters",
        ],
    }

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    # Pull best-performing values across dimensions
    def _best_dim(d_dict):
        if not d_dict: return "?"
        return max(d_dict.items(), key=lambda x: x[1].get("avg",0))[0]

    exec_summary = {
        "corpus_size": corpus_total,
        "global_avg_engagement": round(global_avg, 3),
        "top_5_do": [
            f"Format: {_best_dim(format_section['by_content_type'])} — highest content type",
            f"Visual complexity: complex beats moderate by +28pp (86% vs 58%)",
            f"Heritage framing: +{int((cult.get('heritage_uplift_vs_modern') or 0)*100)}pp uplift vs modern",
            f"Posting day: {(dow.get('ranked_days') or ['sunday'])[0]} beats worst day by ~17pp",
            f"Caption: 10-30 words + 1-5 hashtags = {_best_dim(caption_section['by_word_count'])} wins",
        ],
        "top_5_avoid": [
            f"Content type: video is the weakest format ({(ct_by_type.get('video') or {}).get('avg_engagement',0):.0%})",
            f"Text overlays: posts WITH overlays score {(toi.get('has_overlay_avg') or 0):.0%} vs {(toi.get('no_overlay_avg') or 0):.0%} without",
            f"Aspect ratio: vertical_9x16 massively overindexed by weak accounts (-55pp)",
            f"Visual complexity: moderate complexity is the weakest signal (-28pp vs complex)",
            f"Hashtags: 16+ hashtags underperform — keep to 1-5 for best engagement",
        ],
        "sector_ranking": [
            {"sector": k, "avg": v.get("avg_engagement"), "lift": v.get("lift_vs_corpus")}
            for k,v in sorted((sfp.get("sectors") or {}).items(),
                              key=lambda x: -(x[1].get("avg_engagement") or 0))
        ],
    }

    out = {
        "schema_version": 4,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": "OGZ Saudi Instagram Intelligence Playbook v4",
        "corpus": {
            "total_observations": corpus_total,
            "sectors": ["f_and_b (524)", "beauty (87)", "retail (37)"],
            "global_avg_engagement": round(global_avg, 3),
            "analytics_logs_used": 28,
        },
        "executive_summary": exec_summary,
        "sections": {
            "format":        format_section,
            "visual":        visual_section,
            "voice":         voice_section,
            "caption":       caption_section,
            "phrases":       phrases_section,
            "occasion":      occasion_section,
            "posting_day":   dow_section,
            "hospitality":   hosp_section,
            "overlay":       overlay_section,
            "sector_dna":    sector_section,
            "elite_vs_weak": dna_section,
            "signals":       signals_section,
            "formulas":      formula_section,
            "carousel":      carousel_section,
            "video":         video_section,
            "posting_cadence": cadence_section,
        },
    }

    (LOGS / "intelligence_playbook.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"\nOGZ Intelligence Playbook v{out['schema_version']} — {corpus_total} obs | {global_avg:.0%} corpus avg")
    print(f"\nExecutive Summary:")
    for i, item in enumerate(exec_summary["top_5_do"], 1):
        print(f"  DO  {i}. {item}")
    for i, item in enumerate(exec_summary["top_5_avoid"], 1):
        print(f"  ✗   {i}. {item}")
    print(f"\nSector ranking:")
    for s in exec_summary["sector_ranking"]:
        lift = f"+{s['lift']:.2f}" if (s['lift'] or 0) >= 0 else f"{s['lift']:.2f}"
        print(f"  {s['sector']:<12}  {(s['avg'] or 0):.0%}  lift {lift}")
    print(f"\n  Output → logs/intelligence_playbook.json  ({len(out['sections'])} sections, v{out['schema_version']})")

if __name__ == "__main__":
    main()
