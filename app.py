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

@app.route('/api/dart_lookup', methods=['POST'])
def api_dart_lookup():
    """API endpoint for DART registry lookup"""
    try:
        data = request.json
        company = data.get('company')
        registry_id = data.get('registry_id')
        
        # Log the request
        app.logger.info(f"DART lookup request: {company} (ID: {registry_id})")
        
        # Generate simulated response
        result = generate_simulated_dart_lookup_result(company, registry_id)
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400

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
