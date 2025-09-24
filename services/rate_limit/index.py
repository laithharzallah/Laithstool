import time
from typing import Dict


class TokenBucket:
    """Very small token bucket for per-provider rate limiting (in-memory).
    Not process-safe; adequate for single-instance demo mode.
    """

    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = max(1, int(capacity))
        self.refill_per_sec = float(refill_per_sec)
        self.tokens = float(capacity)
        self.last = time.time()

    def take(self, amount: float = 1.0) -> bool:
        now = time.time()
        elapsed = max(0.0, now - self.last)
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


_buckets: Dict[str, TokenBucket] = {}


def allow(provider: str, capacity: int = 5, per_sec: float = 1.0) -> bool:
    b = _buckets.get(provider)
    if not b:
        b = TokenBucket(capacity=capacity, refill_per_sec=per_sec)
        _buckets[provider] = b
    return b.take(1.0)

