"""
Implementation for Individual Screening API
"""
import random
from datetime import datetime, timedelta
from flask import jsonify, request

def setup_individual_screening_api(app):
    """Set up the individual screening API routes"""
    
    @app.route('/api/screen_individual', methods=['POST'])
    def api_screen_individual():
        """API endpoint for individual screening"""
        try:
            data = request.json
            name = data.get('name')
            country = data.get('country')
            date_of_birth = data.get('date_of_birth')
            level = data.get('level', 'standard')
            include_sanctions = data.get('include_sanctions', True)
            include_adverse_media = data.get('include_adverse_media', True)
            
            # Log the request
            app.logger.info(f"Individual screening request: {name} ({country})")
            
            # Generate simulated response
            result = generate_simulated_individual_screening_result(name, country, date_of_birth, level)
            
            return jsonify(result)
                
        except Exception as e:
            app.logger.error(f"API error: {str(e)}")
            return jsonify({
                "error": "Invalid request",
                "details": str(e),
                "status": "error"
            }), 400

def generate_simulated_individual_screening_result(name, country, date_of_birth, level):
    """Generate a simulated individual screening result for testing"""
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
    
    # Generate aliases
    aliases = []
    if random.random() > 0.6:
        for i in range(random.randint(1, 3)):
            aliases.append(f"{name.split()[0]} {chr(65+i)}. {name.split()[-1]}")
    
    # Generate sanctions
    sanctions = []
    if random.random() > 0.7:
        for i in range(random.randint(1, 3)):
            sanctions.append({
                "list_name": random.choice(["OFAC", "EU Sanctions", "UN Sanctions", "UK Sanctions"]),
                "entity_name": name,
                "date": random_date(),
                "source_url": f"https://example.com/sanctions/{i}" if random.random() > 0.3 else None
            })
    
    # Generate adverse media
    adverse_media = []
    if random.random() > 0.5:
        for i in range(random.randint(1, 5)):
            adverse_media.append({
                "title": f"Potential issue involving {name}",
                "source": random.choice(["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal"]),
                "date": random_date(),
                "url": f"https://example.com/news/{i}" if random.random() > 0.3 else None
            })
    
    # Generate PEP status
    pep_status = random.random() > 0.8
    pep_details = None
    if pep_status:
        pep_details = {
            "position": random.choice(["Minister", "Ambassador", "Senator", "Governor", "Mayor"]),
            "country": country,
            "since": str(random.randint(2000, 2023)),
            "source": random.choice(["Global PEP Database", "National Registry", "Official Website"])
        }
    
    # Generate citations
    citations = []
    for i in range(random.randint(3, 10)):
        citations.append({
            "title": f"Reference {i+1}",
            "url": f"https://example.com/reference/{i}"
        })
    
    # Create the result object
    result = {
        "name": name,
        "country": country,
        "date_of_birth": date_of_birth,
        "screening_level": level,
        "timestamp": datetime.now().isoformat(),
        "overall_risk_level": risk_level_text,
        "executive_summary": f"Individual screening completed for {name}. " +
                            f"The overall risk level is {risk_level_text.lower()}. " +
                            f"Found {len(sanctions)} sanctions, {len(adverse_media)} adverse media items, " +
                            f"and {'PEP status identified' if pep_status else 'no PEP status'}.",
        "aliases": aliases,
        "pep_status": pep_status,
        "pep_details": pep_details,
        "sanctions": sanctions,
        "adverse_media": adverse_media,
        "citations": citations,
        "risk_assessment": f"Based on our analysis, {name} presents a {risk_level_text.lower()} risk profile. " +
                          "This assessment is based on various factors including sanctions screening, " +
                          "adverse media analysis, and PEP status.",
        "metrics": {
            "overall_risk": risk_value,
            "sanctions": random.uniform(0, 0.5) if sanctions else 0,
            "pep": random.uniform(0, 0.8) if pep_status else 0,
            "adverse_media": random.uniform(0, 0.7) if adverse_media else 0,
            "matches": random.randint(5, 50),
            "alerts": len(sanctions) + len(adverse_media) + (1 if pep_status else 0)
        }
    }
    
    return result
