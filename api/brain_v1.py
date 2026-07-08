#!/usr/bin/env python3
"""brain_v1.py — SPEC-012 THE BRAIN API, the /v1 action/runtime service.

A SEPARATE SIBLING FastAPI app on 127.0.0.1:4150 (FABLE ruling #2 — NEVER bolt mutating
job/publish handlers onto the read-only retrieval service on :4140, tools/brain_api.py). Distinct
lifecycle, distinct launchd (com.ogz.brain-v1, STAGED not loaded).

WAVE 1 (this build — first three must-build-new of SPEC-012 §9, in the ratified build order):
  (6) the /v1 app shell (this file) — thin FastAPI over the jail spine + ledgers.
  (2) job_events streaming [critical path, ruling #1] — GET /v1/jobs/{id}/events (poll + SSE),
      reading ledgers/job_events.jsonl via tools/jail/events.read_events(). Producers emit through
      tools/jail/events.py.
  (3) per-brand auth + tenancy wall [survey #1 blocker] — Bearer org_token + X-Brand header,
      resolved against ledgers/api_keys.json; every /v1 route brand-scoped; brand A touching brand
      B = 403 namespace_breach + one audit line + a needs_mohamed flag (the CEO-law halt).

Surface (b) job create is included because the stream (c) is meaningless without a job to stream,
and it is the smallest mutating surface that exercises the audit ledger + tenancy wall end-to-end.
Surfaces a/d/e/f/g/h/i are LATER waves — they answer with a loud `not_wired` refusal here (Rule #8:
refuse-don't-warn; never a silent 200), so a caller learns the truth instead of a fake success.

CONTRACT INVARIANTS (SPEC-012 §1):
  - Every response carries `confidence` + `provenance` (§1.2 / §1.1).
  - Refuse-don't-warn: a bad/unsafe/out-of-scope call returns the §1.1 refusal object, 4xx,
    confidence:"refused", a plain-Arabic reason_ar, an English reason_code. Never a degraded 200.
  - Every mutating call writes exactly one brain_api_audit line through tools/jail/ledger.py (the
    ONE write path). A refused mutating call still audits (reason_code set). actor_token is HASHED.

stdlib + FastAPI only (FastAPI is installed for the portal; we reuse its patterns from
api/portal_mini.py). No new LLM calls. No git in HOME. Honors OGZ_JAIL_ROOT for the test sandbox.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

# --------------------------------------------------------------------------- roots + wiring
# DATA lives under ROOT (OGZ_JAIL_ROOT for a sandbox); the tool SCRIPTS live in the real repo
# (jail/_common.py + arena.py use the same split). We import the jail spine tools directly.
ROOT = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else Path.home() / "OGZ-System"
CODE_ROOT = Path(os.environ["OGZ_BRAINV1_CODE_ROOT"]) if os.environ.get("OGZ_BRAINV1_CODE_ROOT") else Path.home() / "OGZ-System"

_JAIL = CODE_ROOT / "tools" / "jail"
sys.path.insert(0, str(_JAIL))
import ledger  # type: ignore   # tools/jail/ledger.py — the ONE write path
import events  # type: ignore   # tools/jail/events.py — job_events reader + STEP_MAP
import enqueue as enqueue_mod  # type: ignore  # tools/jail/enqueue.py — compute_id, validate

QUEUE = ROOT / "queue"
PENDING = QUEUE / "pending"
CLAIMED = QUEUE / "claimed"
DONE = QUEUE / "done"
PARKED = QUEUE / "parked"
LEDGERS = ROOT / "ledgers"
API_KEYS = LEDGERS / "api_keys.json"
PLAN_TIERS = LEDGERS / "plan_tiers.json"
DRAFTS_LEDGER_PATH = LEDGERS / "drafts.jsonl"
JUDGMENTS_LEDGER_PATH = LEDGERS / "judgments.jsonl"
OUTPUTS = ROOT / "outputs"
LEARNED_CANDIDATES = OUTPUTS / "learned-candidates"   # §e: compiler.py globs *.json here
CLIENTS = ROOT / "02-Platform-AI" / "Knowledge" / "brain" / "clients"
BRAIN_SCRIPTS = CODE_ROOT / "02-Platform-AI" / "Knowledge" / "brain" / "scripts"
BRAIN_DATA = ROOT / "02-Platform-AI" / "Knowledge" / "brain" / "data"
LEARNED_GATE_RULES = BRAIN_DATA / "learned_gate_rules.json"   # §i: global phrase_bans
GATES_REGISTRY = ROOT / "gates" / "REGISTRY.json"             # §i: the 5 blocking gates
CONTRACTS = ROOT / "contracts"                               # §h: contract ## 4. LEARNED lines
NEEDS_MOHAMED = CODE_ROOT / "tools" / "needs_mohamed.py"

AUDIT_LEDGER = "brain_api_audit"
DRAFTS_LEDGER = "drafts"     # §f approve: append a status=approved receipt row (registered ledger)

# §a: the brand organs served by GET /v1/brands/{handle}/profile. The product's Brand screen +
# the onboarding wizard read this set; provenance = the exact organ paths read (SPEC-012 §a).
PROFILE_ORGANS = (
    "state", "gap_report", "fingerprint", "red_lines", "cultural_overrides", "goals",
    "product_truth", "truth_pack", "taste", "gold", "media_class", "moments_bank",
    "strategy_brief", "audience_mirror", "visual_dna", "trust", "passport",
    "commercial_terms", "comm_contract", "competitor_set",
)

# §i: map each gate_id to a plain-Arabic explanation (the ONLY new copy this surface adds — the
# verdict itself is the gate's, unchanged, SPEC-012 §i). Blocks explained in Arabic, never jargon.
GATE_REASON_AR = {
    "post_audit": "بوابة تدقيق المنشور: المحتوى لا يجتاز فحص الجودة/المناسبة.",
    "caption_filter.kill_ban_check": "فلتر الكابشن: العبارة تحتوي كلمة أو نمطاً ممنوعاً.",
    "taste_guard": "حارس الذوق: الخيار يحمل نمطاً مرفوضاً في ذوق العلامة.",
    "pre_ship_gate": "بوابة ما قبل النشر: مخالفة ثقافية صريحة أو عبارة تعلّمها النظام كمرفوضة.",
    "extraction_release_gate": "بوابة إطلاق الاستخراج: معايرة النظام لم تُجَز بعد.",
}

# arena.DEFAULT_BUDGET — the documented fallback until plan_tiers.json exists (§b).
DEFAULT_BUDGET = {"max_calls": 40, "max_usd": 5.0, "max_minutes": 30}

HANDLE_RE = re.compile(r"^[a-z0-9_.-]+$")   # §2 tenant filesystem scoping (reject / \ traversal); hyphens allowed (FIX b1d3c1f804fb)

# §1.1 reason_code -> default plain-Arabic reason (the ONLY new human-facing strings, SPEC-012 §9.7).
REASON_AR = {
    "namespace_breach": "غير مسموح: هذه العلامة التجارية ليست ضمن صلاحياتك.",
    "budget_exceeded": "تم تجاوز حد الميزانية المسموح لهذه العلامة.",
    "missing_field": "ينقص حقل مطلوب في الطلب.",
    "not_found": "غير موجود.",
    "gate_block": "تم إيقاف المحتوى عند إحدى البوابات.",
    "law_conflict": "الطلب يخالف قانوناً ثابتاً في النظام.",
    "confidence_blocked": "لا يمكن تنفيذ هذا التعديل إلا بتأكيد بشري.",
    "frozen_ledger": "السجل مجمّد بسبب خلل في السلسلة — يتطلب تدخلاً بشرياً.",
    "bad_scope": "نطاق الطلب غير صالح.",
    "not_wired": "هذه الواجهة غير موصولة بعد.",
    "bad_auth": "المصادقة غير صالحة أو ناقصة.",
}


# --------------------------------------------------------------------------- envelope helpers

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_token(token: str) -> str:
    """actor_token is stored HASHED, never raw (SPEC-012 §6)."""
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()[:16]


def _ok(data: dict, confidence: str, provenance: list[str], audit_id: str | None = None):
    """§1.2 standard success envelope."""
    body = {"ok": True, "confidence": confidence, "data": data, "provenance": provenance}
    if audit_id is not None:
        body["audit_id"] = audit_id
    return JSONResponse(body, status_code=200)


def _refuse(reason_code: str, provenance: list[str], http: int = 400,
            reason_ar: str | None = None, audit_id: str | None = None):
    """§1.1 refusal object. Never a degraded 200 — always 4xx with confidence:"refused"."""
    body = {
        "ok": False,
        "confidence": "refused",
        "reason_code": reason_code,
        "reason_ar": reason_ar or REASON_AR.get(reason_code, "طلب غير صالح."),
        "provenance": provenance,
    }
    if audit_id is not None:
        body["audit_id"] = audit_id
    return JSONResponse(body, status_code=http)


def _audit(surface: str, op: str, handle: str, job_id: str, token: str, role: str,
           reason_code: str = "", detail: dict | None = None) -> str:
    """Write exactly ONE brain_api_audit line through the ONE write path (ledger.py). Returns the
    audit_id (the line's sha, the chain head after this append). A ledger failure is surfaced, not
    swallowed — but audit is inside the mutating handler, so the handler must call this and use the
    returned id even on refusals (SPEC-012 §6: refused mutating calls still audit)."""
    line = {
        "surface": surface, "op": op, "handle": handle, "job_id": job_id,
        "actor_token": _hash_token(token), "role": role,
        "reason_code": reason_code, "detail": detail or {},
    }
    stored = ledger.append(AUDIT_LEDGER, line, actor="brain_v1")
    # audit_id = sha of the exact stored line (mirrors ledger.py's chain head computation).
    canon = json.dumps(stored, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _flag_breach(handle: str, detail: str) -> None:
    """The CEO-law halt (contracts/ceo.md §3): a namespace_breach flags the brand for human
    resolution via needs_mohamed.py add. Best-effort — never blocks the 403."""
    try:
        subprocess.run(
            [sys.executable, str(NEEDS_MOHAMED), "add", "brain-v1",
             f"namespace_breach on {handle}: {detail}"],
            capture_output=True, timeout=15, cwd=str(CODE_ROOT),
        )
    except Exception:
        pass


# --------------------------------------------------------------------------- auth + tenancy

def _load_keys() -> dict:
    """Load ledgers/api_keys.json — {tokens:{token->{org,role,tier,allowed_brands[]}},
    brand_keys:{brand_key->handle}}. Missing/invalid store => empty (every call then refuses)."""
    if not API_KEYS.exists():
        return {"tokens": {}, "brand_keys": {}}
    try:
        obj = json.loads(API_KEYS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"tokens": {}, "brand_keys": {}}
    obj.setdefault("tokens", {})
    obj.setdefault("brand_keys", {})
    return obj


def _bearer(request: Request) -> str | None:
    h = request.headers.get("authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return None


class AuthCtx:
    """Resolved auth for one request. `ok` False => `refusal` is a ready JSONResponse."""
    def __init__(self, token=None, org=None, role=None, tier=None, allowed=None, brand=None):
        self.token = token
        self.org = org
        self.role = role
        self.tier = tier
        self.allowed = allowed or []
        self.brand = brand          # the resolved X-Brand handle
        self.ok = True
        self.refusal = None


def _handle_exists(handle: str) -> bool:
    """§2 tenant filesystem scoping: handle validated ^[a-z0-9_.]+$ AND confirmed on disk under
    clients/<handle>/ before any organ path is composed (same guard brain_api.py uses)."""
    if not handle or not HANDLE_RE.match(handle):
        return False
    return (CLIENTS / handle).is_dir()


def _authorize(request: Request, path_handle: str | None) -> AuthCtx:
    """Resolve Bearer org_token + X-Brand, enforce the tenancy wall.

    Returns an AuthCtx. On any failure ctx.ok is False and ctx.refusal is the JSONResponse to
    return. The tenancy wall (namespace_breach) is enforced here: X-Brand not in the token's
    allowed_brands, OR a path {handle} that differs from X-Brand => 403 namespace_breach.
    """
    ctx = AuthCtx()
    keys = _load_keys()

    token = _bearer(request)
    if not token or token not in keys["tokens"]:
        ctx.ok = False
        ctx.refusal = _refuse("bad_auth", ["ledgers/api_keys.json"], http=401)
        return ctx

    rec = keys["tokens"][token]
    ctx.token = token
    ctx.org = rec.get("org", "")
    ctx.role = rec.get("role", "")
    ctx.tier = rec.get("tier", "")
    ctx.allowed = list(rec.get("allowed_brands", []))

    brand = request.headers.get("x-brand", "").strip()
    if not brand:
        ctx.ok = False
        ctx.refusal = _refuse("missing_field", ["ledgers/api_keys.json"], http=400,
                              reason_ar="ينقص رأس X-Brand الذي يحدد العلامة.")
        return ctx

    # bad handle shape / not on disk => not_found (never compose a traversal path).
    if not _handle_exists(brand):
        ctx.ok = False
        ctx.refusal = _refuse("not_found", [f"clients/{brand}"], http=404,
                              reason_ar="العلامة المطلوبة غير موجودة.")
        return ctx

    # TENANCY WALL #1: X-Brand must be in the token's allowed_brands.
    if brand not in ctx.allowed:
        aid = _audit("auth", "namespace_breach", brand, "", token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "x_brand_not_allowed", "allowed": ctx.allowed})
        _flag_breach(brand, f"token(org={ctx.org}) requested X-Brand={brand} not in allowed")
        ctx.ok = False
        ctx.refusal = _refuse("namespace_breach", ["contracts/ceo.md", "ledgers/api_keys.json"],
                              http=403, audit_id=aid)
        return ctx

    # TENANCY WALL #2: a path {handle} must equal X-Brand (brand A can NEVER address brand B).
    if path_handle is not None and path_handle != brand:
        aid = _audit("auth", "namespace_breach", brand, "", token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "path_handle_ne_x_brand", "path_handle": path_handle})
        _flag_breach(brand, f"X-Brand={brand} tried to address path handle {path_handle}")
        ctx.ok = False
        ctx.refusal = _refuse("namespace_breach", ["contracts/ceo.md"], http=403, audit_id=aid)
        return ctx

    ctx.brand = brand
    return ctx


def _job_client(job_id: str) -> str | None:
    """Read a job's stored `client` (the brand it belongs to) from anywhere in the queue.
    Returns the handle, or None if no such job. Used for the stream tenancy check."""
    for d in (PENDING, DONE, PARKED):
        p = d / f"task_{job_id}.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("client")
            except (json.JSONDecodeError, OSError):
                return None
    # claimed/<lane>/
    if CLAIMED.is_dir():
        for lane_dir in CLAIMED.iterdir():
            p = lane_dir / f"task_{job_id}.json"
            if p.is_file():
                try:
                    return json.loads(p.read_text(encoding="utf-8")).get("client")
                except (json.JSONDecodeError, OSError):
                    return None
    return None


# --------------------------------------------------------------------------- read helpers (wave 2)

def _read_json(p: Path):
    """Read a JSON file, or None on any error (missing / malformed). Read-only, never raises."""
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _organ_path(handle: str, organ: str) -> Path:
    return CLIENTS / handle / "profile" / f"{organ}.json"


def _job_task(job_id: str) -> dict | None:
    """Read a job's FULL task JSON from anywhere in the queue (or None). Used by revise to carry the
    original request/deliverable forward into the revision job."""
    for d in (PENDING, DONE, PARKED):
        obj = _read_json(d / f"task_{job_id}.json")
        if obj is not None:
            return obj
    if CLAIMED.is_dir():
        for lane_dir in CLAIMED.iterdir():
            obj = _read_json(lane_dir / f"task_{job_id}.json")
            if obj is not None:
                return obj
    return None


def _budget_for_tier(tier: str | None) -> dict:
    """§b: the budget attached from the plan tier (ledgers/plan_tiers.json), DEFAULT_BUDGET fallback.
    The caller NEVER sets its own budget (that would let a brand buy itself more compute). The store
    nests the map under a top-level `tiers` key (alongside _spec/_note); tolerate a flat store too."""
    budget = dict(DEFAULT_BUDGET)
    if PLAN_TIERS.exists() and tier:
        store = _read_json(PLAN_TIERS)
        if isinstance(store, dict):
            tiers = store.get("tiers", store)
            cand = tiers.get(tier) if isinstance(tiers, dict) else None
            if isinstance(cand, dict) and all(k in cand for k in ("max_calls", "max_usd", "max_minutes")):
                budget = dict(cand)
    return budget


def _write_learned_candidate(handle: str, parent_job: str, new_job: str,
                             scope: str, correction: str) -> bool:
    """§e lesson capture: write the correction as a learned-candidate the compiler globs from
    outputs/learned-candidates/*.json and routes to the owning mind's contract ## 4. LEARNED next
    cycle. Schema matches compiler._validate_candidate: {brief_id, lessons[list[str]], lesson_srcs,
    role/lane for contract resolution}. Brand-scoped: the lesson names the handle so the drift wall
    keeps it to THIS brand (SPEC-012 §h do_not_aggregate). Best-effort — a write failure never
    blocks the revision (the revision job itself already carries the note); returns whether written."""
    try:
        LEARNED_CANDIDATES.mkdir(parents=True, exist_ok=True)
        lesson = f"[{handle}] client revision ({scope}): {correction.strip()}"
        candidate = {
            "brief_id": f"revise_{new_job}",
            "handle": handle,
            "role": "creative-director" if scope in ("idea", "visual", "all") else "caption-writer",
            "lane": "claude",
            "task_type": "content",
            "lessons": [lesson],
            "lesson_srcs": {lesson: f"revision:{parent_job}"},
            "ts": _now_iso(),
        }
        path = LEARNED_CANDIDATES / f"revise_{new_job}.json"
        path.write_text(json.dumps(candidate, ensure_ascii=False, indent=1), encoding="utf-8")
        return True
    except OSError:
        return False


def _profile_confidence(state: dict | None, gap: dict | None) -> str:
    """§a: confidence from the organ's own state.json / gap_report.json completeness. A brand whose
    core organs are RED (still onboarding) is `low`; some YELLOW gaps = `medium`; none = `high`."""
    reds = len((gap or {}).get("organs_red", []) or [])
    yellows = len((gap or {}).get("organs_yellow", []) or [])
    checkpoint = (state or {}).get("human_checkpoint")
    if reds or checkpoint == "pending" and (state or {}).get("state", "").startswith("newborn"):
        return "low" if reds else "medium"
    if yellows:
        return "medium"
    return "high"


def _year_map_summary(handle: str) -> dict | None:
    """§a: the year_map summary (slots/cadence) the product's Brand screen + onboarding wizard read.
    year_map.json lives at clients/<handle>/year_map.json (NOT under profile/). Returns a compact
    summary (never the full 365-slot body), or None if the brand has no year_map yet."""
    ym = _read_json(CLIENTS / handle / "year_map.json")
    if not isinstance(ym, dict):
        return None
    return {
        "total_slots": ym.get("total_slots"),
        "cadence_per_week": ym.get("cadence_per_week"),
        "anchors": ym.get("anchors"),
        "reels": ym.get("reels"),
        "window": ym.get("window"),
        "state": ym.get("state"),
        "built": ym.get("built"),
        "months": sorted((ym.get("months") or {}).keys()),
    }


def _draft_receipt(job_id: str) -> dict | None:
    """The latest `drafts` ledger receipt for a job (or None). Read-only; the drafts ledger is
    written by tools/jail/generate.py (status protected|ready) and by this API's approve surface
    (status approved) — both through the ONE write path (ledger.py). Newest line wins, so once a
    job is approved the approved row is the current receipt (Surface d serves its status)."""
    if not DRAFTS_LEDGER_PATH.exists():
        return None
    last = None
    for ln in DRAFTS_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        obj = _read_json_line(ln)
        if obj and obj.get("job_id") == job_id:
            last = obj  # newest wins (append-only, last line is latest)
    return last


def _read_json_line(ln: str):
    try:
        return json.loads(ln)
    except json.JSONDecodeError:
        return None


def _judgments_for(handle: str, job_id: str | None = None) -> list[dict]:
    """§h: recent judgments for a brand from ledgers/judgments.jsonl, tenancy-filtered by handle
    (optionally one job_id), newest first. Read-only. A row whose handle names a DIFFERENT brand is
    never returned (defense-in-depth even though the caller is already brand-scoped)."""
    if not JUDGMENTS_LEDGER_PATH.exists():
        return []
    out: list[dict] = []
    for ln in JUDGMENTS_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        obj = _read_json_line(ln)
        if not obj or obj.get("handle") != handle:
            continue
        if job_id is not None and obj.get("job_id") != job_id:
            continue
        out.append(obj)
    return list(reversed(out))


def _brand_learned_lines(handle: str) -> list[dict]:
    """§h: the contract `## 4. LEARNED` lines that name THIS brand. Contracts live in contracts/*.md;
    a LEARNED line reads `- {date: ..., lesson: "...", source_verdict_id: ...}`. We surface only the
    lines whose lesson text or source names the handle (drift wall: a brand sees only its own
    lessons, never another brand's — SPEC-012 §h do_not_aggregate). Best-effort text scan."""
    out: list[dict] = []
    if not CONTRACTS.is_dir():
        return out
    for cp in sorted(CONTRACTS.glob("*.md")):
        text = None
        try:
            text = cp.read_text(encoding="utf-8")
        except OSError:
            continue
        if "## 4. LEARNED" not in text:
            continue
        section = text.split("## 4. LEARNED", 1)[1]
        # stop at the next top-level heading
        section = re.split(r"\n## ", section, 1)[0]
        for line in section.splitlines():
            line = line.strip()
            if not line.startswith("- "):
                continue
            if handle in line:  # only lines that name this brand (drift wall)
                out.append({"contract": cp.name, "line": line[2:].strip()})
    return out


def _load_gate_registry() -> list[dict]:
    """§i: the active blocking gates from gates/REGISTRY.json (names only, no secrets)."""
    reg = _read_json(GATES_REGISTRY)
    if not isinstance(reg, dict):
        return []
    return [g for g in reg.get("gates", []) if isinstance(g, dict)]


def _job_gate_events(job_id: str, handle: str) -> list[dict]:
    """§i per-job guardrails: the gating-phase job_events for a job (subtask `gate:<id>`),
    tenancy-filtered by handle. Read-only, via the events reader (the ONE read side)."""
    return [e for e in events.read_events(job_id, handle=handle)
            if e.get("phase") == "gating" and str(e.get("subtask", "")).startswith("gate:")]


# --------------------------------------------------------------------------- app

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title="OGZ Brain /v1")


@app.get("/v1/health")
def health():
    """Unauthenticated liveness only — no brand data. Names the service + wave."""
    return JSONResponse({
        "ok": True, "confidence": "high",
        "data": {"service": "brain_v1", "port": 4150, "wave": 1},
        "provenance": ["specs/SPEC-012-brain-api.md"],
    })


# ----- Surface (b): job create ------------------------------------------------

@app.post("/v1/brands/{handle}/jobs")
async def create_job(handle: str, request: Request):
    """POST prompt -> job (SPEC-012 §b). client is FORCED to X-Brand (tenancy). budget attached
    from the plan tier (plan_tiers.json) or DEFAULT_BUDGET. Returns job_id instantly (202-style)."""
    ctx = _authorize(request, path_handle=handle)
    if not ctx.ok:
        return ctx.refusal

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    req_text = (body.get("request") or "").strip()
    deliverable = (body.get("deliverable") or "").strip()
    task_type = (body.get("task_type") or "post").strip()
    lane = (body.get("lane") or "claude").strip()

    # DELIVERABLE header law (§b): deliverable is MANDATORY.
    if not req_text or not deliverable:
        aid = _audit("job_create", "enqueue", ctx.brand, "", ctx.token, ctx.role,
                     reason_code="missing_field",
                     detail={"has_request": bool(req_text), "has_deliverable": bool(deliverable)})
        return _refuse("missing_field", ["tools/jail/enqueue.py"], http=400, audit_id=aid,
                       reason_ar="ينقص نص الطلب أو وصف المُخرَج المطلوب (deliverable).")

    # budget from the plan tier (§b) — plan_tiers.json; DEFAULT_BUDGET fallback. The caller NEVER
    # sets its own budget (one budget-resolution definition, shared with revise — Rule: no dupes).
    budget = _budget_for_tier(ctx.tier)

    # client is FORCED to X-Brand — never taken from the body (the tenancy wall).
    task = {
        "client": ctx.brand,
        "request": req_text,
        "task_type": task_type,
        "lane": lane if lane in ("claude", "codex") else "claude",
        "deliverable": deliverable,
        "budget": budget,
    }

    err = enqueue_mod.validate(task)
    if err:
        aid = _audit("job_create", "enqueue", ctx.brand, "", ctx.token, ctx.role,
                     reason_code="missing_field", detail={"validate": err})
        return _refuse("missing_field", ["tools/jail/enqueue.py"], http=400, audit_id=aid)

    job_id = enqueue_mod.compute_id(task["client"], task["request"], task["task_type"])

    # run enqueue.py as the ONE queue-write path (subprocess, so its dup-id guard + atomic write
    # are exactly the tested behavior). Map its exit-2 dup to a clean refusal (§b).
    proc = subprocess.run(
        [sys.executable, str(_JAIL / "enqueue.py"), json.dumps(task)],
        capture_output=True, text=True, cwd=str(CODE_ROOT),
        env={**os.environ, "OGZ_JAIL_ROOT": str(ROOT)},
    )
    if proc.returncode != 0:
        # duplicate-id (exit 2) -> a clean refusal (§b maps enqueue exit 2 to missing_field-ish).
        aid = _audit("job_create", "enqueue", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="missing_field",
                     detail={"enqueue_rc": proc.returncode, "stderr": proc.stderr.strip()[:200]})
        return _refuse("missing_field", ["tools/jail/enqueue.py"], http=409, audit_id=aid,
                       reason_ar="في مهمة مطابقة قيد التنفيذ بالفعل.")

    # emit the first job_events line (queued) so the stream has a phase immediately.
    try:
        events.emit(job_id, "queue", "ok", handle=ctx.brand, note=deliverable)
    except events.EventError:
        pass  # best-effort; the queue directory still gives the stream a coarse phase.

    aid = _audit("job_create", "enqueue", ctx.brand, job_id, ctx.token, ctx.role,
                 detail={"task_type": task_type, "deliverable": deliverable, "budget": budget})
    return _ok(
        {"job_id": job_id, "deliverable": deliverable, "budget": budget, "status": "queued"},
        confidence="high",
        provenance=["tools/jail/enqueue.py", f"queue/pending/task_{job_id}.json"],
        audit_id=aid,
    )


# ----- Surface (c): progress stream (job_events) ------------------------------

def _snapshot(job_id: str, handle: str) -> dict:
    """Latest-state snapshot for a job: its job_events lines (tenancy-filtered) + a coarse phase
    derived from the queue directory the task sits in (graceful degradation, never a lie)."""
    evs = events.read_events(job_id, handle=handle)
    # coarse phase from the queue directory (SPEC-012 §c: where no event line exists yet).
    coarse = None
    if (PENDING / f"task_{job_id}.json").is_file():
        coarse = "queued"
    elif (DONE / f"task_{job_id}.json").is_file():
        coarse = "done"
    elif (PARKED / f"task_{job_id}.json").is_file():
        coarse = "parked"
    elif CLAIMED.is_dir() and any((ld / f"task_{job_id}.json").is_file() for ld in CLAIMED.iterdir()):
        coarse = "claimed"
    phase = evs[-1]["phase"] if evs else coarse
    return {"job_id": job_id, "phase": phase, "coarse_phase": coarse, "events": evs}


@app.get("/v1/jobs/{job_id}/events")
async def job_events_stream(job_id: str, request: Request):
    """GET job stream (SPEC-012 §c). SSE (text/event-stream) by default; Accept: application/json
    falls back to a poll returning the latest-state snapshot. Tenancy: the job's stored client must
    equal X-Brand, else namespace_breach 403."""
    client = _job_client(job_id)
    if client is None:
        # unknown job — authorize first so we don't leak existence across tenants, then not_found.
        ctx = _authorize(request, path_handle=None)
        if not ctx.ok:
            return ctx.refusal
        return _refuse("not_found", ["ledgers/job_events.jsonl"], http=404,
                       reason_ar="لا توجد مهمة بهذا المعرّف.")

    # the job belongs to `client` — authorize the caller against THAT as the path handle so a
    # brand-A token streaming a brand-B job trips the tenancy wall (§c refusal namespace_breach).
    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal

    accept = request.headers.get("accept", "")
    wants_json = "application/json" in accept and "text/event-stream" not in accept

    if wants_json:
        snap = _snapshot(job_id, ctx.brand)
        return _ok(snap, confidence="high",
                   provenance=["ledgers/job_events.jsonl", f"queue/*/task_{job_id}.json"])

    # SSE: replay existing events, then tail for new ones until the job reaches a terminal phase
    # or the client disconnects. No extra dependency — FastAPI StreamingResponse + a generator.
    async def event_gen():
        seen = 0
        terminal = {"done", "parked"}
        # a small bounded tail loop so a test / a real client both terminate deterministically.
        for _ in range(600):  # ~ up to 600 * 0.05s poll windows as a safety ceiling
            if await request.is_disconnected():
                break
            evs = events.read_events(job_id, handle=ctx.brand)
            while seen < len(evs):
                ev = evs[seen]
                seen += 1
                yield f"data: {json.dumps(ev, ensure_ascii=False, sort_keys=True)}\n\n"
            snap_phase = evs[-1]["phase"] if evs else None
            if snap_phase in terminal:
                break
            # if the task is already terminal in the queue but emitted no terminal event, stop too.
            if (DONE / f"task_{job_id}.json").is_file() or (PARKED / f"task_{job_id}.json").is_file():
                # emit a synthetic coarse terminal marker once, then stop.
                marker = {"job_id": job_id, "phase": "done"
                          if (DONE / f"task_{job_id}.json").is_file() else "parked",
                          "subtask": "queue-terminal", "status": "ok", "coarse": True}
                yield f"data: {json.dumps(marker, ensure_ascii=False, sort_keys=True)}\n\n"
                break
            await asyncio.sleep(0.05)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ----- LATER-WAVE surfaces: loud refusal, never a silent 200 (Rule #8) --------

_NOT_WIRED = {
    # Only the genuinely-unbuilt surfaces remain here. Surface (a) GET / (e) / (f) approve / (h) /
    # (i) are WIRED (wave 2). The brand_profile PUT (intake-answer organ writes) and Postiz publish
    # are the two still-unbuilt paths that refuse LOUD via _later_wave (SPEC-012 ruling #3 / Rule #8).
    "brand_profile": "specs/SPEC-012-brain-api.md#a",   # the PUT path only (GET is wired)
    "publish": "specs/SPEC-012-brain-api.md#f",
}


def _later_wave(surface: str, request: Request, path_handle: str | None):
    """Every not-yet-built surface still enforces auth+tenancy, then refuses LOUD (not_wired).
    This keeps the tenancy wall total (a brand-B probe of an unbuilt surface still 403s) and makes
    the missing machinery honest instead of a fake 200 (SPEC-012 ruling #3 / Rule #8)."""
    ctx = _authorize(request, path_handle=path_handle)
    if not ctx.ok:
        return ctx.refusal
    return _refuse("not_wired", [_NOT_WIRED[surface]], http=501,
                   reason_ar=REASON_AR["not_wired"])


@app.get("/v1/brands/{handle}/profile")
async def brand_profile(handle: str, request: Request):
    """Surface a (SPEC-012 §a). Serve the brand's ORGANS — the product's Brand screen + the
    onboarding wizard read this. Brand-scoped + tenancy-walled (path {handle} must equal X-Brand).
    `?organ=red_lines` returns one organ. Confidence from the organ's own state.json / gap_report
    completeness. provenance = the exact organ paths read. Read-only (no audit line). Includes the
    gap_report.json presence + the year_map summary (slots/cadence). PUT is a later wave — a PUT
    here refuses LOUD (intake writes are not yet wired), never a fake 200 (Rule #8)."""
    ctx = _authorize(request, path_handle=handle)
    if not ctx.ok:
        return ctx.refusal

    one = (request.query_params.get("organ") or "").strip()
    if one:
        # a single organ (?organ=red_lines) — must be a known profile organ, else not_found.
        if one not in PROFILE_ORGANS or not HANDLE_RE.match(one.replace("_", "")):
            return _refuse("not_found", [f"clients/{ctx.brand}/profile/{one}.json"], http=404,
                           reason_ar="العضو المطلوب غير معروف.")
        obj = _read_json(_organ_path(ctx.brand, one))
        if obj is None:
            return _refuse("not_found", [f"clients/{ctx.brand}/profile/{one}.json"], http=404,
                           reason_ar="هذا العضو غير موجود لهذه العلامة.")
        return _ok({"organ": one, "value": obj}, confidence="high",
                   provenance=[f"clients/{ctx.brand}/profile/{one}.json"])

    # the full organ set (present ones only). A brand with NO organs at all => not_found (an
    # unknown/never-onboarded brand is not a fake empty 200).
    organs: dict = {}
    prov: list[str] = []
    for name in PROFILE_ORGANS:
        obj = _read_json(_organ_path(ctx.brand, name))
        if obj is not None:
            organs[name] = obj
            prov.append(f"clients/{ctx.brand}/profile/{name}.json")
    if not organs:
        return _refuse("not_found", [f"clients/{ctx.brand}/profile"], http=404,
                       reason_ar="لا توجد بيانات لهذه العلامة بعد (لم تُهيَّأ).")

    gap = organs.get("gap_report")
    state = organs.get("state")
    year_map = _year_map_summary(ctx.brand)
    if year_map is not None:
        prov.append(f"clients/{ctx.brand}/year_map.json")

    data = {
        "handle": ctx.brand,
        "organs": organs,
        "organs_present": sorted(organs.keys()),
        "gap_report_present": gap is not None,
        "gaps_open": (gap or {}).get("questions", []) if isinstance(gap, dict) else [],
        "year_map": year_map,   # slots/cadence summary (None if not built yet)
        "state": (state or {}).get("state") if isinstance(state, dict) else None,
    }
    return _ok(data, confidence=_profile_confidence(state, gap), provenance=prov)


@app.put("/v1/brands/{handle}/profile")
async def brand_profile_put(handle: str, request: Request):
    """Surface a PUT (SPEC-012 §a) — intake-answer organ writes are a LATER wave (organ_write.py +
    intake_projection.py are not wired here yet). Refuse LOUD, never a fake 200; auth+tenancy still
    enforced so a cross-brand PUT probe still 403s (the wall is total)."""
    return _later_wave("brand_profile", request, path_handle=handle)


@app.get("/v1/jobs/{job_id}/draft")
async def draft(job_id: str, request: Request):
    """Surface d (SPEC-012 §d / SPEC-014 typed content model). Returns the job's typed draft
    {type, payload, provenance, versions}, brand-scoped. Tenancy: the job's stored client must
    equal X-Brand (a brand-A token can NEVER read a brand-B draft) — namespace_breach 403 else.
    A job with no draft yet (still producing / protected-and-unwritten) => not_found 404 (Rule #8:
    never a fake empty 200)."""
    client = _job_client(job_id)
    if client is None:
        # unknown job — authorize first (don't leak existence across tenants), then not_found.
        ctx = _authorize(request, path_handle=None)
        if not ctx.ok:
            return ctx.refusal
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404,
                       reason_ar="لا توجد مهمة بهذا المعرّف.")

    # authorize the caller against the job's OWN brand as the path handle (the tenancy wall).
    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal

    receipt = _draft_receipt(job_id)
    if receipt is None:
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404,
                       reason_ar="لا توجد مسودة لهذه المهمة بعد.")

    # DEFENSE-IN-DEPTH: the receipt's handle must also match X-Brand (a drafts row is brand-stamped).
    if receipt.get("handle") not in ("", ctx.brand):
        aid = _audit("drafts", "read", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "draft_handle_ne_x_brand", "draft_handle": receipt.get("handle")})
        _flag_breach(ctx.brand, f"X-Brand={ctx.brand} tried to read draft of {receipt.get('handle')}")
        return _refuse("namespace_breach", ["contracts/ceo.md", "ledgers/drafts.jsonl"],
                       http=403, audit_id=aid)

    # resolve + load the typed draft file (draft_path is stored ROOT-relative by the worker).
    dp = Path(receipt.get("draft_path", ""))
    if not dp.is_absolute():
        dp = ROOT / dp
    if not dp.is_file():
        return _refuse("not_found", ["ledgers/drafts.jsonl", str(receipt.get("draft_path"))],
                       http=404, reason_ar="ملف المسودة غير موجود على القرص.")
    try:
        typed = json.loads(dp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _refuse("not_found", [str(receipt.get("draft_path"))], http=404,
                       reason_ar="تعذّر قراءة المسودة.")

    # FINAL tenancy check on the file body itself (never serve a draft whose body names another brand).
    if typed.get("handle") not in ("", ctx.brand):
        aid = _audit("drafts", "read", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "draft_body_handle_ne_x_brand"})
        _flag_breach(ctx.brand, f"draft body handle {typed.get('handle')} != X-Brand {ctx.brand}")
        return _refuse("namespace_breach", ["contracts/ceo.md"], http=403, audit_id=aid)

    return _ok(typed, confidence="high",
               provenance=["ledgers/drafts.jsonl", receipt.get("draft_path", ""),
                           f"clients/{ctx.brand}/profile/*.json"])


