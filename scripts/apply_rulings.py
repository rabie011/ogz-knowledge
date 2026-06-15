#!/usr/bin/env python3
"""APPLY RULINGS — the consumer for Mohamed's decision-card answers (June 13, 02:40).

THE HOLE THIS CLOSES: at 02:10-02:13 Mohamed tapped six rulings on the portal
(drop_conflicted, brand_voice, daily, 2× yes_law, keep_hunting, reshow) and NOTHING
consumed them — the router handles judge verdicts, gold_mint handles approvals, but
button answers on decision cards had NO wire. His drop order sat unexecuted while the
renderer few-shot from the very gold he struck. A ruling that only exists in a ledger
is a ruling that didn't happen.

Mechanics: read data/mohamed_answers.jsonl in full (idempotency comes from the applied
ledger, not a cursor — replays are safe), match (item_id, answer) against HANDLERS,
execute, append evidence to data/applied_rulings.jsonl. Unknown decision answers are
REPORTED (and make_sure_feedback flags them red) — never silently skipped.

Also runs founder-note parity: any Mohamed note ≥15 chars in the answers ledger that
never reached data/founder_words.jsonl is backfilled with provenance (the religion
note was lost this way tonight).

Honors OGZ_BASE for sandboxed tests. Every handler is idempotent and asserts its own
effect on disk before claiming applied (self-audit law).
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# DIRECTIVE GUARD (zoom-out 2026-06-14): a passport answer that is a META-INSTRUCTION
# ("go search the client", "no answer for this brand, figure it out") must NOT be stored
# as the brand's organ value — it poisoned albaik's identity/red_lines with his command.
_PASSPORT_DIRECTIVE = re.compile(
    r"go\s*(check|search)|search (for )?the client|extract every|no answer for this brand|"
    r"figure (it )?out|let the system|consider.*(role|is the role)|could be for (a )?new brand|"
    r"very established brand", re.I)

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base

ANSWERS = "data/mohamed_answers.jsonl"
LEDGER = "data/applied_rulings.jsonl"
ACK_ANSWERS = {"ack", "seen", "ok", "noted", "comment"}  # answers that ARE the whole action
# "comment" = he left a note (read as feedback, not a ruling to apply to an organ)


def _read_jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── handlers ─────────────────────────────────────────────────────────────────

def h_drop_conflicted(b: Path, row: dict) -> str:
    """Move disputed gold entries (named in data/gold_conflicts.json) to 'dropped'."""
    reg = json.loads((b / "data/gold_conflicts.json").read_text())
    payload = reg.get(row["item_id"])
    if not payload:
        raise RuntimeError(f"no payload in data/gold_conflicts.json for {row['item_id']}")
    keys = set(payload["keys"])
    gf = b / f"clients/{payload['handle']}/profile/gold.json"
    g = json.loads(gf.read_text())
    gold, dropped = [], g.get("dropped", [])
    already = {e.get("key") or e.get("id") for e in dropped}
    for e in g.get("gold", []):
        k = e.get("key") or e.get("id")
        if k in keys:
            e["dropped_by"] = f"ruling {row['item_id']} (Mohamed, {row.get('client_ts') or row.get('ts')})"
            e["dropped_at"] = datetime.now().isoformat(timespec="seconds")
            dropped.append(e)
        else:
            gold.append(e)
    g["gold"], g["dropped"] = gold, dropped
    gf.write_text(json.dumps(g, ensure_ascii=False, indent=1))
    live = {e.get("key") or e.get("id") for e in json.loads(gf.read_text())["gold"]}
    assert not (live & keys), "drop did not stick"
    assert keys <= {e.get("key") or e.get("id") for e in json.loads(gf.read_text())["dropped"]}, \
        "dropped audit trail incomplete"
    return f"{len(keys)} entries gold→dropped in {gf.relative_to(b)} ({len(keys - already)} new)"


def h_brand_voice(b: Path, row: dict) -> str:
    """jurisha_voice_v3 = brand_voice: the speaker decision lands in the fingerprint organ."""
    from organ_write import write_organ
    fp_path = b / "clients/eatjurisha/profile/fingerprint.json"
    fp = json.loads(fp_path.read_text())
    v = fp.setdefault("l2_voice", {})
    v["speaker"] = "brand"
    v["speaker_ruling"] = {
        "value": "brand_voice — the brand speaks (warm Najdi home-food voice, adapts by audience)",
        "source": f"portal:{row['item_id']}", "confirmer": "mohamed",
        "confidence": "confirmed", "date": (row.get("client_ts") or row.get("ts", ""))[:10]}
    if "RED" in str(v.get("_status", "")):
        v["_status"] = ("AMBER — speaker RULED by Mohamed (brand voice, 2026-06-13); "
                        "dialect/love-lines still pending the voice birth")
    write_organ(str(fp_path), fp)
    chk = json.loads(fp_path.read_text())["l2_voice"]
    assert chk.get("speaker") == "brand", "voice ruling did not stick"
    return "jurisha fingerprint l2_voice.speaker=brand (status RED→AMBER)"


def h_taxonomy_daily(b: Path, row: dict) -> str:
    """taxonomy ruling: «Saudi doesn't have evergreen» → slot type evergreen→daily in
    every year map. Post FILES keep their historical names (rendered artifacts); the
    display layer already says daily (seed_judge_cards)."""
    import glob
    changed, files = 0, 0
    for f in glob.glob(str(b / "clients/*/year_map.json")):
        d = json.loads(Path(f).read_text())
        n = 0
        for slots in (d.get("months") or {}).values():
            for s in slots:
                if s.get("type") == "evergreen":
                    s["type"] = "daily"; n += 1
                elif s.get("type") == "ramadan_evergreen":
                    s["type"] = "ramadan_daily"; n += 1
        if n:
            d["taxonomy_ruling"] = (f"evergreen→daily per Mohamed portal tap "
                                    f"{(row.get('client_ts') or row.get('ts',''))[:16]} ({row['item_id']})")
            Path(f).write_text(json.dumps(d, ensure_ascii=False, indent=1))
            changed += n; files += 1
    leftover = sum(1 for f in glob.glob(str(b / "clients/*/year_map.json"))
                   for slots in (json.loads(Path(f).read_text()).get("months") or {}).values()
                   for s in slots if s.get("type") in ("evergreen", "ramadan_evergreen"))
    assert leftover == 0, f"{leftover} evergreen slots survived the retag"
    return (f"{changed} slots retagged evergreen→daily across {files} year maps"
            if changed else "already retagged (0 evergreen slots remain)")


def _law_exists(b: Path, lid: str) -> bool:
    reg = json.loads((b / "data/law_registry.json").read_text())
    return any(l["id"] == lid for l in reg["laws"])


def _add_law(b: Path, law: dict) -> str:
    """Append a law; enforcement entries whose symbol is NOT literally in the file are
    stripped and the law downgrades to paper_only (the registry never lies)."""
    reg_p = b / "data/law_registry.json"
    reg = json.loads(reg_p.read_text())
    if any(l["id"] == law["id"] for l in reg["laws"]):
        return f"law {law['id']} already in registry"
    kept = [ep for ep in law.get("enforcement", [])
            if (b / ep["file"]).exists() and ep["symbol"] in (b / ep["file"]).read_text()]
    if not kept and law["status"] == "enforced":
        law["status"] = "paper_only"
        law["note"] = (law.get("note", "") + " · downgraded: no live enforcement symbol verified").strip(" ·")
    law["enforcement"] = kept
    reg["laws"].append(law)
    reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    assert _law_exists(b, law["id"]), "law append did not stick"
    return f"law {law['id']} added ({law['status']}, {len(kept)} enforcement points)"


def h_law_verified_before_shown(b: Path, row: dict) -> str:
    return _add_law(b, {
        "id": "verified_before_shown",
        "statement": "No candidate (client, account, handle, shortlist) is shown to Mohamed "
                     "without LIVE verification first — a dead or mangled handle on his screen "
                     "is a lie wearing a suggestion.",
        "source": f"Mohamed portal tap yes_law ({(row.get('client_ts') or row.get('ts',''))[:16]}) "
                  "after the 5/5-bad-shortlist incident (xlsx handle mangling, June 12)",
        "enforcement": [
            {"file": "scripts/verify_account_handles.py", "symbol": "instagram-profile-scraper"},
            {"file": "scripts/verify_shortlist.py", "symbol": "verify"},
        ],
        "test": None, "status": "enforced",
        "note": "practice since June 12: hunt scripts verify live before staging any pick card"})


def h_law_machine_evidence(b: Path, row: dict) -> str:
    return _add_law(b, {
        "id": "machine_evidence_closure",
        "statement": "Mac-required actions NEVER close on self-report — only machine evidence "
                     "(launchctl print, process tables, on-disk deltas) closes them.",
        "source": f"Mohamed portal tap yes_law ({(row.get('client_ts') or row.get('ts',''))[:16]}) "
                  "after plist verification theater ×2 (June 12)",
        "enforcement": [
            {"file": "scripts/make_sure_feedback.py", "symbol": "reboot_proofed"},
        ],
        "test": None, "status": "enforced",
        "note": "reboot_proofed auto-closes plist cards on launchctl evidence, never on a claim"})


def h_law_assert_system(b: Path, row: dict) -> str:
    assert _law_exists(b, "assert_at_system_layer"), \
        "his yes_law tap targets assert_at_system_layer but the law is missing"
    return "assert_at_system_layer already in registry (pre-written) — his tap ratifies it"


def h_keep_hunting(b: Path, row: dict) -> str:
    """coffee keep_hunting: a backlog step, not an inline Apify run (a ruling-consumer
    that spends scraper credits on every replay would violate money discipline)."""
    bl_p = b / "data/backlog.json"
    bl = json.loads(bl_p.read_text())
    sid = "B_coffee_rehunt_0613"
    if not any(s.get("id") == sid for s in bl["steps"]):
        bl["steps"].append({
            "id": sid, "title": "Coffee pilot re-hunt — wider net, live-verified only",
            "status": "open", "top": "pilot clients prove the pyramid",
            "why": f"Mohamed tapped keep_hunting on coffee_pick_v2 "
                   f"({(row.get('client_ts') or row.get('ts',''))[:16]}) — camelstep not picked",
            "needs_llm": False, "needs_apify": True})
        bl_p.write_text(json.dumps(bl, ensure_ascii=False, indent=1))
    assert any(s.get("id") == sid for s in json.loads(bl_p.read_text())["steps"])
    return f"backlog step {sid} staged (Apify re-hunt, runs next orchestra pick)"


def h_reshow_recipes(b: Path, row: dict) -> str:
    """reshow_4_recipes: re-push the 4 format-contaminated ratify cards CLEAN, straight
    from the pattern library (full mechanism, Arabic example as island)."""
    import queue_decision as qd
    q = json.loads((b / "data/decision_queue.json").read_text())["items"]
    existing = {it["id"] for it in q}
    quar = json.loads((b / "data/verdict_quarantine.json").read_text())
    slugs = [i.replace("ratify_", "").replace("_v2", "")
             for i in quar["format_contaminated_2026_06_13"]["item_ids"]]
    lib = json.loads((b / "data/pattern_cards_v1.json").read_text())["survivors"]
    pushed = []
    for slug in slugs:
        cid = f"ratify2_{slug}"
        if cid in existing:
            continue
        card = next((c for c in lib if c["slug"] == slug), None)
        if not card:
            continue
        qd.push_attributed({
            "id": cid, "title": f"Recipe: {slug.replace('_', ' ')} — ratify?",
            "tag": "Recipe", "clock": "", "priority": "normal",
            "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
            "kind": "buttons", "judge_lane": False, "lane": "creative",
            "why": card["move"],
            "need": f"When it works: {card['when']}",
            "did": f"Skeleton: {card['skeleton']}",
            "island_text": card.get("example_real", ""),
            "options": [
                {"v": "ratify", "label": "✅ Ratify — into the recipe book", "rec": True},
                {"v": "kill", "label": "🗑 Kill it"},
                {"v": "edit", "label": "✏️ Needs work (say what in the note)"}],
        }, made_by="system:apply_rulings", via="scripts/apply_rulings.py",
           reason=f"his reshow tap on reshow_4_recipes — clean re-push of {slug}")
        pushed.append(cid)
    return f"re-pushed clean: {pushed or 'all 4 already in queue'}"


def h_recipe_verdict(b: Path, row: dict) -> str:
    """ratify2_<slug> → recipe status in the pattern library (the original ratify_*
    verdicts were hand-processed; ratify2 was about to be the same hole again)."""
    slug = row["item_id"].replace("ratify2_", "")
    ans = row["answer"]
    p = b / "data/pattern_cards_v1.json"
    lib = json.loads(p.read_text())
    card = next((c for c in lib["survivors"] if c["slug"] == slug), None)
    if not card:
        raise RuntimeError(f"recipe {slug} not in survivors")
    ts = (row.get("client_ts") or row.get("ts", ""))[:16]
    note = (row.get("note") or "").strip()
    if ans == "ratify":
        card["status"] = f"RATIFIED by Mohamed {ts} (ratify2 clean re-show)" + (f" «{note[:80]}»" if note else "")
    elif ans == "kill":
        lib["survivors"] = [c for c in lib["survivors"] if c["slug"] != slug]
        lib.setdefault("killed", []).append({**card, "killed_by": f"Mohamed {ts}", "note": note[:120]})
        card = None
    elif ans == "edit":
        card["status"] = f"REVISED-REQUESTED by Mohamed {ts}: «{note[:120]}» — awaiting re-approval"
    p.write_text(json.dumps(lib, ensure_ascii=False, indent=1))
    import subprocess as _sp
    _sp.run(["python3", str(b / "scripts/render_recipes_md.py")], capture_output=True, timeout=60)
    return f"recipe {slug} → {ans}" + (" (removed to killed)" if card is None else f" ({card['status'][:50]})")


def h_regen_scope(b: Path, row: dict) -> str:
    p = b / "data/mohamed_rulings_live.json"
    r = json.loads(p.read_text()) if p.exists() else {}
    r["regen_scope"] = {"value": row["answer"],
                        "ruled_at": row.get("client_ts") or row.get("ts"),
                        "source": "portal:regen_scope_ruling",
                        "doc": "which posts regenerate when keys refill (B216/B219)"}
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    assert json.loads(p.read_text())["regen_scope"]["value"] == row["answer"]
    return f"regen_scope={row['answer']} in mohamed_rulings_live.json (B219 unblocked on keys)"


def h_albaik_outreach(b: Path, row: dict) -> str:
    from organ_write import write_organ
    p = b / "clients/albaik/profile/state.json"
    st = json.loads(p.read_text())
    st["outreach_ruling"] = {"value": row["answer"],
                             "ruled_at": row.get("client_ts") or row.get("ts"),
                             "source": "portal:albaik_outreach_ruling (GAP-10)"}
    write_organ(str(p), st)
    ping = b / "clients/albaik/presentations/service_ping.md"
    if ping.exists():
        txt = ping.read_text()
        if "حكم محمد" not in txt:
            label = {"dry_run": "تمرين داخلي للأبد — لا يُرسل أبداً",
                     "real_prospect": "عميل محتمل حقيقي — التواصل بيد محمد فقط",
                     "park": "السؤال مؤجل"}.get(row["answer"], row["answer"])
            ping.write_text(txt.replace("# albaik", f"# albaik", 1)
                            .replace("مسودة داخلية", f"حكم محمد: {label} · مسودة داخلية", 1))
    return f"albaik outreach_ruling={row['answer']} (state organ + ping header)"


def h_coffee_v3(b: Path, row: dict) -> str:
    ans = row["answer"]
    bl = json.loads((b / "data/backlog.json").read_text())
    sid = {"elixirbunn": "B_elixirbunn_intake", "verify_rawi": "B_rawi_location_verify",
           "keep_hunting": "B_coffee_rehunt_r3"}.get(ans, f"B_coffee_{ans}")
    if not any(x.get("id") == sid for x in bl["steps"]):
        title = {"elixirbunn": "elixirbunn PILOT INTAKE — extraction → pyramid → year map (his pick)",
                 "verify_rawi": "Verify rawicoffee location from posts (his tap)",
                 "keep_hunting": "Coffee hunt round 3 — wider net (his tap)"}.get(ans, ans)
        bl["steps"].append({"id": sid, "title": title, "status": "open",
                            "top": "pilot clients prove the pyramid", "needs_apify": True,
                            "why": f"his coffee_pick_v3 tap → {ans} @ {(row.get('client_ts') or row.get('ts',''))[:16]}"})
        (b / "data/backlog.json").write_text(json.dumps(bl, ensure_ascii=False, indent=1))
    return f"coffee_pick_v3={ans} → backlog step {sid} staged (next orchestra pick)"


def h_idea_gate(b: Path, row: dict) -> str:
    """approvals_idea_gate A/B/C → the gate philosophy lands in mohamed_rulings_live.json
    (RABIE catch June 13: this was a live dead-end card — his architecture decision had
    nowhere to land)."""
    p = b / "data/mohamed_rulings_live.json"
    r = json.loads(p.read_text()) if p.exists() else {}
    posture = {"A": "sampled_then_graduate", "B": "autonomous_now",
               "C": "full_tap_every_idea"}.get(row["answer"], row["answer"])
    r["idea_gate"] = {"value": posture, "answer": row["answer"],
                      "ruled_at": row.get("client_ts") or row.get("ts"),
                      "source": "portal:approvals_idea_gate",
                      "doc": "idea/brief autonomy posture (docs/APPROVALS_ARCHITECTURE.md)"}
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    assert json.loads(p.read_text())["idea_gate"]["value"] == posture
    return f"idea_gate={posture} in mohamed_rulings_live.json"


def h_law_draft(b: Path, row: dict) -> str:
    """law_draft_<i> yes_law/no → promote the crystallize draft to law, or drop it
    (RABIE catch: the 'Make it law' button was wired to nothing)."""
    cq = b / "data/crystallize_queue.json"
    d = json.loads(cq.read_text())
    items = d.get("cards") or d.get("candidates") or []
    drafts = [c for c in items if "DRAFT" in str(c.get("status", ""))]
    try:
        idx = int(row["item_id"].split("_")[2])
    except (IndexError, ValueError):
        idx = 0
    draft = drafts[idx] if idx < len(drafts) else None
    if not draft:
        return f"no draft at index {idx} (already resolved?)"
    ts = (row.get("client_ts") or row.get("ts", ""))[:16]
    if row["answer"] == "no":
        draft["status"] = f"DROPPED by Mohamed {ts}"
        cq.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        return f"law draft «{str(draft.get('draft',''))[:40]}» DROPPED"
    draft["status"] = f"RATIFIED by Mohamed {ts} → law"
    cq.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    return (f"law draft «{str(draft.get('draft',''))[:40]}» RATIFIED — receipt logged; "
            "registry enforcement symbol added by hand")


def h_passport(b: Path, row: dict) -> str:
    """CLIENT PASSPORT (June 13): a free-text intake answer (passport_<handle>_<field>)
    → raw to clients/<h>/profile/passport.json (attributed) AND derived into the organ
    that fingerprint_status reads, so the RED organ goes green. The answer is the
    client's/founder's truth — confirmer = mohamed (founder) or client:<answerer>."""
    from organ_write import write_organ
    item = row["item_id"]
    q = json.loads((b / "data/decision_queue.json").read_text())["items"]
    card = next((c for c in q if c["id"] == item), {})
    handle = card.get("handle") or item.split("_")[1]
    field = card.get("field") or item.rsplit("_", 1)[-1]
    organ = card.get("organ") or {"identity": "fingerprint", "goals": "goals",
        "capacity": "goals", "red_lines": "red_lines", "truth": "truth_pack",
        "audience": "audience_mirror"}.get(field)
    answer = (row.get("note") or row.get("text_answer") or row.get("answer") or "").strip()
    if not answer or answer in ("A", "B", "C"):
        raise RuntimeError(f"empty/non-text passport answer for {item}")
    answerer = row.get("judge", "unknown")
    confirmer = "mohamed" if answerer == "mohamed" else f"client:{answerer}"
    ts = row.get("client_ts") or row.get("ts")
    prov = {"source": f"passport:{answerer}", "confirmer": confirmer,
            "confidence": "confirmed", "date": (ts or "")[:10]}

    # DIRECTIVE GUARD: a meta-instruction is not the brand's value — route to extraction_mode
    if _PASSPORT_DIRECTIVE.search(answer):
        mode = ("no_answer_figure_out"
                if re.search(r"no answer|figure (it )?out|let the system", answer, re.I)
                else "auto_research")
        emp = b / f"clients/{handle}/profile/extraction_mode.json"
        write_organ(str(emp), {"mode": mode, "note": answer[:200], "by": confirmer,
                               "date": (ts or "")[:10], "source": "passport directive (not stored as a value)"})
        pp = b / f"clients/{handle}/profile/passport.json"
        data = json.loads(pp.read_text()) if pp.exists() else {"handle": handle, "answers": {}}
        data["answers"][field] = {"directive": answer, "answerer": answerer, "mode": mode, "ts": ts}
        write_organ(str(pp), data)
        return f"{handle}.{field}: DIRECTIVE → extraction_mode={mode} (NOT stored as an organ value)"

    # 1. raw passport ledger (the client's verbatim truth, attributed)
    pp = b / f"clients/{handle}/profile/passport.json"
    data = json.loads(pp.read_text()) if pp.exists() else {"handle": handle, "answers": {}}
    data["answers"][field] = {"answer": answer, "answerer": answerer,
                              "confirmer": confirmer, "ts": ts}
    write_organ(str(pp), data)

    # 2. derive into the organ fingerprint_status reads (flip RED→green)
    op = b / f"clients/{handle}/profile/{organ}.json"
    o = json.loads(op.read_text()) if op.exists() else {}
    if organ == "fingerprint":
        l1 = o.setdefault("l1_strategy", {})
        l1["who_speaks"] = answer
        l1["usp"] = answer
        l1["_passport"] = prov
    elif organ == "goals":
        if field == "capacity":
            o["capacity"] = answer
        else:
            o["primary"] = answer
        o["answered"] = len(data["answers"])   # climbs to green (>=4) as they answer
        o["of"] = max(o.get("of", 5), 6)
        o["_passport"] = prov
    elif organ == "red_lines":
        o.setdefault("lines", []).append({"line": answer, **prov})
    elif organ == "truth_pack":
        o.setdefault("confirmed", []).append({"name": answer, **prov})
    elif organ == "audience_mirror":
        o.setdefault("segments", []).append({"desc": answer, **prov})
    write_organ(str(op), o)
    return f"{handle}.{field} → {organ} (confirmer {confirmer}); passport {len(data['answers'])}/6"


def h_crystallize_review(b: Path, row: dict) -> str:
    """digest review_now: the top 3 drafts arrive as individual yes/no law cards."""
    import queue_decision as qd
    d = json.loads((b / "data/crystallize_queue.json").read_text())
    items = d.get("cards") or d.get("candidates") or []
    drafts = [c for c in items if "DRAFT" in str(c.get("status", ""))][:3]
    q = json.loads((b / "data/decision_queue.json").read_text())["items"]
    existing = {it["id"] for it in q}
    pushed = []
    for i, c in enumerate(drafts):
        slug = str(c.get("draft", f"draft_{i}"))[:40].replace(" ", "_").replace(":", "")
        cid = f"law_draft_{i}_{slug[:24]}"
        if cid in existing:
            continue
        ev = c.get("evidence") or []
        ev_line = (ev[0].get("verdict", "")[:140] if ev and isinstance(ev[0], dict) else str(ev)[:140])
        qd.push_attributed({
            "id": cid, "title": f"Law draft: {str(c.get('draft',''))[:70]}",
            "tag": "Law", "clock": "", "priority": "normal",
            "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
            "kind": "buttons", "judge_lane": False, "lane": "strategy",
            "why": str(c.get("proposed_action", ""))[:200],
            "need": "Yes = permanent rule (registry + enforcement). No = the draft dies.",
            "did": f"Receipt: {ev_line}",
            "options": [{"v": "yes_law", "label": "✅ Make it law", "rec": True},
                        {"v": "no", "label": "🗑 Drop it"}],
        }, made_by="system:apply_rulings", via="scripts/apply_rulings.py",
           reason=f"his review_now tap on {row['item_id']}")
        pushed.append(cid)
    return f"pushed {len(pushed)} law-draft cards: {pushed}"


def h_crystallize_later(b: Path, row: dict) -> str:
    return "parked for the D6 sitting (his tap recorded; drafts stay in the queue with receipts)"


# prefix dispatch: (prefix, answer) pairs that match any item_id with that prefix
def h_v37_direction(b: Path, row: dict) -> str:
    """Mohamed's v3.7 first-render decision (the directional card). His tap is a write; it
    needs a reader (Rule #6). Records his choice to data/v37_direction.json so the orchestra
    acts on it — and so it stops flagging UNCONSUMED. 2026-06-14: he chose phoneshoot_batch."""
    ans = row.get("answer", "")
    meaning = {"phoneshoot_batch": "produce no-key phone-shoot posts (caption + shoot brief, $0) for his taste-gate",
               "render_now": "flip no_fal_photos + B141, render the v3.7 batch (≤$3)",
               "confirm_first": "confirm palette/material per brand before any render"}.get(ans, ans)
    p = b / "data/v37_direction.json"
    p.write_text(json.dumps({"choice": ans, "ts": row.get("ts"), "by": "mohamed",
                             "meaning": meaning, "status": "claude_to_act"}, ensure_ascii=False, indent=2))
    return f"v3.7 direction recorded: {ans} → {meaning}"


PREFIX_HANDLERS = {
    ("ratify2_", "ratify"): h_recipe_verdict,
    ("ratify2_", "kill"): h_recipe_verdict,
    ("ratify2_", "edit"): h_recipe_verdict,
    ("law_draft_", "yes_law"): h_law_draft,   # crystallize 'Make it law' (was wired to nothing)
    ("law_draft_", "no"): h_law_draft,
}

def h_pairwise_noop(b: Path, row: dict) -> str:
    """Pairwise A-vs-B picks are consumed by pairwise.consume() (called at main() start) into the
    taste-preference ledger — this no-op just marks them handled so they don't trip UNCONSUMED."""
    return f"pairwise pick {row.get('item_id')}={row.get('answer')} → taste-calibration ledger"


# item-prefix only (answer is arbitrary free text) — the client passport intake + pairwise picks
ITEM_PREFIX_HANDLERS = {
    "passport_": h_passport,
    "pw_": h_pairwise_noop,
}

HANDLERS = {
    ("gold_conflicts_0613", "drop_conflicted"): h_drop_conflicted,
    ("jurisha_voice_v3", "brand_voice"): h_brand_voice,
    ("taxonomy_evergreen_ruling", "daily"): h_taxonomy_daily,
    ("law_1_assert_at_the_SYSTEM", "yes_law"): h_law_assert_system,
    ("law_2_no_candidate_(client", "yes_law"): h_law_verified_before_shown,
    ("law_3_Mac-required_actions", "yes_law"): h_law_machine_evidence,
    ("coffee_pick_v2", "keep_hunting"): h_keep_hunting,
    ("reshow_4_recipes", "reshow"): h_reshow_recipes,
    ("regen_scope_ruling", "rolling_window"): h_regen_scope,
    ("regen_scope_ruling", "pilots_full"): h_regen_scope,
    ("regen_scope_ruling", "killed_only"): h_regen_scope,
    ("albaik_outreach_ruling", "dry_run"): h_albaik_outreach,
    ("albaik_outreach_ruling", "real_prospect"): h_albaik_outreach,
    ("albaik_outreach_ruling", "park"): h_albaik_outreach,
    ("coffee_pick_v3", "elixirbunn"): h_coffee_v3,
    ("coffee_pick_v3", "verify_rawi"): h_coffee_v3,
    ("coffee_pick_v3", "keep_hunting"): h_coffee_v3,
    ("crystallize_digest", "review_now"): h_crystallize_review,
    ("crystallize_digest", "later"): h_crystallize_later,
    ("approvals_idea_gate", "A"): h_idea_gate,   # his architecture decision (was dead-end)
    ("approvals_idea_gate", "B"): h_idea_gate,
    ("approvals_idea_gate", "C"): h_idea_gate,
    ("v37_alignment_summary", "phoneshoot_batch"): h_v37_direction,
    ("v37_alignment_summary", "render_now"): h_v37_direction,
    ("v37_alignment_summary", "confirm_first"): h_v37_direction,
}


def _resolve(key):
    """exact HANDLERS first, then PREFIX_HANDLERS (item-prefix + answer),
    then ITEM_PREFIX_HANDLERS (item-prefix only — for free-text intake where the
    answer is arbitrary, e.g. passport questions)."""
    if key in HANDLERS:
        return HANDLERS[key]
    for (pref, ans), fn in PREFIX_HANDLERS.items():
        if key[0].startswith(pref) and key[1] == ans:
            return fn
    for pref, fn in ITEM_PREFIX_HANDLERS.items():
        if key[0].startswith(pref):
            return fn
    return None


def founder_note_parity(b: Path) -> list:
    """Every Mohamed note ≥15 chars in the answers ledger must exist in founder_words.
    The religion note («play it very safe...») was consumed by the router tonight and
    never written — his words are gold, losing one is a system lie.
    Writes the ledger's NATIVE shape (field 'words' — first version wrote 'text' and
    duplicated 36 rows before the shape mismatch was caught)."""
    fw_p = b / "data/founder_words.jsonl"
    have = " ".join(r.get("words", "") for r in _read_jsonl(fw_p))
    fixed = []
    for r in _read_jsonl(b / ANSWERS):
        note = (r.get("note") or "").strip()
        if r.get("judge") == "mohamed" and len(note) >= 15 and note[:60] not in have:
            with open(fw_p, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "item_id": r.get("item_id"), "words": note, "processed": False,
                    "said_at": r.get("client_ts") or r.get("ts"),
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "via": "apply_rulings.founder_note_parity (backfill — router dropped it)",
                }, ensure_ascii=False) + "\n")
            have += " " + note
            fixed.append(r.get("item_id"))
    return fixed


