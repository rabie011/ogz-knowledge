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
from feedback_lib import base, crystallize_cards, pending_crystallize

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
    drafts = pending_crystallize(crystallize_cards(d))
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
    drafts = pending_crystallize(crystallize_cards(d))[:3]
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


# v3.7 visual_dna free-text card → the organ field(s) the converter reads. One card per
# (handle, group); his free-text answer is the CLIENT truth for that group. The targets are
# exactly the paths openclaw_convert._sf() reads, so his answer reaches the render (Rule #6 —
# build the consumer in the same cycle). brand_paths land on visual_dna['brand']; product_keys
# are stamped on EVERY product (one card covers all of a brand's products).
V37_GROUP_TARGETS = {
    "colour":           {"brand_paths": [("palette", "primary"), ("palette", "background_tone"),
                                         ("color_field_palette",)]},
    "product_physical": {"product_keys": ["material_finish", "material_texture",
                                          "silhouette_description", "dimensions"]},
    "identity_lock":    {"product_keys": ["identity_dna", "label_text_arabic", "label_text_latin"]},
}


def _v37_stamp_field(node: dict, key, ans: str, ts: str, item: str) -> bool:
    """Flip one statusField {value,status,provenance} to client-confirmed truth (idempotent).
    Stores his verbatim answer in client_confirmed (the converter appends it as authoritative
    client truth) + flips status GREEN + provenance.confirmer=mohamed. Returns True if stamped."""
    fld = node.get(key)
    if not isinstance(fld, dict):
        fld = {"value": None, "status": "RED"}
        node[key] = fld
    fld["client_confirmed"] = {"answer": ans, "confirmer": "mohamed", "ts": ts, "source": f"portal:{item}"}
    fld["status"] = "GREEN"
    prov = fld.setdefault("provenance", {})
    prov["confirmer"], prov["confidence"], prov["confirmed_ts"] = "mohamed", "confirmed", ts
    return True


def h_v37_visual(b: Path, row: dict) -> str:
    """B186d — Mohamed's free-text answer on a v3.7 visual card (palette / products_phys /
    identity_ref) is the CLIENT truth the v3.7 organ was waiting on. Until this handler the 10
    cards had NO consumer, so bridge_drain HELD them off his portal (Rule #7 — a tap with
    nowhere to land never ships). This is that consumer: it writes his verbatim answer into
    clients/<handle>/profile/visual_dna.json at the exact fields openclaw_convert reads, flips
    their status GREEN + confirmer=mohamed, so his confirmed truth reaches the render (Rule #6).
    We never author the value — his words are stored verbatim (Rule #12). Self-audit: the write
    MUST be on disk before we claim it applied (Rule #11)."""
    item, ans = row.get("item_id", ""), (row.get("answer") or "").strip()
    if not ans:
        raise RuntimeError(f"v37 card {item} returned an empty answer — nothing to confirm")
    staged = b / "data" / "v37_confirm_staged.json"
    if not staged.exists():
        raise RuntimeError("no data/v37_confirm_staged.json — run the v37 card generator")
    cards = {c["id"]: c for c in json.loads(staged.read_text(encoding="utf-8")).get("cards", [])}
    card = cards.get(item)
    if not card:
        raise RuntimeError(f"v37 card {item} not in staged file")
    handle, group = card["handle"], card.get("group", "")
    targets = V37_GROUP_TARGETS.get(group)
    if not targets:
        raise RuntimeError(f"v37 card {item}: unknown group «{group}»")
    vdf = b / "clients" / handle / "profile" / "visual_dna.json"
    if not vdf.exists():
        raise RuntimeError(f"no visual_dna.json for {handle}")
    vd = json.loads(vdf.read_text(encoding="utf-8"))
    ts = row.get("ts") or datetime.now().isoformat(timespec="seconds")
    n = 0
    brand = vd.setdefault("brand", {})
    for path in targets.get("brand_paths", []):
        node = brand
        for seg in path[:-1]:
            node = node.setdefault(seg, {})
        n += _v37_stamp_field(node, path[-1], ans, ts, item)
    for prod in vd.get("products", []):
        for key in targets.get("product_keys", []):
            n += _v37_stamp_field(prod, key, ans, ts, item)
    # also keep a per-group audit record at organ top-level (findable, never re-authored)
    vd.setdefault("client_confirmed", {})[group] = {
        "answer": ans, "confirmer": "mohamed", "ts": ts, "card": item, "fields_stamped": n}
    sys.path.insert(0, str(Path(__file__).parent))
    from organ_write import write_organ
    write_organ(vdf, vd)
    # self-audit (Rule #11): the confirmation MUST be on disk before we claim it applied
    disk = json.loads(vdf.read_text(encoding="utf-8")).get("client_confirmed", {}).get(group, {})
    assert disk.get("answer") == ans, f"v37 confirm not on disk for {handle}/{group}"
    return f"v3.7 {group} confirmed for {handle}: «{ans[:40]}» → {n} field(s) GREEN (client truth reaches render)"