@app.post("/v1/jobs/{job_id}/revise")
async def revise(job_id: str, request: Request):
    """Surface e (SPEC-012 §e). A revision is a FRESH content job that carries the prior draft +
    the correction as context; the generation worker (task_type=content) picks it up. The prior
    version is KEPT (Surface d serves it). The correction ALSO feeds the learned path the same way
    judge kill-reasons do — a learned-candidate under outputs/learned-candidates/ that the compiler
    routes to the owning mind's contract ## 4. LEARNED next cycle (Surface h closes the loop).
    Mutating => audits exactly one line (even on refusal). Tenancy: the job's stored client must
    equal X-Brand, else namespace_breach 403. Refuse on missing draft / empty correction / breach."""
    # resolve the ORIGINAL job's brand, then authorize the caller against THAT (the tenancy wall:
    # a brand-A token can never revise a brand-B job).
    client = _job_client(job_id)
    if client is None:
        ctx = _authorize(request, path_handle=None)
        if not ctx.ok:
            return ctx.refusal
        aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"reason": "no_such_job"})
        return _refuse("not_found", ["queue/*/task_*.json"], http=404, audit_id=aid,
                       reason_ar="لا توجد مهمة بهذا المعرّف لتعديلها.")

    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    correction = (body.get("correction_ar") or body.get("correction") or "").strip()
    scope = (body.get("scope") or "all").strip()
    if scope not in ("caption", "visual", "idea", "all"):
        scope = "all"

    if not correction:
        aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="missing_field", detail={"need": "correction_ar"})
        return _refuse("missing_field", ["specs/SPEC-012-brain-api.md#e"], http=400, audit_id=aid,
                       reason_ar="ينقص نص التصحيح المطلوب (correction_ar).")

    # the job must have a draft to revise (else there is nothing to correct — not_found, Rule #8).
    parent = _draft_receipt(job_id)
    if parent is None or parent.get("handle") not in ("", ctx.brand):
        aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"has_parent_draft": parent is not None})
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404, audit_id=aid,
                       reason_ar="لا توجد مسودة سابقة لهذه المهمة لتعديلها.")

    # rebuild the ORIGINAL request text so the revision job carries continuity, then SALT it with
    # the correction so compute_id yields a DISTINCT id (a same-request revision must not collide
    # with the parent — enqueue REFUSES a duplicate id).
    orig = _job_task(job_id) or {}
    base_request = (orig.get("request") or "").strip() or f"revise draft {job_id}"
    deliverable = (orig.get("deliverable") or "").strip() or f"revision of {job_id}"
    rev_request = f"{base_request}\n\n[REVISION {scope}] {correction}"
    new_job_id = enqueue_mod.compute_id(ctx.brand, rev_request, "content")

    budget = _budget_for_tier(ctx.tier)
    task = {
        "client": ctx.brand,               # FORCED to X-Brand (tenancy)
        "request": rev_request,
        "task_type": "content",           # so the generation worker (generate.py) claims it
        "lane": "claude",
        "deliverable": deliverable,
        "budget": budget,
        "parent_job": job_id,             # provenance link to the superseded job (§e)
        "revision_note": correction,
        "revision_scope": scope,
        "provenance": {"source": "brain_v1:revise", "parent_job": job_id},
    }

    err = enqueue_mod.validate(task)
    if err:
        aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="missing_field", detail={"validate": err})
        return _refuse("missing_field", ["tools/jail/enqueue.py"], http=400, audit_id=aid)

    proc = subprocess.run(
        [sys.executable, str(_JAIL / "enqueue.py"), json.dumps(task)],
        capture_output=True, text=True, cwd=str(CODE_ROOT),
        env={**os.environ, "OGZ_JAIL_ROOT": str(ROOT)},
    )
    if proc.returncode != 0:
        aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="missing_field",
                     detail={"enqueue_rc": proc.returncode, "stderr": proc.stderr.strip()[:200]})
        return _refuse("missing_field", ["tools/jail/enqueue.py"], http=409, audit_id=aid,
                       reason_ar="في تعديل مطابق قيد التنفيذ بالفعل.")

    # lesson capture: the correction becomes a learned-candidate the compiler routes to the owning
    # mind's contract next cycle (§e — how a chat correction becomes durable memory for THIS brand).
    candidate_written = _write_learned_candidate(ctx.brand, job_id, new_job_id, scope, correction)

    # first job_events line for the revision job so its stream has a phase immediately.
    try:
        events.emit(new_job_id, "queue", "ok", handle=ctx.brand, note=f"revision:{scope}")
    except events.EventError:
        pass

    aid = _audit("revision", "revise", ctx.brand, job_id, ctx.token, ctx.role,
                 detail={"new_job_id": new_job_id, "scope": scope,
                         "correction_len": len(correction), "learned_candidate": candidate_written})
    return _ok(
        {"job_id": new_job_id, "parent_job": job_id, "supersedes_version": parent.get("status"),
         "scope": scope, "status": "queued", "learned_candidate": candidate_written},
        confidence="high",
        provenance=["tools/jail/enqueue.py", f"queue/pending/task_{new_job_id}.json",
                    f"outputs/learned-candidates/revise_{new_job_id}.json"],
        audit_id=aid,
    )


