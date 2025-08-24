#!/usr/bin/env python3
"""
Debug script to test Render deployment
Replace YOUR_APP_URL with your actual Render app URL
"""
import requests
import json

# Replace this with your actual Render app URL
RENDER_URL = "https://your-app-name.onrender.com"  # CHANGE THIS!

def test_render_deployment():
    print("🔍 TESTING RENDER DEPLOYMENT")
    print("="*50)
    
    try:
        # Test 1: Health Check
        print("\n1️⃣ TESTING HEALTH ENDPOINT")
        health_url = f"{RENDER_URL}/api/v1/health"
        print(f"   URL: {health_url}")
        
        try:
            health_response = requests.get(health_url, timeout=10)
            print(f"   Status Code: {health_response.status_code}")
            print(f"   Response: {health_response.text[:200]}")
            
            if health_response.status_code == 200:
                try:
                    health_data = health_response.json()
                    print("   ✅ Health endpoint working!")
                except:
                    print("   ⚠️ Health endpoint returns non-JSON")
            else:
                print("   ❌ Health endpoint failed")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
        
        # Test 2: Login Page
        print("\n2️⃣ TESTING LOGIN PAGE")
        login_url = f"{RENDER_URL}/login"
        print(f"   URL: {login_url}")
        
        try:
            login_page = requests.get(login_url, timeout=10)
            print(f"   Status Code: {login_page.status_code}")
            
            if login_page.status_code == 200:
                if "login" in login_page.text.lower():
                    print("   ✅ Login page accessible")
                else:
                    print("   ⚠️ Unexpected login page content")
            else:
                print("   ❌ Login page not accessible")
        except Exception as e:
            print(f"   ❌ Login page test failed: {e}")
        
        # Test 3: API Authentication Flow
        print("\n3️⃣ TESTING AUTHENTICATED API CALL")
        session = requests.Session()
        
        try:
            # First login
            login_data = {"username": "ens@123", "password": "$$$$55"}
            login_response = session.post(f"{RENDER_URL}/login", data=login_data, timeout=10)
            print(f"   Login Status: {login_response.status_code}")
            
            if login_response.status_code in [200, 302]:
                print("   ✅ Login appears successful")
                
                # Try API call
                api_data = {"company": "Test Company", "country": "USA"}
                api_response = session.post(
                    f"{RENDER_URL}/api/v1/screen", 
                    json=api_data, 
                    timeout=10
                )
                
                print(f"   API Status: {api_response.status_code}")
                print(f"   API Response: {api_response.text[:200]}")
                
                if api_response.status_code in [200, 202]:
                    try:
                        api_json = api_response.json()
                        print("   ✅ API returning JSON!")
                        if "task_id" in api_json:
                            print(f"   Task ID: {api_json['task_id']}")
                    except:
                        print("   ⚠️ API response not valid JSON")
                else:
                    print("   ❌ API call failed")
            else:
                print("   ❌ Login failed")
        
        except Exception as e:
            print(f"   ❌ Authentication test failed: {e}")
        
        # Test 4: Environment Variables Check
        print("\n4️⃣ CHECKING FOR COMMON ISSUES")
        
        # Try to determine if it's an environment issue
        try:
            test_response = requests.get(f"{RENDER_URL}/", timeout=10)
            if "error" in test_response.text.lower():
                print("   ⚠️ Application may have startup errors")
            if "internal server error" in test_response.text.lower():
                print("   ❌ Server error - check Render logs")
            if test_response.status_code == 500:
                print("   ❌ 500 Error - likely missing environment variables")
        except:
            pass
        
        print("\n" + "="*50)
        print("🎯 DEBUGGING RECOMMENDATIONS:")
        print("\n1. Check Render Logs:")
        print("   - Go to render.com → Your Service → Logs")
        print("   - Look for startup errors")
        print("   - Check if environment variables are loaded")
        
        print("\n2. Verify Environment Variables in Render:")
        print("   - OPENAI_API_KEY (required)")
        print("   - SECRET_KEY (required)")
        print("   - FLASK_ENV=production")
        
        print("\n3. Test Endpoints in Order:")
        print("   - /api/v1/health (should work without auth)")
        print("   - /login (should show login form)")
        print("   - / (should redirect to login or dashboard)")
        
        print("\n4. If Still Failing:")
        print("   - Check build logs in Render")
        print("   - Verify requirements.txt installed correctly")
        print("   - Make sure Procfile is correct")
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")

if __name__ == "__main__":
    if "your-app-name" in RENDER_URL:
        print("❌ ERROR: Please update RENDER_URL with your actual app URL!")
        print("   Change line 9: RENDER_URL = 'https://YOUR-ACTUAL-APP.onrender.com'")
    else:
        test_render_deployment()