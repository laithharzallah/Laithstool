"""
Dilisense AML Compliance Service
Provides comprehensive screening for both individuals and companies
"""

import os
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import unicodedata
import re

logger = logging.getLogger(__name__)

# Strict client timeout: total 20s, connect 5s
HTTP_TIMEOUT = httpx.Timeout(20.0, connect=5.0)

# --- Normalization helpers (for exact comparison) ---
LEGAL_SUFFIXES = r"(?:S\.?A\.?|SAE|SE|AG|GMBH|LLC|LTD\.?|PLC|PJSC|NV|BV|SPA|OYJ|AB|AS|JSC|OJSC|INC\.?|CORP\.?|CO\.?|S\.?P\.?A\.?)"
SUFFIX_RE = re.compile(rf"\b{LEGAL_SUFFIXES}\b\.?", re.IGNORECASE)

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def _normalize_org(name: str) -> str:
    # trim, collapse spaces, strip accents, drop quotes/punct that commonly vary
    n = (name or "").strip()
    n = re.sub(r"\s+", " ", n)
    n = _strip_accents(n)
    n = n.replace("'", "'").replace("`","'")
    # remove legal suffixes (for strict org equality we compare both with & without)
    n_no_suffix = SUFFIX_RE.sub("", n).strip()
    # lower + remove dots/commas/hyphens and extra spaces
    def canon(x: str) -> str:
        x = x.lower()
        x = re.sub(r"[.,''`\"()\-_/]", " ", x)
        x = re.sub(r"\s+", " ", x).strip()
        return x
    return canon(n_no_suffix)

def _normalize_person(name: str) -> str:
    n = (name or "").strip()
    n = re.sub(r"\s+", " ", n)
    n = _strip_accents(n)
    n = n.replace("'", "'").replace("`","'")
    n = n.lower()
    return n

def _candidate_org_names(base: str) -> set:
    """Build a set of canonical variants for exact comparison"""
    variants = set()
    raw = (base or "").strip()
    variants.add(_normalize_org(raw))
    # remove trailing parenthetical like "(USC)"
    variants.add(_normalize_org(re.sub(r"\s*\([^)]*\)\s*$", "", raw)))
    # also compare the raw (no suffix removal) canon as backup
    def canon_full(x: str) -> str:
        x = _strip_accents((x or "").strip())
        x = x.lower()
        x = re.sub(r"[.,''`\"()\-_/]", " ", x)
        x = re.sub(r"\s+", " ", x).strip()
        return x
    variants.add(canon_full(raw))
    return {v for v in variants if v}

def _record_name_variants(record: dict) -> set:
    """Collect all plausible name strings for a record"""
    fields = []
    def add(x):
        if not x: return
        if isinstance(x, str): fields.append(x)
        elif isinstance(x, list):
            for i in x:
                if i: fields.append(str(i))
    add(record.get("name"))
    add(record.get("alias_names"))
    add(record.get("also_known_as"))
    add(record.get("other_names"))
    add(record.get("entity_name"))
    out = set()
    for f in fields:
        out.add(_normalize_org(f))
        # also keep a fully-canon variant
        fc = _strip_accents(f).lower()
        fc = re.sub(r"[.,''`\"()\-_/]", " ", fc)
        fc = re.sub(r"\s+", " ", fc).strip()
        out.add(fc)
    return {x for x in out if x}

def _exact_company_match(record: dict, company: str) -> bool:
    # If record is clearly an INDIVIDUAL and this is a company screening, skip
    ent_type = (record.get("entity_type") or "").upper()
    if ent_type == "INDIVIDUAL":
        return False
    targets = _candidate_org_names(company)
    names = _record_name_variants(record)
    # Exact equality on any normalized variant
    return any(n in targets or t in names for n in names for t in targets)

def _country_consistent(record: dict, country: str) -> bool:
    if not country:
        return True
    pool = []
    for k in ("country", "countries", "citizenship", "address", "jurisdiction"):
        v = record.get(k)
        if isinstance(v, str):
            pool.append(v)
        elif isinstance(v, list):
            pool.extend([str(x) for x in v if x])
    c = country.lower()
    return any(c in str(x).lower() for x in pool)

