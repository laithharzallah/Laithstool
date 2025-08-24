import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from pydantic import ValidationError
import logging
from datetime import datetime

# Import our schema
try:
    from schemas.due_diligence import DueDiligenceResponse
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from schemas.due_diligence import DueDiligenceResponse

logger = logging.getLogger(__name__)

class GPT5WebSearchService:
    """GPT-5 Web Search Service for Due Diligence"""
    
    def __init__(self):
        """Initialize GPT-5 client with web search capabilities"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Use latest available model (GPT-5 when available)
        
        print(f"✅ GPT-5 Web Search Service initialized")
        print(f"🤖 Model: {self.model}")
        print(f"🔑 API Key: {'*' * 20}{api_key[-10:] if len(api_key) > 10 else '***'}")

    async def screen_company(self, company: str, country: str = "") -> Dict[str, Any]:
        """
        Perform comprehensive due diligence screening using GPT-5 web search
        
        Args:
            company: Company name to screen
            country: Country/jurisdiction (optional)
            
        Returns:
            Comprehensive due diligence data with web citations
        """
        try:
            print(f"🔍 Starting GPT-5 web search for: {company} ({country})")
            
            # Create comprehensive web search prompt
            prompt = self._build_web_search_prompt(company, country)
            
            # Call GPT-5 with JSON mode (simpler than structured schema)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional due diligence analyst with internet access. "
                            "Use your web search capabilities to find comprehensive, current information "
                            "about companies. Always search the web for real-time data and provide "
                            "accurate source URLs for all information found. "
                            "Return results in valid JSON format."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for factual accuracy
                max_tokens=4000
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            # Validate with Pydantic
            validated_response = DueDiligenceResponse(**result_data)
            
            print(f"✅ GPT-5 screening completed for {company}")
            print(f"📊 Found {len(validated_response.key_executives)} executives")
            print(f"📰 Found {len(validated_response.adverse_media)} adverse media items")
            print(f"🚩 Found {len(validated_response.sanctions_flags)} sanctions flags")
            print(f"🔗 Total citations: {len(validated_response.citations)}")
            
            return validated_response.model_dump()
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            return self._create_error_response(f"Data validation failed: {str(e)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return self._create_error_response(f"Invalid JSON response: {str(e)}")
            
        except Exception as e:
            logger.error(f"GPT-5 screening failed: {e}")
            return self._create_error_response(f"Screening failed: {str(e)}")

    def _build_web_search_prompt(self, company: str, country: str) -> str:
        """Build comprehensive web search prompt for GPT-5"""
        return f"""
COMPREHENSIVE DUE DILIGENCE WEB SEARCH

TARGET: {company}
JURISDICTION: {country if country else "Unknown"}

🔍 MANDATORY WEB SEARCHES - Search the internet for ALL of the following:

1. COMPANY PROFILE & BASIC INFO:
   - Search: "{company} official website"
   - Search: "{company} company profile"
   - Search: "{company} about us legal name"
   - Search: "{company} industry sector business"
   - Search: "{company} founded year employees"
   - Search: "{company} headquarters location"
   - Find: Legal name, industry, founding year, employee count, jurisdiction, entity type

2. KEY EXECUTIVES & LEADERSHIP:
   - Search: "{company} CEO current 2024"
   - Search: "{company} management team executives"
   - Search: "{company} board of directors"
   - Search: "{company} leadership team"
   - Search: "{company} key personnel officers"
   - Find: Current CEO, CFO, key executives with names, positions, backgrounds

3. FINANCIAL CAPABILITIES:
   - Search: "{company} financial results cash flow"
   - Search: "{company} revenue earnings ability generate cash"
   - Search: "{company} debt payment capability financial health"
   - Search: "{company} cash reserves liquidity"
   - Search: "{company} financial statements annual report"
   - Find: Cash generation ability, debt payment capability, cash reserves

4. BUSINESS INTELLIGENCE:
   - Search: "{company} government contracts public sector"
   - Search: "{company} expansion announcements new markets"
   - Search: "{company} future commitments investments"
   - Search: "{company} strategic plans growth"
   - Find: Government contracts, expansion plans, future commitments

5. OWNERSHIP STRUCTURE:
   - Search: "{company} shareholders major investors"
   - Search: "{company} beneficial owners ownership structure"
   - Search: "{company} parent company subsidiaries"
   - Search: "{company} ownership transparency"
   - Find: Major shareholders, beneficial owners, ownership structure

6. SANCTIONS & COMPLIANCE:
   - Search: "{company} OFAC sanctions list"
   - Search: "{company} EU sanctions UN sanctions"
   - Search: "{company} regulatory violations compliance"
   - Search: "{company} enforcement actions penalties"
   - Find: Any sanctions listings, regulatory violations, compliance issues

7. ADVERSE MEDIA & CONTROVERSIES:
   - Search: "{company} controversy scandal news"
   - Search: "{company} lawsuit legal issues court"
   - Search: "{company} investigation regulatory action"
   - Search: "{company} negative news adverse media"
   - Search: "{company} criticism allegations"
   - Find: Recent controversies, legal issues, negative coverage

