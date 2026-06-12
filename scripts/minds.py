#!/usr/bin/env python3
"""THE MINDS FRAMEWORK (June 12 — Mohamed's architecture: "go build, we need to start").
ONE mind per role, never two copies. Each mind = role methodology + TWO inputs it
always reads: the CLIENT (this brand's truth/organs) and the BRAIN (the shared
knowledge — local intelligence_layer for v1, Supabase at scale). The mind sits
BETWEEN them and produces THIS client's work. Two copies would drift apart (the
frozen-copy bug we killed June 12) — so it's one mind, two inputs, one shared Brain.

Zero-LLM by default: --dry ASSEMBLES the full context the mind would reason over and
prints it + the trace, proving the wiring with no spend. --run (keys live) adds the
LLM call. The walking-skeleton spine.

Usage:
  python3 scripts/minds.py --mind ceo --client eatjurisha --occasion ramadan --dry
  python3 scripts/minds.py --list
"""
import argparse, json
from pathlib import Path

BASE = Path(__file__).parent.parent

# the roster — one definition per role, the methodology file, what it reads, its job
MINDS = {
    "ceo":       {"file": "10_agent_brains/ceo_system_prompt_v1.md", "job": "strategy",
                  "reads": ["client", "brain"], "ar": "المدير التنفيذي — الاستراتيجية"},
    "coo":       {"file": "10_agent_brains/coo_system_prompt_v1.md", "job": "operations",
                  "reads": ["client"], "ar": "مدير العمليات — الجدوى والطاقة"},
    "cco":       {"file": "10_agent_brains/cco_system_prompt_v1.md", "job": "creative_qc",
                  "reads": ["client", "brain"], "ar": "المدير الإبداعي — الجودة الإبداعية"},
    "firaasa":      {"file": "20_cd_brains/cd_01_firaasa_architect.md", "job": "creative",
                     "reads": ["client", "brain"], "ar": "فِراسة"},
    "metaphor":     {"file": "20_cd_brains/cd_02_metaphor_architect.md", "job": "creative",
                     "reads": ["client", "brain"], "ar": "الاستعارة"},
    "authenticity": {"file": "20_cd_brains/cd_03_authenticity_detective.md", "job": "creative",
                     "reads": ["client", "brain"], "ar": "الأصالة"},
    "heritage":     {"file": "20_cd_brains/cd_04_heritage_decoder.md", "job": "creative",
                     "reads": ["client", "brain"], "ar": "التراث"},
    "paradox":      {"file": "20_cd_brains/cd_05_paradox_hunter.md", "job": "creative",
                     "reads": ["client", "brain"], "ar": "المفارقة"},
}


def _org(handle: str, name: str):
    f = BASE / "clients" / handle / "profile" / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else None


def load_client_context(handle: str) -> dict:
    """INPUT 1 — the client's truth (the organs). What makes the work THEIRS."""
    fp = _org(handle, "fingerprint") or {}
    g = _org(handle, "goals") or {}
    rl = _org(handle, "red_lines") or {}
    tp = _org(handle, "truth_pack") or {}
    am = _org(handle, "audience_mirror") or {}
    st = _org(handle, "state") or {}
    products = [p["name"] for p in tp.get("product_candidates", [])
                if "حساب" not in p.get("name", "") and len(p.get("name", "")) >= 3][:6]
    ctx = {
        "brand": st.get("name") or handle,
        "state": st.get("state"),
        "strategy_l1": fp.get("l1_strategy", {}),
        "voice_l2": fp.get("l2_voice", {}),
        "goals": {k: g.get(k) for k in ("goal_ratio", "capacity_ceiling", "usp_his_words", "forward_calendar")},
        "red_lines": rl.get("lines", []),
        "prices_not_redline": rl.get("prices_not_redline"),
        "products": products,
        "audience": {"maps_signals": am.get("maps_signals"), "customer_language": am.get("customer_language", [])[:6]},
        "brand_language": tp.get("brand_language", []),
    }
    # honesty: which strategic inputs are still EMPTY (the CEO must not invent them)
    missing = [k for k, v in {
        "goal/sell-ratio": ctx["goals"]["goal_ratio"], "capacity": ctx["goals"]["capacity_ceiling"],
        "USP-in-their-words": ctx["goals"]["usp_his_words"], "voice-owner": ctx["voice_l2"].get("who_speaks"),
        "positioning": ctx["strategy_l1"].get("positioning"),
    }.items() if not v]
    ctx["_missing_inputs"] = missing
    return ctx