def h_crosswalk_confirm(b: Path, row: dict) -> str:
    """B083c — Mohamed's tap on the reason_code crosswalk card (A-47) is the gate that
    UNSEVERS the writeback kill-wire (B083/B083b). His confirm flips proposed→confirmed in
    data/reason_code_crosswalk.json; load_crosswalk() then propagates the translated kills.
    Until this tap every entry stays 'proposed' and propagation is an honest 0 (Rule #12 —
    we never author taste; his tap is the only thing that flips a proposal).

    answer 'reject' → confirms nothing, records his call. answer 'confirm_all' → flips every
    proposed entry that carries a real proposed_kill (null-target codes like tone_off/off_brief
    can never confirm — they have no kill to map to). An optional row['confirm_codes'] list
    restricts the flip to those codes (granular taste). Idempotent: already-confirmed rows are
    left untouched. Self-audit: asserts the flip is on disk before claiming applied."""
    ans = row.get("answer", "")
    path = b / "data/reason_code_crosswalk.json"
    if not path.exists():
        raise RuntimeError("no data/reason_code_crosswalk.json to confirm")
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc.get("map", [])
    ts = row.get("ts") or datetime.now().isoformat(timespec="seconds")
    if ans == "reject":
        doc.setdefault("_meta", {})["stamp"] = f"REJECTED — Mohamed declined {ts} (all entries stay proposed)"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        return "crosswalk rejected — all entries stay proposed, kill-wire propagates an honest 0 (his call recorded)"
    only = row.get("confirm_codes")  # optional granular subset; None = confirm_all
    flipped = []
    for r in rows:
        if r.get("status") != "proposed" or not r.get("proposed_kill"):
            continue  # already confirmed, or null-target (no kill to map to)
        if only and r.get("code") not in only:
            continue
        r["status"], r["confirmer"], r["ts"] = "confirmed", "mohamed", ts
        flipped.append(r["code"])
    doc.setdefault("_meta", {})["stamp"] = f"CONFIRMED — Mohamed tapped {ts} ({len(flipped)} mappings live)"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    # self-audit (Rule #11): the flip MUST be on disk before we claim it applied
    confirmed_now = {r["code"] for r in json.loads(path.read_text(encoding="utf-8")).get("map", [])
                     if r.get("status") == "confirmed"}
    missing = [c for c in flipped if c not in confirmed_now]
    if missing:
        raise RuntimeError(f"crosswalk flip not on disk for {missing}")
    return f"crosswalk confirmed {len(flipped)} mappings: {flipped} → kill-wire now propagates"


def h_publish_confirm(b: Path, row: dict) -> str:
    """B095v STEP 2 — Mohamed's go-live tap (his side; fork B095t ruled =A) records ONE
    `published` event into the outcome ledger via outcome_ledger.record_published. This is
    the reader Rule #6/#7 demand for build_publish_confirm_cards.py: without it his
    'published' tap vanishes and BOTH outcome readers (outcome_receipt + outcome_question)
    stay honest-empty forever — the learning loop never closes.

    The card id → (subject_generation_ulid, brand_ulid) mapping comes from
    data/publish_confirm_staged.json (the generator is the only authority on what each card
    means — same contract as truth_confirm). Rule #8: refuse (RuntimeError) if the staged
    file, the card, or its join-keys are missing — never half-record. Rule #11: the event
    MUST be on disk before we claim it applied. Rule #12: the SYSTEM minted the ulids at
    produce time; his tap only confirms the piece went live — we never author the identity."""
    item = row.get("item_id", "")
    staged = b / "data" / "publish_confirm_staged.json"
    if not staged.exists():
        raise RuntimeError("no data/publish_confirm_staged.json — run build_publish_confirm_cards.py --write")
    cards = {c["id"]: c for c in json.loads(staged.read_text(encoding="utf-8")).get("cards", [])}
    card = cards.get(item)
    if not card:
        raise RuntimeError(f"publish-confirm card {item} not in staged file")
    gen = (card.get("subject_generation_ulid") or "").strip()
    brand = (card.get("brand_ulid") or "").strip()
    if not gen or not brand:
        raise RuntimeError(f"publish-confirm card {item} missing subject_generation_ulid/brand_ulid")
    sys.path.insert(0, str(Path(__file__).parent))
    import outcome_ledger as ol
    ledger = b / "data" / "published.jsonl"
    ev = ol.record_published(gen, brand, timestamp=row.get("client_ts") or row.get("ts"), path=ledger)
    on_disk = {e.get("subject_generation_ulid") for e in ol._read_jsonl(ledger)}  # Rule #11 — assert before claiming
    assert gen in on_disk, f"publish event for {gen} not on disk"
    return (f"published recorded: {card.get('handle','?')} {card.get('date','')} "
            f"gen={gen[:10]}… → outcome ledger ({ev['timestamp'][:10]})")


