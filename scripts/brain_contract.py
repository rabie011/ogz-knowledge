#!/usr/bin/env python3
"""BRAIN REQUEST CONTRACT (June 28, 2026) — the explicit accept/reject spec for the 3 brain_api endpoints.

Beat 9 (RABIE + DeepSeek pick). DeepSeek verified the gap: brain_api.py validated only field *truthiness*
(handle/product/chain non-empty) — a dev sending handle=123 (int), chain=" " (whitespace), or reach="lots"
(string) got a silent failure or an opaque 500 with no contract. This module is the contract: each
validator returns a clean, typed dict OR raises ContractError(field, message) → brain_api returns 400 with
the exact field error. Plain Python, NO pydantic dependency (the bridge runs on the stock interpreter).

This is the dev-facing answer to "what exactly does the brain accept?" — not "it works", but "here is the
shape, here is what I reject and why." Rule #6 (consumer law): brain_api is the consumer, wired same cycle.
"""
import re

HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{2,40}$")     # a client handle dir name
CHAIN_RE = re.compile(r"^[A-Za-z0-9_-]{2,16}$")        # e.g. G03, TF01, openclaw chain ids
_ENG_KEYS = ("likes", "saves", "comments", "shares", "reach")


class ContractError(ValueError):
    """A request that violates the contract. Carries the offending field + a dev-readable message."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _req_str(data, key):
    v = data.get(key)
    if v is None:
        raise ContractError(key, "required")
    if not isinstance(v, str):
        raise ContractError(key, f"must be a string, got {type(v).__name__}")
    v = v.strip()
    if not v:
        raise ContractError(key, "must be a non-empty string")
    return v


def _opt_str(data, key, default):
    v = data.get(key, default)
    if v is None:
        return default
    if not isinstance(v, str):
        raise ContractError(key, f"must be a string, got {type(v).__name__}")
    return v.strip() or default


def _opt_bool(data, key, default):
    v = data.get(key, default)
    if not isinstance(v, bool):
        raise ContractError(key, f"must be a boolean, got {type(v).__name__}")
    return v


def validate_extract(data):
    """GET /extract — {handle}. Returns {handle}."""
    h = _req_str(data, "handle")
    if not HANDLE_RE.match(h):
        raise ContractError("handle", "must be 2-40 chars of [A-Za-z0-9._-]")
    return {"handle": h}


def validate_produce(data):
    """POST /produce — {handle, product, chain, occasion?, produce?, regenerate?}. Returns the clean dict."""
    h = _req_str(data, "handle")
    if not HANDLE_RE.match(h):
        raise ContractError("handle", "must be 2-40 chars of [A-Za-z0-9._-]")
    product = _req_str(data, "product")
    chain = _req_str(data, "chain")
    if not CHAIN_RE.match(chain):
        raise ContractError("chain", "must be 2-16 chars of [A-Za-z0-9_-] (e.g. G03, TF01)")
    return {
        "handle": h, "product": product, "chain": chain,
        "occasion": _opt_str(data, "occasion", "everyday"),
        "produce": _opt_bool(data, "produce", True),
        "regenerate": _opt_bool(data, "regenerate", False),
    }


def validate_performance(data):
    """POST /performance — {post_id, likes?, saves?, comments?, shares?, reach}. Returns {post_id, engagement}.

    Engagement counts must be non-negative ints (JSON numbers); reach must be > 0 (a z-score needs a
    denominator). Missing optional counts default to 0 — but a present count of the wrong type is rejected."""
    pid = _req_str(data, "post_id")
    eng = {}
    for k in _ENG_KEYS:
        if k not in data or data[k] is None:
            eng[k] = 0
            continue
        v = data[k]
        if isinstance(v, bool) or not isinstance(v, int):   # bool is an int subclass — reject it explicitly
            raise ContractError(k, f"must be a non-negative integer, got {type(v).__name__}")
        if v < 0:
            raise ContractError(k, "must be non-negative")
        eng[k] = v
    if eng["reach"] <= 0:
        raise ContractError("reach", "must be a positive integer (engagement_rate divides by reach)")
    return {"post_id": pid, "engagement": eng}


if __name__ == "__main__":
    # smoke: good + bad cases per endpoint
    import json
    cases = [
        ("extract good", validate_extract, {"handle": "albaik"}),
        ("produce good", validate_produce, {"handle": "albaik", "product": "بروست", "chain": "G03"}),
        ("perf good", validate_performance, {"post_id": "a__b__G03", "likes": 10, "reach": 1000}),
    ]
    for name, fn, d in cases:
        print(f"✅ {name}: {json.dumps(fn(d), ensure_ascii=False)}")
    bad = [
        ("extract int handle", validate_extract, {"handle": 123}),
        ("produce blank chain", validate_produce, {"handle": "a", "product": "p", "chain": "  "}),
        ("perf string reach", validate_performance, {"post_id": "x", "reach": "lots"}),
        ("perf zero reach", validate_performance, {"post_id": "x", "reach": 0}),
    ]
    for name, fn, d in bad:
        try:
            fn(d)
            print(f"🔴 {name}: SHOULD HAVE RAISED")
        except ContractError as e:
            print(f"✅ {name} → 400 {e.field}: {e.message}")
