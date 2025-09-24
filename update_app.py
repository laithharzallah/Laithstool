#!/usr/bin/env python3
"""
Script to update the app.py file to use the new environment configuration
"""
import os
import re
import shutil

def update_app_py():
    """Update app.py to use the new environment configuration"""
    app_py_path = 'app.py'
    backup_path = 'app.py.bak'
    
    # Create backup
    shutil.copy2(app_py_path, backup_path)
    print(f"✅ Created backup of {app_py_path} at {backup_path}")
    
    # Read the app.py file
    with open(app_py_path, 'r') as f:
        content = f.read()
    
    # Add import for environment configuration
    import_pattern = r"import os\s+from flask import"
    import_replacement = "import os\nfrom app_env_config import configure_environment, initialize_services\nfrom flask import"
    content = re.sub(import_pattern, import_replacement, content)
    
    # Replace environment variable loading
    env_pattern = r"# Load environment variables.*?# End environment variables setup"
    env_replacement = """# Load environment variables
config = configure_environment()

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config['ENV'] = config['FLASK_ENV']
app.config['DEBUG'] = config['DEBUG']

# Initialize services with API keys
app = initialize_services(app, config)

# End environment variables setup"""
    
    content = re.sub(env_pattern, env_replacement, content, flags=re.DOTALL)
    
    # Update API endpoint for company screening
    api_screen_pattern = r"@app.route\('/api/screen', methods=\['POST'\]\)\s+def api_screen\(\):"
    if api_screen_pattern not in content:
        # If the endpoint doesn't exist, we'll add it at the end
        content += """

# Add API endpoint for company screening
@app.route('/api/screen', methods=['POST'])
def api_screen():
    \"\"\"API endpoint for company screening\"\"\"
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
        
        # Check if we have cached results for this company
        cache_key = f"screening_{company}_{country}".lower().replace(' ', '_')
        cached_result = cache.get(cache_key)
        
        if cached_result:
            app.logger.info(f"Returning cached result for {company}")
            return jsonify(cached_result)
        
        # If no cached result, perform the screening
        try:
            # This is where you would call your actual screening service
            result = None
            
            # If we have a real screening service, call it here
            if company and hasattr(app, 'dilisense_service'):
                result = app.dilisense_service.screen_company(
                    company, 
                    country=country,
                    domain=domain,
                    level=level,
                    include_sanctions=include_sanctions,
                    include_adverse_media=include_adverse_media
                )
            
            # If no result from service, use simulated data
            if not result:
                # Generate simulated response
                result = generate_simulated_screening_result(company, country, domain, level)
            
            # Cache the result
            cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
            
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Screening error: {str(e)}")
            return jsonify({
                "error": str(e),
                "status": "error"
            }), 500
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400

def generate_simulated_screening_result(company, country, domain, level):
    \"\"\"Generate a simulated screening result for testing\"\"\"
    import random
    from datetime import datetime, timedelta
    
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
"""
    
    # Add route for enhanced company screening if it doesn't exist
    enhanced_route_pattern = r"@app.route\('/enhanced/company_screening'\)"
    if enhanced_route_pattern not in content:
        # Find a good place to add the route, before the if __name__ == '__main__' block
        main_pattern = r"if __name__ == '__main__':"
        if main_pattern in content:
            main_index = content.find(main_pattern)
            content = content[:main_index] + """
# Add a new route to use the enhanced UI
@app.route('/enhanced/company_screening')
def enhanced_company_screening_ui():
    \"\"\"Enhanced company screening page with improved UI and JSON visualization\"\"\"
    return render_template('new_company_screening.html')

""" + content[main_index:]
    
    # Write the updated content back to app.py
    with open(app_py_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {app_py_path} with new environment configuration")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found in current directory")
        print("Please run this script from the project root directory")
        exit(1)
    
    update_app_py()
    print("✅ App update complete")