@app.post("/v1/jobs/{job_id}/approve")
async def approve(job_id: str, request: Request):
    """Surface f approve (SPEC-012 §f) — one of the ONLY human-gated writes. Marks the draft
    approved in a RECEIPTS-BEARING way: a NEW append-only `drafts` row status=approved (mirrors how
    generate.py writes protected/ready rows; the approved row becomes the current receipt Surface d
    serves — the writer's reader, Rule #6). Role-gated: owner/admin only (an agent token => refusal
    law_conflict). Mutating => audits exactly one line (even on refusal). NO publishing / external
    anything — approve = state + ledger only; publish is a later wave (POST /publish refuses loud).
    Refuse on: non-human role, no ready draft, cross-brand (namespace_breach), bad version."""
    client = _job_client(job_id)
    if client is None:
        ctx = _authorize(request, path_handle=None)
        if not ctx.ok:
            return ctx.refusal
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"reason": "no_such_job"})
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404, audit_id=aid,
                       reason_ar="لا توجد مهمة بهذا المعرّف لاعتمادها.")

    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal

    # ROLE GATE (§2 / §f): only owner/admin may approve; an agent token is refused with law_conflict.
    if ctx.role not in ("owner", "admin"):
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="law_conflict", detail={"role": ctx.role})
        return _refuse("law_conflict", ["contracts/ceo.md", "ledgers/api_keys.json"], http=403,
                       audit_id=aid, reason_ar="الاعتماد يتطلب صلاحية المالك — هذا الدور غير مخوّل.")

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    rating = body.get("rating")

    receipt = _draft_receipt(job_id)
    if receipt is None:
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"reason": "no_draft"})
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404, audit_id=aid,
                       reason_ar="لا توجد مسودة لهذه المهمة لاعتمادها.")

    # tenancy defense-in-depth: the draft row must be this brand's.
    if receipt.get("handle") not in ("", ctx.brand):
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "draft_handle_ne_x_brand", "draft_handle": receipt.get("handle")})
        _flag_breach(ctx.brand, f"X-Brand={ctx.brand} tried to approve draft of {receipt.get('handle')}")
        return _refuse("namespace_breach", ["contracts/ceo.md", "ledgers/drafts.jsonl"],
                       http=403, audit_id=aid)

    # a draft the gates KILLED (status=protected) is not approvable — refuse loud (Rule #8: never
    # let an approve resurrect a blocked draft). Only a `ready` (or already-approved) draft passes.
    if receipt.get("status") not in ("ready", "approved"):
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="gate_block", detail={"status": receipt.get("status")})
        return _refuse("gate_block", ["ledgers/drafts.jsonl"], http=409, audit_id=aid,
                       reason_ar="لا يمكن اعتماد مسودة أوقفتها إحدى البوابات.")

    # append the APPROVED receipt row — ONLY the drafts-schema keys (ledger.py refuses extras),
    # same draft_path so Surface d still resolves the file (the writer's reader).
    approval_row = {
        "job_id": job_id,
        "handle": ctx.brand,
        "type": receipt.get("type", "text"),
        "status": "approved",
        "draft_path": receipt.get("draft_path", ""),
        "gate_verdict": receipt.get("gate_verdict", ""),
        "provenance": {**(receipt.get("provenance") or {}),
                       "approved_by_role": ctx.role,
                       "rating": rating if isinstance(rating, int) else None,
                       "approved_via": "brain_v1:approve"},
    }
    try:
        ledger.append(DRAFTS_LEDGER, approval_row, actor="brain_v1")
    except ledger.LedgerError as ex:
        aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="frozen_ledger", detail={"ledger_error": str(ex)[:160]})
        return _refuse("frozen_ledger", ["ledgers/drafts.jsonl"], http=500, audit_id=aid,
                       reason_ar="تعذّر تسجيل الاعتماد في السجل.")

    aid = _audit("approve", "approve", ctx.brand, job_id, ctx.token, ctx.role,
                 detail={"version": receipt.get("status"), "rating": rating,
                         "draft_path": receipt.get("draft_path")})
    return _ok(
        {"job_id": job_id, "status": "approved", "rating": rating if isinstance(rating, int) else None,
         "draft_path": receipt.get("draft_path"),
         "published": False, "publish_note": "النشر غير موصول بعد (يتطلب ربط Postiz)."},
        confidence="high",
        provenance=["ledgers/drafts.jsonl", receipt.get("draft_path", "")],
        audit_id=aid,
    )


