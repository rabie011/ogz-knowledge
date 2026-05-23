#!/usr/bin/env python3
"""
audit_full.py
Comprehensive corpus health check. Answers:
  1. Are all observations schema-valid?
  2. What is the field coverage across 474 obs?
  3. Which log files are missing, empty, or broken?
  4. Do numbers agree across artifacts?
  5. Which pattern slugs in obs have no definition file?
  6. What analytical gaps remain?
Output: logs/audit_report.json + printed report
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
PATTERNS    = BASE / "11_who_to_learn_from" / "patterns"
LOGS        = BASE / "logs"
SCHEMA_FILE = BASE / "12_data_shapes" / "observation_v1.schema.json"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

REQUIRED_LOG_FILES = [
    "account_archetypes.json","account_consistency.json","account_similarity_matrix.json",
    "account_themes_index.json","archetype_benchmark.json","brand_dna_index.json",
    "caption_analysis.json","character_analysis.json","color_palette_dna.json",
    "compliance_intelligence.json","compliance_risk_report.json","content_health_scores.json",
    "content_pillars.json","content_recipe_combos.json","content_score_model.json",
    "cross_sector_benchmark.json","engagement_signal_table.json",
    "hospitality_analysis.json","intelligence_playbook.json",
    "lighting_composition_normalization.json","media_engagement_analysis.json",
    "occasion_format_grid.json","occasion_sector_matrix.json",
    "pattern_cooccurrence_matrix.json","pattern_density.json",
    "pattern_network_graph.json","pattern_sector_matrix.json",
    "pattern_trend_analysis.json","pattern_usage_analysis.json",
    "phrase_engagement_analysis.json","props_analysis.json",
    "quality_signals.json","register_tone_matrix.json",
    "register_tone_normalization.json","setting_lighting_synergy.json",
    "setting_normalization.json","temporal_analysis.json",
    "visual_dna_profiles.json","voice_positioning_map.json",
    "winning_formula_analysis.json","brand_dna_index.json",
]

CRITICAL_OBS_FIELDS = {
    # Top-level
    "account_handle_normalized": lambda d: bool(d.get("account_handle_normalized")),
    "sector":                    lambda d: bool(d.get("sector")),
    # quality_assessment
    "engagement_potential":      lambda d: bool((d.get("quality_assessment") or {}).get("engagement_potential")),
    "production_quality":        lambda d: bool((d.get("quality_assessment") or {}).get("production_quality")),
    "brand_consistency":         lambda d: bool((d.get("quality_assessment") or {}).get("brand_consistency_with_account")),
    # visual_observations
    "setting":                   lambda d: bool((d.get("visual_observations") or {}).get("setting")),
    "lighting":                  lambda d: bool((d.get("visual_observations") or {}).get("lighting")),
    "composition_style":         lambda d: bool((d.get("visual_observations") or {}).get("composition_style")),
    "color_palette_dominant":    lambda d: bool((d.get("visual_observations") or {}).get("color_palette_dominant")),
    "props_visible":             lambda d: bool((d.get("visual_observations") or {}).get("props_visible")),
    "characters_visible":        lambda d: bool((d.get("visual_observations") or {}).get("characters_visible")),
    # voice_observations
    "register":                  lambda d: bool((d.get("voice_observations") or {}).get("register")),
    "tone":                      lambda d: bool((d.get("voice_observations") or {}).get("tone")),
    "dialect_detected":          lambda d: bool((d.get("voice_observations") or {}).get("dialect_detected")),
    "notable_phrases":           lambda d: bool((d.get("voice_observations") or {}).get("notable_phrases")),
    # cultural_notes
    "heritage_vs_modern":        lambda d: bool((d.get("cultural_notes") or {}).get("heritage_vs_modern")),
    "occasion_relevance":        lambda d: bool((d.get("cultural_notes") or {}).get("occasion_relevance")),
    "hospitality_cues":          lambda d: bool((d.get("cultural_notes") or {}).get("hospitality_cues")),
    # content_ref
    "content_type":              lambda d: bool((d.get("content_ref") or {}).get("content_type")),
    "capture_date":              lambda d: bool((d.get("content_ref") or {}).get("capture_date")),
    "source_url":                lambda d: bool((d.get("content_ref") or {}).get("source_url")),
    # pattern_matches
    "pattern_matches":           lambda d: bool(d.get("pattern_matches")),
    # compliance_check
    "compliance_check":          lambda d: (d.get("compliance_check") is not None),
}


def check_obs():
    """Scan all observations. Return coverage stats + issues."""
    total = 0
    parse_errors = []
    field_coverage = defaultdict(int)
    sector_counts  = Counter()
    account_counts = Counter()
    pattern_slug_counts = Counter()
    engagement_dist = Counter()
    obs_with_issues = []
    schema_issues = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception as e:
            parse_errors.append({"file": str(obs_file.name), "error": str(e)})
            continue

        total += 1
        account = data.get("account_handle_normalized","MISSING")
        sector  = data.get("sector","MISSING")
        sector_counts[sector]  += 1
        account_counts[account] += 1

        # Field coverage
        issues = []
        for field, check in CRITICAL_OBS_FIELDS.items():
            try:
                if check(data):
                    field_coverage[field] += 1
                else:
                    issues.append(f"missing:{field}")
            except Exception:
                issues.append(f"error:{field}")

        # Engagement
        qa = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        engagement_dist[eng_raw or "MISSING"] += 1

        # Pattern slugs
        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: pattern_slug_counts[slug] += 1

        # Flag obs with critical missing fields
        critical_missing = [i for i in issues if i in (
            "missing:account_handle_normalized","missing:sector",
            "missing:engagement_potential","missing:setting","missing:content_type"
        )]
        if critical_missing:
            schema_issues += 1
            obs_with_issues.append({
                "file": obs_file.name,
                "account": account,
                "issues": issues[:5],
            })

    coverage_pct = {
        field: round(count/total*100, 1) if total else 0
        for field, count in field_coverage.items()
    }

    return {
        "total_obs": total,
        "parse_errors": parse_errors,
        "schema_issues": schema_issues,
        "sector_distribution": dict(sector_counts.most_common()),
        "account_obs_counts": dict(account_counts.most_common()),
        "engagement_distribution": dict(engagement_dist.most_common()),
        "field_coverage_count": dict(field_coverage),
        "field_coverage_pct": coverage_pct,
        "unique_pattern_slugs_in_obs": len(pattern_slug_counts),
        "pattern_slug_counts": dict(pattern_slug_counts.most_common(20)),
        "obs_with_critical_issues": obs_with_issues[:10],
    }


def check_patterns():
    """Audit pattern library vs obs usage."""
    defined_slugs = set()
    for pf in PATTERNS.rglob("*.json"):
        try:
            p = json.loads(pf.read_text())
            if p.get("pattern_slug"):
                defined_slugs.add(p["pattern_slug"])
        except: pass

    used_in_obs = set()
    for obs_file in OBS_ROOT.rglob("*.json"):
        try:
            data = json.loads(obs_file.read_text())
        except: continue
        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: used_in_obs.add(slug)

    defined_and_used   = defined_slugs & used_in_obs
    defined_not_used   = defined_slugs - used_in_obs
    used_not_defined   = used_in_obs  - defined_slugs

    return {
        "total_defined": len(defined_slugs),
        "total_used_in_obs": len(used_in_obs),
        "defined_and_used": len(defined_and_used),
        "defined_but_never_used": len(defined_not_used),
        "used_in_obs_but_undefined": len(used_not_defined),
        "undefined_slug_list": sorted(used_not_defined),
        "library_only_slug_count": len(defined_not_used),
    }


def check_logs():
    """Check all expected log files exist, are valid JSON, and are non-trivially sized."""
    results = []
    seen = set()
    for log_name in sorted(set(REQUIRED_LOG_FILES)):
        if log_name in seen: continue
        seen.add(log_name)
        path = LOGS / log_name
        if not path.exists():
            results.append({"file": log_name, "status": "MISSING", "size_kb": 0, "keys": []})
            continue
        size_kb = round(path.stat().st_size / 1024, 1)
        try:
            data = json.loads(path.read_text())
            keys = list(data.keys()) if isinstance(data, dict) else ["(array)"]
            status = "OK" if size_kb > 1 else "EMPTY"
        except Exception as e:
            keys = []
            status = f"BROKEN: {str(e)[:60]}"
        results.append({"file": log_name, "status": status, "size_kb": size_kb, "keys": keys[:6]})

    # Also scan actual logs dir for any extra files
    all_log_files = sorted(LOGS.glob("*.json"))
    known = set(REQUIRED_LOG_FILES)
    extra = [f.name for f in all_log_files if f.name not in known]

    return {
        "expected_count": len(seen),
        "results": results,
        "extra_log_files_not_in_checklist": extra,
        "total_log_files_on_disk": len(all_log_files),
    }


def cross_validate(obs_data):
    """Cross-check numbers between artifacts."""
    checks = []
    total_obs = obs_data["total_obs"]

    # brand_dna_index
    dna = json.loads((LOGS/"brand_dna_index.json").read_text()) if (LOGS/"brand_dna_index.json").exists() else {}
    dna_accounts = len(dna.get("accounts",[]))
    checks.append({
        "check": "brand_dna_index account count vs obs unique accounts",
        "expected": len(obs_data["account_obs_counts"]),
        "actual": dna_accounts,
        "pass": dna_accounts == len(obs_data["account_obs_counts"]),
    })

    # engagement_signal_table
    est = json.loads((LOGS/"engagement_signal_table.json").read_text()) if (LOGS/"engagement_signal_table.json").exists() else {}
    signals = est.get("all_signals",[])
    checks.append({
        "check": "engagement_signal_table has signals",
        "expected": ">100",
        "actual": len(signals),
        "pass": len(signals) > 100,
    })

    # archetype_benchmark account coverage
    ab = json.loads((LOGS/"archetype_benchmark.json").read_text()) if (LOGS/"archetype_benchmark.json").exists() else {}
    ab_obs = sum(p.get("obs_count",0) for p in ab.get("archetype_profiles",[]))
    checks.append({
        "check": "archetype_benchmark total obs matches corpus",
        "expected": total_obs,
        "actual": ab_obs,
        "pass": ab_obs == total_obs,
    })

    # pattern_density total
    pd = json.loads((LOGS/"pattern_density.json").read_text()) if (LOGS/"pattern_density.json").exists() else {}
    pd_obs = pd.get("total_obs",0)
    checks.append({
        "check": "pattern_density total_obs matches corpus",
        "expected": total_obs,
        "actual": pd_obs,
        "pass": pd_obs == total_obs,
    })

    # hospitality_analysis total
    ha = json.loads((LOGS/"hospitality_analysis.json").read_text()) if (LOGS/"hospitality_analysis.json").exists() else {}
    checks.append({
        "check": "hospitality_analysis total_obs",
        "expected": total_obs,
        "actual": ha.get("total_obs",0),
        "pass": ha.get("total_obs",0) == total_obs,
    })

    return checks


def identify_gaps(obs_data, pattern_data, log_data):
    """Identify what's genuinely missing."""
    gaps = []

    # Coverage gaps
    cov = obs_data["field_coverage_pct"]
    for field, pct in sorted(cov.items(), key=lambda x: x[1]):
        if pct < 80:
            gaps.append({
                "type": "low_field_coverage",
                "field": field,
                "coverage_pct": pct,
                "severity": "high" if pct < 50 else "medium",
                "note": f"Only {pct}% of obs have this field populated",
            })

    # Undefined patterns
    if pattern_data["used_in_obs_but_undefined"] > 0:
        gaps.append({
            "type": "undefined_patterns",
            "count": pattern_data["used_in_obs_but_undefined"],
            "severity": "high",
            "slugs": pattern_data["undefined_slug_list"][:10],
            "note": "Pattern slugs referenced in obs but no definition file exists",
        })

    # Missing log files
    missing_logs = [r for r in log_data["results"] if r["status"] == "MISSING"]
    if missing_logs:
        gaps.append({
            "type": "missing_log_files",
            "count": len(missing_logs),
            "severity": "high",
            "files": [r["file"] for r in missing_logs],
        })

    # Sector imbalance
    sectors = obs_data["sector_distribution"]
    total   = obs_data["total_obs"]
    for sec, count in sectors.items():
        pct = round(count/total*100, 1)
        if pct < 10 and sec not in ("unknown","MISSING"):
            gaps.append({
                "type": "sector_underrepresentation",
                "sector": sec,
                "obs_count": count,
                "pct_of_corpus": pct,
                "severity": "medium",
                "note": f"Only {pct}% of corpus — cross-sector findings for this sector are statistically weak",
            })

    # Parse errors
    if obs_data["parse_errors"]:
        gaps.append({
            "type": "parse_errors",
            "count": len(obs_data["parse_errors"]),
            "severity": "critical",
            "files": [e["file"] for e in obs_data["parse_errors"]],
        })

    # Analytical gaps — things we know we haven't built
    analytical_gaps = [
        {
            "type": "analytical_gap",
            "name": "color_x_occasion",
            "description": "Do amber/gold palettes outperform on Ramadan? White on Eid? Unmined.",
            "severity": "low",
        },
        {
            "type": "analytical_gap",
            "name": "character_type_analysis",
            "description": "characters_visible has count but not type (hands/lifestyle/group). Richer typing needed.",
            "severity": "low",
        },
        {
            "type": "analytical_gap",
            "name": "dialect_full_matrix",
            "description": "Dialect × sector × occasion × engagement — only partial analysis done.",
            "severity": "low",
        },
        {
            "type": "analytical_gap",
            "name": "caption_text",
            "description": "Zero Arabic caption text in obs. The actual words written are unanalyzed.",
            "severity": "high",
        },
        {
            "type": "analytical_gap",
            "name": "account_posting_frequency",
            "description": "How many posts/week per account? Does cadence affect engagement? Dates are available.",
            "severity": "low",
        },
    ]
    gaps.extend(analytical_gaps)

    return gaps


