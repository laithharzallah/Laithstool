#!/usr/bin/env python3
"""
Render Deployment Diagnostic Script
Run this on your deployed Render instance to diagnose issues
"""

import os
import sys
import json
from datetime import datetime

def diagnose_render():
    """Comprehensive Render deployment diagnosis"""
    print("🚀 Render Deployment Diagnostic")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print("=" * 60)

    issues = []
    warnings = []

    # 1. Check environment
    print("\n🔍 1. ENVIRONMENT CHECK")
    env_vars = {
        'FLASK_ENV': os.getenv('FLASK_ENV', 'not set'),
        'DART_API_KEY': 'Set' if os.getenv('DART_API_KEY') else 'MISSING',
        'OPENAI_API_KEY': 'Set' if os.getenv('OPENAI_API_KEY') else 'MISSING',
        'SECRET_KEY': 'Set' if os.getenv('SECRET_KEY') else 'MISSING',
        'PORT': os.getenv('PORT', 'not set'),
        'RENDER': os.getenv('RENDER', 'false')
    }

    for var, status in env_vars.items():
        if status in ['MISSING', 'not set']:
            issues.append(f"❌ {var}: {status}")
        else:
            print(f"✅ {var}: {status}")

    # 2. Check file system
    print("\n📁 2. FILE SYSTEM CHECK")
    required_files = [
        'app.py', 'wsgi.py', 'requirements.txt', 'render.yaml',
        'services/adapters/dart.py', 'utils/translate.py',
        'templates/dart_search.html'
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            issues.append(f"❌ Missing file: {file_path}")

    # 3. Check imports
    print("\n📦 3. IMPORT CHECK")
    import_tests = [
        ('flask', 'import flask'),
        ('requests', 'import requests'),
        ('dart_adapter', 'from services.adapters.dart import dart_adapter'),
        ('translate', 'from utils.translate import translate_company_data'),
    ]

    for name, import_stmt in import_tests:
        try:
            if 'from' in import_stmt:
                exec(import_stmt)
            else:
                exec(import_stmt)
            print(f"✅ {name} import successful")
        except Exception as e:
            issues.append(f"❌ {name} import failed: {str(e)}")

    # 4. Check DART API (if key is available)
    print("\n🌐 4. DART API CHECK")
    dart_key = os.getenv('DART_API_KEY')
    if dart_key:
        try:
            import requests
            from datetime import datetime, timedelta

            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            today = datetime.now().strftime('%Y%m%d')

            url = "https://opendart.fss.or.kr/api/list.json"
            params = {
                "crtfc_key": dart_key,
                "corp_name": "삼성전자",
                "bgn_de": three_months_ago,
                "end_de": today,
                "page_no": 1,
                "page_count": 1
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '000':
                    print(f"✅ DART API working - found {len(data.get('list', []))} companies")
                else:
                    issues.append(f"❌ DART API error: {data.get('message')}")
            else:
                issues.append(f"❌ DART API HTTP error: {response.status_code}")

        except Exception as e:
            issues.append(f"❌ DART API test failed: {str(e)}")
    else:
        issues.append("❌ DART_API_KEY not set")

    # 5. Check Flask app
    print("\n🧪 5. FLASK APP CHECK")
    try:
        from app import app
        print("✅ Flask app imported successfully")

        # Test basic functionality
        with app.test_client() as client:
            response = client.get('/healthz')
            if response.status_code == 200:
                health_data = json.loads(response.data)
                print(f"✅ Health check: {health_data.get('status')}")

                # Check for any issues in health data
                if 'issues' in health_data:
                    warnings.extend(health_data['issues'])
            else:
                issues.append(f"❌ Health check failed: {response.status_code}")

    except Exception as e:
        issues.append(f"❌ Flask app failed: {str(e)}")

    # SUMMARY
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if issues:
        print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  {issue}")

    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")

    if not issues and not warnings:
        print("\n✅ ALL CHECKS PASSED!")
        print("   Your Render deployment should be working correctly.")

    print("\n" + "=" * 60)
    print("🔧 TROUBLESHOOTING TIPS:")
    print("=" * 60)

    if any("DART_API_KEY" in issue for issue in issues):
        print("• Set DART_API_KEY in Render Environment Variables")
        print("  Get your key from: https://opendart.fss.or.kr/")

    if any("import failed" in issue for issue in issues):
        print("• Check that requirements.txt is properly installed")
        print("• Verify Python version compatibility")

    if any("HTTP error" in issue for issue in issues):
        print("• Check network connectivity on Render")
        print("• Verify API endpoints are accessible")

    print("• Visit /healthz endpoint for real-time diagnostics")
    print("• Check Render deployment logs for startup errors")

if __name__ == "__main__":
    diagnose_render()
