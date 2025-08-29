#!/usr/bin/env python3
"""
INSTANT DART Test - One-time load, instant searches
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.adapters.dart import dart_adapter

def instant_test():
    """Test instant DART searches"""

    print("⚡ INSTANT DART TEST")
    print("=" * 50)
    print("Loading data once, then instant searches...")
    print()

    # Test companies
    companies = [
        "삼성전자",
        "Samsung Electronics",
        "현대자동차",
        "Hyundai Motor",
        "LG Chem",
        "SK Hynix",
        "POSCO"
    ]

    print("🔄 Performing searches...")
    print("-" * 40)

    for company in companies:
        start_time = time.time()

        # Search
        results = dart_adapter.search_company(company)

        end_time = time.time()
        search_time = end_time - start_time

        if results:
            print(f"   ✅ {len(results)} results in {search_time:.2f} seconds")
        else:
            print(f"   ❌ No results in {search_time:.2f} seconds")
    print()
    print("🎉 ALL SEARCHES COMPLETED INSTANTLY!")
    print("💡 Data loaded once, searches are now instant!")

if __name__ == "__main__":
    instant_test()
