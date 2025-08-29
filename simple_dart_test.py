#!/usr/bin/env python3
"""
Simple DART test to isolate issues
"""

import os
import sys
import requests

# Test DART API directly
DART_API_KEY = os.getenv("DART_API_KEY")
if not DART_API_KEY:
    print("❌ DART_API_KEY not set")
    sys.exit(1)

print("🔍 Testing DART API directly...")

# Test company search
url = "https://opendart.fss.or.kr/api/list.json"
params = {
    "crtfc_key": DART_API_KEY,
    "corp_name": "삼성전자",
    "bgn_de": "20240601",  # 3 months ago
    "end_de": "20240830",  # today
    "page_no": 1,
    "page_count": 5
}

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"Message: {data.get('message', 'No message')}")
        print(f"Companies found: {len(data.get('list', []))}")

        if data.get('list'):
            first_company = data['list'][0]
            print(f"First company: {first_company.get('corp_name')} ({first_company.get('corp_code')})")
        else:
            print("No companies in response")
    else:
        print(f"HTTP Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Request failed: {e}")

print("✅ Direct API test completed")
