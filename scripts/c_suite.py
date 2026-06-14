#!/usr/bin/env python3
"""THE C-SUITE MINDS — COO + CCO, wired live (Mohamed 2026-06-14: "make them all work").
Completes the governance layer the pilot had dormant:

  CEO  (client_strategy.py)  — what to build: reads the full organs → strategy brief.
  CCO  (here)                — is it Saudi-native + culturally correct? LLM Arabic-QC pass:
                               per-post 0–100 + dialect/cultural/tone/negpat flags (its prompt's job).
  COO  (here)                — how safely? per-post CONFIDENCE via its own formula:
                               0.40 floor + 0.30·arabic_qc + 0.15·occasion + 0.15·policy.

These run at the JUDGE stage (before anything reaches Mohamed — Rule #13), on top of the
deterministic gates (client_rules/occasion_align/pre_ship_gate). Zero-LLM safe: no key → CCO
returns a neutral score with a note, COO still computes from the deterministic signals.
"""
import json, os, sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return ""


def _load(h, name, default=None):
    f = B / "clients" / h / "profile" / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else (default if default is not None else {})


def _gpt(system, user, temp=0.2, max_tok=500):
    import urllib.request
    body = {"model": "gpt-4o", "temperature": temp, "max_tokens": max_tok,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=90).read())["choices"][0]["message"]["content"]


def cco_pass(post, handle):
    """CCO mind — Saudi cultural / Arabic QC. Returns {saudi_score 0-100, flags[], verdict}.
    The orchestra-eye, automated: catches the off-register/flat/culturally-off lines a regex can't
    (its prompt: 'silent quality failures are worse than no output; when in doubt, score lower')."""
    caps = post.get("captions") or ([post.get("caption")] if post.get("caption") else [])
    if not caps:
        return {"saudi_score": 0, "flags": ["empty"], "verdict": "reject", "by": "cco"}
    fp = _load(handle, "fingerprint")
    dialect = (fp.get("l2_voice") or {}).get("dialect", "saudi")
    if not env("OPENAI_API_KEY"):
        return {"saudi_score": 70, "flags": [], "verdict": "review", "by": "cco", "note": "no key — neutral"}
    try:
        cco_sys = (B / "10_agent_brains/cco_system_prompt_v1.md").read_text()[:3500]
        user = (f"Brand dialect: {dialect}. Judge these Instagram captions for Saudi-native correctness. "
                "Return JSON {\"saudi_score\":0-100,\"flags\":[\"dialect|cultural|tone_flat|negpat|brave\"],"
                "\"verdict\":\"pass|review|reject\",\"worst_line\":\"\"}. When in doubt score lower.\n\n"
                f"CAPTIONS: {json.dumps(caps, ensure_ascii=False)}")
        r = json.loads(_gpt(cco_sys, user))
        r["by"] = "cco"
        return r
    except Exception as e:
        return {"saudi_score": 70, "flags": [], "verdict": "review", "by": "cco", "note": f"cco err {str(e)[:40]}"}


def coo_confidence(post, handle, cco_score=None, gate_clean=True, occasion_ok=True):
    """COO mind — operational confidence via its own formula:
       0.40 floor + 0.30·arabic_qc + 0.15·occasion + 0.15·policy.  Returns 0–1."""
    arabic_qc = (cco_score if cco_score is not None else 70) / 100.0
    occ = 1.0 if occasion_ok else 0.0
    policy = 1.0 if gate_clean else 0.0
    conf = 0.40 + 0.30 * arabic_qc + 0.15 * occ + 0.15 * policy
    return round(min(1.0, conf), 3)


def judge_post(post, handle):
    """Full C-suite + gate verdict for one post — what the system knows before Mohamed sees it."""
    import pre_ship_gate as psg
    import client_rules as cr
    import occasion_align as oa
    gate = psg.gate(post, handle)
    gate_clean = not gate.get("block")
    slot = post.get("slot") or {}
    occ_ok = True
    for c in (post.get("captions") or []):
        if oa.caption_misaligned(slot, c):
            occ_ok = False
            break
    cco = cco_pass(post, handle)
    conf = coo_confidence(post, handle, cco.get("saudi_score"), gate_clean, occ_ok)
    return {"gate_clean": gate_clean, "occasion_ok": occ_ok,
            "cco": cco, "coo_confidence": conf,
            "ship": gate_clean and occ_ok and cco.get("verdict") != "reject" and conf >= 0.70}
