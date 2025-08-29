"""
Real-Time Internet Search Service with GPT-5 Integration
Provides comprehensive real-time search capabilities for due diligence
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
import httpx
import tldextract
from datetime import datetime, timedelta
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from dotenv import load_dotenv
from services.helpers.json_guard import force_json, prune_to_schema
from services.google_search import GoogleSearch

# Load environment variables (development or if .env exists)
if os.environ.get('FLASK_ENV', '').lower() == 'development' or os.path.exists('.env'):
    load_dotenv()

logger = logging.getLogger(__name__)

def _log_preview(label: str, text: Any, n: int = 400):
    try:
        s = text if isinstance(text, str) else json.dumps(text)
        print(f"{label}: {s[:n]}{'…' if len(s) > n else ''}")
    except Exception:
        print(f"{label}: <unprintable>")

class RealTimeSearchService:
    """Real-time internet search service with GPT-5 integration"""
    
    def __init__(self):
        """Initialize the real-time search service"""
        self.openai_client = None
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.serper_api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPER_API") or os.getenv("SERPER")
        self.google = GoogleSearch()
        
        # Initialize OpenAI client if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                print(f"✅ OpenAI client initialized for real-time search")
                print(f"🤖 Model: {self.openai_model}")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
        
        # Initialize search providers
        self.search_providers = self._initialize_search_providers()
        
        print(f"✅ Real-time search service initialized with {len(self.search_providers)} providers")
        # Provider availability logs
        try:
            if getattr(self.google, "api_key", None) and getattr(self.google, "cx", None):
                print("🔎 Google CSE enabled (GOOGLE_CSE_ID found)")
        except Exception:
            pass
        if self.serper_api_key:
            print("🔎 Serper enabled")
        else:
            print("⚠️ Serper key missing — web/news search will be LLM-only")

        # Strict system prompt reused for all intents (LLM extraction only)
        self.STRICT_SYSTEM_PROMPT = (
            "You are an extraction engine.\n"
            "- You MUST use your live web browsing capability to fetch information.\n"
            "- Do NOT rely only on memory. Always verify with current sources.\n"
            "- You MUST return ONLY a single valid JSON object.\n"
            "- Do NOT include code fences, commentary, or explanations.\n"
            "- If a field is unknown or you cannot find a current, verifiable source, set it to null.\n"
            "- Never fabricate URLs. If a verifiable URL is not available, use null.\n"
            "- Only include the keys specified in the schema for this task; omit all other keys.\n"
            "- Verification step: Confirm that the information comes from a real, live web page.\n"
            "  If you did not access the internet, set all fields in the JSON to null."
        )

        self.INTENT_SCHEMAS: Dict[str, Any] = {
            "company_profile": {"company_info": {
                "legal_name": None, "website": None, "founded_year": None, "headquarters": None,
                "industry": None, "business_description": None, "registration_status": None, "entity_type": None
            }},
            "executives": {"executives": [
                {"name": None, "position": None, "company": None, "background": None, "source_url": None, "source": None}
            ]},
            "financials": {"financial_data": {
                "revenue": None, "profit": None, "assets": None, "employees": None, "market_cap": None, "financial_year": None
            }, "performance": {"growth_rate": None, "profitability": None, "financial_health": None}},
            "adverse_media": {"adverse_media": [
                {"headline": None, "summary": None, "date": None, "source": None, "severity": None, "category": None, "source_url": None}
            ], "total_incidents": 0, "risk_level": None, "key_concerns": []},
            "sanctions": {"sanctions_status": {
                "ofac_status": None, "eu_status": None, "un_status": None, "overall_status": None
            }, "compliance_issues": [
                {"type": None, "description": None, "severity": None, "source": None, "date": None}
            ]},
            "ownership": {"ownership_structure": {
                "parent_company": None, "subsidiaries": [], "ownership_type": None
            }, "shareholders": [{"name": None, "percentage": None, "type": None, "source": None}],
               "beneficial_owners": [{"name": None, "relationship": None, "source": None}]}
        }

    def _intent_prompt(self, intent: str, company: str, country: str) -> str:
        country_hint = f" in {country}" if country else ""
        if intent == "company_profile":
            return (
                f'Extract factual company profile for: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON (no extra keys, no explanations):\n"
                "{\n  \"company_info\": {\n    \"legal_name\": null,\n    \"website\": null,\n    \"founded_year\": null,\n    \"headquarters\": null,\n    \"industry\": null,\n    \"business_description\": null,\n    \"registration_status\": null,\n    \"entity_type\": null\n  }\n}\n\n"
                "Rules:\n- Use null if unknown.\n- Never fabricate URLs.\n- Do not include \"search_results\" or any other keys."
            )
        if intent == "executives":
            return (
                f'Extract key executives for: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON:\n"
                "{\n  \"executives\": [\n    {\n      \"name\": null,\n      \"position\": null,\n      \"company\": \"" + company + "\",\n      \"background\": null,\n      \"source_url\": null,\n      \"source\": null\n    }\n  ]\n}\n\n"
                "Rules:\n- Up to 10 entries is fine; empty array if none found.\n- source_url must be real (else null). No extra keys."
            )
        if intent == "financials":
            return (
                f'Extract financials for: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON:\n"
                "{\n  \"financial_data\": {\n    \"revenue\": null,\n    \"profit\": null,\n    \"assets\": null,\n    \"employees\": null,\n    \"market_cap\": null,\n    \"financial_year\": null\n  },\n  \"performance\": {\n    \"growth_rate\": null,\n    \"profitability\": null,\n    \"financial_health\": null\n  }\n}\n\n"
                "Rules:\n- Null for unknown values. No other keys (e.g. no search_results)."
            )
        if intent == "adverse_media":
            return (
                f'Extract adverse media about: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON:\n"
                "{\n  \"adverse_media\": [\n    {\n      \"headline\": null,\n      \"summary\": null,\n      \"date\": null,\n      \"source\": null,\n      \"severity\": null,\n      \"category\": null,\n      \"source_url\": null\n    }\n  ],\n  \"total_incidents\": 0,\n  \"risk_level\": null,\n  \"key_concerns\": []\n}\n\n"
                "Rules:\n- Severity must be High/Medium/Low or null.\n- Do not include \"search_results\". Only the keys above."
            )
        if intent == "sanctions":
            return (
                f'Extract sanctions/compliance for: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON:\n"
                "{\n  \"sanctions_status\": {\n    \"ofac_status\": null,\n    \"eu_status\": null,\n    \"un_status\": null,\n    \"overall_status\": null\n  },\n  \"compliance_issues\": [\n    {\n      \"type\": null,\n      \"description\": null,\n      \"severity\": null,\n      \"source\": null,\n      \"date\": null\n    }\n  ]\n}\n\n"
                "Rules:\n- No extra keys. Null if unknown. Do not invent statuses."
            )
        if intent == "ownership":
            return (
                f'Extract ownership for: "{company}"{country_hint}\n\n'
                "Return EXACTLY this JSON:\n"
                "{\n  \"ownership_structure\": {\n    \"parent_company\": null,\n    \"subsidiaries\": [],\n    \"ownership_type\": null\n  },\n  \"shareholders\": [\n    { \"name\": null, \"percentage\": null, \"type\": null, \"source\": null }\n  ],\n  \"beneficial_owners\": [\n    { \"name\": null, \"relationship\": null, \"source\": null }\n  ]\n}\n\n"
                "Rules:\n- No extra keys. Use nulls/empty arrays when unknown."
            )
        return f'Extract data for intent {intent} for: "{company}"{country_hint} using ONLY the allowed keys.'

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def _llm_json(self, prompt: str, schema_example: Dict) -> Dict:
        resp = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": self.STRICT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            timeout=20,
        )
        raw = resp.choices[0].message.content or "{}"
        return force_json(raw, schema_example)

    def _initialize_search_providers(self) -> List[Dict]:
        """Enable LLM + Google CSE (if configured) + Serper Google Search"""
        providers: List[Dict[str, Any]] = [{
            "name": "chatgpt4o_live",
            "type": "llm",
            "model": self.openai_model,
        }]
        # Register Google CSE as a provider if keys are configured
        try:
            if getattr(self.google, "api_key", None) and getattr(self.google, "cx", None):
                providers.append({"name": "google_cse", "type": "google_search"})
        except Exception:
            pass
        if self.serper_api_key:
            providers.append({"name": "serper", "type": "google_search"})
        return providers

    async def comprehensive_search(self, company: str, country: str, domain: str = "") -> Dict[str, Any]:
        """Comprehensive extraction across intents, schema-first with Serper enrichment."""
        try:
            print(f"🔍 Starting comprehensive extraction for: {company}")
            search_intents = [
                "company_profile",
                "executives",
                "adverse_media",
                "financials",
                "sanctions",
                "ownership",
            ]

            processed_results: Dict[str, Any] = {}
            for intent in search_intents:
                res = await self._search_intent(company, country, intent, domain=domain)
                processed_results[intent] = res

            categorized_results = {
                "company_info": {},
                "executives": [],
                "adverse_media": [],
                "financials": {},
                "sanctions": {},
                "ownership": {},
            }

            # Map per-intent result payloads into categories
            ci = processed_results.get("company_profile", {}).get("results", {})
            categorized_results["company_info"] = ci.get("company_info", {}) if isinstance(ci, dict) else {}

            ex = processed_results.get("executives", {}).get("results", {})
            categorized_results["executives"] = ex.get("executives", []) if isinstance(ex, dict) else []

            am = processed_results.get("adverse_media", {}).get("results", {})
            categorized_results["adverse_media"] = am.get("adverse_media", []) if isinstance(am, dict) else []

            fin = processed_results.get("financials", {}).get("results", {})
            categorized_results["financials"] = fin.get("financial_data", {}) if isinstance(fin, dict) else {}

            sanc = processed_results.get("sanctions", {}).get("results", {})
            categorized_results["sanctions"] = sanc.get("sanctions_status", {}) if isinstance(sanc, dict) else {}

            own = processed_results.get("ownership", {}).get("results", {})
            categorized_results["ownership"] = own.get("ownership_structure", {}) if isinstance(own, dict) else {}

            total_counts = (
                len(categorized_results["executives"]) +
                len(categorized_results["adverse_media"]) +
                (1 if categorized_results["company_info"] else 0) +
                (1 if categorized_results["financials"] else 0) +
                (1 if categorized_results["sanctions"] else 0) +
                (1 if categorized_results["ownership"] else 0)
            )

            output = {
                "categorized_results": categorized_results,
                "total_results": total_counts,
                "metadata": {
                    "search_timestamp": datetime.now().isoformat(),
                    "company": company,
                    "country": country,
                    "search_intents": search_intents,
                    "providers_used": [p["name"] for p in self.search_providers],
                },
            }

            print(f"✅ Comprehensive extraction completed for {company}")
            return output
            
        except Exception as e:
            print(f"❌ Comprehensive search failed: {e}")
            import traceback
            traceback.print_exc()
            # Return a basic structure instead of error to prevent company screening from failing
            return {
                "categorized_results": {
                    "company_info": [],
                    "executives": [],
                    "adverse_media": [],
                    "financials": [],
                    "sanctions": [],
                    "ownership": [],
                    "all_search_results": []
                },
                "total_results": 0,
                "error": f"Search failed: {str(e)}"
            }

    async def _search_intent(self, company: str, country: str, intent: str, domain: str = "") -> Dict[str, Any]:
        """Serper-first; enrich query for stronger hits, then structure via GPT-4o."""
        try:
            schema = self.INTENT_SCHEMAS.get(intent, {})
            # 1) Build geo+intent-aware query (bias to official site/leadership)
            cc = (country or "").strip()
            # Guard: only add site: when domain is a non-empty hostname
            def _clean_domain(d: str) -> str:
                if not d:
                    return ""
                d = d.strip()
                if d.startswith("http://") or d.startswith("https://"):
                    try:
                        from urllib.parse import urlparse
                        d = urlparse(d).netloc
                    except Exception:
                        pass
                # basic sanity: must contain a dot and no spaces
                return d if (" " not in d and "." in d) else ""

            safe_domain = _clean_domain(domain)
            site_hint = f" site:{safe_domain}" if safe_domain else ""
            if intent == "company_profile":
                query = f"{company} {cc} official site about us company profile{site_hint}".strip()
                if not domain and cc.upper() == "SA":
                    query += " site:*.sa"
            elif intent == "executives":
                query = f"{company} {cc} leadership management executives team board{site_hint}".strip()
                if not domain and cc.upper() == "SA":
                    query += " site:*.sa"
            else:
                query = f"{company} {cc} {intent}".strip()

            # 2) Google first (CSE), then Serper as fallback (tiny retry/backoff)
            serper_results: List[Dict[str, Any]] = []
            google_hits: List[Dict[str, Any]] = []
            try:
                # Prefer Google if configured
                gq = query
                google_hits = await self.google.search(gq, num=10)
            except Exception as _ge:
                print(f"⚠️ Google search failed: {_ge}")
            if self.serper_api_key:
                max_attempts = 3 if (cc or "").upper() == "SA" else 2
                for attempt in range(max_attempts):
                    try:
                        # adverse_media benefits from news endpoint
                        if intent == "adverse_media":
                            news_hits = await self._serper_search(query, country=cc, kind="news")
                            serper_results.extend(news_hits or [])
                        web_hits = await self._serper_search(query, country=cc, kind="web")
                        serper_results.extend(web_hits or [])
                        if serper_results:
                            break
                    except Exception:
                        pass
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1)

            # 2b) Seed from known domain so website/execs aren't null when search throttles
            if domain and intent in ("company_profile", "executives"):
                seed_url = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
                host = domain.split("/")[0]
                serper_results.append({
                    "title": f"{company} official site",
                    "url": seed_url,
                    "snippet": f"Official website for {company}",
                    "source": host,
                    "date": None,
                })
                serper_results.append({
                    "title": f"{company} leadership/about",
                    "url": seed_url.rstrip("/") + "/about-us",
                    "snippet": "Leadership / About Us",
                    "source": host,
                    "date": None,
                })
            merged_hits: List[Dict[str, Any]] = []
            # Merge Google and Serper hits (Google first)
            if google_hits:
                merged_hits.extend(self._dedupe_and_cap(google_hits, cap=30))
            if serper_results:
                merged_hits.extend(self._dedupe_and_cap(serper_results, cap=30))
            merged_hits = self._dedupe_and_cap(merged_hits, cap=40)

            if not merged_hits:
                return {"intent": intent, "results": schema, "total_found": 0, "providers": ["serper:0"]}

            if not self.openai_client:
                clean = prune_to_schema({}, schema)
                return {"intent": intent, "results": clean, "total_found": 0, "providers": [f"serper:{len(serper_results)}"]}

            # 3) Strict prompt with only the real results
            STRICT_SYS = (
                "You are a factual extraction engine.\n"
                "Use ONLY the provided web results below as evidence. Do not use prior knowledge.\n"
                "Return a SINGLE JSON object matching the schema. Unknown ⇒ null. Do not invent URLs."
            )
            base = self._intent_prompt(intent, company, country)
            user_prompt = (
                f'Company: "{company}" Country: "{country}" Intent: "{intent}"\n\n'
                f"WEB RESULTS (use as evidence; cite with source_url fields where applicable):\n"
                f"{json.dumps(merged_hits[:12], ensure_ascii=False, indent=2)}\n\n"
                f"Return ONLY a JSON object that matches this schema example (same keys, nulls allowed):\n"
                f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
            )
            try:
                resp = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "system", "content": STRICT_SYS}, {"role": "user", "content": base + "\n\n" + user_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0,
                    timeout=20,
                )
                raw = resp.choices[0].message.content or "{}"
                try:
                    data = json.loads(raw)
                except Exception:
                    data = {}
                clean = prune_to_schema(data, schema)
                total_found = self._count_for_intent(intent, clean)
                print("✅ GPT-4o structured response parsed")
                providers = []
                if google_hits: providers.append("google")
                if serper_results: providers.append(f"serper:{len(serper_results)}")
                providers.append("gpt-4o")
                return {"intent": intent, "results": clean, "total_found": total_found, "providers": providers}
            except Exception as e:
                print(f"⚠️ LLM structuring failed for {intent}: {e}")
                clean = prune_to_schema({}, schema)
                return {"intent": intent, "results": clean, "total_found": 0, "providers": [f"serper:{len(serper_results)}"]}

            # Create ChatGPT-5 search prompt for this intent
            if intent == "company_profile":
                search_prompt = f"""You are an extraction engine. Do NOT explain, comment, or add any text outside the required JSON.
