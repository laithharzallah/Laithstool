import os, json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from dotenv import load_dotenv
from openai import OpenAI
import integrations

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2024'

# Authentication credentials
VALID_USERNAME = "ens@123"
VALID_PASSWORD = "$$$$55"

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
    sector: Optional[str] = None
    market_cap: Optional[str] = None

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
    data_sources: List[str] = Field(default_factory=list)

SYSTEM_PROMPT = "You are a professional due diligence researcher with access to real-time company data. Analyze the provided data and respond with valid JSON only."

def create_enhanced_prompt(company: str, country_hint: str, level: str, web_data: dict) -> str:
    """Create an enhanced prompt using real-time web data"""
    
    base_prompt = f"""You are a professional due diligence researcher. Analyze the provided real-time data about "{company}"{country_hint} and provide comprehensive information.

REAL-TIME DATA PROVIDED:
"""
    
    # Add website information
    if "website_info" in web_data and not web_data["website_info"].get("error"):
        base_prompt += f"\nWEBSITE INFO: {json.dumps(web_data['website_info'], indent=2)}"
    
    # Add executive information
    if "executives" in web_data and web_data["executives"]:
        base_prompt += f"\nEXECUTIVES FOUND: {json.dumps(web_data['executives'], indent=2)}"
    
    # Add adverse media
    if "adverse_media" in web_data and web_data["adverse_media"]:
        base_prompt += f"\nADVERSE MEDIA: {json.dumps(web_data['adverse_media'], indent=2)}"
    
    # Add financial data
    if "financial_highlights" in web_data and not web_data["financial_highlights"].get("error"):
        base_prompt += f"\nFINANCIAL DATA: {json.dumps(web_data['financial_highlights'], indent=2)}"
    
    # Add general search results
    if "general_search" in web_data and "organic" in web_data["general_search"]:
        search_results = web_data["general_search"]["organic"][:3]  # Top 3 results
        base_prompt += f"\nGENERAL SEARCH RESULTS: {json.dumps(search_results, indent=2)}"
    
    base_prompt += f"""

Return your response as a JSON object with this exact structure:
{{
    "website_info": {{
        "official_website": "the official website URL or 'Not found'",
        "title": "brief description of the company",
        "status": "Found/Not found",
        "source": "Real-time web search"
    }},
    "executives": [
        {{
            "name": "Executive Name",
            "position": "Job Title",
            "background": "Brief professional background",
            "source": "Real-time web search"
        }}
    ],
    "adverse_media": [
        {{
            "title": "News headline or issue title",
            "summary": "Detailed description of the issue",
            "severity": "High/Medium/Low",
            "date": "YYYY-MM-DD",
            "source": "News source URL",
            "category": "Legal/Financial/Regulatory/Operational"
        }}
    ],
    "financial_highlights": {{
        "revenue": "Latest revenue if known",
        "employees": "Number of employees if known",
        "founded": "Year founded if known",
        "industry": "Primary industry",
        "sector": "Business sector",
        "market_cap": "Market capitalization if available"
    }},
    "risk_assessment": {{
        "overall_risk": "Low/Medium/High",
        "key_risks": ["List of key risk factors based on findings"],
        "recommendations": ["Due diligence recommendations based on data"]
    }}
}}

Use the real-time data provided above to fill out this structure. Focus on accuracy and cite recent developments."""

    if level == "basic":
        base_prompt += "\n\nProvide basic screening focusing on website, key executives, and major issues only."
    else:
        base_prompt += "\n\nProvide comprehensive analysis including detailed risk assessment and financial insights."
    
    return base_prompt

@app.route("/")
def home():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/api/screen", methods=["POST"])
def screen():
    if 'logged_in' not in session:
        return jsonify({"error": "Authentication required"}), 401
        
    data = request.get_json(force=True) or {}
    company = (data.get("company_name") or "").strip()
    country = (data.get("country") or "").strip()
    level = (data.get("screening_level") or "basic").strip()
    
    if not company:
        return jsonify({"error": "company_name is required"}), 400
    if level not in ("basic","advanced"):
        level = "basic"

    country_hint = f" in {country}" if country else ""
    
    try:
        # First, gather real-time web data
        print(f"Gathering real-time data for {company}...")
        web_data = integrations.comprehensive_company_search(company, country)
        
        # Create enhanced prompt with real-time data
        user_prompt = create_enhanced_prompt(company, country_hint, level, web_data)
        
        # Get GPT analysis
        print("Analyzing data with GPT...")
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":user_prompt}],
            temperature=0.2,
            max_tokens=4000 if level=="advanced" else 2500
        )
        
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1].lstrip("json\n").lstrip()
        
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: use web data directly if GPT response is malformed
            payload = {
                "website_info": web_data.get("website_info", {}),
                "executives": web_data.get("executives", []),
                "adverse_media": web_data.get("adverse_media", []),
                "financial_highlights": web_data.get("financial_highlights", {}),
                "risk_assessment": {
                    "overall_risk": "Medium",
                    "key_risks": ["Data analysis incomplete"],
                    "recommendations": ["Manual review recommended"]
                }
            }
        
        # Enhance payload with any missing data from web search
        if not payload.get("website_info") and web_data.get("website_info"):
            payload["website_info"] = web_data["website_info"]
        
        if not payload.get("executives") and web_data.get("executives"):
            payload["executives"] = web_data["executives"]
        
        if not payload.get("adverse_media") and web_data.get("adverse_media"):
            payload["adverse_media"] = web_data["adverse_media"]
        
        if not payload.get("financial_highlights") and web_data.get("financial_highlights"):
            payload["financial_highlights"] = web_data["financial_highlights"]
        
        # Create data sources list
        data_sources = ["Real-time web search", "GPT Analysis"]
        if not web_data.get("general_search", {}).get("error"):
            data_sources.append("Google Search")
        if not web_data.get("news_search", {}).get("error"):
            data_sources.append("News API")
        
        out = ScreenResponse(
            company_name=company,
            country=country or None,
            screening_level=level,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            model=OPENAI_MODEL,
            data_sources=data_sources,
            **payload
        )
        
        return jsonify(out.model_dump())
        
    except ValidationError as ve:
        return jsonify({"error":"Schema validation failed","details":json.loads(ve.json())}), 422
    except Exception as e:
        print(f"Error during screening: {str(e)}")
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
