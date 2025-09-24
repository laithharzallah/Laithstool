"""
Enhanced TPRM Tool with Professional JSON Visualization
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import API implementations
from dart_registry_api import setup_dart_registry_api, generate_simulated_dart_lookup_result

app = Flask(__name__)

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)

# Setup API routes
@app.route('/api/screen', methods=['POST'])
def api_screen():
    """API endpoint for company screening"""
    try:
        data = request.json
        company = data.get('company')
        country = data.get('country')
        domain = data.get('domain')
        level = data.get('level', 'standard')
        
        # Log the request
        app.logger.info(f"Company screening request: {company} ({country})")
        
        # Generate simulated response
        result = generate_simulated_company_result(company, country, domain, level)
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400

@app.route('/api/screen_individual', methods=['POST'])
def api_screen_individual():
    """API endpoint for individual screening"""
    try:
        data = request.json
        name = data.get('name')
        country = data.get('country')
        date_of_birth = data.get('date_of_birth')
        level = data.get('level', 'standard')
        
        # Log the request
        app.logger.info(f"Individual screening request: {name} ({country})")
        
        # Generate simulated response
        result = generate_simulated_individual_result(name, country, date_of_birth, level)
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400

# Setup DART Registry API
setup_dart_registry_api(app)

# Setup web routes
@app.route('/')
def index():
    """Home page"""
    return redirect(url_for('enhanced_company_screening'))

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, host='0.0.0.0', port=port)
