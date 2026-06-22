#!/usr/bin/env python3
"""MODEL REGISTRY — the single source of truth for WHICH models the moat currently sits on,
plus the two helpers that make a model CHANGE detectable (the consult's "silent time-bomb"):
FINGERPRINT (stamp an artifact with the model id+version+date it was made on) and
DETECT-DRIFT (compare a stamped artifact to the live registry).

WHY (proportionate hedge, NOT a platform):
OGZ's moat is "the LLM changes, the prompt doesn't" — but the prompt's OUTPUT still rides on
live models: fal flux-2-pro/edit for renders, gpt-4o / claude-sonnet for captions. A model
UPDATE / DEPRECATION / silent re-tune could invalidate visual consistency or the taste-Elo
(which is calibrated on CAPTIONS, so a caption-model change moves the bar under it) and nobody
would know. The minimal hedge is: FINGERPRINT every render/caption/the taste-Elo with the model
id+version+date, then a $0 DRIFT-CHECK flags 're-validate' when the live model differs from the
artifact's stamp. This module is that source-of-truth + the two pure helpers. Zero deps, $0.

This is deliberately a flat dict + small functions — NOT a plugin system, factory, or registry
class. Three clients, one pilot. To bump a model: edit the dict below + DATE, re-validate, done.

TWO LIVE RENDER PATHS (both fingerprinted here so a model swap on EITHER is detectable):
  • MASTER  = render_openclaw.py → fal flux-2-pro/edit — the JUDGED path (v3.7 prompt + reference
              lock + brand-text suppression + logo composite + pixel modesty gate). RENDER_MODEL.
  • DRAFT   = render_image.py    → fal flux/schnell    — the NON-JUDGED improvised draft path
              (cheap exploratory renders, never shown to Mohamed as final). RENDER_MODEL_DRAFT.
A model change on the draft path was previously UNDETECTABLE (no fingerprint); it is now stamped
exactly like the master so check_model_drift bites on a silent schnell swap too.

CONSUMERS (Rule #6 — every writer has a reader, asserted same cycle):
  • render_openclaw.py        → fingerprint_render()        stamps each MASTER render in the fal cost log
  • render_image.py           → fingerprint_render_draft()  stamps each DRAFT render in the image cost log
  • render_client_slot.py     → fingerprint_caption()       stamps each caption batch
  • taste_elo.py              → caption_fingerprint()        embeds the caption-model stamp in taste_elo.json
  • check_model_drift.py      → detect_*_drift()             the $0 gate that BITES on a mismatch (both render paths + captions)
"""
from __future__ import annotations
import time
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# THE REGISTRY — the live models. Bump these (and BUMP THE DATE) when you swap a
# model, then run check_model_drift.py --strict and re-validate consistency/taste.
# ─────────────────────────────────────────────────────────────────────────────
RENDER_MODEL = "fal-ai/flux-2-pro/edit"     # MASTER render backend (the JUDGED path; visual consistency rides on this)
RENDER_MODEL_VERSION = "flux-2-pro"         # coarse version tag; bump on any provider re-tune we learn of
RENDER_REGISTERED = "2026-06-22"            # date this render model was last validated as the active one

# DRAFT render backend (render_image.py): the cheap NON-JUDGED path for exploratory drafts. Its
# output never ships as final, but a silent model swap here was previously invisible — fingerprinted
# now so check_model_drift catches it too. Bump these (+ DATE) when render_image's model changes.
RENDER_MODEL_DRAFT = "fal-ai/flux/schnell"  # render_image.py's backend (~$0.003/img, 4 steps)
RENDER_MODEL_DRAFT_VERSION = "flux-schnell" # coarse version tag for the draft backend
RENDER_DRAFT_REGISTERED = "2026-06-22"      # date the draft render model was last validated

# captions: primary pen + fallback pen. The taste-Elo is calibrated on captions, so a change to
# EITHER of these is a reason to re-validate the taste bar (check_model_drift watches the primary).
CAPTION_MODEL_PRIMARY = "gpt-4o"            # render_client_slot.gpt()
CAPTION_MODEL_FALLBACK = "claude-sonnet-4-6"  # render_client_slot.sonnet()
CAPTION_REGISTERED = "2026-06-22"           # date the caption stack was last validated


def render_registry() -> dict:
    """The active MASTER render-model triple (id+version+date). The render fingerprint stamps this."""
    return {"render_model": RENDER_MODEL,
            "render_model_version": RENDER_MODEL_VERSION,
            "registered": RENDER_REGISTERED}


