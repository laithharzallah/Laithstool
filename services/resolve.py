"""
Entity resolution service for normalizing company names, domains, and countries
"""
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


class EntityResolver:
    """Resolve and normalize company entities"""
    
    def __init__(self):
        self.country_mappings = {
            'usa': 'United States',
            'us': 'United States', 
            'america': 'United States',
            'uk': 'United Kingdom',
            'britain': 'United Kingdom',
            'england': 'United Kingdom',
            'germany': 'Germany',
            'deutschland': 'Germany',
            'saudi': 'Saudi Arabia',
            'ksa': 'Saudi Arabia',
            'uae': 'United Arab Emirates',
            'emirates': 'United Arab Emirates'
        }
        
        self.company_suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited',
            'llc', 'plc', 'ag', 'gmbh', 'sa', 'nv', 'bv', 'holdings',
            'holding', 'group', 'international', 'global', 'worldwide'
        ]
    
    def resolve_input(self, company: str, domain: str = "", country: str = "") -> Dict[str, str]:
        """
        Resolve and normalize input parameters
        
        Args:
            company: Company name
            domain: Domain hint (optional)
            country: Country hint (optional)
            
        Returns:
            Dict with normalized values
        """
        try:
            # Normalize company name
            normalized_company = self._normalize_company_name(company)
            
            # Normalize domain
            normalized_domain = self._normalize_domain(domain)
            
            # Normalize country
            normalized_country = self._normalize_country(country)
            
            # Try to extract additional hints
            extracted_info = self._extract_additional_hints(company, domain)
            
            resolved = {
                'company_name': normalized_company,
                'company_clean': self._get_clean_company_name(normalized_company),
                'domain': normalized_domain,
                'country': normalized_country or extracted_info.get('country', ''),
                'industry_hints': extracted_info.get('industry_hints', []),
                'search_variations': self._generate_search_variations(normalized_company)
            }
            
            print(f"🔍 Resolved entity: {resolved['company_name']} | {resolved['country']} | {resolved['domain']}")
            return resolved
            
        except Exception as e:
            print(f"❌ Entity resolution failed: {e}")
            return {
                'company_name': company,
                'company_clean': company,
                'domain': domain,
                'country': country,
                'industry_hints': [],
                'search_variations': [company]
            }
    
    def _normalize_company_name(self, company: str) -> str:
        """Normalize company name"""
        if not company:
            return ""
        
        # Basic cleaning
        normalized = company.strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Capitalize properly
        normalized = normalized.title()
        
        return normalized
    
    def _get_clean_company_name(self, company: str) -> str:
        """Get clean company name without suffixes for search"""
        clean = company.lower()
        
        # Remove common suffixes
        for suffix in self.company_suffixes:
            if clean.endswith(f' {suffix}'):
                clean = clean[:-len(f' {suffix}')]
                break
        
        return clean.title()
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain name"""
        if not domain:
            return ""
        
        # Remove protocol and path
        if '://' in domain:
            domain = urlparse(domain).netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain.lower()
    
    def _normalize_country(self, country: str) -> str:
        """Normalize country name"""
        if not country:
            return ""
        
        country_lower = country.lower().strip()
        
        # Check mappings
        if country_lower in self.country_mappings:
            return self.country_mappings[country_lower]
        
        # Capitalize properly
        return country.title()
    
    def _extract_additional_hints(self, company: str, domain: str) -> Dict:
        """Extract additional hints from company name or domain"""
        hints = {
            'country': '',
            'industry_hints': []
        }
        
        try:
            # Country hints from company name
            company_lower = company.lower()
            for key, value in self.country_mappings.items():
                if key in company_lower:
                    hints['country'] = value
                    break
            
            # Industry hints from name or domain
            industry_keywords = {
                'technology': ['tech', 'software', 'digital', 'data', 'ai', 'cloud'],
                'finance': ['bank', 'finance', 'capital', 'investment', 'fund'],
                'healthcare': ['health', 'medical', 'pharma', 'bio', 'care'],
                'energy': ['energy', 'oil', 'gas', 'power', 'electric'],
                'manufacturing': ['manufacturing', 'industrial', 'engineering'],
                'consulting': ['consulting', 'advisory', 'services'],
                'retail': ['retail', 'store', 'shop', 'market'],
                'real_estate': ['real estate', 'property', 'development', 'construction']
            }
            
            text_to_check = f"{company} {domain}".lower()
            
            for industry, keywords in industry_keywords.items():
                if any(keyword in text_to_check for keyword in keywords):
                    hints['industry_hints'].append(industry)
            
            return hints
            
        except Exception:
            return hints
    
    def _generate_search_variations(self, company: str) -> list:
        """Generate search variations for better coverage"""
        variations = [company]
        
        try:
            # Add variation without common suffixes
            clean_name = self._get_clean_company_name(company)
            if clean_name != company:
                variations.append(clean_name)
            
            # Add abbreviation if company has multiple words
            words = company.split()
            if len(words) > 1:
                abbreviation = ''.join(word[0].upper() for word in words if len(word) > 2)
                if len(abbreviation) >= 2:
                    variations.append(abbreviation)
            
            # Add quoted version for exact match
            variations.append(f'"{company}"')
            
            return list(set(variations))  # Remove duplicates
            
        except Exception:
            return [company]
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain.lower()
            
        except Exception:
            return ""
    
    def is_official_domain(self, url: str, company: str) -> bool:
        """Check if URL is likely the official company domain"""
        try:
            domain = self.extract_domain_from_url(url)
            company_clean = self._get_clean_company_name(company).lower()
            
            # Remove spaces and special characters from company name
            company_slug = re.sub(r'[^a-z0-9]', '', company_clean)
            
            # Check if company name is in domain
            domain_clean = re.sub(r'[^a-z0-9]', '', domain)
            
            return company_slug in domain_clean or domain_clean in company_slug
            
        except Exception:
            return False


# Global entity resolver instance
entity_resolver = EntityResolver()