def h_post_review(b: Path, row: dict) -> str:
    """June 29 — the READER for push_posts_for_review.py cards (Rule #6/#7: his tap needs a handler).
    Mohamed's approve/reject on a `post_<bankkey>` card is the AUTHORITATIVE HUMAN signal (he is the
    ground truth — AI can't judge Saudi creative). APPROVE passes the post by human verdict WITHOUT
    weakening the machine 2-signal gate (Rule #13 stays intact) + seeds gold (Rule #14). REJECT kills
    the setup so the producer avoids it (kill_registry, Rule #14)."""
    bankkey = row["item_id"][len("post_"):]
    ans = row["answer"]
    ts = (row.get("client_ts") or row.get("ts", ""))[:16]
    note = (row.get("note") or "").strip()
    handle, product, chain = (bankkey.split("__") + ["", "", ""])[:3]
    bankf = b / "data/caption_bank.json"
    bank = json.loads(bankf.read_text())
    entry = bank.get(bankkey)
    if not entry:
        raise RuntimeError(f"post {bankkey} not in caption_bank")
    entry["human_verdict"] = {"verdict": ans, "by": "mohamed", "ts": ts, "note": note[:160]}
    if ans == "approved":
        entry["passed_by_human"] = True   # authoritative human signal; machine 'passed' gate untouched
        bankf.write_text(json.dumps(bank, ensure_ascii=False, indent=1))
        # mission count = REAL human-passed posts (honest; replaces the inflated produced-count)
        mf = b / "data/mission_9posts.json"
        m = json.loads(mf.read_text())
        cl = m.setdefault("clients", {}).setdefault(handle, {"target": 3})
        hp = cl.setdefault("human_passed", [])
        if bankkey not in hp:
            hp.append(bankkey)
        m["_VERIFIED_true_passed"] = sum(len(c.get("human_passed", [])) for c in m["clients"].values())
        mf.write_text(json.dumps(m, ensure_ascii=False, indent=1))
        # seed gold (Rule #14 — his YES teaches the renderer)
        try:
            gf = b / f"clients/{handle}/profile/gold.json"
            g = json.loads(gf.read_text()) if gf.exists() else {"gold": [], "dropped": []}
            if not any(e.get("key") == bankkey for e in g.get("gold", [])):
                g.setdefault("gold", []).append({"key": bankkey, "caption": entry.get("caption"),
                                                 "source": f"mohamed_approve {ts}", "product": product})
                gf.parent.mkdir(parents=True, exist_ok=True)
                gf.write_text(json.dumps(g, ensure_ascii=False, indent=1))
        except Exception as _ge:
            sys.stderr.write(f"  (gold seed skipped: {type(_ge).__name__})\n")
        return f"post {bankkey} → APPROVED by Mohamed (human-passed; true_passed={m['_VERIFIED_true_passed']}/9) + gold seeded"
    elif ans == "rejected":
        bankf.write_text(json.dumps(bank, ensure_ascii=False, indent=1))
        try:
            import kill_registry as kr
            kr.add_perf_kill(handle, product, chain, f"Mohamed rejected the post {ts}: {note[:80]}")
        except Exception as _ke:
            sys.stderr.write(f"  (kill_registry skipped: {type(_ke).__name__})\n")
        return f"post {bankkey} → REJECTED by Mohamed → kill_registry (producer will avoid it)"
    return f"post {bankkey} → {ans} (noted)"


PREFIX_HANDLERS = {
    ("ratify2_", "ratify"): h_recipe_verdict,
    ("ratify2_", "kill"): h_recipe_verdict,
    ("ratify2_", "edit"): h_recipe_verdict,
    ("law_draft_", "yes_law"): h_law_draft,   # crystallize 'Make it law' (was wired to nothing)
    ("law_draft_", "no"): h_law_draft,
    ("publish_confirm_", "published"): h_publish_confirm,  # B095v STEP 2 — the go-live tap → outcome ledger
    ("post_", "approved"): h_post_review,     # June 29 — his post approve = authoritative human pass + gold
    ("post_", "rejected"): h_post_review,     # his post reject = kill the setup (Rule #14)
}

