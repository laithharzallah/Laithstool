import os
import base64
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

DEFAULT_BASE_URL = "https://api.company-information.service.gov.uk"


class CompaniesHouseError(Exception):
    pass


class CompaniesHouseAdapter:
    """Thin wrapper for UK Companies House API.

    Auth: Basic auth with API key as username, blank password.
    Rate limit: 600 requests / 5 minutes. Keep modest timeouts and retries.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.api_key = api_key or os.getenv("UK_CH_API_KEY") or os.getenv("COMPANIES_HOUSE_API_KEY") or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = max(3.0, float(timeout))
        if not self.api_key:
            raise CompaniesHouseError("Companies House API key not set in UK_CH_API_KEY or COMPANIES_HOUSE_API_KEY")

        token = base64.b64encode(f"{self.api_key}:".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "Risklytics-CH/1.0",
        }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, retries: int = 2) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_err: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=self._headers, params=params or {}, timeout=self.timeout)
                if resp.status_code == 429:
                    # simple backoff then retry
                    time.sleep(1 + attempt)
                    continue
                if resp.status_code >= 400:
                    raise CompaniesHouseError(f"HTTP {resp.status_code}: {resp.text[:300]}")
                return resp.json()
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise CompaniesHouseError(f"Request failed for {path}: {e}")
        raise CompaniesHouseError(f"Request failed for {path}: {last_err}")

    # --- Company info ---
    def get_company_profile(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}")

    def get_registered_office_address(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/registered-office-address")

    def get_filing_history(self, company_number: str, items_per_page: int = 50) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/filing-history", params={"items_per_page": items_per_page})

    def get_charges(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/charges")

    def get_insolvency(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/insolvency")

    def get_registers(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/registers")

    # --- Officers ---
    def get_company_officers(self, company_number: str, items_per_page: int = 50) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/officers", params={"items_per_page": items_per_page})

    def get_officer_appointments(self, officer_id: str, items_per_page: int = 50) -> Dict[str, Any]:
        return self._get(f"officers/{officer_id}/appointments", params={"items_per_page": items_per_page})

    # --- PSC ---
    def get_psc_list(self, company_number: str, items_per_page: int = 50) -> Dict[str, Any]:
        return self._get(
            f"company/{company_number}/persons-with-significant-control",
            params={"items_per_page": items_per_page},
        )

    def get_psc_individual(self, company_number: str, psc_id: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/persons-with-significant-control/individual/{psc_id}")

    def get_psc_corporate(self, company_number: str, psc_id: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/persons-with-significant-control/corporate-entity/{psc_id}")

    def get_psc_corporate_beneficial(self, company_number: str, psc_id: str) -> Dict[str, Any]:
        return self._get(
            f"company/{company_number}/persons-with-significant-control/corporate-entity-beneficial-owner/{psc_id}"
        )

    def get_psc_legal_person(self, company_number: str, psc_id: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/persons-with-significant-control/legal-person/{psc_id}")

    def get_psc_statements(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"company/{company_number}/persons-with-significant-control-statements")

    # --- Search ---
    def search_companies(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        return self._get("search/companies", params={"q": query, "items_per_page": items_per_page})

    def search_officers(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        return self._get("search/officers", params={"q": query, "items_per_page": items_per_page})

    def search_disqualified_officers(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        return self._get("search/disqualified-officers", params={"q": query, "items_per_page": items_per_page})

    def search_all(self, query: str, items_per_page: int = 20) -> Dict[str, Any]:
        return self._get("search", params={"q": query, "items_per_page": items_per_page})


# Singleton helper if needed
companies_house_adapter: Optional[CompaniesHouseAdapter] = None

def get_companies_house_adapter() -> CompaniesHouseAdapter:
    global companies_house_adapter
    if companies_house_adapter is None:
        companies_house_adapter = CompaniesHouseAdapter()
    return companies_house_adapter