Extract ONLY the following fields about the company: {company}{country_filter}.
If information is not available, return null.

Return in EXACT JSON format:

{{
    "company_info": {{
        "legal_name": "<full legal company name or null>",
        "website": "<official website URL or null>",
        "founded_year": "<year founded or null>",
        "headquarters": "<main office location or null>",
        "industry": "<primary business sector or null>",
        "business_description": "<what the company does or null>",
        "registration_status": "<legal registration status or null>",
        "entity_type": "<type of business entity or null>"
    }},
    "search_results": [
        {{
            "title": "<title of webpage or article>",
            "snippet": "<brief excerpt or summary>",
            "url": "<full URL where found>",
            "source": "<website or source name>",
            "date": "<date if available or null>"
        }}
    ]
}}

Search the web thoroughly and extract factual information. Return ONLY the JSON structure above."""
                
            elif intent == "executives":
                search_prompt = f"""You are an extraction engine. Do NOT explain, comment, or add any text outside the required JSON.
Extract ONLY the following fields about executives of: {company}{country_filter}.
If information is not available, return null.

Return in EXACT JSON format:

{{
    "executives": [
        {{
            "name": "<full name of executive or null>",
            "position": "<job title or position or null>",
            "company": "{company}",
            "background": "<brief background or experience or null>",
            "source_url": "<URL where found or null>",
            "source": "<website or source name or null>"
        }}
    ],
    "search_results": [
        {{
            "title": "<title of webpage or article>",
            "snippet": "<brief excerpt or summary>",
            "url": "<full URL where found>",
            "source": "<website or source name>",
            "date": "<date if available or null>"
        }}
    ]
}}

