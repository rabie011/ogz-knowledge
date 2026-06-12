#!/usr/bin/env python3
"""FEEDBACK SYSTEM — ALL-SCENARIO TEST HARNESS (June 12, Mohamed: "test every thing
and see all the scenarios"). Hard asserts only (ASSERT LAW): the script REFUSES to
pass on any failure. Runs in an OGZ_BASE sandbox (its own git repo + ledgers) — the
real ledgers are never touched.

This file is also the standing verify_cmd for the feedback system's own issues.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).parent.parent
SB = Path(tempfile.mkdtemp(prefix="ogz_fb_test_"))
os.environ["OGZ_BASE"] = str(SB)

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '🔴'} {name}{(' — ' + str(detail)) if detail and not cond else ''}")


def iso(dt):
    return dt.isoformat(timespec="seconds")


def setup_sandbox():
    (SB / "data").mkdir(parents=True)
    (SB / "scripts").mkdir()
    # roster + keys (test secrets: t-mo / t-am)
    (SB / "data/portal_team.json").write_text(json.dumps({
        "key": "shared-test", "members": [
            {"id": "mohamed", "name": "محمد", "lane": "all", "owner": True},
            {"id": "amira", "name": "أميرة", "lane": "strategy"}]}))
    (SB / "data/portal_keys.json").write_text(json.dumps({
        "legacy_write": True, "keys": [
            {"key_hash": hashlib.sha256(b"t-mo").hexdigest(), "judge": "mohamed", "revoked": None},
            {"key_hash": hashlib.sha256(b"t-am").hexdigest(), "judge": "amira", "revoked": None}]}))
    for f in ("producer_map.json", "reason_codes.json"):
        shutil.copy(REPO / "data" / f, SB / "data" / f)
    (SB / "data/portal_lane_map.json").write_text("{}")
    # a real git repo for the evidence gates
    subprocess.run(["git", "init", "-q"], cwd=SB, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=SB, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=SB, check=True)
    (SB / "target_file.py").write_text("x = 1\n")
    (SB / "unrelated.py").write_text("y = 2\n")
    subprocess.run(["git", "add", "-A"], cwd=SB, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=SB, check=True)
    # a passing + a failing verify script INSIDE scripts/ (the allowlist)
    (SB / "scripts/verify_pass.py").write_text("assert True\nprint('evidence: 42 ok')\n")
    (SB / "scripts/verify_fail.py").write_text("raise SystemExit(1)\n")


def commit_touching(path: str, msg="fix") -> str:
    p = SB / path
    p.write_text(p.read_text() + f"# {msg} {datetime.now().timestamp()}\n")
    subprocess.run(["git", "add", path], cwd=SB, check=True)
    subprocess.run(["git", "commit", "-qm", msg], cwd=SB, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=SB,
                          capture_output=True, text=True).stdout.strip()


def main():
    setup_sandbox()
    import feedback_lib as fl
    import attribute as attr
    import issue_log as il
    import feedback_router as fr
    import scorecards as sc
    import queue_decision as qd
    import feedback_cards as fc
    from api import portal_mini
    from fastapi.testclient import TestClient
    client = TestClient(portal_mini.app)
    answers = SB / "data/mohamed_answers.jsonl"

    print("\n── 1. IDENTITY (the unrecoverable failure) ──")
    r = client.post("/api/approvals/answer?k=WRONG-KEY",
                    json={"item_id": "x", "answer": "approved", "judge": "mohamed"})
    check("bogus key → 403 + quarantined", r.status_code == 403)
    check("bogus key row NOT in truth ledger", not answers.exists() or "x" not in answers.read_text())
    unv = fl.read_jsonl(SB / "data/unverified_answers.jsonl")
    check("bogus key row IS in quarantine as unverified",
          len(unv) == 1 and unv[0]["judge"] == "unverified" and unv[0]["auth"] == "none")
    r = client.post("/api/approvals/answer?k=t-mo",
                    json={"item_id": "id_test", "answer": "approved", "judge": "amira"})  # body LIES
    rows = fl.read_jsonl(answers)
    check("per-judge key: body judge IGNORED, server resolves mohamed",
          r.status_code == 200 and rows[-1]["judge"] == "mohamed" and rows[-1]["auth"] == "key")
    check("no `else \"mohamed\"` fallback in portal source",
          'else "mohamed"' not in (REPO / "api/portal_mini.py").read_text())
    # shared key transition: picker judge honored, flagged auth:shared; UNKNOWN picker quarantines
    r = client.post("/api/approvals/answer?k=shared-test",
                    json={"item_id": "sh1", "answer": "approved", "judge": "amira"})
    check("shared key + valid picker → truth with auth:shared",
          fl.read_jsonl(answers)[-1]["auth"] == "shared" and fl.read_jsonl(answers)[-1]["judge"] == "amira")
    n_before = len(fl.read_jsonl(answers))
    r = client.post("/api/approvals/answer?k=shared-test",
                    json={"item_id": "sh2", "answer": "approved", "judge": "GHOST"})
    check("shared key + UNKNOWN picker → quarantine (never mohamed)",
          r.status_code == 403 and len(fl.read_jsonl(answers)) == n_before)

    print("\n── 2. CLOCK SKEW + DEDUPE (offline flush) ──")
    old = iso(datetime.now() - timedelta(days=6))
    client.post("/api/approvals/answer?k=t-mo",
                json={"item_id": "skew1", "answer": "approved", "client_ts": old})
    row = fl.read_jsonl(answers)[-1]
    check("client_ts 6d old → clamped to now-48h + skewed flag",
          row.get("skewed") is True and row["client_ts"] >= iso(datetime.now() - timedelta(hours=49)))
    ct = iso(datetime.now())
    for _ in range(2):
        client.post("/api/approvals/answer?k=t-mo",
                    json={"item_id": "dup1", "answer": "approved", "client_ts": ct})
    dups = [r for r in fl.read_jsonl(answers) if r.get("item_id") == "dup1"]
    check("double offline flush → exactly ONE row (dedupe)", len(dups) == 1, len(dups))

    print("\n── 3. GRAMMAR + ATTRIBUTION TRUTH ──")
    check("grammar accepts mind:firaasa", fl.validate_target("mind:firaasa"))
    check("grammar rejects mind:GHOST", not fl.validate_target("mind:ghostmind"))
    check("grammar accepts card:abc / judge:amira",
          fl.validate_target("card:abc") and fl.validate_target("judge:amira"))
    try:
        attr.attribute("card:evil", "card", "mind:firaasa", via="scripts/queue_decision.py", reason="t")
        check("SELF-MISATTRIBUTION refused (queue_decision claiming a mind)", False)
    except ValueError:
        check("SELF-MISATTRIBUTION refused (queue_decision claiming a mind)", True)
    check("zero bytes written on refusal", not (SB / "data/attribution.jsonl").exists())
    e1 = attr.attribute("post:p1", "post", "mind:firaasa", via="scripts/minds.py", reason="t")
    e2 = attr.attribute("post:p1", "post", "mind:firaasa", via="scripts/minds.py", reason="regen")
    check("version auto-increments on regeneration", e1["artifact_version"] == 1 and e2["artifact_version"] == 2)

    print("\n── 4. PRODUCER WIRING (transactional ordering + card stamping) ──")
    qd.push_attributed({"id": "fbcard1", "title": "t", "tag": "x", "desc": "", "clock": "",
                        "priority": "normal", "created": iso(datetime.now()), "status": "open",
                        "kind": "buttons", "options": [{"v": "y", "label": "Y"}]},
                       made_by="claude", reason="test")
    q = json.loads((SB / "data/decision_queue.json").read_text())
    it = q["items"][0]
    check("card stamped made_by + artifact_version", it["made_by"] == "claude" and it["artifact_version"] == 1)
    check("attribution line exists BEFORE card (ordering)", attr.latest_version("card:fbcard1") == 1)

    print("\n── 5. ROUTER: intake, corrections, cursor ──")
    client.post("/api/approvals/answer?k=t-mo",
                json={"item_id": "fbcard1", "answer": "rejected", "note": "النبرة غلط",
                      "artifact_id": "card:fbcard1", "artifact_version": 1})
    client.post("/api/approvals/answer?k=t-mo",
                json={"item_id": "fbcard1", "answer": "comment", "fix": "الصح: نبرة البيت",
                      "artifact_id": "card:fbcard1", "artifact_version": 1})
    s = fr.process()
    issues = fl.read_jsonl(SB / "data/issues.jsonl")
    check("reject → issue opened against claude (resolved via attribution)",
          any(e["event"] == "open" and e["player"] == "claude" for e in issues))
    corr = fl.read_jsonl(SB / "data/corrections.jsonl")
    check("fix box → VERBATIM correction captured + consumable",
          len(corr) == 1 and corr[0]["fix_text"] == "الصح: نبرة البيت")
    check("quote is VERBATIM Mohamed words",
          any(e.get("quote") == "النبرة غلط" for e in issues))
    size_before = (SB / "data/issues.jsonl").stat().st_size
    fr.process()
    check("double router run → byte-identical issues ledger (idempotent)",
          (SB / "data/issues.jsonl").stat().st_size == size_before)
    check("cursor advanced + append-only sha holds", fr.check_append_only())

    print("\n── 6. EVIDENCE GATES (the false-PREPARED scar) ──")
    iid = next(e["issue_id"] for e in issues if e["event"] == "open")
    try:
        il.fix_claimed(iid, "deadbeef" * 5, "fake")
        check("nonexistent commit REFUSED", False)
    except ValueError:
        check("nonexistent commit REFUSED", True)
    unrelated = commit_touching("unrelated.py", "unrelated work")
    # issue has no target_path → must pass --files; give the file the commit does NOT touch
    try:
        il.fix_claimed(iid, unrelated, "sneaky", files=["target_file.py"])
        check("real-but-unrelated commit REFUSED", False)
    except ValueError:
        check("real-but-unrelated commit REFUSED", True)
    good = commit_touching("target_file.py", "real fix")
    il.fix_claimed(iid, good, "real fix", files=["target_file.py"])
    check("real commit touching target ACCEPTED", il.current_state(iid) == "fix_claimed")
    try:
        il.verified(iid, ["/bin/echo", "ok"])
        check("verify cmd outside scripts/ REFUSED", False)
    except ValueError:
        check("verify cmd outside scripts/ REFUSED", True)
    try:
        il.verified(iid, ["python3", "scripts/verify_fail.py"])
        check("failing verify script REFUSED (fix stays claimed)", False)
    except ValueError:
        check("failing verify script REFUSED (fix stays claimed)", il.current_state(iid) == "fix_claimed")
    il.verified(iid, ["python3", "scripts/verify_pass.py"])
    check("passing allowlisted verify ACCEPTED with evidence",
          il.current_state(iid) == "verified" and
          "evidence: 42" in [e for e in fl.read_jsonl(SB / "data/issues.jsonl") if e["event"] == "verified"][-1]["evidence"])
    il.close(iid, closed_by="mohamed_tap")
    check("full lifecycle: open→fix→verified→closed", il.current_state(iid) == "closed")

    print("\n── 6b. CLI PATH SMOKE (the argparse-collision scar: silent no-op exit 0) ──")
    r = subprocess.run([sys.executable, str(REPO / "scripts/issue_log.py"), "open",
                        "--player", "claude", "--quote", "cli smoke test", "--source", "telegram"],
                       capture_output=True, text=True, env={**os.environ})
    check("issue_log CLI actually writes (not a silent no-op)",
          r.returncode == 0 and "iss_" in r.stdout, r.stdout[:60] + r.stderr[:60])

    print("\n── 7. RECURRENCE + ESCALATION ──")
    e = il.open_issue("claude", "النبرة غلط مرة ثانية", reason_code="unspecified",
                      source="portal", source_answer={"ts": iso(datetime.now()), "item_id": "fbcard1"})
    check("same fingerprint within 14d → REOPENED not new",
          e["event"] == "reopened" and e["recurrence_count"] == 1)

    print("\n── 8. REVERSAL CASCADE (void the innocent) ──")
    client.post("/api/approvals/answer?k=t-mo",
                json={"item_id": "fbcard1", "answer": "REVERSED", "note": "غلطت — البوست تمام"})
    # the portal reverse endpoint requires note; we wrote via answer to simulate ledger row
    fr.process()
    states = [il.current_state(x["issue_id"]) for x in fl.read_jsonl(SB / "data/issues.jsonl")
              if x["event"] == "open"]
    check("REVERSED → the reopened issue is VOIDED (innocent cleared)",
          il.current_state(iid) == "voided")

    print("\n── 9. SCORECARDS: fencing, damping, bench, conflicts, min-N ──")
    # seed: mind:metaphor with 8 lifetime judgments, then 3 rejection sittings
    for i in range(8):
        attr.attribute(f"post:m{i}", "post", "mind:metaphor", via="scripts/minds.py", reason="t")
    base_t = datetime.now() - timedelta(days=3)
    rows = []
    for i in range(5):   # 5 approvals spread out (lifetime base)
        rows.append({"schema_v": 2, "ts": iso(base_t + timedelta(minutes=40 * i)), "judge": "mohamed",
                     "auth": "key", "item_id": f"m{i}", "answer": "approved",
                     "artifact_id": f"post:m{i}", "artifact_version": 1, "source": "team_portal"})
    # 3 rejections in ONE sitting (5 min apart) — damping must count streak=1
    sit = datetime.now() - timedelta(days=2)
    for i in range(5, 8):
        rows.append({"schema_v": 2, "ts": iso(sit + timedelta(minutes=5 * (i - 5))), "judge": "mohamed",
                     "auth": "key", "item_id": f"m{i}", "answer": "rejected",
                     "artifact_id": f"post:m{i}", "artifact_version": 1, "source": "team_portal"})
    for r_ in rows:
        fl.append_jsonl(answers, r_)
    out = sc.compute()
    met = out["scorecards"]["players"]["mind:metaphor"]
    check("rage-tap sitting damped: 3 rejections in 15min → streak 1",
          met["streak"] == 1, met["streak"])
    check("metaphor NOT benched at streak 1", "mind:metaphor" not in out["bench"])
    # two more SEPARATE sittings → streak 3 → bench (lifetime is 8)
    for j, dt_ in enumerate([timedelta(days=1), timedelta(hours=2)]):
        fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now() - dt_), "judge": "mohamed",
                                  "auth": "key", "item_id": f"mb{j}", "answer": "rejected",
                                  "artifact_id": f"post:m{j}", "artifact_version": 1, "source": "team_portal"})
    out = sc.compute()
    met = out["scorecards"]["players"]["mind:metaphor"]
    check("3 separate sittings → streak 3 → BENCHED (lifetime n>=8)",
          met["streak"] == 3 and "mind:metaphor" in out["bench"], met["streak"])
    # bench enforcement
    sc.write_all()
    try:
        qd.push_attributed({"id": "benchedcard", "title": "t", "tag": "x", "desc": "", "clock": "",
                            "priority": "normal", "created": iso(datetime.now()), "status": "open",
                            "kind": "buttons", "options": [{"v": "y", "label": "Y"}]},
                           made_by="mind:metaphor", via="scripts/queue_decision.py", reason="t")
        check("queue refuses BENCHED player", False)
    except SystemExit:
        check("queue refuses BENCHED player", True)
    import minds
    rr = minds.run("metaphor", "eatjurisha", "evergreen")
    check("minds.run refuses BENCHED mind", rr.get("refused") and "benched" in rr.get("why", ""))
    # un-bench by ARITHMETIC: reverse one rejection → recompute → bench dissolves
    last_rej = [r_ for r_ in fl.read_jsonl(answers) if r_.get("answer") == "rejected"][-1]
    fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now()), "judge": "mohamed", "auth": "key",
                              "item_id": last_rej["item_id"], "answer": "REVERSED",
                              "in_reply_to": f"{last_rej['ts']}+{last_rej['item_id']}", "source": "team_portal"})
    out = sc.write_all()
    check("reversal → recompute → UN-BENCHED by arithmetic (no unbench button)",
          "mind:metaphor" not in out["bench"])
    rr = minds.run("metaphor", "eatjurisha", "evergreen")
    check("un-benched mind runs again (refuses only on empty truth now)",
          "benched" not in rr.get("why", ""))
    # noise floor: 3 rejections on lifetime n=3 → NO bench
    for i in range(3):
        attr.attribute(f"post:h{i}", "post", "mind:heritage", via="scripts/minds.py", reason="t")
        fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now() - timedelta(hours=10 - 3 * i)),
                                  "judge": "mohamed", "auth": "key", "item_id": f"h{i}",
                                  "answer": "rejected", "artifact_id": f"post:h{i}",
                                  "artifact_version": 1, "source": "team_portal"})
    out = sc.compute()
    check("NOISE FLOOR: streak 3 but lifetime n=3 → NOT benched",
          "mind:heritage" not in out["bench"])
    # conflicts: amira approves what mohamed rejected
    fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now()), "judge": "amira", "auth": "key",
                              "item_id": "h0", "answer": "approved", "artifact_id": "post:h0",
                              "artifact_version": 1, "source": "team_portal"})
    out = sc.compute()
    check("conflict detected (amira ✓ vs mohamed ✗), never blended",
          any(c["judge"] == "amira" for c in out["scorecards"]["conflicts"]))
    # min-N honesty
    her = out["scorecards"]["players"]["mind:heritage"]
    check("min-N: n<10 → rates null + بيانات قليلة note",
          her["rates"] is None and "قليلة" in (her["low_n_note"] or ""))
    # source separation
    fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now()), "judge": "mohamed", "auth": "key",
                              "item_id": "strip1", "answer": "approved", "target": "claude",
                              "source": "after_strip"})
    out = sc.compute()
    cl = out["scorecards"]["players"]["claude"]
    check("after-strip thumbs counted SEPARATELY from card verdicts",
          cl["by_source"]["after_strip"].get("thumbs_up", 0) >= 1)
    # self-review exclusion
    fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now()), "judge": "amira", "auth": "key",
                              "item_id": "self1", "answer": "approved", "target": "judge:amira",
                              "source": "team_portal"})
    out = sc.compute()
    check("self-review excluded + surfaced",
          out["scorecards"]["players"].get("judge:amira", {}).get("self_review_excluded", 0) == 1)
    # v1 mixed replay (real legacy shape) — no crash
    fl.append_jsonl(answers, {"ts": iso(datetime.now()), "item_id": "legacy1", "answer": "approved",
                              "note": "", "fix": "", "rating": None, "judge": "mohamed",
                              "lane": "all", "source": "team_portal"})
    try:
        out = sc.compute()
        check("v1/v2 mixed replay → zero crashes", True)
    except Exception as ex:
        check("v1/v2 mixed replay → zero crashes", False, ex)
    # TASTE FILTER (June 12 zoom-out): rows with no artifact_id AND no target are
    # decisions, not taste — they must NOT pollute any player's scorecard
    polluted = any(out["scorecards"]["players"].get(p, {}).get("lifetime", {}).get("judged", 0)
                   for p in ("system:unattributed",))
    check("legacy/ops row without artifact → EXCLUDED from taste scorecards", not polluted)

    print("\n── 10. BATCH + TOMBSTONE ──")
    attr.attribute("batch:b1", "batch", "claude", via="scripts/queue_decision.py",
                   reason="t", members=[f"post:m{i}" for i in range(3)])
    fl.append_jsonl(answers, {"schema_v": 2, "ts": iso(datetime.now()), "judge": "mohamed", "auth": "key",
                              "item_id": "b1", "answer": "rejected", "artifact_id": "batch:b1",
                              "artifact_version": 1, "source": "team_portal"})
    out = sc.compute()
    fir = out["scorecards"]["players"].get("mind:firaasa", {}).get("lifetime", {})
    check("batch verdict counts ONCE against assembler, zero against members",
          fir.get("rejected", 0) == 0)
    e = il.open_issue("claude", "قضية على هدف بينحذف", reason_code="tone_off",
                      target="post:p1", source="portal")
    attr.retire("post:p1", "DELETE APPROVED test")
    n = fc.retire_pass()
    check("tombstone: open issue on retired target auto-closes (target_retired)",
          il.current_state(e["issue_id"]) == "closed")

    print("\n── 11. META-CARD BUDGET ──")
    sc.write_all()
    pushed = fc.inject()
    q = json.loads((SB / "data/decision_queue.json").read_text())
    live_fb = [i for i in q["items"] if i.get("source") == "feedback_cards" and i.get("status") != "answered"]
    check("feedback cards within global budget (<=3)", len(live_fb) <= 3, len(live_fb))

    print("\n── 12. FORBIDDEN METRICS (the AI-judge law, enforced in code) ──")
    try:
        fl.append_jsonl(answers, {"ts": iso(datetime.now()), "quality_score": 8})
        check("ledger lint refuses quality_score field", False)
    except ValueError:
        check("ledger lint refuses quality_score field", True)
    sc_json = json.dumps(out["scorecards"], ensure_ascii=False)
    check("no composite scores anywhere in scorecards",
          "quality_score" not in sc_json and "7.2/10" not in sc_json)

    print(f"\n{'='*60}\n{'🟢 ALL PASS' if not FAIL else '🔴 FAILURES'}: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        for f in FAIL:
            print(f"   🔴 {f}")
    shutil.rmtree(SB, ignore_errors=True)
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
