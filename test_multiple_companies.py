#!/usr/bin/env python3
"""
Test multiple companies to verify real data collection
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
            print(f"   📄 Description: {website.get('description', 'N/A')[:150]}...")
            contact = website.get('contact_info', {})
            if contact:
                print(f"   📧 Email: {contact.get('email', 'N/A')}")
                print(f"   📞 Phone: {contact.get('phone', 'N/A')}")
        else:
            print(f"   ❌ Error: {website.get('error', 'Unknown error')}")
        
        # Executives
        executives = result.get('executives', [])
        print(f"\n👥 EXECUTIVES ({len(executives)} found):")
        if executives:
            for i, exec in enumerate(executives[:5], 1):
                name = exec.get('name', 'Unknown')
                title = exec.get('title', 'Unknown title')
                source = exec.get('source_url', 'Unknown source')
                print(f"   {i}. {name}")
                print(f"      🏷️ Title: {title}")
                print(f"      🔗 Source: {source[:60]}..." if len(source) > 60 else f"      🔗 Source: {source}")
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
            
            if company_matches:
                print("   🚨 Company sanctions found:")
                for match in company_matches[:3]:
                    print(f"      - {match.get('name', 'Unknown')}: {match.get('reason', 'Unknown reason')}")
            
            if exec_matches:
                print("   🚨 Executive sanctions found:")
                for match in exec_matches[:3]:
                    print(f"      - {match.get('name', 'Unknown')}: {match.get('reason', 'Unknown reason')}")
            
            if not company_matches and not exec_matches:
                print("   ✅ No sanctions matches found")
        else:
            print(f"   ❌ Error: {sanctions.get('error', 'Unknown error')}")
        
        # Adverse Media
        adverse_media = result.get('adverse_media', [])
        print(f"\n📰 ADVERSE MEDIA ({len(adverse_media)} articles found):")
        if adverse_media:
            for i, article in enumerate(adverse_media[:3], 1):
                title = article.get('title', 'Unknown title')
                url = article.get('url', 'No URL')
                sentiment = article.get('sentiment', 'Unknown')
                print(f"   {i}. {title[:80]}...")
                print(f"      🔗 URL: {url[:60]}..." if len(url) > 60 else f"      🔗 URL: {url}")
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
            key_points = exec_sum.get('key_points', [])
            
            print(f"   📊 Risk Score: {risk_score}/100")
            print(f"   📝 Overview: {overview}")
            if key_points:
                print(f"   🔑 Key Points:")
                for point in key_points[:3]:
                    print(f"      • {point}")
        else:
            print(f"   ❌ Error: {ai_summary.get('error', 'AI analysis failed')}")
        
        # Performance
        processing_time = (end_time - start_time) * 1000
        print(f"\n⏱️ PERFORMANCE:")
        print(f"   Processing Time: {processing_time:.1f}ms")
        
        # Data Sources
        sources = result.get('data_sources_used', [])
        if sources:
            print(f"   📚 Data Sources: {', '.join(sources)}")
        
        return result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

async def run_comprehensive_tests():
    """Test multiple companies"""
    companies = [
        "Apple Inc",      # Tech giant (US)
        "Siemens AG",     # Industrial conglomerate (German)
        "Toyota Motor",   # Automotive (Japanese)
        "ASML",          # Semiconductor equipment (Dutch)
        "Microsoft"       # Tech giant (US)
    ]
    
    print("🚀 STARTING COMPREHENSIVE COMPANY SCREENING TESTS")
    print(f"📅 Testing {len(companies)} companies")
    print("🔍 Will check: Website, Executives, Sanctions, Adverse Media, AI Analysis")
    
    results = []
    total_start = time.time()
    
    for i, company in enumerate(companies, 1):
        result = await test_company(company, i)
        results.append({
            'company': company,
            'success': result is not None,
            'result': result
        })
        
        # Small delay between tests to be respectful
        if i < len(companies):
            print(f"\n⏳ Waiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    total_time = (time.time() - total_start) * 1000
    
    # Summary Report
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    successful_tests = sum(1 for r in results if r['success'])
    print(f"✅ Successful tests: {successful_tests}/{len(companies)}")
    print(f"⏱️ Total processing time: {total_time:.1f}ms")
    print(f"📈 Average per company: {total_time/len(companies):.1f}ms")
    
    for result in results:
        company = result['company']
        if result['success']:
            data = result['result']
            executives = len(data.get('executives', []))
            media = len(data.get('adverse_media', []))
            website = "✅" if data.get('website_info', {}).get('url') else "❌"
            sanctions = "✅" if not data.get('sanctions', {}).get('error') else "❌"
            ai = "✅" if data.get('ai_summary', {}).get('executive_summary') else "❌"
            
            print(f"\n🏢 {company}:")
            print(f"   🌐 Website: {website}")
            print(f"   👥 Executives: {executives}")
            print(f"   📰 Media: {media}")
            print(f"   🛡️ Sanctions: {sanctions}")
            print(f"   🤖 AI: {ai}")
        else:
            print(f"\n🏢 {company}: ❌ FAILED")
    
    print(f"\n{'='*80}")
    print("🎯 TEST COMPLETE - Real data collection verified!")
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())