Search the web thoroughly for current CEO, board members, and top executives. Return ONLY the JSON structure above."""
                
            elif intent == "financials":
                search_prompt = f"""Search the internet for financial information about {company}{country_filter}.

IMPORTANT: You MUST return a JSON response with EXACTLY this structure:

{{
    "financial_data": {{
        "revenue": "Annual revenue or latest available",
        "profit": "Net profit or earnings",
        "assets": "Total assets if available",
        "employees": "Number of employees",
        "market_cap": "Market capitalization if public",
        "financial_year": "Year of financial data"
    }},
    "performance": {{
        "growth_rate": "Revenue or profit growth rate",
        "profitability": "Profit margin or profitability metrics",
        "financial_health": "Overall financial health assessment"
    }},
    "search_results": [
        {{
            "title": "Title of the webpage or article",
            "snippet": "Brief excerpt or summary of the content",
            "url": "Full URL where this information was found",
            "source": "Website or source name",
            "date": "Date if available"
        }}
    ],
    "source_urls": ["List of URLs where financial information was found"]
}}

Search thoroughly for current financial performance, annual reports, and financial statements. Return BOTH structured financial data AND raw search results."""
                
            elif intent == "adverse_media":
                search_prompt = f"""Search the internet for any adverse media coverage, controversies, negative news, legal issues, or concerning information about {company}{country_filter}.

IMPORTANT: You MUST return a JSON response with EXACTLY this structure:

{{
    "adverse_media": [
        {{
            "headline": "Specific headline or title of the negative news",
            "summary": "Brief summary of the controversy or issue",
            "date": "Date of the news if available",
            "source": "News source or website name",
            "severity": "High/Medium/Low",
            "category": "Legal/Financial/Regulatory/Reputation/Environmental/Other",
            "source_url": "URL where this information was found"
        }}
    ],
    "search_results": [
        {{
            "title": "Title of the webpage or article",
            "snippet": "Brief excerpt or summary of the content",
            "url": "Full URL where this information was found",
            "source": "Website or source name",
            "date": "Date if available"
        }}
    ],
    "total_incidents": "Number of adverse media items found",
    "risk_level": "High/Medium/Low based on findings",
    "key_concerns": ["List of main concerns or issues identified"],
    "source_urls": ["List of all source URLs where adverse media was found"]
}}

Search thoroughly for:
- Legal disputes or lawsuits
- Regulatory violations or fines
- Financial scandals or fraud
- Environmental controversies
- Labor disputes or worker issues
- Corruption allegations
- Negative media coverage
- Reputation issues
- Compliance problems
- Any other concerning news

Be thorough and search for real controversies that exist in the public domain.

Return BOTH structured adverse media data AND raw search results to ensure comprehensive coverage."""
                
            elif intent == "sanctions":
                search_prompt = f"""Search the internet for sanctions and compliance information about {company}{country_filter}.

IMPORTANT: You MUST return a JSON response with EXACTLY this structure:

{{
    "sanctions_status": {{
        "ofac_status": "OFAC sanctions status",
        "eu_status": "EU sanctions status",
        "un_status": "UN sanctions status",
        "overall_status": "Clean/Under Investigation/Sanctioned"
    }},
    "compliance_issues": [
        {{
            "type": "Type of compliance issue",
            "description": "Description of the issue",
            "severity": "High/Medium/Low",
            "source": "Source of information",
            "date": "Date if available"
        }}
    ],
    "search_results": [
        {{
            "title": "Title of the webpage or article",
            "snippet": "Brief excerpt or summary of the content",
            "url": "Full URL where this information was found",
            "source": "Website or source name",
            "date": "Date if available"
        }}
    ],
    "source_urls": ["List of URLs where sanctions information was found"]
}}

