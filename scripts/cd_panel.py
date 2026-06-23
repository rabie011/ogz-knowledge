#!/usr/bin/env python3
"""CD-PANEL — the 5 CD brains RUN as a multi-model panel (W1/W3, Mohamed June 23:
"the full system must work, all agents and minds" + "the minds on DIFFERENT models").

The brainstorm found only the CEO actually ran; the 5 CD brains (20_cd_brains/) were
methodology files applied ONE-at-a-time on ONE model inside make_angle. This module makes
them a PANEL: the slot routes to its CD-brain spread (brain_router.route_decision via
build_angle_cards.angle_brains), each routed brain builds the SAME concrete-scene prompt
(render_client_slot.angle_prompt — methodology BODY + CEO strategy frame + organ armor) and
runs on a DIFFERENT model (GPT / Gemini / Groq, round-robin via consult.py's _PANEL). The
output is N DIVERSE angles for the slot; the lead brain's angle is returned to the producer,
with the rival angles attached as `panel_alts` so the caption pen is SEEDED by the minds.

Laws honoured:
- Rule #8 REFUSE-DON'T-WARN does NOT apply to a dead MODEL — a dead model/key is degraded
  capacity, not bad work: it FALLS BACK to the next live model, never blocks the pipeline.
- Never-stuck: if EVERY model is dead the panel returns None and make_angle uses its single-pen
  path; the producer never stalls on the minds.
- Rule #12 THE SYSTEM PRODUCES: this is machinery — it picks/routes/dispatches by rule. No
  caption text or hand-authored angle lives here.

Usage:
  from cd_panel import run_panel
  angle = run_panel(client, slot, sector)            # -> lead angle dict (+ panel_alts)
  python3 scripts/cd_panel.py --handle X --date Y     # smoke (needs client profile + keys)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))

# The model ring the brains are spread across (Mohamed: "the minds on DIFFERENT models").
# consult.py owns the per-model HTTP + dead-key handling; we only choose WHICH model each
# brain talks to and round-robin so two adjacent brains rarely share a model.
MODEL_RING = ("gpt", "gemini", "groq")


def _strip_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (Gemini/Groq wrap it in prose/fences)."""
    if not text:
        raise ValueError("empty")
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("no json object")
    return json.loads(text[i:j + 1])


def _default_ask(model: str, sys_p: str, user: str) -> str:
    """Dispatch ONE brain's prompt to ONE model via consult.py's panel helpers (the multi-model
    wire). Each helper returns an answer string OR an '(... error ...)' string for a dead key —
    we treat a leading '(' with no JSON as a model miss and let the caller fall back."""
    import consult
    fn = consult._PANEL.get(model)
    if fn is None:
        return f"(unknown model {model})"
    # consult helpers take (prompt, system=...) for gpt/groq; gemini takes (prompt) only and has
    # no system slot — fold the system prompt into the user prompt so the brain's method survives.
    combined = sys_p + "\n\n" + user + '\n\nReturn ONLY the JSON object, no prose.'
    try:
        if model == "gemini":
            return fn(combined)
        return fn(combined, system=sys_p)
    except TypeError:
        return fn(combined)


def run_panel(client: dict, slot: dict, sector: str, lead_brain: str | None = None,
              n: int = 5, ask=None, prompt_builder=None, brains=None) -> dict | None:
    """Run the CD-brain panel for one slot. Returns the LEAD angle dict (the routed primary brain)
    with `panel_alts` (the rival brains' angles) attached, plus `brain`/`by_model` provenance.
    Returns None only if EVERY brain on EVERY model failed (caller falls back to single-pen).

    Injectable seams (so the wiring is testable with zero network / zero heavy imports):
      ask(model, sys_p, user) -> reply str   — defaults to consult.py dispatch
      prompt_builder(client, slot, sector, brain) -> (sys_p, user, brain)
                                              — defaults to render_client_slot.angle_prompt
      brains: list[str]                       — defaults to the routed CD-brain spread
    """
    if ask is None:
        ask = _default_ask
    if prompt_builder is None:
        from render_client_slot import angle_prompt as prompt_builder
    if brains is None:
        # ROUTE: same deterministic spread the angle-card path uses (route_decision under the hood:
        # occasion → its provenance-backed two-CD pair leads, daily → the four non-occasion brains;
        # sector safety-locks already removed). Foreground lead_brain if the caller routed one.
        import build_angle_cards as bac
        occ = slot.get("occasion") or ""
        brand_ar = client.get("brand_ar", "")
        brains = bac.angle_brains(occ, brand_ar, n=n, sector=sector)
        # distinct, order-preserving — a 5-mind panel wants 5 DIFFERENT methodologies, not repeats
        brains = list(dict.fromkeys(brains))
        if lead_brain and lead_brain in brains:
            brains = [lead_brain] + [b for b in brains if b != lead_brain]
        elif lead_brain:
            brains = [lead_brain] + brains
            brains = list(dict.fromkeys(brains))[:n]

    angles = []
    for idx, brain in enumerate(brains):
        sys_p, user, eff_brain = prompt_builder(client, slot, sector, brain=brain)
        # spread brains across the model ring; on a model miss, walk the ring to the next live one
        tried = []
        got = None
        for off in range(len(MODEL_RING)):
            model = MODEL_RING[(idx + off) % len(MODEL_RING)]
            if model in tried:
                continue
            tried.append(model)
            reply = ask(model, sys_p, user)
            try:
                obj = _strip_json(reply)
            except Exception:
                continue   # model miss (dead key returns '(... error ...)') — fall to next model
            if not (obj.get("scene_ar") or obj.get("scene")):
                continue   # empty/degenerate reply (e.g. gemini returned '{}') — not a real angle
            obj.setdefault("scene_ar", obj.get("scene", ""))
            obj.setdefault("post_type", "moment")   # downstream diversity reads .get(post_type) — keep it well-formed
            obj.setdefault("why_it_lands", "")
            obj["brain"] = eff_brain
            obj["by_model"] = model
            got = obj
            break
        if got:
            angles.append(got)

    if not angles:
        return None   # every brain on every model failed — caller uses single-pen path

    lead = angles[0]
    lead["panel_alts"] = [
        {"brain": a["brain"], "by_model": a["by_model"], "scene_ar": a.get("scene_ar", ""),
         "why_it_lands": a.get("why_it_lands", "")}
        for a in angles[1:]
    ]
    lead["panel_models"] = sorted({a["by_model"] for a in angles})
    lead["panel_brains"] = [a["brain"] for a in angles]
    return lead


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    from render_client_slot import load_client
    ymap = json.loads((BASE / "clients" / a.handle / "year_map.json").read_text())
    slot = next((s for mm in ymap["months"].values() for s in mm if s["date"] == a.date), None)
    if not slot:
        sys.exit(f"no slot {a.date} in {a.handle} year map")
    slot.setdefault("sector", ymap["sector"])
    c = load_client(a.handle)
    angle = run_panel(c, slot, ymap["sector"])
    print(json.dumps(angle, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
