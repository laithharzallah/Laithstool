#!/usr/bin/env python3
"""
Test GPT-5 Enhanced Web Search for Due Diligence
Tests real data collection capabilities
"""

import asyncio
import json
import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our service
from services.gpt5_web_search import gpt5_search_service

@pytest.mark.parametrize(
    "company,country",
    [
        ("Apple Inc", "United States"),
        ("Siemens AG", "Germany"),
        ("Tesla Inc", "United States"),
        ("Rawabi Holding", "Saudi Arabia"),
    ],
)
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_company_screening(company: str, country: str):
    """Test comprehensive company screening"""
    print(f"\n🔍 TESTING: {company} ({country})")
    print("=" * 60)
    
    try:
        # Perform screening
        result = asyncio.run(gpt5_search_service.screen_company(company, country))
        
        # Check if it's an error response
        if result.get('error'):
            print(f"❌ Screening failed: {result.get('message')}")
            return False
        
        # Analyze results quality
        print(f"📊 RESULTS ANALYSIS:")
        print(f"   Company: {result.get('company_profile', {}).get('legal_name', 'Unknown')}")
        print(f"   Industry: {result.get('company_profile', {}).get('industry', 'Unknown')}")
        print(f"   Website: {result.get('official_website', 'Not found')}")
        
        # Check executives
        executives = result.get('key_executives', [])
        print(f"\n👥 EXECUTIVES ({len(executives)} found):")
        for i, exec in enumerate(executives[:5]):
            name = exec.get('name', 'Unknown')
            position = exec.get('position', 'Unknown')
            source = exec.get('source_url', 'No source')
            print(f"   {i+1}. {name} - {position}")
            print(f"      Source: {source[:60]}...")
        
        # Check financial data
        financial_fields = ['ability_to_generate_cash', 'capability_of_paying_debt', 'cash_reserve']
        print(f"\n💰 FINANCIAL DATA:")
        for field in financial_fields:
            data = result.get(field)
            if data:
                value = data.get('value', 'No data')
                source = data.get('source_url', 'No source')
                print(f"   {field}: {value}")
                print(f"      Source: {source[:60]}...")
            else:
                print(f"   {field}: No data found")
        
        # Check adverse media
        adverse_media = result.get('adverse_media', [])
        print(f"\n📰 ADVERSE MEDIA ({len(adverse_media)} items):")
        for i, item in enumerate(adverse_media[:3]):
            headline = item.get('headline', 'No headline')
            source = item.get('source_url', 'No source')
            print(f"   {i+1}. {headline[:60]}...")
            print(f"      Source: {source[:60]}...")
        
        # Check sanctions
        sanctions = result.get('sanctions_flags', [])
        print(f"\n🚫 SANCTIONS ({len(sanctions)} flags):")
        for i, sanction in enumerate(sanctions[:3]):
            entity = sanction.get('entity_name', 'Unknown')
            list_name = sanction.get('list_name', 'Unknown')
            confidence = sanction.get('confidence', 'Unknown')
            print(f"   {i+1}. {entity} on {list_name} (confidence: {confidence})")
        
        # Check citations
        citations = result.get('citations', [])
        print(f"\n🔗 CITATIONS ({len(citations)} sources):")
        for i, citation in enumerate(citations[:5]):
            print(f"   {i+1}. {citation}")
        
        # Quality assessment
        has_executives = len(executives) > 0
        has_website = bool(result.get('official_website'))
        has_financial = any(result.get(field) for field in financial_fields)
        has_citations = len(citations) > 0
        
        quality_score = sum([has_executives, has_website, has_financial, has_citations])
        print(f"\n📈 QUALITY ASSESSMENT:")
        print(f"   ✅ Has executives: {has_executives}")
        print(f"   ✅ Has website: {has_website}")
        print(f"   ✅ Has financial data: {has_financial}")
        print(f"   ✅ Has citations: {has_citations}")
        print(f"   📊 Quality score: {quality_score}/4")
        
        # Success criteria
        success = quality_score >= 3 and has_citations
        print(f"\n🎯 TEST RESULT: {'✅ PASS' if success else '❌ FAIL'}")
        assert success, "Quality criteria not met"
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        assert False, f"Exception during screening: {e}"

async def main():
    """Run comprehensive tests"""
    print("🚀 GPT-5 ENHANCED WEB SEARCH TEST SUITE")
    print("=" * 60)
    
    # Test companies
    test_companies = [
        ("Apple Inc", "United States"),
        ("Siemens AG", "Germany"),
        ("Tesla Inc", "United States"),
        ("Rawabi Holding", "Saudi Arabia")
    ]
    
    results = []
    
    for company, country in test_companies:
        success = await test_company_screening(company, country)
        results.append((company, success))
        
        # Wait between tests to avoid rate limiting
        await asyncio.sleep(2)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for company, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {company}: {status}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - GPT-5 web search is working!")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return passed == total

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    exit(0 if success else 1)