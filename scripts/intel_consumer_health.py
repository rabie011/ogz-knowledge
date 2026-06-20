#!/usr/bin/env python3
"""intel_consumer_health.py — Rule #6 consumer-health detector for intelligence_layer.json.

WHY THIS EXISTS (the recurring rot it closes):
Thin-Brain-v3.0 (commit f80d27e4) dropped 7 keys from intelligence_layer.json
(sector_playbooks, occasion_rules, universal_rules, anti_patterns, visual_rules,
caption_rules, format_rules) — but multiple readers kept calling `intel.get("<dropped>")`
and silently received {} / []. The brief engine's "PRIMARY — distilled rules" block ran
EMPTY through the live enricher daemon for many commits WITH NO ALARM. Three RABIE
zoom-outs in a row named the same structural hole: "we add organs faster than we verify
their consumers (Rule #6)" and "no alarm".

This is the DETECTOR for that hole, made GENERAL (not hardcoded to those 7 keys): it finds
every script that loads intelligence_layer.json, resolves the variable that holds the loaded
content, extracts every string-literal key it `.get()`s, and reports any key the LIVE
intelligence_layer.json no longer has. A rising count is the alarm we never had.

DIRECTION-INDEPENDENT (does not pre-judge Mohamed's B057c fork): it only makes the silent
degeneracy VISIBLE. Branch A (rewire readers) → the count shows the work remaining; branch B
(strip the dead reads) → the count auto-closes to 0 once the reads are removed. A refuse-guard
would have pre-judged branch A, so this surfaces rather than refuses (Rule #8 applies to
hard gates; this is a visibility signal, by design non-blocking).

Zero-LLM, pure static analysis. Usage: python3 scripts/intel_consumer_health.py
"""
from __future__ import annotations
import ast
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INTEL_FILE = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
SCRIPTS = BASE / "scripts"
INTEL_BASENAME = "intelligence_layer.json"

# Files that legitimately do NOT read the intel dict by key (e.g. they only write it, or
# only reference the path string). Kept explicit so the exclusion is auditable, not silent.
_NOT_KEY_READERS = {"index_freshness.py"}


def live_intel_keys(path: Path = INTEL_FILE) -> set[str]:
    """The keys the live intelligence_layer.json actually has right now (the ground truth)."""
    return set(json.loads(path.read_text(encoding="utf-8")).keys())


def _src_has_intel_ref(node: ast.AST) -> bool:
    """True if the (assignment-value) AST contains the basename string anywhere."""
    for s in ast.walk(node):
        if isinstance(s, ast.Constant) and isinstance(s.value, str) and INTEL_BASENAME in s.value:
            return True
    return False


def _is_intel_load(value: ast.AST, path_consts: set[str]) -> bool:
    """True if `value` is a json.load[s](...) call whose source is intelligence_layer.json —
    either the basename appears in the call, or it references a known path-const name."""
    if not isinstance(value, ast.Call):
        return False
    fn = value.func
    if not (isinstance(fn, ast.Attribute) and fn.attr in ("load", "loads")
            and isinstance(fn.value, ast.Name) and fn.value.id == "json"):
        return False
    if _src_has_intel_ref(value):
        return True
    for n in ast.walk(value):
        if isinstance(n, ast.Name) and n.id in path_consts:
            return True
    return False


_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _walk_own_scope(scope: ast.AST):
    """Yield every node in `scope` WITHOUT crossing into a nested function/class body — so each
    scope is evaluated on its own statements only (true lexical isolation). The scope node's own
    args/decorators are skipped; we descend only its body."""
    for stmt in getattr(scope, "body", []):
        stack = [stmt]
        while stack:
            n = stack.pop()
            yield n
            if isinstance(n, _SCOPE_NODES):
                continue  # yield the nested scope node, but never descend into its internals
            stack.extend(ast.iter_child_nodes(n))


def _path_consts(tree: ast.AST) -> set[str]:
    """Module-level names bound to a value mentioning intelligence_layer.json (e.g. INTEL_PATH)."""
    consts: set[str] = set()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign) and _src_has_intel_ref(node.value):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    consts.add(t.id)
    return consts


def _scope_intel_vars(scope, path_consts, params):
    """The intel vars BOUND inside this scope's own body: a name is one iff at least one local
    assignment to it is an intel-load. ANY-load (not all-load) so the common guard pattern
    `X = {}` / `X = json.loads(...) if path.exists()` still counts X. The derived-dict reuse
    that any-load would otherwise mis-flag (creative_pipeline.py's `intel = load_intelligence()`)
    is already separated by LEXICAL SCOPE isolation — it lives in a different function than the
    `intel = json.loads(...)` load. Returns (intel_vars, locally_bound) where locally_bound =
    every name assigned or param'd here (shadowing a module global of the same name)."""
    loaded: set[str] = set()
    assigned: set[str] = set()
    for stmt in _walk_own_scope(scope):
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
                    if _is_intel_load(stmt.value, path_consts):
                        loaded.add(t.id)
    intel_vars = {n for n in loaded if n not in params}
    locally_bound = assigned | params
    return intel_vars, locally_bound