@app.post("/v1/jobs/{job_id}/publish")
async def publish(job_id: str, request: Request):
    """Surface f publish (SPEC-012 §f + FABLE ruling #3). Postiz has NO wire today — publish REFUSES
    LOUD (not_wired) until built; it NEVER silently succeeds (Rule #8). The attempt is audited so
    the loud failure is on the record. Auth+tenancy enforced first (a cross-brand probe still 403s)."""
    client = _job_client(job_id)
    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal
    aid = _audit("publish", "publish_attempt", ctx.brand, job_id, ctx.token, ctx.role,
                 reason_code="not_wired", detail={"reason": "postiz_unwired"})
    return _refuse("not_wired", ["specs/SPEC-012-brain-api.md#f"], http=501, audit_id=aid,
                   reason_ar="النشر غير موصول بعد.")


@app.post("/v1/brands/{handle}/render")
async def render(handle: str, request: Request):
    """Surface g (SPEC-012 §g). Wraps scripts/render_image.render(card_path) — the visual step —
    for a job's typed draft. Mutating => audits exactly one line (even on refusal). Tenancy: path
    {handle} must equal X-Brand. Body: {job_id}. render_image REFUSES loud if a live FAL ruling
    blocks spend, and STAGES the image_prompt (no spend) when no FAL key is set — either way the
    visual direction is materialized, never a fake image (Rule #8)."""
    ctx = _authorize(request, path_handle=handle)
    if not ctx.ok:
        return ctx.refusal

    try:
        body = await request.json()
    except Exception:
        body = {}
    job_id = (body.get("job_id") or "").strip() if isinstance(body, dict) else ""
    if not job_id:
        aid = _audit("render", "render", ctx.brand, "", ctx.token, ctx.role,
                     reason_code="missing_field", detail={"need": "job_id"})
        return _refuse("missing_field", ["scripts/render_image.py"], http=400, audit_id=aid,
                       reason_ar="ينقص معرّف المهمة (job_id) المطلوب للتصميم.")

    # the job must belong to THIS brand (tenancy) and have a draft to render.
    jclient = _job_client(job_id)
    if jclient is not None and jclient != ctx.brand:
        aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="namespace_breach",
                     detail={"reason": "render_job_of_other_brand", "job_client": jclient})
        _flag_breach(ctx.brand, f"X-Brand={ctx.brand} tried to render job of {jclient}")
        return _refuse("namespace_breach", ["contracts/ceo.md"], http=403, audit_id=aid)

    receipt = _draft_receipt(job_id)
    if receipt is None or receipt.get("handle") not in ("", ctx.brand):
        aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"has_receipt": receipt is not None})
        return _refuse("not_found", ["ledgers/drafts.jsonl"], http=404, audit_id=aid,
                       reason_ar="لا توجد مسودة لهذه المهمة للتصميم عليها.")

    dp = Path(receipt.get("draft_path", ""))
    if not dp.is_absolute():
        dp = ROOT / dp
    try:
        typed = json.loads(dp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_found", detail={"draft_path": str(receipt.get("draft_path"))})
        return _refuse("not_found", [str(receipt.get("draft_path"))], http=404, audit_id=aid,
                       reason_ar="تعذّر قراءة المسودة للتصميم.")

    # build the card render_image expects (captions + visual) from the typed draft, write it under
    # the brand's posts dir so render_image derives the handle from path.parent.parent (tenancy-safe),
    # then wrap render(card_path). No fal spend by default (stages image_prompt).
    payload = typed.get("payload") or {}
    card = {
        "handle": ctx.brand, "date": payload.get("date"),
        "captions": typed.get("versions") or ([payload.get("caption")] if payload.get("caption") else []),
        "idea": payload.get("idea") or {},
        "visual": {k: v for k, v in (payload.get("visual") or {}).items() if v is not None},
        "provenance": typed.get("provenance") or {},
    }
    posts_dir = CLIENTS / ctx.brand / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    card_path = posts_dir / f"_v1render_{job_id}.json"
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

    sys.path.insert(0, str(BRAIN_SCRIPTS))
    try:
        import render_image  # type: ignore
        image_url = render_image.render(str(card_path))
    except SystemExit as se:
        # render_image REFUSES (live no_fal_photos ruling / budget guard) via sys.exit — surface it
        # as a loud gate_block, not a crash, and audit it.
        aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="gate_block", detail={"render_refused": str(se)[:160]})
        return _refuse("gate_block", ["scripts/render_image.py"], http=409, audit_id=aid,
                       reason_ar="التصميم موقوف بأمر تشغيلي حالي (لا صور حتى إذن محمد).")
    except Exception as ex:
        aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                     reason_code="not_wired", detail={"render_error": str(ex)[:160]})
        return _refuse("not_wired", ["scripts/render_image.py"], http=500, audit_id=aid,
                       reason_ar="تعذّر تنفيذ خطوة التصميم.")

    # re-read the card render_image just enriched (image_prompt staged, or image_url/blocked set).
    try:
        enriched = json.loads(card_path.read_text(encoding="utf-8")).get("visual", {})
    except (OSError, json.JSONDecodeError):
        enriched = {}
    staged = image_url is None
    aid = _audit("render", "render", ctx.brand, job_id, ctx.token, ctx.role,
                 detail={"staged": staged, "image_url": image_url,
                         "blocked": bool((enriched.get("ai_imagery") or {}).get("blocked"))})
    return _ok(
        {"job_id": job_id, "image_url": image_url,
         "staged": staged,  # True = prompt staged (no fal key / spend), not a live image
         "image_prompt": enriched.get("image_prompt"),
         "ai_imagery": enriched.get("ai_imagery")},
        confidence="high",
        provenance=["scripts/render_image.py", str(card_path.relative_to(ROOT))
                    if str(card_path).startswith(str(ROOT)) else str(card_path)],
        audit_id=aid,
    )