def h_pairwise_noop(b: Path, row: dict) -> str:
    """Pairwise A-vs-B picks are consumed by pairwise.consume() (called at main() start) into the
    taste-preference ledger — this no-op just marks them handled so they don't trip UNCONSUMED."""
    return f"pairwise pick {row.get('item_id')}={row.get('answer')} → taste-calibration ledger"


def h_truth_confirm(b: Path, row: dict) -> str:
    """B186 — Mohamed's tap on a truth-confirm card ratifies (or kills) a mined product
    candidate in clients/<handle>/profile/truth_pack.json. This is the reader Rule #6
    demands for build_truth_confirm_cards.py — without it the cards would be a write with
    no consumer and his tap would vanish.

    The card id → (handle, candidate) mapping comes from data/truth_confirm_staged.json
    (the generator is the only authority on what each card means). Answers:
      confirm → provenance.confirmer=mohamed, confidence=confirmed (the producer may now
                use this product as ratified truth; Rule #12 — we never confirm, his tap does)
      reject  → confidence=rejected, confirmer=mohamed (KEPT, never deleted — nothing is lost)
      <text>  → on a *_prices card, written verbatim into truth_pack['prices']; the named
                candidates are confirmed in the same move.
    Self-audit (Rule #11): the change MUST be on disk before we claim it applied."""
    item, ans = row.get("item_id", ""), row.get("answer", "")
    staged = b / "data" / "truth_confirm_staged.json"
    if not staged.exists():
        raise RuntimeError("no data/truth_confirm_staged.json — run build_truth_confirm_cards.py --write")
    cards = {c["id"]: c for c in json.loads(staged.read_text(encoding="utf-8")).get("cards", [])}
    card = cards.get(item)
    if not card:
        raise RuntimeError(f"truth-confirm card {item} not in staged file")
    handle, cand = card["handle"], card["candidate"]
    tpf = b / "clients" / handle / "profile" / "truth_pack.json"
    if not tpf.exists():
        raise RuntimeError(f"no truth_pack for {handle}")
    tp = json.loads(tpf.read_text(encoding="utf-8"))
    ts = row.get("ts") or datetime.now().isoformat(timespec="seconds")
    sys.path.insert(0, str(Path(__file__).parent))
    from organ_write import write_organ

    if cand == "__prices__":
        tp["prices"] = [{"line": ans, "confirmer": "mohamed", "ts": ts, "source": f"portal:{item}"}]
        for c in tp.get("product_candidates", []):
            prov = c.setdefault("provenance", {})
            if prov.get("confirmer") in ("data_diagnosis", "pending_client"):
                prov["confirmer"], prov["confidence"], prov["confirmed_ts"] = "mohamed", "confirmed", ts
        write_organ(tpf, tp)
        on_disk = json.loads(tpf.read_text(encoding="utf-8")).get("prices", [])
        assert on_disk and on_disk[0].get("line") == ans, f"price write not on disk for {handle}"
        return f"truth prices recorded for {handle}: «{ans[:40]}» + {handle} candidates confirmed"

    found = next((c for c in tp.get("product_candidates", []) if c.get("name") == cand), None)
    if not found:
        raise RuntimeError(f"candidate «{cand}» not in {handle} truth_pack")
    prov = found.setdefault("provenance", {})
    if ans == "reject":
        prov["confirmer"], prov["confidence"], prov["rejected_ts"] = "mohamed", "rejected", ts
        verb = "rejected (kept, never deleted)"
    else:  # confirm (or any positive tap)
        prov["confirmer"], prov["confidence"], prov["confirmed_ts"] = "mohamed", "confirmed", ts
        verb = "confirmed → ratified truth"
    write_organ(tpf, tp)
    disk = next((c for c in json.loads(tpf.read_text(encoding="utf-8")).get("product_candidates", [])
                 if c.get("name") == cand), {})
    want = "rejected" if ans == "reject" else "confirmed"
    assert disk.get("provenance", {}).get("confidence") == want, \
        f"truth-confirm flip not on disk for {handle}/{cand}"
    return f"truth candidate «{cand}» ({handle}) {verb}"


