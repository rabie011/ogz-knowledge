#!/usr/bin/env python3
"""CHECK MODEL DRIFT — the $0 gate that makes the consult's "silent time-bomb" LOUD.

The moat is "the prompt doesn't change" — but the OUTPUT still rides on live models. If fal
deprecates/re-tunes flux-2-pro (the MASTER render path) or schnell (the DRAFT render path), or
the caption model changes under the taste-Elo, visual consistency or the taste bar can silently
invalidate and nobody would know. This gate reads what the LIVE artifacts were fingerprinted with
(the last render in the fal cost log AND the image cost log; the caption model behind
taste_elo.json) and compares each to model_registry. On a mismatch it flags LOUDLY: 're-validate
consistency / taste before trusting them'.

Rule #8 (refuse, don't warn): with --strict it EXITS NON-ZERO on any drift — a gate that bites.
Without --strict it prints the verdict and exits 0 (a $0 visibility pass for the heartbeat).
Rule #6: it is the READER of the fingerprints I2 writes (render cost log + taste_elo.json).
Rule #9: it reads the ACTUAL stamps on disk, never assumes — no-data is reported as no-data.

Usage:
  python3 scripts/check_model_drift.py            # report; exit 0
  python3 scripts/check_model_drift.py --strict   # BITE: exit non-zero on any detected drift
  python3 scripts/check_model_drift.py --json      # machine-readable verdict
Zero deps, zero spend.
"""
import argparse, json, sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import model_registry as mr

FAL_COST_LOG = B / "data/fal_cost_log.jsonl"        # MASTER path (render_openclaw / flux-2-pro)
IMAGE_COST_LOG = B / "data/image_cost_log.jsonl"    # DRAFT path (render_image / schnell)
TASTE_ELO = B / "data/taste_elo.json"


def _last_stamp_in(log_path):
    """The model_fingerprint of the MOST RECENT fingerprinted render in `log_path`.
    Returns (stamp|None, found_any_render). A log with renders but NO fingerprint → stamp=None
    with found=True (an un-stamped live render IS unverified — we can't vouch for it)."""
    if not log_path.exists():
        return None, False
    found = False
    last_stamp = None
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        # only rows that actually rendered (have a model + an image) count as a live render
        if row.get("model") and row.get("image_url"):
            found = True
            last_stamp = row.get("model_fingerprint")   # None if this render predates the fingerprint
    return last_stamp, found


def _last_render_stamp():
    """The most recent MASTER render fingerprint (render_openclaw → fal cost log)."""
    return _last_stamp_in(FAL_COST_LOG)


def _last_draft_render_stamp():
    """The most recent DRAFT render fingerprint (render_image → image cost log)."""
    return _last_stamp_in(IMAGE_COST_LOG)


def _taste_caption_stamp():
    """The caption_model_fingerprint embedded in taste_elo.json (None if absent/missing file)."""
    if not TASTE_ELO.exists():
        return None, False
    try:
        elo = json.loads(TASTE_ELO.read_text())
    except json.JSONDecodeError:
        return None, True
    return elo.get("caption_model_fingerprint"), True


def check() -> dict:
    """Pure verdict (testable): per-axis drift + an overall `drift` flag. No exit, no print.
    Three axes now: the MASTER render path (render_openclaw/flux-2-pro), the DRAFT render path
    (render_image/schnell), and the caption model under the taste-Elo."""
    render_stamp, render_found = _last_render_stamp()
    draft_stamp, draft_found = _last_draft_render_stamp()
    caption_stamp, taste_found = _taste_caption_stamp()

    axes = {}

    if not render_found:
        axes["render"] = {"drift": False, "checked": False,
                          "reason": "no live renders logged yet — nothing to drift against",
                          "registry_model": mr.RENDER_MODEL}
    else:
        v = mr.detect_render_drift(render_stamp)
        v["checked"] = True
        axes["render"] = v

    if not draft_found:
        axes["render_draft"] = {"drift": False, "checked": False,
                                "reason": "no live draft renders logged yet — nothing to drift against",
                                "registry_model": mr.RENDER_MODEL_DRAFT}
    else:
        v = mr.detect_render_draft_drift(draft_stamp)
        v["checked"] = True
        axes["render_draft"] = v

    if not taste_found:
        axes["caption_taste"] = {"drift": False, "checked": False,
                                 "reason": "no taste_elo.json yet — nothing to drift against",
                                 "registry_primary": mr.CAPTION_MODEL_PRIMARY}
    else:
        v = mr.detect_caption_drift(caption_stamp)
        v["checked"] = True
        axes["caption_taste"] = v

    drift = any(ax.get("drift") for ax in axes.values())
    unverified = any(ax.get("unverified") for ax in axes.values())
    return {"drift": drift, "unverified": unverified, "axes": axes,
            "registry": {"render": mr.render_registry(), "caption": mr.caption_registry()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="Rule #8 — exit NON-ZERO on any detected drift (a gate that bites)")
    ap.add_argument("--json", action="store_true", help="machine-readable verdict")
    a = ap.parse_args()

    v = check()
    if a.json:
        print(json.dumps(v, ensure_ascii=False, indent=1))
    else:
        print("MODEL DRIFT CHECK ($0) — comparing live artifacts to model_registry")
        print(f"  registry render  : {mr.RENDER_MODEL} / {mr.RENDER_MODEL_VERSION} (registered {mr.RENDER_REGISTERED})")
        print(f"  registry draft   : {mr.RENDER_MODEL_DRAFT} / {mr.RENDER_MODEL_DRAFT_VERSION} (registered {mr.RENDER_DRAFT_REGISTERED})")
        print(f"  registry caption : {mr.CAPTION_MODEL_PRIMARY} (registered {mr.CAPTION_REGISTERED})")
        _revalidate = {"render": "visual consistency", "render_draft": "the draft render path"}
        for name, ax in v["axes"].items():
            if not ax.get("checked"):
                print(f"  · {name:14s} ⏭  {ax['reason']}")
            elif ax.get("drift"):
                print(f"  · {name:14s} 🛑 DRIFT — {ax['reason']}")
                print(f"                  → RE-VALIDATE {_revalidate.get(name, 'the taste-Elo')} "
                      f"before trusting it; then bump model_registry + re-date.")
            elif ax.get("unverified"):
                print(f"  · {name:14s} ⚠️  UNVERIFIED — {ax['reason']}")
            else:
                print(f"  · {name:14s} ✅ matches registry")

    if v["drift"]:
        if a.strict:
            sys.exit("🛑 MODEL DRIFT DETECTED — refusing (Rule #8). Re-validate, then update model_registry.")
        print("⚠️  DRIFT DETECTED — re-validate before trusting these artifacts (run with --strict to make it a hard gate).")
        return
    if v["unverified"]:
        # not a CHANGE — just legacy artifacts with no stamp yet. Loud, but never a hard fail.
        print("ℹ️  no model drift, but some live artifacts are UNVERIFIED (legacy, un-stamped) — they re-stamp on next run.")
        return
    print("✅ no model drift — live artifacts match the registry.")


if __name__ == "__main__":
    main()
