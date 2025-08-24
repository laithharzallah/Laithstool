"""
GPT-5 LLM client for due diligence analysis with citation requirements
"""
import json
import os
from typing import Dict, List, Optional, Any
from pydantic import ValidationError
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from schemas.report import ReportSchema


class GPT5Client:
    """GPT-5 client for structured due diligence analysis"""
    
    def __init__(self):
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                print("✅ GPT-5 client initialized successfully")
            else:
                print("⚠️ OpenAI API key not found")
        except Exception as e:
            print(f"❌ Failed to initialize GPT-5 client: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def ask_gpt5(self, company: str, country: str, snippets: List[Dict]) -> Dict[str, Any]:
        """
        Ask GPT-5 to analyze company data using provided snippets
        
        Args:
            company: Company name
            country: Company country
            snippets: List of extracted web snippets with {url, title, text, source_type}
        
        Returns:
            Structured report dict validated against ReportSchema
        """
        try:
            if not self.client:
                return self._error_response("GPT-5 client not initialized")
            
            # Prepare snippets for prompt
            snippet_text = self._format_snippets(snippets)
            
            # Create comprehensive prompt
            prompt = self._build_analysis_prompt(company, country, snippet_text)
            
            print(f"🤖 Asking GPT-5 to analyze {company} using {len(snippets)} snippets...")
            
            # Call GPT-5 with JSON mode
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use gpt-4 as gpt-5 may not be available yet
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a senior compliance analyst specializing in corporate due diligence. You MUST use ONLY the supplied evidence snippets. Never invent or hallucinate information. If evidence is insufficient, respond with 'unknown' for that field."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=2500
            )
            
            result = response.choices[0].message.content
            
            # Parse and validate JSON response
            return self._validate_response(result, snippets)
            
        except Exception as e:
            print(f"❌ GPT-5 analysis failed: {e}")
            return self._error_response(f"GPT-5 analysis failed: {str(e)}")
    
    def _format_snippets(self, snippets: List[Dict]) -> str:
        """Format snippets for GPT-5 prompt"""
        formatted = []
        for i, snippet in enumerate(snippets, 1):
            url = snippet.get('url', 'Unknown URL')
            title = snippet.get('title', 'No title')
            text = snippet.get('text', '')[:1200]  # Limit text length
            source_type = snippet.get('source_type', 'web')
            
            formatted.append(f"""
SNIPPET {i} [{source_type.upper()}]:
URL: {url}
TITLE: {title}
TEXT: {text}
---""")
        
        return "\n".join(formatted)
    
    def _build_analysis_prompt(self, company: str, country: str, snippet_text: str) -> str:
        """Build comprehensive analysis prompt for GPT-5"""
        return f"""
You are a senior due-diligence analyst. Use ONLY the evidence below to analyze {company} from {country}.

CRITICAL INSTRUCTIONS:
- Use ONLY the provided snippets as evidence
- If insufficient evidence exists for any field, return 'unknown'
- NEVER invent, assume, or hallucinate information
- Every fact must be supported by at least one citation URL
- Include confidence levels: high/medium/low based on evidence quality

ANALYSIS TASKS:
1. Identify the official website if present in snippets
2. Summarize sanctions/watchlist mentions (none/possible/confirmed) with evidence
3. Extract adverse media from last 24 months with headlines and dates
4. Flag any bribery/corruption allegations with details
5. Flag political exposure (PEP connections, government ownership)
6. List disadvantages/risks (opacity, regulatory actions, lawsuits, controversies)
7. Provide executive summary of key findings
8. List all URLs used as citations

COMPANY: {company}
COUNTRY: {country}

EVIDENCE:
{snippet_text}

Return valid JSON matching this exact schema:
{{
    "executive_summary": "Brief overview of key findings from evidence",
    "official_website": "https://example.com or unknown",
    "company_profile": {{
        "legal_name": "Company name from evidence or unknown",
        "country": "{country}",
        "industry": "Industry from evidence or unknown",
        "description": "Description from evidence or unknown"
    }},
    "sanctions": [
        {{
            "entity_name": "Name found on sanctions list",
            "list_name": "OFAC/EU/UN etc",
            "match_type": "exact/partial/alias",
            "confidence": "high/medium/low",
            "citation_url": "URL where this was found"
        }}
    ],
    "adverse_media": [
        {{
            "headline": "News headline from evidence",
            "date": "YYYY-MM-DD or unknown",
            "source": "News outlet name",
            "category": "Legal/Financial/Regulatory/Operational",
            "severity": "high/medium/low",
            "summary": "Brief summary from evidence",
            "citation_url": "URL where this was found"
        }}
    ],
    "bribery_corruption": [
        {{
            "allegation": "Specific allegation from evidence",
            "date": "YYYY-MM-DD or unknown",
            "source": "News outlet or authority",
            "status": "alleged/charged/convicted/settled",
            "citation_url": "URL where this was found"
        }}
    ],
    "political_exposure": [
        {{
            "type": "PEP/Government Ownership/Political Connections",
            "description": "Details from evidence",
            "confidence": "high/medium/low",
            "citation_url": "URL where this was found"
        }}
    ],
    "disadvantages": [
        {{
            "risk_type": "Ownership Opacity/Regulatory Action/Lawsuit/Controversy",
            "description": "Risk description from evidence",
            "severity": "high/medium/low",
            "citation_url": "URL where this was found"
        }}
    ],
    "citations": ["list", "of", "all", "URLs", "used"]
}}

REMEMBER: Only use the evidence provided. No hallucinations. Every item needs a citation URL.
"""
    
    def _validate_response(self, response_text: str, snippets: List[Dict]) -> Dict[str, Any]:
        """Validate GPT-5 response against schema"""
        try:
            # Parse JSON
            response_data = json.loads(response_text)
            
            # Validate against Pydantic schema
            validated_report = ReportSchema(**response_data)
            
            # Add metadata
            result = validated_report.dict()
            result['analysis_metadata'] = {
                'snippets_analyzed': len(snippets),
                'analysis_method': 'gpt-5-rag',
                'model_used': 'gpt-4',
                'validation_status': 'passed'
            }
            
            print(f"✅ GPT-5 analysis completed and validated")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON from GPT-5: {e}")
            return self._error_response("GPT-5 returned invalid JSON", response_text[:500])
            
        except ValidationError as e:
            print(f"❌ Schema validation failed: {e}")
            # Return partial results with error
            try:
                partial_data = json.loads(response_text)
                partial_data['validation_errors'] = str(e)
                partial_data['validation_status'] = 'failed'
                return partial_data
            except:
                return self._error_response("Schema validation failed", str(e))
    
    def _error_response(self, message: str, details: str = None) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "executive_summary": f"Analysis failed: {message}",
            "official_website": "unknown",
            "company_profile": {
                "legal_name": "unknown",
                "country": "unknown", 
                "industry": "unknown",
                "description": "unknown"
            },
            "sanctions": [],
            "adverse_media": [],
            "bribery_corruption": [],
            "political_exposure": [],
            "disadvantages": [],
            "citations": [],
            "error": message,
            "error_details": details,
            "validation_status": "error"
        }


# Global GPT-5 client instance
gpt5_client = GPT5Client()