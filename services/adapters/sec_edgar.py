import os
import time
from typing import Any, Dict, Optional, List

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

    def __init__(self, user_agent: Optional[str] = None, timeout: float = 20.0):
        ua = user_agent or os.getenv("SEC_USER_AGENT") or os.getenv("EDGAR_USER_AGENT")
        if not ua:
            # Default safe UA; recommend setting SEC_USER_AGENT in env for production
            ua = "Risklytics/1.0 (risklytics@example.com)"
        self.headers = {
            "User-Agent": ua,
            "Accept": "application/json,text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
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

    def _parse_proxy_html(self, html: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse proxy HTML to extract executives and major holders with multiple heuristics."""
        import re
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text("\n")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        executives: List[Dict[str, str]] = []
        holders: List[Dict[str, str]] = []

        # Regex patterns
        pct_pat = re.compile(r"(\d{1,2}(?:\.\d{1,2})?)\s*%")
        # Support mixed-case personal names with optional middle initial
        person_pat = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+){1,3})")
        # Uppercase institution names (captures GROUP/CAPITAL/etc.)
        inst_keywords = [
            'GROUP','CAPITAL','ADVISORS','ADVISERS','MANAGEMENT','TRUST','LLC','INC','INC.','LP','HOLDINGS','PARTNERS',
            'BLACKROCK','VANGUARD','STATE STREET','T. ROWE','FIDELITY','GEODE','BERKSHIRE','MORGAN STANLEY','GOLDMAN'
        ]
        inst_pat = re.compile(r"([A-Z][A-Z&.,\- ]{3,})")

        def pick_name(span: str) -> Optional[str]:
            m = person_pat.search(span)
            if m:
                return m.group(1)
            # Try uppercase institution blocks and keep ones with known keywords
            for m2 in inst_pat.finditer(span):
                raw = m2.group(1).strip(' ,.-')
                if any(k in raw for k in inst_keywords) and len(raw) <= 80:
                    return raw
            return None

        # 1) Ownership sections
        for i, ln in enumerate(lines):
            low = ln.lower()
            if ("security ownership" in low) or ("beneficial ownership" in low) or ("principal shareholders" in low):
                block = " ".join(lines[i:i+200])
                for m in pct_pat.finditer(block):
                    span = block[max(0, m.start()-160):m.end()+160]
                    nm = pick_name(span)
                    if nm:
                        holders.append({"name": nm, "ownership": m.group(1) + "%"})

        # 2) Table-based ownership parsing
        for table in soup.find_all("table"):
            txt = table.get_text(" ", strip=True)
            if not txt:
                continue
            low = txt.lower()
            if ("ownership" in low or "%" in low or "beneficial" in low) and ("name" in low or "holder" in low):
                for m in pct_pat.finditer(txt):
                    span = txt[max(0, m.start()-160):m.end()+160]
                    nm = pick_name(span)
                    if nm:
                        holders.append({"name": nm, "ownership": m.group(1) + "%"})

        # 3) Executives by titles keywords
        exec_keywords = [
            "chief executive", "chief financial", "chief operating", "ceo", "cfo", "coo",
            "chair", "director", "president", "senior vice president", "executive vice president", "general counsel"
        ]
        for ln in lines:
            low = ln.lower()
            if any(k in low for k in exec_keywords):
                nm = person_pat.search(ln) or inst_pat.search(ln)
                if nm:
                    executives.append({"name": nm.group(1).strip(' ,.-'), "title": ln})

        # Deduplicate and cap
        def dedup(items, key):
            seen = set()
            out = []
            for it in items:
                k = it.get(key)
                if k and k not in seen:
                    seen.add(k)
                    out.append(it)
            return out

        return {
            "executives": dedup(executives, "name")[:30],
            "holders": dedup(holders, "name")[:30],
        }

    def extract_major_holders_and_executives_from_proxy(self, cik: str, accession: str, primary_doc: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse a specific proxy HTML document."""
        import requests
        cik_int = int(cik)
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{primary_doc}"
        r = requests.get(url, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return self._parse_proxy_html(r.text)

    def extract_from_proxy_best_effort(self, cik: str, accession: str, primary_doc: Optional[str] = None, max_files: int = 6) -> Dict[str, List[Dict[str, str]]]:
        """Try primary document, then fall back to scanning several HTML files from index.json."""
        import requests
        results = {"executives": [], "holders": []}
        cik_int = int(cik)

        def merge(a, b):
            return {
                "executives": (a.get("executives") or []) + (b.get("executives") or []),
                "holders": (a.get("holders") or []) + (b.get("holders") or []),
            }

        # 1) Try primary document first
        if primary_doc:
            try:
                url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{primary_doc}"
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                r.raise_for_status()
                results = merge(results, self._parse_proxy_html(r.text))
            except Exception:
                pass

        # 2) If still empty, scan index for other HTML files
        if not results["executives"] and not results["holders"]:
            try:
                idx = self.get_filing_index(cik, accession)
                items = ((idx.get("directory") or {}).get("item")) or []
                # Prefer likely proxy HTMLs: contain 'def', 'proxy', then by size desc
                def score(it):
                    name = str(it.get("name", "")).lower()
                    size = int(it.get("size", 0) or 0)
                    prio = 2 if ("def" in name or "proxy" in name) else 1
                    return (prio, size)
                htmls = [it for it in items if str(it.get("name", "")).lower().endswith((".htm", ".html"))]
                htmls.sort(key=score, reverse=True)
                for it in htmls[:max_files]:
                    name = it.get("name")
                    if not name or name == primary_doc:
                        continue
                    try:
                        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{name}"
                        r = requests.get(url, headers=self.headers, timeout=self.timeout)
                        r.raise_for_status()
                        parsed = self._parse_proxy_html(r.text)
                        # Merge and break early if we found enough
                        results = merge(results, parsed)
                        if len(results["executives"]) >= 5 and len(results["holders"]) >= 3:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        # Final dedup
        def dedup(items, key):
            seen = set()
            out = []
            for it in items:
                k = it.get(key)
                if k and k not in seen:
                    seen.add(k)
                    out.append(it)
            return out
        results["executives"] = dedup(results.get("executives", []), "name")[:30]
        results["holders"] = dedup(results.get("holders", []), "name")[:30]
        return results


sec_edgar_adapter: Optional[SecEdgarAdapter] = None


def get_sec_edgar_adapter() -> SecEdgarAdapter:
    global sec_edgar_adapter
    if sec_edgar_adapter is None:
        sec_edgar_adapter = SecEdgarAdapter()
    return sec_edgar_adapter