# item-prefix only (answer is arbitrary free text) — the client passport intake + pairwise picks
ITEM_PREFIX_HANDLERS = {
    "passport_": h_passport,
    "pw_": h_pairwise_noop,
    "truth_confirm_": h_truth_confirm,  # B186 — free-text price answers (confirm/reject hit PREFIX_HANDLERS first)
    "v37_": h_v37_visual,  # B186d — v3.7 visual_dna free-text cards (v37_alignment_summary stays an exact handler, resolved first)
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
    ("reason_code_crosswalk_0619", "confirm_all"): h_crosswalk_confirm,  # B083c — flips proposed→confirmed
    ("reason_code_crosswalk_0619", "reject"): h_crosswalk_confirm,
}


def h_fork_decision(b: Path, row: dict) -> str:
    """Generic landing for ANY portal `*_fork` decision card (Rule #7 — his A/B tap must
    LAND, not trip a red alarm + vanish; born June 22, RABIE's pick, when
    B057c_thinbrain_primary_fork and B095t_publish_trigger_fork sat live on his phone with
    no handler — the exact dead-end scar h_idea_gate was built to close).

    Reads the card from data/decision_queue.json — the only authority on the fork's valid
    option values + their meaning — validates his answer against the declared options
    (Rule #8: refuse an undeclared answer, never guess), then records the confirmed choice
    into data/mohamed_rulings_live.json under fork_decisions[<card_id>]. That live-rulings
    file is already CONSUMED across the system (producer + make_sure + next-shift backlog),
    so the write has a reader (Rule #6) — the same landing pattern as h_idea_gate. Asserts
    on disk (Rule #11). Does NOT execute the fork's follow-on work (e.g. B057b rewire/strip):
    that is the dependent backlog step, done by the pair next shift per his recorded
    direction — we land the decision, we don't pre-judge or pre-build it (Rule #11/#12)."""
    item = row.get("item_id", "")
    ans = (row.get("answer") or "").strip()
    dq_p = b / "data/decision_queue.json"
    if not dq_p.exists():
        raise RuntimeError("no data/decision_queue.json — cannot validate fork options")
    dq = json.loads(dq_p.read_text(encoding="utf-8"))
    items = dq.get("items", []) if isinstance(dq, dict) else dq
    card = next((c for c in items if c.get("id") == item), None)
    if not card:
        raise RuntimeError(f"fork card {item} not in decision_queue.json")
    valid = {str(o.get("v")): (o.get("label") or "")
             for o in (card.get("options") or []) if isinstance(o, dict)}
    if ans not in valid:
        raise RuntimeError(f"fork {item}: answer «{ans}» not a declared option {sorted(valid)}")
    p = b / "data/mohamed_rulings_live.json"
    r = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    fd = r.setdefault("fork_decisions", {})
    fd[item] = {
        "answer": ans,
        "choice": valid[ans],
        "title": card.get("title", ""),
        "ruled_at": row.get("client_ts") or row.get("ts"),
        "confirmer": "mohamed",
        "source": f"portal:{item}",
    }
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    on_disk = json.loads(p.read_text(encoding="utf-8")).get("fork_decisions", {}).get(item, {})
    assert on_disk.get("answer") == ans, f"fork decision {item} not on disk"
    return f"fork {item} → «{ans}: {valid[ans][:50]}» landed in mohamed_rulings_live.json"


def _resolve(key):
    """exact HANDLERS first, then PREFIX_HANDLERS (item-prefix + answer),
    then ITEM_PREFIX_HANDLERS (item-prefix only — for free-text intake where the
    answer is arbitrary, e.g. passport questions), then the `*_fork` suffix dispatch
    (every decision-fork card lands generically — Rule #7, no per-fork wiring needed)."""
    if key in HANDLERS:
        return HANDLERS[key]
    for (pref, ans), fn in PREFIX_HANDLERS.items():
        if key[0].startswith(pref) and key[1] == ans:
            return fn
    for pref, fn in ITEM_PREFIX_HANDLERS.items():
        if key[0].startswith(pref):
            return fn
    if key[0].endswith("_fork"):
        return h_fork_decision
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
    # A corrupt tap-ledger must NOT be swallowed here (the old `except Exception: pass` hid exactly the
    # Consumer-Law fault this loop keeps scarring on): pairwise.ConsumeError re-raises so the heartbeat
    # EXITS loud (Rule #8). Only a soft/optional failure (e.g. taste_elo recompute) degrades quietly.
    import sys as _s
    _s.path.insert(0, str(b / "scripts"))
    import pairwise as _pw
    _pw.consume()                                    # raises ConsumeError on a severed/corrupt wire
    try:
        import taste_elo as _te; _te.main()          # recompute Mohamed-Elo (soft — never blocks rulings)
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
