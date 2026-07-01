#!/usr/bin/env python3
"""CLIENT STRATEGY STAGE — Mohamed 2026-06-14: "the minds didn't do proper search + analysis of
the client BEFORE they produced; where are the CEO/COO/CCO?". This is the missing FRONT of the
pipeline: research → analyze the FULL organs → C-suite brief → (then the CD brains produce inside it).

  research → analyze → BRIEF (this stage) → produce (CD brains, make_angle reads the brief) → gate → judge

The brief is built from the client's OWN confirmed truth (Rule #13 — never a template):
  • DOSSIER: every organ (truth_pack, fingerprint, moments, red_lines, cultural_overrides,
    audience_mirror, competitor_set, goals, gold) — the minds finally SEE the full history.
  • AVOID-LIST: deterministic from red_lines + cultural_overrides + kill_patterns + learned_bans +
    format (cloud_kitchen). This is what the CD brains must never do — derived, not guessed.
  • PILLARS + ANGLES + POSITIONING: the CEO mind (10_agent_brains/ceo) synthesises from the dossier.
  • RESEARCH_REQUESTS: gaps the dossier can't answer → queued for Claude/agents to research +
    report back (clients/<h>/profile/research_ledger.jsonl) — tracked, the audit trail Mohamed asked for.

Writes clients/<h>/profile/strategy_brief.json (confidence:experimental — Mohamed confirms). make_angle
reads it. Zero-LLM safe: if no key, the deterministic core (dossier + avoid + pillars) still writes;
the CEO synthesis is skipped with a note. Usage: python3 scripts/client_strategy.py --handle eatjurisha
"""
import argparse, glob, json, os, sys, time
from collections import Counter
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import client_rules as cr


def _load(h, name, default=None):
    f = B / "clients" / h / "profile" / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else (default if default is not None else {})


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return ""


def gpt(system, user, temp=0.5, max_tok=900):
    import urllib.request
    body = {"model": "gpt-4o", "temperature": temp, "max_tokens": max_tok,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=120).read())["choices"][0]["message"]["content"]


def build_avoid(h):
    """The DON'T list — derived from the client's confirmed organs (no LLM, no guessing)."""
    avoid = []
    ov = _load(h, "cultural_overrides")
    if ov.get("real_person_mentions") == "off":
        avoid.append("never name a real person (roles only)")
    if str(ov.get("family_voice_lines", "")).startswith("blocked"):
        avoid.append("never put words in a family member's mouth")
    if cr.faces_forbidden(ov):
        avoid.append("visual: no visible faces/expressions (hands/food/objects only)")
    if ov.get("family_member_visibility") == "never":
        avoid.append("visual: no family members/children in frame")
    if cr._is_cloud_kitchen(h):
        avoid.append("delivery-only: no dine-in/restaurant/cart scenes — the food arrives")
    if cr._sector(h) in cr.FOOD_SECTORS:
        avoid.append("no gym/workout framing (this is a food brand)")
    for k in _load(h, "taste").get("kill_patterns", []):
        if isinstance(k, dict) and k.get("pattern"):
            avoid.append(f"founder kill: {k['pattern']}")
    rl = _load(h, "red_lines", {"lines": []}).get("lines", [])
    for l in rl[:6]:
        avoid.append("red-line: " + (l.get("line") if isinstance(l, dict) else str(l)))
    lgr = B / "data/learned_gate_rules.json"
    if lgr.exists():
        for p in json.loads(lgr.read_text()).get("phrase_bans", []):
            avoid.append(f"rejected phrase: {p}")
    return avoid


