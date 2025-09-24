import os
import json
from typing import List, Dict
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def summarize_and_classify(items: List[Dict]) -> Dict:
    if not os.getenv("OPENAI_API_KEY"):
        return {"summary": "", "items": []}
    client = OpenAI()
    system = (
        "You are a news summarizer. Return ONLY JSON. For each item, classify sentiment (negative/neutral/positive) and severity 1-5 (5 is worst)."
    )
    schema = {
        "summary": "",
        "items": [
            {"title": "", "url": "", "source": "", "publishedAt": None, "sentiment": "neutral", "severity": 3, "snippet": ""}
        ],
    }
    prompt = {
        "items": [
            {
                "title": it.get("title"),
                "url": it.get("url"),
                "source": it.get("source"),
                "publishedAt": it.get("publishedAt"),
                "snippet": it.get("snippet"),
            }
            for it in items[:20]
        ]
    }
    resp = client.chat.completions.create(
        model=_MODEL,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except Exception:
        data = {"summary": "", "items": []}
    # Sanitize severities to 1..5
    for it in data.get("items", []):
        try:
            sev = int(it.get("severity", 3))
            it["severity"] = max(1, min(5, sev))
        except Exception:
            it["severity"] = 3
        sent = (it.get("sentiment") or "neutral").lower()
        if sent not in ("negative", "neutral", "positive"):
            it["sentiment"] = "neutral"
    return data

