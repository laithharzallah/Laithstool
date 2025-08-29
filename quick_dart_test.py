#!/usr/bin/env python3
"""
Quick DART test - search for specific companies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.adapters.dart import dart_adapter

def quick_test():
    """Quick test of DART search for specific companies"""

    test_companies = ["삼성전자", "Samsung Electronics", "현대자동차", "Hyundai"]

    print("🇰🇷 DART Registry Quick Test")
    print("=" * 50)
    print("Testing company searches...")
    print()

    for company_name in test_companies:
        print(f"🔍 Searching for: '{company_name}'")
        print("-" * 40)

        try:
            # Use our DART adapter (this is what the actual app uses)
            results = dart_adapter.search_company(company_name)

            if results:
                print(f"✅ Found {len(results)} result(s):")
                print()

                for i, company in enumerate(results[:3], 1):  # Show first 3
                    print(f"{i}. 🏢 {company.get('name', 'Unknown')}")
                    print(f"   English: {company.get('name_eng', 'N/A')}")
                    print(f"   Stock Code: {company.get('stock_code', 'N/A')}")
                    print(f"   Company Code: {company.get('corp_code', 'N/A')}")
                    print(f"   Registry: 🇰🇷 DART (Korean FSC)")
                    print("   [Official Data Only]")
                    print()
            else:
                print("❌ No results found")
                print()

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()

        print("-" * 50)

    print("🎉 Test completed!")
    print("\n💡 These are the exact results users will see in your DART Registry tab!")

if __name__ == "__main__":
    quick_test()