@app.get("/v1/brands/{handle}/memory")
async def memory(handle: str, request: Request):
    """Surface h (SPEC-012 §h introspection endpoint, read-only). The brand's LEARNED STATE:
    recent judgments (ledgers/judgments.jsonl filtered by handle), the contract ## 4. LEARNED lines
    scoped to this brand, a taste summary (kills + client kill_patterns), and the gold count. Brand-
    scoped + tenancy-walled (path {handle} must equal X-Brand). provenance = the ledgers/organs/
    contracts read. Read-only => NO audit line. DRIFT WALL: only THIS brand's lessons are returned
    (never another brand's — do_not_aggregate)."""
    ctx = _authorize(request, path_handle=handle)
    if not ctx.ok:
        return ctx.refusal

    judgments = _judgments_for(ctx.brand)
    recent = [{
        "job_id": j.get("job_id"), "verdict": j.get("verdict"), "overall": j.get("overall"),
        "reasons": j.get("reasons", [])[:6], "ts": j.get("ts"),
    } for j in judgments[:10]]
    verdict_counts: dict = {}
    for j in judgments:
        v = str(j.get("verdict", "?"))
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    learned = _brand_learned_lines(ctx.brand)

    taste = _read_json(_organ_path(ctx.brand, "taste")) or {}
    kill_patterns = taste.get("kill_patterns", []) if isinstance(taste, dict) else []
    taste_summary = {
        "inherited_kills": len(taste.get("kills", []) or []) if isinstance(taste, dict) else 0,
        "client_patterns": len(kill_patterns),
        "patterns": [{"pattern": p.get("pattern"), "confirmer": p.get("confirmer"),
                      "date": p.get("date")} for p in kill_patterns if isinstance(p, dict)],
    }

    gold = _read_json(_organ_path(ctx.brand, "gold")) or {}
    gold_entries = gold.get("gold", []) if isinstance(gold, dict) else []

    prov = ["ledgers/judgments.jsonl", f"clients/{ctx.brand}/profile/taste.json",
            f"clients/{ctx.brand}/profile/gold.json"]
    if learned:
        prov += sorted({f"contracts/{l['contract']}" for l in learned})

    # confidence: a brand with real judged history + learned lines is `high`; only organs = `medium`.
    conf = "high" if judgments else ("medium" if (learned or gold_entries) else "low")
    data = {
        "handle": ctx.brand,
        "recent_judgments": recent,
        "judgment_counts": verdict_counts,
        "judgment_total": len(judgments),
        "learned_lines": learned,
        "taste_summary": taste_summary,
        "gold_count": len(gold_entries),
    }
    return _ok(data, confidence=conf, provenance=prov)


