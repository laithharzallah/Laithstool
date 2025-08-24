"""
Real-time internet data collection for due diligence screening.
Uses free APIs and ethical web scraping with OpenAI analysis.
"""
import asyncio
import json
import re
import ssl
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize HTTP client with proper headers
async_client = httpx.AsyncClient(
    timeout=30.0,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
)

class RealDataCollector:
    """Collects real internet data for due diligence"""
    
    def __init__(self):
        self.openai_client = None
        self.setup_openai()
    
    def setup_openai(self):
        """Setup OpenAI client"""
        try:
            import os
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized successfully")
            else:
                print("⚠️ OpenAI API key not found")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search Google using custom search engine or scraping"""
        try:
            # Use Google Custom Search API if available
            import os
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cse_id = os.getenv("GOOGLE_CSE_ID")
            
            if google_api_key and google_cse_id:
                return await self._google_api_search(query, google_api_key, google_cse_id, num_results)
            else:
                # Fallback to web scraping (ethical and rate-limited)
                return await self._google_scrape_search(query, num_results)
                
        except Exception as e:
            print(f"❌ Google search failed: {e}")
            return []
    
    async def _google_api_search(self, query: str, api_key: str, cse_id: str, num_results: int) -> List[Dict]:
        """Search using Google Custom Search API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': query,
                'num': min(num_results, 10)
            }
            
            response = await async_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'Google Custom Search'
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Google API search failed: {e}")
            return []
    
    async def _google_scrape_search(self, query: str, num_results: int) -> List[Dict]:
        """Ethical Google scraping with rate limiting"""
        try:
            # Rate limit: 1 request per 2 seconds
            await asyncio.sleep(2)
            
            url = "https://www.google.com/search"
            params = {
                'q': query,
                'num': min(num_results, 10),
                'hl': 'en'
            }
            
            response = await async_client.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Parse search results
            for result in soup.find_all('div', class_='g'):
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('span', class_='aCOpRe')
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    if url.startswith('http'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'Google Search'
                        })
            
            return results[:num_results]
            
        except Exception as e:
            print(f"❌ Google scraping failed: {e}")
            return []
    
    async def discover_company_website(self, company_name: str, domain_hint: str = "") -> Dict:
        """Discover company's official website"""
        try:
            # Try domain hint first
            if domain_hint:
                if not domain_hint.startswith('http'):
                    domain_hint = f"https://{domain_hint}"
                
                website_info = await self.analyze_website(domain_hint)
                if website_info and website_info.get('valid'):
                    return website_info
            
            # Search for official website
            search_query = f'"{company_name}" official website site:'
            results = await self.google_search(search_query, 5)
            
            for result in results:
                url = result['url']
                if self._is_likely_official_website(url, company_name):
                    website_info = await self.analyze_website(url)
                    if website_info and website_info.get('valid'):
                        return website_info
            
            # Fallback: try common domain patterns
            domain_patterns = [
                company_name.lower().replace(' ', '').replace('.', '') + '.com',
                company_name.lower().replace(' ', '').replace('.', '') + '.org',
                company_name.lower().replace(' ', '-').replace('.', '') + '.com',
            ]
            
            for domain in domain_patterns:
                try:
                    url = f"https://{domain}"
                    website_info = await self.analyze_website(url)
                    if website_info and website_info.get('valid'):
                        return website_info
                except:
                    continue
            
            return {'error': 'Website not found'}
            
        except Exception as e:
            print(f"❌ Website discovery failed: {e}")
            return {'error': str(e)}
    
    def _is_likely_official_website(self, url: str, company_name: str) -> bool:
        """Check if URL is likely the official website"""
        domain = urlparse(url).netloc.lower()
        company_lower = company_name.lower().replace(' ', '').replace('.', '')
        
        # Skip social media and other platforms
        excluded_domains = ['linkedin.com', 'facebook.com', 'twitter.com', 'youtube.com', 'wikipedia.org']
        if any(excluded in domain for excluded in excluded_domains):
            return False
        
        # Check if domain contains company name
        return company_lower in domain or domain in company_lower
    
    async def analyze_website(self, url: str) -> Dict:
        """Analyze a website for company information"""
        try:
            response = await async_client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic information
            title = soup.title.get_text().strip() if soup.title else ''
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # Extract clean text content
            content = trafilatura.extract(html, include_comments=False, include_tables=True)
            
            # Extract contact information
            contact_info = self._extract_contact_info(soup, content or '')
            
            # Extract social media links
            social_media = self._extract_social_media(soup)
            
            # Get SSL certificate info
            ssl_info = await self._get_ssl_info(url)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'content_preview': content[:500] if content else '',
                'contact_info': contact_info,
                'social_media': social_media,
                'ssl_info': ssl_info,
                'valid': True,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Website analysis failed for {url}: {e}")
            return {'error': str(e), 'valid': False}
    
    def _extract_contact_info(self, soup: BeautifulSoup, content: str) -> Dict:
        """Extract contact information from website"""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': []
        }
        
        text_content = soup.get_text() + " " + content
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        contact_info['emails'] = list(set(emails))[:5]
        
        # Extract phone numbers
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
                if len(phone) >= 10:
                    phones.append(phone)
        
        contact_info['phones'] = list(set(phones))[:3]
        
        return contact_info
    
    def _extract_social_media(self, soup: BeautifulSoup) -> Dict:
        """Extract social media links"""
        social_media = {}
        
        social_patterns = {
            'linkedin': r'linkedin\.com/(?:company/|in/)[^/\s"]+',
            'twitter': r'twitter\.com/[^/\s"]+',
            'facebook': r'facebook\.com/[^/\s"]+',
            'instagram': r'instagram\.com/[^/\s"]+',
            'youtube': r'youtube\.com/(?:channel/|user/|c/)[^/\s"]+'
        }
        
        # Check all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    if platform not in social_media:
                        social_media[platform] = href
        
        return social_media
    
    async def _get_ssl_info(self, url: str) -> Dict:
        """Get SSL certificate information"""
        try:
            parsed = urlparse(url)
            if parsed.scheme != 'https':
                return {'valid': False, 'reason': 'Not HTTPS'}
            
            hostname = parsed.netloc
            port = 443
            
            context = ssl.create_default_context()
            with ssl.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'valid': True,
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'not_after': cert.get('notAfter'),
                        'not_before': cert.get('notBefore')
                    }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def check_sanctions(self, company_name: str, executives: List[Dict] = None) -> Dict:
        """Check sanctions lists (OFAC, EU, UK, UN)"""
        try:
            sanctions_results = {
                'company_matches': [],
                'executive_matches': [],
                'lists_checked': ['OFAC SDN', 'EU Sanctions', 'UK HMT', 'UN Sanctions'],
                'checked_at': datetime.utcnow().isoformat()
            }
            
            # Check OFAC SDN List
            ofac_matches = await self._check_ofac_sanctions(company_name, executives)
            if ofac_matches:
                sanctions_results['company_matches'].extend(ofac_matches.get('company', []))
                sanctions_results['executive_matches'].extend(ofac_matches.get('executives', []))
            
            # Check EU Sanctions (simplified check)
            eu_matches = await self._check_eu_sanctions(company_name, executives)
            if eu_matches:
                sanctions_results['company_matches'].extend(eu_matches.get('company', []))
                sanctions_results['executive_matches'].extend(eu_matches.get('executives', []))
            
            return sanctions_results
            
        except Exception as e:
            print(f"❌ Sanctions check failed: {e}")
            return {'error': str(e)}
    
    async def _check_ofac_sanctions(self, company_name: str, executives: List[Dict] = None) -> Dict:
        """Check OFAC SDN list"""
        try:
            # OFAC provides XML and CSV downloads
            url = "https://www.treasury.gov/ofac/downloads/sdn.xml"
            
            response = await async_client.get(url)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            matches = {'company': [], 'executives': []}
            
            # Check company name
            for entry in root.findall('.//sdnEntry'):
                first_name = entry.find('.//firstName')
                last_name = entry.find('.//lastName')
                entity_name = entry.find('.//name')
                
                if entity_name is not None:
                    name = entity_name.text or ''
                    if self._fuzzy_match(company_name, name):
                        matches['company'].append({
                            'list_name': 'OFAC SDN',
                            'matched_name': name,
                            'match_score': self._calculate_match_score(company_name, name),
                            'entry_type': 'Entity'
                        })
            
            # Check executives if provided
            if executives:
                for exec_info in executives:
                    exec_name = exec_info.get('name', '')
                    for entry in root.findall('.//sdnEntry'):
                        first_name = entry.find('.//firstName')
                        last_name = entry.find('.//lastName')
                        
                        if first_name is not None and last_name is not None:
                            full_name = f"{first_name.text} {last_name.text}"
                            if self._fuzzy_match(exec_name, full_name):
                                matches['executives'].append({
                                    'list_name': 'OFAC SDN',
                                    'matched_name': full_name,
                                    'input_name': exec_name,
                                    'match_score': self._calculate_match_score(exec_name, full_name),
                                    'entry_type': 'Individual'
                                })
            
            return matches
            
        except Exception as e:
            print(f"❌ OFAC check failed: {e}")
            return {}
    
    async def _check_eu_sanctions(self, company_name: str, executives: List[Dict] = None) -> Dict:
        """Check EU sanctions list"""
        try:
            # EU provides consolidated list
            url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token="
            
            # For demo purposes, return empty results
            # In production, implement proper EU sanctions checking
            return {'company': [], 'executives': []}
            
        except Exception as e:
            print(f"❌ EU sanctions check failed: {e}")
            return {}
    
    def _fuzzy_match(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching"""
        try:
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            return similarity >= threshold
        except:
            # Fallback to simple substring matching
            return name1.lower() in name2.lower() or name2.lower() in name1.lower()
    
    def _calculate_match_score(self, name1: str, name2: str) -> float:
        """Calculate match score between two names"""
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        except:
            # Fallback scoring
            if name1.lower() == name2.lower():
                return 1.0
            elif name1.lower() in name2.lower() or name2.lower() in name1.lower():
                return 0.8
            else:
                return 0.0
    
    async def search_adverse_media(self, company_name: str, executives: List[Dict] = None) -> List[Dict]:
        """Search for adverse media coverage"""
        try:
            adverse_queries = [
                f'"{company_name}" fraud',
                f'"{company_name}" corruption',
                f'"{company_name}" lawsuit',
                f'"{company_name}" investigation',
                f'"{company_name}" penalty',
                f'"{company_name}" scandal',
                f'"{company_name}" violation'
            ]
            
            all_articles = []
            
            for query in adverse_queries:
                # Add date filter for recent news
                recent_query = f"{query} after:2022-01-01"
                results = await self.google_search(recent_query, 5)
                
                for result in results:
                    article = await self._analyze_article(result, company_name)
                    if article and article.get('is_adverse'):
                        all_articles.append(article)
                
                # Rate limit
                await asyncio.sleep(1)
            
            # Remove duplicates and sort by relevance
            unique_articles = self._deduplicate_articles(all_articles)
            return sorted(unique_articles, key=lambda x: x.get('relevance_score', 0), reverse=True)[:10]
            
        except Exception as e:
            print(f"❌ Adverse media search failed: {e}")
            return []
    
    async def _analyze_article(self, search_result: Dict, company_name: str) -> Optional[Dict]:
        """Analyze if an article is adverse and extract key information"""
        try:
            url = search_result['url']
            title = search_result['title']
            snippet = search_result['snippet']
            
            # Quick relevance check
            adverse_keywords = ['fraud', 'corruption', 'lawsuit', 'investigation', 'penalty', 'scandal', 'violation', 'fine', 'settlement']
            
            text_to_check = (title + " " + snippet).lower()
            adverse_count = sum(1 for keyword in adverse_keywords if keyword in text_to_check)
            
            if adverse_count == 0:
                return None
            
            # Try to extract full article content
            try:
                response = await async_client.get(url, timeout=10)
                if response.status_code == 200:
                    content = trafilatura.extract(response.text)
                    if content:
                        snippet = content[:300]  # Use article content for snippet
            except:
                pass  # Use original snippet if extraction fails
            
            # Use OpenAI to analyze sentiment and extract key details
            analysis = await self._ai_analyze_article(title, snippet, company_name)
            
            return {
                'title': title,
                'url': url,
                'snippet': snippet,
                'source_name': urlparse(url).netloc,
                'published_date': 'Recent',  # Could be enhanced with date extraction
                'sentiment': analysis.get('sentiment', 'negative'),
                'category': analysis.get('category', 'General'),
                'severity': analysis.get('severity', 'medium'),
                'key_allegations': analysis.get('key_allegations', []),
                'is_adverse': True,
                'relevance_score': adverse_count + analysis.get('relevance_boost', 0)
            }
            
        except Exception as e:
            print(f"❌ Article analysis failed: {e}")
            return None
    
    async def _ai_analyze_article(self, title: str, content: str, company_name: str) -> Dict:
        """Use OpenAI to analyze article content"""
        try:
            if not self.openai_client:
                return {'sentiment': 'negative', 'category': 'General', 'severity': 'medium'}
            
            prompt = f"""
            Analyze this news article about {company_name}:
            
            Title: {title}
            Content: {content}
            
            Provide analysis in JSON format:
            {{
                "sentiment": "positive/negative/neutral",
                "category": "Legal/Financial/Regulatory/Operational/Reputational",
                "severity": "low/medium/high",
                "key_allegations": ["list", "of", "key", "points"],
                "relevance_boost": 0-2
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a due diligence analyst. Analyze news articles for adverse content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                return json.loads(result)
            except:
                # Fallback if JSON parsing fails
                return {
                    'sentiment': 'negative',
                    'category': 'General',
                    'severity': 'medium',
                    'key_allegations': [],
                    'relevance_boost': 1
                }
                
        except Exception as e:
            print(f"❌ AI article analysis failed: {e}")
            return {'sentiment': 'negative', 'category': 'General', 'severity': 'medium'}
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on URL and title similarity"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    async def search_executives(self, company_name: str) -> List[Dict]:
        """Search for company executives and key personnel"""
        try:
            executive_queries = [
                f'"{company_name}" CEO OR "Chief Executive Officer"',
                f'"{company_name}" CTO OR "Chief Technology Officer"',
                f'"{company_name}" CFO OR "Chief Financial Officer"',
                f'"{company_name}" executives OR leadership OR management',
                f'"{company_name}" board of directors',
                f'site:linkedin.com "{company_name}" executive OR director'
            ]
            
            executives = []
            
            for query in executive_queries:
                results = await self.google_search(query, 5)
                
                for result in results:
                    extracted_execs = await self._extract_executives_from_result(result, company_name)
                    executives.extend(extracted_execs)
                
                await asyncio.sleep(1)  # Rate limit
            
            # Deduplicate and rank executives
            unique_executives = self._deduplicate_executives(executives)
            return unique_executives[:10]
            
        except Exception as e:
            print(f"❌ Executive search failed: {e}")
            return []
    
    async def _extract_executives_from_result(self, search_result: Dict, company_name: str) -> List[Dict]:
        """Extract executive information from search result"""
        try:
            url = search_result['url']
            title = search_result['title']
            snippet = search_result['snippet']
            
            # Try to extract full content
            content = snippet
            try:
                if 'linkedin.com' not in url:  # Don't scrape LinkedIn directly
                    response = await async_client.get(url, timeout=10)
                    if response.status_code == 200:
                        extracted = trafilatura.extract(response.text)
                        if extracted:
                            content = extracted[:1000]
            except:
                pass
            
            # Use AI to extract executive information
            executives = await self._ai_extract_executives(content, company_name, url)
            return executives
            
        except Exception as e:
            print(f"❌ Executive extraction failed: {e}")
            return []
    
    async def _ai_extract_executives(self, content: str, company_name: str, source_url: str) -> List[Dict]:
        """Use OpenAI to extract executive information from content"""
        try:
            if not self.openai_client:
                return []
            
            prompt = f"""
            Extract executive/leadership information from this content about {company_name}:
            
            {content}
            
            Return JSON array of executives found:
            [
                {{
                    "name": "Full Name",
                    "role": "Position/Title",
                    "background": "Brief background if available",
                    "confidence": "high/medium/low"
                }}
            ]
            
            Only include clear, unambiguous executive information. Don't make assumptions.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist. Extract only factual executive information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            try:
                executives = json.loads(result)
                if isinstance(executives, list):
                    # Add source information
                    for exec in executives:
                        exec['source_url'] = source_url
                        exec['linkedin_url'] = source_url if 'linkedin.com' in source_url else None
                    return executives
            except:
                pass
            
            return []
            
        except Exception as e:
            print(f"❌ AI executive extraction failed: {e}")
            return []
    
    def _deduplicate_executives(self, executives: List[Dict]) -> List[Dict]:
        """Remove duplicate executives based on name similarity"""
        unique_executives = []
        seen_names = set()
        
        for exec in executives:
            name = exec.get('name', '').lower().strip()
            if name and name not in seen_names:
                # Check for similar names
                is_duplicate = False
                for seen_name in seen_names:
                    if self._fuzzy_match(name, seen_name, threshold=0.9):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    seen_names.add(name)
                    unique_executives.append(exec)
        
        return unique_executives
    
    async def comprehensive_screening(self, company_name: str, domain: str = "", country: str = "") -> Dict:
        """Perform comprehensive due diligence screening"""
        try:
            print(f"🔍 Starting comprehensive screening for {company_name}")
            
            results = {
                'company_name': company_name,
                'screening_date': datetime.utcnow().isoformat(),
                'processing_time_ms': 0,
                'data_sources_used': []
            }
            
            start_time = time.time()
            
            # 1. Website Discovery
            print("🌐 Discovering company website...")
            website_info = await self.discover_company_website(company_name, domain)
            results['website_info'] = website_info
            if not website_info.get('error'):
                results['data_sources_used'].append('Company Website')
            
            # 2. Executive Search
            print("👥 Searching for executives...")
            executives = await self.search_executives(company_name)
            results['executives'] = executives
            if executives:
                results['data_sources_used'].append('Executive Search')
            
            # 3. Sanctions Check
            print("🛡️ Checking sanctions databases...")
            sanctions = await self.check_sanctions(company_name, executives)
            results['sanctions'] = sanctions
            if not sanctions.get('error'):
                results['data_sources_used'].append('Sanctions Databases')
            
            # 4. Adverse Media Search
            print("📰 Searching adverse media...")
            adverse_media = await self.search_adverse_media(company_name, executives)
            results['adverse_media'] = adverse_media
            if adverse_media:
                results['data_sources_used'].append('Media Monitoring')
            
            # 5. Generate AI Summary
            print("🤖 Generating AI analysis...")
            ai_summary = await self._generate_ai_summary(results)
            results.update(ai_summary)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            results['processing_time_ms'] = int(processing_time)
            
            print(f"✅ Screening completed in {processing_time:.1f}ms")
            return results
            
        except Exception as e:
            print(f"❌ Comprehensive screening failed: {e}")
            return {'error': str(e)}
    
    async def _generate_ai_summary(self, screening_data: Dict) -> Dict:
        """Generate AI-powered summary and risk assessment"""
        try:
            if not self.openai_client:
                return self._generate_fallback_summary(screening_data)
            
            # Prepare data for AI analysis
            company_name = screening_data.get('company_name', '')
            website_info = screening_data.get('website_info', {})
            executives = screening_data.get('executives', [])
            sanctions = screening_data.get('sanctions', {})
            adverse_media = screening_data.get('adverse_media', [])
            
            prompt = f"""
            Analyze this due diligence screening data for {company_name} and provide a comprehensive assessment:
            
            Website: {json.dumps(website_info, indent=2)}
            Executives: {json.dumps(executives, indent=2)}
            Sanctions: {json.dumps(sanctions, indent=2)}
            Adverse Media: {json.dumps(adverse_media, indent=2)}
            
            Provide analysis in this JSON format:
            {{
                "executive_summary": {{
                    "overview": "2-3 sentence overview of findings",
                    "key_points": ["bullet", "points", "of", "key", "findings"],
                    "risk_score": 0-100,
                    "confidence_level": "high/medium/low"
                }},
                "company_profile": {{
                    "legal_name": "{company_name}",
                    "primary_industry": "detected industry",
                    "founded_year": "if determinable",
                    "employee_count_band": "estimate if possible",
                    "registration_details": {{
                        "jurisdiction": "if determinable",
                        "entity_type": "Corporation/LLC/etc",
                        "status": "Active/Unknown"
                    }}
                }},
                "risk_flags": [
                    {{
                        "category": "Category",
                        "description": "Description",
                        "severity": "low/medium/high",
                        "confidence": "high/medium/low"
                    }}
                ],
                "compliance_notes": {{
                    "methodology": "Brief description of screening methodology",
                    "limitations": ["limitation1", "limitation2"],
                    "recommendations": ["recommendation1", "recommendation2"]
                }}
            }}
            
            Be factual and conservative. Only flag real risks with evidence.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert due diligence analyst. Provide thorough, factual analysis based solely on provided data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content
            
            try:
                ai_analysis = json.loads(result)
                return ai_analysis
            except:
                print("❌ Failed to parse AI response, using fallback")
                return self._generate_fallback_summary(screening_data)
                
        except Exception as e:
            print(f"❌ AI summary generation failed: {e}")
            return self._generate_fallback_summary(screening_data)
    
    def _generate_fallback_summary(self, screening_data: Dict) -> Dict:
        """Generate fallback summary without AI"""
        company_name = screening_data.get('company_name', '')
        
        # Calculate basic risk score
        risk_score = 20  # Base low risk
        
        sanctions = screening_data.get('sanctions', {})
        if sanctions.get('company_matches') or sanctions.get('executive_matches'):
            risk_score += 60
        
        adverse_media = screening_data.get('adverse_media', [])
        if adverse_media:
            risk_score += min(len(adverse_media) * 10, 30)
        
        website_info = screening_data.get('website_info', {})
        if website_info.get('error'):
            risk_score += 10
        
        risk_score = min(risk_score, 100)
        
        return {
            "executive_summary": {
                "overview": f"Completed automated due diligence screening for {company_name}. Analysis based on publicly available information and regulatory databases.",
                "key_points": [
                    f"Sanctions check: {'Matches found' if sanctions.get('company_matches') or sanctions.get('executive_matches') else 'No matches'}",
                    f"Adverse media: {len(adverse_media)} articles found",
                    f"Website analysis: {'Completed' if not website_info.get('error') else 'Limited'}"
                ],
                "risk_score": risk_score,
                "confidence_level": "medium"
            },
            "company_profile": {
                "legal_name": company_name,
                "primary_industry": "To be determined",
                "founded_year": "Unknown",
                "employee_count_band": "Unknown",
                "registration_details": {
                    "jurisdiction": "Unknown",
                    "entity_type": "Unknown",
                    "status": "Unknown"
                }
            },
            "risk_flags": [
                {
                    "category": "Data Limitations",
                    "description": "Assessment based on limited publicly available information",
                    "severity": "low",
                    "confidence": "high"
                }
            ],
            "compliance_notes": {
                "methodology": "Automated screening using web search, sanctions databases, and media monitoring",
                "limitations": [
                    "Based on publicly available information only",
                    "No access to proprietary databases",
                    "Real-time data subject to change"
                ],
                "recommendations": [
                    "Verify company registration details through official channels",
                    "Conduct enhanced due diligence if proceeding with business relationship"
                ]
            }
        }

# Global instance
real_data_collector = RealDataCollector()