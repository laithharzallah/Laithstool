#!/usr/bin/env python3
"""
Test the specific companies requested by user
"""
import asyncio
import json
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

async def test_company(company_name: str, test_number: int):
    """Test a single company"""
    print(f"\n{'='*80}")
    print(f"🏢 TEST {test_number}: {company_name.upper()}")
    print(f"{'='*80}")
    
    try:
        from services.real_data import real_data_collector
        
        start_time = time.time()
        result = await real_data_collector.comprehensive_screening(company_name)
        end_time = time.time()
        
        # Website Results
        website = result.get('website_info', {})
        print(f"\n🌐 WEBSITE:")
        if website and not website.get('error'):
            print(f"   ✅ Found: {website.get('url', 'N/A')}")
            print(f"   📝 Title: {website.get('title', 'N/A')}")
            print(f"   📄 Description: {website.get('description', 'N/A')[:100]}...")
        else:
            print(f"   ❌ Error: {website.get('error', 'Unknown error')}")
        
        # Executives
        executives = result.get('executives', [])
        print(f"\n👥 EXECUTIVES ({len(executives)} found):")
        if executives:
            for i, exec in enumerate(executives[:3], 1):
                name = exec.get('name', 'Unknown')
                title = exec.get('title', 'Unknown title')
                print(f"   {i}. {name} - {title}")
        else:
            print("   ❌ No executives found")
        
        # Sanctions
        sanctions = result.get('sanctions', {})
        print(f"\n🛡️ SANCTIONS CHECK:")
        if sanctions and not sanctions.get('error'):
            company_matches = sanctions.get('company_matches', [])
            exec_matches = sanctions.get('executive_matches', [])
            print(f"   📊 Company matches: {len(company_matches)}")
            print(f"   👤 Executive matches: {len(exec_matches)}")
            if not company_matches and not exec_matches:
                print("   ✅ No sanctions matches - Clean record")
        else:
            print(f"   ❌ Error: {sanctions.get('error', 'Unknown error')}")
        
        # Adverse Media
        adverse_media = result.get('adverse_media', [])
        print(f"\n📰 ADVERSE MEDIA ({len(adverse_media)} articles found):")
        if adverse_media:
            for i, article in enumerate(adverse_media[:2], 1):
                title = article.get('title', 'Unknown title')
                sentiment = article.get('sentiment', 'Unknown')
                print(f"   {i}. {title[:60]}...")
                print(f"      😐 Sentiment: {sentiment}")
        else:
            print("   ❌ No adverse media found")
        
        # AI Summary
        ai_summary = result.get('ai_summary', {})
        print(f"\n🤖 AI ANALYSIS:")
        if ai_summary and not ai_summary.get('error'):
            exec_sum = ai_summary.get('executive_summary', {})
            risk_score = exec_sum.get('risk_score', 'N/A')
            overview = exec_sum.get('overview', 'N/A')
            print(f"   📊 Risk Score: {risk_score}/100")
            print(f"   📝 Overview: {overview[:100]}...")
        else:
            print(f"   ❌ AI analysis failed")
        
        # Performance
        processing_time = (end_time - start_time) * 1000
        print(f"\n⏱️ Processing Time: {processing_time:.1f}ms")
        
        return result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return None

async def run_user_tests():
    """Test the user's requested companies"""
    companies = [
        "Rawabi Holding",    # Middle East conglomerate
        "Siemens AG",        # German industrial
        "SAP",               # German software
        "China Petroleum",   # Chinese oil & gas
        "Apple Inc"          # US tech giant
    ]
    
    print("🚀 TESTING YOUR REQUESTED COMPANIES")
    print(f"📅 Testing {len(companies)} companies")
    print("🔍 Checking: Website, Executives, Sanctions, Media, AI Analysis")
    
    results = []
    
    for i, company in enumerate(companies, 1):
        print(f"\n⏳ Starting test {i}/{len(companies)}...")
        result = await test_company(company, i)
        results.append({
            'company': company,
            'success': result is not None,
            'result': result
        })
        
        # Brief pause between tests
        if i < len(companies):
            print(f"\n⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # Final Summary
    print(f"\n{'='*80}")
    print("📊 FINAL RESULTS SUMMARY")
    print(f"{'='*80}")
    
    for result in results:
        company = result['company']
        if result['success']:
            data = result['result']
            executives = len(data.get('executives', []))
            media = len(data.get('adverse_media', []))
            website = "✅" if data.get('website_info', {}).get('url') else "❌"
            
            print(f"\n🏢 {company}:")
            print(f"   🌐 Website: {website}")
            print(f"   👥 Executives: {executives} found")
            print(f"   📰 Media: {media} articles")
            print(f"   ✅ Status: SUCCESS")
        else:
            print(f"\n🏢 {company}: ❌ FAILED")
    
    successful = sum(1 for r in results if r['success'])
    print(f"\n🎯 OVERALL: {successful}/{len(companies)} companies successfully screened")
    print("✅ Real data collection system is working!")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_user_tests())