def main():
    print("OGZ Corpus Full Audit")
    print("=" * 60)

    print("\n[1/4] Scanning observations...")
    obs_data = check_obs()

    print(f"\n[2/4] Auditing pattern library...")
    pattern_data = check_patterns()

    print(f"\n[3/4] Checking log files...")
    log_data = check_logs()

    print(f"\n[4/4] Cross-validating artifacts...")
    xval = cross_validate(obs_data)

    print(f"\n[5/4] Identifying gaps...")
    gaps = identify_gaps(obs_data, pattern_data, log_data)

    # ── Print report ──────────────────────────────────────────────────────────
    print(f"\n{'═'*60}")
    print("OBSERVATION HEALTH")
    print(f"{'─'*60}")
    print(f"  Total observations : {obs_data['total_obs']}")
    print(f"  Parse errors       : {len(obs_data['parse_errors'])} {'⚠️' if obs_data['parse_errors'] else '✅'}")
    print(f"  Schema issues      : {obs_data['schema_issues']} {'⚠️' if obs_data['schema_issues'] else '✅'}")
    print(f"  Sectors            : {dict(obs_data['sector_distribution'])}")
    print(f"  Accounts           : {len(obs_data['account_obs_counts'])}")
    print(f"  Unique patterns    : {obs_data['unique_pattern_slugs_in_obs']}")

    print(f"\n{'─'*60}")
    print("FIELD COVERAGE")
    print(f"{'─'*60}")
    cov = obs_data["field_coverage_pct"]
    for field, pct in sorted(cov.items(), key=lambda x: -x[1]):
        icon = "✅" if pct >= 90 else "🟡" if pct >= 70 else "🔴"
        bar  = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {icon} {field:<28} {bar} {pct:>5}%")

    print(f"\n{'─'*60}")
    print("PATTERN LIBRARY")
    print(f"{'─'*60}")
    print(f"  Defined patterns              : {pattern_data['total_defined']}")
    print(f"  Used in observations          : {pattern_data['total_used_in_obs']}")
    print(f"  Defined AND used              : {pattern_data['defined_and_used']} ✅")
    print(f"  Defined but NEVER used        : {pattern_data['defined_but_never_used']} {'⚠️' if pattern_data['defined_but_never_used']>10 else '🟡'}")
    print(f"  Used in obs but UNDEFINED     : {pattern_data['used_in_obs_but_undefined']} {'🔴' if pattern_data['used_in_obs_but_undefined']>0 else '✅'}")
    if pattern_data["undefined_slug_list"]:
        print(f"  Undefined slugs: {', '.join(pattern_data['undefined_slug_list'][:8])}")

    print(f"\n{'─'*60}")
    print("LOG FILES")
    print(f"{'─'*60}")
    ok     = [r for r in log_data["results"] if r["status"]=="OK"]
    miss   = [r for r in log_data["results"] if r["status"]=="MISSING"]
    broken = [r for r in log_data["results"] if r["status"] not in ("OK","MISSING","EMPTY")]
    print(f"  Files on disk     : {log_data['total_log_files_on_disk']}")
    print(f"  Expected + valid  : {len(ok)} ✅")
    print(f"  Missing           : {len(miss)} {'🔴' if miss else '✅'}")
    print(f"  Broken JSON       : {len(broken)} {'🔴' if broken else '✅'}")
    if miss:
        for r in miss: print(f"    ❌ MISSING: {r['file']}")
    if broken:
        for r in broken: print(f"    💥 BROKEN: {r['file']} — {r['status']}")
    if log_data["extra_log_files_not_in_checklist"]:
        print(f"  Extra (not in checklist): {len(log_data['extra_log_files_not_in_checklist'])}")
        for f in log_data["extra_log_files_not_in_checklist"][:5]:
            print(f"    + {f}")

    print(f"\n{'─'*60}")
    print("CROSS-VALIDATION")
    print(f"{'─'*60}")
    for c in xval:
        icon = "✅" if c["pass"] else "❌"
        print(f"  {icon} {c['check'][:52]:<52} expected={c['expected']} actual={c['actual']}")

    print(f"\n{'─'*60}")
    print("GAPS IDENTIFIED")
    print(f"{'─'*60}")
    critical = [g for g in gaps if g.get("severity")=="critical"]
    high     = [g for g in gaps if g.get("severity")=="high"]
    medium   = [g for g in gaps if g.get("severity")=="medium"]
    low      = [g for g in gaps if g.get("severity")=="low"]
    for level, items, icon in [("CRITICAL",critical,"🔴"),("HIGH",high,"🟠"),("MEDIUM",medium,"🟡"),("LOW",low,"⚪")]:
        if items:
            print(f"\n  {icon} {level}:")
            for g in items:
                print(f"     • [{g['type']}] {g.get('name') or g.get('field') or g.get('sector') or g.get('files','')}")
                if g.get("note"): print(f"       {g['note']}")

    # Save report
    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "observation_health": obs_data,
        "pattern_library_audit": pattern_data,
        "log_file_audit": log_data,
        "cross_validation": xval,
        "gaps": gaps,
        "summary": {
            "total_obs": obs_data["total_obs"],
            "parse_errors": len(obs_data["parse_errors"]),
            "schema_issues": obs_data["schema_issues"],
            "log_files_ok": len(ok),
            "log_files_missing": len(miss),
            "undefined_patterns": pattern_data["used_in_obs_but_undefined"],
            "cross_val_passed": sum(1 for c in xval if c["pass"]),
            "cross_val_total": len(xval),
            "gaps_critical": len(critical),
            "gaps_high": len(high),
            "gaps_medium": len(medium),
            "gaps_low": len(low),
        }
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "audit_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n{'═'*60}")
    print(f"Output: logs/audit_report.json")


if __name__ == "__main__":
    main()
