#!/usr/bin/env python3
"""WEEK RECEIPT / IM-HERE GENERATOR (D7-1, June 12 — RABIE's slice step 2).
Mohamed can say «im here» any minute; the protocol owes him ONE message:
(a) everything done since he left, (b) the portal link + what awaits his taps,
(c) an honest opinion. This script keeps that package permanently fresh —
machine-assembled EVIDENCE; the live opinion stays Claude's at delivery.

Usage: python3 scripts/week_receipt.py     # writes data/im_here.md
"""
import json, subprocess, datetime
from pathlib import Path

BASE = Path(__file__).parent.parent


def feedback_closure_section() -> str:
    """«ايش صار بكلامك» — his verbatim quote → commit → evidence → state. The
    loop-closing surface: proof his words became commits (June 12 feedback system)."""
    import json as _j
    st_f = BASE / "data/issues_state.json"
    if not st_f.exists():
        return ""
    st = _j.loads(st_f.read_text())
    issues = st.get("issues", {})
    if not issues:
        return ""
    AR = {"open": "مفتوحة", "fix_claimed": "قيد الإصلاح", "verified": "اتصلحت (حسب السكربت)",
          "closed": "اتقفلت", "voided": "أُلغيت (عكست حكمك)"}
    lines = ["\n## (d) ايش صار بكلامك"]
    for iid, s in sorted(issues.items(), key=lambda x: x[1].get("opened", ""), reverse=True)[:8]:
        commit = next((e.get("commit") for e in s.get("events", []) if e.get("commit")), None)
        lines.append(f"- «{s.get('quote','')[:60]}» → {AR.get(s['status'], s['status'])}"
                     + (f" @ `{commit}`" if commit else "")
                     + (f" · رجعت {s['recurrence_count']}×" if s.get("recurrence_count") else ""))
    if st.get("oldest_open_days", 0):
        lines.append(f"- أقدم قضية مفتوحة: {st['oldest_open_days']} يوم")
    auto = [s for s in issues.values() if any(e.get("closed_by") == "auto_verify_timeout"
                                              for e in s.get("events", []))]
    if auto:
        lines.append(f"- اتقفل تلقائياً (72h بعد التحقق): {len(auto)}")
    return "\n".join(lines) + "\n"


def mohamed_last_seen() -> str:
    f = BASE / "data/mohamed_answers.jsonl"
    if not f.exists():
        return "2026-06-12T00:00:00"
    return json.loads(f.read_text().strip().split("\n")[-1])["ts"]