def load_brain_context(sector: str, occasion: str) -> dict:
    """INPUT 2 — the shared Brain (what worked across all brands). v1 = local layer."""
    il = BASE / "11_who_to_learn_from/intelligence_layer.json"
    if not il.exists():
        return {"_source": "MISSING intelligence_layer", "patterns": []}
    d = json.loads(il.read_text())
    return {
        "_source": "local intelligence_layer.json (Supabase at scale)",
        "cultural_guardrails": d.get("cultural_guardrails", {}),
        "sector_facts": (d.get("sector_facts", {}) or {}).get(sector, {}),
        "occasion": (d.get("occasion_calendar", {}) or {}).get(occasion, {}),
        "what_works": d.get("caption_intelligence", {}),
        "honest_gaps": d.get("honest_gaps", []),
    }


def assemble(mind_id: str, handle: str, occasion: str) -> dict:
    """ONE mind, TWO inputs → the full context it reasons over + the trace."""
    m = MINDS[mind_id]
    methodology = (BASE / m["file"]).read_text() if (BASE / m["file"]).exists() else "(methodology file missing)"
    st = _org(handle, "state") or {}
    sector = st.get("sector") or json.loads((BASE / "clients" / handle / "year_map.json").read_text()).get("sector", "")
    client_ctx = load_client_context(handle) if "client" in m["reads"] else None
    brain_ctx = load_brain_context(sector, occasion) if "brain" in m["reads"] else None
    trace = {"mind": mind_id, "job": m["job"], "reads": m["reads"],
             "client_loaded": bool(client_ctx), "brain_loaded": bool(brain_ctx),
             "client_missing": (client_ctx or {}).get("_missing_inputs", []),
             "brain_source": (brain_ctx or {}).get("_source")}
    return {"mind": mind_id, "ar": m["ar"], "methodology_chars": len(methodology),
            "client_ctx": client_ctx, "brain_ctx": brain_ctx, "trace": trace,
            "_ready_to_run": not (client_ctx or {}).get("_missing_inputs")}


def readiness(handle: str) -> dict:
    """What's blocking this client's minds from running — the unblock map (zero-LLM)."""
    cc = load_client_context(handle)
    missing = cc.get("_missing_inputs", [])
    # which questions fill which input (so a tap has a visible target)
    UNBLOCKS = {
        "goal/sell-ratio": "jurisha_q_goal (هدف المحتوى + نسبة العروض)",
        "capacity": "jurisha_q_capacity (كم طلب باليوم)",
        "USP-in-their-words": "jurisha_q_usp (وش يميزكم بكلماتها)",
        "voice-owner": "jurisha_q_voice (مين ينطق باسم البراند)",
        "positioning": "(يُشتق من الإجابات أعلاه + الاستراتيجية)",
    }
    return {"handle": handle, "missing": missing,
            "ready": not missing, "unblocks": {m: UNBLOCKS.get(m, "?") for m in missing}}


