import os
import time
from typing import Any, Dict, Optional

import requests

BASE_URL = "https://data.sec.gov"


class SecEdgarError(Exception):
    pass


class SecEdgarAdapter:
    """Adapter for SEC EDGAR public data endpoints.

    Notes:
    - No API key, but requires a descriptive User-Agent: e.g. "Risklytics/1.0 (email@domain)".
    - Be polite: ~10 req/s. This adapter includes minimal sleep between retries.
    """

    def __init__(self, user_agent: Optional[str] = None, timeout: float = 12.0):
        ua = user_agent or os.getenv("SEC_USER_AGENT") or os.getenv("EDGAR_USER_AGENT")
        if not ua:
            # Default safe UA; recommend setting SEC_USER_AGENT in env for production
            ua = "Risklytics/1.0 (risklytics@example.com)"
        self.headers = {"User-Agent": ua, "Accept": "application/json"}
        self.timeout = max(5.0, float(timeout))

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, retries: int = 2) -> Dict[str, Any]:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        last_err: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=self.headers, params=params or {}, timeout=self.timeout)
                if resp.status_code == 429:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if resp.status_code >= 400:
                    raise SecEdgarError(f"HTTP {resp.status_code}: {resp.text[:300]}")
                # Some archives return JSON files under Archives domain too
                ctype = resp.headers.get("Content-Type", "")
                if "application/json" in ctype or url.endswith(".json"):
                    return resp.json()
                return {"raw": resp.text}
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise SecEdgarError(f"Request failed for {path}: {e}")
        raise SecEdgarError(f"Request failed for {path}: {last_err}")

    @staticmethod
    def normalize_cik(cik: str) -> str:
        cik_digits = str(int(cik))  # strip leading zeros if provided
        return cik_digits.zfill(10)

    # --- Company endpoints ---
    def get_company_submissions(self, cik: str) -> Dict[str, Any]:
        cik10 = self.normalize_cik(cik)
        return self._get(f"submissions/CIK{cik10}.json")

    def get_company_facts(self, cik: str) -> Dict[str, Any]:
        cik10 = self.normalize_cik(cik)
        return self._get(f"api/xbrl/companyfacts/CIK{cik10}.json")

    def get_company_concept(self, cik: str, taxonomy: str, tag: str) -> Dict[str, Any]:
        cik10 = self.normalize_cik(cik)
        return self._get(f"api/xbrl/companyconcept/CIK{cik10}/{taxonomy}/{tag}.json")

    # --- Archives helper (filing index.json or document) ---
    def get_filing_index(self, cik: str, accession_no_nohyphen: str) -> Dict[str, Any]:
        cik_int = int(cik)
        return self._get(f"/Archives/edgar/data/{cik_int}/{accession_no_nohyphen}/index.json")

    def get_archive_document(self, cik: str, accession_no_nohyphen: str, filename: str) -> Dict[str, Any]:
        cik_int = int(cik)
        return self._get(f"/Archives/edgar/data/{cik_int}/{accession_no_nohyphen}/{filename}")


sec_edgar_adapter: Optional[SecEdgarAdapter] = None


def get_sec_edgar_adapter() -> SecEdgarAdapter:
    global sec_edgar_adapter
    if sec_edgar_adapter is None:
        sec_edgar_adapter = SecEdgarAdapter()
    return sec_edgar_adapter
