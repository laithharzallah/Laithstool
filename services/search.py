"""
Web search service with multiple providers and RSS fallback
"""
import os
import asyncio
from typing import List, Dict, Optional, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import feedparser
from datetime import datetime, timedelta


class SearchProvider:
    """Base search provider class"""
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Execute search and return results"""
        raise NotImplementedError


class SerperProvider(SearchProvider):
    """Serper.dev search provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using Serper API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": min(num_results, 100)
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("organic", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source_type": "web",
                        "provider": "serper"
                    })
                
                return results
                
        except Exception as e:
            print(f"❌ Serper search failed: {e}")
            return []


class BingProvider(SearchProvider):
    """Bing Web Search API provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using Bing API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers={
                        "Ocp-Apim-Subscription-Key": self.api_key
                    },
                    params={
                        "q": query,
                        "count": min(num_results, 50),
                        "responseFilter": "Webpages"
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("webPages", {}).get("value", []):
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "source_type": "web",
                        "provider": "bing"
                    })
                
                return results
                
        except Exception as e:
            print(f"❌ Bing search failed: {e}")
            return []


class RSSFallbackProvider(SearchProvider):
    """RSS feeds fallback when APIs are unavailable"""
    
    def __init__(self):
        self.news_feeds = [
            "https://news.google.com/rss?q={query}&hl=en&gl=US&ceid=US:en",
            "https://www.bing.com/news/search?q={query}&format=rss",
            "https://feeds.reuters.com/reuters/companyNews"
        ]
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using RSS feeds"""
        try:
            results = []
            
            for feed_url in self.news_feeds[:2]:  # Limit to 2 feeds
                try:
                    formatted_url = feed_url.format(query=query.replace(" ", "+"))
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(formatted_url, timeout=20)
                        response.raise_for_status()
                        
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries[:num_results//2]:
                        results.append({
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "snippet": entry.get("summary", "")[:300],
                            "source_type": "news",
                            "provider": "rss",
                            "published": entry.get("published", "")
                        })
                    
                except Exception as e:
                    print(f"⚠️ RSS feed failed: {e}")
                    continue
                
            return results[:num_results]
            
        except Exception as e:
            print(f"❌ RSS fallback failed: {e}")
            return []


class SearchService:
    """Main search service coordinating multiple providers"""
    
    def __init__(self):
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self) -> SearchProvider:
        """Initialize the best available search provider"""
        provider_type = os.getenv("SEARCH_PROVIDER", "").lower()
        
        if provider_type == "serper":
            api_key = os.getenv("SERPER_API_KEY")
            if api_key:
                print("✅ Using Serper search provider")
                return SerperProvider(api_key)
        
        elif provider_type == "bing":
            api_key = os.getenv("BING_API_KEY")
            if api_key:
                print("✅ Using Bing search provider")
                return BingProvider(api_key)
        
        print("⚠️ No API provider available, using RSS fallback")
        return RSSFallbackProvider()
    
    async def search_multiple_intents(self, company: str, country: str = "") -> Dict[str, List[Dict]]:
        """
        Search for company using multiple intent buckets
        
        Returns:
            Dict with buckets: official_site, news, adverse_media, sanctions, tech_footprint
        """
        try:
            country_filter = f" {country}" if country else ""
            
            # Define search intent buckets
            search_intents = {
                "official_site": [
                    f'"{company}"{country_filter} site:company.com OR site:corporation.com',
                    f'"{company}"{country_filter} official website',
                    f'"{company}"{country_filter} about company'
                ],
                "registry": [
                    f'"{company}"{country_filter} company registration',
                    f'"{company}"{country_filter} business registry',
                    f'"{company}"{country_filter} corporate filings'
                ],
                "news": [
                    f'"{company}"{country_filter} news 2024',
                    f'"{company}"{country_filter} press release',
                    f'"{company}"{country_filter} announcement'
                ],
                "adverse_media": [
                    f'"{company}"{country_filter} lawsuit investigation',
                    f'"{company}"{country_filter} fraud corruption',
                    f'"{company}"{country_filter} penalty fine scandal',
                    f'"{company}"{country_filter} controversy allegations'
                ],
                "sanctions": [
                    f'"{company}"{country_filter} sanctions OFAC',
                    f'"{company}"{country_filter} watchlist blacklist',
                    f'"{company}"{country_filter} restricted entity'
                ],
                "bribery_corruption": [
                    f'"{company}"{country_filter} bribery corruption',
                    f'"{company}"{country_filter} kickback embezzlement',
                    f'"{company}"{country_filter} FCPA violations'
                ],
                "political_exposure": [
                    f'"{company}"{country_filter} government owned',
                    f'"{company}"{country_filter} political connections PEP',
                    f'"{company}"{country_filter} state enterprise'
                ]
            }
            
            results = {}
            
            print(f"🔍 Searching for {company} across {len(search_intents)} intent buckets...")
            
            # Execute searches for each intent bucket
            for bucket, queries in search_intents.items():
                bucket_results = []
                
                for query in queries[:2]:  # Limit queries per bucket
                    try:
                        search_results = await self.provider.search(query, 5)
                        bucket_results.extend(search_results)
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"⚠️ Query failed for {bucket}: {e}")
                        continue
                
                # Deduplicate by URL
                unique_results = self._deduplicate_by_url(bucket_results)
                results[bucket] = unique_results[:5]  # Top 5 per bucket
                
                print(f"📊 {bucket}: {len(unique_results)} unique results")
            
            return results
            
        except Exception as e:
            print(f"❌ Multi-intent search failed: {e}")
            return {}
    
    def _deduplicate_by_url(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results by URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def search_single(self, query: str, num_results: int = 10) -> List[Dict]:
        """Execute single search query"""
        try:
            return await self.provider.search(query, num_results)
        except Exception as e:
            print(f"❌ Single search failed: {e}")
            return []


# Global search service instance
search_service = SearchService()