class DilisenseService:
    """Dilisense AML compliance service for individual and company screening"""
    
    def __init__(self):
        """Initialize the Dilisense service"""
        self.api_key = os.getenv("DILISENSE_API_KEY")
        self.base_url = os.getenv("DILISENSE_BASE_URL", "https://api.dilisense.com/v1")
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            print(f"✅ Dilisense service initialized")
            env = (os.getenv("FLASK_ENV") or "").lower()
            if env == "development":
                print(f"🔑 API Key present (masked)")
            print(f"🌐 Base URL: {self.base_url}")
        else:
            print(f"⚠️ Dilisense service disabled - no API key found")

    # ============================================================================
    # INDIVIDUAL SCREENING METHODS
    # ============================================================================
    
    async def screen_individual(self, name: str, country: str = "", date_of_birth: str = "", gender: str = "") -> dict:
        """
        Screen individual with intelligent name variations for better PEP detection
        """
        print(f"🔍 Screening individual: {name}")
        
        # Generate multiple name variations for better matching
        name_variations = self._generate_name_variations(name)
        print(f"🔍 Trying {len(name_variations)} name variations: {name_variations}")
        
        all_results = []
        best_result = None
        highest_hits = 0
        
        # Try each name variation
        for variation in name_variations:
            try:
                print(f"🔍 Trying variation: {variation}")
                result = await self._check_individual_single(variation, country, date_of_birth, gender)
                
                if result and not result.get("error"):
                    all_results.append({
                        "variation": variation,
                        "result": result,
                        "total_hits": result.get("total_hits", 0)
                    })
                    
                    # Track the best result (most hits)
                    if result.get("total_hits", 0) > highest_hits:
                        highest_hits = result.get("total_hits", 0)
                        best_result = result
                        
                    print(f"✅ Variation '{variation}' found {result.get('total_hits', 0)} hits")
                else:
                    print(f"⚠️ Variation '{variation}' failed or no results")
                    
            except Exception as e:
                print(f"⚠️ Error with variation '{variation}': {e}")
                continue
        
        # Combine all results intelligently
        if all_results:
            combined_result = self._combine_individual_results(all_results, name)
            print(f"✅ Combined results from {len(all_results)} variations, total hits: {combined_result.get('total_hits', 0)}")
            return combined_result
        else:
            print(f"❌ No results found for any name variation")
            return self._create_empty_individual_result(name, country, date_of_birth, gender)
    
    def _generate_name_variations(self, name: str) -> list:
        """
        Generate specific, conservative variations. Never emit 1-token names.
        Handle Arabic 'Al'/'Al-' prefixes sanely.
        """
        original = name.strip()
        clean_name = original.upper()
        # Remove common titles and honorifics
        titles_to_remove = ['MR ', 'DR ', 'PROF ', 'SHEIKH ', 'HIS EXCELLENCY ', 'HONORABLE ']
        for title in titles_to_remove:
            if clean_name.startswith(title):
                clean_name = clean_name[len(title):]
                break
        parts = clean_name.split()
        if len(parts) < 2:
            return [original]
        first = parts[0].title()
        last = parts[-1].title()
        last_norm = last.replace('Al-', 'Al ').replace('AL-', 'Al ').replace('AL ', 'Al ').replace('AL', 'Al')
        last_no_al = last_norm.replace('Al ', '')
        specific_variations = []
        if len(parts) >= 3:
            middle = " ".join(p.title() for p in parts[1:-1])
            specific_variations.append(f"{first} {middle} {last_norm}".strip())
        specific_variations.extend([
            f"{first} {last_norm}".strip(),
            f"{first} {last_no_al}".strip(),
            f"{last_norm} {first}".strip(),
        ])
        seen = set(); out = []
        for v in [original] + specific_variations:
            v = " ".join(v.split())
            if not v or " " not in v:
                continue
            key = v.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(v)
        out.sort(key=lambda x: (x.lower() != original.lower(), len(x)))
        return out[:5]
    
    async def _check_individual_single(self, name: str, country: str = "", date_of_birth: str = "", gender: str = "") -> dict:
        """
        Check individual with a single name variation
        """
        try:
            # Prepare parameters with enhanced fuzzy search for high-profile individuals
            params = {
                'names': name,
                'fuzzy_search': '1',  # Enable fuzzy search
                'fuzzy_threshold': '0.7',  # Lower threshold for better matching
                'includes': 'dilisense_pep,dilisense_sanctions,dilisense_criminal,dilisense_adverse_media'
            }
            
            if country:
                params['country'] = self._normalize_country(country)
            if date_of_birth:
                params['dob'] = date_of_birth
            if gender:
                params['gender'] = gender
            
            data = await self._http_get(f"{self.base_url}/checkIndividual", params, retries=1)
            if data is None:
                print(f"❌ API error for '{name}'")
                return None
            print(f"✅ API call successful for '{name}'")
            return self._process_individual_results(data, name)
                    
        except Exception as e:
            print(f"❌ Error checking individual '{name}': {e}")
            return None
    
    def _combine_individual_results(self, all_results: list, original_name: str) -> dict:
        """
        Intelligently combine results from multiple name variations
        Focus on the specific individual, not broad family connections
        """
        if not all_results:
            return self._create_empty_individual_result(original_name)
        
        # Use the best result as base
        best_result = max(all_results, key=lambda x: x['total_hits'])
        base_result = best_result['result'].copy()
        # Ensure structures exist
        base_result.setdefault('sanctions', {}).setdefault('found_records', [])
        base_result.setdefault('pep', {}).setdefault('found_records', [])
        base_result.setdefault('criminal', {}).setdefault('found_records', [])
        base_result.setdefault('other', {}).setdefault('found_records', [])
        
        # Filter results to focus on the specific individual
        filtered_sanctions = []
        filtered_pep = []
        filtered_criminal = []
        filtered_other = []
        
        seen_records = set()
        
        # Extract key identifiers from the original name
        original_parts = original_name.upper().split()
        first_name = original_parts[0] if original_parts else ""
        last_name = original_parts[-1] if original_parts else ""
        
        for result_data in all_results:
            result = result_data['result']
            
            # Filter sanctions - only include relevant matches
            if result.get('sanctions', {}).get('found_records'):
                for record in result['sanctions']['found_records']:
                    record_id = f"s_{record.get('name', '')}_{record.get('source_id', '')}"
                    if record_id not in seen_records and self._is_relevant_match(record, first_name, last_name):
                        filtered_sanctions.append(record)
                        seen_records.add(record_id)
            
            # Filter PEP records - only include relevant matches
            if result.get('pep', {}).get('found_records'):
                for record in result['pep']['found_records']:
                    record_id = f"p_{record.get('name', '')}_{record.get('source_id', '')}"
                    if record_id not in seen_records and self._is_relevant_match(record, first_name, last_name):
                        filtered_pep.append(record)
                        seen_records.add(record_id)
            
            # Filter criminal records - only include relevant matches
            if result.get('criminal', {}).get('found_records'):
                for record in result['criminal']['found_records']:
                    record_id = f"c_{record.get('name', '')}_{record.get('source_id', '')}"
                    if record_id not in seen_records and self._is_relevant_match(record, first_name, last_name):
                        filtered_criminal.append(record)
                        seen_records.add(record_id)
            
            # Filter other records - only include relevant matches
            if result.get('other', {}).get('found_records'):
                for record in result['other']['found_records']:
                    record_id = f"o_{record.get('name', '')}_{record.get('source_id', '')}"
                    if record_id not in seen_records and self._is_relevant_match(record, first_name, last_name):
                        filtered_other.append(record)
                        seen_records.add(record_id)
        
        # Limit results to prevent overwhelming output (max 10 per category)
        filtered_sanctions = filtered_sanctions[:10]
        filtered_pep = filtered_pep[:10]
        filtered_criminal = filtered_criminal[:10]
        filtered_other = filtered_other[:10]
        
        # Update the base result with filtered data
        base_result['sanctions']['found_records'] = filtered_sanctions[:10]
        base_result['sanctions']['total_hits'] = len(base_result['sanctions']['found_records'])
        base_result['pep']['found_records'] = filtered_pep[:10]
        base_result['pep']['total_hits'] = len(base_result['pep']['found_records'])
        base_result['criminal']['found_records'] = filtered_criminal[:10]
        base_result['criminal']['total_hits'] = len(base_result['criminal']['found_records'])
        base_result['other']['found_records'] = filtered_other[:10]
        base_result['other']['total_hits'] = len(base_result['other']['found_records'])
        
        # Recalculate total hits
        base_result['total_hits'] = len(filtered_sanctions) + len(filtered_pep) + len(filtered_criminal) + len(filtered_other)
        
        # Update risk assessment
        base_result['overall_risk_level'] = self._calculate_individual_risk_level(base_result)
        # Compute risk factors inline (avoid missing helper issues)
        factors = []
        if base_result['sanctions']['total_hits'] > 0:
            factors.append("Sanctions listed")
        if base_result['pep']['total_hits'] > 0:
            factors.append("PEP status")
        if base_result['criminal']['total_hits'] > 0:
            factors.append("Criminal records")
        if base_result['other']['total_hits'] > 0:
            factors.append("Other adverse records")
        base_result['risk_factors'] = factors
        # Add risk score for downstream UIs
        base_result['risk_score'] = self._score_from_buckets(
            base_result['sanctions']['total_hits'],
            base_result['pep']['total_hits'],
            base_result['criminal']['total_hits']
        )
        
        # Add metadata about variations tried
        base_result['name_variations_tried'] = [r['variation'] for r in all_results]
        base_result['best_variation'] = best_result['variation']
        
        return base_result
    
    def _is_relevant_match(self, record: dict, first_name: str, last_name: str, country_code: str = "") -> bool:
        """Strict relevance: require last-name match; prefer country alignment if present."""
        record_name = (record.get('name') or '').upper()
        aliases = record.get('alias_names') or []
        if isinstance(aliases, str):
            aliases = [aliases]

        def has(piece: str, token: str) -> bool:
            return bool(piece) and bool(token) and token in piece

        # Require last name somewhere (name or aliases)
        if not has(record_name, last_name):
            ok = False
            for a in aliases:
                if has((a or '').upper(), last_name):
                    ok = True; break
            if not ok:
                return False

        # First name strengthens match
        if first_name and not has(record_name, first_name):
            ok = False
            for a in aliases:
                au = (a or '').upper()
                if has(au, first_name) and has(au, last_name):
                    ok = True; break
            if not ok:
                return False

        # Optional country check
        if country_code:
            cits = record.get('citizenship') or []
            if isinstance(cits, str):
                cits = [cits]
            cits_u = [c.upper() for c in cits]
            if cits_u and country_code.upper() not in cits_u:
                return False
        return True

    def _process_individual_results(self, data: Dict, name: str) -> Dict[str, Any]:
        """Process individual screening results from Dilisense API"""
        try:
            total_hits = data.get("total_hits", 0)
            found_records = data.get("found_records", [])
            
            # Categorize records by source type
            sanctions = []
            peps = []
            criminal = []
            other = []
            
            for record in found_records:
                stype = (record.get("source_type") or "").upper()
                if ("SANCTION" in stype) or ("OFAC" in stype) or ("EU" in stype):
                    sanctions.append(record)
                elif "PEP" in stype:
                    peps.append(record)
                elif ("CRIMINAL" in stype) or ("CRIME" in stype):
                    criminal.append(record)
                else:
                    other.append(record)
            
            # Build results structure
            results = {
                "name": name,
                "total_hits": total_hits,
                "sanctions": {
                    "total_hits": len(sanctions),
                    "found_records": sanctions
                },
                "pep": {
                    "total_hits": len(peps),
                    "found_records": peps
                },
                "criminal": {
                    "total_hits": len(criminal),
                    "found_records": criminal
                },
                "other": {
                    "total_hits": len(other),
                    "found_records": other
                }
            }
            
            # Determine overall risk level
            if len(sanctions) > 0:
                results["overall_risk_level"] = "High"
                results["risk_factors"] = ["Sanctions found"]
            elif len(peps) > 0:
                results["overall_risk_level"] = "Medium"
                results["risk_factors"] = ["PEP found"]
            elif len(criminal) > 0:
                results["overall_risk_level"] = "High"
                results["risk_factors"] = ["Criminal records found"]
            else:
                results["overall_risk_level"] = "Low"
                results["risk_factors"] = []
            # numeric score for UIs
            results["risk_score"] = self._score_from_buckets(len(sanctions), len(peps), len(criminal))
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to process individual results: {e}")
            return {"error": f"Data processing failed: {str(e)}"}

    def _create_empty_individual_result(self, name: str, country: str = "", date_of_birth: str = "", gender: str = "") -> dict:
        """
        Create an empty individual result structure
        """
        return {
            "name": name,
            "country": country,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "total_hits": 0,
            "sanctions": {
                "found_records": [],
                "total_hits": 0
            },
            "pep": {
                "found_records": [],
                "total_hits": 0
            },
            "criminal": {
                "found_records": [],
                "total_hits": 0
            },
            "other": {
                "found_records": [],
                "total_hits": 0
            },
            "overall_risk_level": "Low",
            "risk_factors": [],
            "risk_score": 0
        }
    
    def _calculate_individual_risk_level(self, result: dict) -> str:
        """
        Calculate overall risk level for individual
        """
        total_hits = result.get('total_hits', 0)
        
        if total_hits == 0:
            return "Low"
        elif total_hits <= 2:
            return "Medium"
        else:
            return "High"

    def _score_from_buckets(self, s: int, p: int, c: int) -> int:
        score = 0
        if s > 0:
            score += 60
        if p > 0:
            score += 25
        if c > 0:
            score += 15
        return min(100, score)

    def _normalize_country(self, country: str) -> str:
        m = {'SA':'Saudi Arabia','US':'United States','UK':'United Kingdom','EU':'European Union','UN':'United Nations','CA':'Canada','AU':'Australia'}
        c = (country or '').strip()
        return m.get(c.upper(), country)

    async def _http_get(self, url: str, params: dict, retries: int = 1) -> Optional[dict]:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            for attempt in range(retries + 1):
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        return None
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return None

    # ============================================================================
    # COMPANY SCREENING METHODS
    # ============================================================================
    
    async def screen_company(self, company_name: str, country: str = "", *, exact: bool = True) -> Dict[str, Any]:
        """
        Comprehensive company screening for sanctions, PEPs, and compliance issues
        
        Args:
            company_name: Name of the company to screen
            country: Country/jurisdiction (optional)
            
        Returns:
            Company screening results with sanctions, PEPs, and compliance data
        """
        if not self.enabled:
            return {"error": "Dilisense service not configured"}
            
        try:
            print(f"🔍 Screening company: {company_name}")
            
            # Execute all company checks in parallel
            sanctions_task = self._check_company_sanctions(company_name, country, exact=exact)
            peps_task = self._check_company_peps(company_name, country, exact=exact)
            criminal_task = self._check_company_criminal(company_name, country, exact=exact)
            
            # Wait for all checks to complete
            sanctions_result, peps_result, criminal_result = await asyncio.gather(
                sanctions_task, peps_task, criminal_task, return_exceptions=True
            )
            
            # Process results
            company_results = {
                "company_name": company_name,
                "country": country,
                "timestamp": datetime.now().isoformat(),
                "overall_risk_level": "Low",
                "risk_factors": []
            }
            
            # Process sanctions results
            if isinstance(sanctions_result, Exception):
                company_results["sanctions"] = {"error": str(sanctions_result)}
            else:
                company_results["sanctions"] = sanctions_result
                if sanctions_result.get("total_hits", 0) > 0:
                    company_results["risk_factors"].append("Sanctions found")
                    company_results["overall_risk_level"] = "High"
            
            # Process PEP results
            if isinstance(peps_result, Exception):
                company_results["pep"] = {"error": str(peps_result)}
            else:
                company_results["pep"] = peps_result
                if peps_result.get("total_hits", 0) > 0:
                    company_results["risk_factors"].append("PEP found")
                    if company_results["overall_risk_level"] != "High":
                        company_results["overall_risk_level"] = "Medium"
            
            # Process criminal results
            if isinstance(criminal_result, Exception):
                company_results["criminal"] = {"error": str(criminal_result)}
            else:
                company_results["criminal"] = criminal_result
                if criminal_result.get("total_hits", 0) > 0:
                    company_results["risk_factors"].append("Criminal records found")
                    company_results["overall_risk_level"] = "High"
            
            # Add summary
            company_results["summary"] = {
                "total_risk_factors": len(company_results["risk_factors"]),
                "compliance_status": "Compliant" if company_results["overall_risk_level"] == "Low" else "Review Required",
                "recommendations": self._generate_company_recommendations(company_results)
            }
            
            print(f"✅ Company screening completed for {company_name}")
            return company_results
            
        except Exception as e:
            print(f"❌ Company screening failed: {e}")
            return {"error": f"Company screening failed: {str(e)}"}

    async def _check_company_sanctions(self, company_name: str, country: str = "", *, exact: bool = True) -> Dict[str, Any]:
        """Check company for sanctions using Dilisense API"""
        try:
            print(f"🔍 Checking company sanctions for: {company_name} (exact={exact})")

            async def call_once(fuzzy: bool) -> Optional[dict]:
                params = {
                    "names": company_name,
                    "includes": "dilisense_sanctions",
                    "fuzzy_search": 0 if fuzzy is False else 1
                }
                if country:
                    params["country"] = self._normalize_country(country)
                return await self._http_get(f"{self.base_url}/checkIndividual", params, retries=1)

            # 1) exact pass
            data = await call_once(fuzzy=False) if exact else None
            # 2) fallback to fuzzy only if exact empty
            if not data or not data.get("found_records"):
                data = await call_once(fuzzy=True)

            if not data:
                print("❌ API error (sanctions)")
                return {"total_hits": 0, "found_records": [], "sanctions_found": False}

            # Post-filter to exact company name if exact requested
            recs = data.get("found_records", [])
            if exact and recs:
                recs = [r for r in recs if _exact_company_match(r, company_name) and _country_consistent(r, country)]
            total = len(recs)

            print(f"✅ Company sanctions check ok; total after filter: {total}")
            return {"total_hits": total, "found_records": recs, "sanctions_found": total > 0}

        except Exception as e:
            print(f"❌ Company sanctions check failed: {e}")
            return {"error": f"Sanctions check failed: {str(e)}"}

    async def _check_company_peps(self, company_name: str, country: str = "", *, exact: bool = True) -> Dict[str, Any]:
        """Check company for PEPs using Dilisense API"""
        try:
            print(f"🔍 Checking company PEPs for: {company_name} (exact={exact})")

            async def call_once(fuzzy: bool) -> Optional[dict]:
                params = {
                    "names": company_name,
                    "includes": "dilisense_pep",
                    "fuzzy_search": 0 if fuzzy is False else 1
                }
                if country:
                    params["country"] = self._normalize_country(country)
                return await self._http_get(f"{self.base_url}/checkIndividual", params, retries=1)

            data = await call_once(fuzzy=False) if exact else None
            if not data or not data.get("found_records"):
                data = await call_once(fuzzy=True)

            if not data:
                print("❌ API error (pep)")
                return {"total_hits": 0, "found_records": [], "peps_found": False}

            recs = data.get("found_records", [])

            # Company context: keep only org-linked records; drop RCA noise
            filtered = []
            for r in recs:
                pep_type = (r.get("pep_type") or "").upper()
                if pep_type in {"RELATIVES_AND_CLOSE_ASSOCIATES", "RCA"}:
                    continue
                # For companies, require exact org match if exact mode
                if exact:
                    if not _exact_company_match(r, company_name):
                        continue
                # country scoping
                if not _country_consistent(r, country):
                    continue
                filtered.append(r)

            total = len(filtered)
            print(f"✅ Company PEP check ok; total after filter: {total}")
            return {"total_hits": total, "found_records": filtered, "peps_found": total > 0}

        except Exception as e:
            print(f"❌ Company PEP check failed: {e}")
            return {"error": f"PEP check failed: {str(e)}"}

    async def _check_company_criminal(self, company_name: str, country: str = "", *, exact: bool = True) -> Dict[str, Any]:
        """Check company for criminal records using Dilisense API"""
        try:
            print(f"🔍 Checking company criminal records for: {company_name} (exact={exact})")

            async def call_once(fuzzy: bool) -> Optional[dict]:
                params = {
                    "names": company_name,
                    "includes": "dilisense_criminal",
                    "fuzzy_search": 0 if fuzzy is False else 1
                }
                if country:
                    params["country"] = self._normalize_country(country)
                return await self._http_get(f"{self.base_url}/checkIndividual", params, retries=1)

            data = await call_once(fuzzy=False) if exact else None
            if not data or not data.get("found_records"):
                data = await call_once(fuzzy=True)

            if not data:
                print("❌ API error (criminal)")
                return {"total_hits": 0, "found_records": [], "criminal_records_found": False}

            recs = data.get("found_records", [])
            if exact and recs:
                recs = [r for r in recs if _exact_company_match(r, company_name) and _country_consistent(r, country)]
            total = len(recs)

            print(f"✅ Company criminal check ok; total after filter: {total}")
            return {"total_hits": total, "found_records": recs, "criminal_records_found": total > 0}

        except Exception as e:
            print(f"❌ Company criminal check failed: {e}")
            return {"error": f"Criminal check failed: {str(e)}"}

    def _process_company_sanctions(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """Process company sanctions results"""
        try:
            total_hits = data.get("total_hits", 0)
            found_records = data.get("found_records", [])
            
            return {
                "total_hits": total_hits,
                "found_records": found_records,
                "sanctions_found": total_hits > 0
            }
        except Exception as e:
            print(f"❌ Failed to process company sanctions: {e}")
            return {"error": f"Sanctions processing failed: {str(e)}"}

    def _process_company_peps(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """Process company PEP results"""
        try:
            total_hits = data.get("total_hits", 0)
            found_records = data.get("found_records", [])
            
            return {
                "total_hits": total_hits,
                "found_records": found_records,
                "peps_found": total_hits > 0
            }
        except Exception as e:
            print(f"❌ Failed to process company PEPs: {e}")
            return {"error": f"PEP processing failed: {str(e)}"}

    def _process_company_criminal(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """Process company criminal results"""
        try:
            total_hits = data.get("total_hits", 0)
            found_records = data.get("found_records", [])
            
            return {
                "total_hits": total_hits,
                "found_records": found_records,
                "criminal_records_found": total_hits > 0
            }
        except Exception as e:
            print(f"❌ Failed to process company criminal: {e}")
            return {"error": f"Criminal processing failed: {str(e)}"}

    def _generate_company_recommendations(self, company_results: Dict) -> List[str]:
        """Generate compliance recommendations for companies"""
        recommendations = []
        
        risk_level = company_results.get("overall_risk_level", "Low")
        
        if risk_level == "High":
            recommendations.append("Immediate review required - high risk factors identified")
            recommendations.append("Consider enhanced due diligence procedures")
            recommendations.append("Consult compliance team before proceeding")
        elif risk_level == "Medium":
            recommendations.append("Review recommended - medium risk factors identified")
            recommendations.append("Consider additional screening")
            recommendations.append("Monitor for changes in risk profile")
        else:
            recommendations.append("Standard due diligence procedures sufficient")
            recommendations.append("Regular monitoring recommended")
        
        return recommendations

    # ============================================================================
    # EXECUTIVE SCREENING METHODS
    # ============================================================================
    
    async def screen_executives(self, company_name: str, executive_names: List[str], country: str = "") -> List[Dict[str, Any]]:
        """
        Screen company executives for compliance issues
        
        Args:
            company_name: Name of the company
            executive_names: List of executive names to screen
            country: Country/jurisdiction (optional)
            
        Returns:
            List of executive screening results
        """
        if not self.enabled:
            return [{"error": "Dilisense service not configured"}]
            
        try:
            print(f"🔍 Screening {len(executive_names)} executives for {company_name}")
            
            sem = asyncio.Semaphore(5)
            async def run_one(exec_name: str):
                async with sem:
                    print(f"🔍 Screening executive: {exec_name}")
                    r = await self.screen_individual(exec_name, country)
                    r["company"] = company_name
                    return r
            executive_results = await asyncio.gather(*[run_one(n) for n in executive_names])
            
            print(f"✅ Executive screening completed for {company_name}")
            return executive_results
            
        except Exception as e:
            print(f"❌ Executive screening failed: {e}")
            return [{"error": f"Executive screening failed: {str(e)}"}]

    # ============================================================================
    # LEGACY METHODS (for backward compatibility)
    # ============================================================================
    
    async def comprehensive_compliance_check(self, company_name: str, country: str = "") -> Dict[str, Any]:
        """Legacy method - now calls screen_company"""
        print(f"⚠️ Using legacy method - calling screen_company instead")
        return await self.screen_company(company_name, country)
    
    async def check_individual(self, name: str, country: str = "", date_of_birth: str = "", gender: str = "") -> Dict[str, Any]:
        """Legacy method - now calls screen_individual"""
        print(f"⚠️ Using legacy method - calling screen_individual instead")
        return await self.screen_individual(name, country, date_of_birth, gender)

# ============================================================================
# GLOBAL INSTANCE (for backward compatibility)
# ============================================================================

# Global Dilisense service instance
dilisense_service = DilisenseService()
