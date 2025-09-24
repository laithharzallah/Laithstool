import os
from typing import List, Dict, Optional
from services.rate_limit.index import allow
from services.cache.index import cache
from services.google_cse import google_cse_search, GoogleCSEError


def _score_source(domain: str) -> int:
    if not domain:
        return 0
    d = domain.lower()
    preferred = ["reuters", "bloomberg", "ft.com", "wsj.com", "apnews", "bbc", "cnbc", "theguardian"]
    for p in preferred:
        if p in d:
            return 3
    return 1


def search_news(query: str, *, max_results: int | None = None, lang: str = "en") -> List[Dict]:
    max_items = int(os.getenv("NEWS_MAX_RESULTS", "20"))
    if isinstance(max_results, int) and max_results > 0:
        max_items = min(max_items, max_results)

    key = f"news|{query}|{lang}|{max_items}"
    cached = cache.get(key)
    if cached:
        return cached

    out: List[Dict] = []
    # Rate limit Google CSE
    if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID") and allow("google_cse", capacity=10, per_sec=2.0):
        try:
            data = google_cse_search(query, num=min(10, max_items), lr=f"lang_{lang}")
            for it in data.get("items", []) or []:
                out.append({
                    "title": it.get("title"),
                    "url": it.get("link"),
                    "source": it.get("displayLink"),
                    "publishedAt": (it.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time") if it.get("pagemap") else None),
                    "snippet": it.get("snippet"),
                    "reputation": _score_source(it.get("displayLink", "")),
                })
        except GoogleCSEError:
            pass

    # TODO: add Serper adapter if present (reuse existing service)
    try:
        from services.real_time_search import RealTimeSearchService  # type: ignore
        # Not calling the full LLM; use serper via private method if available
        # Fallback: do nothing if not available
    except Exception:
        pass

    # Deduplicate by URL
    seen = set()
    deduped: List[Dict] = []
    for it in out:
        u = it.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        deduped.append(it)

    cache.set(key, deduped, ttl_seconds=max(60, int(os.getenv("CACHE_TTL_MIN", "1440")) * 60))
    return deduped[:max_items]