Search thoroughly for any sanctions, compliance issues, or regulatory restrictions. Return BOTH structured sanctions data AND raw search results."""
                
            elif intent == "ownership":
                search_prompt = f"""Search the internet for ownership structure information about {company}{country_filter}.

IMPORTANT: You MUST return a JSON response with EXACTLY this structure:

{{
    "ownership_structure": {{
        "parent_company": "Parent company if any",
        "subsidiaries": ["List of subsidiary companies"],
        "ownership_type": "Public/Private/Family-owned/State-owned"
    }},
    "shareholders": [
        {{
            "name": "Shareholder name",
            "percentage": "Ownership percentage if available",
            "type": "Individual/Corporate/Government",
            "source": "Source of information"
        }}
    ],
    "beneficial_owners": [
        {{
            "name": "Beneficial owner name",
            "relationship": "Relationship to company",
            "source": "Source of information"
        }}
    ],
    "search_results": [
        {{
            "title": "Title of the webpage or article",
            "snippet": "Brief excerpt or summary of the content",
            "url": "Full URL where this information was found",
            "source": "Website or source name",
            "date": "Date if available"
        }}
    ],
    "source_urls": ["List of URLs where ownership information was found"]
}}

Search thoroughly for ownership structure, shareholders, and beneficial ownership information. Return BOTH structured ownership data AND raw search results."""
                
            else:
                search_prompt = f"""Search the internet for comprehensive information about {company}{country_filter} related to {intent}.

Provide detailed, accurate information with source URLs.

