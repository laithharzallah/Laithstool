"""
Implementation for DART Registry API
"""
import random
from datetime import datetime, timedelta
from flask import jsonify, request

def setup_dart_registry_api(app):
    """Set up the DART Registry API routes"""
    
    @app.route('/api/dart_lookup', methods=['POST'])
    def api_dart_lookup():
        """API endpoint for DART Registry lookup"""
        try:
            data = request.json
            company = data.get('company')
            country = data.get('country')
            registry_id = data.get('registry_id')
            
            # Log the request
            app.logger.info(f"DART lookup request: {company} ({registry_id})")
            
            # Generate simulated response
            result = generate_simulated_dart_lookup_result(company, country, registry_id)
            
            return jsonify(result)
                
        except Exception as e:
            app.logger.error(f"API error: {str(e)}")
            return jsonify({
                "error": "Invalid request",
                "details": str(e),
                "status": "error"
            }), 400

def generate_simulated_dart_lookup_result(company, country, registry_id):
    """Generate a simulated DART Registry lookup result for testing"""
    # Generate random dates within the last 20 years
    def random_date():
        days = random.randint(0, 365 * 20)
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Generate random registration date
    registration_date = random_date()
    
    # Generate random industry code and name
    industry_codes = {
        "10100": "Agriculture",
        "20100": "Mining",
        "30100": "Manufacturing",
        "40100": "Technology",
        "50100": "Finance",
        "60100": "Healthcare",
        "70100": "Retail",
        "80100": "Energy"
    }
    industry_code = random.choice(list(industry_codes.keys()))
    industry_name = industry_codes[industry_code]
    
    # Generate random address based on country
    address = f"{random.randint(1, 999)} Test Street, "
    if country.lower() == "korea" or country.lower() == "south korea":
        cities = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"]
        address += f"{random.choice(cities)}, South Korea"
    else:
        address += f"City, {country}"
    
    # Generate random representative name
    first_names = ["Kim", "Lee", "Park", "Choi", "Jung"]
    last_names = ["Min-ho", "Ji-woo", "Seo-yeon", "Jun-ho", "Hye-jin"]
    if country.lower() == "korea" or country.lower() == "south korea":
        representative = f"{random.choice(first_names)} {random.choice(last_names)}"
    else:
        representative = f"John Smith"
    
    # Generate random capital amount
    capital_amount = random.randint(10000, 1000000) * 1000
    if country.lower() == "korea" or country.lower() == "south korea":
        capital = f"{capital_amount:,} KRW"
    else:
        capital = f"${capital_amount/1000:,.0f},000 USD"
    
    # Generate random documents
    documents = []
    current_year = datetime.now().year
    for year in range(current_year - 3, current_year + 1):
        # Annual report
        documents.append({
            "id": f"DOC{len(documents) + 1:03d}",
            "title": f"Annual Report {year}",
            "date": f"{year}-03-{random.randint(10, 28)}",
            "url": f"https://dart.example.com/doc/{registry_id}/annual_{year}"
        })
        
        # Quarterly reports
        for quarter in range(1, 5):
            month = 3 * quarter
            documents.append({
                "id": f"DOC{len(documents) + 1:03d}",
                "title": f"Quarterly Report Q{quarter} {year}",
                "date": f"{year}-{month:02d}-{random.randint(10, 28)}",
                "url": f"https://dart.example.com/doc/{registry_id}/q{quarter}_{year}"
            })
    
    # Create the result object
    result = {
        "company_name": company,
        "country": country,
        "registry_id": registry_id,
        "registration_date": registration_date,
        "status": "Active",
        "industry_code": industry_code,
        "industry_name": industry_name,
        "address": address,
        "representative": representative,
        "capital": capital,
        "documents": documents,
        "financial_summary": {
            "currency": "KRW" if country.lower() == "korea" or country.lower() == "south korea" else "USD",
            "revenue": {
                str(current_year - 2): random.randint(10000, 50000) * 1000000,
                str(current_year - 1): random.randint(10000, 50000) * 1000000,
                str(current_year): random.randint(10000, 50000) * 1000000
            },
            "profit": {
                str(current_year - 2): random.randint(1000, 5000) * 1000000,
                str(current_year - 1): random.randint(1000, 5000) * 1000000,
                str(current_year): random.randint(1000, 5000) * 1000000
            },
            "assets": {
                str(current_year - 2): random.randint(50000, 200000) * 1000000,
                str(current_year - 1): random.randint(50000, 200000) * 1000000,
                str(current_year): random.randint(50000, 200000) * 1000000
            }
        }
    }
    
    return result
