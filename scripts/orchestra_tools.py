#!/usr/bin/env python3
"""ORCHESTRA TOOLS (June 28, 2026) — read-only FILE EYES for RABIE + DeepSeek (orchestra audit B2).

Mohamed: "deepseek sees only facts." RABIE and DeepSeek used to see only Claude's prose → Claude was a
single point of failure (he could err and they couldn't catch it). This gives them their OWN read-only
eyes — grep / read_file / list_dir / find_file — via an OpenAI-style tool-call loop, so they verify
claims against the real code themselves.

DESIGNED WITH DEEPSEEK (it designed its own rails). Honored:
- TOOLS: grep, read_file, list_dir, find_file. NOT git log/blame (leaks keys in messages), NOT run-script.
- SCOPE: ONLY the ogz-knowledge repo + RABIE_MIND.md. READ-ONLY. No writes, no execution.
- SECRET SCRUBBER (mandatory, not just a denylist): every returned byte is scrubbed — sk-/apify_/AKIA/
  ghp_/xox.-/BEGIN PRIVATE KEY/Bearer → [REDACTED]. Path denylist too (*env*/*key*/*secret*/*.pem/id_*/.ssh).
- BUDGET: 12 tool-calls + 8KB per turn. Tool error → fed back as an observation (model adapts), not a crash.
- Hallucination guard (DeepSeek's #1 risk): raw tool outputs are logged so the same slice can be re-fetched
  if RABIE and DeepSeek disagree (the two-reader rule — a process guard, applied when both run via panel).
"""
import json
import os
import re
import subprocess
from pathlib import Path

REPO = Path("/Users/abarihm/Desktop/ogz-knowledge")
EXTRA_OK = [Path("/Users/abarihm/agents/rabie/RABIE_MIND.md")]
MAX_CALLS = 12
BYTE_BUDGET = 8192

# path denylist — never even open these (secrets / keys / identities)
DENY_PATH = re.compile(r"(\.abraham_env|/\.ssh/|/\.aws/|env|key|secret|credential|token|\.pem$|/id_[a-z]+$|\.p12$)", re.I)
# content scrubber — redact any secret-looking match in returned bytes
SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{18,}|apify_[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|"
    r"xox[bpsa]-[A-Za-z0-9\-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._\-]{16,})")


def _scrub(text: str) -> str:
    return SECRET_RE.sub("[REDACTED]", text or "")


def _safe(path_str: str) -> Path:
    """Resolve a path; reject anything outside scope or matching the deny list."""
    p = (REPO / path_str).resolve() if not os.path.isabs(path_str) else Path(path_str).resolve()
    if DENY_PATH.search(str(p)):
        raise PermissionError(f"denied (secret/identity path): {path_str}")
    if not (str(p).startswith(str(REPO)) or p in [e.resolve() for e in EXTRA_OK]):
        raise PermissionError(f"out of scope (read-only repo only): {path_str}")
    return p


# default grep scope = CODE + DOCS + data (shift 4 fix: scripts-only blinded DeepSeek to docs/ → it
# falsely declared CONNECT_THE_BRAIN.md "missing". The eyes must see the whole repo, not just scripts/.)
DEFAULT_GLOBS = ["scripts/**/*.py", "docs/**/*.md", "docs/**/*.txt", "*.md", "data/*.json", "*.json"]


# ── the tools (read-only) ────────────────────────────────────────────────────
def grep(pattern: str, path_glob: str = "", max_lines: int = 40) -> str:
    globs = [path_glob] if path_glob else DEFAULT_GLOBS
    files = []
    for g in globs:
        _safe(g.split("*")[0] or ".")  # scope-check the root of each glob
        files += [f for f in REPO.glob(g) if f.is_file() and not DENY_PATH.search(str(f))]
    files = sorted(set(files))
    out = []
    rx = re.compile(pattern)
    for f in files:
        try:
            for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if rx.search(ln):
                    out.append(f"{f.relative_to(REPO)}:{i}: {ln.strip()[:160]}")
                    if len(out) >= max_lines:
                        out.append("…[max_lines reached]"); return _scrub("\n".join(out))
        except Exception:
            continue
    return _scrub("\n".join(out)) if out else "(no matches)"


