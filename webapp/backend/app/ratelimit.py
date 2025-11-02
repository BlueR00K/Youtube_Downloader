import os
import time
from collections import deque
from typing import Deque, Dict

from fastapi import HTTPException

try:
    REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_URL")
except Exception:
    REDIS_URL = None


class SimpleRateLimiter:
    """In-memory sliding-window rate limiter.

    Uses environment variables:
    - RATE_LIMIT: max requests per window (default 10)
    - RATE_PERIOD: window length in seconds (default 60)

    If REDIS_URL is set, a Redis-backed counter is used per time-window so multiple
    processes/instances can share state.
    """

    def __init__(self):
        self.limit = int(os.getenv("RATE_LIMIT", "10"))
        self.period = int(os.getenv("RATE_PERIOD", "60"))
        # maps key -> deque[timestamp] (local fallback)
        self.buckets: Dict[str, Deque[float]] = {}

        self.use_redis = bool(os.getenv("REDIS_URL"))
        self._redis = None
        if self.use_redis:
            try:
                import redis

                self._redis = redis.Redis.from_url(os.getenv("REDIS_URL"))
            except Exception:
                # fall back to in-memory if redis isn't available
                self.use_redis = False

    def _now(self) -> float:
        return time.time()

    def check(self, key: str) -> None:
        # refresh config each check to allow test-time overrides
        try:
            self.limit = int(os.getenv("RATE_LIMIT", str(self.limit)))
            self.period = int(os.getenv("RATE_PERIOD", str(self.period)))
        except Exception:
            pass

        if self.use_redis and self._redis:
            # Use fixed window keyed by window index
            now = int(self._now())
            window = now // self.period
            rkey = f"rl:{key}:{window}"
            try:
                cnt = self._redis.incr(rkey)
                if cnt == 1:
                    # set expiry slightly longer than window
                    self._redis.expire(rkey, self.period + 2)
                if cnt > self.limit:
                    raise HTTPException(
                        status_code=429, detail="Too many requests")
            except HTTPException:
                raise
            except Exception:
                # On redis errors, fall back to in-memory
                pass
            return

        # In-memory sliding window fallback
        now = self._now()
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = deque()
            self.buckets[key] = bucket

        # drop old timestamps
        cutoff = now - self.period
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests")

        bucket.append(now)


rate_limiter = SimpleRateLimiter()
