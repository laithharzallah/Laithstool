"""
HTML extraction service with robots.txt awareness and content cleaning
"""
import asyncio
import hashlib
import urllib.robotparser
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime

import httpx
import trafilatura
from readability import Document
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


class RobotsChecker:
    """Check robots.txt compliance for URLs"""
    
    def __init__(self):
        self.robots_cache = {}
    
    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = urljoin(base_url, "/robots.txt")
            
            # Check cache first
            if robots_url in self.robots_cache:
                robots_parser = self.robots_cache[robots_url]
            else:
                # Fetch and parse robots.txt
                robots_parser = urllib.robotparser.RobotFileParser()
                robots_parser.set_url(robots_url)
                
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(robots_url, timeout=10)
                        if response.status_code == 200:
                            robots_parser.set_content(response.text)
                        robots_parser.read()
                        
                    self.robots_cache[robots_url] = robots_parser
                    
                except Exception:
                    # If robots.txt can't be fetched, assume allowed
                    robots_parser = None
                    self.robots_cache[robots_url] = None
            
            if robots_parser:
                return robots_parser.can_fetch(user_agent, url)
            else:
                return True  # Default to allowing if no robots.txt
                
        except Exception as e:
            print(f"⚠️ Robots check failed for {url}: {e}")
            return True  # Default to allowing on error


class ContentExtractor:
    """Extract and clean content from HTML"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CompanyScreener/1.0; +https://example.com/bot)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def extract_content(self, url: str) -> Dict:
        """Extract clean text content from URL"""
        try:
            print(f"📄 Extracting content from: {url}")
            
            # Fetch the page
            response = await self.session.get(url)
            response.raise_for_status()
            
            html_content = response.text
            
            # Try trafilatura first (best for main content)
            extracted_text = trafilatura.extract(
                html_content,
                include_tables=True,
                include_links=True,
                output_format='txt'
            )
            
            # Fallback to readability if trafilatura fails
            if not extracted_text or len(extracted_text.strip()) < 100:
                try:
                    doc = Document(html_content)
                    extracted_text = doc.summary()
                    # Convert HTML to text
                    soup = BeautifulSoup(extracted_text, 'html.parser')
                    extracted_text = soup.get_text()
                except Exception:
                    extracted_text = ""
            
            # Final fallback: basic BeautifulSoup extraction
            if not extracted_text or len(extracted_text.strip()) < 50:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                extracted_text = soup.get_text()
            
            # Clean up the text
            cleaned_text = self._clean_text(extracted_text)
            
            # Extract metadata
            metadata = self._extract_metadata(html_content, url)
            
            result = {
                "url": url,
                "title": metadata.get("title", ""),
                "text": cleaned_text,
                "content_length": len(cleaned_text),
                "source_type": self._determine_source_type(url),
                "published_at": metadata.get("published_at"),
                "author": metadata.get("author"),
                "content_hash": hashlib.md5(cleaned_text.encode()).hexdigest(),
                "extraction_success": True,
                "extraction_method": "trafilatura" if "trafilatura" in str(type(extracted_text)) else "fallback"
            }
            
            print(f"✅ Extracted {len(cleaned_text)} chars from {url}")
            return result
            
        except Exception as e:
            print(f"❌ Content extraction failed for {url}: {e}")
            return {
                "url": url,
                "title": "",
                "text": "",
                "content_length": 0,
                "source_type": "unknown",
                "extraction_success": False,
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Split into lines and clean each
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and very short lines
            if len(line) < 3:
                continue
                
            # Skip lines that are mostly punctuation or navigation
            if len([c for c in line if c.isalnum()]) < len(line) * 0.5:
                continue
            
            # Skip common navigation/boilerplate text
            skip_patterns = [
                'cookie', 'privacy policy', 'terms of service', 'all rights reserved',
                'subscribe', 'newsletter', 'follow us', 'social media', 'contact us',
                'home', 'about', 'services', 'products', 'news', 'careers'
            ]
            
            if any(pattern in line.lower() for pattern in skip_patterns) and len(line) < 100:
                continue
            
            cleaned_lines.append(line)
        
        # Join lines and limit length
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Limit to reasonable length for GPT processing
        if len(cleaned_text) > 3000:
            cleaned_text = cleaned_text[:3000] + "..."
        
        return cleaned_text
    
    def _extract_metadata(self, html_content: str, url: str) -> Dict:
        """Extract metadata from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            metadata = {}
            
            # Title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.text.strip()
            
            # Try to find published date
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publishdate"]',
                'meta[name="date"]',
                'time[datetime]',
                '.date', '.published', '.publish-date'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_value = date_elem.get('content') or date_elem.get('datetime') or date_elem.text
                    if date_value:
                        metadata['published_at'] = date_value.strip()
                        break
            
            # Try to find author
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                '.author', '.byline', '.by-author'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author_value = author_elem.get('content') or author_elem.text
                    if author_value:
                        metadata['author'] = author_value.strip()
                        break
            
            return metadata
            
        except Exception:
            return {"title": ""}
    
    def _determine_source_type(self, url: str) -> str:
        """Determine the type of source based on URL"""
        try:
            domain = urlparse(url).netloc.lower()
            
            if any(news_domain in domain for news_domain in [
                'reuters', 'bloomberg', 'wsj', 'ft.com', 'bbc', 'cnn', 'news',
                'times', 'post', 'guardian', 'telegraph', 'economist'
            ]):
                return "news"
            
            if any(gov_domain in domain for gov_domain in [
                '.gov', '.mil', 'treasury', 'sec.gov', 'ofac', 'europa.eu'
            ]):
                return "government"
            
            if 'linkedin.com' in domain:
                return "linkedin"
            
            if any(social_domain in domain for social_domain in [
                'twitter', 'facebook', 'instagram', 'youtube'
            ]):
                return "social"
            
            if any(registry_term in domain for registry_term in [
                'registry', 'filing', 'companies', 'business'
            ]):
                return "registry"
            
            return "web"
            
        except Exception:
            return "unknown"
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()


