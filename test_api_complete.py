#!/usr/bin/env python3
"""
Complete API test for enhanced GPT-5 pipeline with authentication
"""
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_complete_api():
    """Test the complete enhanced GPT-5 API with authentication"""
    print("🧪 TESTING COMPLETE ENHANCED GPT-5 API")
    print("="*80)
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    try:
        # Step 1: Login
        print("1️⃣ AUTHENTICATION")
        login_data = {
            "username": "ens@123",
            "password": "$$$$55"
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code == 200:
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return False
        
        # Step 2: Start screening
        print("\n2️⃣ STARTING ENHANCED GPT-5 SCREENING")
        screening_data = {
            "company": "Rawabi Holding",
            "country": "Saudi Arabia"
        }
        
        screen_response = session.post(
            f"{base_url}/api/v1/screen",
            json=screening_data
        )
        
        if screen_response.status_code in [200, 202]:  # Accept both 200 and 202 for async
            result = screen_response.json()
            task_id = result.get('task_id')
            print(f"   ✅ Screening started: {task_id}")
        else:
            print(f"   ❌ Screening failed: {screen_response.status_code}")
            print(f"   Response: {screen_response.text}")
            return False
        
        # Step 3: Monitor progress
        print("\n3️⃣ MONITORING GPT-5 PROGRESS")
        max_attempts = 60  # 2 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_response = session.get(f"{base_url}/api/v1/status/{task_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                task_status = status_data.get('status', 'unknown')
                
                print(f"   📊 Status: {task_status}")
                
                # Show current step
                steps = status_data.get('steps', {})
                if isinstance(steps, dict):
                    for step_name, step_data in steps.items():
                        step_status = step_data.get('status', 'unknown')
                        message = step_data.get('message', '')
                        if step_status in ['active', 'in_progress']:
                            print(f"      🔄 {step_name}: {message}")
                elif isinstance(steps, list):
                    for step in steps:
                        step_name = step.get('name', 'unknown')
                        step_status = step.get('status', 'unknown')
                        message = step.get('message', '')
                        if step_status in ['active', 'in_progress']:
                            print(f"      🔄 {step_name}: {message}")
                
                # Show recent logs
                logs = status_data.get('source_logs', [])
                if logs:
                    recent_log = logs[-1]
                    print(f"      📝 Latest: {recent_log}")
                
                if task_status == 'completed':
                    print("   ✅ Screening completed!")
                    break
                elif task_status == 'failed':
                    print("   ❌ Screening failed!")
                    return False
                    
            else:
                print(f"   ⚠️ Status check failed: {status_response.status_code}")
            
            time.sleep(2)
            attempt += 1
        
        if attempt >= max_attempts:
            print("   ⏰ Timeout waiting for completion")
            return False
        
        # Step 4: Get final report
        print("\n4️⃣ RETRIEVING GPT-5 ENHANCED REPORT")
        report_response = session.get(f"{base_url}/api/v1/report/{task_id}")
        
        if report_response.status_code == 200:
            report_data = report_response.json()
            print("   ✅ Report retrieved successfully")
            
            # Display key findings
            executive_summary = report_data.get('executive_summary', {})
            company_profile = report_data.get('company_profile', {})
            risk_flags = report_data.get('risk_flags', [])
            sanctions = report_data.get('sanctions_matches', [])
            adverse_media = report_data.get('news_and_media', [])
            
            print(f"\n   📋 EXECUTIVE SUMMARY:")
            print(f"      Risk Score: {executive_summary.get('risk_score', 'Unknown')}/100")
            print(f"      Overview: {executive_summary.get('overview', 'No overview')[:150]}...")
            
            print(f"\n   🏢 COMPANY PROFILE:")
            print(f"      Legal Name: {company_profile.get('legal_name', 'Unknown')}")
            print(f"      Industry: {company_profile.get('industry', 'Unknown')}")
            print(f"      Website: {company_profile.get('official_website', 'Unknown')}")
            
            print(f"\n   📊 KEY FINDINGS:")
            print(f"      🛡️ Sanctions: {len(sanctions)} matches")
            print(f"      📰 Adverse Media: {len(adverse_media)} articles")
            print(f"      ⚠️ Risk Flags: {len(risk_flags)} items")
            
            if risk_flags:
                print(f"\n   ⚠️ RISK FLAGS DETAILS:")
                for i, flag in enumerate(risk_flags[:3], 1):
                    print(f"      {i}. {flag.get('type', 'Unknown')}: {flag.get('description', 'No description')[:80]}...")
                    print(f"         Severity: {flag.get('severity', 'unknown')} | Source: {flag.get('source', 'unknown')}")
            
            # Save full report
            with open('complete_api_test_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n   💾 Full report saved: complete_api_test_report.json")
            
            return True
            
        else:
            print(f"   ❌ Report retrieval failed: {report_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_api()
    
    print(f"\n{'='*80}")
    if success:
        print("🎯 COMPLETE API TEST: ✅ SUCCESS!")
        print("✅ Authentication working")
        print("✅ Enhanced GPT-5 pipeline functional")
        print("✅ Real-time progress monitoring")
        print("✅ Comprehensive report generation")
        print("✅ Ready for production use!")
    else:
        print("🎯 COMPLETE API TEST: ❌ FAILED!")
        print("❌ Issues detected in API pipeline")
    
    exit(0 if success else 1)