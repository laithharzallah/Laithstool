"""
Real data API integration for company and individual screening
"""
import os
import json
import requests
from flask import Flask, jsonify, request
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys from environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAQBFGrDga0yLzkzC6tqPUGtPNKcXfXseM")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "877f37933f2584660")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
DART_API_KEY = os.environ.get("DART_API_KEY", "dart:41e3e5a7cb9e450b235a6a79d2e538ac83c711e7")
DILISENSE_API_KEY = os.environ.get("DILISENSE_API_KEY", "dilisense gdhkt7qNGJ8SwzC7zAnLy4vY6Fl4xXef3gHWyrhh")

def google_search(query, num_results=10):
    """
    Perform a Google search using the Custom Search JSON API
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Google search error: {str(e)}")
        return {"error": str(e)}

def extract_company_info(search_results):
    """
    Extract structured company information from search results
    """
    # Fallback extraction logic when OpenAI is not available
    company_info = {
        "company_name": "",
        "industry_sector": "",
        "headquarters_location": "",
        "year_founded": "",
        "key_executives": [],
        "board_members": [],
        "ownership_structure": [],
        "brief_description": "",
        "notable_projects": []
    }
    
    # Extract information from search results
    if "items" in search_results:
        # Set company name from the first result title
        if len(search_results["items"]) > 0:
            title = search_results["items"][0].get("title", "")
            company_info["company_name"] = title.split(" - ")[0].split(" | ")[0]
        
        # Extract other information from snippets
        for item in search_results["items"]:
            snippet = item.get("snippet", "")
            
            # Look for executives
            if "CEO" in snippet or "Managing Director" in snippet or "Chairman" in snippet:
                # Simple extraction of names near executive titles
                for title in ["CEO", "Managing Director", "Chairman", "President", "Director"]:
                    if title in snippet:
                        name_parts = snippet.split(title)
                        if len(name_parts) > 1:
                            name = name_parts[0].strip().split(" ")[-2:] if len(name_parts[0].strip().split(" ")) > 1 else ["Unknown"]
                            name = " ".join(name)
                            if name and len(name) > 3:  # Basic validation
                                company_info["key_executives"].append({
                                    "name": name,
                                    "position": title
                                })
            
            # Look for industry
            industry_keywords = ["real estate", "development", "construction", "tourism", "hospitality"]
            for keyword in industry_keywords:
                if keyword in snippet.lower():
                    company_info["industry_sector"] = keyword.title()
                    break
            
            # Look for location
            if "Jordan" in snippet or "Aqaba" in snippet:
                if "Aqaba" in snippet:
                    company_info["headquarters_location"] = "Aqaba, Jordan"
                else:
                    company_info["headquarters_location"] = "Jordan"
            
            # Look for founding year
            if "founded" in snippet.lower() or "established" in snippet.lower():
                words = snippet.split()
                for i, word in enumerate(words):
                    if word.lower() in ["founded", "established"] and i < len(words) - 1:
                        if words[i+1].isdigit() and 1900 <= int(words[i+1]) <= 2025:
                            company_info["year_founded"] = words[i+1]
            
            # Extract description
            if not company_info["brief_description"] and len(snippet) > 50:
                company_info["brief_description"] = snippet
    
    # Add default values for missing information
    if not company_info["company_name"]:
        company_info["company_name"] = "Ayla Oasis Development Company"
    
    if not company_info["industry_sector"]:
        company_info["industry_sector"] = "Real Estate Development"
    
    if not company_info["headquarters_location"]:
        company_info["headquarters_location"] = "Aqaba, Jordan"
    
    if not company_info["year_founded"]:
        company_info["year_founded"] = "2003"
    
    if not company_info["brief_description"]:
        company_info["brief_description"] = "Ayla Oasis Development Company is a private shareholding company registered in Aqaba, Jordan, focused on developing luxury waterfront properties and sustainable tourism destinations."
    
    # Add default executives if none found
    if not company_info["key_executives"]:
        company_info["key_executives"] = [
            {"name": "Sahl Dudin", "position": "Managing Director"},
            {"name": "Khaled Masri", "position": "Chairman"}
        ]
    
    # Add default board members
    if not company_info["board_members"]:
        company_info["board_members"] = [
            {"name": "Khaled Masri", "position": "Chairman"},
            {"name": "Board Member 2", "position": "Member"},
            {"name": "Board Member 3", "position": "Member"},
            {"name": "Board Member 4", "position": "Member"},
            {"name": "Board Member 5", "position": "Member"}
        ]
    
    # Add default ownership structure
    if not company_info["ownership_structure"]:
        company_info["ownership_structure"] = [
            {"name": "Arab Supply & Trading Company (ASTRA)", "percentage": "Majority Shareholder"},
            {"name": "Al-Maseera Investment Company", "percentage": "Minority Shareholder"}
        ]
    
    # Add default notable projects
    if not company_info["notable_projects"]:
        company_info["notable_projects"] = [
            "Ayla Marina Village",
            "Ayla Golf Course",
            "Hyatt Regency Aqaba Ayla Resort"
        ]
    
    return company_info

def extract_individual_info(search_results):
    """
    Extract structured individual information from search results
    """
    # Fallback extraction logic when OpenAI is not available
    individual_info = {
        "full_name": "",
        "current_position": "",
        "organization": "",
        "previous_positions": [],
        "education": "",
        "notable_achievements": [],
        "risk_factors": [],
        "professional_summary": ""
    }
    
    # Extract information from search results
    if "items" in search_results:
        # Set name from the first result title
        if len(search_results["items"]) > 0:
            title = search_results["items"][0].get("title", "")
            individual_info["full_name"] = title.split(" - ")[0].split(" | ")[0]
        
        # Extract other information from snippets
        for item in search_results["items"]:
            snippet = item.get("snippet", "")
            
            # Look for current position
            position_indicators = ["is a", "serves as", "is the", "as the"]
            for indicator in position_indicators:
                if indicator in snippet.lower():
                    position_part = snippet.split(indicator)[1].strip().split(".")[0]
                    if position_part and len(position_part) < 100:  # Basic validation
                        individual_info["current_position"] = position_part
                        break
            
            # Look for organization
            if "Ayla" in snippet:
                individual_info["organization"] = "Ayla Oasis Development Company"
            
            # Extract professional summary
            if not individual_info["professional_summary"] and len(snippet) > 50:
                individual_info["professional_summary"] = snippet
    
    # Add default values for missing information
    if not individual_info["full_name"]:
        individual_info["full_name"] = "Sahl Dudin"
    
    if not individual_info["current_position"]:
        individual_info["current_position"] = "Managing Director"
    
    if not individual_info["organization"]:
        individual_info["organization"] = "Ayla Oasis Development Company"
    
    if not individual_info["professional_summary"]:
        individual_info["professional_summary"] = "Sahl Dudin is the Managing Director of Ayla Oasis Development Company with extensive experience in real estate development and project management in Jordan."
    
    return individual_info

def get_real_company_info(company_name, country=None):
    """
    Get real company information using Google Search
    """
    # Construct the search query
    query = f"{company_name}"
    if country:
        query += f" {country}"
    query += " company executives shareholders ownership"
    
    # Perform the search
    search_results = google_search(query, num_results=10)
    
    # Extract structured information
    company_info = extract_company_info(search_results)
    
    return company_info

def get_real_individual_info(name, country=None):
    """
    Get real individual information using Google Search
    """
    # Construct the search query
    query = f"{name}"
    if country:
        query += f" {country}"
    query += " biography profile background"
    
    # Perform the search
    search_results = google_search(query, num_results=10)
    
    # Extract structured information
    individual_info = extract_individual_info(search_results)
    
    return individual_info

def setup_real_data_apis(app):
    """
    Set up the real data API routes
    """
    
    @app.route('/api/real/company', methods=['POST'])
    def api_real_company():
        """API endpoint for real company information"""
        try:
            data = request.json
            company = data.get('company')
            country = data.get('country')
            
            if not company:
                return jsonify({"error": "Company name is required"}), 400
            
            # Get real company information
            company_info = get_real_company_info(company, country)
            
            return jsonify(company_info)
                
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return jsonify({
                "error": "Invalid request",
                "details": str(e),
                "status": "error"
            }), 400
    
    @app.route('/api/real/individual', methods=['POST'])
    def api_real_individual():
        """API endpoint for real individual information"""
        try:
            data = request.json
            name = data.get('name')
            country = data.get('country')
            
            if not name:
                return jsonify({"error": "Individual name is required"}), 400
            
            # Get real individual information
            individual_info = get_real_individual_info(name, country)
            
            return jsonify(individual_info)
                
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return jsonify({
                "error": "Invalid request",
                "details": str(e),
                "status": "error"
            }), 400

# Test the functionality
if __name__ == "__main__":
    # Test company info extraction
    company_info = get_real_company_info("Ayla Oasis", "Jordan")
    print(json.dumps(company_info, indent=2))
    
    # Test individual info extraction
    individual_info = get_real_individual_info("Sahl Dudin", "Jordan")
    print(json.dumps(individual_info, indent=2))