def run(mind_id: str, handle: str, occasion: str) -> dict:
    """Produce — keys live. REFUSES on incomplete truth (procedure-honesty holds at
    run time, not just dry-run): a mind must never invent. Reuses the proven LLM-call
    path from the renderer (battle-tested). The first live run IS the integration test."""
    asm = assemble(mind_id, handle, occasion)
    if not asm["_ready_to_run"]:
        return {"ok": False, "refused": True, "mind": mind_id,
                "why": "client truth incomplete — would invent", "missing": asm["trace"]["client_missing"]}
    import sys as _s
    _s.path.insert(0, str(BASE / "scripts"))
    from render_client_slot import gpt          # proven OpenAI call
    methodology = (BASE / MINDS[mind_id]["file"]).read_text()
    user = ("اشتغل على هذا العميل بصفتك " + asm["ar"] + ".\n\n"
            "حقيقة العميل (لا تخترع شيئاً خارجها):\n"
            + json.dumps(asm["client_ctx"], ensure_ascii=False)
            + "\n\nمعرفة الوكالة (وش اشتغل عبر البراندات):\n"
            + json.dumps(asm["brain_ctx"], ensure_ascii=False)
            + "\n\nأنتج مخرجك حسب منهجيتك. JSON فقط.")
    out = gpt([{"role": "system", "content": methodology[:6000]},
               {"role": "user", "content": user}], temp=0.7, max_tok=900)
    return {"ok": True, "mind": mind_id, "output": out, "trace": asm["trace"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mind", choices=list(MINDS))
    ap.add_argument("--client", default="eatjurisha")
    ap.add_argument("--occasion", default="evergreen")
    ap.add_argument("--dry", action="store_true", help="assemble + print context, zero LLM")
    ap.add_argument("--run", action="store_true", help="produce (keys live; refuses on empty truth)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--readiness", action="store_true", help="the unblock map across all clients")
    a = ap.parse_args()
    if a.list:
        for k, m in MINDS.items():
            print(f"  {k:14s} {m['ar']:28s} job={m['job']:11s} reads={'+'.join(m['reads'])}")
        return
    if a.readiness:
        clients = sorted(d.name for d in (BASE / "clients").iterdir()
                         if (d / "profile").is_dir() and not d.name.startswith("__"))
        print("🧭 MINDS READINESS — what unblocks each client (zero-LLM):\n")
        for h in clients:
            r = readiness(h)
            mark = "🟢 READY" if r["ready"] else f"🔴 blocked on {len(r['missing'])}"
            print(f"  {h:16s} {mark}")
            for inp, q in r["unblocks"].items():
                print(f"       ↳ need «{inp}» → answer {q}")
        return
    asm = assemble(a.mind, a.client, a.occasion)
    t = asm["trace"]
    print(f"\n🧠 MIND: {a.mind} ({asm['ar']}) · job={t['job']} · reads {'+'.join(t['reads'])}")
    print(f"   methodology: {asm['methodology_chars']} chars loaded")
    print(f"   CLIENT input: {'✓ loaded' if t['client_loaded'] else '— (this mind reads brain only)'}"
          + (f" · ⚠ MISSING: {t['client_missing']}" if t['client_missing'] else " · complete"))
    print(f"   BRAIN input:  {'✓ ' + str(t['brain_source']) if t['brain_loaded'] else '— (this mind reads client only)'}")
    print(f"\n   {'🟢 READY TO RUN (keys live → produces work)' if asm['_ready_to_run'] else '🔴 NOT READY — client truth incomplete; the CEO would invent. Fill the missing inputs first.'}")
    if a.dry and asm.get("client_ctx"):
        print("\n── CLIENT CONTEXT the mind would read ──")
        print(json.dumps({k: v for k, v in asm["client_ctx"].items() if k != "_missing_inputs"}, ensure_ascii=False, indent=1)[:900])
    if a.run:
        r = run(a.mind, a.client, a.occasion)
        if r.get("refused"):
            print(f"\n🛑 REFUSED — {r['why']} · missing {r['missing']}  (the mind will NOT invent)")
        else:
            print("\n── PRODUCED ──\n" + str(r.get("output"))[:1200])


if __name__ == "__main__":
    main()