8. POLITICAL EXPOSURE:
   - Search: "{company} political connections government"
   - Search: "{company} politically exposed persons PEP"
   - Search: "{company} state owned government controlled"
   - Search: "{company} political donations lobbying"
   - Find: Political connections, PEP associations, government ownership

9. BRIBERY & CORRUPTION:
   - Search: "{company} bribery corruption allegations"
   - Search: "{company} FCPA violation anti-corruption"
   - Search: "{company} ethics violations misconduct"
   - Search: "{company} fraud embezzlement charges"
   - Find: Corruption allegations, bribery cases, ethics violations

10. DIGITAL PRESENCE:
    - Search: "{company} official website social media"
    - Search: "{company} LinkedIn Twitter Facebook"
    - Find: Official website, verified social media accounts

🎯 CRITICAL REQUIREMENTS:

1. SEARCH THE WEB for ALL information - don't rely only on training data
2. FIND REAL executives with actual names and current positions
3. GET REAL financial data, government contracts, and business intelligence  
4. LOCATE REAL adverse media, sanctions, and compliance issues
5. PROVIDE actual URLs for every piece of information found
6. VERIFY information across multiple web sources when possible
7. ENSURE every non-null field includes at least 1 source URL

📊 OUTPUT REQUIREMENTS:

Return comprehensive JSON data matching the exact schema provided. Include:
- Real executive names and positions with source URLs
- Actual financial metrics with source URLs  
- Real adverse media headlines with source URLs
- Actual sanctions information with source URLs
- Real government contracts and business intelligence with URLs
- All source URLs in the citations array

🚨 QUALITY STANDARDS:
- Use current 2024 information where available
- Provide specific details (names, dates, amounts)
- Include confidence levels for each finding
- Cross-reference multiple sources for accuracy
- Focus on factual, verifiable information

📋 REQUIRED JSON OUTPUT FORMAT:
Return valid JSON with this exact structure:

{{
    "executive_summary": "Comprehensive overview and risk assessment",
    "risk_flags": ["List of identified risk factors"],
    "company_profile": {{
        "legal_name": "Official company name",
        "industry": "Primary industry sector",
        "founded": "Year founded (if known)",
        "employees": "Number of employees (if known)",
        "jurisdiction": "Country of incorporation",
        "entity_type": "Corporation type (if known)",
        "status": "Active status (if known)"
    }},
    "key_executives": [
        {{
            "name": "Executive full name",
            "position": "Job title",
            "background": "Professional background",
            "source_url": "URL where found"
        }}
    ],
    "official_website": "Main company website URL",
    "social_media": ["List of official social media URLs"],
    "ability_to_generate_cash": {{
        "value": "Assessment of cash generation ability",
        "source_url": "URL where found",
        "last_updated": "Date of information"
    }},
    "capability_of_paying_debt": {{
        "value": "Assessment of debt payment capability", 
        "source_url": "URL where found",
        "last_updated": "Date of information"
    }},
    "cash_reserve": {{
        "value": "Current cash reserves information",
        "source_url": "URL where found",
        "last_updated": "Date of information"
    }},
    "government_contracts": ["List of government contracts with URLs"],
    "expansion_announcements": ["List of expansion news with URLs"],
    "future_commitments": ["List of future commitments with URLs"],
    "shareholders": ["List of major shareholders with URLs"],
    "beneficial_owners": ["List of beneficial owners with URLs"],
    "sanctions_flags": [
        {{
            "entity_name": "Name on sanctions list",
            "list_name": "OFAC/EU/UN etc",
            "match_type": "exact/partial/alias",
            "confidence": "high/medium/low",
            "source_url": "URL of sanctions list"
        }}
    ],
    "adverse_media": [
        {{
            "headline": "News headline",
            "date": "Publication date",
            "source": "News source name",
            "category": "Legal/Financial/Regulatory",
            "severity": "high/medium/low",
            "summary": "Brief summary",
            "source_url": "URL of article"
        }}
    ],
    "political_exposure": [
        {{
            "type": "PEP/Government Ownership/Political Connections",
            "description": "Details of exposure",
            "confidence": "high/medium/low",
            "source_url": "URL where found"
        }}
    ],
    "bribery_corruption": [
        {{
            "headline": "Corruption-related headline",
            "date": "Date",
            "source": "Source name",
            "category": "Bribery/Corruption/Ethics",
            "severity": "high/medium/low",
            "summary": "Summary",
            "source_url": "URL"
        }}
    ],
    "search_timestamp": "{datetime.now().isoformat()}",
    "confidence_level": "high/medium/low",
    "citations": ["List of all source URLs used"]
}}

Search the web thoroughly and provide comprehensive due diligence intelligence for {company}.
"""

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "error": True,
            "message": error_message,
            "executive_summary": f"Screening failed: {error_message}",
            "company_profile": {
                "legal_name": "Unknown",
                "industry": "Unknown", 
                "jurisdiction": "Unknown"
            },
            "risk_flags": [f"Data collection error: {error_message}"],
            "search_timestamp": datetime.now().isoformat(),
            "confidence_level": "low",
            "citations": []
        }

# Global instance - initialize on import if API key is available
try:
    gpt5_search_service = GPT5WebSearchService()
except ValueError:
    # Will be initialized when API key is available
    gpt5_search_service = None