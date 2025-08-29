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
            return []
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": q,
            "num": max(1, min(num, 10)),
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.get(self.base_url, params=params)
            if r.status_code != 200:
                print(f"❌ Google Search API error: {r.status_code} {r.text[:200]}")
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

