import time
from typing import Any, Dict, Tuple


class TTLCache:
    """Simple in-memory TTL cache. Not process-safe. For demo/feature-flag usage only."""

    def __init__(self, default_ttl_seconds: int = 3600):
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._default_ttl = max(1, int(default_ttl_seconds))

    def _now(self) -> float:
        return time.time()

    def get(self, key: str) -> Any:
        if not key:
            return None
        rec = self._store.get(key)
        if not rec:
            return None
        exp, val = rec
        if self._now() > exp:
            try:
                del self._store[key]
            except Exception:
                pass
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not key:
            return
        ttl = max(1, int(ttl_seconds or self._default_ttl))
        self._store[key] = (self._now() + ttl, value)


# Global cache instance for light reuse
_DEFAULT_TTL_MIN = int(float(__import__("os").environ.get("CACHE_TTL_MIN", "1440")))
cache = TTLCache(default_ttl_seconds=max(60, _DEFAULT_TTL_MIN * 60))

