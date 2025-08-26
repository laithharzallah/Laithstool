"""
Web crawling and content extraction service for Company Screener.
Respects robots.txt and implements polite crawling with rate limits.
"""
import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from schemas.report import SourceReference, ConfidenceLevel

logger = logging.getLogger(__name__)


class PoliteHttpClient:
    """HTTP client that respects robots.txt and implements rate limiting"""
    
    def __init__(self, delay_seconds: float = 1.0, max_concurrent: int = 3):
        self.delay_seconds = delay_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.last_request_time = {}
        self.robots_cache = {}
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Company-Screener-Bot/1.0 (Due Diligence Research; +https://company-screener.com/robots)'
            }
        )
    
    async def can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL according to robots.txt"""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            if base_url not in self.robots_cache:
                try:
                    robots_url = urljoin(base_url, '/robots.txt')
                    response = await self.client.get(robots_url, timeout=10.0)
                    
                    rp = RobotFileParser()
                    rp.set_url(robots_url)
                    if response.status_code == 200:
                        rp.read_string(response.text)
                    self.robots_cache[base_url] = rp
                except Exception as e:
                    logger.warning(f"Could not fetch robots.txt for {base_url}: {e}")
                    # If we can't fetch robots.txt, assume we can crawl
                    rp = RobotFileParser()
                    rp.set_url(urljoin(base_url, '/robots.txt'))
                    self.robots_cache[base_url] = rp
            
            rp = self.robots_cache[base_url]
            user_agent = self.client.headers.get('User-Agent', '*')
            return rp.can_fetch(user_agent, url)
        
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if check fails
    
    async def fetch_with_rate_limit(self, url: str) -> Optional[httpx.Response]:
        """Fetch URL with rate limiting and politeness"""
        async with self.semaphore:
            try:
                # Check robots.txt
                if not await self.can_fetch(url):
                    logger.info(f"Robots.txt disallows fetching {url}")
                    return None
                
                # Implement per-domain rate limiting
                domain = urlparse(url).netloc
                now = asyncio.get_event_loop().time()
                
                if domain in self.last_request_time:
                    time_since_last = now - self.last_request_time[domain]
                    if time_since_last < self.delay_seconds:
                        sleep_time = self.delay_seconds - time_since_last
                        await asyncio.sleep(sleep_time)
                
                self.last_request_time[domain] = asyncio.get_event_loop().time()
                
                response = await self.client.get(url, follow_redirects=True)
                return response
                
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class ContentExtractor:
    """Extract and clean content from HTML pages"""
    
    @staticmethod
    def extract_with_trafilatura(html: str, url: str) -> Optional[Dict[str, str]]:
        """Extract content using trafilatura (primary method)"""
        try:
            extracted_text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                favor_precision=True,
                url=url
            )
            
            if extracted_text:
                # Extract metadata
                metadata = trafilatura.extract_metadata(html, fast=True)
                
                return {
                    'text': extracted_text,
                    'title': metadata.title if metadata else '',
                    'author': metadata.author if metadata else '',
                    'date': metadata.date if metadata else '',
                    'description': metadata.description if metadata else '',
                    'method': 'trafilatura'
                }
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed for {url}: {e}")
        
        return None
    
    @staticmethod
    def extract_with_readability(html: str, url: str) -> Optional[Dict[str, str]]:
        """Extract content using readability (fallback method)"""
        try:
            doc = Document(html)
            
            # Parse with BeautifulSoup for additional metadata
            soup = BeautifulSoup(html, 'html.parser')
            
            title = doc.title() or ''
            if not title and soup.title:
                title = soup.title.get_text().strip()
            
            # Extract meta description
            description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            return {
                'text': doc.summary(),
                'title': title,
                'author': '',
                'date': '',
                'description': description,
                'method': 'readability'
            }
        except Exception as e:
            logger.warning(f"Readability extraction failed for {url}: {e}")
        
        return None
    
    @staticmethod
    def extract_structured_data(html: str) -> Dict[str, any]:
        """Extract structured data (JSON-LD, microdata, etc.)"""
        structured_data = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract JSON-LD
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            json_ld_data = []
            
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    json_ld_data.append(data)
                except:
                    continue
            
            if json_ld_data:
                structured_data['json_ld'] = json_ld_data
            
            # Extract contact information
            contact_info = ContentExtractor.extract_contact_info(soup)
            if contact_info:
                structured_data['contact'] = contact_info
            
            # Extract social media links
            social_links = ContentExtractor.extract_social_links(soup)
            if social_links:
                structured_data['social'] = social_links
                
        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")
        
        return structured_data
    
    @staticmethod
    def extract_contact_info(soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract contact information from HTML"""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': []
        }
        
        text_content = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        contact_info['emails'] = list(set(emails))[:10]  # Limit and deduplicate
        
        # Extract phone numbers (basic patterns)
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?([0-9]{1,3})[-.\s]?([0-9]{3,4})[-.\s]?([0-9]{3,4})[-.\s]?([0-9]{3,4})'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = match
                if len(phone) >= 10:  # Minimum reasonable phone length
                    phones.append(phone)
        
        contact_info['phones'] = list(set(phones))[:5]
        
        return contact_info
    
    @staticmethod
    def extract_social_links(soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        social_links = {}
        
        social_patterns = {
            'linkedin': r'linkedin\.com/(?:company/|in/)[^/\s"]+',
            'twitter': r'twitter\.com/[^/\s"]+',
            'facebook': r'facebook\.com/[^/\s"]+',
            'instagram': r'instagram\.com/[^/\s"]+',
            'youtube': r'youtube\.com/(?:channel/|user/|c/)[^/\s"]+',
        }
        
        # Check all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    if platform not in social_links:  # Take first match only
                        social_links[platform] = href
        
        return social_links


class CrawlService:
    """Main crawling service"""
    
    def __init__(self, max_pages_per_domain: int = 5, max_total_pages: int = 20):
        self.max_pages_per_domain = max_pages_per_domain
        self.max_total_pages = max_total_pages
        self.http_client = PoliteHttpClient()
        self.content_extractor = ContentExtractor()
        self.crawled_urls = set()
        self.content_hashes = set()
    
    def create_content_hash(self, content: str) -> str:
        """Create hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def crawl_url(self, url: str) -> Optional[Dict[str, any]]:
        """Crawl a single URL and extract content"""
        if url in self.crawled_urls:
            logger.info(f"URL already crawled: {url}")
            return None
        
        self.crawled_urls.add(url)
        
        try:
            response = await self.http_client.fetch_with_rate_limit(url)
            if not response or response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code if response else 'No response'}")
                return None
            
            html = response.text
            
            # Extract content using primary method
            content_data = self.content_extractor.extract_with_trafilatura(html, url)
            
            # Fallback to readability if trafilatura fails
            if not content_data:
                content_data = self.content_extractor.extract_with_readability(html, url)
            
            if not content_data:
                logger.warning(f"No content extracted from {url}")
                return None
            
            # Check for duplicate content
            content_hash = self.create_content_hash(content_data['text'])
            if content_hash in self.content_hashes:
                logger.info(f"Duplicate content detected for {url}")
                return None
            
            self.content_hashes.add(content_hash)
            
            # Extract structured data
            structured_data = self.content_extractor.extract_structured_data(html)
            
            # Create result
            result = {
                'url': url,
                'title': content_data.get('title', ''),
                'text': content_data['text'],
                'description': content_data.get('description', ''),
                'author': content_data.get('author', ''),
                'date_published': content_data.get('date', ''),
                'extraction_method': content_data.get('method', ''),
                'content_hash': content_hash,
                'structured_data': structured_data,
                'crawled_at': datetime.utcnow(),
                'word_count': len(content_data['text'].split()),
                'domain': urlparse(url).netloc
            }
            
            logger.info(f"Successfully crawled {url} - {result['word_count']} words")
            return result
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    async def crawl_multiple_urls(self, urls: List[str]) -> List[Dict[str, any]]:
        """Crawl multiple URLs with domain and total limits"""
        if not urls:
            return []
        
        # Group URLs by domain
        domain_urls = {}
        for url in urls:
            domain = urlparse(url).netloc
            if domain not in domain_urls:
                domain_urls[domain] = []
            domain_urls[domain].append(url)
        
        # Limit URLs per domain
        limited_urls = []
        for domain, domain_url_list in domain_urls.items():
            limited_urls.extend(domain_url_list[:self.max_pages_per_domain])
        
        # Apply total limit
        limited_urls = limited_urls[:self.max_total_pages]
        
        logger.info(f"Crawling {len(limited_urls)} URLs across {len(domain_urls)} domains")
        
        # Create crawling tasks
        tasks = []
        for url in limited_urls:
            task = asyncio.create_task(self.crawl_url(url))
            tasks.append(task)
        
        # Execute all crawling tasks
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Crawling task failed: {e}")
        
        logger.info(f"Successfully crawled {len(results)} out of {len(limited_urls)} URLs")
        return results
    
    def create_source_references(self, crawl_results: List[Dict[str, any]]) -> List[SourceReference]:
        """Convert crawl results to SourceReference objects"""
        references = []
        
        for result in crawl_results:
            try:
                ref = SourceReference(
                    url=result['url'],
                    title=result.get('title', ''),
                    domain=result.get('domain', ''),
                    accessed_at=result.get('crawled_at', datetime.utcnow()),
                    confidence=ConfidenceLevel.HIGH,  # High confidence for crawled content
                    content_hash=result.get('content_hash')
                )
                references.append(ref)
            except Exception as e:
                logger.warning(f"Failed to create source reference: {e}")
                continue
        
        return references
    
    async def close(self):
        """Clean up resources"""
        await self.http_client.close()


# Global crawl service instance
crawl_service = CrawlService()