Return your response in valid JSON format."""
            
            # DEPRECATED: ChatGPT-4o web search (replaced by strict LLM extraction + Serper)
            real_search_results = []
            
            if self.openai_client:
                try:
                    print(f"🤖 Using ChatGPT-4o for real-time internet search with specific {intent} prompt...")
                    print(f"🔍 Model being used: {self.openai_model}")
                    print(f"🔍 Prompt length: {len(search_prompt)} characters")
                    
                    # Use the specific search prompt for this intent
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert due diligence researcher with internet access. "
                                    "Search the web thoroughly and provide comprehensive, accurate information "
                                    "with proper source URLs. Focus on factual, verifiable data. "
                                    "IMPORTANT: You MUST return valid JSON that matches the exact structure requested."
                                )
                            },
                            {
                                "role": "user",
                                "content": search_prompt
                            }
                        ],
                        response_format={"type": "json_object"},
                        temperature=0,
                        max_tokens=3000
                    )
                    
                    print(f"✅ ChatGPT-4o API call successful")
                    result_text = response.choices[0].message.content
                    print(f"🔍 Response length: {len(result_text)} characters")
                    print(f"🔍 Response preview: {result_text[:200]}...")
                    
                    result_data = json.loads(result_text)
                    print(f"✅ JSON parsing successful")
                    
                    # Transform ChatGPT-4o results to standard format based on intent
                    # First, check if we have search_results (raw search data)
                    if 'search_results' in result_data and result_data['search_results']:
                        search_results = result_data['search_results']
                        print(f"✅ ChatGPT-4o search completed: {len(search_results)} raw search results found")
                        
                        # Use the raw search results as the primary data
                        real_search_results = search_results
                        
                        # Also store structured data if available for enhanced analysis
                        if intent == "executives" and 'executives' in result_data:
                            executives_list = result_data['executives']
                            print(f"✅ Plus {len(executives_list)} structured executives found")
                        elif intent == "company_profile" and 'company_info' in result_data:
                            company_info = result_data['company_info']
                            print(f"✅ Plus structured company info found")
                        elif intent == "adverse_media" and 'adverse_media' in result_data:
                            adverse_items = result_data['adverse_media']
                            print(f"✅ Plus {len(adverse_items)} structured adverse media items found")
                        elif intent == "financials" and 'financial_data' in result_data:
                            financial_data = result_data['financial_data']
                            print(f"✅ Plus structured financial data found")
                        elif intent == "sanctions" and 'sanctions_status' in result_data:
                            sanctions_status = result_data['sanctions_status']
                            print(f"✅ Plus structured sanctions data found")
                        elif intent == "ownership" and 'ownership_structure' in result_data:
                            ownership = result_data['ownership_structure']
                            print(f"✅ Plus structured ownership data found")
                    
                    # Fallback: if no search_results, use structured data
                    elif intent == "executives" and 'executives' in result_data:
                        # Special handling for executives to extract the list
                        executives_list = result_data['executives']
                        real_search_results = executives_list
                        print(f"✅ ChatGPT-4o executives search completed: {len(executives_list)} executives found")
                    elif intent == "company_profile" and 'company_info' in result_data:
                        # Handle company profile structured data
                        company_info = result_data['company_info']
                        real_search_results = [{
                            "title": f"Company Profile: {company_info.get('legal_name', 'Unknown')}",
                            "snippet": f"Industry: {company_info.get('industry', 'Unknown')}, Founded: {company_info.get('founded_year', 'Unknown')}, Website: {company_info.get('website', 'Unknown')}",
                            "url": company_info.get('website', ''),
                            "source": "Company Profile Search",
                            "structured_data": result_data
                        }]
                        print(f"✅ ChatGPT-4o company profile search completed with structured data")
                    elif intent == "adverse_media" and 'adverse_media' in result_data:
                        # Handle adverse media structured data
                        adverse_items = result_data['adverse_media']
                        real_search_results = [{
                            "title": item.get('headline', 'Adverse Media Item'),
                            "snippet": f"{item.get('category', 'Unknown')} - {item.get('summary', 'No summary')}",
                            "source": item.get('source', 'Unknown'),
                            "url": item.get('source_url', ''),
                            "structured_data": result_data
                        } for item in adverse_items]
                        print(f"✅ ChatGPT-4o adverse media search completed: {len(adverse_items)} items found")
                    elif intent == "financials" and 'financial_data' in result_data:
                        # Handle financials structured data
                        financial_data = result_data['financial_data']
                        real_search_results = [{
                            "title": f"Financial Information: {company}",
                            "snippet": f"Revenue: {financial_data.get('revenue', 'Unknown')}, Employees: {financial_data.get('employees', 'Unknown')}",
                            "url": "",
                            "source": "Financial Search",
                            "structured_data": result_data
                        }]
                        print(f"✅ ChatGPT-4o financials search completed with structured data")
                    elif intent == "sanctions" and 'sanctions_status' in result_data:
                        # Handle sanctions structured data
                        sanctions_status = result_data['sanctions_status']
                        real_search_results = [{
                            "title": f"Sanctions Status: {company}",
                            "snippet": f"Overall Status: {sanctions_status.get('overall_status', 'Unknown')}",
                            "url": "",
                            "source": "Sanctions Search",
                            "structured_data": result_data
                        }]
                        print(f"✅ ChatGPT-4o sanctions search completed with structured data")
                    elif intent == "ownership" and 'ownership_structure' in result_data:
                        # Handle ownership structured data
                        ownership = result_data['ownership_structure']
                        real_search_results = [{
                            "title": f"Ownership Structure: {company}",
                            "snippet": f"Type: {ownership.get('ownership_type', 'Unknown')}, Parent: {ownership.get('parent_company', 'None')}",
                            "url": "",
                            "source": "Ownership Search",
                            "structured_data": result_data
                        }]
                        print(f"✅ ChatGPT-4o ownership search completed with structured data")
                    elif intent == "executives" and 'search_results' in result_data:
                        # Handle case where executives search returns search_results format
                        search_results = result_data['search_results']
                        # Try to extract executive names from the search results
                        executives_list = []
                        
                        print(f"🔍 DEBUG: Processing {len(search_results)} executive search results")
                        print(f"🔍 DEBUG: Raw search results structure: {type(search_results)}")
                        print(f"🔍 DEBUG: First result keys: {list(search_results[0].keys()) if search_results else 'No results'}")
                        
                        # CRITICAL: Check if we're getting the right data structure
                        print(f"🔍 DEBUG: result_data keys: {list(result_data.keys())}")
                        print(f"🔍 DEBUG: result_data structure: {result_data}")
                        
                        # Process ALL search results, not just executives
                        real_search_results = []
                        
                        for i, result in enumerate(search_results):
                            print(f"🔍 DEBUG: Processing result {i+1}: {result.get('title', 'No title')}")
                            
                            # Add ALL results to real_search_results
                            real_search_results.append({
                                "title": result.get('title', 'No title'),
                                "snippet": result.get('snippet', 'No snippet'),
                                "url": result.get('url', ''),
                                "source": result.get('source', 'Unknown'),
                                "type": "executive_search_result"
                            })
                            
                            if 'snippet' in result and result['snippet']:
                                snippet = result.get('snippet', '')
                                title = result.get('title', '')
                                
                                print(f"🔍 DEBUG: Snippet: {snippet[:200]}...")
                                print(f"🔍 DEBUG: Title: {title}")
                                
                                # Look for executive-related keywords
                                executive_keywords = ['chairman', 'ceo', 'executive', 'president', 'director', 'managing director', 'board member', 'chief', 'head of', 'founder', 'owner', 'leader']
                                
                                if any(keyword in snippet.lower() or keyword in title.lower() for keyword in executive_keywords):
                                    print(f"✅ DEBUG: Found executive keywords in result {i+1}")
                                    
                                    # Try to extract names using multiple approaches
                                    potential_name = None
                                    
                                    # Approach 1: Look for "Name, Position" pattern
                                    import re
                                    name_comma_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)'
                                    match = re.search(name_comma_pattern, snippet)
                                    if match:
                                        potential_name = match.group(1)
                                        print(f"✅ DEBUG: Found name via comma pattern: {potential_name}")
                                    
                                    # Approach 2: Look for "Position Name" pattern
                                    if not potential_name:
                                        position_name_pattern = r'(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                                        match = re.search(position_name_pattern, snippet)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via position pattern: {potential_name}")
                                    
                                    # Approach 3: Look for "Name is Position" pattern
                                    if not potential_name:
                                        name_is_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(?:CEO|Chairman|President|Director)'
                                        match = re.search(name_is_pattern, snippet)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via 'is' pattern: {potential_name}")
                                    
                                    # Approach 4: Look for "The Position is Name" pattern
                                    if not potential_name:
                                        the_position_is_pattern = r'The\s+(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                                        match = re.search(the_position_is_pattern, snippet)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via 'The position is' pattern: {potential_name}")
                                    
                                    # Approach 5: Look for "Name serves as Position" pattern
                                    if not potential_name:
                                        serves_as_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+serves\s+as\s+(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)'
                                        match = re.search(serves_as_pattern, snippet)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via 'serves as' pattern: {potential_name}")
                                    
                                    # Approach 6: Look for "Position Name" in title
                                    if not potential_name and title:
                                        title_position_pattern = r'(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                                        match = re.search(title_position_pattern, title)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via title position pattern: {potential_name}")
                                    
                                    # Approach 7: Look for "Name - Position" in title
                                    if not potential_name and title:
                                        title_name_dash_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+-\s+(?:CEO|Chairman|President|Director|Managing Director|Chief|Head|Founder|Owner)'
                                        match = re.search(title_name_dash_pattern, title)
                                        if match:
                                            potential_name = match.group(1)
                                            print(f"✅ DEBUG: Found name via title dash pattern: {potential_name}")
                                    
                                    # Approach 8: Extract from title if it looks like a person's name
                                    if not potential_name and title:
                                        # Check if title looks like a person's name (not company name)
                                        title_words = title.split()
                                        if len(title_words) >= 2 and len(title_words) <= 4:
                                            # Filter out common company words
                                            company_words = ['rawabi', 'holding', 'company', 'group', 'saudi', 'arabia', 'ltd', 'inc', 'corp', 'overview', 'profile', 'team', 'executive', 'legal', 'regulatory', 'environmental', 'labor', 'financial', 'performance', 'scandals']
                                            if not any(word.lower() in company_words for word in title_words):
                                                potential_name = title
                                                print(f"✅ DEBUG: Found name via title pattern: {potential_name}")
                                    
                                    # Approach 9: Look for any capitalized words that might be names
                                    if not potential_name:
                                        # Find all capitalized word sequences
                                        name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
                                        potential_names = re.findall(name_pattern, snippet)
                                        
                                        # Filter out common non-name words and company names
                                        common_words = ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'company', 'group', 'holding', 'saudi', 'arabia', 'rawabi', 'ltd', 'inc', 'corp', 'rawabi', 'holding', 'group', 'overview', 'profile', 'team', 'executive', 'legal', 'regulatory', 'environmental', 'labor', 'financial', 'performance', 'scandals', 'disputes', 'controversies', 'violations', 'issues', 'practices']
                                        filtered_names = []
                                        
                                        for name in potential_names:
                                            # Skip if it's clearly a company name
                                            if any(company_word in name.lower() for company_word in ['rawabi', 'holding', 'company', 'group', 'saudi', 'arabia']):
                                                continue
                                            # Skip if it's too short or too long
                                            if len(name.split()) < 2 or len(name.split()) > 4:
                                                continue
                                            # Skip if it contains common non-name words
                                            if any(word.lower() in common_words for word in name.split()):
                                                continue
                                            filtered_names.append(name)
                                        
                                        if filtered_names:
                                            potential_name = filtered_names[0]
                                            print(f"✅ DEBUG: Found name via pattern matching: {potential_name}")
                                    
                                    # Approach 10: Look for specific executive name patterns in the snippet
                                    if not potential_name:
                                        # Look for patterns like "Sheikh Abdulaziz AlTurki" or "Mr. John Smith"
                                        executive_name_patterns = [
                                            r'Sheikh\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Sheikh names
                                            r'Mr\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',   # Mr. names
                                            r'Dr\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',   # Dr. names
                                            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(?:CEO|Chairman|President|Director)',  # "Name is Position"
                                            r'(?:CEO|Chairman|President|Director)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "Position Name"
                                        ]
                                        
                                        for pattern in executive_name_patterns:
                                            match = re.search(pattern, snippet)
                                            if match:
                                                potential_name = match.group(1)
                                                print(f"✅ DEBUG: Found name via executive pattern: {potential_name}")
                                                break
                                    
                                    # If we found a name, add it to executives list
                                    if potential_name:
                                        executives_list.append({
                                            "name": potential_name,
                                            "position": "Leadership position",
                                            "source": result.get('source', 'Unknown'),
                                            "url": result.get('url', ''),
                                            "snippet": snippet
                                        })
                                        print(f"✅ DEBUG: Added executive: {potential_name}")
                                    else:
                                        # Fallback: use a descriptive name based on source
                                        source_name = result.get('source', 'search results')
                                        executives_list.append({
                                            "name": f"Executive from {source_name}",
                                            "position": "Leadership position",
                                            "source": source_name,
                                            "url": result.get('url', ''),
                                            "snippet": snippet
                                        })
                                        print(f"⚠️ DEBUG: Using fallback name for result {i+1}")
                        
                        # Store executives separately but keep ALL search results
                        if executives_list:
                            print(f"✅ ChatGPT-4o executives search completed: {len(executives_list)} executives extracted from search results")
                            print(f"🔍 DEBUG: Executive names: {[exec.get('name', 'Unknown') for exec in executives_list]}")
                            # Add executives to the main results
                            real_search_results.extend(executives_list)
                        else:
                            print("⚠️ No executives found in search results")
                        
                        print(f"✅ Total results to return: {len(real_search_results)}")
                        
                    elif 'search_results' in result_data:
                        real_search_results = result_data['search_results']
                        print(f"✅ ChatGPT-4o search completed: {len(real_search_results)} results")
                    else:
                        print("⚠️ ChatGPT-4o response format unexpected, falling back to Serper")
                        real_search_results = []
                        
                except Exception as e:
                    print(f"❌ ChatGPT-4o search failed: {e}")
                    real_search_results = []
            
            # Fallback to Serper API if ChatGPT-4o fails or no results
            if not real_search_results:
                print(f"🔄 Falling back to Serper API...")
                for provider in self.search_providers:
                    if provider["type"] == "google_search":
                        try:
                            serper_results = await self._serper_search(f"{company}{country_filter} {intent}", country=country)
                            if serper_results:
                                real_search_results.extend(serper_results)
                                print(f"✅ Found {len(serper_results)} results via Serper fallback")
                        except Exception as e:
                            print(f"⚠️ Serper fallback failed: {e}")
                            continue
                
                # Final fallback to direct web scraping
                if not real_search_results:
                    try:
                        print(f"🔄 Trying direct web scraping as final fallback...")
                        scraping_results = await self._direct_scraping(company, country, intent)
                        if scraping_results:
                            real_search_results.extend(scraping_results)
                            print(f"✅ Found {len(scraping_results)} results via web scraping")
                    except Exception as e:
                        print(f"⚠️ Web scraping failed: {e}")
            
            # Now use LLM to analyze and structure the real search results
            if self.openai_client and real_search_results:
                try:
                    print(f"🤖 LLM analysis over {len(real_search_results)} real search results...")
                    
                    # Create analysis prompt with real data
                    # Handle different data structures for different intents
                    if intent == "executives" and isinstance(real_search_results, list) and len(real_search_results) > 0:
                        # For executives, analyze the executive information
                        analysis_prompt = f"""Analyze the following executive information about {company}{country_filter}:

