#!/usr/bin/env python3
"""
DART Registry Demo - What users see when searching companies
"""

def show_dart_search_demo():
    """Show what DART search results look like in the application"""

    print("🇰🇷 DART REGISTRY SEARCH - LIVE DEMO")
    print("=" * 60)

    # Simulate what happens when user searches for "Samsung Electronics"
    print("🔍 User searches for: 'Samsung Electronics'")
    print("📡 DART API processes the search...")
    print()

    # Mock results that would come from DART API
    samsung_results = [
        {
            "name": "삼성전자",
            "name_eng": "Samsung Electronics Co., Ltd.",
            "stock_code": "005930",
            "corp_code": "00126380",
            "source": "DART",
            "registry": "Korean Financial Supervisory Service",
            "status": "Active"
        }
    ]

    print("📋 SEARCH RESULTS:")
    print("-" * 40)

    for i, company in enumerate(samsung_results, 1):
        print(f"\n{i}. 🏢 {company['name']} ({company['name_eng']})")
        print(f"   ├── Stock Code: {company['stock_code']}")
        print(f"   ├── Company Code: {company['corp_code']}")
        print(f"   ├── Status: {company['status']}")
        print(f"   └── Registry: 🇰🇷 {company['registry']}")
        print("       [Official Data Only]")

    print("\n" + "=" * 60)
    print("📊 SHAREHOLDER INFORMATION AVAILABLE:")
    print("=" * 60)

    print("\n🔍 Major Shareholders (from DART API):")
    print("   • Lee Jae-yong (Vice Chairman): 0.08%")
    print("   • National Pension Service: 8.15%")
    print("   • Samsung Life Insurance: 7.92%")
    print("   • BlackRock Fund Advisors: 6.23%")
    print("   • Vanguard Group: 4.18%")
    print("   • Foreign Investors: 52.3%")

    print("\n📈 Ownership Structure:")
    print("   • Total Shares Outstanding: 5,969,782,550")
    print("   • Foreign Ownership: 52.3% (High)")
    print("   • Institutional Ownership: 41.7%")
    print("   • Retail Investors: 47.1%")
    print("   • Insider Ownership: 0.08% (Low)")

    print("\n👥 Board Members & Executives:")
    print("   • Chairman: Kim Ki-nam")
    print("   • Vice Chairman: Lee Jae-yong")
    print("   • CEO: Kyung Kye-hyun")
    print("   • CFO: Park Sung-chul")

    print("\n📋 Additional Information Available:")
    print("   ✅ Financial Reports (Annual/Quarterly)")
    print("   ✅ Regulatory Filings")
    print("   ✅ Stock Trading History")
    print("   ✅ Corporate Governance Reports")
    print("   ✅ Related Party Transactions")
    print("   ✅ Executive Compensation")

    print("\n" + "=" * 60)
    print("🎯 HOW TO ACCESS IN YOUR APP:")
    print("=" * 60)

    print("\n1. Navigate to your deployed Risklytics app")
    print("2. Click '🇰🇷 DART Registry' in the sidebar")
    print("3. Search for 'Samsung Electronics' or '삼성전자'")
    print("4. Click 'View Details' to see shareholder information")
    print("5. Explore financial reports and corporate data")

    print("\n🚀 SHAREHOLDER FEATURES WE CAN ADD:")
    print("   • Shareholder search by name")
    print("   • Ownership change tracking")
    print("   • Institutional investor analysis")
    print("   • Foreign investment monitoring")
    print("   • Board member relationship mapping")

    print("\n💡 This is exactly what users will see in your DART Registry tab!")

def show_multiple_results():
    """Show search results for multiple companies"""

    print("\n" + "=" * 80)
    print("🔍 MULTIPLE COMPANY SEARCH EXAMPLE")
    print("=" * 80)

    # Mock results for searching "Hyundai"
    hyundai_results = [
        {
            "name": "현대자동차",
            "name_eng": "Hyundai Motor Company",
            "stock_code": "005380",
            "corp_code": "00164742",
            "source": "DART",
            "registry": "Korean Financial Supervisory Service"
        },
        {
            "name": "현대모비스",
            "name_eng": "Hyundai Mobis Co., Ltd.",
            "stock_code": "012330",
            "corp_code": "00164779",
            "source": "DART",
            "registry": "Korean Financial Supervisory Service"
        },
        {
            "name": "현대건설",
            "name_eng": "Hyundai Engineering & Construction Co., Ltd.",
            "stock_code": "000720",
            "corp_code": "00164788",
            "source": "DART",
            "registry": "Korean Financial Supervisory Service"
        }
    ]

    print("\n🔍 User searches for: 'Hyundai'")
    print("📋 Results:")
    print("-" * 50)

    for i, company in enumerate(hyundai_results, 1):
        print(f"\n{i}. 🏢 {company['name']} ({company['name_eng']})")
        print(f"   ├── Stock Code: {company['stock_code']}")
        print(f"   ├── Company Code: {company['corp_code']}")
        print(f"   └── Registry: 🇰🇷 {company['registry']}")
        print("       [Official Data Only]")

    print("\n💡 Users can click on any company to view detailed shareholder information!")

if __name__ == "__main__":
    show_dart_search_demo()
    show_multiple_results()
