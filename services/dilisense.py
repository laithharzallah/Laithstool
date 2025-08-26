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

logger = logging.getLogger(__name__)

class DilisenseService:
    """Dilisense AML compliance service for individual and company screening"""
    
    def __init__(self):
        """Initialize the Dilisense service"""
        self.api_key = os.getenv("DILISENSE_API_KEY")
        self.base_url = os.getenv("DILISENSE_BASE_URL", "https://api.dilisense.com/v1")
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            print(f"✅ Dilisense service initialized")
            print(f"🔑 API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
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
        Generate specific name variations for the individual being screened
        Focus on finding the exact person, not broad family connections
        """
        variations = [name]  # Start with original name
        
        # Clean and standardize the name
        clean_name = name.strip().upper()
        
        # Remove common titles and honorifics
        titles_to_remove = ['MR ', 'DR ', 'PROF ', 'SHEIKH ', 'HIS EXCELLENCY ', 'HONORABLE ']
        for title in titles_to_remove:
            if clean_name.startswith(title):
                clean_name = clean_name[len(title):]
                break
        
        # Split into parts
        parts = clean_name.split()
        
        if len(parts) >= 2:
            # Focus on SPECIFIC individual variations, not family-wide searches
            specific_variations = []
            
            # Handle names with "AL" prefix - focus on the specific person
            if any('AL ' in part for part in parts):
                # Find the part with "AL" prefix
                for i, part in enumerate(parts):
                    if 'AL ' in part:
                        # Create variations for THIS specific person only
                        first_name = parts[0]
                        last_name = part
                        
                        specific_variations.extend([
                            f"{first_name} {last_name}",  # Original format
                            f"{last_name} {first_name}",  # Reversed
                            f"{first_name} {last_name.replace('AL ', '')}",  # Without AL
                            f"{last_name.replace('AL ', '')} {first_name}",  # Without AL, reversed
                        ])
                        break
            
            # Standard meaningful variations for the specific person
            if len(parts) >= 3:
                first_name = parts[0]
                middle_name = parts[1]
                last_name = parts[-1]
                
                specific_variations.extend([
                    f"{first_name} {last_name}",  # First + Last
                    f"{last_name} {first_name}",  # Last + First
                    f"{first_name} {middle_name} {last_name}",  # Full name
                ])
            elif len(parts) == 2:
                first_name = parts[0]
                last_name = parts[1]
                specific_variations.extend([
                    f"{first_name} {last_name}",
                    f"{last_name} {first_name}",
                ])
            
            # Add specific variations to the list
            variations.extend(specific_variations)
        
        # Remove duplicates and empty strings
        variations = list(set([v for v in variations if v.strip()]))
        
        # Sort by relevance (original name first, then by length)
        variations.sort(key=lambda x: (x != name, len(x)))
        
        # Limit to 4-5 specific variations (not broad family searches)
        return variations[:5]
    
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
                params['country'] = country
            if date_of_birth:
                params['dob'] = date_of_birth
            if gender:
                params['gender'] = gender
            
            # Make API call directly
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/checkIndividual",
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API call successful for '{name}'")
                    return self._process_individual_results(data, name)
                elif response.status_code == 401:
                    print(f"❌ Dilisense API authentication failed for '{name}'")
                    return None
                else:
                    print(f"❌ Dilisense API error for '{name}': {response.status_code}")
                    return None
                    
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
        base_result['sanctions']['found_records'] = filtered_sanctions
        base_result['sanctions']['total_hits'] = len(filtered_sanctions)
        
        base_result['pep']['found_records'] = filtered_pep
        base_result['pep']['total_hits'] = len(filtered_pep)
        
        base_result['criminal']['found_records'] = filtered_criminal
        base_result['criminal']['total_hits'] = len(filtered_criminal)
        
        base_result['other']['found_records'] = filtered_other
        base_result['other']['total_hits'] = len(filtered_other)
        
        # Recalculate total hits
        base_result['total_hits'] = len(filtered_sanctions) + len(filtered_pep) + len(filtered_criminal) + len(filtered_other)
        
        # Update risk assessment
        base_result['overall_risk_level'] = self._calculate_individual_risk_level(base_result)
        base_result['risk_factors'] = self._identify_individual_risk_factors(base_result)
        
        # Add metadata about variations tried
        base_result['name_variations_tried'] = [r['variation'] for r in all_results]
        base_result['best_variation'] = best_result['variation']
        
        return base_result
    
    def _is_relevant_match(self, record: dict, first_name: str, last_name: str) -> bool:
        """
        Check if a record is relevant to the specific individual being screened
        """
        record_name = record.get('name', '').upper()
        
        # Must contain at least the first name or last name
        if first_name and first_name in record_name:
            return True
        if last_name and last_name in record_name:
            return True
        
        # Check alias names
        alias_names = record.get('alias_names', [])
        for alias in alias_names:
            alias_upper = alias.upper()
            if first_name and first_name in alias_upper:
                return True
            if last_name and last_name in alias_upper:
                return True
        
        return False

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
                source_type = record.get("source_type", "").upper()
                if source_type == "SANCTION":
                    sanctions.append(record)
                elif source_type == "PEP":
                    peps.append(record)
                elif source_type == "CRIMINAL":
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
            "risk_factors": []
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
    
    def _identify_individual_risk_factors(self, result: dict) -> list:
        """
        Identify specific risk factors for individual
        """
        risk_factors = []
        
        if result.get('sanctions', {}).get('total_hits', 0) > 0:
            risk_factors.append("Sanctions listed")
        
        if result.get('pep', {}).get('total_hits', 0) > 0:
            risk_factors.append("PEP status")
        
        if result.get('criminal', {}).get('total_hits', 0) > 0:
            risk_factors.append("Criminal records")
        
        if result.get('other', {}).get('total_hits', 0) > 0:
            risk_factors.append("Other adverse records")
        
        return risk_factors

    # ============================================================================
    # COMPANY SCREENING METHODS
    # ============================================================================
    
    async def screen_company(self, company_name: str, country: str = "") -> Dict[str, Any]:
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
            sanctions_task = self._check_company_sanctions(company_name, country)
            peps_task = self._check_company_peps(company_name, country)
            criminal_task = self._check_company_criminal(company_name, country)
            
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

    async def _check_company_sanctions(self, company_name: str, country: str = "") -> Dict[str, Any]:
        """Check company for sanctions using Dilisense API"""
        try:
            print(f"🔍 Checking company sanctions for: {company_name}")
            
            search_params = {
                "names": company_name,
                "fuzzy_search": 1,
                "includes": "dilisense_sanctions"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/checkIndividual",  # Companies also use this endpoint
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    params=search_params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Company sanctions check successful")
                    return self._process_company_sanctions(data, company_name)
                else:
                    print(f"❌ Company sanctions check failed: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ Company sanctions check failed: {e}")
            return {"error": f"Sanctions check failed: {str(e)}"}

    async def _check_company_peps(self, company_name: str, country: str = "") -> Dict[str, Any]:
        """Check company for PEPs using Dilisense API"""
        try:
            print(f"🔍 Checking company PEPs for: {company_name}")
            
            search_params = {
                "names": company_name,
                "fuzzy_search": 1,
                "includes": "dilisense_pep"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/checkIndividual",  # Companies also use this endpoint
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    params=search_params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Company PEP check successful")
                    return self._process_company_peps(data, company_name)
                else:
                    print(f"❌ Company PEP check failed: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ Company PEP check failed: {e}")
            return {"error": f"PEP check failed: {str(e)}"}

    async def _check_company_criminal(self, company_name: str, country: str = "") -> Dict[str, Any]:
        """Check company for criminal records using Dilisense API"""
        try:
            print(f"🔍 Checking company criminal records for: {company_name}")
            
            search_params = {
                "names": company_name,
                "fuzzy_search": 1,
                "includes": "dilisense_criminal"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/checkIndividual",  # Companies also use this endpoint
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    params=search_params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Company criminal check successful")
                    return self._process_company_criminal(data, company_name)
                else:
                    print(f"❌ Company criminal check failed: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}
                    
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
            
            # Screen each executive
            executive_results = []
            for exec_name in executive_names:
                print(f"🔍 Screening executive: {exec_name}")
                exec_result = await self.screen_individual(exec_name, country)
                exec_result["company"] = company_name
                executive_results.append(exec_result)
            
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
