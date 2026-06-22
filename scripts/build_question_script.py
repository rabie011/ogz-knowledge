#!/usr/bin/env python3
"""B184 — build_question_script.py: render a client's gap_report into a choice-card question script.

THE GAP (traces to THE TOP — "a post Mohamed would publish" depends on the client's CONFIRMED organs):
the agreed client flow is EXTRACT → DIAGNOSE → gaps surface → THEN ask ONLY the gap-questions (Rule #11).
The diagnosis already lives in clients/<client>/profile/gap_report.json (its `questions` + `organs_red`).
What was missing is the CONSUMER (Rule #6): a deterministic renderer that turns that diagnosis into a
60-second, choice-card question script Mohamed can hand to the client — WITHOUT inventing a single
question (Rule #12: the system produces; we never hand-author the ask).

What it does, with ZERO LLM:
  - Reads the canonical gap_report (profile/gap_report.json; falls back to the stub).
  - For an ESTABLISHED brand (auto_filled.mode == 'auto_research'): leads with `confirm_instead` —
    "confirm/correct the researched profile" instead of asking from scratch (Rule #11 diagnose-first).
  - Renders every diagnosis question as a card. Where the question already ENUMERATES its options
    inline (e.g. «مبيعات مباشرة، بناء براند، ولا الاثنين؟»), extract_choices() splits them
    deterministically into A/B/C choices; otherwise the card is an open-answer slot.
  - Tags each card with the red organ it serves (best-effort keyword map) so the gap is visible.

It invents nothing: choices come only from the question's own text; questions come only from the
gap_report. Output: presentations/<client>_question_script.md (stable name, deterministic content).

Commands:
  build <client>   — write presentations/<client>_question_script.md and print a summary.
  verify <client>  — REFUSE-guard (Rule #8): exit non-zero if the script would drop a gap_report
                     question or emit a choice-card with fewer than 2 options.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLIENTS = ROOT / "clients"
PRESENTATIONS = ROOT / "presentations"

# Best-effort keyword → red-organ map (deterministic; only labels, never invents questions).
_ORGAN_HINTS = [
    ("goals", ("الهدف", "هدف", "العروض", "مبيعات", "براند")),
    ("l1_strategy", ("طلب", "استيعاب", "إطلاق", "فروع", "مواسم")),
    ("red_lines", ("خط أحمر", "خطوط حمراء", "ممنوع", "نتجنب")),
    ("truth_pack", ("المنتجات", "الأسعار", "منيو", "المرشّح")),
]


def _gap_report_path(client: str) -> Path:
    """Canonical copy lives in profile/ (B010). Fall back to the top-level stub."""
    prof = CLIENTS / client / "profile" / "gap_report.json"
    return prof if prof.exists() else CLIENTS / client / "gap_report.json"


def load_gap_report(client: str) -> dict:
    p = _gap_report_path(client)
    if not p.exists():
        raise FileNotFoundError(f"no gap_report for {client} (looked in profile/ and stub)")
    return json.loads(p.read_text(encoding="utf-8"))


def extract_choices(question: str):
    """Pull inline-enumerated options out of a question, deterministically.

    A question enumerates choices when it contains «ولا » / «أو » before its «؟». We take the clause
    up to the first «؟», drop any leading prompt before «:», then split on «،» / «ولا » / «أو ».
    Returns a cleaned list of >=2 options, else [] (→ the card is an open-answer slot).
    """
    if "؟" not in question:
        return []
    clause = question.split("؟", 1)[0]
    if "ولا " not in clause and "أو " not in clause:
        return []  # a list without «ولا/أو» (e.g. parenthetical examples) is NOT a choice set
    if ":" in clause:
        clause = clause.split(":", 1)[1]
    clause = clause.strip(" «»()،")
    parts = re.split(r"،|\bولا\b|\bأو\b", clause)
    opts = [p.strip(" «»()،.") for p in parts if p.strip(" «»()،.")]
    return opts if len(opts) >= 2 else []


def _organ_for(question: str, organs_red):
    for organ, hints in _ORGAN_HINTS:
        if organ in (organs_red or []) and any(h in question for h in hints):
            return organ
    return None


def build_cards(report: dict):
    """Pure transform: gap_report -> list of card dicts. No I/O, no invention."""
    questions = report.get("questions", []) or []
    organs_red = report.get("organs_red", []) or []
    cards = []
    for q in questions:
        opts = extract_choices(q)
        cards.append({
            "question": q,
            "kind": "choice" if opts else "open",
            "choices": opts,
            "serves_organ": _organ_for(q, organs_red),
        })
    return cards


def render_markdown(client: str, report: dict, cards) -> str:
    auto = report.get("auto_filled") or {}
    established = auto.get("mode") == "auto_research"
    lines = [f"# {client} — سكربت أسئلة التشخيص", ""]
    lines.append(f"> مولّد آليًا من gap_report (الأعضاء الحمراء: {', '.join(report.get('organs_red', []) or []) or '—'}).")
    lines.append("")
    if established:
        confirm = auto.get("confirm_instead", "أكّد أو صحّح الملف المستنتج")
        mined = auto.get("mined") or {}
        lines.append("## ابدأ بالتأكيد، لا بالسؤال من الصفر")
        lines.append(f"**{confirm}**")
        if mined:
            bits = ", ".join(f"{k}: {v}" for k, v in mined.items())
            lines.append(f"<sub>مبني على بحث: {bits}</sub>")
        lines.append("")
    lines.append("## الأسئلة")
    for i, c in enumerate(cards, 1):
        tag = f"  ‹{c['serves_organ']}›" if c["serves_organ"] else ""
        lines.append(f"### {i}. {c['question']}{tag}")
        if c["kind"] == "choice":
            for letter, opt in zip("ABCDEFG", c["choices"]):
                lines.append(f"- [ ] **{letter}.** {opt}")
        else:
            lines.append("- ✏️ ____________________ (إجابة مفتوحة)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_question_script(client: str, write: bool = True) -> dict:
    report = load_gap_report(client)
    cards = build_cards(report)
    md = render_markdown(client, report, cards)
    out = PRESENTATIONS / f"{client}_question_script.md"
    if write:
        PRESENTATIONS.mkdir(exist_ok=True)
        out.write_text(md, encoding="utf-8")
    return {
        "client": client,
        "path": str(out),
        "n_questions": len(cards),
        "n_choice_cards": sum(1 for c in cards if c["kind"] == "choice"),
        "cards": cards,
        "markdown": md,
    }


def verify(client: str) -> int:
    """Rule #8: REFUSE (non-zero) if a question is dropped or a choice-card is malformed."""
    report = load_gap_report(client)
    cards = build_cards(report)
    src_q = report.get("questions", []) or []
    if len(cards) != len(src_q):
        print(f"REFUSE: {client} dropped {len(src_q) - len(cards)} gap_report question(s)")
        return 1
    for c in cards:
        if c["kind"] == "choice" and len(c["choices"]) < 2:
            print(f"REFUSE: {client} choice-card with <2 options: {c['question']!r}")
            return 1
    print(f"OK: {client} — {len(cards)} questions, "
          f"{sum(1 for c in cards if c['kind']=='choice')} choice-card(s), 0 dropped")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("build", "verify"):
        print(__doc__)
        return 2
    cmd = argv[1]
    client = argv[2] if len(argv) > 2 else "albaik"
    if cmd == "verify":
        return verify(client)
    res = build_question_script(client)
    print(f"✅ wrote {res['path']}")
    print(f"   {res['n_questions']} questions · {res['n_choice_cards']} choice-card(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