@app.get("/v1/brands/{handle}/guardrails")
async def brand_guardrails(handle: str, request: Request):
    """Surface i — the ACTIVE guardrail set that protects this brand, so the product can SHOW what
    protects it (GOAL-3). phrase_bans COUNT (global, data/learned_gate_rules.json) + this brand's
    cultural red-line CATEGORIES (clients/<h>/profile/cultural_overrides.json keys) + the gate
    registry list (names only, no secrets — gates/REGISTRY.json). Brand-scoped so the tenancy wall
    covers it (a brand's own red-line categories are brand data). Read-only => NO audit line."""
    ctx = _authorize(request, path_handle=handle)
    if not ctx.ok:
        return ctx.refusal

    rules = _read_json(LEARNED_GATE_RULES) or {}
    phrase_bans = rules.get("phrase_bans", []) if isinstance(rules, dict) else []

    overrides = _read_json(_organ_path(ctx.brand, "cultural_overrides")) or {}
    categories = sorted(k for k in overrides.keys() if not k.startswith("_")) if isinstance(overrides, dict) else []

    red_lines_obj = _read_json(_organ_path(ctx.brand, "red_lines")) or {}
    red_line_count = len(red_lines_obj.get("lines", []) or []) if isinstance(red_lines_obj, dict) else 0

    gates = [{"gate_id": g.get("gate_id"), "blocking": bool(g.get("blocking")),
              "reason_ar": GATE_REASON_AR.get(g.get("gate_id", ""), "بوابة حماية.")}
             for g in _load_gate_registry()]

    data = {
        "handle": ctx.brand,
        "phrase_bans_count": len(phrase_bans),
        "cultural_red_line_categories": categories,
        "red_line_rules_count": red_line_count,
        "gates": gates,
        "gate_count": len(gates),
    }
    prov = ["gates/REGISTRY.json", "02-Platform-AI/Knowledge/brain/data/learned_gate_rules.json",
            f"clients/{ctx.brand}/profile/cultural_overrides.json",
            f"clients/{ctx.brand}/profile/red_lines.json"]
    return _ok(data, confidence="high", provenance=prov)


