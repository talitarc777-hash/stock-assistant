"""Small in-process TTL cache for low-resource deployments.

This keeps repeated read endpoints lighter without adding external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: datetime


class TTLCache(Generic[T]):
    """Simple thread-safe TTL cache with string keys."""

    def __init__(self, *, max_items: int = 256) -> None:
        self._max_items = max(1, int(max_items))
        self._items: dict[str, _CacheEntry[T]] = {}
        self._lock = Lock()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def get(self, key: str) -> T | None:
        clean_key = str(key)
        with self._lock:
            entry = self._items.get(clean_key)
            if entry is None:
                return None
            if entry.expires_at <= self._now():
                self._items.pop(clean_key, None)
                return None
            return entry.value

    def set(self, key: str, value: T, *, ttl_seconds: float) -> None:
        clean_key = str(key)
        ttl = max(0.1, float(ttl_seconds))
        with self._lock:
            if len(self._items) >= self._max_items:
                # Remove one arbitrary (oldest insertion order in CPython dict).
                first_key = next(iter(self._items))
                self._items.pop(first_key, None)
            self._items[clean_key] = _CacheEntry(
                value=value,
                expires_at=self._now() + timedelta(seconds=ttl),
            )

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._items.pop(str(key), None)

    def invalidate_prefix(self, prefix: str) -> None:
        clean_prefix = str(prefix)
        with self._lock:
            for key in [item for item in self._items if item.startswith(clean_prefix)]:
                self._items.pop(key, None)

