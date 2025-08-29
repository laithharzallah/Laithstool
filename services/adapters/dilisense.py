"""
Dilisense API Adapter for Company Registry Integration
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("dilisense-adapter")

class DilisenseAdapter:
    """Dilisense AML compliance service adapter"""

    def __init__(self):
        self.api_key = os.getenv("DILISENSE_API_KEY", "")

    def search_company(self, company_name: str, address: str = "", country: str = "") -> List[Dict[str, Any]]:
        """Search for companies using Dilisense"""
        if not self.api_key:
            logger.warning("DILISENSE_API_KEY not configured")
            return []

        try:
            # Import the existing Dilisense service
            from ..dilisense import dilisense_service

            if not dilisense_service:
                logger.warning("Dilisense service not initialized")
                return []

            # Perform company screening
            results = dilisense_service.screen_company(company_name, country)

            # Convert to adapter format
            formatted_results = []
            for record in results.get("found_records", []):
                formatted_result = {
                    "name": record.get("name", ""),
                    "country": record.get("country", country),
                    "address": record.get("address", address),
                    "company_number": record.get("company_number", ""),
                    "incorporation_date": record.get("incorporation_date", ""),
                    "status": record.get("status", ""),
                    "source": "Dilisense",
                    "entity_type": "COMPANY",
                    "risk_score": record.get("risk_score", 0),
                    "sanctions_found": record.get("sanctions_found", False),
                    "peps_found": record.get("peps_found", False)
                }

                # Add any additional fields from the original record
                for key, value in record.items():
                    if key not in formatted_result:
                        formatted_result[key] = value

                formatted_results.append(formatted_result)

            logger.info(f"Dilisense found {len(formatted_results)} matches for '{company_name}'")
            return formatted_results

        except Exception as e:
            logger.exception(f"Dilisense adapter error: {e}")
            return []

    def get_company_details(self, company_name: str, country: str = "") -> Dict[str, Any]:
        """Get detailed company information from Dilisense"""
        try:
            from ..dilisense import dilisense_service

            if not dilisense_service:
                return {}

            results = dilisense_service.screen_company(company_name, country)
            return results

        except Exception as e:
            logger.exception(f"Dilisense details error: {e}")
            return {}

# Global adapter instance
dilisense_adapter = DilisenseAdapter()

def search_dilisense(company_name: str, address: str = "", country: str = "") -> List[Dict[str, Any]]:
    """Convenience function for Dilisense search"""
    return dilisense_adapter.search_company(company_name, address, country)
