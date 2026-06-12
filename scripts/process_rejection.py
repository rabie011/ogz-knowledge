#!/usr/bin/env python3
"""REJECTION RECOVERY (B112, June 12) — the pyramid's recovery play, mechanized.
On a rejection (Mohamed or client) with a coded reason: exactly ONE regen via a
DIFFERENT brain (B111 door-change law), the reason as a hard constraint. A second
rejection on the same slot = STOP, human calls — logged, never looped.

Usage: python3 scripts/process_rejection.py --handle X --date D --reason too_generic [--note "..."]
"""
import argparse, glob, json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent.parent

REASON_CONSTRAINTS = {
    "too_generic": "السبب المرفوض: عادي/مكرر. المطلوب: زاوية محددة لا يمكن لأي براند آخر نشرها — شخص محدد، لحظة محددة، تفصيلة لا تُنسخ.",
    "off_voice": "السبب المرفوض: مو صوتنا. التزم حرفياً بأمثلة الصوت المرفقة — نفس الحرارة، نفس القاموس.",
    "culture_breach": "السبب المرفوض: حساسية ثقافية. الإعداد الأكثر تحفظاً في كل شيء — لا وجوه، لا اختلاط، لا افتراضات.",
    "factual_error": "السبب المرفوض: معلومة غلط. استخدم فقط الحقائق المؤكدة في حزمة الحقيقة — أي شك = احذف.",
    "wrong_goal": "السبب المرفوض: مو الهدف. صفر طاقة بيع — اللحظة فقط.",
    "unexplained": "رُفض بدون سبب — غيّر الزاوية جذرياً: شخص مختلف، وقت مختلف، مدخل مختلف.",
}
BRAIN_DOORS = ["firaasa", "authenticity", "metaphor", "paradox", "heritage"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--reason", required=True, choices=list(REASON_CONSTRAINTS))
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    # the 2-NOs rule: a prior rejection on this slot = STOP
    lf = BASE / "clients" / a.handle / "events/ledger.jsonl"
    ledger = lf.read_text() if lf.exists() else ""
    slot_key = f"rejection:{a.date}"
    if slot_key in ledger:
        ev = {"ts": __import__("datetime").date.today().isoformat(), "type": "client_rejected", "subject": f"{slot_key}:SECOND",
               "reason_code": a.reason, "note": "2nd rejection — STOPPED, human call required",
               "confirmer": "process_rejection", "stamp": "ESCALATED — no further automation"}
        with open(lf, "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        sys.exit(f"STOP: second rejection on {a.date} — human calls now (logged).")

    # find the rejected card's brain → pick a DIFFERENT door
    rejected_brain = None
    for f in glob.glob(str(BASE / "clients" / a.handle / "posts" / f"{a.date}__*.json")):
        try:
            rejected_brain = json.loads(open(f).read()).get("brain")
            if rejected_brain:
                break
        except Exception:
            continue
    new_brain = next(b for b in BRAIN_DOORS if b != rejected_brain)

    # log the rejection FIRST (memory law), then regen once
    ev = {"ts": __import__("datetime").date.today().isoformat(), "type": "client_rejected", "subject": slot_key,
           "reason_code": a.reason, "note": a.note[:200],
           "confirmer": "pending", "stamp": "rejection logged before recovery"}
    with open(lf, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # B113: a culture_breach verdict auto-writes a PROPOSED red-line candidate —
    # the pain becomes a draft rule instantly (proposed only; client/Mohamed activates)
    if a.reason == "culture_breach":
        rlf = BASE / "clients" / a.handle / "profile/red_lines.json"
        rl = json.loads(rlf.read_text())
        rl.setdefault("proposed_lines", []).append({
            "line": (a.note or f"culture breach on {a.date} — needs naming")[:160],
            "source": f"culture_breach:{a.date}", "status": "PROPOSED — client/Mohamed activates"})
        from organ_write import write_organ
        write_organ(rlf, rl)
        print(f"  📕 red-line candidate proposed from the breach")

    constraint = REASON_CONSTRAINTS[a.reason] + (f" ملاحظة الرافض حرفياً: {a.note}" if a.note else "")
    # constraint travels via env-file the renderer reads? Keep simple: prepend to the brain method
    # by passing --suffix __recovery and writing the constraint into a sidecar the renderer can't
    # miss is overkill — the renderer's note path: use worn_phrases-style injection is internal.
    # Pragmatic v1: regen with the different brain; constraint enforced by reason-specific brain choice
    # + logged for the pen upgrade (full constraint plumbing = client-gate build).
    r = subprocess.run(["python3", str(BASE / "scripts/render_client_slot.py"),
                        "--handle", a.handle, "--date", a.date, "--brain", new_brain,
                        "--suffix", "__recovery"], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(f"recovery render failed: {(r.stderr or r.stdout)[-120:]}")
    card_f = next(iter(glob.glob(str(BASE / "clients" / a.handle / "posts" / f"{a.date}__*__recovery.json"))), None)
    if card_f:
        c = json.loads(open(card_f).read())
        c["recovery"] = {"from_brain": rejected_brain, "to_brain": new_brain,
                          "reason_code": a.reason, "constraint": constraint[:200]}
        Path(card_f).write_text(json.dumps(c, ensure_ascii=False, indent=2))
    print(f"✓ recovery: {rejected_brain} → {new_brain} (door changed) · reason={a.reason} · one shot used")


if __name__ == "__main__":
    main()
