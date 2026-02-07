"""In-memory session cache with TTL and LRU eviction."""

import asyncio
import time
from typing import Any


class SessionCache:
    """Lightweight TTL-based in-memory cache for API responses.

    Thread-safe via asyncio.Lock. Uses LRU eviction when max_entries exceeded.
    """

    def __init__(self, default_ttl: float = 60.0, max_entries: int = 100) -> None:
        self._default_ttl = default_ttl
        self._max_entries = max_entries
        self._store: dict[
            str, tuple[Any, float, float]
        ] = {}  # key -> (value, expires_at, last_access)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get a cached value by key. Returns None if missing or expired."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at, _ = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            # Update last access time
            self._store[key] = (value, expires_at, time.monotonic())
            return value

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store a value with optional custom TTL."""
        async with self._lock:
            expires_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
            self._store[key] = (value, expires_at, time.monotonic())
            self._evict_if_needed()

    async def invalidate(self, pattern: str) -> int:
        """Remove entries whose keys contain the pattern. Returns count removed."""
        async with self._lock:
            keys_to_remove = [k for k in self._store if pattern in k]
            for k in keys_to_remove:
                del self._store[k]
            return len(keys_to_remove)

    async def clear(self) -> None:
        """Remove all entries."""
        async with self._lock:
            self._store.clear()

    def _evict_if_needed(self) -> None:
        """Evict expired entries first, then LRU if still over limit."""
        now = time.monotonic()
        # Remove expired
        expired = [k for k, (_, exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        # LRU eviction if still over limit
        while len(self._store) > self._max_entries:
            oldest_key = min(self._store, key=lambda k: self._store[k][2])
            del self._store[oldest_key]

    @property
    def size(self) -> int:
        """Number of entries currently in cache."""
        return len(self._store)
