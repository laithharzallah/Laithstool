"""
Robust Google Custom Search Engine client with proper validation
"""
import os
import urllib.parse
import httpx

GOOGLE_CSE_KEY = os.getenv("GOOGLE_API_KEY")  # Match Render env var name
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
BASE = "https://www.googleapis.com/customsearch/v1"

class GoogleCSEError(RuntimeError):
    pass

def _validate_params(q: str, num: int, start: int, lr: str | None):
    if not q or not q.strip():
        raise GoogleCSEError("Missing query (q).")
    if not GOOGLE_CSE_KEY or not GOOGLE_CSE_ID:
        raise GoogleCSEError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID env vars.")
    if not (1 <= num <= 10):
        raise GoogleCSEError("num must be between 1 and 10.")
    if not (1 <= start <= 100):
        raise GoogleCSEError("start must be between 1 and 100.")
    if lr and not lr.startswith("lang_"):
        raise GoogleCSEError("lr must look like 'lang_en', 'lang_ar', etc.")

def google_cse_search(
    q: str,
    *,
    num: int = 10,
    start: int = 1,
    gl: str | None = "sa",
    lr: str | None = "lang_en",
    site: str | None = None,          # e.g., "linkedin.com"
    include_site: bool = True,        # True -> include, False -> exclude
    safe: str = "off",
    timeout: float = 20.0
) -> dict:
    """
    Search Google Custom Search Engine with proper validation
    """
    _validate_params(q, num, start, lr)
    params = {
        "key": GOOGLE_CSE_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": q.strip(),
        "num": num,
        "start": start,
        "safe": safe,
    }
    if gl: 
        params["gl"] = gl
    if lr: 
        params["lr"] = lr
    if site:
        params["siteSearch"] = site
        params["siteSearchFilter"] = "i" if include_site else "e"

    # Log a sanitized URL (no key) for debugging
    debug_params = {k: v for k, v in params.items() if k != "key"}
    print(f"🔍 CSE GET {BASE} params={debug_params}")

    with httpx.Client(timeout=timeout) as client:
        r = client.get(BASE, params=params)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Surface Google's error details
            raise GoogleCSEError(f"Google CSE HTTP {r.status_code}: {r.text}") from e
        return r.json()

def map_cse_items_to_adverse_media(items):
    """Map Google CSE items to adverse media format"""
    out = []
    for it in (items or []):
        out.append({
            "category": "media",
            "date": it.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time"),
            "headline": it.get("title"),
            "severity": None,
            "source": it.get("displayLink"),
            "source_url": it.get("link"),
            "summary": it.get("snippet")
        })
    return out

def map_cse_items_to_executives(items):
    """Map Google CSE items to executives format"""
    out = []
    for it in (items or []):
        title = it.get("title", "")
        snippet = it.get("snippet", "")
        
        # Simple name extraction from title/snippet
        import re
        name_patterns = [
            r'CEO\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Chairman\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+CEO',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+Chairman'
        ]
        
        name = None
        position = "Executive"
        for pattern in name_patterns:
            match = re.search(pattern, title + " " + snippet)
            if match:
                name = match.group(1)
                if "CEO" in pattern:
                    position = "CEO"
                elif "Chairman" in pattern:
                    position = "Chairman"
                break
        
        if name:
            out.append({
                "name": name,
                "position": position,
                "source": it.get("displayLink"),
                "source_url": it.get("link"),
                "background": None,
                "company": None
            })
    
    return out

def map_cse_items_to_company_info(items):
    """Map Google CSE items to company info format"""
    if not items:
        return {}
    
    # Use first item as primary source
    first = items[0]
    return {
        "legal_name": None,
        "website": first.get("link"),
        "founded_year": None,
        "headquarters": None,
        "industry": None,
        "business_description": first.get("snippet"),
        "registration_status": None,
        "entity_type": None
    }
