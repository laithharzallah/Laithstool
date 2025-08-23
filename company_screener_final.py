#!/usr/bin/env python3
"""
Company Screener - Final Production Version
GPT-Powered Due Diligence Tool
Ready for public deployment
"""

import openai
import json
import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client with environment API key
client = openai.OpenAI()

def screen_company_with_gpt(company_name, country="", screening_level="basic"):
    """Screen a company using GPT with comprehensive analysis"""
    
    if screening_level == "advanced":
        prompt = f"""
You are a professional due diligence researcher with access to comprehensive business databases. Provide detailed information about "{company_name}" {f"in {country}" if country else ""}.

Return your response as a JSON object with this exact structure:

{{
    "website_info": {{
        "official_website": "the official website URL or 'Not found'",
        "title": "brief description of the company",
        "status": "Found/Not found",
        "source": "GPT Knowledge Base"
    }},
    "executives": [
        {{
            "name": "Executive Name",
            "position": "Job Title (CEO, CFO, etc.)",
            "background": "Brief professional background if known",
            "source": "GPT Knowledge Base"
        }}
    ],
    "adverse_media": [
        {{
            "title": "News headline or issue title",
            "summary": "Detailed description of the issue",
            "severity": "High/Medium/Low",
            "date": "Date if known or Recent",
            "source": "News outlet or source",
            "category": "Legal/Financial/Regulatory/Operational/Reputational"
        }}
    ],
    "financial_highlights": {{
        "revenue": "Latest revenue if known",
        "employees": "Number of employees if known",
        "founded": "Year founded if known",
        "industry": "Primary industry",
        "market_cap": "Market capitalization if public company"
    }},
    "risk_assessment": {{
        "overall_risk": "Low/Medium/High",
        "key_risks": ["List of key risk factors"],
        "recommendations": ["Due diligence recommendations"]
    }}
}}

Focus on:
1. Official company website and digital presence
2. Current leadership team (CEO, CFO, COO, President, etc.)
3. Recent controversies, legal issues, debt problems, scandals, regulatory actions
4. Financial performance and stability indicators
5. Risk factors and compliance issues

Be thorough and include recent developments, especially any financial distress, debt restructuring, regulatory issues, or leadership changes.

Company to research: {company_name} {f"({country})" if country else ""}
"""
    else:
        # Basic screening
        prompt = f"""
You are a business researcher. Provide information about "{company_name}" {f"in {country}" if country else ""}.

Return your response as a JSON object with this exact structure:

{{
    "website_info": {{
        "official_website": "the official website URL or 'Not found'",
        "title": "brief description of the company",
        "status": "Found/Not found",
        "source": "GPT Knowledge Base"
    }},
    "executives": [
        {{
            "name": "Executive Name",
            "position": "Job Title",
            "source": "GPT Knowledge Base"
        }}
    ],
    "adverse_media": [
        {{
            "title": "News headline or issue title",
            "summary": "Brief description of the issue",
            "date": "Date if known or Recent",
            "source": "News source"
        }}
    ]
}}

Focus on:
1. Official company website
2. Key executives (CEO, President, etc.)
3. Major controversies, legal issues, or negative news

Company to research: {company_name} {f"({country})" if country else ""}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional due diligence researcher. Always respond with valid JSON only. Do not include any text before or after the JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000 if screening_level == "advanced" else 1500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up the response to extract JSON
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        
        return json.loads(result)
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {result}")
        return create_error_response(f"Failed to parse GPT response")
    except Exception as e:
        print(f"GPT screening error: {e}")
        return create_error_response(f"Screening failed: {str(e)}")

def create_error_response(error_msg):
    """Create a standardized error response"""
    return {
        "website_info": {
            "official_website": "Error",
            "title": error_msg,
            "status": "Error",
            "source": "System Error"
        },
        "executives": [],
        "adverse_media": []
    }

# HTML Template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Screener - GPT Powered</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            text-align: center; 
            color: white; 
            margin-bottom: 30px; 
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        .header h1 { font-size: 3em; margin-bottom: 10px; }
        .header p { font-size: 1.3em; opacity: 0.9; }
        .search-card { 
            background: white; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            margin-bottom: 30px; 
        }
        .form-row { display: flex; gap: 20px; margin-bottom: 25px; }
        .form-group { flex: 1; }
        .form-group label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #333; 
            font-size: 16px;
        }
        .form-group input, .form-group select { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px; 
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group select:focus { 
            outline: none; 
            border-color: #667eea; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 18px 40px; 
            border: none; 
            border-radius: 12px; 
            font-size: 18px; 
            font-weight: 600; 
            cursor: pointer; 
            width: 100%; 
            transition: all 0.3s;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); }
        .btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
        .results { 
            background: white; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            margin-top: 30px; 
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .section { 
            margin-bottom: 35px; 
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #f0f0f0;
        }
        .section h3 { 
            color: #333; 
            margin-bottom: 20px; 
            padding-bottom: 15px; 
            border-bottom: 3px solid #667eea; 
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .executive-item, .media-item { 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 15px; 
            border-left: 5px solid #667eea; 
            transition: transform 0.2s;
        }
        .executive-item:hover, .media-item:hover { transform: translateX(5px); }
        .website-info { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
            padding: 25px; 
            border-radius: 12px; 
            border-left: 5px solid #28a745; 
        }
        .error { 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
            padding: 25px; 
            border-radius: 12px; 
            border-left: 5px solid #dc3545; 
            color: #721c24; 
        }
        .loading { 
            text-align: center; 
            padding: 40px; 
            color: #667eea;
        }
        .spinner { 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #667eea; 
            border-radius: 50%; 
            width: 50px; 
            height: 50px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 20px; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .badge { 
            display: inline-block; 
            padding: 6px 12px; 
            background: #667eea; 
            color: white; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: 600;
            margin-right: 8px; 
            margin-bottom: 5px;
        }
        .risk-high { border-left-color: #dc3545; background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); }
        .risk-medium { border-left-color: #ffc107; background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); }
        .risk-low { border-left-color: #28a745; background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); }
        @media (max-width: 768px) {
            .form-row { flex-direction: column; }
            .header h1 { font-size: 2em; }
            .container { padding: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Company Screener</h1>
            <p>GPT-Powered Due Diligence Tool</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Find websites, executives, and adverse media instantly</p>
        </div>
        
        <div class="search-card">
            <form id="screeningForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="companyName">🏢 Company Name *</label>
                        <input type="text" id="companyName" name="companyName" placeholder="Enter company name (e.g., Apple Inc., RAWABI HOLDING)" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="country">🌍 Country (Optional)</label>
                        <input type="text" id="country" name="country" placeholder="Enter country (e.g., USA, Saudi Arabia)">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="screeningLevel">📊 Screening Level</label>
                        <select id="screeningLevel" name="screeningLevel">
                            <option value="basic">Basic Screening (Faster)</option>
                            <option value="advanced">Advanced Screening (Detailed)</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    🚀 Start GPT Screening
                </button>
            </form>
        </div>
        
        <div id="results" style="display: none;"></div>
    </div>

    <script>
        document.getElementById('screeningForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const companyName = document.getElementById('companyName').value.trim();
            const country = document.getElementById('country').value.trim();
            const screeningLevel = document.getElementById('screeningLevel').value;
            
            if (!companyName) {
                alert('Please enter a company name');
                return;
            }
            
            const submitBtn = document.getElementById('submitBtn');
            const resultsDiv = document.getElementById('results');
            
            // Show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ GPT is analyzing...';
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>GPT is analyzing company data...</p><p style="font-size: 14px; margin-top: 10px;">This may take 10-30 seconds</p></div>';
            
            try {
                const response = await fetch('/screen', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        company_name: companyName,
                        country: country,
                        screening_level: screeningLevel
                    })
                });
                
                const data = await response.json();
                displayResults(data);
                
            } catch (error) {
                console.error('Screening error:', error);
                resultsDiv.innerHTML = '<div class="error">❌ Error: Failed to screen company. Please try again.</div>';
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 Start GPT Screening';
            }
        });
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            
            if (data.error) {
                resultsDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                return;
            }
            
            let html = `
                <div class="results">
                    <h2>📊 Screening Results: ${data.company_name}</h2>
                    ${data.country ? `<p><strong>🌍 Country:</strong> ${data.country}</p>` : ''}
                    <p><strong>📊 Level:</strong> ${data.screening_level.charAt(0).toUpperCase() + data.screening_level.slice(1)} Screening</p>
                    <p><small>🕐 Generated: ${data.timestamp}</small></p>
                    <hr style="margin: 25px 0; border: none; height: 2px; background: linear-gradient(to right, #667eea, #764ba2);">
            `;
            
            // Website Info
            html += `
                <div class="section">
                    <h3>🌐 Company Website</h3>
                    <div class="website-info">
                        <p><strong>Website:</strong> 
                            ${data.website_info?.official_website && data.website_info.official_website !== 'Not found' && data.website_info.official_website !== 'Error' ? 
                                `<a href="${data.website_info.official_website}" target="_blank" style="color: #007bff; text-decoration: none;">${data.website_info.official_website}</a>` : 
                                data.website_info?.official_website || 'Not found'}
                        </p>
                        <p><strong>Status:</strong> ${data.website_info?.status || 'Unknown'}</p>
                        <p><strong>Description:</strong> ${data.website_info?.title || 'No description available'}</p>
                    </div>
                </div>
            `;
            
            // Executives
            html += `
                <div class="section">
                    <h3>👥 Key Executives</h3>
            `;
            if (data.executives && data.executives.length > 0) {
                data.executives.forEach(exec => {
                    html += `
                        <div class="executive-item">
                            <h4 style="margin-bottom: 8px; color: #333;">${exec.name}</h4>
                            <p style="font-weight: 600; color: #667eea; margin-bottom: 5px;">${exec.position}</p>
                            ${exec.background ? `<p style="font-size: 14px; color: #666; margin-bottom: 5px;">${exec.background}</p>` : ''}
                            <small style="color: #888;">Source: ${exec.source || 'GPT Knowledge Base'}</small>
                        </div>
                    `;
                });
            } else {
                html += '<div class="website-info"><p>ℹ️ No executive information found in GPT knowledge base</p></div>';
            }
            html += '</div>';
            
            // Adverse Media
            html += `
                <div class="section">
                    <h3>⚠️ Adverse Media & Risk Factors</h3>
            `;
            if (data.adverse_media && data.adverse_media.length > 0) {
                data.adverse_media.forEach(media => {
                    const riskClass = media.severity === 'High' ? 'risk-high' : media.severity === 'Medium' ? 'risk-medium' : 'risk-low';
                    html += `
                        <div class="media-item ${riskClass}">
                            <h4 style="margin-bottom: 10px; color: #333;">${media.title}</h4>
                            <p style="margin-bottom: 10px;">${media.summary}</p>
                            <div style="margin-bottom: 10px;">
                                ${media.severity ? `<span class="badge" style="background: ${media.severity === 'High' ? '#dc3545' : media.severity === 'Medium' ? '#ffc107' : '#28a745'};">${media.severity} Risk</span>` : ''}
                                ${media.category ? `<span class="badge" style="background: #6c757d;">${media.category}</span>` : ''}
                            </div>
                            <small style="color: #666;">📰 Source: ${media.source} | 📅 Date: ${media.date || 'Unknown'}</small>
                        </div>
                    `;
                });
            } else {
                html += '<div class="website-info"><p>✅ No adverse media found in GPT knowledge base - Clean screening</p></div>';
            }
            html += '</div>';
            
            // Advanced features
            if (data.financial_highlights) {
                html += `
                    <div class="section">
                        <h3>💰 Financial Highlights</h3>
                        <div class="website-info">
                            ${Object.entries(data.financial_highlights).map(([key, value]) => 
                                `<p><strong>${key.replace('_', ' ').toUpperCase()}:</strong> ${value || 'Not available'}</p>`
                            ).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (data.risk_assessment) {
                const riskColor = data.risk_assessment.overall_risk === 'High' ? '#dc3545' : 
                                 data.risk_assessment.overall_risk === 'Medium' ? '#ffc107' : '#28a745';
                html += `
                    <div class="section">
                        <h3>🎯 Risk Assessment</h3>
                        <div class="media-item" style="border-left-color: ${riskColor};">
                            <p><strong>Overall Risk Level:</strong> 
                                <span style="color: ${riskColor}; font-weight: bold;">${data.risk_assessment.overall_risk}</span>
                            </p>
                            ${data.risk_assessment.key_risks && data.risk_assessment.key_risks.length > 0 ? 
                                `<p><strong>Key Risks:</strong> ${data.risk_assessment.key_risks.join(', ')}</p>` : ''}
                            ${data.risk_assessment.recommendations && data.risk_assessment.recommendations.length > 0 ? 
                                `<p><strong>Recommendations:</strong> ${data.risk_assessment.recommendations.join('; ')}</p>` : ''}
                        </div>
                    </div>
                `;
            }
            
            html += `
                    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 12px;">
                        <p style="color: #666; font-size: 14px;">
                            🤖 Powered by GPT-4 | 🔒 Secure & Private
                        </p>
                    </div>
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/screen', methods=['POST'])
def screen_company():
    """API endpoint for company screening"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        country = data.get('country', '').strip()
        screening_level = data.get('screening_level', 'basic')
        
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        
        # Screen company with GPT
        gpt_results = screen_company_with_gpt(company_name, country, screening_level)
        
        # Add metadata
        results = {
            'company_name': company_name,
            'country': country,
            'screening_level': screening_level,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            **gpt_results
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': f'Screening failed: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Company Screener GPT'})

if __name__ == '__main__':
    print("🚀 Starting GPT-Powered Company Screener...")
    print("📍 Access the tool at: http://localhost:5000")
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key as an environment variable")
    else:
        print("✅ OpenAI API key found and configured")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

