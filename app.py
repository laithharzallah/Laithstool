import os, json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

class Executive(BaseModel):
    name: str
    position: Optional[str] = None
    background: Optional[str] = None
    source: Optional[str] = None

class AdverseMedia(BaseModel):
    title: str
    summary: Optional[str] = None
    severity: Optional[Literal["High","Medium","Low"]] = None
    date: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None

class WebsiteInfo(BaseModel):
    official_website: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None

class Financials(BaseModel):
    revenue: Optional[str] = None
    employees: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None

class RiskAssessment(BaseModel):
    overall_risk: Optional[Literal["Low","Medium","High"]] = None
    key_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ScreenResponse(BaseModel):
    company_name: str
    country: Optional[str] = None
    screening_level: Literal["basic","advanced"]
    timestamp: str
    website_info: Optional[WebsiteInfo] = None
    executives: List[Executive] = Field(default_factory=list)
    adverse_media: List[AdverseMedia] = Field(default_factory=list)
    financial_highlights: Optional[Financials] = None
    risk_assessment: Optional[RiskAssessment] = None
    model: Optional[str] = None

SYSTEM_PROMPT = "You are a professional due diligence researcher. Always respond with valid JSON only."

ADVANCED = """You are a professional due diligence researcher. Provide comprehensive information about "{company}"{country_hint}.
Return your response as a JSON object with this structure:
{
  "website_info": {"official_website": "...", "title": "...", "status": "Found/Not found", "source": "Sources/URLs"},
  "executives": [{"name": "...", "position": "...", "background": "...", "source": "URL"}],
  "adverse_media": [{"title": "...", "summary": "...", "severity": "High/Medium/Low", "date": "YYYY-MM-DD", "source": "URL", "category": "Legal/Financial/Regulatory/Operational"}],
  "financial_highlights": {"revenue": "...", "employees": "...", "founded": "...", "industry": "..."},
  "risk_assessment": {"overall_risk": "Low/Medium/High", "key_risks": ["..."], "recommendations": ["..."]}
}
Focus on the last 24 months, cite credible sources, avoid speculation.
"""

BASIC = """You are a business researcher. Provide basic information about "{company}"{country_hint}.
Return JSON with: website_info (official_website, title, status, source), executives (name, position, source), adverse_media (title, summary, date, source, severity).
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/screen", methods=["POST"])
def screen():
    data = request.get_json(force=True) or {}
    company = (data.get("company_name") or "").strip()
    country = (data.get("country") or "").strip()
    level = (data.get("screening_level") or "basic").strip()
    if not company:
        return jsonify({"error": "company_name is required"}), 400
    if level not in ("basic","advanced"):
        level = "basic"

    country_hint = f" in {country}" if country else ""
    user_prompt = (ADVANCED if level=="advanced" else BASIC).format(company=company, country_hint=country_hint)

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":user_prompt}],
            temperature=0.2,
            max_tokens=3000 if level=="advanced" else 1500
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1].lstrip("json\n").lstrip()
        payload = json.loads(raw)
        out = ScreenResponse(
            company_name=company,
            country=country or None,
            screening_level=level,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            model=OPENAI_MODEL,
            **payload
        )
        return jsonify(out.model_dump())
    except ValidationError as ve:
        return jsonify({"error":"Schema validation failed","details":json.loads(ve.json())}), 422
    except Exception as e:
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
