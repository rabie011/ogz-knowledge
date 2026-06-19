#!/usr/bin/env python3
"""brain_router — the shared CD-brain routing module (B035, June 19 2026).

Extracted verbatim from render_client_slot.py so BOTH the render stage AND the
angle stage (build_angle_cards.py — B041) can route on the SAME logic without
the angle script importing the heavy render module (caption_filter, blackout_gate,
post_unit, urllib …). One source of truth for: which brain a slot routes to, and
the brain's full methodology body.

Root-hunt that birthed this (2026-06-14, see brain_method): the angle pen never
received the methodology BODY — only the YAML front-matter — so every brain
collapsed to the generic 'concrete scene' prompt → the brand-mean formula → the
#1 repetition cause. Sharing this module is the prerequisite for routing the full
methodologies into build_angle_cards (B041).
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent

BRAIN_FILES = {"firaasa": "cd_01_firaasa_architect.md", "metaphor": "cd_02_metaphor_architect.md",
                "authenticity": "cd_03_authenticity_detective.md", "heritage": "cd_04_heritage_decoder.md",
                "paradox": "cd_05_paradox_hunter.md"}

# YAML brain ids (cd_NN_name) → the short keys this module routes on.
_BRAIN_KEY = {"cd_01_firaasa_architect": "firaasa", "cd_02_metaphor_architect": "metaphor",
              "cd_03_authenticity_detective": "authenticity", "cd_04_heritage_decoder": "heritage",
              "cd_05_paradox_hunter": "paradox"}

ROUTER_RULES_YAML = BASE / "10_agent_brains" / "cd_brain_router_rules.yaml"
ROUTING_LOG = BASE / "logs" / "routing_decision.jsonl"
_DAILY = ("metaphor", "paradox", "firaasa", "authenticity")
# Known emotional occasions the YAML occasion_overrides does NOT (yet) cover — they keep the
# validated firaasa+authenticity pair so wiring the YAML never silently REGRESSES them (B053).
_EMOTIONAL_FALLBACK = ("arab_mothers_day", "hajj_season")

_RULES_CACHE = None


def load_router_rules(path: Path = ROUTER_RULES_YAML) -> dict:
    """Load the provenance-backed routing rules from cd_brain_router_rules.yaml (B053, June 19 2026).
    The YAML — not a hardcoded copy — is the source of truth for which CD brain leads each occasion
    (occasion_overrides) and which brains a sector forbids (sector_safety_locks). Returns short-key
    maps: {occasion: [brain,...]} and {sector: [forbidden_brain,...]}. Parse failure → empty maps
    (the deterministic daily/emotional defaults still hold; a missing YAML can never break a render).
    Cached so the file is read once per process."""
    global _RULES_CACHE
    if _RULES_CACHE is not None and path == ROUTER_RULES_YAML:
        return _RULES_CACHE
    occ_over, sector_locks = {}, {}
    try:
        import yaml
        d = yaml.safe_load(Path(path).read_text()) or {}
        for occ, spec in (d.get("occasion_overrides") or {}).items():
            brains = [_BRAIN_KEY.get(b, b) for b in (spec.get("boost_brains") or [])]
            if brains:
                occ_over[occ] = brains
        for sec, spec in (d.get("sector_safety_locks") or {}).items():
            sector_locks[sec] = [_BRAIN_KEY.get(b, b) for b in (spec.get("forbidden_brains") or [])]
    except Exception:
        pass
    rules = {"occasion_overrides": occ_over, "sector_safety_locks": sector_locks}
    if path == ROUTER_RULES_YAML:
        _RULES_CACHE = rules
    return rules


def _apply_sector_lock(dec: dict, sector: str) -> dict:
    """Enforce sector_safety_locks (B053): if the routed primary is a brain the slot's sector
    forbids (e.g. healthcare_wellness forbids paradox), swap to the first eligible brain —
    prefer a clean secondary, else the next non-forbidden daily brain — and record the lock.
    Born from the real myfitness.sa gap: a healthcare daily slot could route to paradox."""
    forbidden = load_router_rules()["sector_safety_locks"].get(sector or "", [])
    if not forbidden or dec.get("primary") not in forbidden:
        return dec
    secondary = dec.get("secondary")
    repl = secondary if (secondary and secondary not in forbidden) else next(
        (b for b in _DAILY if b not in forbidden), None)
    if not repl:
        return dec   # nothing eligible — leave as-is rather than route to nothing
    two_cd = [repl] + [b for b in dec.get("two_cd_diagnostic", []) if b not in forbidden and b != repl]
    return {**dec, "primary": repl, "secondary": (secondary if secondary not in forbidden else None),
            "two_cd_diagnostic": two_cd or [repl],
            "safety_locks": dec.get("safety_locks", []) + [f"sector_forbids:{sector}:{dec['primary']}"],
            "overrides": dec.get("overrides", []) + [f"sector_lock:{sector}"]}


def route_decision(slot: dict, alt: int = 0) -> dict:
    """The FULL routing decision behind route_brain (B051, June 19 2026) — the audit record
    the bare brain-string threw away. Deterministic, so `scores` is empty by design (Rule #9:
    don't invent soft scores the router doesn't compute). Fields: primary, secondary,
    two_cd_diagnostic, trigger_reason, safety_locks, overrides, daily_seed, occasion, slot_type.
    route_brain() returns decision['primary'] — same answer, now observable."""
    occ = slot.get("occasion") or ""
    sector = slot.get("sector") or ""
    rules = load_router_rules()
    base = {"occasion": occ, "slot_type": slot.get("type"), "alt": alt, "sector": sector or None,
            "scores": {}, "overrides": [], "safety_locks": [], "secondary": None,
            "daily_seed": None}
    # 1. YAML occasion_overrides — the provenance-backed source of truth (B053). Replaces the old
    # hardcoded national/emotional copy that had DRIFTED from the YAML (ramadan→authenticity+heritage,
    # eid_al_adha→heritage+authenticity, national_day→heritage+metaphor). alt rotates the lead brain.
    yaml_brains = rules["occasion_overrides"].get(occ)
    if yaml_brains:
        n = len(yaml_brains)
        primary = yaml_brains[alt % n]
        secondary = yaml_brains[(alt + 1) % n] if n >= 2 else None
        # heritage make_angle falls back to firaasa when the brand has no Arabic root material
        locks = ["heritage_falls_back_to_firaasa_when_no_root"] if primary == "heritage" else []
        dec = {**base, "primary": primary, "secondary": secondary,
               "two_cd_diagnostic": [b for b in (primary, secondary) if b],
               "trigger_reason": "yaml_occasion_override", "safety_locks": locks,
               "overrides": [f"yaml_occasion:{occ}"]}
        return _apply_sector_lock(dec, sector)
    # 2. known emotional occasions the YAML hasn't specified yet — keep the validated pair
    if occ in _EMOTIONAL_FALLBACK:
        pair = ("firaasa", "authenticity")
        primary, secondary = pair[alt % 2], pair[(alt + 1) % 2]
        dec = {**base, "primary": primary, "secondary": secondary,
               "two_cd_diagnostic": [primary, secondary], "trigger_reason": "emotional_pair"}
        return _apply_sector_lock(dec, sector)
    if slot.get("type") == "competitor_reference":
        dec = {**base, "primary": "paradox", "two_cd_diagnostic": ["paradox"],
               "trigger_reason": "competitor_paradox"}
        return _apply_sector_lock(dec, sector)
    # daily slots: spread across ALL FOUR non-occasion brains (June 14 — the *-11 batch came
    # out 100% paradox because the old 2-brain date-PARITY keyed identical for every date
    # ending in 1; a batch using one brain isn't using the 5-CD-brain range). Digit-sum%4
    # rotates brains even across same-parity / adjacent dates.
    seed = sum(int(ch) for ch in str(slot.get("date", "")) if ch.isdigit()) or alt
    primary = _DAILY[seed % 4]
    dec = {**base, "primary": primary, "two_cd_diagnostic": [primary],
           "trigger_reason": "daily_rotation", "daily_seed": seed}
    return _apply_sector_lock(dec, sector)


def route_brain(slot: dict, alt: int = 0) -> str:
    """Deterministic CD-brain routing per slot type (Phase B, June 11 — Floward proved
    the full methodologies beat the salvaged one-liners). alt flips the pair for variety.
    Thin wrapper over route_decision so the answer and its audit record never drift."""
    return route_decision(slot, alt)["primary"]


def log_routing_decision(decision: dict, run_id: str = "", path: Path = ROUTING_LOG) -> Path:
    """Append one RoutingDecision to logs/routing_decision.jsonl (B051). Consumer =
    routing_spread() (Rule #6: the reader ships this same cycle). Callers wrap this best-effort
    so a logging failure can never break a render."""
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "run_id": run_id, **decision}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def read_routing_decisions(path: Path = ROUTING_LOG) -> list:
    """Read the routing-decision log back (the reader's input)."""
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def routing_spread(decisions: list, dominance_threshold: float = 0.6) -> dict:
    """THE READER (Rule #6) — turn a batch of decisions into the one number that catches the
    June-14 scar: one brain monopolising a batch. single_brain_domination=True when the most-
    used brain is >= dominance_threshold of the batch (the '100% paradox' batch trips at 1.0)."""
    primaries = [d.get("primary") for d in decisions if d.get("primary")]
    total = len(primaries)
    counts = {}
    for b in primaries:
        counts[b] = counts.get(b, 0) + 1
    dominant = max(counts, key=counts.get) if counts else None
    ratio = (counts[dominant] / total) if total else 0.0
    return {"total": total, "counts": counts, "brains_used": sorted(counts),
            "dominant_brain": dominant, "dominance_ratio": round(ratio, 4),
            "single_brain_domination": total > 1 and ratio >= dominance_threshold}


def brain_method(brain: str) -> str:
    """The CD brain's actual METHODOLOGY BODY — not the YAML front-matter.
    (Root-hunt 2026-06-14: the old [:2800] returned ONLY the front-matter — the front-matter
    ends at char ~3395 — so the creative METHOD never reached the angle pen; every brain fell
    back to the generic 'concrete scene' prompt → captions collapsed to the brand-mean formula.
    THE #1 repetition cause. Now: skip the front-matter, inject the method body.)"""
    f = BASE / "20_cd_brains" / BRAIN_FILES[brain]
    if not f.exists():
        return ""
    t = f.read_text()
    marks = [m.start() for m in re.finditer(r"^---\s*$", t, re.M)]
    body = t[marks[1] + 3:] if len(marks) >= 2 else t   # content AFTER the YAML front-matter
    return body.strip()[:3200]   # the core methodology that makes this brain creative + distinct