@app.get("/v1/jobs/{job_id}/guardrails")
async def guardrails(job_id: str, request: Request):
    """Surface i per-job (SPEC-012 §i). Read-only: the gate verdicts for a job as
    {passed:[gate_id], blocked:[{gate_id, reason_ar}]} — blocks explained in plain Arabic (the ONLY
    new copy; the verdict is the gate's, unchanged). Built from the job's gating-phase job_events.
    A `gate_block` is NOT a refusal of this read call — it is the CONTENT (ok:true, data.blocked
    populated). Tenancy: the job's stored client must equal X-Brand. Refuse `not_found` for an
    unknown job OR a job that has NOT reached the gating phase yet (no gate data => Rule #8: never
    return an empty {passed,blocked} that reads as 'all clear' when the truth is 'not gated yet')."""
    client = _job_client(job_id)
    if client is None:
        ctx = _authorize(request, path_handle=None)
        if not ctx.ok:
            return ctx.refusal
        return _refuse("not_found", ["ledgers/job_events.jsonl"], http=404,
                       reason_ar="لا توجد مهمة بهذا المعرّف.")

    ctx = _authorize(request, path_handle=client)
    if not ctx.ok:
        return ctx.refusal

    gate_events = _job_gate_events(job_id, ctx.brand)
    if not gate_events:
        # no gating events yet — the job hasn't been gated (still producing / queued). Refuse LOUD
        # rather than return a fake all-clear (Rule #8: absence of data is not a pass).
        return _refuse("not_found", ["ledgers/job_events.jsonl"], http=404,
                       reason_ar="لم تُفحَص هذه المهمة عبر البوابات بعد.")

    passed: list[str] = []
    blocked: list[dict] = []
    seen: set = set()
    for e in gate_events:
        gid = str(e.get("subtask", ""))[len("gate:"):]
        if gid in seen:
            continue
        seen.add(gid)
        if e.get("status") == "blocked":
            blocked.append({"gate_id": gid,
                            "reason_ar": GATE_REASON_AR.get(gid, "بوابة حماية أوقفت المحتوى."),
                            "detail": e.get("note")})
        else:
            passed.append(gid)

    data = {"job_id": job_id, "passed": passed, "blocked": blocked,
            "all_clear": len(blocked) == 0}
    return _ok(data, confidence="high", provenance=["ledgers/job_events.jsonl"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=4150, log_level="warning")
