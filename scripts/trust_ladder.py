#!/usr/bin/env python3
"""TRUST LADDER ENGINE (B022, June 12) — the organ's replay machine.
Trust is COMPUTED from the append-only ledger, never asserted: counted unchanged
client approvals advance the unlock counter; any rejection/edit/culture-breach
resets or demotes. L1/L2 are only ever PROPOSED — the advance itself is a
mohamed_must (queued to the portal), never automatic. AI never advances a level.

Usage: python3 scripts/trust_ladder.py [--handle X]
"""
import argparse, json
from pathlib import Path
import fingerprint_status

BASE = Path(__file__).parent.parent

APPROVE_TYPES = {"client_approved", "pick_selected"}
# B103: ping = any client-facing ask. Four machines now generate them — without a
# meter, a future client gets nagged into churn. Budget is Mohamed's (B159);
# until set, the meter counts honestly and warns at nothing.
PING_MARKERS = ("redline_reconfirm", "parked_ask", "gate_send", "revival_script", "client_question")
RESET_TYPES = {"client_rejected"}
DEMOTE_REASONS = {"culture_breach"}


def replay(handle: str) -> dict:
    tf = BASE / "clients" / handle / "profile/trust.json"
    trust = json.loads(tf.read_text())
    lf = BASE / "clients" / handle / "events/ledger.jsonl"
    counter, demotions, resets = 0, 0, 0
    for line in (lf.read_text().strip().split("\n") if lf.exists() else []):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("confirmer") not in ("mohamed", "client"):
            continue  # only real human verdicts move trust
        if e.get("reason_code") in DEMOTE_REASONS:
            trust["level"] = "L0"
            counter = 0
            demotions += 1
        elif e.get("type") in RESET_TYPES:
            counter = 0
            resets += 1
        elif e.get("type") in APPROVE_TYPES:
            counter += 1
    trust["ladder"]["L1"]["unlock_counter"] = counter
    proposal = None
    if trust["level"] == "L0" and counter >= trust["ladder"]["L1"]["unlock_at"]:
        proposal = "L1"
    trust["history"].append({"replayed": __import__("datetime").date.today().isoformat(), "counter": counter,
                               "demotions": demotions, "resets": resets,
                               "proposal": proposal})
    from organ_write import write_organ
    write_organ(tf, trust)
    # B103 ping meter: count ping-class events in the last 30 days
    import datetime as _dt
    cutoff = (_dt.date.today() - _dt.timedelta(days=30)).isoformat()
    pings_30d = 0
    for line in (lf.read_text().strip().split("\n") if lf.exists() else []):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("ts", "") >= cutoff and any(m in str(e.get("subject", "")) + str(e.get("type", "")) for m in PING_MARKERS):
            pings_30d += 1
    budget = trust.get("ping_budget_30d")          # null until Mohamed sets (B159)
    trust["pings_30d"] = pings_30d
    return {"handle": handle, "level": trust["level"], "counter": counter,
            "pings_30d": pings_30d, "ping_budget": budget,
            "unlock_at": trust["ladder"]["L1"]["unlock_at"], "proposal": proposal,
            "demotions": demotions, "resets": resets}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               fingerprint_status.real_clients())
    for h in clients:
        r = replay(h)
        bar = f"{r['counter']}/{r['unlock_at']}"
        ping_line = (f" · pings30d {r['pings_30d']}/{r['ping_budget']}" if r.get("ping_budget")
                      else f" · pings30d {r['pings_30d']} (budget unset — Mohamed's B159)")
        if r.get("ping_budget") and r["pings_30d"] > r["ping_budget"]:
            ping_line += " 🔴 OVER BUDGET — halt asks"
        print(f"  {h}: {r['level']} · approvals {bar}{ping_line}"
              + (f" · 🔔 L1 PROPOSABLE → push to Mohamed's portal" if r["proposal"] else "")
              + (f" · ⚠ {r['demotions']} demotions" if r["demotions"] else ""))
        # B072: 5th-touch red-line reconfirm — one-tap card when due
        rlf = BASE / "clients" / h / "profile/red_lines.json"
        rl = json.loads(rlf.read_text())
        if rl.get("lines") and rl.get("touches_since_confirm", 0) >= 5:
            import subprocess as _sp
            _sp.run(["python3", str(BASE / "scripts/queue_decision.py"),
                     "--id", f"redline_reconfirm_{h}", "--title", f"تأكيد الخطوط الحمراء: {h}",
                     "--tag", "خطوط حمراء", "--desc", "كل 5 لمسات نتأكد مرة — الخطوط الحالية: " + "؛ ".join(str(x) for x in rl["lines"][:3]),
                     "--buttons", "confirm:✅ لسه نفس الخطوط", "update:✏️ في تغيير (اكتبه بالملاحظة)"], capture_output=True)
            rl["touches_since_confirm"] = 0
            rlf.write_text(json.dumps(rl, ensure_ascii=False, indent=2))
            print(f"     🔔 red-line reconfirm card queued for {h}")
        if r["proposal"]:
            import subprocess
            subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                            "--id", f"trust_L1_{h}", "--title", f"ترقية ثقة: {h} → دفعات معتمدة مسبقاً (L1)؟",
                            "--tag", "ثقة", "--desc", f"{r['counter']} موافقة متتالية بدون تعديل. L1 = دفعة معتمدة بموافقة واحدة للدفعة كاملة (مو لكل بوست). أي رفض يرجع العداد.",
                            "--buttons", "yes:✅ رقّوه L1", "no:❌ يبقى L0"], capture_output=True)


if __name__ == "__main__":
    main()
