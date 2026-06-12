#!/usr/bin/env python3
"""META-CARD INJECTOR — the ONLY script that pushes feedback-system cards (June 12).
Global budget: max 3 live at once. Priority: escalation > conflict > closure-group.
Overflow folds into the week receipt (the one pull surface). Every card ships with a
pre-staged default + one-tap override (the MOHAMED_APPROVALS pattern) — Mohamed is
never asked to do HR.

Also runs the auto-close pass: verified NORMAL issues untapped for 72h close as
auto_verify_timeout (blocking issues wait for his tap forever).
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso, read_jsonl
import issue_log

BUDGET = 3
SOURCE_TAG = "feedback_cards"


def _queue() -> dict:
    q = base() / "data/decision_queue.json"
    return json.loads(q.read_text()) if q.exists() else {"items": []}


def live_feedback_cards(q: dict) -> list:
    return [i for i in q["items"] if i.get("status") != "answered"
            and i.get("source") == SOURCE_TAG]


def _push(item: dict):
    """Through queue_decision's push (attribution + stamping included)."""
    import queue_decision
    item["source"] = SOURCE_TAG
    queue_decision.push_attributed(item, made_by="system:feedback_cards",
                                   via="scripts/feedback_cards.py",
                                   reason="feedback meta-card (budgeted injector)")


def _ledger_issues() -> dict:
    """Fold straight from the LEDGER — state changes must never gate on a possibly
    stale derived file (the tombstone test caught exactly this)."""
    out = {}
    for e in read_jsonl(base() / "data/issues.jsonl"):
        if e.get("event") == "open" and e.get("issue_id") not in out:
            out[e["issue_id"]] = e
    return out


def auto_close_pass() -> int:
    """verified + normal + 72h untapped → closed(auto_verify_timeout)."""
    closed = 0
    for iid, opener in _ledger_issues().items():
        if issue_log.current_state(iid) != "verified" or opener.get("severity") == "blocking":
            continue
        ver_ts = max((e["ts"] for e in issue_log.issue_events(iid) if e["event"] == "verified"), default="")
        if ver_ts and datetime.now() - datetime.fromisoformat(ver_ts) >= timedelta(hours=72):
            try:
                issue_log.close(iid, closed_by="auto_verify_timeout")
                closed += 1
            except ValueError:
                pass
    return closed


def retire_pass() -> int:
    """Open issues whose target is tombstoned → closed(target_retired)."""
    import attribute as attr
    n = 0
    for iid, opener in _ledger_issues().items():
        if issue_log.current_state(iid) in ("open", "fix_claimed", "verified"):
            target = opener.get("target")
            if target and attr.is_retired(target):
                try:
                    issue_log.close(iid, closed_by="target_retired")
                    n += 1
                except ValueError:
                    pass
    return n


def inject() -> list:
    """Build the candidate list by priority, respect the global budget, push."""
    q = _queue()
    slots = BUDGET - len(live_feedback_cards(q))
    if slots <= 0:
        return []
    pushed = []
    existing_ids = {i["id"] for i in q["items"]}
    bench = json.loads((base() / "data/bench.json").read_text()) \
        if (base() / "data/bench.json").exists() else {}
    sc = json.loads((base() / "data/scorecards.json").read_text()) \
        if (base() / "data/scorecards.json").exists() else {"players": {}, "conflicts": []}
    state = json.loads((base() / "data/issues_state.json").read_text()) \
        if (base() / "data/issues_state.json").exists() else {"issues": {}}

    candidates = []
    # P1 — escalations: a benched player (cold streak) or recurrence>=2
    for player, b in bench.items():
        candidates.append({"id": b["card_id"], "kind": "buttons", "priority": "urgent",
            "title": f"🧊 {player} — {b['streak']} رفضات ورا بعض",
            "tag": "تغذية راجعة", "why": "نفس العقل ينرفض باستمرار — يحتاج قرارك: نوقفه أو نكمل",
            "need": "قرّر: إيقاف مؤقت أو فرصة أخيرة", "did": "النظام جمّد إنتاجه تلقائياً بانتظارك",
            "desc": "الافتراضي الجاهز: إيقاف مؤقت حتى تصحيح. عكس أي رفض سابق يفك الإيقاف تلقائياً.",
            "options": [{"v": "bench_ok", "label": "🧊 أوقفه مؤقتاً", "rec": True},
                        {"v": "one_more", "label": "🔄 فرصة أخيرة"}]})
    for iid, st in state.get("issues", {}).items():
        if st["recurrence_count"] >= 2 and st["status"] == "open":
            candidates.append({"id": f"esc_{iid}", "kind": "buttons", "priority": "urgent",
                "title": f"🔁 نفس الشكوى رجعت — {st['reason_code']}",
                "tag": "تغذية راجعة", "why": "شكوى اتقفلت ورجعت مرتين — وقتها تصير قانوناً",
                "need": "قرّر: نحولها قانوناً دائماً؟",
                "did": f"النظام رصد التكرار ({st['recurrence_count']}×) ورشّحها للقوانين",
                "desc": f"«{st['quote']}» — على {st['player']}",
                "options": [{"v": "law", "label": "📜 اقفلها بقانون", "rec": True},
                            {"v": "once_more", "label": "مرة كمان وبس"}]})
    # P2 — conflicts
    for c in sc.get("conflicts", []):
        candidates.append({"id": f"conf_{c['item_id']}", "kind": "buttons",
            "title": "⚖️ اختلاف حكم بينك وبين الفريق",
            "tag": "تغذية راجعة", "why": "حكمان متعاكسان على نفس الكرت — كلمتك تحسمها وتعلّم النظام",
            "need": "احسم الخلاف", "did": f"{c['judge']}: {c['their']} ↔ أنت: {c['mohamed']}",
            "options": [{"v": "mine", "label": "كلامي", "rec": True},
                        {"v": "theirs", "label": f"كلام {c['judge']}"}]})
    # P3 — closure group (issues closed since last receipt)
    closed = [(iid, st) for iid, st in state.get("issues", {}).items() if st["status"] == "closed"]
    unacked = [x for x in closed if f"closure_{x[0]}" not in existing_ids][:5]
    if len(unacked) >= 3:
        lines = " · ".join(f"«{st['quote'][:40]}»" for _, st in unacked[:3])
        candidates.append({"id": f"closures_{now_iso()[:10]}", "kind": "buttons",
            "title": f"✅ {len(unacked)} إصلاحات اتقفلت — بالأدلة",
            "tag": "تغذية راجعة", "why": "كلامك صار commits — هذا الإثبات",
            "did": lines, "options": [{"v": "seen", "label": "✓ شفتها كلها", "rec": True},
                                      {"v": "reopen_one", "label": "↩ وحدة لسه ما اتصلحت (اشرح بالملاحظة)"}]})

    for cand in candidates[:slots]:
        if cand["id"] in existing_ids:
            continue
        _push(cand)
        pushed.append(cand["id"])
    return pushed


if __name__ == "__main__":
    ac = auto_close_pass()
    rp = retire_pass()
    pushed = inject()
    print(f"auto-closed: {ac} · tombstone-closed: {rp} · cards pushed: {pushed or '—'}")
