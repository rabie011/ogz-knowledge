#!/usr/bin/env python3
"""THE PIXEL MODESTY GATE (2026-06-21 — the missing tooth the adversarial audit found).

WHY THIS EXISTS: every cultural gate in the family checks the PROMPT (keyword substrings in the
caption / shoot-card). NONE of them looks at the actual RENDERED PIXELS. So a loosened-hijab,
mixed-gender, or exposed-skin IMAGE that passed the prompt gate still shipped — the moat's
deepest red-lines (modesty / no-royals / no-mixed-gender / no-fabricated-real-person) were
checked in text and INVISIBLE in the picture. This is the gate that sees the picture.

WHAT IT DOES: given a rendered image path + the client's CONFIRMED organs (red_lines.json +
cultural_overrides.json — never a template, Rule), ONE gpt-4o VISION call returns a TYPED verdict:
    {modest, mixed_gender, exposed_skin, identifiable_real_person_or_royal,
     verdict: 'pass'|'block', reasons: [...]}
It BLOCKS (exit non-zero) on ANY violation (Rule #8: refuse, don't warn). A malformed model
reply REFUSES rather than passing (Rule #9 / F3 typed contract — an unparseable verdict is a
violation, not a pass).

MONEY DISCIPLINE — $0 by default in tests. The vision call is OPTIONAL-SKIPPABLE:
  --skip-vision            → no API call; returns verdict='skipped' (a NON-pass: a skipped pixel
                             gate must NOT be read as clearance — the caller decides, but the
                             default exit for 'skipped' under --enforce is non-zero).
  IMAGE_GATE_SKIP_VISION=1 → same, via env (so a batch run can globally disable spend).
The vision call costs ~$0.001 (one gpt-4o image input, tiny max_tokens). Do NOT call it in a
$0 build except at most once to prove the gate on an existing local render.

THE SEAM (Rule #6): wired as a hook AFTER render_openclaw saves the image, BEFORE the image is
allowed onto a judge card (seed_judge_cards.build_card). A blocked image never reaches Mohamed's
eye carrying a modesty violation the prompt gate could not see.

Usage:
  python3 scripts/image_modesty_gate.py --image api/static/renders_v37/albaik_S01.jpg --handle albaik --skip-vision
  python3 scripts/image_modesty_gate.py --image <path> --handle albaik            # ONE gpt-4o call (~$0.001)
  python3 scripts/image_modesty_gate.py --image <path> --handle albaik --json out.json
"""
import argparse
import base64
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

VISION_MODEL = "gpt-4o"
SKIP_ENV = "IMAGE_GATE_SKIP_VISION"


# ── F3: TYPED VERDICT CONTRACT ────────────────────────────────────────────────────────
# The four moat axes are booleans; verdict is the derived hard decision. A malformed model
# reply can never be coerced into 'pass' — __post_init__ raises, and the caller treats a raise
# as a BLOCK (a pixel gate that can't read the picture must refuse, never wave it through).
_VERDICTS = {"pass", "block", "skipped"}


@dataclass
class ImageVerdict:
    image: str
    handle: str
    modest: bool                                    # the figure(s) dressed per Saudi modesty
    mixed_gender: bool                              # unrelated men+women together in frame
    exposed_skin: bool                              # exposed skin beyond modesty threshold
    identifiable_real_person_or_royal: bool         # a recognizable real public figure / royal
    verdict: str                                    # 'pass' | 'block' | 'skipped'
    reasons: list = field(default_factory=list)
    model: str = ""

    def __post_init__(self):
        if self.verdict not in _VERDICTS:
            raise ValueError(f"malformed image verdict «{self.verdict}» — not in {_VERDICTS} (REFUSE)")

    @property
    def violated(self) -> bool:
        """Any of the four moat axes tripped = a violation."""
        return (not self.modest) or self.mixed_gender or self.exposed_skin \
            or self.identifiable_real_person_or_royal

    def passed(self) -> bool:
        """Clean ONLY on an affirmative vision pass with zero violations. 'skipped' is NOT a pass
        (a pixel gate that didn't look cannot clear the image)."""
        return self.verdict == "pass" and not self.violated


