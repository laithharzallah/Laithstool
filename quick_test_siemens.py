#!/usr/bin/env python3
"""
Quick test of Siemens AG screening - simplified version
"""
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_siemens_simple():
    """Test Siemens AG screening"""
    print("🔍 Testing Siemens AG screening...")
    
    try:
        # Import the real data collector
        from services.real_data import real_data_collector
        
        print("📊 Starting Siemens AG screening...")
        result = await real_data_collector.comprehensive_screening("Siemens AG")
        
        print("\n" + "="*60)
        print("🏢 SIEMENS AG SCREENING RESULTS")
        print("="*60)
        
        # Website Results
        website = result.get('website_info', {})
        if website and not website.get('error'):
            print(f"🌐 Website: {website.get('url', 'Not found')}")
            print(f"   Title: {website.get('title', 'N/A')}")
            print(f"   Description: {website.get('description', 'N/A')[:100]}...")
        else:
            print("🌐 Website: Not found or error")
        
        # Executives
        executives = result.get('executives', [])
        print(f"\n👥 Executives Found: {len(executives)}")
        for i, exec in enumerate(executives[:3], 1):
            print(f"   {i}. {exec.get('name', 'Unknown')} - {exec.get('title', 'Unknown title')}")
        
        # Sanctions
        sanctions = result.get('sanctions', {})
        company_matches = sanctions.get('company_matches', [])
        exec_matches = sanctions.get('executive_matches', [])
        print(f"\n🛡️ Sanctions Check:")
        print(f"   Company matches: {len(company_matches)}")
        print(f"   Executive matches: {len(exec_matches)}")
        
        # Adverse Media
        adverse_media = result.get('adverse_media', [])
        print(f"\n📰 Adverse Media: {len(adverse_media)} articles found")
        for i, article in enumerate(adverse_media[:2], 1):
            print(f"   {i}. {article.get('title', 'Unknown title')[:80]}...")
        
        # AI Summary
        ai_summary = result.get('ai_summary', {})
        if ai_summary and not ai_summary.get('error'):
            exec_sum = ai_summary.get('executive_summary', {})
            print(f"\n🤖 AI Analysis:")
            print(f"   Risk Score: {exec_sum.get('risk_score', 'N/A')}/100")
            print(f"   Overview: {exec_sum.get('overview', 'N/A')}")
        else:
            print("\n🤖 AI Analysis: Failed or unavailable")
        
        # Processing time
        processing_time = result.get('processing_time_ms', 0)
        print(f"\n⏱️ Processing Time: {processing_time:.1f}ms")
        
        print("\n" + "="*60)
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_siemens_simple())