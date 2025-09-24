from typing import Dict, List
import hashlib


def _key(title: str, url: str) -> str:
    base = (title or "").strip().lower() + "|" + (url or "").strip().lower()
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def normalize_company(
    name: str,
    country: str,
    website: str | None,
    executives: List[Dict] | None,
    ownership: List[Dict] | None,
    news_items: List[Dict],
    news_summary: str,
    sources: List[str],
    cache_hit: bool,
    feature_flags: Dict[str, bool],
) -> Dict:
    # Dedup news items by canonical key
    seen = set()
    deduped: List[Dict] = []
    for it in news_items or []:
        k = _key(it.get("title", ""), it.get("url", ""))
        if k in seen:
            continue
        seen.add(k)
        deduped.append(it)

    return {
        "company": {
            "name": name,
            "country": country or None,
            "website": website,
            "identifiers": {"other": {}},
        },
        "executives": [
            {"name": e.get("name"), "role": e.get("position") or e.get("role"), "source": e.get("source") or "web"}
            for e in (executives or [])
        ],
        "ownership": [
            {
                "holder": o.get("name") or o.get("holder"),
                "percent": o.get("percent"),
                "relation": o.get("relation"),
                "source": o.get("source") or "web",
            }
            for o in (ownership or [])
        ],
        "adverseMedia": {
            "summary": news_summary or "",
            "items": [
                {
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "source": it.get("source"),
                    "publishedAt": it.get("publishedAt"),
                    "sentiment": it.get("sentiment") or "neutral",
                    "severity": int(it.get("severity") or 3),
                    "snippet": it.get("snippet"),
                }
                for it in deduped
            ],
        },
        "meta": {
            "generatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "sources": sources,
            "warnings": [],
            "cacheHit": bool(cache_hit),
            "featureFlags": feature_flags,
        },
    }