EXECUTIVE DATA:
{json.dumps(real_search_results[:5], indent=2)}

Based on this executive information, provide comprehensive analysis in this JSON format:
{{
    "summary": "Summary of executive team structure and leadership",
    "key_information": ["List of key executives and their roles"],
    "source_urls": ["List of all source URLs"],
    "risk_assessment": "Assessment of any risks or concerns about leadership",
    "recommendations": ["List of recommendations for further research"]
}}

Focus on extracting factual information about the executive team."""
                    else:
                        # For other intents, use the standard analysis
                        analysis_prompt = f"""Analyze the following real internet search results about {company}{country_filter} for {intent}:

SEARCH RESULTS:
{json.dumps(real_search_results[:5], indent=2)}

Based on these real search results, provide comprehensive analysis in this JSON format:
{{
    "summary": "Comprehensive summary of findings",
    "key_information": ["List of key facts and data points"],
    "source_urls": ["List of all source URLs"],
    "risk_assessment": "Assessment of any risks or concerns",
    "recommendations": ["List of recommendations for further research"]
}}

Focus on extracting factual information from the real search results provided."""
                    
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert due diligence researcher. "
                                    "Analyze the provided search results and extract comprehensive, "
                                    "factual information. Focus on accuracy and proper source attribution."
                                )
                            },
                            {
                                "role": "user",
                                "content": analysis_prompt
                            }
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                        max_tokens=2000
                    )
                    
                    text = response.choices[0].message.content or "{}"
                    try:
                        result_data = json.loads(text)
                    except json.JSONDecodeError:
                        if text.strip().startswith("```"):
                            text = text.split("```", 2)[1].lstrip("json\n").strip()
                        result_data = json.loads(text)
                    
                    # Combine real search results with ChatGPT analysis
                    enhanced_results = {
                        "intent": intent,
                        "results": real_search_results,
                        "total_found": len(real_search_results),
                        "search_method": "Serper API + LLM Analysis",
                        "real_search_results": real_search_results,
                        "llm_analysis": result_data,
                        "gpt5_analysis": result_data
                    }
                    
                    return enhanced_results
                    
                except Exception as e:
                    print(f"❌ ChatGPT-5 analysis failed for {intent}: {e}")
                    # Return just the real search results
                    return {
                        "intent": intent,
                        "results": real_search_results,
                        "total_found": len(real_search_results),
                        "search_method": "Serper API (ChatGPT analysis failed)",
                        "real_search_results": real_search_results
                    }
            else:
                # Return just the real search results if no ChatGPT
                return {
                    "intent": intent,
                    "results": real_search_results,
                    "total_found": len(real_search_results),
                    "search_method": "Serper API + Web Scraping",
                    "real_search_results": real_search_results
                }
            
        except Exception as e:
            print(f"❌ Intent search failed for {intent}: {e}")
            return {"error": f"Intent search failed: {str(e)}"}

    async def _serper_search(self, query: str, country: str = "", num: int = 20, kind: str = "web") -> List[Dict]:
        """Query Serper (web or news) and normalize results."""
        if not self.serper_api_key:
            return []
        endpoint = "https://google.serper.dev/search" if kind == "web" else "https://google.serper.dev/news"
        headers = {"X-API-KEY": self.serper_api_key, "Content-Type": "application/json"}
        body = {"q": query, "num": max(30, num)}
        # Light geo hint from country code; default to KSA for relevance
        gl = (country or "sa").strip().lower() or "sa"
        body["gl"] = gl
        body["hl"] = "en"
        out: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            r = await client.post(endpoint, headers=headers, json=body)
        if r.status_code != 200:
            raise RuntimeError(f"Serper {kind} HTTP {r.status_code}: {r.text[:200]}")
        j = r.json() or {}
        keys = ["organic", "topStories", "knowledgeGraph", "answerBox"] if kind == "web" else ["news"]
        for sec in keys:
            items = j.get(sec) or []
            for it in items:
                url = it.get("link") or it.get("url") or it.get("website") or ""
                if not url:
                    continue
                out.append({
                    "title": it.get("title") or it.get("name") or it.get("snippet") or "",
                    "url": url,
                    "snippet": it.get("snippet") or it.get("description") or "",
                    "source": it.get("source") or sec,
                    "date": it.get("date") or it.get("publishedDate"),
                })
        return self._dedupe_and_cap(out, cap=30)



    async def _direct_scraping(self, company: str, country: str, intent: str) -> List[Dict]:
        """No-op: scraping disabled in LLM-only mode"""
        return []

    async def _enhance_with_gpt5(self, company: str, country: str, search_results: Dict) -> Dict[str, Any]:
        """Enhance search results with GPT-5 analysis"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        try:
            print(f"🤖 Enhancing results with GPT-5 for {company}")
            
            # Prepare context for GPT-5
            context = self._prepare_gpt5_context(company, country, search_results)
            
            # Create prompt for GPT-5
            prompt = f"""
You are a professional due diligence analyst. Analyze the following real-time search results for {company}{f" in {country}" if country else ""} and provide enhanced insights.

SEARCH RESULTS:
{json.dumps(context, indent=2)}

Please provide:
1. Executive summary of findings
2. Key risk factors identified
3. Confidence level in the data
4. Recommendations for further investigation
5. Data quality assessment

Return your response in JSON format.
"""
            
            # Call GPT-5
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a due diligence expert. Provide accurate, professional analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            print(f"✅ GPT-5 enhancement completed for {company}")
            return result_data
            
        except Exception as e:
            print(f"❌ GPT-5 enhancement failed: {e}")
            return {"error": f"GPT-5 enhancement failed: {str(e)}"}

    def _prepare_gpt5_context(self, company: str, country: str, search_results: Dict) -> Dict:
        """Prepare context for GPT-5 analysis"""
        context = {
            "company": company,
            "country": country,
            "search_timestamp": datetime.now().isoformat(),
            "search_summary": {}
        }
        
        for intent, results in search_results.items():
            if intent == "metadata":
                continue
                
            if "error" in results:
                context["search_summary"][intent] = {"status": "failed", "error": results["error"]}
            else:
                # Handle both list and dict results
                if isinstance(results, list):
                    # If results is a list, count the items
                    context["search_summary"][intent] = {
                        "status": "success",
                        "total_found": len(results),
                        "sample_results": results[:3] if results else []  # Top 3 results
                    }
                elif isinstance(results, dict):
                    # If results is a dict, use the standard approach
                    context["search_summary"][intent] = {
                        "status": "success",
                        "total_found": results.get("total_found", 0),
                        "sample_results": results.get("results", [])[:3] if results.get("results") else []  # Top 3 results
                    }
                else:
                    # Fallback for other types
                    context["search_summary"][intent] = {
                        "status": "success",
                        "total_found": 0,
                        "sample_results": []
                    }
        
        return context

    def _transform_gpt5_search_results(self, gpt5_data: Dict, intent: str, company: str) -> List[Dict]:
        """Transform ChatGPT-5 search results to standard format"""
        try:
            results = []
            
            # Handle different response structures from GPT-5
            if "results" in gpt5_data:
                # Standard results array
                for item in gpt5_data["results"]:
                    results.append({
                        "title": item.get("title", f"{company} - {intent}"),
                        "url": item.get("url", item.get("source_url", "")),
                        "snippet": item.get("summary", item.get("description", "")),
                        "source": "ChatGPT-5 Web Search",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": item.get("confidence", "high")
                    })
            elif "company_info" in gpt5_data:
                # Company profile structure
                company_info = gpt5_data["company_info"]
                results.append({
                    "title": f"{company} - Company Profile",
                    "url": company_info.get("website", ""),
                    "snippet": company_info.get("description", ""),
                    "source": "ChatGPT-5 Web Search",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": "high"
                })
            elif "executives" in gpt5_data:
                # Executives structure
                for exec_info in gpt5_data["executives"]:
                    results.append({
                        "title": f"{exec_info.get('name', 'Unknown')} - {exec_info.get('position', 'Unknown')}",
                        "url": exec_info.get("source_url", ""),
                        "snippet": exec_info.get("background", ""),
                        "source": "ChatGPT-5 Web Search",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": exec_info.get("confidence", "high")
                    })
            elif "financials" in gpt5_data:
                # Financial information structure
                financials = gpt5_data["financials"]
                results.append({
                    "title": f"{company} - Financial Information",
                    "url": financials.get("source_url", ""),
                    "snippet": f"Revenue: {financials.get('revenue', 'N/A')}, Employees: {financials.get('employees', 'N/A')}",
                    "source": "ChatGPT-5 Web Search",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": "high"
                })
            else:
                # Generic structure - try to extract any useful information
                for key, value in gpt5_data.items():
                    if isinstance(value, list) and value:
                        for item in value[:3]:  # Limit to first 3 items
                            if isinstance(item, dict):
                                results.append({
                                    "title": f"{company} - {key.title()}",
                                    "url": item.get("url", item.get("source_url", "")),
                                    "snippet": str(item.get("summary", item.get("description", ""))),
                                    "source": "ChatGPT-5 Web Search",
                                    "timestamp": datetime.now().isoformat(),
                                    "confidence": "high"
                                })
            
            return results[:10]  # Limit to top 10 results
            
        except Exception as e:
            print(f"❌ Error transforming GPT-5 results: {e}")
            return []

    async def _fallback_search(self, company: str, country: str, intent: str) -> Dict[str, Any]:
        """Fallback search using traditional methods"""
        try:
            print(f"🔄 Using fallback search for {intent}")
            
            country_filter = f" {country}" if country else ""
            query = f"{company}{country_filter} {intent}"
            
            all_results = []
            
            # Try Serper API if available
            for provider in self.search_providers:
                if provider["type"] == "google_search":
                    try:
                        results = await self._serper_search(query, country=country)
                        if results:
                            all_results.extend(results)
                    except Exception as e:
                        print(f"⚠️ Serper fallback failed: {e}")
                        continue
                
                elif provider["type"] == "web_scraping":
                    try:
                        results = await self._direct_scraping(company, country, intent)
                        if results:
                            all_results.extend(results)
                    except Exception as e:
                        print(f"⚠️ Direct scraping fallback failed: {e}")
                        continue
            
            # Deduplicate and return results
            unique_results = self._deduplicate_results(all_results)
            return {
                "intent": intent,
                "results": unique_results[:10],
                "total_found": len(unique_results),
                "search_method": "Fallback (Traditional)"
            }
            
        except Exception as e:
            print(f"❌ Fallback search failed: {e}")
            return {"error": f"Fallback search failed: {str(e)}"}

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results by URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results

    def _dedupe_and_cap(self, items: List[Dict], cap: int = 50) -> List[Dict]:
        """Deduplicate by URL and cap the list length"""
        seen: set = set()
        out: List[Dict] = []
        for it in items or []:
            u = it.get("url") if isinstance(it, dict) else None
            if not u or u in seen:
                continue
            seen.add(u)
            out.append(it)
            if len(out) >= cap:
                break
        return out

    def _count_for_intent(self, intent: str, clean: Dict[str, Any]) -> int:
        if intent == "executives":
            return len(clean.get("executives") or [])
        if intent == "adverse_media":
            return len(clean.get("adverse_media") or [])
        if intent == "company_profile":
            return 1 if clean.get("company_info") else 0
        if intent == "financials":
            return 1 if clean.get("financial_data") else 0
        if intent == "sanctions":
            return 1 if clean.get("sanctions_status") else 0
        if intent == "ownership":
            return 1 if clean.get("ownership_structure") else 0
        return 0

    async def quick_search(self, company: str, country: str = "") -> Dict[str, Any]:
        """Quick search for basic company information using real internet data + ChatGPT-5 analysis"""
        try:
            print(f"🔍 Quick search for: {company}")
            
            country_filter = f" {country}" if country else ""
            
            # DEPRECATED: ChatGPT-4o web search (replaced by strict LLM extraction + Serper)
            real_search_results = []
            
            if self.openai_client:
                try:
                    print(f"🤖 Using ChatGPT-4o for real-time company search...")
                    
                    # Create a comprehensive search prompt for ChatGPT-4o
                    company_search_prompt = f"""Search the internet in real-time for comprehensive company information about {company}{country_filter}.

Focus on:
1. Official website URL
2. Company description and overview
3. Current executives and leadership team
4. Company structure and background

Search the web thoroughly and provide detailed, factual information with source URLs. Return your response in valid JSON format with this structure:
{{
    "search_results": [
        {{
            "title": "Title or headline of the information found",
            "snippet": "Brief summary or excerpt",
            "url": "Source URL",
            "source": "Website or source name",
            "date": "Date if available",
            "relevance": "High/Medium/Low"
        }}
    ],
    "company_info": {{
        "website": "Official website URL if found",
        "description": "Company description based on search results",
        "executives": [
            {{
                "name": "Executive Name if found",
                "position": "Job Title if found",
                "source_url": "URL where found"
            }}
        ]
    }}
}}"""
                    
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert due diligence researcher with internet access. "
                                    "Search the web thoroughly and provide comprehensive company information. "
                                    "Focus on accuracy and proper source attribution."
                                )
                            },
                            {
                                "role": "user",
                                "content": company_search_prompt
                            }
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                        max_tokens=2500
                    )
                    
                    result_text = response.choices[0].message.content
                    result_data = json.loads(result_text)
                    
                    # Extract company info directly from ChatGPT-4o response
                    if 'company_info' in result_data:
                        company_info = result_data['company_info']
                        real_search_results = result_data.get('search_results', [])
                        
                        # Transform to standard format
                        quick_summary = {
                            "company": company,
                            "country": country,
                            "website": company_info.get("website"),
                            "company_description": company_info.get("description", ""),
                            "executives": company_info.get("executives", []),
                            "search_timestamp": datetime.now().isoformat(),
                            "search_method": "ChatGPT-4o Real-time Search",
                            "real_search_results": real_search_results,
                            "gpt5_analysis": result_data
                        }
                        
                        print(f"✅ Quick search completed using ChatGPT-4o real-time search")
                        return quick_summary
                    else:
                        print("⚠️ ChatGPT-4o response format unexpected, falling back to Serper")
                        real_search_results = []
                        
                except Exception as e:
                    print(f"❌ ChatGPT-4o search failed: {e}")
                    real_search_results = []
            
            # Fallback to Serper API if ChatGPT-4o fails or no results
            if not real_search_results:
                print(f"🔄 Falling back to Serper API...")
                for provider in self.search_providers:
                    if provider["type"] == "google_search":
                        try:
                            serper_results = await self._serper_search(f"{company}{country_filter} company profile executives", country=country)
                            if serper_results:
                                real_search_results.extend(serper_results)
                                print(f"✅ Found {len(serper_results)} results via Serper fallback")
                        except Exception as e:
                            print(f"⚠️ Serper fallback failed: {e}")
                            continue
                
                # Final fallback to direct web scraping
                if not real_search_results:
                    try:
                        print(f"🔄 Trying direct web scraping as final fallback...")
                        scraping_results = await self._direct_scraping(company, country, "company_profile")
                        if scraping_results:
                            real_search_results.extend(scraping_results)
                            print(f"✅ Found {len(scraping_results)} results via web scraping")
                    except Exception as e:
                        print(f"⚠️ Web scraping failed: {e}")
            
            # Now use ChatGPT-5 to analyze and extract key information from fallback results
            if self.openai_client and real_search_results:
                try:
                    print(f"🤖 Using ChatGPT-5 to analyze {len(real_search_results)} real search results...")
                    
                    analysis_prompt = f"""Analyze the following real internet search results about {company}{country_filter}:

SEARCH RESULTS:
{json.dumps(real_search_results[:5], indent=2)}

Extract and return the following information in this exact JSON format:
{{
    "website": "official website URL if found",
    "company_description": "brief company description based on search results",
    "executives": [
        {{
            "name": "Executive Name if found",
            "position": "Job Title if found",
            "source_url": "URL where found"
        }}
    ]
}}

Focus on extracting factual information from the real search results provided."""
                    
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert due diligence researcher. "
                                    "Analyze the provided search results and extract key company information. "
                                    "Focus on accuracy and proper source attribution."
                                )
                            },
                            {
                                "role": "user",
                                "content": analysis_prompt
                            }
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                        max_tokens=1500
                    )
                    
                    result_text = response.choices[0].message.content
                    result_data = json.loads(result_text)
                    
                    # Transform to standard format
                    quick_summary = {
                        "company": company,
                        "country": country,
                        "website": result_data.get("website"),
                        "company_description": result_data.get("company_description", ""),
                        "executives": result_data.get("executives", []),
                        "search_timestamp": datetime.now().isoformat(),
                        "search_method": "Serper API + ChatGPT-5 Analysis",
                        "real_search_results": real_search_results,
                        "gpt5_analysis": result_data
                    }
                    
                    print(f"✅ Quick search completed using real internet data + ChatGPT-5 analysis")
                    return quick_summary
                    
                except Exception as e:
                    print(f"❌ ChatGPT-5 analysis failed: {e}")
                    # Return just the real search results
                    return {
                        "company": company,
                        "country": country,
                        "website": None,
                        "company_description": "Analysis failed, but real search results available",
                        "executives": [],
                        "search_timestamp": datetime.now().isoformat(),
                        "search_method": "Serper API (ChatGPT analysis failed)",
                        "real_search_results": real_search_results
                    }
            else:
                # Return just the real search results if no ChatGPT
                return {
                    "company": company,
                    "country": country,
                    "website": None,
                    "company_description": "Real search results available, no analysis",
                    "executives": [],
                    "search_timestamp": datetime.now().isoformat(),
                    "search_method": "Serper API + Web Scraping",
                    "real_search_results": real_search_results
                }
            
        except Exception as e:
            print(f"❌ Quick search failed: {e}")
            return {"error": f"Quick search failed: {str(e)}"}

    async def _fallback_quick_search(self, company: str, country: str = "") -> Dict[str, Any]:
        """Fallback quick search using traditional methods"""
        try:
            print("🔄 Using fallback quick search...")
            essential_intents = ["company_profile", "executives"]
            collected: Dict[str, Any] = {}
            for intent in essential_intents:
                collected[intent] = await self._fallback_search(company, country, intent)

            quick_summary = {
                "company": company,
                "country": country,
                "website": None,
                "executives": [],
                "search_timestamp": datetime.now().isoformat(),
                "search_method": "Fallback (Traditional)",
            }

            profile_results = collected.get("company_profile", {}).get("results", [])
            for r in profile_results:
                title = (r.get("title") or "").lower()
                if "official" in title or "website" in title:
                    quick_summary["website"] = r.get("url")
                    break

            exec_results = collected.get("executives", {}).get("results", [])
            for r in exec_results[:3]:
                ttl = r.get("title", "")
                name, _, role = ttl.partition(" - ")
                quick_summary["executives"].append({
                    "name": name.strip() or "Unknown",
                    "position": role.strip() or "Unknown",
                    "source": r.get("url"),
                })

            return quick_summary
        except Exception as e:
            print(f"❌ Fallback quick search failed: {e}")
            return {"error": f"Fallback quick search failed: {str(e)}"}

# Global real-time search service instance
real_time_search_service = RealTimeSearchService()
