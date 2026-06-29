#!/usr/bin/env python3
"""BRAIN RATE LIMIT (June 29, 2026) — a standalone, dependency-free per-client token-bucket limiter.

DeepSeek #4 (orchestra consult): today the ONLY backpressure on the brain bridge is the global produce
queue (`brain_api._Q`, maxsize=4). That is a SHARED resource — one noisy client hammering /produce fills
the queue and STARVES every other client (no fairness primitive). The missing piece is a per-CLIENT bucket
so each handle gets its own allowance and a rude neighbour can't eat the whole pipe.

This module builds that primitive STANDALONE, this step only — it is NOT wired into brain_api.py here
(no existing-file edits; a later session imports it in one line). Built in isolation WITH a biting
assert-based self-test (DeepSeek flagged that __main__ blocks that only print prove nothing) so the
fairness primitive is verifiable on its own before it ever touches the live bridge.

Algorithm: classic lazy-refill token bucket per key.
- A bucket starts FULL (`capacity` tokens). Each allowed request spends `n` tokens.
- Tokens refill continuously at `refill_per_sec`, computed lazily on each call from a monotonic clock
  (time.monotonic — immune to wall-clock/NTP jumps), capped at `capacity` (no unbounded accrual).
- A request is allowed iff the (refilled) bucket holds >= n tokens; otherwise it is denied and NO tokens
  are spent (a denied request must not deplete the bucket further).
- `retry_after(key)` returns the seconds until the bucket holds >= 1 token, for the API to surface in a
  Retry-After header — mirroring the existing /produce 429 shape in brain_api.do_POST (which returns
  `retry_after_seconds` + a `Retry-After` header). 0.0 when a token is already available.

Keys are the CLIENT HANDLE (or, when auth is on, the bearer token) — the natural per-tenant identity.

Intended wiring point (NOT performed here): at the TOP of `brain_api.Handler.do_POST` for path "/produce",
after auth + contract validation, do a per-key check:

    limiter = brain_ratelimit.default_limiter()        # module-level singleton, created once
    key = data["handle"]                               # the validated client handle
    if not limiter.allow(key):
        ra = limiter.retry_after(key)
        return self._send(429, {"ok": False, "error": "rate limit — slow down",
                                "retry_after_seconds": round(ra, 1)},
                          headers={"Retry-After": int(ra) + 1})

That single check gives each client its own fair share BEFORE the shared queue is touched. This module does
NOT do it — it only provides the primitive.

Thread-safety: every bucket guards its own state with a threading.Lock; the RateLimiter guards its key→bucket
registry with a separate lock (so concurrent first-touches of distinct keys can't race a dict insert). The
brain bridge is a ThreadingHTTPServer, so concurrency safety is mandatory, not optional.

Run:  python3 scripts/brain_ratelimit.py     # runs the assert-based self-test; exits non-zero on any failure
"""
import threading
import time

# ── module-level defaults ────────────────────────────────────────────────────────────────────────
# Conservative starting allowance per client. /produce is SLOW + money-costing (caption gen + 2 judges,
# 30-180s) and serialized by the single HUMAIN browser — a client does not legitimately need to fire many
# in quick succession. CAPACITY = small burst; REFILL_PER_SEC = a steady ~1 request / 10s sustained rate.
# These are deliberately loose defaults; the caller can pass its own when constructing a RateLimiter.
CAPACITY = 5.0            # max burst of requests a single key may make back-to-back
REFILL_PER_SEC = 0.1      # sustained rate: one fresh token every 10 seconds


class TokenBucket:
    """A single thread-safe token bucket with monotonic-clock lazy refill.

    capacity        — max tokens the bucket can hold (the burst size); also the starting fill.
    refill_per_sec  — tokens added per second, capped at capacity.
    """

    def __init__(self, capacity: float, refill_per_sec: float):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if refill_per_sec <= 0:
            raise ValueError("refill_per_sec must be > 0")
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self._tokens = float(capacity)          # start full
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill_locked(self):
        """Add the tokens accrued since the last touch, capped at capacity. Caller must hold the lock."""
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_sec)
            self._last = now

    def allow(self, n: float = 1) -> bool:
        """Try to spend n tokens. Returns True (and spends them) if available, else False (spends nothing)."""
        with self._lock:
            self._refill_locked()
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def retry_after(self, n: float = 1) -> float:
        """Seconds until the bucket holds >= n tokens. 0.0 if already available."""
        with self._lock:
            self._refill_locked()
            deficit = n - self._tokens
            if deficit <= 0:
                return 0.0
            return deficit / self.refill_per_sec


