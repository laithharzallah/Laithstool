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
        """Build comprehensive knowledge-based analysis prompt"""
        return f"""
You are conducting a comprehensive due diligence analysis of {company} from {country} using your extensive knowledge base.

COMPANY: {company}
COUNTRY: {country}

ANALYSIS REQUIREMENTS:
Use your comprehensive knowledge to provide detailed intelligence on:

1. OFFICIAL WEBSITE & COMPANY PROFILE:
   - Official website URL (if known from your training data)
   - Legal company name, industry sector, business description
   - Key business activities, subsidiaries, market position

2. SANCTIONS & COMPLIANCE:
   - Any OFAC, EU, UN, or other sanctions list appearances
   - Historical regulatory violations or enforcement actions
   - Compliance issues or legal settlements

3. ADVERSE MEDIA & CONTROVERSIES:
   - Major scandals, investigations, or controversies
   - Legal disputes, lawsuits, or regulatory actions
   - Negative media coverage from your knowledge base

4. KEY EXECUTIVES & PEOPLE:
   - Current CEO, CFO, Chairman, and other C-level executives
   - Board of Directors members (if known from your training)
   - Founders, major shareholders, or key stakeholders
   - Any executive changes, resignations, or appointments
   - Educational background, previous roles of key executives

5. BRIBERY & CORRUPTION:
   - Any bribery or corruption allegations or convictions
   - FCPA violations or anti-corruption enforcement
   - Ethics violations or misconduct cases

6. POLITICAL EXPOSURE:
   - Government ownership or state enterprise status
   - Political connections of leadership
   - Politically Exposed Persons (PEP) associations

7. RISK FACTORS & DISADVANTAGES:
   - Ownership opacity or beneficial ownership issues
   - Operational risks or financial difficulties
   - Reputational risks or market concerns
   - Regulatory or environmental issues

8. EXECUTIVE SUMMARY:
   - Overall risk assessment and key findings
   - Critical issues that require attention
   - Recommended due diligence focus areas

IMPORTANT INSTRUCTIONS:
- Draw from your VAST TRAINING KNOWLEDGE about this company and its executives
- For well-known companies, provide REAL executives, subsidiaries, and controversies from your training data
- Include specific names, dates, amounts, and details where you know them from training
- Be comprehensive and detailed - use your full knowledge base
- For executives: provide actual names and positions you know from your training
- For controversies: include real scandals, lawsuits, or issues you're aware of
- Only mark as "unknown" if you genuinely have no training data about that aspect

Return ONLY valid JSON matching this exact schema:
{{
    "executive_summary": "Comprehensive overview based on knowledge",
    "official_website": "https://example.com or unknown",
    "company_profile": {{
        "legal_name": "Full legal name from knowledge",
        "country": "{country}",
        "industry": "Industry sector from knowledge",
        "description": "Detailed business description"
    }},
    "sanctions": [
        {{
            "entity_name": "Name on sanctions list",
            "list_name": "OFAC/EU/UN etc",
            "match_type": "exact/partial/alias", 
            "confidence": "high/medium/low",
            "citation_url": "knowledge_base"
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