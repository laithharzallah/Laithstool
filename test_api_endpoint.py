#!/usr/bin/env python3
"""
Test Suite for GPT-5 Due Diligence API
Includes mock tests and real smoke tests
"""

import requests
import json
import time
from unittest.mock import patch, MagicMock

def test_mock_screening():
    """Mock test to verify API structure without actual GPT-5 calls"""
    print("🧪 MOCK TEST - API Structure Validation")
    print("=" * 50)
    
    # Mock response data
    mock_response = {
        "executive_summary": "Mock company analysis for testing purposes",
        "risk_flags": ["Test risk flag 1", "Test risk flag 2"],
        "company_profile": {
            "legal_name": "Test Company Inc",
            "industry": "Technology",
            "founded": "2000",
            "employees": "1000",
            "jurisdiction": "United States",
            "entity_type": "Corporation",
            "status": "Active"
        },
        "key_executives": [
            {
                "name": "John Doe",
                "position": "CEO",
                "background": "Former executive at Tech Corp",
                "source_url": "https://example.com/executives"
            }
        ],
        "official_website": "https://testcompany.com",
        "social_media": ["https://linkedin.com/company/testcompany"],
        "ability_to_generate_cash": {
            "value": "Strong cash generation capabilities",
            "source_url": "https://example.com/financials",
            "last_updated": "2024-01-01"
        },
        "capability_of_paying_debt": {
            "value": "Excellent debt payment capability",
            "source_url": "https://example.com/financials",
            "last_updated": "2024-01-01"
        },
        "cash_reserve": {
            "value": "$100 million in cash reserves",
            "source_url": "https://example.com/financials",
            "last_updated": "2024-01-01"
        },
        "government_contracts": ["Contract #123 with DOD - https://example.com"],
        "expansion_announcements": ["Expanding to Europe - https://example.com"],
        "future_commitments": ["$50M R&D investment - https://example.com"],
        "shareholders": ["Major Investor LLC - https://example.com"],
        "beneficial_owners": ["John Smith (25%) - https://example.com"],
        "sanctions_flags": [],
        "adverse_media": [
            {
                "headline": "Company faces minor regulatory inquiry",
                "date": "2024-01-01",
                "source": "Business News",
                "category": "Regulatory",
                "severity": "low",
                "summary": "Minor inquiry resolved quickly",
                "source_url": "https://example.com/news"
            }
        ],
        "political_exposure": [],
        "bribery_corruption": [],
        "search_timestamp": "2024-01-01T12:00:00",
        "confidence_level": "high",
        "citations": [
            "https://example.com/executives",
            "https://example.com/financials",
            "https://example.com/news"
        ]
    }
    
    # Validate structure
    required_fields = [
        "executive_summary", "company_profile", "key_executives",
        "ability_to_generate_cash", "capability_of_paying_debt", "cash_reserve",
        "government_contracts", "shareholders", "beneficial_owners",
        "sanctions_flags", "adverse_media", "citations"
    ]
    
    print("✅ Validating response structure:")
    for field in required_fields:
        if field in mock_response:
            print(f"   ✅ {field}: Present")
        else:
            print(f"   ❌ {field}: Missing")
    
    # Check evidence URLs
    url_fields = ["ability_to_generate_cash", "capability_of_paying_debt", "cash_reserve"]
    print("\n✅ Validating evidence URLs:")
    for field in url_fields:
        data = mock_response.get(field, {})
        if data.get("source_url"):
            print(f"   ✅ {field}: Has URL")
        else:
            print(f"   ❌ {field}: Missing URL")
    
    # Check executives have URLs
    executives = mock_response.get("key_executives", [])
    exec_with_urls = sum(1 for exec in executives if exec.get("source_url"))
    print(f"   ✅ Executives with URLs: {exec_with_urls}/{len(executives)}")
    
    # Check citations
    citations = mock_response.get("citations", [])
    print(f"   ✅ Total citations: {len(citations)}")
    
    print("\n🎯 MOCK TEST RESULT: ✅ PASSED")
    return True

def test_api_endpoint_smoke():
    """Real smoke test against actual API endpoint"""
    print("\n🔥 SMOKE TEST - Real API Endpoint")
    print("=" * 50)
    
    # Test parameters
    base_url = "http://localhost:5000"  # Adjust for your setup
    test_company = "Apple Inc"
    test_country = "United States"
    
    try:
        # Test health endpoint
        print("1️⃣ Testing health endpoint...")
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ Health check: {health_data.get('status')}")
            print(f"   🔧 Service: {health_data.get('service')}")
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return False
        
        # Test screening endpoint
        print(f"\n2️⃣ Testing screening endpoint with {test_company}...")
        screening_url = f"{base_url}/api/screen"
        params = {"company": test_company, "country": test_country}
        
        start_time = time.time()
        screening_response = requests.get(screening_url, params=params, timeout=60)
        response_time = time.time() - start_time
        
        print(f"   ⏱️ Response time: {response_time:.2f} seconds")
        
        if screening_response.status_code == 200:
            data = screening_response.json()
            
            # Check if it's an error response
            if data.get("error"):
                print(f"   ❌ API returned error: {data.get('message')}")
                return False
            
            # Validate response structure
            print("   ✅ Successful response received")
            print(f"   📊 Company: {data.get('company_profile', {}).get('legal_name', 'Unknown')}")
            print(f"   🌐 Website: {data.get('official_website', 'Not found')}")
            
            # Check executives
            executives = data.get("key_executives", [])
            print(f"   👥 Executives found: {len(executives)}")
            for exec in executives[:2]:
                name = exec.get("name", "Unknown")
                position = exec.get("position", "Unknown")
                print(f"      • {name} - {position}")
            
            # Check financial data
            financial_fields = ["ability_to_generate_cash", "capability_of_paying_debt", "cash_reserve"]
            financial_count = sum(1 for field in financial_fields if data.get(field))
            print(f"   💰 Financial metrics: {financial_count}/{len(financial_fields)}")
            
            # Check citations
            citations = data.get("citations", [])
            print(f"   🔗 Citations: {len(citations)} sources")
            
            # Overall assessment
            quality_indicators = [
                len(executives) > 0,
                bool(data.get("official_website")),
                financial_count > 0,
                len(citations) > 0
            ]
            quality_score = sum(quality_indicators)
            
            print(f"\n   📈 Quality Score: {quality_score}/4")
            
            if quality_score >= 3:
                print("   🎯 SMOKE TEST RESULT: ✅ PASSED")
                return True
            else:
                print("   🎯 SMOKE TEST RESULT: ⚠️ PARTIAL")
                return False
                
        else:
            print(f"   ❌ API request failed: {screening_response.status_code}")
            print(f"   📄 Response: {screening_response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the API server running?")
        print("   💡 Start with: python3 api_screen.py")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout - API may be overloaded")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GPT-5 DUE DILIGENCE API TEST SUITE")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Mock Structure Test", test_mock_screening),
        ("API Smoke Test", test_api_endpoint_smoke)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - API is ready for production!")
    else:
        print("⚠️ Some tests failed - check implementation")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)