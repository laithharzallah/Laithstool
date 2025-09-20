"""
DART (Data Analysis, Retrieval and Transfer) API Adapter for Korean Companies
FAST & TARGETED VERSION - Only real DART endpoints
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional
import io, zipfile, xml.etree.ElementTree as ET
import time

logger = logging.getLogger("dart-adapter")

# -------------------- Simple in-memory caches --------------------
_CORP_LIST_CACHE: Optional[List[Dict[str, Any]]] = None
_CORP_LIST_FETCHED_AT: float = 0.0
_SEARCH_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_SEARCH_CACHE_TTL = 1800.0  # 30 minutes

def _now() -> float:
    return time.time()

def _translate_to_korean(text: str) -> str:
    """Translate company name to Korean legal/company name form for better DART search."""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or not text.strip():
        return text
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Translate the company name to Korean legal/company name form. Return text only."},
                {"role":"user","content": text.strip()}
            ],
            temperature=0,
            max_tokens=50
        )
        return (resp.choices[0].message.content or text).strip()
    except Exception as e:
        logger.warning(f"Translation failed for '{text}': {e}")
        return text

class DARTAdapter:
    """Korea Financial Supervisory Service DART API - FAST TARGETED VERSION"""

    def __init__(self):
        # Use provided API key (no hardcoded default)
        self.api_key = os.getenv("DART_API_KEY", "")
        self.base_url = "https://opendart.fss.or.kr/api"

    def _get(self, path: str, **params) -> dict:
        """Minimal HTTP helper for DART API calls (strict - surfaces errors)."""
        params = {"crtfc_key": self.api_key, **params}
        try:
            r = requests.get(f"{self.base_url}/{path}", params=params, timeout=8)
        except requests.Timeout:
            logger.error("DART %s timed out with params=%s", path, params)
            return {"status": "408", "message": "DART request timed out"}
        except Exception as e:
            logger.error("DART %s request error: %s", path, e)
            return {"status": "500", "message": f"request error: {e}"}
        try:
            js = r.json()
        except Exception:
            js = {"status": "999", "message": f"invalid json (HTTP {r.status_code})", "raw": r.text[:500]}
        # If not OK, include the raw bits so you can see why
        if js.get("status") != "000":
            logger.error("DART %s error status=%s msg=%s params=%s",
                         path, js.get("status"), js.get("message"), params)
        return js

    def _ensure_corp_list_cache(self) -> List[Dict[str, Any]]:
        global _CORP_LIST_CACHE, _CORP_LIST_FETCHED_AT
        # Reuse for 24h
        if _CORP_LIST_CACHE and (_now() - _CORP_LIST_FETCHED_AT) < 86400:
            return _CORP_LIST_CACHE

        try:
            r = requests.get(f"{self.base_url}/corpCode.xml", params={"crtfc_key": self.api_key}, timeout=20)
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                xml_name = zf.namelist()[0]
                xml_bytes = zf.read(xml_name)
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            logger.error("Failed downloading/parsing corpCode.zip: %s", e)
            return _CORP_LIST_CACHE or []

        items: List[Dict[str, Any]] = []
        for corp in root.findall('.//list'):
            items.append({
                "corp_code": (corp.findtext('corp_code') or '').strip(),
                "corp_name": (corp.findtext('corp_name') or '').strip(),
                "corp_name_eng": (corp.findtext('corp_name_eng') or '').strip(),
                "stock_code": (corp.findtext('stock_code') or '').strip(),
            })
        _CORP_LIST_CACHE = items
        _CORP_LIST_FETCHED_AT = _now()
        logger.info("Cached %d corp entries from corpCode.xml", len(items))
        return items

    def _lookup_corp_codes_via_zip(self, query: str) -> List[Dict[str, Any]]:
        """Fallback: download corpCode.xml ZIP once and search locally.

        Matches by partial corp_name (ko/en) or stock_code tokens.
        """
        if not self.api_key or not query.strip():
            return []

        items = self._ensure_corp_list_cache()
        if not items:
            return []
        q = query.strip().lower().replace(" ", "")
        # Common aliases for SK hynix
        aliases = {q}
        if "sk" in q and "hynix" in q:
            aliases.update(["skhynix", "에스케이하이닉스", "하이닉스", "sk하이닉스"]) 

        results: List[Dict[str, Any]] = []
        for corp in items:
            cc = corp.get('corp_code', '')
            name_ko = corp.get('corp_name', '')
            name_en = corp.get('corp_name_eng', '')
            stock = corp.get('stock_code', '')
            key_ko = name_ko.lower().replace(" ", "")
            key_en = name_en.lower().replace(" ", "")
            if not cc:
                continue
            match = False
            if any(a in key_ko for a in aliases) or any(a in key_en for a in aliases):
                match = True
            if q and stock and q in stock:
                match = True
            if match:
                results.append({
                    "name": name_ko or name_en or "Unknown",
                    "corp_code": cc,
                    "stock_code": stock,
                    "country": "KR",
                    "source": "DART",
                    "entity_type": "COMPANY",
                    "match_type": "corpCode.xml"
                })
                if len(results) >= 5:
                    break
        return results

    def search_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Targeted search via filings; retries in Korean if first pass empty."""
        if not (self.api_key and company_name.strip()):
            return []

        def _norm(s: str) -> str:
            return (s or "").lower().replace(" ", "").replace(".", "").replace("-", "")

        # Cache hot queries to avoid repeated network/zip work
        key = _norm(company_name)
        cached = _SEARCH_CACHE.get(key)
        if cached and (_now() - _CORP_LIST_FETCHED_AT) < _SEARCH_CACHE_TTL:
            return cached

        def _search_once(name: str) -> List[Dict[str, Any]]:
            from datetime import datetime, timedelta
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            today = datetime.now().strftime('%Y%m%d')

            js = self._get(
                "list.json",
                corp_name=name.strip(),
                bgn_de=three_months_ago,
                end_de=today,
                page_no=1,
                page_count=50
            )
            rows = js.get("list") or []
            seen, out = set(), []
            for it in rows:
                cc, cn = it.get("corp_code"), it.get("corp_name")
                if not cc or not cn or cc in seen:
                    continue
                seen.add(cc)
                out.append({
                    "name": cn,
                    "corp_code": cc,
                    "stock_code": it.get("stock_code",""),
                    "country": "KR",
                    "source": "DART",
                    "entity_type": "COMPANY",
                    "match_type": "list.json"
                })
                if len(out) >= 5:
                    break
            return out

        # 1) First try as-is (works if you already used Korean). If low-quality, fall back.
        out = _search_once(company_name)
        if out:
            qn = _norm(company_name)
            has_good = any(qn in _norm(item.get("name")) for item in out)
            if has_good:
                return out

        # 2) If empty and the name looks English/Arabic/etc., translate to Korean and retry
        ko = _translate_to_korean(company_name)
        if ko and ko != company_name:
            logger.info("Retrying DART search with Korean name: %s", ko)
            out = _search_once(ko)
            if out:
                qn = _norm(ko)
                has_good = any(qn in _norm(item.get("name")) for item in out)
                if has_good:
                    return out

        # 3) Final fallback: corpCode.zip directory search
        logger.info("Falling back to corpCode.xml lookup for: %s", company_name)
        out = self._lookup_corp_codes_via_zip(company_name)
        _SEARCH_CACHE[key] = out
        return out

    def search_filings(self, corp_code: str, years_back: int = 5) -> List[Dict[str, Any]]:
        """Search for ALL filings for a company over specified years (optimized for speed)."""
        if not (self.api_key and corp_code):
            return []

        from datetime import datetime
        current_year = datetime.now().year
        start_year = current_year - years_back

        all_filings = []

        # OPTIMIZATION: Use broader date ranges to reduce API calls
        # Instead of 1 call per year, use 1 call per 2 years
        for start in range(start_year, current_year + 1, 2):
            end = min(start + 1, current_year)
            logger.info(f"Searching filings for {corp_code} in {start}-{end}...")

            # Search for all filing types in this period
            js = self._get(
                "list.json",
                corp_code=corp_code,
                bgn_de=f"{start}0101",
                end_de=f"{end}1231",
                page_no=1,
                page_count=100  # Get many filings per period
            )

            filings = js.get("list") or []
            for filing in filings:
                filing_data = {
                    "corp_code": filing.get("corp_code"),
                    "corp_name": filing.get("corp_name"),
                    "stock_code": filing.get("stock_code"),
                    "report_nm": filing.get("report_nm"),
                    "rcept_no": filing.get("rcept_no"),
                    "flr_nm": filing.get("flr_nm"),
                    "rcept_dt": filing.get("rcept_dt"),
                    "rm": filing.get("rm")
                }
                all_filings.append(filing_data)

        logger.info(f"✅ Found {len(all_filings)} total filings for {corp_code} over {years_back} years")
        return all_filings



    def get_complete_company_info(self, corp_code: str, year: str = "2024") -> Dict[str, Any]:
        """Full snapshot from DART (real endpoints only) - defensive version."""
        if not (self.api_key and corp_code):
            return {"error": "API key or corp_code missing"}

        # basics - try company.json endpoint
        basic_js = self._get("company.json", corp_code=corp_code)
        logger.info(f"Company.json response: {basic_js}")

        basic_row = {}
        if isinstance(basic_js.get("list"), list) and basic_js["list"]:
            basic_row = basic_js["list"][0]
            logger.info(f"Found basic info from list[0]: {basic_row}")
        elif isinstance(basic_js.get("company"), dict):
            basic_row = basic_js["company"]
            logger.info(f"Found basic info from company: {basic_row}")
        else:
            logger.warning(f"No basic info found in response: {basic_js}")

        # If basic info is empty, try getting it from the list endpoint
        if not basic_row or not any(basic_row.values()):
            logger.info("Basic info empty, trying to get from list.json...")
            # DART API requires 3-month limit when searching by corp_code
            from datetime import datetime, timedelta
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            today = datetime.now().strftime('%Y%m%d')
            list_js = self._get("list.json", corp_code=corp_code, bgn_de=three_months_ago, end_de=today, page_no=1, page_count=1)
            if list_js.get("list") and len(list_js["list"]) > 0:
                list_item = list_js["list"][0]
                basic_row = {
                    "corp_name": list_item.get("corp_name"),
                    "stock_code": list_item.get("stock_code"),
                    "corp_code": corp_code
                }
                logger.info(f"Using basic info from list.json: {basic_row}")

        # ≥5% holders
        major_js = self._get("majorstock.json", corp_code=corp_code)
        majors = []
        for it in (major_js.get("list") or []):
            majors.append({
                "holder": it.get("repror"),                      # shareholder name (Korean)
                "ratio": it.get("stkrt"),                        # ownership ratio
                "report_date": it.get("rcept_dt"),               # report date
                "change_reason": it.get("report_resn"),          # report reason
            })

        # executives / major shareholders (insiders)
        exec_js = self._get("elestock.json", corp_code=corp_code)
        execs = []
        for it in (exec_js.get("list") or []):
            execs.append({
                "name": it.get("repror"),                         # executive name (Korean)
                "relation": it.get("isu_exctv_ofcps"),            # position/title
                "chg_date": it.get("rcept_dt"),                   # change date
                "stock_code": it.get("corp_code"),                # company code
                "before": it.get("sp_stock_lmp_irds_cnt"),        # shares before change
                "after": it.get("sp_stock_lmp_cnt"),              # shares after change
            })

        # financials: fetch multiple years to avoid 3-month artifact
        financials = []
        try:
            current = int(year)
        except Exception:
            from datetime import datetime
            current = datetime.now().year

        # collect up to 5 years (current -> current-4)
        for try_year in range(current, current - 5, -1):
            fin_js = self._get(
                "fnlttSinglAcnt.json",
                corp_code=corp_code,
                bsns_year=str(try_year),
                reprt_code="11011"
            )
            rows = fin_js.get("list") or []
            if rows:
                financials.extend(rows)

        return {
            "basic_info": {
                "corp_name": basic_row.get("corp_name"),
                "ceo_nm":    basic_row.get("ceo_nm"),
                "est_dt":    basic_row.get("est_dt"),
                "acc_mt":    basic_row.get("acc_mt"),
                "adr":       basic_row.get("adr"),
                "hm_url":    basic_row.get("hm_url"),
                "phn_no":    basic_row.get("phn_no"),
                "fax_no":    basic_row.get("fax_no"),
                "corp_code": corp_code,
            },
            "shareholders": majors,      # may be empty for some issuers
            "executives":   execs,       # may be empty if no recent insider filings
            "financials":   financials   # large; filter by account_nm if needed
        }



# Global adapter instance
dart_adapter = DARTAdapter()

def search_dart(company_name: str) -> List[Dict[str, Any]]:
    """Convenience function for DART search"""
    return dart_adapter.search_company(company_name)


