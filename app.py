"""
Enhanced TPRM Tool with Professional JSON Visualization
"""
import os
import json
import asyncio
import threading
import concurrent.futures
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure sessions work by setting a secret key
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-dev")
if app.secret_key == "change-me-in-dev":
    import logging as _logging
    _logging.getLogger(__name__).warning("SECRET_KEY not set; using default for development")

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)

# Setup API routes
@app.route('/api/screen', methods=['POST'])
def api_screen():
    """API endpoint for company screening (Google CSE + OpenAI backed).

    Feature flag: ENHANCED_SCREENING=1 returns normalized CompanyScreening in
    addition to legacy fields (non-breaking).
    """
    try:
        from utils.validation import (
            validate_company_name, validate_country, validate_domain, 
            validate_screening_level, ValidationError, sanitize_output
        )
        
        data = request.json or {}
        
        # Validate inputs
        try:
            company = validate_company_name(data.get('company'))
            country = validate_country(data.get('country'))
            domain = validate_domain(data.get('domain'))
            level = validate_screening_level(data.get('level'))
        except ValidationError as ve:
            return jsonify({"error": str(ve), "status": "validation_error"}), 400

        app.logger.info(f"Company screening request: {company} ({country})")

        # Check cache first
        from utils.cache import cached, CACHE_TTL
        cache_key = f"company_screen:{company}:{country}:{domain}:{level}"
        
        @cached(ttl_seconds=CACHE_TTL['company_screening'])
        def get_cached_result(comp, ctry, dom):
            # This function will be cached
            return None  # Return None to indicate cache miss
        
        # Try cache (we'll implement actual caching in the service layer)
        # For now, proceed with the real-time search service
        
        # Use the real-time search service (uses Google CSE when keys set, and OpenAI for structuring)
        from services.real_time_search import real_time_search_service
        try:
            # Use thread-safe event loop handling for production
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                # We're in an existing event loop (e.g., Jupyter, some WSGI servers)
                
                result = None
                exception = None
                
                def run_in_thread():
                    nonlocal result, exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(
                                real_time_search_service.comprehensive_search(company=company, country=country, domain=domain)
                            )
                        finally:
                            new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if exception:
                    raise exception
                web = result or {"categorized_results": {}, "error": "Timeout"}
            else:
                # No existing event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    web = loop.run_until_complete(
                        real_time_search_service.comprehensive_search(company=company, country=country, domain=domain)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
        except Exception as se:
            app.logger.error(f"Real-time search failed: {se}")
            # Fall back to simulation data if real search fails
            if os.getenv('USE_SIMULATION', 'false').lower() == 'true':
                return jsonify(generate_simulated_company_result(company, country, domain, level))
            web = {"categorized_results": {}, "error": str(se)}

        cat = (web or {}).get('categorized_results') or {}
        ci = (cat.get('company_info') or {})
        ex = (cat.get('executives') or [])
        am = (cat.get('adverse_media') or [])
        sanc = (cat.get('sanctions') or {})
        fin = (cat.get('financials') or {})

        website = ci.get('website') if isinstance(ci, dict) else None
        industry = ci.get('industry') if isinstance(ci, dict) else None
        founded_year = ci.get('founded_year') if isinstance(ci, dict) else None
        # Best-effort headquarters extraction
        headquarters = None
        if isinstance(ci, dict):
            headquarters = (
                ci.get('headquarters')
                or ci.get('hq')
                or ci.get('headquarters_location')
                or ci.get('location')
                or ci.get('address')
            )

        # Executives mapping
        execs = []
        for it in (ex if isinstance(ex, list) else []):
            execs.append({
                "name": it.get("name"),
                "position": it.get("position") or "Executive",
                "risk_level": "Low"
            })

        # Metrics and simple risk derivation
        sanctions_flag = 1 if any(v for v in (sanc or {}).values() if v) else 0
        adverse_count = len(am if isinstance(am, list) else [])
        alerts = sanctions_flag + (1 if adverse_count > 0 else 0)
        overall = "Low"
        if sanctions_flag or adverse_count >= 6:
            overall = "High"
        elif adverse_count > 0:
            overall = "Medium"

        # Normalize adverse media and derive citations
        citations = []
        adverse_media_norm = []
        for it in (am if isinstance(am, list) else [])[:25]:
            title = it.get('headline') or it.get('title') or 'Source'
            url = it.get('source_url') or it.get('url')
            if title and url:
                citations.append({
                    "title": title,
                    "url": url
                })
            adverse_media_norm.append({
                "title": title,
                "date": it.get('published_date') or it.get('date'),
                "summary": it.get('summary') or it.get('snippet') or it.get('description'),
                "url": url
            })

        # Executive summary and risk assessment (brief)
        executive_summary = f"{company} screening completed. Website: {website or 'N/A'}. " \
                             f"Executives: {len(execs)}. Adverse media: {adverse_count}."
        risk_assessment = (
            f"Overall risk is {overall.lower()} based on {adverse_count} adverse media"
            f"{', sanctions present' if sanctions_flag else ''}."
        )

        result = {
            "company_name": company,
            "country": country,
            "domain": domain or website,
            "overall_risk_level": overall,
            "industry": industry,
            "founded_year": founded_year,
            "headquarters": headquarters,
            "executives": execs,
            "metrics": {
                "sanctions": sanctions_flag,
                "adverse_media": adverse_count,
                "alerts": alerts
            },
            "adverse_media": adverse_media_norm,
            "citations": citations,
            "executive_summary": executive_summary,
            "risk_assessment": risk_assessment,
            "website": website,
            "timestamp": datetime.now().isoformat(),
            "real_data": cat
        }

        # Attach diagnostics so you can verify real providers used
        result["_providers"] = (web or {}).get("metadata", {}).get("providers_used")
        result["_search_timestamp"] = (web or {}).get("metadata", {}).get("search_timestamp")
        result["_errors"] = web.get("error") if isinstance(web, dict) else None

        # Enhanced normalized output (feature-flagged)
        enhanced = os.getenv('ENHANCED_SCREENING', '').strip() == '1'
        if enhanced:
            try:
                from services.search.news_search import search_news
                from services.nlp.news_summarize import summarize_and_classify
                from services.normalize.company_merge import normalize_company
                news = search_news(f"{company} {country} adverse news", max_results=20)
                summary = summarize_and_classify(news)
                normalized = normalize_company(
                    name=company,
                    country=country,
                    website=website,
                    executives=execs,
                    ownership=[],
                    news_items=summary.get('items', []),
                    news_summary=summary.get('summary', ''),
                    sources=(web or {}).get('metadata', {}).get('providers_used', []),
                    cache_hit=False,
                    feature_flags={
                        'enhanced': True,
                    },
                )
                result['normalized'] = normalized
            except Exception as _e:
                app.logger.warning(f"Enhanced screening disabled: {_e}")

        # Sanitize output before sending to frontend
        return jsonify(sanitize_output(result))

    except Exception as e:
        app.logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An error occurred processing your request",
            "status": "error",
            "request_id": datetime.now().isoformat()
        }), 500

