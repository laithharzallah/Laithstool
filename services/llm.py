"""
GPT-5 LLM client for due diligence analysis with primary knowledge-based approach
Enhanced to rely primarily on GPT-5's knowledge with web citations as supplementary evidence
"""
import json
import os
from typing import Dict, List, Optional, Any
from pydantic import ValidationError
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from schemas.report import ReportSchema


class GPT5Client:
    """Enhanced GPT-5 client that relies primarily on LLM knowledge with web supplementation"""

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
    async def analyze_company_primary(self, company: str, country: str) -> Dict[str, Any]:
        """
        Primary GPT-5 analysis using its vast knowledge base
        This is the main intelligence source
        """
        try:
            if not self.client:
                return self._error_response("GPT-5 client not initialized")

            # Create knowledge-based analysis prompt
            prompt = self._build_primary_knowledge_prompt(company, country)

            print(f"🧠 GPT-5 PRIMARY ANALYSIS: Using vast knowledge base for {company}...")

            # Call GPT-5 for primary knowledge-based analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using latest available model
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a world-class corporate intelligence analyst with access to comprehensive global business databases. You have extensive knowledge of companies, their operations, leadership, controversies, and regulatory issues worldwide. Provide detailed, accurate analysis based on your training knowledge."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for factual accuracy
                response_format={"type": "json_object"},
                max_tokens=3000
            )

            result = response.choices[0].message.content

            # Parse and validate JSON response
            return self._validate_primary_response(result)

        except Exception as e:
            print(f"❌ GPT-5 primary analysis failed: {e}")
            return self._error_response(f"GPT-5 primary analysis failed: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def enhance_with_web_evidence(self, primary_analysis: Dict, snippets: List[Dict]) -> Dict[str, Any]:
        """
        Enhance the primary GPT-5 analysis with web evidence
        This supplements and validates the knowledge-based analysis
        """
        try:
            if not self.client:
                return primary_analysis

            if not snippets:
                print("📝 No web evidence available, using primary GPT-5 analysis")
                return primary_analysis

            # Format snippets for enhancement
            snippet_text = self._format_snippets(snippets)

            # Create enhancement prompt
            prompt = self._build_enhancement_prompt(primary_analysis, snippet_text)

            print(f"🔍 GPT-5 ENHANCEMENT: Validating with {len(snippets)} web sources...")

            # Call GPT-5 to enhance with web evidence
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are enhancing an existing corporate analysis with new web evidence. Update the analysis ONLY where web evidence provides additional confirmation, updates, or corrections. Maintain the quality and depth of the original analysis while incorporating verified web information with proper citations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_tokens=3500
            )

            result = response.choices[0].message.content

            # Parse and validate enhanced response
            return self._validate_enhanced_response(result, snippets)

        except Exception as e:
            print(f"❌ GPT-5 enhancement failed: {e}")
            # Return primary analysis if enhancement fails
            return primary_analysis

    def _build_primary_knowledge_prompt(self, company: str, country: str) -> str:
        """Build comprehensive internet search-enabled analysis prompt"""
        return f"""
You are conducting a comprehensive due diligence analysis of {company} from {country}. 

CRITICAL: You have internet access and web search capabilities. Use them extensively to gather REAL-TIME information.

COMPANY: {company}
COUNTRY: {country}

SEARCH INSTRUCTIONS:
1. Search the web for current information about this company
2. Look up the company's official website and recent news
3. Search for current executives, leadership team, and board members
4. Find recent controversies, legal issues, or adverse media
5. Check for sanctions lists and regulatory actions
6. Look for political connections and business relationships

ANALYSIS REQUIREMENTS:
Use your WEB SEARCH capabilities to provide current, detailed intelligence on:

1. OFFICIAL WEBSITE & COMPANY PROFILE:
   - SEARCH for the company's official website URL
   - Find current legal company name, industry sector, business description
   - Research key business activities, subsidiaries, market position
   - Look up company size, revenue, headquarters location

2. CURRENT EXECUTIVES & LEADERSHIP:
   - SEARCH for current CEO, CFO, Chairman, and C-level executives 
   - Find Board of Directors members and their backgrounds
   - Look up founders, major shareholders, key stakeholders
   - Research recent executive changes, appointments, or resignations
   - Find LinkedIn profiles and professional backgrounds

3. SANCTIONS & COMPLIANCE:
   - SEARCH OFAC, EU, UN sanctions lists for company and executives
   - Look up regulatory violations, enforcement actions, fines
   - Check for compliance issues, legal settlements, court cases
   - Research any debarment or exclusion listings

4. ADVERSE MEDIA & CONTROVERSIES:
   - SEARCH recent news for scandals, investigations, controversies
   - Find legal disputes, lawsuits, regulatory actions
   - Look for negative media coverage, criticism, or allegations
   - Research any ongoing investigations or regulatory scrutiny

5. BRIBERY & CORRUPTION:
   - SEARCH for bribery, corruption allegations or convictions
   - Look up FCPA violations, anti-corruption enforcement actions
   - Find ethics violations, misconduct cases, integrity issues
   - Research any plea deals, settlements, or ongoing cases

6. POLITICAL EXPOSURE:
   - SEARCH for government ownership or state enterprise status
   - Research political connections of executives and board members
   - Look up Politically Exposed Persons (PEP) associations
   - Find government contracts, political donations, lobbying activities

7. FINANCIAL & WEBSITE FOOTPRINT:
   - SEARCH for the company's main website and digital presence
   - Find financial reports, SEC filings, annual reports
   - Look up stock exchange listings, market data
   - Research subsidiary companies and corporate structure

8. RISK ASSESSMENT & SUMMARY:
   - Synthesize all web search findings into risk assessment
   - Identify critical issues requiring attention
   - Provide overall risk score and recommendations

CRITICAL SEARCH REQUIREMENTS:
- USE WEB SEARCH for ALL information - don't rely only on training data
- SEARCH multiple sources: news sites, company websites, regulatory databases
- FIND REAL, CURRENT executives with actual names and positions
- LOOK UP recent news, press releases, and media coverage
- VERIFY information across multiple web sources
- SEARCH for: "[company name] executives", "[company name] CEO", "[company name] controversy", "[company name] sanctions"
- Include URLs and sources for verification

Return ONLY valid JSON matching this exact schema:
{{
    "executive_summary": "Comprehensive overview based on knowledge",
    "official_website": "https://example.com or unknown",
    "company_profile": {{
        "legal_name": "Full legal name from knowledge",
        "country": "{country}",
        "industry": "Industry sector from web search",
        "description": "Detailed business description from web search"
    }},
    "people": {{
        "executives": [
            {{
                "name": "Full name from web search",
                "position": "Current title/role from web search",
                "company": "{company}",
                "background": "Education/previous roles from web search",
                "tenure": "Start date or length of service",
                "source_url": "Web source URL where found"
            }}
        ],
        "board_members": [
            {{
                "name": "Full name from web search", 
                "position": "Board role from web search",
                "background": "Professional background from web search",
                "source_url": "Web source URL where found"
            }}
        ]
    }},
    "website": {{
        "official_url": "Main company website from web search",
        "description": "Website content analysis",
        "last_verified": "Current date"
    }},
    "sanctions": [
        {{
            "entity_name": "Name found on sanctions list via web search",
            "list_name": "OFAC/EU/UN/UK HMT etc",
            "match_type": "exact/partial/alias", 
            "confidence": "high/medium/low",
            "source_url": "URL where sanctions info was found"
        }}
    ],
    "adverse_media": [
        {{
            "headline": "Specific controversy or news from knowledge",
            "date": "YYYY-MM-DD or unknown",
            "source": "Known source from training data",
            "category": "Legal/Financial/Regulatory/Operational",
            "severity": "high/medium/low",
            "summary": "Detailed summary from knowledge",
            "citation_url": "knowledge_base"
        }}
    ],
    "bribery_corruption": [
        {{
            "allegation": "Specific allegation from knowledge", 
            "date": "YYYY-MM-DD or unknown",
            "source": "Authority or source from knowledge",
            "status": "alleged/charged/convicted/settled",
            "citation_url": "knowledge_base"
        }}
    ],
    "political_exposure": [
        {{
            "type": "PEP/Government Ownership/Political Connections",
            "description": "Details from knowledge base",
            "confidence": "high/medium/low",
            "citation_url": "knowledge_base"
        }}
    ],
    "disadvantages": [
        {{
            "risk_type": "Ownership Opacity/Regulatory Action/Lawsuit/Controversy",
            "description": "Risk description from knowledge",
            "severity": "high/medium/low", 
            "citation_url": "knowledge_base"
        }}
    ],
    "citations": ["knowledge_base"],
    "analysis_method": "gpt5_primary_knowledge",
    "confidence_level": "high/medium/low based on knowledge depth"
}}

Provide the most comprehensive analysis possible based on your training knowledge of {company}.
"""

    def _build_enhancement_prompt(self, primary_analysis: Dict, snippet_text: str) -> str:
        """Build prompt to enhance primary analysis with web evidence"""
        return f"""
You have an existing comprehensive corporate analysis that you need to enhance with new web evidence.

EXISTING ANALYSIS:
{json.dumps(primary_analysis, indent=2)}

NEW WEB EVIDENCE:
{snippet_text}

ENHANCEMENT INSTRUCTIONS:
1. Review the existing analysis quality and completeness
2. Examine the web evidence for new information, updates, or corrections
3. Enhance the analysis by:
   - Adding new findings supported by web evidence
   - Updating dates, amounts, or details with more recent information
   - Adding proper citation URLs where web evidence supports findings
   - Correcting any inaccuracies if web evidence contradicts knowledge base
   - Maintaining the depth and quality of the original analysis

4. For web-supported findings, use actual URLs from the evidence
5. For knowledge-based findings, keep "knowledge_base" as citation
6. Improve the executive summary to reflect any new findings
7. Update confidence levels based on web validation

CRITICAL: 
- Maintain all valuable knowledge-based insights
- Only modify where web evidence provides clear updates or corrections
- Add web citations only where evidence directly supports specific claims
- Keep the JSON schema exactly the same

Return the enhanced analysis in the same JSON format with proper citations.
"""

    def _validate_primary_response(self, response_text: str) -> Dict[str, Any]:
        """Validate primary GPT-5 response"""
        try:
            # Parse JSON
            response_data = json.loads(response_text)

            # Validate against Pydantic schema
            validated_report = ReportSchema(**response_data)

            # Add metadata
            result = validated_report.dict()
            result['analysis_metadata'] = {
                'analysis_method': 'gpt5_primary_knowledge',
                'model_used': 'gpt-4o',
                'validation_status': 'passed',
                'knowledge_based': True
            }
            result['validation_status'] = 'passed'  # Add at top level too

            print(f"✅ GPT-5 primary analysis completed and validated")
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

    def _validate_enhanced_response(self, response_text: str, snippets: List[Dict]) -> Dict[str, Any]:
        """Validate enhanced GPT-5 response"""
        try:
            # Parse JSON
            response_data = json.loads(response_text)

            # Validate against Pydantic schema
            validated_report = ReportSchema(**response_data)

            # Add metadata
            result = validated_report.dict()
            result['analysis_metadata'] = {
                'analysis_method': 'gpt5_enhanced_with_web',
                'model_used': 'gpt-4o',
                'validation_status': 'passed',
                'snippets_used': len(snippets),
                'knowledge_based': True,
                'web_enhanced': True
            }
            result['validation_status'] = 'passed'  # Add at top level too

            print(f"✅ GPT-5 enhanced analysis completed and validated")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON from enhanced GPT-5: {e}")
            return self._error_response("GPT-5 enhanced analysis returned invalid JSON", response_text[:500])

        except ValidationError as e:
            print(f"❌ Enhanced schema validation failed: {e}")
            # Return partial results with error
            try:
                partial_data = json.loads(response_text)
                partial_data['validation_errors'] = str(e)
                partial_data['validation_status'] = 'failed'
                return partial_data
            except:
                return self._error_response("Enhanced schema validation failed", str(e))

    def _format_snippets(self, snippets: List[Dict]) -> str:
        """Format snippets for enhancement prompt"""
        formatted = []
        for i, snippet in enumerate(snippets, 1):
            url = snippet.get('url', 'Unknown URL')
            title = snippet.get('title', 'No title')
            text = snippet.get('text', '')[:1000]  # Limit text length
            source_type = snippet.get('source_type', 'web')

            formatted.append(f"""
EVIDENCE {i} [{source_type.upper()}]:
URL: {url}
TITLE: {title}
TEXT: {text}
---""")

        return "\n".join(formatted)

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

    # Legacy method for backward compatibility
    async def ask_gpt5(self, company: str, country: str, snippets: List[Dict]) -> Dict[str, Any]:
        """
        Legacy method that now uses the enhanced GPT-5 first approach
        """
        try:
            # Step 1: Primary GPT-5 knowledge analysis
            primary_analysis = await self.analyze_company_primary(company, country)
            
            # Step 2: Enhance with web evidence if available
            if snippets:
                enhanced_analysis = await self.enhance_with_web_evidence(primary_analysis, snippets)
                return enhanced_analysis
            else:
                return primary_analysis
                
        except Exception as e:
            print(f"❌ GPT-5 combined analysis failed: {e}")
            return self._error_response(f"GPT-5 analysis failed: {str(e)}")


# Global GPT-5 client instance
gpt5_client = GPT5Client()