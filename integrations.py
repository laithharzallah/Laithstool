import os, requests
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY   = os.getenv("NEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_serper(query, num=5):
    if not SERPER_API_KEY:
        return {"error":"SERPER_API_KEY missing"}
    h = {"X-API-KEY": SERPER_API_KEY, "Content-Type":"application/json"}
    r = requests.post("https://google.serper.dev/search", headers=h, json={"q": query, "num": num}, timeout=20)
    try:
        j = r.json()
    except Exception:
        j = {"error": r.text}
    return j

def search_newsapi(query, page_size=5, language="en"):
    if not NEWS_API_KEY:
        return {"error":"NEWS_API_KEY missing"}
    p = {"q": query, "pageSize": page_size, "language": language, "sortBy":"relevancy", "apiKey": NEWS_API_KEY}
    r = requests.get("https://newsapi.org/v2/everything", params=p, timeout=20)
    try:
        j = r.json()
    except Exception:
        j = {"error": r.text}
    return j