@app.route('/api/screen_individual', methods=['POST'])
def api_screen_individual():
    """API endpoint for individual screening (Dilisense-backed)."""
    try:
        from utils.validation import (
            validate_person_name, validate_country, validate_date_of_birth,
            validate_screening_level, ValidationError, sanitize_output
        )
        
        data = request.get_json(force=True, silent=True) or {}
        
        # Validate inputs
        try:
            name = validate_person_name(data.get('name'))
            country = validate_country(data.get('country'))
            date_of_birth = validate_date_of_birth(data.get('date_of_birth'))
            level = validate_screening_level(data.get('level'))
        except ValidationError as ve:
            return jsonify({"error": str(ve), "status": "validation_error"}), 400

        app.logger.info(f"Individual screening request: {name} ({country})")

        # Call Dilisense asynchronously with safe loop handling
        from services.dilisense import dilisense_service
        try:
            # Use thread-safe event loop handling for production
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                # We're in an existing event loop
                
                result = None
                exception = None
                
                def run_in_thread():
                    nonlocal result, exception
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(
                                dilisense_service.screen_individual(name, country, date_of_birth)
                            )
                        finally:
                            new_loop.close()
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if exception:
                    raise exception
                dil = result or {}
            else:
                # No existing event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    dil = loop.run_until_complete(
                        dilisense_service.screen_individual(name, country, date_of_birth)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
        except Exception as se:
            app.logger.error(f"Dilisense screening failed: {se}")
            # Fall back to simulation data if real search fails
            if os.getenv('USE_SIMULATION', 'false').lower() == 'true':
                return jsonify(generate_simulated_individual_result(name, country, date_of_birth, level))
            return jsonify({"error": "Screening service temporarily unavailable", "status": "error"}), 503

        # Map to legacy-friendly structure used by UI
        sanctions_hits = int(((dil or {}).get('sanctions') or {}).get('total_hits', 0))
        pep_hits = int(((dil or {}).get('pep') or {}).get('total_hits', 0))
        criminal_hits = int(((dil or {}).get('criminal') or {}).get('total_hits', 0))
        total_hits = int(dil.get('total_hits', sanctions_hits + pep_hits + criminal_hits)) if isinstance(dil, dict) else 0
        overall = (dil or {}).get('overall_risk_level') or (
            'High' if sanctions_hits > 0 or criminal_hits > 0 else 'Medium' if pep_hits > 0 else 'Low')

        # Extract PEP details from Dilisense response
        pep_details = None
        if pep_hits > 0 and isinstance(dil, dict):
            pep_data = dil.get('pep', {})
            if isinstance(pep_data, dict) and pep_data.get('items'):
                # Get the first PEP entry for details
                first_pep = pep_data['items'][0] if isinstance(pep_data['items'], list) else {}
                pep_details = {
                    "position": first_pep.get('position', 'Political Position'),
                    "country": first_pep.get('country', country or 'Unknown'),
                    "since": first_pep.get('since', first_pep.get('start_date', 'Unknown')),
                    "source": first_pep.get('source', 'Dilisense'),
                    "level": first_pep.get('level', 'Senior'),
                    "description": first_pep.get('description', ''),
                    "end_date": first_pep.get('end_date', ''),
                    "reason": first_pep.get('reason', 'Political exposure')
                }

        executive_summary = f"{name} is an individual based in {country or 'Unknown'}. "
        if pep_hits > 0 and pep_details:
            executive_summary += f"Identified as a Politically Exposed Person ({pep_details['position']}). "
        executive_summary += f"Total matches: {total_hits}. Risk: {overall.lower()}."
        
        risk_assessment = "; ".join((dil or {}).get('risk_factors', [])) or (
            'Sanctions listed' if sanctions_hits else 'No significant risk factors identified'
        )

        response = {
            "name": name,
            "country": country,
            "date_of_birth": date_of_birth or None,
            "overall_risk_level": overall,
            "pep_status": pep_hits > 0,
            "pep_details": pep_details,
            "aliases": dil.get('aliases', []) if isinstance(dil, dict) else [],
            "metrics": {
                "sanctions": sanctions_hits,
                "adverse_media": int(((dil or {}).get('other') or {}).get('total_hits', 0)),
                "pep": pep_hits,
            },
            "citations": [],
            "executive_summary": executive_summary,
            "risk_assessment": risk_assessment,
            "timestamp": datetime.now().isoformat(),
            "raw": dil,
        }

        # Sanitize output before sending to frontend
        return jsonify(sanitize_output(response))

    except Exception as e:
        app.logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An error occurred processing your request",
            "status": "error",
            "request_id": datetime.now().isoformat()
        }), 500

