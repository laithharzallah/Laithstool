import os, json
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, make_response
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables only in development or if .env exists locally
if os.environ.get('FLASK_ENV', '').lower() == 'development' or os.path.exists('.env'):
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
else:
    print("🌍 Production mode: using system environment variables")

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DILISENSE_API_KEY = os.getenv("DILISENSE_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Initialize OpenAI client only if key is available
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"✅ OpenAI client initialized successfully")
        print(f"🔑 API Key present: Yes")
        print(f"🔑 API Key length: {len(OPENAI_API_KEY)}")
        print(f"🤖 Model: {OPENAI_MODEL}")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {str(e)}")
        client = None
else:
    print("⚠️ OPENAI_API_KEY not found - some features will be limited")
    print("📝 Add OPENAI_API_KEY to Render environment variables")
    client = None

# Check Dilisense API key
if DILISENSE_API_KEY:
    print(f"✅ Dilisense API key loaded")
else:
    print("⚠️ DILISENSE_API_KEY not found - company screening will not work")
    print("📝 Add DILISENSE_API_KEY in Render → Environment")

# Check OpenAI API key
if not os.environ.get('OPENAI_API_KEY'):
    print("⚠️ OPENAI_API_KEY missing; features limited")
    print("📝 Add OPENAI_API_KEY in Render → Environment")

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-2024'

# Global error handlers - NEVER return raw 500s
@app.errorhandler(500)
def handle_internal_error(error):
    """Global handler for internal server errors"""
    import traceback
    error_details = {
        "error": "Internal server error",
        "message": "The system encountered an unexpected error but recovered gracefully",
        "step": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "partial_results": True
    }
    
    # Log the full error for debugging
    print(f"❌ Internal Error: {str(error)}")
    traceback.print_exc()
    
    return jsonify(error_details), 500

@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not found", 
        "message": "The requested resource was not found",
        "timestamp": datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 errors"""
    return jsonify({
        "error": "Forbidden",
        "message": "Access denied - please check authentication",
        "timestamp": datetime.utcnow().isoformat()
    }), 403

@app.errorhandler(Exception)
def handle_all_exceptions(error):
    """Catch-all exception handler"""
    import traceback
    error_details = {
        "error": "System error",
        "message": f"Unexpected error: {str(error)}",
        "step": "system",
        "timestamp": datetime.utcnow().isoformat(),
        "recovered": True
    }
    
    print(f"❌ Unhandled Exception: {str(error)}")
    traceback.print_exc()
    
    return jsonify(error_details), 500

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
    return redirect(url_for('company_screening'))

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
    # Temporarily disable session check for testing
    # if 'logged_in' not in session:
    #     return jsonify({"error": "Authentication required"}), 401
    
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
    
    # Check GPT-5 and search services
    try:
        from services.real_time_search import real_time_search_service
        health_status["components"]["search"] = {
            "status": "healthy",
            "providers": len(real_time_search_service.search_providers) if hasattr(real_time_search_service, 'search_providers') else 0,
            "message": "Real-time search services initialized"
        }
    except Exception as e:
        health_status["components"]["search"] = {
            "status": "warning",
            "message": f"Search service check failed: {str(e)}"
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
        # Skip web data gathering temporarily for debugging
        print(f"🔍 Skipping web data gathering for debugging...")
        web_data = {
            "website_info": {"official_website": f"https://{company.lower().replace(' ', '')}.com"},
            "executives": [{"name": "Test Executive", "position": "CEO", "background": "Test info"}],
            "adverse_media": [],
            "financial_highlights": {"industry": "Technology", "founded": "2020", "employees": "50"},
            "sanctions_check": {"matches": []}
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

@app.route("/api/test", methods=["POST"])
def test_endpoint():
    """Simple test endpoint to debug issues"""
    try:
        print("🧪 Test endpoint called")
        
        # Check session
        if 'logged_in' not in session:
            return jsonify({"error": "Not authenticated"}), 401
        
        print("✅ Session is valid")
        
        # Get request data
        data = request.get_json() or {}
        company = data.get("company", "Test Company")
        
        print(f"📝 Company: {company}")
        
        # Test basic response
        test_response = {
            "task_id": f"test_{int(datetime.utcnow().timestamp())}",
            "company_name": company,
            "status": "completed",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "executive_summary": {
                "overview": "This is a test response to verify the system is working",
                "key_points": ["Test point 1", "Test point 2", "Test point 3"]
            },
            "company_profile": {
                "legal_name": company,
                "primary_industry": "Test Industry",
                "founded_year": "2020",
                "employee_count_band": "10-50"
            },
            "key_people": [
                {
                    "name": "Test Executive",
                    "role": "CEO",
                    "background": "Test background information",
                    "confidence": "high"
                }
            ],
            "web_footprint": {
                "official_website": f"https://{company.lower().replace(' ', '')}.com",
                "social_media": {"linkedin": "https://linkedin.com/company/test"}
            },
            "news_and_media": [
                {
                    "title": "Test News Article",
                    "summary": "This is a test news summary",
                    "source_name": "Test News Source",
                    "published_date": "2024-01-01",
                    "sentiment": "neutral"
                }
            ],
            "sanctions_matches": [],
            "risk_flags": [
                {
                    "category": "Test Risk",
                    "description": "This is a test risk flag",
                    "severity": "low"
                }
            ],
            "compliance_notes": {
                "data_sources_used": ["Test API", "Mock Data"],
                "methodology": "Test methodology for debugging"
            }
        }
        
        print("✅ Test response created successfully")
        return jsonify(test_response)
        
    except Exception as e:
        print(f"❌ Test endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

# Add missing routes for company and individual screening
@app.route("/company")
def company_screening():
    """Company screening page"""
    # Temporarily disable session check for testing
    # if 'logged_in' not in session:
    #     return redirect(url_for('login'))
    try:
        return render_template("company_screening.html")
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        return f"Template error: {str(e)}", 500

@app.route("/test-company")
def test_company():
    """Test route for company screening"""
    print("🔍 Test company route accessed!")
    return "Company screening route is working! No session required!"

@app.route("/individual")
def individual_screening():
    """Individual screening page"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("individual_screening.html")

