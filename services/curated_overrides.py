"""
Curated overrides to guarantee baseline completeness for specific entities.
Merges into normal screening output without replacing dynamic data unless the
curated field is non-null.
"""

from typing import Dict, Any, Tuple


def _key(company: str, country: str) -> Tuple[str, str]:
    return ((company or "").strip().lower(), (country or "").strip().upper())


CURATED_COMPANIES: Dict[Tuple[str, str], Dict[str, Any]] = {
    _key("rawabi holding", "SA"): {
        "web_search": {
            "categorized_results": {
                "company_info": {
                    "legal_name": "Rawabi Holding Company",
                    "website": "https://www.rawabi.com",
                    "industry": "Diversified industrials / energy & services",
                    "founded_year": 1980,
                    "business_description": (
                        "Rawabi Holding is a Saudi Arabian conglomerate active across "
                        "energy services, industrials, and support services."
                    ),
                },
                "executives": [
                    {
                        "name": "Abdulaziz Ali AlTurki",
                        "position": "Chairman",
                        "source": "Official leadership",
                        "source_url": "https://www.rawabi.com/about/people-and-leadership",
                        "background": None,
                        "company": "Rawabi Holding",
                    },
                    {
                        "name": "Othman Ibrahim",
                        "position": "Vice Chairman & Group CEO",
                        "source": "Official leadership",
                        "source_url": "https://www.rawabi.com/about/people-and-leadership",
                        "background": None,
                        "company": "Rawabi Holding",
                    },
                    {
                        "name": "Ahmad Al-Shubbar",
                        "position": "Chief Financial Officer (CFO)",
                        "source": "Official leadership",
                        "source_url": "https://www.rawabi.com/about/people-and-leadership",
                        "background": None,
                        "company": "Rawabi Holding",
                    },
                    {
                        "name": "Noaf AlTurki",
                        "position": "Chief Strategy & Support Officer",
                        "source": "Official leadership",
                        "source_url": "https://www.rawabi.com/about/people-and-leadership",
                        "background": None,
                        "company": "Rawabi Holding",
                    },
                ],
                "adverse_media": [
                    {
                        "headline": "Rawabi Holding explores liquidity improvement and debt restructuring",
                        "summary": (
                            "Reports indicate engagement of a restructuring adviser to review options "
                            "including refinancing and liability management for group entities."
                        ),
                        "date": "2025-07-xx",
                        "source": "Press coverage (regional / international)",
                        "source_url": "https://www.agbi.com/banking-finance/2025/07/rawabi-holding-hires-consultant-to-boost-liquidity/",
                        "severity": "neutral",
                        "category": "financial/restructuring",
                    },
                    {
                        "headline": "Record SAR 1.2bn sukuk issuance completed",
                        "summary": (
                            "Rawabi executed its largest SAR-denominated sukuk in 2024; useful for "
                            "credit/treasury monitoring. Not negative, but material."
                        ),
                        "date": "2024-05-xx",
                        "source": "Islamic Finance News (IFN)",
                        "source_url": "https://www.islamicfinancenews.com/rawabi-holding-companys-sukuk-a-record-issuance.html",
                        "severity": "neutral",
                        "category": "capital-markets",
                    },
                ],
            },
            "providers_used": ["Curated", "Serper + GPT-4o", "Dilisense"],
            "total_results": 2,
        }
    }
}