@app.route('/api/dart_lookup', methods=['POST'])
def api_dart_lookup():
    """API endpoint for DART registry lookup (now using live DART)."""
    try:
        from utils.validation import validate_company_name, ValidationError, sanitize_output
        
        payload = request.get_json(force=True, silent=True) or {}
        
        # Validate inputs
        try:
            company = validate_company_name(payload.get('company'))
        except ValidationError as ve:
            return jsonify({"error": str(ve), "status": "validation_error"}), 400

        from services.adapters.dart import dart_adapter
        companies = dart_adapter.search_company(company)
        if not companies:
            return jsonify({"error": "No DART results found"}), 404

        first = companies[0]
        corp_code = first.get('corp_code')
        detailed = {}
        if corp_code:
            try:
                detailed = dart_adapter.get_complete_company_info(corp_code)
            except Exception:
                detailed = {}

        basic = (detailed or {}).get('basic_info') or {}
        # Map to UI fields expected by enhanced_dart_registry
        result = {
            "company_name": basic.get('corp_name') or first.get('name') or company,
            "registry_id": corp_code or '',
            "status": "Active",
            "industry_code": None,
            "industry_name": None,
            "registration_date": basic.get('est_dt'),
            "address": basic.get('adr'),
            "representative": basic.get('ceo_nm'),
            "capital": None,
            "major_shareholders": detailed.get('shareholders', []),
            "subsidiaries": [],
            "financial_summary": {
                "currency": None,
                "revenue": {},
                "profit": {},
                "assets": {}
            },
            "documents": [],
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(sanitize_output(result))
    except Exception as e:
        app.logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An error occurred processing your request", 
            "status": "error",
            "request_id": datetime.now().isoformat()
        }), 500