def _params(scope) -> set[str]:
    params = set()
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = scope.args
        for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs):
            params.add(arg.arg)
        if a.vararg: params.add(a.vararg.arg)
        if a.kwarg: params.add(a.kwarg.arg)
    return params


def _scope_findings(scope, path_consts, live, file, module_intel_vars=frozenset()):
    """Flag `<intelvar>.get("literal")` where the key is absent from the live file. An intel var
    is either bound locally as an intel-load, OR a module-level intel global visible here (not
    shadowed by a local binding/param) — so a global read INSIDE a function (the live
    build_production_brief_engine.py case) is caught."""
    params = _params(scope)
    local_intel_vars, locally_bound = _scope_intel_vars(scope, path_consts, params)
    inherited = set(module_intel_vars) - locally_bound
    intel_vars = local_intel_vars | inherited
    own_nodes = list(_walk_own_scope(scope))
    findings = []
    for n in own_nodes:
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get"
                and isinstance(n.func.value, ast.Name) and n.func.value.id in intel_vars
                and n.args and isinstance(n.args[0], ast.Constant)
                and isinstance(n.args[0].value, str)):
            key = n.args[0].value
            if key not in live:
                findings.append({"file": file, "line": n.lineno, "key": key, "var": n.func.value.id})
    return findings