def render_draft_registry() -> dict:
    """The active DRAFT render-model triple (render_image.py / schnell). Same shape as the master so
    the draft fingerprint stamps + the drift axis compare identically."""
    return {"render_model": RENDER_MODEL_DRAFT,
            "render_model_version": RENDER_MODEL_DRAFT_VERSION,
            "registered": RENDER_DRAFT_REGISTERED}


def caption_registry() -> dict:
    """The active caption-model set. The caption + taste-Elo fingerprints stamp this."""
    return {"caption_model_primary": CAPTION_MODEL_PRIMARY,
            "caption_model_fallback": CAPTION_MODEL_FALLBACK,
            "caption_models": [CAPTION_MODEL_PRIMARY, CAPTION_MODEL_FALLBACK],
            "registered": CAPTION_REGISTERED}


def _today() -> str:
    return time.strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# FINGERPRINT — stamp an artifact with the model that made it, so a later change
# is DETECTABLE. Each returns a small dict you merge into the artifact / log line.
# `model` is recorded explicitly (what was ACTUALLY used this run, which on a
# caption fallback may be the fallback) alongside the registry's declared id.
# ─────────────────────────────────────────────────────────────────────────────
def fingerprint_render(model: Optional[str] = None, stamped_at: Optional[str] = None) -> dict:
    """Stamp for a single render. `model` = the model actually called (defaults to the registry
    render model). Returns {model_fingerprint:{...}} to merge into the cost-log line / a sidecar."""
    reg = render_registry()
    return {"model_fingerprint": {
        "kind": "render",
        "model": model or reg["render_model"],
        "registry_model": reg["render_model"],
        "model_version": reg["render_model_version"],
        "registered": reg["registered"],
        "stamped_at": stamped_at or _today(),
    }}


def fingerprint_render_draft(model: Optional[str] = None, stamped_at: Optional[str] = None) -> dict:
    """Stamp for a single DRAFT render (render_image.py / schnell). Mirrors fingerprint_render's I2
    stamp but against the DRAFT registry, so a silent schnell swap is detectable. `model` = the model
    actually called (defaults to the registry draft model). Merge into the image cost-log line."""
    reg = render_draft_registry()
    return {"model_fingerprint": {
        "kind": "render_draft",
        "model": model or reg["render_model"],
        "registry_model": reg["render_model"],
        "model_version": reg["render_model_version"],
        "registered": reg["registered"],
        "stamped_at": stamped_at or _today(),
    }}


def fingerprint_caption(model: Optional[str] = None, stamped_at: Optional[str] = None) -> dict:
    """Stamp for a caption (batch). `model` = the pen actually used this run (primary or, on a
    fallback, the fallback). Returns {model_fingerprint:{...}} to merge into the caption record."""
    reg = caption_registry()
    return {"model_fingerprint": {
        "kind": "caption",
        "model": model or reg["caption_model_primary"],
        "registry_models": reg["caption_models"],
        "registry_primary": reg["caption_model_primary"],
        "registered": reg["registered"],
        "stamped_at": stamped_at or _today(),
    }}