# --- Real DART search endpoint (uses services.adapters.dart) ---
@app.route('/api/dart/search', methods=['POST'])
def api_dart_search():
    try:
        data = request.get_json(force=True, silent=True) or {}
        company_name = (data.get('company') or data.get('company_name') or '').strip()
        if not company_name:
            return jsonify({"error": "company is required"}), 400

        from services.adapters.dart import dart_adapter
        companies = dart_adapter.search_company(company_name)

        # Optionally fetch detailed info for the first 1-2 companies
        detailed = []
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            max_items = min(2, len(companies))
            with ThreadPoolExecutor(max_workers=max_items) as pool:
                fut_map = {}
                for c in companies[:max_items]:
                    cc = c.get('corp_code')
                    if not cc:
                        detailed.append(c)
                        continue
                    fut = pool.submit(dart_adapter.get_complete_company_info, cc)
                    fut_map[fut] = c
                for fut in as_completed(fut_map, timeout=8):
                    base = fut_map[fut]
                    try:
                        info = fut.result(timeout=2)
                        if info and 'error' not in info:
                            base['detailed_info'] = info
                    except Exception:
                        pass
                    detailed.append(base)
        except Exception:
            detailed = companies[:3]

        return jsonify({
            "success": True,
            "companies": detailed or companies,
            "total_results": len(companies)
        })
    except Exception as e:
        return jsonify({"error": f"DART search failed: {e}"}), 500

# Setup web routes
@app.route('/')
def index():
    """Home page - Dashboard"""
    return render_template('dashboard.html')

@app.route('/enhanced/company_screening')
def enhanced_company_screening():
    """Enhanced company screening page"""
    return render_template('enhanced_company_screening.html')

@app.route('/enhanced/individual_screening')
def enhanced_individual_screening():
    """Enhanced individual screening page"""
    return render_template('enhanced_individual_screening.html')

@app.route('/enhanced/dart_registry')
def enhanced_dart_registry():
    """Enhanced DART registry page"""
    return render_template('enhanced_dart_registry.html')

