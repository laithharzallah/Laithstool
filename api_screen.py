from flask import Flask, request, jsonify
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from services.gpt5_web_search import gpt5_search_service

app = Flask(__name__)

@app.route('/api/screen', methods=['GET'])
def screen_company():
    """
    Screen a company using GPT-5 web search
    
    Query Parameters:
        company (str): Company name to screen
        country (str, optional): Country/jurisdiction
        
    Returns:
        JSON: Comprehensive due diligence data
    """
    try:
        # Get parameters
        company = request.args.get('company')
        country = request.args.get('country', '')
        
        # Validate required parameters
        if not company:
            return jsonify({
                "error": True,
                "message": "Missing required parameter: company"
            }), 400
        
        # Perform screening (run async function in sync context)
        result = asyncio.run(gpt5_search_service.screen_company(company, country))
        
        # Return results
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Screening failed: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "GPT-5 Due Diligence Screener",
        "version": "1.0",
        "capabilities": [
            "Web search",
            "Executive discovery", 
            "Financial analysis",
            "Sanctions screening",
            "Adverse media monitoring"
        ]
    })

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)