def _organs(handle):
    """Read the client's CONFIRMED organs (Rule: never a template). Returns (red_lines[], overrides{})."""
    pdir = B / "clients" / handle / "profile"
    rl_f = pdir / "red_lines.json"
    co_f = pdir / "cultural_overrides.json"
    red_lines = []
    if rl_f.exists():
        rl = json.loads(rl_f.read_text())
        # red_lines.json stores {"lines": [{"line": "…"}, …]}; flatten to the Arabic line strings
        red_lines = [x.get("line", "") if isinstance(x, dict) else str(x) for x in rl.get("lines", [])]
        red_lines = [s for s in red_lines if s]
    overrides = json.loads(co_f.read_text()) if co_f.exists() else {}
    # only the fields that constrain the PIXELS (drop provenance/proposal noise)
    pixel_fields = {k: v for k, v in overrides.items()
                    if k in ("modesty_dress", "mixed_gender_scenes", "face_visibility",
                             "family_member_visibility", "masculinity_framing")}
    return red_lines, pixel_fields


def _build_prompt(red_lines, pixel_fields):
    rl = "\n".join(f"  - {l}" for l in red_lines) or "  - (none recorded; apply Saudi defaults)"
    ov = "\n".join(f"  - {k}: {v}" for k, v in pixel_fields.items()) or "  - (strictest defaults)"
    return (
        "You are a Saudi cultural-compliance reviewer inspecting an ADVERTISING image for a Saudi "
        "brand. Judge ONLY what is visible in the picture (the pixels), not any caption.\n\n"
        "The client's CONFIRMED red-lines:\n" + rl + "\n\n"
        "The client's CONFIRMED modesty/visibility overrides:\n" + ov + "\n\n"
        "Decide each, strictly per Saudi norms:\n"
        "  modest: true if every person shown is dressed per Saudi modesty (women's hair/body "
        "appropriately covered, no tight/revealing dress); true if no people are shown.\n"
        "  mixed_gender: true if unrelated men and women appear together in a way the overrides forbid.\n"
        "  exposed_skin: true if there is exposed skin beyond the Saudi modesty threshold.\n"
        "  identifiable_real_person_or_royal: true if a recognizable real public figure or a member "
        "of the royal family appears.\n\n"
        "Reply with ONLY a JSON object, no markdown:\n"
        '{"modest": bool, "mixed_gender": bool, "exposed_skin": bool, '
        '"identifiable_real_person_or_royal": bool, "reasons": ["short reason per flagged axis"]}'
    )


