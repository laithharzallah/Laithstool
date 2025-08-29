import os
import httpx
from typing import List, Dict

TIMEOUT = httpx.Timeout(20.0, connect=5.0)

class GoogleSearch:
    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cx = os.getenv("GOOGLE_CSE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, q: str, num: int = 10) -> List[Dict]:
        if not (self.api_key and self.cx):
            print("❌ Google CSE: missing API key or CSE ID")
            return []
        
        # Validate and clean query
        query = (q or "").strip()
        if not query or len(query) < 2:
            print(f"❌ Google CSE: invalid query '{query}'")
            return []
        
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": max(1, min(num, 10)),
            "safe": "off",
            "lr": "lang_en"
        }
        
        try:
            print(f"🔍 Google CSE request: q='{query[:50]}...', num={params['num']}, cx={self.cx[:8]}...")
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.get(self.base_url, params=params)
            
            print(f"🔍 Google CSE response: {r.status_code}")
            if r.status_code != 200:
                error_text = r.text[:300]
                print(f"❌ Google Search API error {r.status_code}: {error_text}")
                # Log the exact request for debugging
                print(f"🔍 Failed request params: {params}")
                return []
            j = r.json() or {}
        except Exception as e:
            print(f"❌ Google Search exception: {e}")
            return []
        hits: List[Dict] = []
        for item in j.get("items", []) or []:
            url = item.get("link")
            if not url:
                continue
            hits.append({
                "title": item.get("title"),
                "url": url,
                "snippet": item.get("snippet"),
                "source": "google",
            })
        return hits