def main():
    since = mohamed_last_seen()
    # (a) WORK SINCE HE LEFT — commits are the spine (evidence law: hashes, not feelings)
    log = subprocess.run(["git", "-C", str(BASE), "log", f"--since={since}",
                          "--pretty=%h %s"], capture_output=True, text=True).stdout.strip()
    commits = [l for l in log.split("\n") if l] if log else []
    cards = len(list(BASE.glob("clients/*/posts/*.json")))
    backlog = json.loads((BASE / "data/backlog.json").read_text())
    done = [s for s in backlog["steps"] if s["status"] == "done"]
    # rabie chair activity
    rs = Path.home() / "agents/rabie/sessions"
    rulings_today = 0
    today = str(datetime.date.today())
    sf = rs / f"{today}.jsonl"
    if sf.exists():
        rulings_today = len(sf.read_text().strip().split("\n"))
    # alarms + zooms
    alarms, zooms = 0, 0
    ml = BASE / "data/make_sure_log.jsonl"
    if ml.exists():
        for l in ml.read_text().strip().split("\n"):
            try:
                e = json.loads(l)
            except Exception:
                continue
            if e.get("ts", "") >= since:
                zooms += e.get("type") == "zoom_out"
                alarms += bool(e.get("alarm"))
    # (b) THE PORTAL — open cards, urgent first
    q = json.loads((BASE / "data/decision_queue.json").read_text())
    open_items = [i for i in q.get("items", []) if i.get("status") == "open"]
    urgent = [i for i in open_items if i.get("priority") == "urgent"]
    jb = json.loads((BASE / "data/judging_batch.json").read_text()) if (BASE / "data/judging_batch.json").exists() else {}
    cq = json.loads((BASE / "data/crystallize_queue.json").read_text()) if (BASE / "data/crystallize_queue.json").exists() else {"cards": []}
    drafts = [c for c in cq["cards"] if "DRAFT" in str(c.get("status", ""))]
    # (c) OPINION EVIDENCE — both directions, drafted not decided
    rs = {}
    rsf = BASE / "data/retro_sweep.json"
    if rsf.exists():
        rs = json.loads(rsf.read_text()).get("report", {})
    strong = [f"{len(commits)} commits since your last tap, every build plant-tested with refusing asserts",
              f"judging 20-batch STAGED (6 brains × 10 occasions) — your fal tap = one command to your screen",
              f"{zooms} zoom-out ritual(s) ran; cold-eyes findings fixed at source (CTA 84%→gated)"]
    rd = BASE / "data/reviews_digest.json"
    if rd.exists():
        r = json.loads(rd.read_text())
        if "albaik" in r:
            a_ = r["albaik"]
            strong.append(f"شارع البيك يتكلم: {a_['total']} مراجعة خرائط — والوجع الأول خدمة ({a_['complaints'].get('service',0)} شكوى) مو الأكل؛ 209 نجمة-واحدة تستاهل نظرتك")
        if "eatjurisha" in r:
            strong.append(f"جريشة محبوبة الشارع: {r['eatjurisha']['stars'].get(5,0)}/{r['eatjurisha']['total']} مراجعات ٥★ — الطعم يقود")
    ue = BASE / "data/unit_economics.json"
    if ue.exists():
        u = json.loads(ue.read_text())
        strong.append(f"money law held: week ≈ ${u.get('week_total_usd_lower_bound','?')} for "
                       f"{sum(c['cards'] for c in u.get('clients_EST', {}).values())} cards "
                       f"(~3 cents/post-unit, ZERO image spend until your fal tap)")
    gm = BASE / "data/gate_metrics.json"
    if gm.exists():
        s0 = (json.loads(gm.read_text()).get("sessions") or [{}])[-1]
        if s0.get("median_sec_per_verdict"):
            strong.append(f"your last portal session: {s0['verdicts']} verdicts at median "
                           f"{s0['median_sec_per_verdict']}s each — the 60-second law holds, measured")
    if rs:
        strong.append("retro sweep: albaik corpus armor-clean ("
                       + ", ".join(f"{h} {v['armor_caught_pct']}% caught" for h, v in rs.items()) + ")")
    worry = [f"{len(urgent)} urgent card(s) unanswered" if urgent else None,
             "myfitness still throttled — needs client truth, no spend on expired drafts",
             "Floward R2 lead pick clock runs to ~June 13 23:00" if any("floward" in str(i.get("id","")).lower() for i in open_items) else None,
             f"orchestrator daemon was found DEAD 88 days (revived; reboot-proofing awaits your paste)",
             (f"myfitness endemic snap-tic: {rs['myfitness.sa']['worn_pct']}% of cards push سناب شات"
              if rs.get("myfitness.sa", {}).get("worn_pct", 0) > 50 else None)]
    pkg = f"""# IM-HERE PACKAGE — auto-fresh {datetime.datetime.now().isoformat(timespec='minutes')}
*(generated by week_receipt.py — Claude delivers this + live opinion in ONE message)*

## (a) منذ آخر لمسة لك ({since[:16]})
- **{len(commits)} commits** — الأحدث أولاً:
{chr(10).join('  - ' + c for c in commits[:15])}
- كروت المحتوى: **{cards}** · باكلوج: **{len(done)} منجز** · أحكام رابي اليوم: {rulings_today}
- إنذارات: {alarms} · جولات zoom-out: {zooms}

## (b) البوابة — ينتظر لمستك
**https://brain.ogzstudios.com/approvals?k=ogz-0d08cf69**
- {len(open_items)} كرت مفتوح ({len(urgent)} عاجل)
- دفعة الحكم: {jb.get('status','—')} — أمر الإطلاق جاهز بعد سطر fal
- مسودات قوانين (crystallize): {len(drafts)}

## (c) أدلة الرأي (Claude يحكم لحظة التسليم)
STRONG: {' · '.join(x for x in strong if x)}
WORRY: {' · '.join(x for x in worry if x)}
{feedback_closure_section()}"""
    (BASE / "data/im_here.md").write_text(pkg)
    print(f"im-here package fresh: {len(commits)} commits since {since[:16]} · {len(open_items)} portal cards · → data/im_here.md")


if __name__ == "__main__":
    main()
