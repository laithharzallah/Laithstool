import os, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, make_response
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

# Initialize OpenAI client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print(f"✅ OpenAI client initialized successfully")
    print(f"🔑 API Key present: {'Yes' if OPENAI_API_KEY else 'No'}")
    print(f"🔑 API Key length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")
    print(f"🤖 Model: {OPENAI_MODEL}")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI client: {str(e)}")
    client = None

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2024'

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Configure session to last longer and be more persistent
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),  # 24 hour sessions
    SESSION_COOKIE_NAME='laiths_tool_session'
)

# Authentication credentials
VALID_USERNAME = "ens@123"
VALID_PASSWORD = "$$$$55"

# Add before_request handler to refresh session on each request
@app.before_request
def refresh_session():
    """Refresh session on each request to prevent expiration during long operations"""
    if 'logged_in' in session:
        session.permanent = True
        session.modified = True

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
    return render_template("screener.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session.permanent = True  # Make session permanent
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.utcnow().isoformat()
            print(f"✅ User {username} logged in successfully")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    print(f"🚪 User {session.get('username', 'unknown')} logged out")
    session.clear()
    return redirect(url_for('login'))

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify system status"""
    if 'logged_in' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "components": {}
    }
    
    # Check OpenAI API
    try:
        if not OPENAI_API_KEY:
            health_status["components"]["openai"] = {
                "status": "error",
                "message": "API key not configured"
            }
        elif not client:
            health_status["components"]["openai"] = {
                "status": "error", 
                "message": "Client initialization failed"
            }
        else:
            # Test API call
            test_response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=10
            )
            health_status["components"]["openai"] = {
                "status": "healthy",
                "model": OPENAI_MODEL,
                "message": "API connection successful"
            }
    except Exception as e:
        health_status["components"]["openai"] = {
            "status": "error",
            "message": f"API test failed: {str(e)}"
        }
    
    # Check environment variables
    env_vars = {
        "OPENAI_API_KEY": "Present" if OPENAI_API_KEY else "Missing",
        "SERPER_API_KEY": "Present" if os.getenv("SERPER_API_KEY") else "Missing",
        "NEWS_API_KEY": "Present" if os.getenv("NEWS_API_KEY") else "Missing"
    }
    health_status["components"]["environment"] = {
        "status": "healthy" if OPENAI_API_KEY else "warning",
        "variables": env_vars
    }
    
    # Check integrations
    try:
        # Test a simple search
        test_result = integrations.search_serper("test", num=1)
        serper_status = "healthy" if "error" not in test_result else "warning"
        health_status["components"]["integrations"] = {
            "status": serper_status,
            "serper": "Available" if serper_status == "healthy" else "Limited",
            "message": "Web search capabilities checked"
        }
    except Exception as e:
        health_status["components"]["integrations"] = {
            "status": "warning",
            "message": f"Integration test failed: {str(e)}"
        }
    
    # Overall status
    component_statuses = [comp["status"] for comp in health_status["components"].values()]
    if "error" in component_statuses:
        health_status["status"] = "degraded"
    elif "warning" in component_statuses:
        health_status["status"] = "warning"
    
    return jsonify(health_status)

@app.route("/api/screen", methods=["POST"])
def screen():
    # Enhanced session checking with debugging
    print(f"🔍 Session check - session keys: {list(session.keys())}")
    print(f"🔍 Logged in status: {'logged_in' in session}")
    
    if 'logged_in' not in session:
        print("❌ Authentication failed - no logged_in in session")
        return jsonify({"error": "Authentication required"}), 401
    
    print(f"✅ Authentication successful for user: {session.get('username', 'unknown')}")
    
    # Refresh session on screening request
    session.permanent = True
    session.modified = True
    
    # Check OpenAI availability
    if not client:
        return jsonify({"error": "OpenAI service not available. Please check API key configuration."}), 503
        
    data = request.get_json(force=True) or {}
    # Handle both old and new UI formats
    company = (data.get("company_name") or data.get("company") or "").strip()
    country = (data.get("country") or "").strip()
    level = (data.get("screening_level") or "basic").strip()
    options = data.get("options", {})
    
    if not company:
        return jsonify({"error": "company_name is required"}), 400
    if level not in ("basic","advanced"):
        level = "basic"

    country_hint = f" in {country}" if country else ""
    
    try:
        # First, gather real-time web data
        print(f"🔍 Gathering real-time data for {company}...")
        try:
            web_data = integrations.comprehensive_company_search(company, country)
            print(f"✅ Web data gathered successfully")
        except Exception as web_error:
            print(f"❌ Web data gathering failed: {str(web_error)}")
            # Use empty web data as fallback
            web_data = {
                "website_info": {"error": "Web search failed"},
                "executives": [],
                "adverse_media": [],
                "financial_highlights": {"error": "Financial data unavailable"},
                "sanctions_check": {"error": "Sanctions check failed"}
            }
        
        # Refresh session again during long operation
        session.modified = True
        
        # Create enhanced prompt with real-time data
        try:
            user_prompt = create_enhanced_prompt(company, country_hint, level, web_data)
            print(f"✅ Enhanced prompt created")
        except Exception as prompt_error:
            print(f"❌ Prompt creation failed: {str(prompt_error)}")
            # Simple fallback prompt
            user_prompt = f"Analyze {company}{country_hint} and provide basic company information in JSON format."
        
        # Get GPT analysis
        print(f"🤖 Analyzing data with GPT using model: {OPENAI_MODEL}")
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role":"system","content":SYSTEM_PROMPT},
                          {"role":"user","content":user_prompt}],
                temperature=0.2,
                max_tokens=4000 if level=="advanced" else 2500
            )
            
            # Refresh session after GPT call
            session.modified = True
            
            raw = resp.choices[0].message.content.strip()
            print(f"✅ GPT response received, length: {len(raw)} characters")
            
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1].lstrip("json\n").lstrip()
            
            try:
                payload = json.loads(raw)
                print("✅ GPT response parsed successfully")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {str(e)}")
                # Fallback: use web data directly if GPT response is malformed
                payload = {
                    "website_info": web_data.get("website_info", {}),
                    "executives": web_data.get("executives", []),
                    "adverse_media": web_data.get("adverse_media", []),
                    "financial_highlights": web_data.get("financial_highlights", {}),
                    "risk_assessment": {
                        "overall_risk": "Medium",
                        "key_risks": ["GPT analysis incomplete - using web data only"],
                        "recommendations": ["Manual review recommended"]
                    }
                }
        except Exception as gpt_error:
            print(f"❌ GPT analysis failed: {str(gpt_error)}")
            # Complete fallback payload
            payload = {
                "website_info": {"official_website": f"https://{company.lower().replace(' ', '')}.com"},
                "executives": [{"name": "Information not available", "position": "Unknown", "background": "Web search failed"}],
                "adverse_media": [],
                "financial_highlights": {"industry": "Unknown", "founded": "Unknown", "employees": "Unknown"},
                "risk_assessment": {
                    "overall_risk": "Medium",
                    "key_risks": ["Unable to complete full analysis due to system error"],
                    "recommendations": ["Manual research recommended"]
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
        if web_data.get("sanctions_check") and not web_data["sanctions_check"].get("error"):
            data_sources.append("Sanctions Databases")
        
        # Transform to new UI format with safe access
        try:
            # Ensure payload is a dictionary
            if not isinstance(payload, dict):
                payload = {}
            
            # Safe access to nested data
            risk_assessment = payload.get("risk_assessment", {})
            financial_highlights = payload.get("financial_highlights", {})
            website_info = payload.get("website_info", {})
            executives = payload.get("executives", [])
            adverse_media = payload.get("adverse_media", [])
            
            # Get first risk as overview, with fallback
            key_risks = risk_assessment.get("key_risks", [])
            overview = key_risks[0] if key_risks and isinstance(key_risks, list) else "Company screening completed successfully."
            
            transformed_response = {
                "task_id": f"task_{int(datetime.utcnow().timestamp())}",
                "company_name": company,
                "status": "completed",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "executive_summary": {
                    "overview": overview,
                    "key_points": key_risks[:3] if isinstance(key_risks, list) else []
                },
                "company_profile": {
                    "legal_name": company,
                    "primary_industry": financial_highlights.get("industry", "Not available") if isinstance(financial_highlights, dict) else "Not available",
                    "founded_year": financial_highlights.get("founded", "Not available") if isinstance(financial_highlights, dict) else "Not available",
                    "employee_count_band": financial_highlights.get("employees", "Not available") if isinstance(financial_highlights, dict) else "Not available"
                },
                "key_people": [
                    {
                        "name": exec.get("name", "Unknown") if isinstance(exec, dict) else "Unknown",
                        "role": exec.get("position", "Unknown position") if isinstance(exec, dict) else "Unknown position",
                        "background": exec.get("background", "No background information") if isinstance(exec, dict) else "No background information",
                        "confidence": "high" if isinstance(exec, dict) and exec.get("source") else "medium"
                    } for exec in (executives if isinstance(executives, list) else [])
                ],
                "web_footprint": {
                    "official_website": website_info.get("official_website") if isinstance(website_info, dict) else None,
                    "social_media": {}
                },
                "news_and_media": [
                    {
                        "title": media.get("title", "Unknown title") if isinstance(media, dict) else "Unknown title",
                        "summary": media.get("summary", "No summary available") if isinstance(media, dict) else "No summary available",
                        "source_name": media.get("source", "Unknown source") if isinstance(media, dict) else "Unknown source",
                        "published_date": media.get("date", "Unknown date") if isinstance(media, dict) else "Unknown date",
                        "sentiment": "negative" if isinstance(media, dict) and media.get("severity") == "High" else "neutral"
                    } for media in (adverse_media if isinstance(adverse_media, list) else [])
                ],
                "sanctions_matches": web_data.get("sanctions_check", {}).get("matches", []) if isinstance(web_data.get("sanctions_check"), dict) else [],
                "risk_flags": [
                    {
                        "category": "General Risk",
                        "description": risk,
                        "severity": "medium"
                    } for risk in (key_risks if isinstance(key_risks, list) else [])
                ],
                "compliance_notes": {
                    "data_sources_used": data_sources,
                    "methodology": "Automated web-based due diligence screening using AI analysis"
                }
            }
            print(f"✅ Response transformation completed successfully")
        except Exception as transform_error:
            print(f"❌ Response transformation failed: {str(transform_error)}")
            # Emergency fallback response
            transformed_response = {
                "task_id": f"task_{int(datetime.utcnow().timestamp())}",
                "company_name": company,
                "status": "completed",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "executive_summary": {
                    "overview": "Basic screening completed with limited data",
                    "key_points": ["System encountered processing issues", "Manual verification recommended"]
                },
                "company_profile": {
                    "legal_name": company,
                    "primary_industry": "Not available",
                    "founded_year": "Not available",
                    "employee_count_band": "Not available"
                },
                "key_people": [],
                "web_footprint": {"official_website": None, "social_media": {}},
                "news_and_media": [],
                "sanctions_matches": [],
                "risk_flags": [],
                "compliance_notes": {
                    "data_sources_used": ["Basic search"],
                    "methodology": "Fallback mode due to system limitations"
                }
            }
        
        print(f"✅ Screening completed successfully for {company}")
        return jsonify(transformed_response)
        
    except ValidationError as ve:
        print(f"❌ Validation error: {str(ve)}")
        return jsonify({"error":"Schema validation failed","details":json.loads(ve.json())}), 422
    except Exception as e:
        print(f"❌ Error during screening: {str(e)}")
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    print(f"🚀 Starting Laith's Tool on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