def orphaned_intel_reads(scripts_dir: Path = SCRIPTS, intel_path: Path = INTEL_FILE):
    """Scan every script that loads intelligence_layer.json; return reads of keys the live file
    no longer has. Scope-aware (ast) so a var reused as a parameter/derived dict is not a false
    positive. Returns a list of {file, line, key, var}, sorted."""
    live = live_intel_keys(intel_path)
    findings = []
    for py in sorted(scripts_dir.glob("*.py")):
        if py.name in _NOT_KEY_READERS or py.name == Path(__file__).name:
            continue
        try:
            src = py.read_text(encoding="utf-8")
        except Exception:
            continue
        if INTEL_BASENAME not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        pcs = _path_consts(tree)
        module_intel_vars, _ = _scope_intel_vars(tree, pcs, params=set())
        # module scope first (catches module-level reads), then every function scope with the
        # module intel globals propagated in (catches global reads inside functions)
        findings.extend(_scope_findings(tree, pcs, live, py.name))
        for scope in (n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            findings.extend(_scope_findings(scope, pcs, live, py.name, module_intel_vars))
    # a module-scope walk re-counts function-body gets; dedupe by (file,line,key,var)
    seen, uniq = set(), []
    for f in findings:
        k = (f["file"], f["line"], f["key"], f["var"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return sorted(uniq, key=lambda f: (f["file"], f["line"]))


# --- Human-confirmed verdict starvation (Rule #6 — verified June 20) -------------------------------
# THE SEVERANCE: Mohamed taps APPROVE / rating>=4 on the portal (data/mohamed_answers.jsonl), but no
# consumer turns a POSITIVE verdict into a HUMAN-confirmed client-ledger event. Every verdict event on
# every pilot ledger carries confirmer=rabie_provisional; B082 writeback_replay and B084
# writeback_moments move trust on HUMAN hands only (approvers_registry.HUMANS), so they replay/promote
# NOTHING — the loops are built but structurally STARVED while make_sure stays all-green. This detector
# makes that starvation MACHINE-VISIBLE (it was invisible): his real YESes never reach the wells they
# should feed. Visibility signal only (mirrors orphaned_intel_reads) — the fix is the unbuilt
# portal-approve→human-confirmed-ledger writer (next backlog pick), not a gate here.
_CLIENTS_DIR = BASE / "clients"
_ANSWERS_FILE = BASE / "data" / "mohamed_answers.jsonl"
_PILOTS = ("eatjurisha", "albaik", "myfitness.sa")
_HUMAN_CONFIRMERS = {"mohamed", "alhareth", "client"}
# ledger event types that carry a human VERDICT (vs intake / structural events)
_VERDICT_TYPES = {"client_approved", "client_rejected", "version_verdict", "batch_rating",
                  "voice_rating", "compare_verdict", "pick_selected", "occasion_gold"}
# a positive portal verdict that SHOULD compound the human-hands wells (B082/B084)
_POSITIVE_ANSWERS = {"approved", "approve", "yes", "gold", "love"}
# THE SEVERED LANE specifically: judge2_* batch approvals. The pairwise PICK lane already lands
# human-confirmed pick_selected events (3 exist) — so a binary "any human verdict exists?" GREEN-WASHES
# the break (an unrelated lane clears it). The real gap is per-lane: his judge2 batch approvals
# (49 positive) produce ZERO human-confirmed ledger events. A judge2 approval SHOULD land as one of
# these human-confirmed ledger types; today none does (batch_rating events are all rabie_provisional).
_JUDGE2_LEDGER_TYPES = {"client_approved", "batch_rating"}


def _read_jsonl(p):
    """Tolerant JSONL reader: missing file → [], a torn line is skipped (never crash a detector)."""
    rows = []
    try:
        text = Path(p).read_text(encoding="utf-8")
    except FileNotFoundError:
        return rows
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return rows


def portal_positive_verdicts(answers_path: Path = _ANSWERS_FILE) -> int:
    """Count Mohamed's POSITIVE portal verdicts (approve / rating>=4) — the taps that SHOULD feed the
    human-hands wells. Only judge==mohamed (his eye is the trust mover)."""
    n = 0
    for r in _read_jsonl(answers_path):
        if r.get("judge") != "mohamed":
            continue
        ans = str(r.get("answer", "")).strip().lower()
        rating = r.get("rating")
        if ans in _POSITIVE_ANSWERS or (isinstance(rating, int) and rating >= 4):
            n += 1
    return n


def judge2_positive_approvals(answers_path: Path = _ANSWERS_FILE) -> int:
    """His judge2_* BATCH approvals that are positive (approved / rating>=4) — the input to the lane
    that SHOULD compound the moments well (B084) but is severed."""
    n = 0
    for r in _read_jsonl(answers_path):
        if r.get("judge") != "mohamed":
            continue
        if not str(r.get("item_id", "")).startswith("judge2_"):
            continue
        ans = str(r.get("answer", "")).strip().lower()
        rating = r.get("rating")
        if ans in _POSITIVE_ANSWERS or (isinstance(rating, int) and rating >= 4):
            n += 1
    return n


def human_confirmed_ledger_verdicts(clients_dir: Path = _CLIENTS_DIR, pilots=_PILOTS,
                                    types=_VERDICT_TYPES) -> int:
    """Count ledger verdict events that carry a HUMAN confirmer — the events B082/B084 actually replay.
    rabie_provisional events do NOT count (they never move trust). `types` narrows to a lane."""
    n = 0
    for h in pilots:
        for ev in _read_jsonl(Path(clients_dir) / h / "events" / "ledger.jsonl"):
            if (ev.get("type") in types
                    and (ev.get("confirmer") or "").lower() in _HUMAN_CONFIRMERS):
                n += 1
    return n


def human_verdict_starvation(answers_path: Path = _ANSWERS_FILE,
                             clients_dir: Path = _CLIENTS_DIR, pilots=_PILOTS) -> dict:
    """The severance signal — LANE-AWARE so an unrelated fed lane can't green-wash a real break.

    `starved` keys ONLY on the judge2 batch-approval lane: positive judge2 approvals exist (input) but
    ZERO of them became a human-confirmed ledger verdict (client_approved / human batch_rating). The
    general counts (all-lane positive taps + all-lane human-confirmed verdicts) ride along for context
    — the pairwise PICK lane already lands pick_selected, so the all-lane human count is >0 and must
    NOT clear the signal. Auto-closes the moment the judge2 writer lands one human-confirmed event."""
    j2_pos = judge2_positive_approvals(answers_path)
    j2_led = human_confirmed_ledger_verdicts(clients_dir, pilots, types=_JUDGE2_LEDGER_TYPES)
    return {"judge2_positive": j2_pos,
            "judge2_human_confirmed_ledger": j2_led,
            "portal_positive": portal_positive_verdicts(answers_path),
            "human_confirmed_ledger_verdicts": human_confirmed_ledger_verdicts(clients_dir, pilots),
            "starved": j2_pos > 0 and j2_led == 0}


def report():
    findings = orphaned_intel_reads()
    if not findings:
        print("✅ intel-consumer health: 0 orphaned reads — every reader's keys exist in "
              "intelligence_layer.json")
        return 0
    print(f"⚠️  intel-consumer health: {len(findings)} ORPHANED read(s) — readers .get() keys the "
          f"live intelligence_layer.json no longer has (Rule #6 — silent degeneracy):")
    for f in findings:
        print(f"   {f['file']}:{f['line']}  {f['var']}.get(\"{f['key']}\")  ← key absent")
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], 0)
        by_file[f["file"]] += 1
    print("   by file: " + " · ".join(f"{k}:{v}" for k, v in sorted(by_file.items())))
    print("   (visibility signal only — resolution is gated on B057c fork: rewire vs strip)")
    return 0  # non-blocking by design: a visibility signal, not a hard gate


if __name__ == "__main__":
    import sys
    sys.exit(report())