def read_file(path: str, start: int = 1, end: int = 120) -> str:
    p = _safe(path)
    lines = p.read_text(errors="ignore").splitlines()
    end = min(end, start + 200)  # hard cap span
    slice_ = lines[max(0, start - 1):end]
    return _scrub("\n".join(f"{start+i}\t{l}" for i, l in enumerate(slice_)))


def list_dir(path: str = ".") -> str:
    p = _safe(path)
    names = sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()
                   if not DENY_PATH.search(str(x)))
    return _scrub("\n".join(names[:200]))


def find_file(pattern: str, root: str = "scripts/") -> str:
    base = _safe(root)
    hits = [str(f.relative_to(REPO)) for f in base.rglob(pattern)
            if f.is_file() and not DENY_PATH.search(str(f))][:50]
    return _scrub("\n".join(hits)) if hits else "(no files)"


_DISPATCH = {"grep": grep, "read_file": read_file, "list_dir": list_dir, "find_file": find_file}

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "grep", "description": "Search the ogz-knowledge repo for a regex; returns file:line matches. Default scope covers CODE + DOCS (scripts/*.py, docs/*.md, root *.md, data/*.json) — so you CAN find a doc like CONNECT_THE_BRAIN.md without a path_glob.",
     "parameters": {"type": "object", "properties": {"pattern": {"type": "string"},
        "path_glob": {"type": "string", "description": "optional; e.g. 'docs/**/*.md' or '**/*' to widen. Empty = code+docs default."}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a line slice of a repo file (read-only).",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"},
        "start": {"type": "integer"}, "end": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_dir", "description": "List names in a repo directory.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "find_file", "description": "Find files by glob under a repo root.",
     "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "root": {"type": "string"}}, "required": ["pattern"]}}},
]

TOOL_LOG = []   # raw outputs (the two-reader buffer; lets us re-fetch a disputed slice)


def _post(url, body, headers, timeout=120):
    import urllib.request
    rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    return json.loads(urllib.request.urlopen(rq, timeout=timeout).read())


def run_with_tools(messages, model, key, base_url, system=None, max_tokens=1500, temperature=0.3):
    """OpenAI-style tool-call loop (works for GPT-4o AND deepseek — both OpenAI-compatible). The model
    can grep/read the real repo to VERIFY before answering. Read-only, scrubbed, budgeted. Returns text."""
    msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    used = 0
    for _ in range(MAX_CALLS):
        body = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": msgs, "tools": TOOL_SCHEMAS, "tool_choice": "auto"}
        out = _post(base_url, body, headers)
        m = out["choices"][0]["message"]
        msgs.append(m)
        tcs = m.get("tool_calls")
        if not tcs:
            return m.get("content", "") or ""
        for tc in tcs:
            name = (tc.get("function") or {}).get("name", "")
            try:
                args = json.loads((tc["function"].get("arguments") or "{}"))
                res = _DISPATCH[name](**args) if name in _DISPATCH else f"TOOL ERROR: unknown tool {name}"
            except Exception as e:
                res = f"TOOL ERROR: {type(e).__name__}: {str(e)[:120]}"   # fed back as observation
            if used + len(res) > BYTE_BUDGET:
                res = res[:max(0, BYTE_BUDGET - used)] + "\n[BYTE BUDGET REACHED — answer with what you have]"
            used += len(res)
            TOOL_LOG.append({"tool": name, "args": tc["function"].get("arguments"), "out": res})
            msgs.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": res})
        if used >= BYTE_BUDGET:
            break
    # budget/calls exhausted → force a final answer
    msgs.append({"role": "user", "content": "Tool budget reached. Give your FINAL answer now, citing what you verified."})
    out = _post(base_url, {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": msgs}, headers)
    return out["choices"][0]["message"].get("content", "") or ""


if __name__ == "__main__":   # self-test the tools (no model)
    print("grep PREFILL_KEYS:\n", grep("PREFILL_KEYS", "scripts/export_prefill.py")[:300])
    print("\nfind export_*:\n", find_file("export_*.py"))
    print("\nDENY check (~/.abraham_env):")
    try:
        read_file(os.path.expanduser("~/.abraham_env"))
    except Exception as e:
        print("  ✅ blocked:", e)
