#!/usr/bin/env python3
"""
Simple script to run the Flask application with minimal configuration
"""
import os
import sys
from flask import Flask, render_template, jsonify, request
import random
from datetime import datetime, timedelta
import logging

# Import the API implementations
from individual_screening_api import setup_individual_screening_api
from dart_registry_api import setup_dart_registry_api

# Set environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['PUBLIC_APIS'] = '1'  # Allow public API access for testing

# Create a simple Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Set a secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')

# Route for the enhanced company screening UI
@app.route('/enhanced/company_screening')
def enhanced_company_screening():
    """Enhanced company screening page with improved UI and JSON visualization"""
    return render_template('fixed_company_screening.html')

# API endpoint for company screening
@app.route('/api/screen', methods=['POST'])
def api_screen():
    """API endpoint for company screening"""
    try:
        data = request.json
        company = data.get('company')
        country = data.get('country')
        domain = data.get('domain')
        level = data.get('level', 'standard')
        include_sanctions = data.get('include_sanctions', True)
        include_adverse_media = data.get('include_adverse_media', True)
        
        # Log the request
        app.logger.info(f"Screening request: {company} ({country})")
        
        # Generate simulated response
        result = generate_simulated_screening_result(company, country, domain, level)
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400

def generate_simulated_screening_result(company, country, domain, level):
    """Generate a simulated screening result for testing"""
    # Base risk levels based on screening level
    risk_levels = {
        'standard': random.uniform(0.1, 0.4),
        'enhanced': random.uniform(0.3, 0.6),
        'comprehensive': random.uniform(0.4, 0.8)
    }
    
    # Determine overall risk level text
    risk_value = risk_levels.get(level, 0.3)
    if risk_value < 0.3:
        risk_level_text = "Low"
    elif risk_value < 0.6:
        risk_level_text = "Medium"
    else:
        risk_level_text = "High"
    
    # Generate random dates within the last 5 years
    def random_date():
        days = random.randint(0, 365 * 5)
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Generate executives
    executive_titles = ["CEO", "CFO", "CTO", "COO", "CIO", "CHRO", "CMO", "President", "Vice President", "Director"]
    executives = []
    for i in range(random.randint(3, 8)):
        executives.append({
            "name": f"Executive {i+1}",
            "position": random.choice(executive_titles),
            "risk_level": random.choice(["Low", "Medium", "High"]) if random.random() > 0.7 else "Low",
            "source_url": f"https://example.com/executive/{i}" if random.random() > 0.5 else None
        })
    
    # Generate sanctions
    sanctions = []
    if random.random() > 0.7:
        for i in range(random.randint(1, 3)):
            sanctions.append({
                "list_name": random.choice(["OFAC", "EU Sanctions", "UN Sanctions", "UK Sanctions"]),
                "entity_name": company,
                "date": random_date(),
                "source_url": f"https://example.com/sanctions/{i}" if random.random() > 0.3 else None
            })
    
    # Generate adverse media
    adverse_media = []
    if random.random() > 0.5:
        for i in range(random.randint(1, 5)):
            adverse_media.append({
                "title": f"Potential issue with {company}",
                "source": random.choice(["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal"]),
                "date": random_date(),
                "url": f"https://example.com/news/{i}" if random.random() > 0.3 else None
            })
    
    # Generate citations
    citations = []
    for i in range(random.randint(3, 10)):
        citations.append({
            "title": f"Reference {i+1}",
            "url": f"https://example.com/reference/{i}"
        })
    
    # Create the result object
    result = {
        "company_name": company,
        "country": country,
        "domain": domain or f"www.{company.lower().replace(' ', '')}.com",
        "screening_level": level,
        "timestamp": datetime.now().isoformat(),
        "overall_risk_level": risk_level_text,
        "executive_summary": f"Company screening completed for {company}. " +
                            f"The overall risk level is {risk_level_text.lower()}. " +
                            f"Found {len(sanctions)} sanctions, {len(adverse_media)} adverse media items, and {len(executives)} key executives.",
        "company_profile": f"{company} is a company based in {country or 'unknown location'}. " +
                          "This is a simulated company profile for demonstration purposes.",
        "business_activities": "The company engages in various business activities across multiple sectors. " +
                              "This is simulated data for demonstration purposes.",
        "founded_year": str(random.randint(1950, 2020)),
        "headquarters": country or "Unknown",
        "industry": random.choice(["Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Energy"]),
        "legal_form": random.choice(["Corporation", "LLC", "Partnership", "Sole Proprietorship"]),
        "registration_number": f"REG{random.randint(10000, 99999)}",
        "website": domain or f"https://www.{company.lower().replace(' ', '')}.com",
        "jurisdictions": [country] if country else [],
        "executives": executives,
        "sanctions": sanctions,
        "adverse_media": adverse_media,
        "citations": citations,
        "risk_assessment": f"Based on our analysis, {company} presents a {risk_level_text.lower()} risk profile. " +
                          "This assessment is based on various factors including sanctions screening, " +
                          "adverse media analysis, and executive background checks.",
        "metrics": {
            "overall_risk": risk_value,
            "sanctions": random.uniform(0, 0.5) if sanctions else 0,
            "pep": random.uniform(0, 0.6) if random.random() > 0.7 else 0,
            "adverse_media": random.uniform(0, 0.7) if adverse_media else 0,
            "matches": random.randint(5, 50),
            "alerts": len(sanctions) + len(adverse_media)
        }
    }
    
    return result

# Set up the Individual Screening API
setup_individual_screening_api(app)

# Set up the DART Registry API
setup_dart_registry_api(app)

if __name__ == "__main__":
    print("🚀 Starting simplified Flask application with all APIs...")
    app.run(host='0.0.0.0', port=5001, debug=True)