# Diagnostics to verify providers/keys presence live
@app.route('/debug/providers', methods=['GET'])
def debug_providers():
    try:
        from services.real_time_search import real_time_search_service as rt
        info = {
            "OPENAI": bool(os.getenv("OPENAI_API_KEY")),
            "SERPER": bool(os.getenv("SERPER_API_KEY")),
            "GOOGLE_API": bool(os.getenv("GOOGLE_API_KEY")),
            "GOOGLE_CSE_ID": bool(os.getenv("GOOGLE_CSE_ID")),
            "DART_API_KEY": bool(os.getenv("DART_API_KEY")),
            "providers": getattr(rt, "search_providers", []),
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/status/<request_id>', methods=['GET'])
def api_status(request_id):
    """Get status of a long-running request"""
    # For now, return a simple status
    # In production, this would check actual job status
    return jsonify({
        "request_id": request_id,
        "status": "completed",
        "progress": 100,
        "message": "Request completed"
    })


@app.route('/api/cache/stats', methods=['GET'])
def api_cache_stats():
    """Get cache statistics"""
    from utils.cache import get_cache_stats
    return jsonify(get_cache_stats())

def generate_simulated_company_result(company, country, domain, level):
    """Generate a simulated company screening result for testing"""
    import random
    from datetime import datetime, timedelta
    
    # Generate random risk level
    risk_levels = ["Low", "Medium", "High"]
    risk_weights = [0.5, 0.3, 0.2]
    overall_risk_level = random.choices(risk_levels, weights=risk_weights)[0]
    
    # Generate random industry
    industries = ["Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Energy", "Real Estate"]
    industry = random.choice(industries)
    
    # Generate random founded year
    founded_year = str(random.randint(1950, 2020))
    
    # Generate random executives
    executive_count = random.randint(3, 10)
    executives = []
    positions = ["CEO", "CFO", "COO", "CTO", "CMO", "Director", "President", "VP"]
    
    for i in range(executive_count):
        risk_level = random.choices(risk_levels, weights=[0.6, 0.3, 0.1])[0]
        executives.append({
            "name": f"Executive {i}",
            "position": random.choice(positions),
            "risk_level": risk_level,
            "source_url": f"https://example.com/executive/{i}" if i < 2 else None
        })
    
    # Generate random metrics
    sanctions = random.randint(0, 2) if overall_risk_level == "High" else 0
    adverse_media = random.randint(0, 10)
    alerts = random.randint(0, 20)
    
    # Generate random citations
    citation_count = random.randint(5, 15)
    citations = []
    for i in range(citation_count):
        citations.append({
            "title": f"Citation {i+1}",
            "url": f"https://example.com/citation/{i+1}"
        })
    
    # Generate executive summary
    executive_summary = f"{company} is a {industry.lower()} company based in {country or 'Unknown'}. "
    executive_summary += f"The company has an overall {overall_risk_level.lower()} risk profile. "
    
    if sanctions > 0:
        executive_summary += f"There are {sanctions} active sanctions against the company. "
    else:
        executive_summary += "No sanctions were found. "
        
    if adverse_media > 0:
        executive_summary += f"There are {adverse_media} adverse media mentions. "
    else:
        executive_summary += "No adverse media was found. "
    
    high_risk_execs = sum(1 for exec in executives if exec["risk_level"] == "High")
    medium_risk_execs = sum(1 for exec in executives if exec["risk_level"] == "Medium")
    
    if high_risk_execs > 0:
        executive_summary += f"{high_risk_execs} executives have a high risk profile. "
    if medium_risk_execs > 0:
        executive_summary += f"{medium_risk_execs} executives have a medium risk profile. "
    
    # Generate risk assessment
    risk_assessment = f"Based on our analysis, {company} presents a {overall_risk_level.lower()} risk. "
    
    if overall_risk_level == "High":
        risk_assessment += "The high risk assessment is primarily due to "
        factors = []
        if sanctions > 0:
            factors.append(f"active sanctions ({sanctions})")
        if adverse_media > 5:
            factors.append(f"significant adverse media coverage ({adverse_media} mentions)")
        if high_risk_execs > 0:
            factors.append(f"high-risk executives ({high_risk_execs})")
        risk_assessment += ", ".join(factors) + ". "
        risk_assessment += "Enhanced due diligence and ongoing monitoring are strongly recommended."
    elif overall_risk_level == "Medium":
        risk_assessment += "The medium risk assessment is based on "
        factors = []
        if adverse_media > 0:
            factors.append(f"some adverse media coverage ({adverse_media} mentions)")
        if medium_risk_execs > 0:
            factors.append(f"executives with medium risk profiles ({medium_risk_execs})")
        if not factors:
            factors.append("general industry and geographic risk factors")
        risk_assessment += ", ".join(factors) + ". "
        risk_assessment += "Standard due diligence and regular monitoring are recommended."
    else:
        risk_assessment += "The low risk assessment indicates no significant risk factors were identified. "
        risk_assessment += "Standard due diligence is recommended."
    
    # Create the result object
    result = {
        "company_name": company,
        "country": country,
        "domain": domain,
        "overall_risk_level": overall_risk_level,
        "industry": industry,
        "founded_year": founded_year,
        "executives": executives,
        "metrics": {
            "sanctions": sanctions,
            "adverse_media": adverse_media,
            "alerts": alerts
        },
        "citations": citations,
        "executive_summary": executive_summary,
        "risk_assessment": risk_assessment,
        "timestamp": datetime.now().isoformat()
    }
    
    return result

def generate_simulated_individual_result(name, country, date_of_birth, level):
    """Generate a simulated individual screening result for testing"""
    import random
    from datetime import datetime, timedelta
    
    # Generate random risk level
    risk_levels = ["Low", "Medium", "High"]
    risk_weights = [0.5, 0.3, 0.2]
    overall_risk_level = random.choices(risk_levels, weights=risk_weights)[0]
    
    # Generate random PEP status
    pep_status = random.random() < 0.3  # 30% chance of being a PEP
    
    # Generate PEP details if applicable
    pep_details = None
    if pep_status:
        positions = ["Senator", "Minister", "Ambassador", "Judge", "Central Bank Official"]
        sources = ["World-Check", "Dow Jones", "LexisNexis", "Internal Research"]
        years = list(range(2010, 2025))
        
        pep_details = {
            "position": random.choice(positions),
            "country": country or "Unknown",
            "since": str(random.choice(years)),
            "source": random.choice(sources)
        }
    
    # Generate random aliases
    alias_count = random.randint(0, 3)
    aliases = []
    for i in range(alias_count):
        aliases.append(f"Alias {i+1} of {name}")
    
    # Generate random metrics
    sanctions = random.randint(0, 2) if overall_risk_level == "High" else 0
    adverse_media = random.randint(0, 10)
    pep_score = random.random() if pep_status else 0
    
    # Generate random citations
    citation_count = random.randint(3, 10)
    citations = []
    for i in range(citation_count):
        citations.append({
            "title": f"Citation {i+1}",
            "url": f"https://example.com/citation/{i+1}"
        })
    
    # Generate executive summary
    executive_summary = f"{name} is an individual based in {country or 'Unknown'}. "
    executive_summary += f"The individual has an overall {overall_risk_level.lower()} risk profile. "
    
    if pep_status:
        executive_summary += f"The individual is identified as a Politically Exposed Person ({pep_details['position']} in {pep_details['country']} since {pep_details['since']}). "
    else:
        executive_summary += "The individual is not identified as a Politically Exposed Person. "
        
    if sanctions > 0:
        executive_summary += f"There are {sanctions} active sanctions against the individual. "
    else:
        executive_summary += "No sanctions were found. "
        
    if adverse_media > 0:
        executive_summary += f"There are {adverse_media} adverse media mentions. "
    else:
        executive_summary += "No adverse media was found. "
    
    # Generate risk assessment
    risk_assessment = f"Based on our analysis, {name} presents a {overall_risk_level.lower()} risk. "
    
    if overall_risk_level == "High":
        risk_assessment += "The high risk assessment is primarily due to "
        factors = []
        if sanctions > 0:
            factors.append(f"active sanctions ({sanctions})")
        if adverse_media > 5:
            factors.append(f"significant adverse media coverage ({adverse_media} mentions)")
        if pep_status:
            factors.append(f"PEP status ({pep_details['position']})")
        risk_assessment += ", ".join(factors) + ". "
        risk_assessment += "Enhanced due diligence and ongoing monitoring are strongly recommended."
    elif overall_risk_level == "Medium":
        risk_assessment += "The medium risk assessment is based on "
        factors = []
        if adverse_media > 0:
            factors.append(f"some adverse media coverage ({adverse_media} mentions)")
        if pep_status:
            factors.append(f"PEP status ({pep_details['position']})")
        if not factors:
            factors.append("general risk factors")
        risk_assessment += ", ".join(factors) + ". "
        risk_assessment += "Standard due diligence and regular monitoring are recommended."
    else:
        risk_assessment += "The low risk assessment indicates no significant risk factors were identified. "
        risk_assessment += "Standard due diligence is recommended."
    
    # Create the result object
    result = {
        "name": name,
        "country": country,
        "date_of_birth": date_of_birth,
        "overall_risk_level": overall_risk_level,
        "pep_status": pep_status,
        "pep_details": pep_details,
        "aliases": aliases,
        "metrics": {
            "sanctions": sanctions,
            "adverse_media": adverse_media,
            "pep": pep_score
        },
        "citations": citations,
        "executive_summary": executive_summary,
        "risk_assessment": risk_assessment,
        "timestamp": datetime.now().isoformat()
    }
    
    return result

def generate_simulated_dart_lookup_result(company, registry_id):
    """Generate a simulated DART registry lookup result for testing"""
    import random
    from datetime import datetime, timedelta
    
    # Generate random registry ID if not provided
    if not registry_id:
        registry_id = f"KR{random.randint(10000, 99999)}"
    
    # Generate random industry
    industries = [
        {"code": "60100", "name": "Healthcare"},
        {"code": "70200", "name": "Technology"},
        {"code": "80300", "name": "Finance"},
        {"code": "90400", "name": "Manufacturing"},
        {"code": "10500", "name": "Energy"}
    ]
    industry = random.choice(industries)
    
    # Generate random registration date
    year = random.randint(2010, 2020)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    registration_date = f"{year}-{month:02d}-{day:02d}"
    
    # Generate random address
    addresses = [
        "123 Main Street, Seoul, South Korea",
        "456 Business Avenue, Busan, South Korea",
        "789 Corporate Plaza, Incheon, South Korea",
        "321 Industry Road, Daegu, South Korea",
        "654 Commerce Street, Daejeon, South Korea"
    ]
    address = random.choice(addresses)
    
    # Generate random representative
    representatives = [
        "Kim Min-jun",
        "Lee Ji-woo",
        "Park Seo-yeon",
        "Choi Joon-ho",
        "Jung Hye-jin"
    ]
    representative = random.choice(representatives)
    
    # Generate random capital
    capital = random.randint(10000, 500000) * 1000
    
    # Generate random major shareholders
    shareholder_count = random.randint(2, 5)
    major_shareholders = []
    shareholder_names = ["SK Holdings", "Samsung Group", "LG Corporation", "Hyundai Motor Group", "POSCO", "Lotte Group", "Hanwha Group"]
    relationships = ["Parent Company", "Institutional Investor", "Individual Investor", "Strategic Partner"]
    
    total_ownership = 0
    for i in range(shareholder_count):
        ownership_percent = random.randint(5, 30)
        if i == shareholder_count - 1:
            ownership_percent = 100 - total_ownership
        else:
            total_ownership += ownership_percent
            if total_ownership >= 95:
                break
        
        major_shareholders.append({
            "name": random.choice(shareholder_names),
            "ownership": f"{ownership_percent}%",
            "relationship": random.choice(relationships)
        })
    
    # Generate random subsidiaries
    subsidiary_count = random.randint(0, 4)
    subsidiaries = []
    subsidiary_names = [f"{company} {suffix}" for suffix in ["Biotech", "Electronics", "Logistics", "R&D", "Services", "Solutions"]]
    businesses = ["Research", "Manufacturing", "Distribution", "Services", "Development"]
    
    for i in range(subsidiary_count):
        subsidiaries.append({
            "name": random.choice(subsidiary_names),
            "ownership": f"{random.randint(51, 100)}%",
            "business": random.choice(businesses)
        })
    
    # Generate random financial summary
    years = [str(year) for year in range(2023, 2026)]
    financial_summary = {
        "currency": "KRW",
        "revenue": {},
        "profit": {},
        "assets": {}
    }
    
    base_revenue = random.randint(10000, 50000) * 1000000
    base_profit = int(base_revenue * random.uniform(0.05, 0.15))
    base_assets = int(base_revenue * random.uniform(1.5, 2.5))
    
    for year in years:
        revenue_factor = random.uniform(0.9, 1.2)
        profit_factor = random.uniform(0.8, 1.3)
        assets_factor = random.uniform(0.95, 1.1)
        
        financial_summary["revenue"][year] = int(base_revenue * revenue_factor)
        financial_summary["profit"][year] = int(base_profit * profit_factor)
        financial_summary["assets"][year] = int(base_assets * assets_factor)
        
        base_revenue = financial_summary["revenue"][year]
        base_profit = financial_summary["profit"][year]
        base_assets = financial_summary["assets"][year]
    
    # Generate random documents
    document_count = random.randint(10, 20)
    documents = []
    document_types = ["Annual Report", "Quarterly Report", "Audit Report", "Corporate Disclosure", "Regulatory Filing"]
    
    for i in range(document_count):
        doc_year = random.choice(years)
        doc_quarter = random.choice(["Q1", "Q2", "Q3", "Q4"]) if "Quarterly" in document_types[i % len(document_types)] else ""
        doc_date = f"{doc_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        doc_title = f"{document_types[i % len(document_types)]}"
        if doc_quarter:
            doc_title += f" {doc_quarter}"
        doc_title += f" {doc_year}"
        
        documents.append({
            "id": f"DOC{i+1:03d}",
            "title": doc_title,
            "date": doc_date,
            "url": f"https://dart.example.com/doc/{registry_id}/{doc_year.lower()}_{doc_quarter.lower() if doc_quarter else 'annual'}"
        })
    
    # Sort documents by date
    documents.sort(key=lambda x: x["date"], reverse=True)
    
    # Create the result object
    result = {
        "company_name": company,
        "registry_id": registry_id,
        "status": "Active",
        "industry_code": industry["code"],
        "industry_name": industry["name"],
        "registration_date": registration_date,
        "address": address,
        "representative": representative,
        "capital": f"{capital:,} KRW",
        "major_shareholders": major_shareholders,
        "subsidiaries": subsidiaries,
        "financial_summary": financial_summary,
        "documents": documents,
        "timestamp": datetime.now().isoformat()
    }
    
    return result

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