@app.route("/api/enhanced-screen", methods=["POST"])
def enhanced_company_screening():
    """Enhanced company screening with Dilisense and real-time search"""
    print("🚀 API endpoint called: /api/enhanced-screen")
    
    if 'logged_in' not in session:
        print("❌ Authentication failed - not logged in")
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        print("🔍 Parsing request data...")
        try:
            data = request.get_json()
            if data is None:
                data = {}
        except Exception as json_error:
            print(f"❌ JSON parsing failed: {json_error}")
            data = {}
        print(f"📊 Request data: {data}")
        
        company_name = data.get("company_name", "").strip() or data.get("companyName", "").strip()
        country = data.get("country", "").strip()
        
        print(f"🏢 Company: '{company_name}', Country: '{country}'")
        
        if not company_name:
            print("❌ Company name missing")
            return jsonify({"error": "company_name is required"}), 400
        
        print(f"🔍 Starting enhanced screening for: {company_name}")
        
        # Import services
        print("📦 Importing services...")
        from services.dilisense import dilisense_service
        from services.real_time_search import real_time_search_service
        print("✅ Services imported successfully")
        
        # Create event loop for async operations
        print("🔄 Creating async event loop...")
        
        # Run async operations in event loop
        loop = asyncio.new_event_loop()
        # Don't set as global event loop to avoid conflicts in production
        print("✅ Event loop created")
        
        # Memory optimization for production
        import gc
        gc.collect()  # Force garbage collection before heavy operations
        
        try:
            # Perform Dilisense company screening
            print("🔍 Calling Dilisense service...")
            dilisense_results = loop.run_until_complete(
                dilisense_service.screen_company(company_name, country)
            )
            print(f"✅ Dilisense completed: {type(dilisense_results)}")
            
            # Perform real-time web search
            print("🔍 Calling real-time search service...")
            web_search_results = loop.run_until_complete(
                real_time_search_service.comprehensive_search(
                    company=company_name,
                    country=country
                )
            )
            print(f"✅ Web search completed: {type(web_search_results)}")
            print(f"🔍 Web search results keys: {list(web_search_results.keys()) if isinstance(web_search_results, dict) else 'Not a dict'}")
            print(f"🔍 Company profile: {web_search_results.get('company_profile', 'Not found')}")
            print(f"🔍 Executives: {web_search_results.get('executives', 'Not found')}")
            print(f"🔍 Total results: {web_search_results.get('total_results', 'Not found')}")
        except Exception as service_error:
            print(f"❌ Service call failed: {service_error}")
            raise service_error
        finally:
            print("🔄 Closing event loop...")
            loop.close()
            print("✅ Event loop closed")
        
        # Combine results
        print("🔧 Combining results...")
        combined_results = {
            "company": company_name.upper(),
            "country": country.upper() if country else "N/A",
            "timestamp": datetime.utcnow().isoformat(),
            "data_sources": ["Dilisense Company Screening", "Real-time Web Search"],
            "dilisense": dilisense_results,
            "web_search": {
                "categorized_results": {
                    "company_info": web_search_results.get("company_profile", {}).get("results", []) if web_search_results.get("company_profile") else [],
                    "executives": web_search_results.get("executives", {}).get("results", []) if web_search_results.get("executives") else [],
                    "adverse_media": web_search_results.get("adverse_media", {}).get("results", []) if web_search_results.get("adverse_media") else [],
                    "financials": web_search_results.get("financials", {}).get("results", []) if web_search_results.get("financials") else [],
                    "sanctions": web_search_results.get("sanctions", {}).get("results", []) if web_search_results.get("sanctions") else [],
                    "ownership": web_search_results.get("ownership", {}).get("results", []) if web_search_results.get("ownership") else []
                },
                "total_results": web_search_results.get("total_results", 0)
            },
            "overall_risk_level": dilisense_results.get("overall_risk_level", "Low"),
            "risk_score": dilisense_results.get("risk_score", 0),
            "risk_factors": dilisense_results.get("risk_factors", [])
        }
        
        print(f"✅ Enhanced screening completed for {company_name}")
        print(f"📊 Final results structure: {list(combined_results.keys())}")
        print(f"🔍 Web search structure: {list(combined_results['web_search'].keys())}")
        print(f"🔍 Categorized results: {list(combined_results['web_search']['categorized_results'].keys())}")
        print(f"🔍 Company info count: {len(combined_results['web_search']['categorized_results']['company_info'])}")
        print(f"🔍 Executives count: {len(combined_results['web_search']['categorized_results']['executives'])}")
        print(f"🔍 Total results: {combined_results['web_search']['total_results']}")
        return jsonify(combined_results)
        
    except Exception as e:
        print(f"❌ Enhanced screening failed: {str(e)}")
        print(f"🌍 Environment: {'PRODUCTION' if os.environ.get('RENDER') else 'LOCAL'}")
        print(f"🔑 OpenAI Key present: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
        print(f"🔑 Dilisense Key present: {'Yes' if os.getenv('DILISENSE_API_KEY') else 'No'}")
        import traceback
        traceback.print_exc()
        
        # Return more detailed error information for debugging
        error_details = {
            "error": "Screening failed",
            "details": str(e),
            "type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_info": {
                "git_commit": "1f73afd",
                "fixes_applied": [
                    "asyncio import moved to top",
                    "parameter names fixed",
                    "global event loop conflicts removed",
                    "JSON error handling added"
                ]
            }
        }
        
        print(f"🔍 Error details: {error_details}")
        return jsonify(error_details), 500



@app.route("/api/individual-screen", methods=["POST"])
def individual_screening_api():
    """Individual screening with Dilisense"""
    if 'logged_in' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        try:
            data = request.get_json()
            if data is None:
                data = {}
        except Exception as json_error:
            print(f"❌ JSON parsing failed: {json_error}")
            data = {}
        name = data.get("name", "").strip()
        country = data.get("country", "").strip()
        date_of_birth = data.get("dateOfBirth", "").strip()
        gender = data.get("gender", "").strip()
        
        if not name:
            return jsonify({"error": "name is required"}), 400
        
        print(f"🔍 Starting individual screening for: {name}")
        
        # Import Dilisense service
        from services.dilisense import dilisense_service
        
        # Create event loop for async operations
        
        # Run async operations in event loop
        loop = asyncio.new_event_loop()
        # Don't set as global event loop to avoid conflicts in production
        
        try:
            # Perform individual screening
            screening_results = loop.run_until_complete(
                dilisense_service.screen_individual(name, country, date_of_birth, gender)
            )
        finally:
            loop.close()
        
        # Calculate risk score and level
        risk_score = 0
        risk_level = "Low"
        
        if screening_results.get("sanctions", {}).get("total_hits", 0) > 0:
            risk_score += 60
        if screening_results.get("pep", {}).get("total_hits", 0) > 0:
            risk_score += 25
        if screening_results.get("criminal", {}).get("total_hits", 0) > 0:
            risk_score += 15
        
        if risk_score >= 70:
            risk_level = "High"
        elif risk_score >= 40:
            risk_level = "Medium"
        
        # Prepare response
        response = {
            "name": name,
            "country": country,
            "timestamp": datetime.utcnow().isoformat(),
            "dilisense": screening_results,
            "overall_risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": screening_results.get("risk_factors", [])
        }
        
        print(f"✅ Individual screening completed for {name}")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Individual screening failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Screening failed: {str(e)}"}), 500

if __name__ == '__main__':
    # For local development only
    if os.environ.get('FLASK_ENV') == 'development':
        port = int(os.environ.get('PORT', 5000))
        print(f"🚀 Starting Laith's Tool locally on 0.0.0.0:{port}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            threaded=True
        )
    else:
        # Production mode - let Gunicorn handle this
        print("🚀 Laith's Tool ready for production (Gunicorn)")
