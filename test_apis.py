#!/usr/bin/env python3
"""
Test script to verify all APIs in the Risklytics application
"""
import requests
import json
import time
import sys

# Base URL for the API
BASE_URL = "http://localhost:5001"

def test_company_screening_api():
    """Test the company screening API"""
    print("\n🔍 Testing Company Screening API...")
    
    # Test data
    data = {
        "company": "Test Corporation",
        "country": "United States",
        "domain": "testcorp.com",
        "level": "standard",
        "include_sanctions": True,
        "include_adverse_media": True
    }
    
    # Make the API request
    try:
        response = requests.post(f"{BASE_URL}/api/screen", json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("✅ Company Screening API: SUCCESS")
            print(f"   - Company: {result.get('company_name')}")
            print(f"   - Risk Level: {result.get('overall_risk_level')}")
            print(f"   - Sanctions: {len(result.get('sanctions', []))}")
            print(f"   - Adverse Media: {len(result.get('adverse_media', []))}")
            return True
        else:
            print(f"❌ Company Screening API: FAILED (Status Code: {response.status_code})")
            print(f"   - Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Company Screening API: ERROR - {str(e)}")
        return False

def test_individual_screening_api():
    """Test the individual screening API"""
    print("\n🔍 Testing Individual Screening API...")
    
    # Test data
    data = {
        "name": "John Smith",
        "country": "United States",
        "date_of_birth": "1980-01-01",
        "level": "standard",
        "include_sanctions": True,
        "include_adverse_media": True
    }
    
    # Make the API request
    try:
        response = requests.post(f"{BASE_URL}/api/screen_individual", json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("✅ Individual Screening API: SUCCESS")
            print(f"   - Name: {result.get('name')}")
            print(f"   - Risk Level: {result.get('overall_risk_level', 'N/A')}")
            return True
        elif response.status_code == 404:
            print("⚠️ Individual Screening API: NOT IMPLEMENTED")
            print("   - This endpoint needs to be implemented in the application")
            # Create a mock implementation suggestion
            print("\n📝 Suggested Implementation:")
            print("""
@app.route('/api/screen_individual', methods=['POST'])
def api_screen_individual():
    \"\"\"API endpoint for individual screening\"\"\"
    try:
        data = request.json
        name = data.get('name')
        country = data.get('country')
        date_of_birth = data.get('date_of_birth')
        level = data.get('level', 'standard')
        
        # Generate simulated response
        result = generate_simulated_individual_screening_result(name, country, date_of_birth, level)
        
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400
            """)
            return False
        else:
            print(f"❌ Individual Screening API: FAILED (Status Code: {response.status_code})")
            print(f"   - Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Individual Screening API: ERROR - {str(e)}")
        return False

def test_dart_registry_api():
    """Test the DART Registry API"""
    print("\n🔍 Testing DART Registry API...")
    
    # Test data
    data = {
        "company": "Test Corporation",
        "country": "Korea",
        "registry_id": "KR12345"
    }
    
    # Make the API request
    try:
        response = requests.post(f"{BASE_URL}/api/dart_lookup", json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("✅ DART Registry API: SUCCESS")
            print(f"   - Company: {result.get('company_name', 'N/A')}")
            print(f"   - Registry ID: {result.get('registry_id', 'N/A')}")
            return True
        elif response.status_code == 404:
            print("⚠️ DART Registry API: NOT IMPLEMENTED")
            print("   - This endpoint needs to be implemented in the application")
            # Create a mock implementation suggestion
            print("\n📝 Suggested Implementation:")
            print("""
@app.route('/api/dart_lookup', methods=['POST'])
def api_dart_lookup():
    \"\"\"API endpoint for DART Registry lookup\"\"\"
    try:
        data = request.json
        company = data.get('company')
        country = data.get('country')
        registry_id = data.get('registry_id')
        
        # Generate simulated response
        result = {
            "company_name": company,
            "country": country,
            "registry_id": registry_id,
            "registration_date": "2010-05-15",
            "status": "Active",
            "industry_code": "12345",
            "industry_name": "Technology",
            "address": "123 Test Street, Seoul, Korea",
            "representative": "Kim Test",
            "capital": "100,000,000 KRW",
            "documents": [
                {
                    "id": "DOC001",
                    "title": "Annual Report 2024",
                    "date": "2024-03-15",
                    "url": "https://dart.example.com/doc001"
                },
                {
                    "id": "DOC002",
                    "title": "Quarterly Report Q1 2024",
                    "date": "2024-04-30",
                    "url": "https://dart.example.com/doc002"
                }
            ]
        }
        
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            "error": "Invalid request",
            "details": str(e),
            "status": "error"
        }), 400
            """)
            return False
        else:
            print(f"❌ DART Registry API: FAILED (Status Code: {response.status_code})")
            print(f"   - Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ DART Registry API: ERROR - {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("🚀 Starting API Tests...")
    
    # Track test results
    results = {
        "company_screening": test_company_screening_api(),
        "individual_screening": test_individual_screening_api(),
        "dart_registry": test_dart_registry_api()
    }
    
    # Print summary
    print("\n📊 Test Summary:")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    # Print detailed results
    print("\nDetailed Results:")
    for api, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{api}: {status}")
    
    # Return overall success
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
