#!/usr/bin/env python3
"""
Simple test to debug executive search
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def test_executive_search():
    """Test executive search specifically"""
    print("🔍 Testing executive search...")
    
    from services.real_data import real_data_collector
    
    # Test a simple search first
    print("\n1️⃣ Testing Google search...")
    results = await real_data_collector.google_search("Tim Cook Apple CEO", 3)
    print(f"Search results: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.get('title', 'No title')}")
        print(f"      URL: {result.get('url', 'No URL')}")
        print(f"      Snippet: {result.get('snippet', 'No snippet')[:100]}...")
    
    if len(results) > 0:
        print("\n2️⃣ Testing executive extraction...")
        test_result = results[0]
        executives = await real_data_collector._extract_executives_from_result(test_result, "Apple Inc")
        print(f"Executives extracted: {len(executives)}")
        for exec in executives:
            print(f"   - {exec.get('name', 'Unknown')} - {exec.get('title', 'Unknown')}")
    else:
        print("\n❌ No search results - Google search may be blocked")
        
        # Test regex extraction directly
        print("\n3️⃣ Testing regex extraction directly...")
        test_content = "Tim Cook is the Chief Executive Officer of Apple Inc. Craig Federighi serves as Senior Vice President of Software Engineering."
        executives = real_data_collector._regex_extract_executives(test_content, "Apple Inc", "test_source")
        print(f"Regex executives found: {len(executives)}")
        for exec in executives:
            print(f"   - {exec.get('name', 'Unknown')} - {exec.get('title', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_executive_search())