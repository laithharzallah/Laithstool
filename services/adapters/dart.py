"""
DART (Data Analysis, Retrieval and Transfer) API Adapter for Korean Companies
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("dart-adapter")

class DARTAdapter:
    """Korea Financial Supervisory Service DART API"""

    def __init__(self):
        self.api_key = os.getenv("DART_API_KEY", "")
        self.base_url = "https://opendart.fss.or.kr/api"

    def search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for Korean companies by name"""
        if not self.api_key:
            logger.warning("DART_API_KEY not configured")
            return []

        try:
            # First, get company list to find corp_code
            corp_list = self._get_corp_list()

            # Find matching companies
            matches = []
            query_lower = company_name.lower()

            for corp in corp_list:
                corp_name = corp.get("corp_name", "").lower()
                corp_name_eng = corp.get("corp_name_eng", "").lower()

                if query_lower in corp_name or query_lower in corp_name_eng:
                    matches.append({
                        "name": corp.get("corp_name", ""),
                        "name_eng": corp.get("corp_name_eng", ""),
                        "corp_code": corp.get("corp_code", ""),
                        "stock_code": corp.get("stock_code", ""),
                        "country": "KR",
                        "source": "DART",
                        "entity_type": "COMPANY"
                    })

            logger.info(f"DART found {len(matches)} matches for '{company_name}'")
            return matches[:5]  # Limit results

        except Exception as e:
            logger.exception(f"DART search error: {e}")
            return []

    def _get_corp_list(self) -> List[Dict[str, Any]]:
        """Get list of all corporations from DART"""
        try:
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

            logger.info(f"Loaded {len(corps)} corporations from DART")
            return corps

        except Exception as e:
            logger.exception(f"Failed to get DART corp list: {e}")
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