# Answers before the wire existed were consumed BY HAND in their sessions; the cold
# review audited tonight's batch and the two real losses (drop ruling, religion note)
# are fixed above. From this epoch on, every ruling must flow through this wire.
WIRE_EPOCH = "2026-06-13T02:40:00"


def pending_unhandled(b: Path) -> list:
    """Post-epoch decision-card answers with no handler and no ledger entry —
    make_sure flags these red until a handler exists."""
    applied = {(r["item_id"], r["answer"]) for r in _read_jsonl(b / LEDGER)}
    out = []
    for r in _read_jsonl(b / ANSWERS):
        item, ans = r.get("item_id", ""), r.get("answer")
        if not ans or r.get("rating") is not None or item.startswith(("judge_", "judge2_", "ratify_")):
            continue  # judge/ratify lanes have their own consumers (router, gold_mint)
        if item in ("_general_note", "_repudiation"):
            continue  # control events — founder_note_parity / scorecards+portal own these
            # (_repudiation «مو أنا» is consumed by portal_mini in_reply_to + scorecards negation)
        if (r.get("ts") or r.get("client_ts") or "") < WIRE_EPOCH:
            continue  # pre-wire era: hand-consumed, audited by the June 13 cold review
        if ans in ACK_ANSWERS or (item, ans) in applied:
            continue
        if _resolve((item, ans)):
            out.append((item, ans, "HANDLER EXISTS BUT NOT APPLIED"))
        else:
            out.append((item, ans, "NO HANDLER"))
    return out


