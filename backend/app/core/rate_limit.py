"""Sliding-window rate limiter for the auth endpoints.

Why it exists: Argon2 makes each password GUESS slow, but nothing stopped an
attacker from guessing all day. This caps attempts per client IP per window,
turning online brute force from "slow" into "not feasible".

Deliberately in-memory and dependency-free: at this project's scale Cloud Run
runs a single instance, so per-instance state is effectively global. If the
service ever scales out, each instance enforces the limit independently —
an attacker gets (limit × instances), which still blocks brute force. A
shared store (Firestore/Redis) is the upgrade path if that ever matters.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict


class SlidingWindowLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, Deque[float]] = {}

    def check(self, key: str) -> float:
        """Record one attempt for `key`.

        Returns 0.0 when the attempt is allowed, otherwise the number of
        seconds the caller must wait before the next attempt is allowed.
        """
        now = time.monotonic()
        window_start = now - self.window_seconds

        attempts = self._attempts.get(key)
        if attempts is None:
            attempts = deque()
            self._attempts[key] = attempts

        while attempts and attempts[0] <= window_start:
            attempts.popleft()

        if len(attempts) >= self.max_attempts:
            return attempts[0] - window_start

        attempts.append(now)

        # Opportunistic cleanup so idle keys don't accumulate forever.
        if len(self._attempts) > 10_000:
            for stale_key in [k for k, v in self._attempts.items() if not v]:
                del self._attempts[stale_key]

        return 0.0