def build_pillars(h):
    """Content pillars from the client's NEUTRAL everyday material (occasion-free) + products."""
    moments = _load(h, "moments_bank", {"moments": []}).get("moments", [])
    import occasion_align as oa
    tags = Counter(m.get("occasion") for m in moments
                   if m.get("occasion") and m["occasion"] not in oa.CALENDAR_OCC_MOMENTS
                   and not oa.occ_hits(m.get("evidence") or ""))
    pillars = [t for t, _ in tags.most_common(8)]
    prods = [c.get("name") for c in _load(h, "truth_pack").get("product_candidates", []) if c.get("name")][:5]
    return {"everyday_pillars": pillars, "hero_products": prods}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    h = a.handle
    pdir = B / "clients" / h / "profile"
    if not pdir.exists():
        sys.exit(f"no profile for {h}")

    fp = _load(h, "fingerprint")
    dossier = {
        "brand": fp.get("brand_ar") or (_load(h, "truth_pack").get("brand_ar")) or h,
        "positioning_organ": (fp.get("l1_strategy") or {}).get("positioning", ""),
        "voice": (fp.get("l2_voice") or {}),
        "products": [c.get("name") for c in _load(h, "truth_pack").get("product_candidates", [])][:6],
        "audience": _load(h, "audience_mirror"),
        "competitors": _load(h, "competitor_set"),
        "goals": _load(h, "goals"),
        "gold_examples": [g.get("line") for g in _load(h, "gold", {"gold": []}).get("gold", [])][:5],
    }
    avoid = build_avoid(h)
    pillars = build_pillars(h)

    brief = {"built": time.strftime("%Y-%m-%dT%H:%M:%S"), "handle": h,
             "confirmer": "ceo_agent", "confidence": "experimental",
             "avoid": avoid, **pillars, "dossier_seen": list(dossier.keys())}

    # CEO synthesis (the C-suite governance layer) — strategic positioning + angles + research gaps
    if not a.no_llm and env("OPENAI_API_KEY"):
        try:
            ceo_sys = (B / "10_agent_brains/ceo_system_prompt_v1.md").read_text()[:4000]
            user = ("You are the CEO setting the content STRATEGY BRIEF for this brand from its OWN confirmed data. "
                    "Read the dossier + the AVOID list (hard constraints from the client's organs — never violate). "
                    "Return JSON {\"positioning\":\"one line\",\"angles_to_pursue\":[5 concrete everyday content angles that "
                    "RESPECT the avoid list and are NOT occasion/holiday posts],\"goal_ratio\":\"brand-build% / offer%\","
                    "\"research_requests\":[up to 3 specific things we should research to serve this client better]}.\n\n"
                    f"DOSSIER: {json.dumps(dossier, ensure_ascii=False)[:2500]}\n\nAVOID (hard): {json.dumps(avoid, ensure_ascii=False)[:1200]}")
            syn = json.loads(gpt(ceo_sys, user))
            brief.update({k: syn.get(k) for k in ("positioning", "angles_to_pursue", "goal_ratio", "research_requests") if syn.get(k)})
            brief["ceo_synth"] = True
        except Exception as e:
            brief["ceo_synth"] = False
            brief["ceo_note"] = f"CEO synthesis skipped ({str(e)[:60]}) — deterministic core stands"
    else:
        brief["ceo_synth"] = False
        brief["ceo_note"] = "no key / --no-llm — deterministic core (dossier+avoid+pillars) only"

    (pdir / "strategy_brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1))
    # research requests → the tracked ledger (Mohamed: "how do we keep all of this tracked")
    for q in brief.get("research_requests", []) or []:
        (pdir / "research_ledger.jsonl").open("a").write(json.dumps(
            {"ts": brief["built"], "request": q, "status": "open", "by": "ceo_agent"}, ensure_ascii=False) + "\n")
    print(f"✅ {h}: strategy_brief written — {len(avoid)} avoid-rules · {len(pillars['everyday_pillars'])} pillars · "
          f"CEO synth={brief['ceo_synth']} · {len(brief.get('angles_to_pursue', []))} angles · "
          f"{len(brief.get('research_requests', []))} research requests")


if __name__ == "__main__":
    main()
