"""
Web search service for Company Screener.
Supports multiple search providers: Serper, Bing Web Search, Google Custom Search.
"""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from schemas.report import SourceReference, ConfidenceLevel

logger = logging.getLogger(__name__)


class SearchProvider:
    """Base class for search providers"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for a query and return results"""
        raise NotImplementedError
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class SerperProvider(SearchProvider):
    """Serper.dev search provider"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://google.serper.dev"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Serper API"""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": "us",
            "hl": "en"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic" in data:
                for item in data["organic"]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "serper",
                        "position": item.get("position", 0)
                    })
            
            logger.info(f"Serper search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Serper search failed for '{query}': {str(e)}")
            return []


class BingProvider(SearchProvider):
    """Bing Web Search API provider"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API"""
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": min(num_results, 50),  # Bing max is 50
            "mkt": "en-US",
            "safeSearch": "Moderate"
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "webPages" in data and "value" in data["webPages"]:
                for i, item in enumerate(data["webPages"]["value"]):
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "bing",
                        "position": i + 1
                    })
            
            logger.info(f"Bing search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Bing search failed for '{query}': {str(e)}")
            return []


class SearchService:
    """Main search service that manages multiple providers"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available search providers based on environment variables"""
        serper_key = os.getenv("SERPER_API_KEY")
        bing_key = os.getenv("BING_API_KEY")
        
        if serper_key:
            self.providers["serper"] = SerperProvider(serper_key)
            logger.info("Serper search provider initialized")
        
        if bing_key:
            self.providers["bing"] = BingProvider(bing_key)
            logger.info("Bing search provider initialized")
        
        if not self.providers:
            logger.warning("No search providers available - add SERPER_API_KEY or BING_API_KEY")
    
    def is_available(self) -> bool:
        """Check if any search providers are available"""
        return len(self.providers) > 0
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    async def search_multiple(self, queries: List[str], provider: str = "auto", num_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Search multiple queries and return aggregated results"""
        if not self.is_available():
            logger.error("No search providers available")
            return {}
        
        if provider == "auto":
            provider = list(self.providers.keys())[0]  # Use first available
        
        if provider not in self.providers:
            logger.error(f"Provider '{provider}' not available")
            return {}
        
        results = {}
        search_provider = self.providers[provider]
        
        # Run searches concurrently
        tasks = []
        for query in queries:
            task = asyncio.create_task(search_provider.search(query, num_results))
            tasks.append((query, task))
        
        for query, task in tasks:
            try:
                query_results = await task
                results[query] = query_results
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {str(e)}")
                results[query] = []
        
        return results
    
    async def search_company_intents(self, company_name: str, domain: Optional[str] = None, country: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search for company information across different intent buckets"""
        
        # Build base search terms
        base_terms = [company_name]
        if domain:
            base_terms.append(domain)
        if country:
            location_hint = f"in {country}"
        else:
            location_hint = ""
        
        # Define search intent buckets
        search_intents = {
            "official_site": [
                f"{company_name} official website {location_hint}",
                f"{company_name} about us {location_hint}",
                f"site:{domain}" if domain else f"{company_name} company website"
            ],
            "contact_info": [
                f"{company_name} contact information {location_hint}",
                f"{company_name} headquarters address {location_hint}",
                f"{company_name} phone email {location_hint}"
            ],
            "executives": [
                f"{company_name} CEO executive team {location_hint}",
                f"{company_name} leadership management {location_hint}",
                f"{company_name} board of directors {location_hint}"
            ],
            "news_press": [
                f"{company_name} news press release {location_hint}",
                f"{company_name} announcement {location_hint}",
                f"{company_name} media coverage {location_hint}"
            ],
            "linkedin": [
                f"site:linkedin.com/company {company_name}",
                f"site:linkedin.com/in {company_name} CEO",
                f"site:linkedin.com {company_name} employees"
            ],
            "registry": [
                f"{company_name} company registration {location_hint}",
                f"{company_name} business license {location_hint}",
                f"{company_name} incorporation {location_hint}"
            ],
            "financials": [
                f"{company_name} financial results {location_hint}",
                f"{company_name} annual report {location_hint}",
                f"{company_name} revenue earnings {location_hint}"
            ]
        }
        
        # Flatten all queries
        all_queries = []
        intent_mapping = {}
        
        for intent, queries in search_intents.items():
            for query in queries:
                all_queries.append(query)
                intent_mapping[query] = intent
        
        # Execute all searches
        raw_results = await self.search_multiple(all_queries, num_results=5)
        
        # Group results by intent
        intent_results = {intent: [] for intent in search_intents.keys()}
        
        for query, results in raw_results.items():
            intent = intent_mapping.get(query)
            if intent and results:
                intent_results[intent].extend(results)
        
        # Deduplicate results within each intent
        for intent in intent_results:
            seen_urls = set()
            deduplicated = []
            for result in intent_results[intent]:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    deduplicated.append(result)
            intent_results[intent] = deduplicated[:10]  # Limit to top 10 per intent
        
        return intent_results
    
    def create_source_references(self, search_results: List[Dict[str, Any]]) -> List[SourceReference]:
        """Convert search results to SourceReference objects"""
        references = []
        
        for result in search_results:
            try:
                ref = SourceReference(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    domain=self._extract_domain(result.get("url", "")),
                    confidence=ConfidenceLevel.MEDIUM,
                    accessed_at=datetime.utcnow()
                )
                references.append(ref)
            except Exception as e:
                logger.warning(f"Failed to create source reference: {str(e)}")
                continue
        
        return references
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None
    
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            await provider.close()


# Global search service instance
search_service = SearchService()