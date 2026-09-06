"""Tiny in-process TTL cache.

Why this exists: every database call is a network round trip, and from a
client far from the database region a round trip can cost ~1 s. The analysis
itself takes ~7 ms, so request latency was dominated by repeated reads of
data that barely changes (the caller's auth session, user record, and
learning session). Caching those for a few seconds removes most round trips
from the hot path without changing behaviour the user can perceive.

Deliberately in-process: a single Cloud Run instance serves the user's
session, and a stale entry lives at most `ttl_seconds`. Security-relevant
entries (auth) are invalidated explicitly on sign-out.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    def __init__(self, ttl_seconds: float, max_entries: int = 2000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= time.monotonic():
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if len(self._entries) >= self.max_entries:
            now = time.monotonic()
            for stale_key in [k for k, (exp, _) in self._entries.items() if exp <= now]:
                self._entries.pop(stale_key, None)
            if len(self._entries) >= self.max_entries:
                self._entries.clear()
        self._entries[key] = (time.monotonic() + self.ttl_seconds, value)

    def invalidate(self, key: str) -> None:
        self._entries.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        for key in [k for k in self._entries if k.startswith(prefix)]:
            self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()
