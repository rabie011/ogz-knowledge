#!/usr/bin/env python3
"""PER-CLIENT TOKEN-BUCKET RATE LIMITER (June 29 — standalone, dependency-free).
A token bucket per client_id: each allow() spends one token, tokens refill at a
fixed rate up to capacity. Ready to wire into brain_api later (NOT wired yet).
The clock is INJECTABLE so the self-test simulates time without real sleep.

Usage:
    from rate_limit import RateLimiter
    limiter = RateLimiter(capacity=60, refill_per_sec=1.0)  # 60 burst, ~1/sec sustained
    if not limiter.allow(client_id):
        ...  # reject / 429

Self-test: python3 scripts/rate_limit.py  (exit 0 = pass, exit 1 = fail)
"""
import time


class TokenBucket:
    """A single token bucket. Holds up to `capacity` tokens; refills at
    `refill_per_sec` tokens/second. `clock` is any callable -> float seconds
    (injectable so tests can simulate time without sleeping)."""

    def __init__(self, capacity: float, refill_per_sec: float, clock=time.time):
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        if refill_per_sec < 0:
            raise ValueError(f"refill_per_sec must be >= 0, got {refill_per_sec}")
        self.capacity = float(capacity)
        self.refill_per_sec = float(refill_per_sec)
        self.clock = clock
        self.tokens = float(capacity)          # start full
        self.last = clock()

    def _refill(self):
        now = self.clock()
        elapsed = now - self.last
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
            self.last = now

    def allow(self, cost: float = 1.0) -> bool:
        """Spend `cost` tokens if available. Returns True (allowed) or False (blocked)."""
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class RateLimiter:
    """Registry of one TokenBucket per client_id, all sharing the same
    capacity/refill/clock. allow(client_id) -> bool spends a token for that client."""

    def __init__(self, capacity: float, refill_per_sec: float, clock=time.time):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.clock = clock
        self._buckets: dict[str, TokenBucket] = {}

    def _bucket(self, client_id: str) -> TokenBucket:
        b = self._buckets.get(client_id)
        if b is None:
            b = TokenBucket(self.capacity, self.refill_per_sec, clock=self.clock)
            self._buckets[client_id] = b
        return b

    def allow(self, client_id: str, cost: float = 1.0) -> bool:
        """True if `client_id` has tokens to spend, False otherwise."""
        return self._bucket(client_id).allow(cost)


# ---------------------------------------------------------------------------
def _self_test() -> int:
    """Asserts the limiter with a FAKE clock (no real sleep). Returns assert count."""
    asserts = 0

    class FakeClock:
        def __init__(self):
            self.now = 1000.0

        def __call__(self):
            return self.now

        def advance(self, secs):
            self.now += secs

    clock = FakeClock()
    capacity = 5
    refill_per_sec = 1.0  # one token back per second
    limiter = RateLimiter(capacity=capacity, refill_per_sec=refill_per_sec, clock=clock)
    cid = "client-A"

    # 1) allowed `capacity` times in a row (no time advance => no refill)
    for i in range(capacity):
        assert limiter.allow(cid) is True, f"call {i + 1}/{capacity} should be ALLOWED"
        asserts += 1

    # 2) the (capacity+1)th is BLOCKED
    assert limiter.allow(cid) is False, "the (capacity+1)th call must be BLOCKED"
    asserts += 1

    # 3) still blocked when barely any time passed (0.5s < 1s for one token)
    clock.advance(0.5)
    assert limiter.allow(cid) is False, "0.5s refill (<1 token) must still be BLOCKED"
    asserts += 1

    # 4) after advancing enough to refill, allowed again
    clock.advance(1.0)  # total 1.5s elapsed -> >= 1 whole token available
    assert limiter.allow(cid) is True, "after >=1s refill the client must be ALLOWED again"
    asserts += 1

    # 5) refill never exceeds capacity (advance far, then can only spend `capacity`)
    clock.advance(10_000)
    for i in range(capacity):
        assert limiter.allow(cid) is True, f"post-long-refill call {i + 1} should be ALLOWED"
        asserts += 1
    assert limiter.allow(cid) is False, "refill must cap at capacity (no extra beyond capacity)"
    asserts += 1

    # 6) buckets are independent per client_id (B's fresh bucket is full)
    assert limiter.allow("client-B") is True, "a different client must have its own full bucket"
    asserts += 1

    return asserts


if __name__ == "__main__":
    try:
        n = _self_test()
    except AssertionError as e:
        print(f"❌ rate_limit: FAILED — {e}")
        raise SystemExit(1)
    print(f"✅ rate_limit: {n} asserts passed")
