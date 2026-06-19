"""Bedrock OpenAI client factory — the ONE place a client is born.

Why this exists (B258, June 19 2026): 30+ callers each constructed
`openai.OpenAI(...)` by hand with inconsistent or ZERO timeout. Since Anthropic
is dry, OpenAI is the only funded LLM — every producing path runs through it, so
a single un-timed-out call silently stalls the whole orchestra (the one failure
that hides all others). The fix is at bedrock, not per-caller: build the client
HERE with a hard timeout + bounded retries baked in.

Drop-in for the legacy pattern:
    api_key = load_key()
    client = openai.OpenAI(api_key=api_key)
becomes:
    from lib.openai_client import make_client
    client = make_client(api_key)            # api_key optional — auto-loaded
"""
import os
from pathlib import Path

# Defaults (Rule #5 amendment "make it hard to break"): every call bounded.
DEFAULT_TIMEOUT = 90.0   # seconds — a hung socket can never stall the orchestra
DEFAULT_MAX_RETRIES = 2  # bounded retry on transient 5xx / connection errors


def load_openai_key() -> str:
    """Read OPENAI_API_KEY from ~/.abraham_env (shell does not auto-source it),
    falling back to the process environment. Mirrors the legacy per-caller helper."""
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")


def make_client(api_key: str = None, timeout: float = DEFAULT_TIMEOUT,
                max_retries: int = DEFAULT_MAX_RETRIES):
    """Return an OpenAI client with timeout + bounded retries ALWAYS set.

    api_key: pass an already-loaded key for drop-in compatibility; if None, the
             key is loaded from ~/.abraham_env. Empty/missing key raises — a
             producing path must never silently run keyless (Rule #8 refuse,
             don't warn)."""
    from openai import OpenAI  # imported lazily so the module loads without the SDK
    key = api_key or load_openai_key()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY missing — set it in ~/.abraham_env (no client can be born keyless)")
    return OpenAI(api_key=key, timeout=timeout, max_retries=max_retries)


def make_async_client(api_key: str = None, timeout: float = DEFAULT_TIMEOUT,
                      max_retries: int = DEFAULT_MAX_RETRIES):
    """Async twin of make_client (B258 follow-up, June 19 2026). The async producing
    path (multi_llm_collector) was the one live caller the sync factory could not cover;
    an un-timed-out AsyncOpenAI hangs the gather() and stalls the whole collection run.

    A caller that runs its OWN retry loop should pass max_retries=0 so the SDK does not
    double-retry on top of it — but the timeout is ALWAYS baked in regardless."""
    from openai import AsyncOpenAI  # lazy import — module loads without the SDK
    key = api_key or load_openai_key()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY missing — set it in ~/.abraham_env (no client can be born keyless)")
    return AsyncOpenAI(api_key=key, timeout=timeout, max_retries=max_retries)
