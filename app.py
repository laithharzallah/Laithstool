"""
Risklytics - Professional Risk Intelligence Platform
A comprehensive due diligence and company screening platform with modern UI
"""

import os
import json
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import logging

# Import services
from services.dilisense import dilisense_service
from services.adapters.dart import dart_adapter
from services.whatsapp_registry import whatsapp_registry_service
from services.gpt5_web_search import gpt5_search_service
from utils.translate import translate_company_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Simple user store (replace with proper auth in production)
USERS = {
    'admin': generate_password_hash('risklytics2024'),
    'demo': generate_password_hash('demo123')
}

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main dashboard"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in USERS and check_password_hash(USERS[username], password):
            session['user'] = username
            session.permanent = True
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# MAIN SCREENING ROUTES
# ============================================================================

@app.route('/company')
@login_required
def company_screening():
    """Company screening interface"""
    return render_template('company_screening.html')

@app.route('/individual')
@login_required
def individual_screening():
    """Individual screening interface"""
    return render_template('individual_screening.html')

@app.route('/dart')
@login_required
def dart_search():
    """DART registry search interface"""
    return render_template('dart_search.html')

@app.route('/whatsapp')
@login_required
def whatsapp_test():
    """WhatsApp registry test interface"""
    whatsapp_available = bool(
        os.getenv("WHATSAPP_PHONE_ID") and 
        os.getenv("WHATSAPP_BEARER")
    )
    return render_template('whatsapp_test.html', whatsapp_available=whatsapp_available)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health')
def health_check():
    """System health check"""
    try:
        # Check OpenAI
        openai_status = "healthy" if os.getenv("OPENAI_API_KEY") else "unhealthy"
        
        # Check Dilisense
        dilisense_status = "healthy" if dilisense_service.enabled else "degraded"
        
        # Check DART
        dart_status = "healthy" if os.getenv("DART_API_KEY") else "degraded"
        
        overall_status = "healthy"
        if openai_status == "unhealthy":
            overall_status = "unhealthy"
        elif dilisense_status == "degraded" or dart_status == "degraded":
            overall_status = "degraded"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "openai": {"status": openai_status},
                "dilisense": {"status": dilisense_status},
                "dart": {"status": dart_status}
            }
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/company/screen', methods=['POST'])
@login_required
def api_company_screen():
    """Company screening API endpoint"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        country = data.get('country', '').strip()
        
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400
        
        logger.info(f"Starting company screening for: {company_name} ({country})")
        
        # Use GPT-5 web search service if available
        if gpt5_search_service:
            result = asyncio.run(gpt5_search_service.screen_company(company_name, country))
        else:
            # Fallback to basic screening
            result = {
                "company_name": company_name,
                "country": country,
                "error": "GPT-5 service not available",
                "timestamp": datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Company screening failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/individual/screen', methods=['POST'])
@login_required
def api_individual_screen():
    """Individual screening API endpoint"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        country = data.get('country', '').strip()
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        logger.info(f"Starting individual screening for: {name} ({country})")
        
        # Screen individual using Dilisense
        if dilisense_service.enabled:
            result = asyncio.run(dilisense_service.screen_individual(name, country))
            result['name'] = name
            result['country'] = country
            result['timestamp'] = datetime.now().isoformat()
        else:
            result = {
                "name": name,
                "country": country,
                "error": "Dilisense service not available",
                "timestamp": datetime.now().isoformat()
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Individual screening failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dart/search', methods=['POST'])
@login_required
def api_dart_search():
    """DART registry search API endpoint"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400
        
        logger.info(f"DART search for: {company_name}")
        
        # Search DART registry
        companies = dart_adapter.search_company(company_name)
        
        # Get detailed info for each company
        for company in companies:
            corp_code = company.get('corp_code')
            if corp_code:
                try:
                    detailed_info = dart_adapter.get_complete_company_info(corp_code)
                    # Translate Korean text to English
                    detailed_info = translate_company_data(detailed_info)
                    company['detailed_info'] = detailed_info
                except Exception as e:
                    logger.warning(f"Failed to get details for {corp_code}: {e}")
        
        return jsonify({
            "companies": companies,
            "total": len(companies),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"DART search failed: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# WHATSAPP WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """WhatsApp webhook endpoint"""
    if request.method == 'GET':
        # Webhook verification
        token = request.args.get('hub.verify_token', '')
        challenge = request.args.get('hub.challenge', '')
        return whatsapp_registry_service.verify_webhook(token, challenge)
    
    elif request.method == 'POST':
        # Handle incoming message
        data = request.get_json()
        return whatsapp_registry_service.handle_inbound_message(data)

@app.route('/simulate', methods=['POST'])
@login_required
def simulate_whatsapp():
    """Simulate WhatsApp message for testing"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        wa_from = data.get('from', '+0000000')
        
        if not text:
            return jsonify({"error": "Message text is required"}), 400
        
        result = whatsapp_registry_service.simulate_message(text, wa_from)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"WhatsApp simulation failed: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ============================================================================
# DEVELOPMENT HELPERS
# ============================================================================

@app.route('/debug')
@login_required
def debug_page():
    """Debug interface for development"""
    return render_template('debug.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Risklytics on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🔑 OpenAI: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"🔍 Dilisense: {'✅' if os.getenv('DILISENSE_API_KEY') else '❌'}")
    print(f"🇰🇷 DART: {'✅' if os.getenv('DART_API_KEY') else '❌'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)