class ExtractionService:
    """Main extraction service coordinating robots checking and content extraction"""
    
    def __init__(self):
        self.robots_checker = RobotsChecker()
        self.content_extractor = ContentExtractor()
        self.processed_urls = set()
    
    async def extract_multiple(self, search_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Extract content from multiple search results grouped by intent
        
        Args:
            search_results: Dict with intent buckets containing search results
            
        Returns:
            Dict with same buckets containing extracted content
        """
        try:
            extracted_results = {}
            all_urls = set()
            
            print(f"📊 Starting extraction for {len(search_results)} intent buckets...")
            
            # Collect all unique URLs first
            for bucket, results in search_results.items():
                for result in results:
                    url = result.get('url', '')
                    if url and url not in all_urls and url not in self.processed_urls:
                        all_urls.add(url)
            
            print(f"🔍 Found {len(all_urls)} unique URLs to extract")
            
            # Check robots.txt for all URLs (batch operation)
            allowed_urls = []
            for url in all_urls:
                if await self.robots_checker.can_fetch(url):
                    allowed_urls.append(url)
                else:
                    print(f"🚫 Robots.txt blocks: {url}")
            
            print(f"✅ {len(allowed_urls)} URLs allowed by robots.txt")
            
            # Extract content from allowed URLs
            extraction_tasks = []
            for url in allowed_urls[:30]:  # Limit to 30 URLs to avoid overload
                task = asyncio.create_task(self.content_extractor.extract_content(url))
                extraction_tasks.append((url, task))
            
            # Wait for all extractions to complete
            url_to_content = {}
            for url, task in extraction_tasks:
                try:
                    content = await task
                    if content.get('extraction_success'):
                        url_to_content[url] = content
                        self.processed_urls.add(url)
                except Exception as e:
                    print(f"❌ Extraction failed for {url}: {e}")
            
            # Group extracted content back into buckets
            for bucket, results in search_results.items():
                bucket_extractions = []
                
                for result in results:
                    url = result.get('url', '')
                    if url in url_to_content:
                        extracted_content = url_to_content[url]
                        
                        # Merge search result with extracted content
                        merged_result = {
                            **result,  # Original search result
                            **extracted_content,  # Extracted content
                            'original_snippet': result.get('snippet', '')
                        }
                        bucket_extractions.append(merged_result)
                
                extracted_results[bucket] = bucket_extractions
                print(f"📄 {bucket}: {len(bucket_extractions)} successful extractions")
            
            return extracted_results
            
        except Exception as e:
            print(f"❌ Multi-extraction failed: {e}")
            return search_results  # Return original results on failure
    
    def deduplicate_by_content(self, extracted_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Remove duplicate content based on content hash"""
        try:
            seen_hashes = set()
            deduplicated_results = {}
            
            for bucket, results in extracted_results.items():
                unique_results = []
                
                for result in results:
                    content_hash = result.get('content_hash', '')
                    if content_hash and content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        unique_results.append(result)
                    elif not content_hash:  # Keep results without hash
                        unique_results.append(result)
                
                deduplicated_results[bucket] = unique_results
                print(f"🔄 {bucket}: {len(unique_results)} after deduplication")
            
            return deduplicated_results
            
        except Exception as e:
            print(f"❌ Deduplication failed: {e}")
            return extracted_results
    
    def get_best_snippets(self, extracted_results: Dict[str, List[Dict]], max_per_bucket: int = 3) -> List[Dict]:
        """Get the best content snippets for GPT-5 analysis"""
        try:
            best_snippets = []
            
            for bucket, results in extracted_results.items():
                # Sort by content length and quality
                sorted_results = sorted(
                    results,
                    key=lambda x: (
                        x.get('content_length', 0),
                        1 if x.get('extraction_success', False) else 0,
                        -len(x.get('url', ''))  # Prefer shorter URLs (often more authoritative)
                    ),
                    reverse=True
                )
                
                # Take the best results from this bucket
                bucket_snippets = sorted_results[:max_per_bucket]
                
                for snippet in bucket_snippets:
                    if snippet.get('content_length', 0) > 100:  # Only include substantial content
                        best_snippets.append({
                            'url': snippet.get('url', ''),
                            'title': snippet.get('title', ''),
                            'text': snippet.get('text', ''),
                            'source_type': snippet.get('source_type', 'web'),
                            'bucket': bucket,
                            'content_length': snippet.get('content_length', 0)
                        })
            
            # Final sorting and limiting
            best_snippets.sort(
                key=lambda x: (x.get('content_length', 0), x.get('source_type') == 'news'),
                reverse=True
            )
            
            final_snippets = best_snippets[:20]  # Limit to top 20 for GPT-5
            
            print(f"📝 Selected {len(final_snippets)} best snippets for analysis")
            return final_snippets
            
        except Exception as e:
            print(f"❌ Snippet selection failed: {e}")
            return []
    
    async def close(self):
        """Close all resources"""
        await self.content_extractor.close()


# Global extraction service instance
extraction_service = ExtractionService()