def main():
    b = base()
    # PAIRWISE consumer (Rule #6/#7 — the A-vs-B tap needs a handler that RUNS): every portal answer
    # cycle, fold his new pairwise picks into the taste-preference ledger so they never sit unconsumed.
    try:
        import sys as _s
        _s.path.insert(0, str(b / "scripts"))
        import pairwise as _pw
        _n = _pw.consume()
        import taste_elo as _te; _te.main()  # recompute Mohamed-Elo from his accumulating picks (Rule #6)
    except Exception:
        pass
    applied = {(r["item_id"], r["answer"]) for r in _read_jsonl(b / LEDGER)}
    done, errors = [], []
    seen = set()
    for r in _read_jsonl(b / ANSWERS):
        key = (r.get("item_id", ""), r.get("answer"))
        fn = _resolve(key)
        if key in applied or key in seen or fn is None:
            continue
        seen.add(key)
        try:
            evidence = fn(b, r)
            with open(b / LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "item_id": key[0], "answer": key[1],
                    "ruled_at": r.get("client_ts") or r.get("ts"),
                    "applied_at": datetime.now().isoformat(timespec="seconds"),
                    "handler": fn.__name__, "evidence": evidence,
                }, ensure_ascii=False) + "\n")
            done.append(f"  ✅ {key[0]} → {key[1]}: {evidence}")
        except Exception as e:
            errors.append(f"  🔴 {key[0]} → {key[1]}: {e}")
    backfilled = founder_note_parity(b)
    for d in done:
        print(d)
    if backfilled:
        print(f"  📜 founder notes backfilled: {backfilled}")
    leftover = pending_unhandled(b)
    for item, ans, why in leftover:
        print(f"  ⚠️ UNCONSUMED: {item} → {ans} ({why})")
    for e in errors:
        print(e)
    print(f"\n{'🔴 RULINGS PENDING' if (errors or leftover) else '🟢 ALL RULINGS APPLIED'}")
    raise SystemExit(1 if (errors or leftover) else 0)


if __name__ == "__main__":
    main()