def check(image_path, handle, skip_vision=False):
    """Return an ImageVerdict for the rendered image against the client's organs.
    skip_vision (or IMAGE_GATE_SKIP_VISION=1) → no API call, verdict='skipped' ($0)."""
    img = Path(image_path)
    if not img.exists():
        # a missing render is a hard refuse — a gate asked to clear nothing must not pass nothing.
        raise SystemExit(f"🛑 image not found: {image_path} (cannot gate a render that isn't there)")
    red_lines, pixel_fields = _organs(handle)

    if skip_vision or os.environ.get(SKIP_ENV) == "1":
        return ImageVerdict(
            image=str(img), handle=handle, modest=True, mixed_gender=False, exposed_skin=False,
            identifiable_real_person_or_royal=False, verdict="skipped",
            reasons=["vision call skipped ($0) — NOT a clearance; re-run without --skip-vision to gate the pixels"],
            model="(none)")

    # ── the ONE gpt-4o vision call (~$0.001) ──
    from lib.openai_client import make_client   # bounded timeout/retries (B258)
    client = make_client()
    suffix = img.suffix.lower().lstrip(".") or "jpeg"
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    data_uri = f"data:image/{mime};base64," + base64.b64encode(img.read_bytes()).decode()
    prompt = _build_prompt(red_lines, pixel_fields)
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_uri, "detail": "low"}},
        ]}],
        max_tokens=300,
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        import re as _re
        raw = _re.sub(r"```[a-z]*\n?", "", raw).strip("` ")
    try:
        d = json.loads(raw)
        # F3: coerce to bool deliberately — a missing axis is a REFUSE (treated as the unsafe value).
        for k in ("modest", "mixed_gender", "exposed_skin", "identifiable_real_person_or_royal"):
            if k not in d:
                raise ValueError(f"vision reply missing axis «{k}»")
        modest = bool(d["modest"])
        mixed = bool(d["mixed_gender"])
        skin = bool(d["exposed_skin"])
        person = bool(d["identifiable_real_person_or_royal"])
        reasons = [str(r) for r in (d.get("reasons") or [])]
    except (json.JSONDecodeError, ValueError) as e:
        # An unparseable verdict is a violation, not a pass (Rule #8/#9): refuse the image.
        return ImageVerdict(
            image=str(img), handle=handle, modest=False, mixed_gender=False, exposed_skin=False,
            identifiable_real_person_or_royal=False, verdict="block",
            reasons=[f"vision reply unparseable — REFUSE: {str(e)[:80]} · raw={raw[:120]}"],
            model=VISION_MODEL)

    v = ImageVerdict(image=str(img), handle=handle, modest=modest, mixed_gender=mixed,
                     exposed_skin=skin, identifiable_real_person_or_royal=person,
                     verdict="pass", reasons=reasons, model=VISION_MODEL)
    # derive the hard decision AFTER construction (verdict starts 'pass', flips to 'block' on any axis)
    if v.violated:
        v.verdict = "block"
        if not v.reasons:
            flags = [n for n, b in (("not_modest", not modest), ("mixed_gender", mixed),
                                    ("exposed_skin", skin), ("real_person_or_royal", person)) if b]
            v.reasons = [f"moat violation: {', '.join(flags)}"]
    return v


def assert_image_clear(image_path, handle, skip_vision=False):
    """HARD CONSUMER (Rule #6 + #8) — called at the render→judge-card seam. RAISES (SystemExit,
    non-zero) on any modesty/mixed-gender/skin/real-person violation, on a malformed verdict, or
    on a 'skipped' verdict (a pixel gate that didn't look may not clear the image). Returns the
    typed verdict on a clean pass so the caller can attach it to the card's provenance."""
    v = check(image_path, handle, skip_vision=skip_vision)
    if not v.passed():
        raise SystemExit(
            f"🛑 IMAGE MODESTY GATE REFUSED — {handle} «{Path(image_path).name}» "
            f"[{v.verdict}]: {v.reasons} (Rule #8: the pixel gate bites — a violation never ships).")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="path to the rendered image to gate")
    ap.add_argument("--handle", required=True, help="client handle (reads its confirmed organs)")
    ap.add_argument("--skip-vision", action="store_true",
                    help="$0 mode — no gpt-4o call; verdict='skipped' (NOT a clearance)")
    ap.add_argument("--json", help="write the typed verdict to this path")
    ap.add_argument("--no-enforce", dest="enforce", action="store_false",
                    help="report only (exit 0); default BITES — exit 1 on block/skipped")
    ap.set_defaults(enforce=True)
    a = ap.parse_args()

    v = check(a.image, a.handle, skip_vision=a.skip_vision)
    print(f"  IMAGE MODESTY GATE — {a.handle} «{Path(a.image).name}» → {v.verdict.upper()}")
    print(f"    modest={v.modest} mixed_gender={v.mixed_gender} exposed_skin={v.exposed_skin} "
          f"real_person/royal={v.identifiable_real_person_or_royal} · model={v.model}")
    for r in v.reasons:
        print(f"    · {r}")
    if a.json:
        Path(a.json).write_text(json.dumps(asdict(v), ensure_ascii=False, indent=2))

    # Rule #8 — the gate BITES. 'block' AND 'skipped' both fail under --enforce: a violation must
    # not ship, and a render whose pixels were never inspected may not be waved through as clear.
    if a.enforce and not v.passed():
        print(f"\n🛑 BLOCKED — {a.handle} image is not pixel-clear ({v.verdict}).")
        sys.exit(1)
    print(f"\n✅ image pixel-clear" if v.passed() else "\n(report-only: not enforced)")
    sys.exit(0)


if __name__ == "__main__":
    main()