def caption_fingerprint(stamped_at: Optional[str] = None) -> dict:
    """The compact caption-model stamp embedded INTO taste_elo.json so a caption-model change is
    visible against the calibrated taste (the Elo is calibrated on captions). Flat — taste_elo.json
    merges this verbatim under "caption_model_fingerprint"."""
    reg = caption_registry()
    return {
        "caption_model_primary": reg["caption_model_primary"],
        "caption_models": reg["caption_models"],
        "registered": reg["registered"],
        "stamped_at": stamped_at or _today(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# DETECT DRIFT — compare an artifact's stamp to the LIVE registry. Pure; the
# gate (check_model_drift.py) decides what to do (it BITES). Returns a small
# verdict dict: drift=True means the live model differs from what made the
# artifact → re-validate before trusting it.
# ─────────────────────────────────────────────────────────────────────────────
def detect_render_drift(stamp: Optional[dict]) -> dict:
    """stamp = the model_fingerprint dict pulled off a render's cost-log line (or None/{}).

    Two distinct conditions, never conflated (Rule #9 — a missing stamp is NOT the same fact as a
    changed model):
      • drift=True       — the stamp EXISTS and its model/version DIFFERS from the registry. This is
                           the real time-bomb: a model actually changed under the live renders.
      • unverified=True  — the stamp is MISSING (a legacy render made before fingerprinting). We
                           can't vouch for it, but it's not evidence of a CHANGE — it re-stamps on
                           the next render. A softer flag than drift.
    """
    reg = render_registry()
    if not stamp:
        return {"drift": False, "unverified": True,
                "reason": "render artifact has NO model fingerprint (legacy render) — re-stamps on next render",
                "registry_model": reg["render_model"], "artifact_model": None}
    art_model = stamp.get("registry_model") or stamp.get("model")
    art_ver = stamp.get("model_version")
    drift = (art_model != reg["render_model"]) or (art_ver not in (None, reg["render_model_version"]))
    return {"drift": bool(drift), "unverified": False,
            "reason": (f"render model changed: artifact={art_model}/{art_ver} → registry="
                       f"{reg['render_model']}/{reg['render_model_version']}" if drift else "render model matches registry"),
            "registry_model": reg["render_model"], "artifact_model": art_model}


def detect_render_draft_drift(stamp: Optional[dict]) -> dict:
    """stamp = the model_fingerprint dict pulled off a DRAFT render's image cost-log line (or None/{}).
    Identical logic to detect_render_drift, but against the DRAFT registry (render_image / schnell):
      • drift=True       — the stamp EXISTS and its model/version DIFFERS from the draft registry
                           (a real schnell swap behind the live draft renders).
      • unverified=True  — the stamp is MISSING (a draft render made before fingerprinting). Not a
                           CHANGE; re-stamps on the next draft render (Rule #9 — missing != changed).
    """
    reg = render_draft_registry()
    if not stamp:
        return {"drift": False, "unverified": True,
                "reason": "draft render artifact has NO model fingerprint (legacy draft) — re-stamps on next draft render",
                "registry_model": reg["render_model"], "artifact_model": None}
    art_model = stamp.get("registry_model") or stamp.get("model")
    art_ver = stamp.get("model_version")
    drift = (art_model != reg["render_model"]) or (art_ver not in (None, reg["render_model_version"]))
    return {"drift": bool(drift), "unverified": False,
            "reason": (f"draft render model changed: artifact={art_model}/{art_ver} → registry="
                       f"{reg['render_model']}/{reg['render_model_version']}" if drift else "draft render model matches registry"),
            "registry_model": reg["render_model"], "artifact_model": art_model}


def detect_caption_drift(stamp: Optional[dict]) -> dict:
    """stamp = the caption_model_fingerprint dict from taste_elo.json (or a caption record), or
    None/{}. Drift if the registry PRIMARY caption model is no longer the one the taste bar was
    calibrated under (a caption-model change moves the bar under the taste-Elo), OR if missing."""
    reg = caption_registry()
    if not stamp:
        return {"drift": False, "unverified": True,
                "reason": "taste-Elo / caption artifact has NO caption-model fingerprint (legacy) — re-stamps on next run",
                "registry_primary": reg["caption_model_primary"], "artifact_primary": None}
    art_primary = stamp.get("caption_model_primary") or stamp.get("registry_primary")
    drift = art_primary != reg["caption_model_primary"]
    return {"drift": bool(drift), "unverified": False,
            "reason": (f"caption model changed under the taste-Elo: calibrated on {art_primary} → "
                       f"registry primary is now {reg['caption_model_primary']}" if drift
                       else "caption model matches registry"),
            "registry_primary": reg["caption_model_primary"], "artifact_primary": art_primary}


# ─────────────────────────────────────────────────────────────────────────────
# PERSONA / VISUAL-ASSET HOME — NOT defined here (proportionality). The persona
# organ does not exist yet and has zero importers; its model-AGNOSTIC contract
# already lives at 12_data_shapes/brand_visual_dna_v37_v1.schema.json (durable
# description + reference pack; LoRA ids are re-mintable derivatives). The
# Art-Director fills that schema when the organ is actually built — this registry
# stays scoped to the model-fingerprint/drift hedge, which is the valuable part.
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import json
    print("RENDER  :", json.dumps(render_registry(), ensure_ascii=False))
    print("CAPTION :", json.dumps(caption_registry(), ensure_ascii=False))
    print("render fp :", json.dumps(fingerprint_render(), ensure_ascii=False))
    print("caption fp:", json.dumps(caption_fingerprint(), ensure_ascii=False))