class RateLimiter:
    """A registry of per-key TokenBuckets sharing one (capacity, refill_per_sec) policy.

    Each distinct key gets its own bucket on first touch, so clients are isolated from one another.
    """

    def __init__(self, capacity: float = CAPACITY, refill_per_sec: float = REFILL_PER_SEC):
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self._buckets = {}                      # key → TokenBucket
        self._lock = threading.Lock()

    def _bucket(self, key) -> TokenBucket:
        """Fetch (or lazily create) the bucket for key, guarding the registry against concurrent inserts."""
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = TokenBucket(self.capacity, self.refill_per_sec)
                self._buckets[key] = b
            return b

    def allow(self, key, n: float = 1) -> bool:
        """True iff this key may spend n tokens right now (spends them); False otherwise (spends nothing)."""
        return self._bucket(key).allow(n)

    def retry_after(self, key) -> float:
        """Seconds until this key has a token again — for a Retry-After header (mirrors /produce 429)."""
        return self._bucket(key).retry_after()


# ── default singleton factory ────────────────────────────────────────────────────────────────────
_DEFAULT = None
_DEFAULT_LOCK = threading.Lock()


def default_limiter() -> RateLimiter:
    """The process-wide RateLimiter (module-level defaults). Created once, returned thereafter."""
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = RateLimiter(CAPACITY, REFILL_PER_SEC)
    return _DEFAULT


# ── biting self-test (Rule #8: REFUSE, DON'T WARN — any failed assert exits non-zero) ──────────────
def _selftest():
    # 1. A burst of exactly `capacity` is allowed, then the very next is denied.
    cap = 5
    b = TokenBucket(capacity=cap, refill_per_sec=0.001)   # refill ~off for the duration of this test
    grants = sum(1 for _ in range(cap) if b.allow())
    assert grants == cap, f"burst: expected {cap} grants, got {grants}"
    assert b.allow() is False, "burst: the (capacity+1)th request must be denied"

    # 2. Two distinct keys are independent — draining one does not affect the other.
    rl = RateLimiter(capacity=3, refill_per_sec=0.001)
    assert all(rl.allow("clientA") for _ in range(3)), "key-isolation: clientA should get its full burst"
    assert rl.allow("clientA") is False, "key-isolation: clientA must now be exhausted"
    assert rl.allow("clientB") is True, "key-isolation: clientB must be unaffected by clientA"

    # 3. Refill restores a token after sleeping the refill interval.
    interval = 0.05
    rb = TokenBucket(capacity=1, refill_per_sec=1.0 / interval)   # one token per `interval` seconds
    assert rb.allow() is True, "refill: first token should be available"
    assert rb.allow() is False, "refill: bucket should be empty immediately after"
    ra = rb.retry_after()
    assert 0 < ra <= interval + 1e-6, f"refill: retry_after should be ~{interval}s, got {ra}"
    time.sleep(interval + 0.02)
    assert rb.allow() is True, "refill: a token should have refilled after the interval"

    # 4. Thread-safety: hammer ONE key from ~20 threads; total grants must not exceed capacity + small refill.
    hammer_cap = 10
    refill = 1.0                                    # 1 tok/s — negligible over a sub-second hammer
    hb = TokenBucket(capacity=hammer_cap, refill_per_sec=refill)
    granted = []
    glock = threading.Lock()

    def _worker():
        for _ in range(50):
            if hb.allow():
                with glock:
                    granted.append(1)

    threads = [threading.Thread(target=_worker) for _ in range(20)]
    t0 = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.monotonic() - t0
    allowed_refill = elapsed * refill + 1            # tokens that could legitimately have refilled mid-run
    total = len(granted)
    assert total <= hammer_cap + allowed_refill, (
        f"thread-safety: {total} grants exceeds capacity({hammer_cap}) + refill({allowed_refill:.2f}); "
        "a lock is leaking tokens under concurrency")
    assert total >= hammer_cap, f"thread-safety: only {total} grants — should at least drain the full bucket"

    # 5. default_limiter() is a stable singleton.
    assert default_limiter() is default_limiter(), "default_limiter must return the same instance"

    print(f"OK  brain_ratelimit self-test passed  (burst={cap}, isolation, refill, "
          f"thread-hammer={total} grants ≤ {hammer_cap}+{allowed_refill:.2f})")


if __name__ == "__main__":
    _selftest()
