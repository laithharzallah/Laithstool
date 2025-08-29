"""
OpenCorporates API Adapter for Global Company Registry
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("opencorporates-adapter")

class OpenCorporatesAdapter:
    """OpenCorporates global company database"""

    def __init__(self):
        self.api_key = os.getenv("OPENCORPORATES_API_KEY", "")
        self.base_url = "https://api.opencorporates.com/v0.4"

    def search_company(self, company_name: str, country_code: str = "") -> List[Dict[str, Any]]:
        """Search for companies by name"""
        try:
            url = f"{self.base_url}/companies/search"
            params = {
                "q": company_name,
                "per_page": 10
            }

            if self.api_key:
                params["api_token"] = self.api_key

            if country_code:
                params["jurisdiction_code"] = country_code.lower()

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            results = []
            for company in data.get("results", {}).get("companies", []):
                company_data = company.get("company", {})

                result = {
                    "name": company_data.get("name", ""),
                    "company_number": company_data.get("company_number", ""),
                    "jurisdiction_code": company_data.get("jurisdiction_code", ""),
                    "country": self._jurisdiction_to_country(company_data.get("jurisdiction_code", "")),
                    "incorporation_date": company_data.get("incorporation_date", ""),
                    "dissolution_date": company_data.get("dissolution_date", ""),
                    "company_type": company_data.get("company_type", ""),
                    "registry_url": company_data.get("registry_url", ""),
                    "source": "OpenCorporates",
                    "entity_type": "COMPANY"
                }

                # Add address if available
                address_data = company_data.get("registered_address_in_full", "")
                if address_data:
                    result["address"] = address_data

                results.append(result)

            logger.info(f"OpenCorporates found {len(results)} matches for '{company_name}'")
            return results

        except Exception as e:
            logger.exception(f"OpenCorporates search error: {e}")
            return []

    def get_company_details(self, company_number: str, jurisdiction_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed company information"""
        try:
            url = f"{self.base_url}/companies/{jurisdiction_code}/{company_number}"
            params = {}

            if self.api_key:
                params["api_token"] = self.api_key

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("results", {}).get("company"):
                company = data["results"]["company"]

                return {
                    "name": company.get("name", ""),
                    "company_number": company.get("company_number", ""),
                    "jurisdiction_code": company.get("jurisdiction_code", ""),
                    "country": self._jurisdiction_to_country(company.get("jurisdiction_code", "")),
                    "incorporation_date": company.get("incorporation_date", ""),
                    "company_type": company.get("company_type", ""),
                    "status": company.get("status", ""),
                    "registry_url": company.get("registry_url", ""),
                    "branch": company.get("branch", ""),
                    "address": company.get("registered_address_in_full", ""),
                    "source": "OpenCorporates",
                    "entity_type": "COMPANY"
                }

            return None

        except Exception as e:
            logger.exception(f"OpenCorporates details error: {e}")
            return None

    def _jurisdiction_to_country(self, jurisdiction_code: str) -> str:
        """Convert jurisdiction code to country name"""
        # Simple mapping for common jurisdictions
        jurisdiction_map = {
            "us": "United States",
            "us_de": "United States (Delaware)",
            "us_ca": "United States (California)",
            "us_ny": "United States (New York)",
            "gb": "United Kingdom",
            "de": "Germany",
            "fr": "France",
            "nl": "Netherlands",
            "cn": "China",
            "jp": "Japan",
            "kr": "South Korea",
            "sg": "Singapore",
            "hk": "Hong Kong",
            "au": "Australia",
            "ca": "Canada",
            "ch": "Switzerland",
            "se": "Sweden",
            "no": "Norway",
            "dk": "Denmark",
            "fi": "Finland",
            "at": "Austria",
            "be": "Belgium",
            "pt": "Portugal",
            "es": "Spain",
            "it": "Italy",
            "pl": "Poland",
            "cz": "Czech Republic",
            "hu": "Hungary",
            "ru": "Russia",
            "in": "India",
            "br": "Brazil",
            "mx": "Mexico",
            "ar": "Argentina",
            "za": "South Africa",
            "ae": "United Arab Emirates",
            "sa": "Saudi Arabia"
        }

        return jurisdiction_map.get(jurisdiction_code.lower(), jurisdiction_code.upper())

# Global adapter instance
opencorporates_adapter = OpenCorporatesAdapter()

def search_opencorporates(company_name: str) -> List[Dict[str, Any]]:
    """Convenience function for OpenCorporates search"""
    return opencorporates_adapter.search_company(company_name)
