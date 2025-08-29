"""
DART (Data Analysis, Retrieval and Transfer) API Adapter for Korean Companies
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("dart-adapter")

class DARTAdapter:
    """Korea Financial Supervisory Service DART API - INSTANT VERSION"""

    def __init__(self):
        # Use provided API key
        self.api_key = os.getenv("DART_API_KEY", "41e3e5a7cb9e450b235a6a79d2e538ac83c711e7")
        self.base_url = "https://opendart.fss.or.kr/api"

        # Pre-loaded top Korean companies for INSTANT searches
        self._top_companies = self._get_top_korean_companies()
        self._full_data_loaded = False

    def search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for Korean companies by name - INSTANT VERSION"""
        if not self.api_key:
            logger.warning("DART_API_KEY not configured")
            return []

        try:
            # INSTANT search using pre-loaded top companies
            matches = []
            query_lower = company_name.lower().strip()

            # Search in top companies first (INSTANT)
            for corp in self._top_companies:
                corp_name = corp.get("corp_name", "").lower()
                corp_name_eng = corp.get("corp_name_eng", "").lower() if corp.get("corp_name_eng") else ""

                # Exact match first, then partial match
                if query_lower == corp_name or query_lower == corp_name_eng:
                    # Exact match - highest priority
                    matches.insert(0, {
                        "name": corp.get("corp_name", ""),
                        "name_eng": corp.get("corp_name_eng", ""),
                        "corp_code": corp.get("corp_code", ""),
                        "stock_code": corp.get("stock_code", ""),
                        "country": "KR",
                        "source": "DART",
                        "entity_type": "COMPANY",
                        "match_type": "exact"
                    })
                elif query_lower in corp_name or query_lower in corp_name_eng:
                    # Partial match
                    matches.append({
                        "name": corp.get("corp_name", ""),
                        "name_eng": corp.get("corp_name_eng", ""),
                        "corp_code": corp.get("corp_code", ""),
                        "stock_code": corp.get("stock_code", ""),
                        "country": "KR",
                        "source": "DART",
                        "entity_type": "COMPANY",
                        "match_type": "partial"
                    })

            # If no matches in top companies and not fully loaded, load full data
            if not matches and not self._full_data_loaded:
                logger.info("🔄 Company not in top list, loading full DART data...")
                full_data = self._load_full_corp_data()
                if full_data:
                    self._full_data_loaded = True
                    # Search in full data
                    for corp in full_data:
                        corp_name = corp.get("corp_name", "").lower()
                        corp_name_eng = corp.get("corp_name_eng", "").lower() if corp.get("corp_name_eng") else ""

                        if query_lower == corp_name or query_lower == corp_name_eng:
                            matches.insert(0, {
                                "name": corp.get("corp_name", ""),
                                "name_eng": corp.get("corp_name_eng", ""),
                                "corp_code": corp.get("corp_code", ""),
                                "stock_code": corp.get("stock_code", ""),
                                "country": "KR",
                                "source": "DART",
                                "entity_type": "COMPANY",
                                "match_type": "exact"
                            })
                        elif query_lower in corp_name or query_lower in corp_name_eng:
                            if len(matches) < 5:
                                matches.append({
                                    "name": corp.get("corp_name", ""),
                                    "name_eng": corp.get("corp_name_eng", ""),
                                    "corp_code": corp.get("corp_code", ""),
                                    "stock_code": corp.get("stock_code", ""),
                                    "country": "KR",
                                    "source": "DART",
                                    "entity_type": "COMPANY",
                                    "match_type": "partial"
                                })

            # Sort: exact matches first
            matches.sort(key=lambda x: 0 if x.get("match_type") == "exact" else 1)

            result_count = len(matches)
            search_type = "top companies" if not self._full_data_loaded else "full database"
            logger.info(f"✅ DART found {result_count} matches for '{company_name}' from {search_type}")
            return matches[:5]  # Return top 5 results

        except Exception as e:
            logger.exception(f"❌ DART search error: {e}")
            return []

    def _get_top_korean_companies(self) -> List[Dict[str, Any]]:
        """Get pre-loaded top Korean companies for INSTANT searches"""
        # Top Korean companies by market cap and recognition
        top_companies = [
            {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "corp_name_eng": "Samsung Electronics Co., Ltd.",
                "stock_code": "005930"
            },
            {
                "corp_code": "00164742",
                "corp_name": "현대자동차",
                "corp_name_eng": "Hyundai Motor Company",
                "stock_code": "005380"
            },
            {
                "corp_code": "00164779",
                "corp_name": "현대모비스",
                "corp_name_eng": "Hyundai Mobis Co., Ltd.",
                "stock_code": "012330"
            },
            {
                "corp_code": "00356361",
                "corp_name": "LG화학",
                "corp_name_eng": "LG Chem, Ltd.",
                "stock_code": "051910"
            },
            {
                "corp_code": "00120030",
                "corp_name": "SK하이닉스",
                "corp_name_eng": "SK Hynix, Inc.",
                "stock_code": "000660"
            },
            {
                "corp_code": "00155319",
                "corp_name": "POSCO",
                "corp_name_eng": "POSCO",
                "stock_code": "005490"
            },
            {
                "corp_code": "00130641",
                "corp_name": "LG전자",
                "corp_name_eng": "LG Electronics Inc.",
                "stock_code": "066570"
            },
            {
                "corp_code": "00159193",
                "corp_name": "카카오",
                "corp_name_eng": "Kakao Corp.",
                "stock_code": "035720"
            },
            {
                "corp_code": "00164788",
                "corp_name": "현대건설",
                "corp_name_eng": "Hyundai Engineering & Construction Co., Ltd.",
                "stock_code": "000720"
            },
            {
                "corp_code": "00266961",
                "corp_name": "셀트리온",
                "corp_name_eng": "Celltrion, Inc.",
                "stock_code": "068270"
            }
        ]

        logger.info(f"✅ Pre-loaded {len(top_companies)} top Korean companies for instant search")
        return top_companies

    def _load_full_corp_data(self) -> List[Dict[str, Any]]:
        """Load complete corporation data from DART API"""
        try:
            logger.info("📡 Downloading complete DART corporation database...")

            url = f"{self.base_url}/corpCode.xml"
            params = {"crtfc_key": self.api_key}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            corps = []
            for corp in root.findall(".//list"):
                corp_data = {
                    "corp_code": corp.find("corp_code").text if corp.find("corp_code") is not None else "",
                    "corp_name": corp.find("corp_name").text if corp.find("corp_name") is not None else "",
                    "corp_name_eng": corp.find("corp_name_eng").text if corp.find("corp_name_eng") is not None else "",
                    "stock_code": corp.find("stock_code").text if corp.find("stock_code") is not None else "",
                    "modify_date": corp.find("modify_date").text if corp.find("modify_date") is not None else ""
                }
                corps.append(corp_data)

            logger.info(f"✅ Loaded complete database: {len(corps)} Korean corporations")
            return corps

        except Exception as e:
            logger.exception(f"❌ Failed to load complete DART database: {e}")
            return []

    def get_company_info(self, corp_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed company information"""
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/company.json"
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [{}])[0] if data.get("list") else {}

            return None

        except Exception as e:
            logger.exception(f"Failed to get company info for {corp_code}: {e}")
            return None

# Global adapter instance
dart_adapter = DARTAdapter()

def search_dart(company_name: str) -> List[Dict[str, Any]]:
    """Convenience function for DART search"""
    return dart_adapter.search_company(company_name)
