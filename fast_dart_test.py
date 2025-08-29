#!/usr/bin/env python3
"""
FAST DART Test - Uses cached data for instant results
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.adapters.dart import dart_adapter

def fast_test():
    """Fast test using cached DART data"""

    print("🚀 FAST DART TEST - Cached Results")
    print("=" * 50)

    test_companies = [
        "삼성전자",
        "Samsung Electronics",
        "현대자동차",
        "Hyundai Motor",
        "LG Chem",
        "SK Hynix"
    ]

    print("Testing multiple company searches...")
    print()

    for i, company in enumerate(test_companies, 1):
        print(f"{i}. 🔍 Searching for: '{company}'")

        start_time = time.time()

        # Search using our FAST DART adapter
        results = dart_adapter.search_company(company)

        end_time = time.time()
        search_time = end_time - start_time

        if results:
            print(f"   ✅ Found {len(results)} results in {search_time:.2f} seconds")
            print(f"   🏢 Top result: {results[0].get('name', 'Unknown')}")
            if results[0].get('stock_code'):
                print(f"   📈 Stock Code: {results[0]['stock_code']}")
        else:
            print(f"   ❌ No results found ({search_time:.2f} seconds)")

        print()

    print("🎉 FAST SEARCH COMPLETE!")
    print("💡 Subsequent searches will be even faster (using cache)")

def test_cache_performance():
    """Test cache performance"""

    print("\n" + "=" * 60)
    print("⚡ CACHE PERFORMANCE TEST")
    print("=" * 60)

    company = "삼성전자"

    print("1️⃣ First search (downloads data):")
    start_time = time.time()
    results1 = dart_adapter.search_company(company)
    end_time = time.time()
    time1 = end_time - start_time
    print(f"   Time: {time1:.2f} seconds")
    print(f"   Results: {len(results1) if results1 else 0}")

    print("\n2️⃣ Second search (uses cache):")
    start_time = time.time()
    results2 = dart_adapter.search_company(company)
    end_time = time.time()
    time2 = end_time - start_time
    print(f"   Time: {time2:.2f} seconds")
    print(f"   Results: {len(results2) if results2 else 0}")

    if time1 > 0 and time2 > 0:
        speedup = time1 / time2
        print(f"\n🚀 Performance Improvement: {speedup:.1f}x faster!")
if __name__ == "__main__":
    fast_test()
    test_cache_performance()
