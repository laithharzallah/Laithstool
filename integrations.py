import os, requests, json, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yfinance as yf
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin
import random

load_dotenv()

NEWS_API_KEY   = os.getenv("NEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

# User agents for web scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def get_random_headers():
    """Get random headers for web scraping"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def search_serper(query, num=10):
    """Enhanced Serper search with better error handling"""
    if not SERPER_API_KEY:
        print("WARNING: SERPER_API_KEY not found")
        return {"error":"SERPER_API_KEY missing"}
    
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type":"application/json"}
    payload = {"q": query, "num": num, "gl": "us", "hl": "en"}
    
    try:
        print(f"Searching Serper for: {query}")
        response = requests.post("https://google.serper.dev/search", 
                               headers=headers, json=payload, timeout=20)
        result = response.json()
        print(f"Serper response status: {response.status_code}")
        return result
    except Exception as e:
        print(f"Serper search error: {str(e)}")
        return {"error": f"Serper search failed: {str(e)}"}

def search_newsapi(query, page_size=10, language="en"):
    """Enhanced NewsAPI search"""
    if not NEWS_API_KEY:
        print("WARNING: NEWS_API_KEY not found")
        return {"error":"NEWS_API_KEY missing"}
    
    # Search for last 30 days
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    params = {
        "q": query, 
        "pageSize": page_size, 
        "language": language, 
        "sortBy": "relevancy",
        "from": from_date,
        "apiKey": NEWS_API_KEY
    }
    
    try:
        print(f"Searching NewsAPI for: {query}")
        response = requests.get("https://newsapi.org/v2/everything", 
                              params=params, timeout=20)
        result = response.json()
        print(f"NewsAPI response status: {response.status_code}")
        return result
    except Exception as e:
        print(f"NewsAPI search error: {str(e)}")
        return {"error": f"NewsAPI search failed: {str(e)}"}

def search_linkedin_executives(company_name: str) -> List[Dict]:
    """Search for company executives on LinkedIn using Google search"""
    try:
        executives = []
        
        # LinkedIn search queries
        linkedin_queries = [
            f'site:linkedin.com/in "{company_name}" CEO',
            f'site:linkedin.com/in "{company_name}" CFO',
            f'site:linkedin.com/in "{company_name}" CTO',
            f'site:linkedin.com/in "{company_name}" President',
            f'site:linkedin.com/in "{company_name}" Executive',
            f'site:linkedin.com/in "{company_name}" Director',
            f'site:linkedin.com/in "{company_name}" VP'
        ]
        
        for query in linkedin_queries[:4]:  # Limit queries to avoid rate limits
            search_results = search_serper(query, num=10)
            
            if "organic" in search_results:
                for result in search_results["organic"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    url = result.get("link", "")
                    
                    # Extract executive information from LinkedIn profiles
                    if "linkedin.com/in/" in url:
                        # Extract name from title (usually "FirstName LastName - Position at Company")
                        name_match = re.search(r'^([A-Z][a-z]+ [A-Z][a-z]+)', title)
                        if name_match:
                            name = name_match.group(1)
                            
                            # Extract position
                            position = "Executive"
                            if "CEO" in title.upper() or "Chief Executive" in title:
                                position = "CEO"
                            elif "CFO" in title.upper() or "Chief Financial" in title:
                                position = "CFO"
                            elif "CTO" in title.upper() or "Chief Technology" in title:
                                position = "CTO"
                            elif "President" in title:
                                position = "President"
                            elif "VP" in title or "Vice President" in title:
                                position = "Vice President"
                            elif "Director" in title:
                                position = "Director"
                            
                            executive = {
                                "name": name,
                                "position": position,
                                "background": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                                "source": url,
                                "linkedin_profile": url
                            }
                            
                            # Avoid duplicates
                            if not any(exec["name"] == executive["name"] for exec in executives):
                                executives.append(executive)
            
            time.sleep(1)  # Rate limiting
        
        print(f"Found {len(executives)} LinkedIn executives for {company_name}")
        return executives[:10]  # Return top 10
    
    except Exception as e:
        print(f"LinkedIn search error: {str(e)}")
        return []

def check_sanctions_databases(company_name: str, executives: List[Dict]) -> Dict:
    """Check company and executives against sanctions databases"""
    try:
        sanctions_results = {
            "company_sanctions": [],
            "executive_sanctions": [],
            "databases_checked": []
        }
        
        # Sanctions databases to check
        sanctions_queries = [
            f'"{company_name}" site:treasury.gov sanctions',
            f'"{company_name}" site:ofac.treasury.gov',
            f'"{company_name}" site:export.gov denied persons',
            f'"{company_name}" OFAC SDN sanctions',
            f'"{company_name}" EU sanctions list',
            f'"{company_name}" UN sanctions',
            f'"{company_name}" BIS denied persons list'
        ]
        
        # Check company sanctions
        for query in sanctions_queries[:4]:  # Limit to avoid rate limits
            search_results = search_serper(query, num=5)
            
            if "organic" in search_results:
                for result in search_results["organic"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    url = result.get("link", "")
                    
                    # Check if this is a real sanctions hit
                    sanctions_keywords = ["sanctions", "denied", "blocked", "restricted", "OFAC", "SDN"]
                    if any(keyword.lower() in title.lower() or keyword.lower() in snippet.lower() 
                           for keyword in sanctions_keywords):
                        
                        sanctions_results["company_sanctions"].append({
                            "title": title,
                            "summary": snippet,
                            "source": url,
                            "severity": "High" if any(high in snippet.lower() for high in ["blocked", "denied", "SDN"]) else "Medium"
                        })
            
            time.sleep(0.5)
        
        # Check executives against sanctions
        for executive in executives[:5]:  # Check top 5 executives
            exec_name = executive.get("name", "")
            if exec_name:
                exec_sanctions_query = f'"{exec_name}" OFAC sanctions SDN'
                search_results = search_serper(exec_sanctions_query, num=3)
                
                if "organic" in search_results:
                    for result in search_results["organic"]:
                        title = result.get("title", "")
                        snippet = result.get("snippet", "")
                        url = result.get("link", "")
                        
                        if any(keyword in snippet.lower() for keyword in ["sanctions", "ofac", "sdn", "denied"]):
                            sanctions_results["executive_sanctions"].append({
                                "executive_name": exec_name,
                                "title": title,
                                "summary": snippet,
                                "source": url,
                                "severity": "High"
                            })
                
                time.sleep(0.3)
        
        sanctions_results["databases_checked"] = [
            "OFAC SDN List", "Treasury.gov", "BIS Denied Persons", "EU Sanctions", "UN Sanctions"
        ]
        
        print(f"Sanctions check completed: {len(sanctions_results['company_sanctions'])} company hits, {len(sanctions_results['executive_sanctions'])} executive hits")
        return sanctions_results
    
    except Exception as e:
        print(f"Sanctions check error: {str(e)}")
        return {"company_sanctions": [], "executive_sanctions": [], "databases_checked": [], "error": str(e)}

def scrape_company_website_details(url: str) -> Dict:
    """Scrape additional details from company website"""
    try:
        headers = get_random_headers()
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract meta information
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            # Look for company information
            company_info = {
                "description": description,
                "title": soup.title.string if soup.title else "",
                "contact_info": [],
                "social_media": []
            }
            
            # Find contact information
            text_content = soup.get_text().lower()
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text_content)
            company_info["contact_info"] = list(set(emails))[:5]  # Top 5 unique emails
            
            # Find social media links
            social_patterns = {
                "linkedin": r'linkedin\.com/company/[^"\s]+',
                "twitter": r'twitter\.com/[^"\s]+',
                "facebook": r'facebook\.com/[^"\s]+'
            }
            
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, str(soup))
                if matches:
                    company_info["social_media"].append({
                        "platform": platform,
                        "url": f"https://{matches[0]}" if not matches[0].startswith('http') else matches[0]
                    })
            
            return company_info
        
    except Exception as e:
        print(f"Website scraping error: {str(e)}")
    
    return {"description": "", "title": "", "contact_info": [], "social_media": []}

def search_company_website(company_name: str) -> Dict:
    """Search for company's official website and extract information"""
    try:
        # First try to find official website
        search_query = f"{company_name} official website"
        search_results = search_serper(search_query, num=5)
        
        if "error" in search_results:
            # Fallback: try basic search
            search_query = f"{company_name}"
            search_results = search_serper(search_query, num=5)
        
        website_info = {"official_website": "Not found", "title": "No information available", "status": "Not found", "source": "Web search"}
        
        # Look for official website in search results
        if "organic" in search_results and search_results["organic"]:
            for result in search_results["organic"][:5]:
                url = result.get("link", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                # Check if this looks like an official website
                company_lower = company_name.lower().replace(" ", "").replace("inc", "").replace("ltd", "").replace("llc", "")
                
                if url and (company_lower in url.lower() or 
                           any(indicator in title.lower() for indicator in ['official', company_name.lower()]) or
                           any(indicator in snippet.lower() for indicator in ['official', 'company'])):
                    website_info["official_website"] = url
                    website_info["title"] = title
                    website_info["status"] = "Found"
                    
                    # Scrape additional details from the website
                    website_details = scrape_company_website_details(url)
                    website_info.update(website_details)
                    break
            
            # If no official site found, take the first relevant result
            if website_info["status"] == "Not found" and search_results["organic"]:
                first_result = search_results["organic"][0]
                website_info["official_website"] = first_result.get("link", "Not found")
                website_info["title"] = first_result.get("title", "No title available")
                website_info["status"] = "Found (best match)"
        
        print(f"Website search for {company_name}: {website_info['status']}")
        return website_info
    except Exception as e:
        print(f"Website search error: {str(e)}")
        return {"official_website": "Error during search", "title": "Search failed", "status": "Error", "source": "Web search"}

def get_financial_data(company_name: str, ticker: str = None) -> Dict:
    """Get financial data using yfinance and other sources"""
    try:
        financial_data = {"revenue": "Not available", "employees": "Not available", "industry": "Not available", "founded": "Not available"}
        
        # Try to guess ticker symbol from company name
        if not ticker:
            # Common mappings
            ticker_guesses = []
            name_clean = company_name.upper().replace(" INC", "").replace(" CORP", "").replace(" LTD", "").replace(" LLC", "")
            
            # Try different variations
            if "APPLE" in name_clean:
                ticker_guesses = ["AAPL"]
            elif "MICROSOFT" in name_clean:
                ticker_guesses = ["MSFT"]
            elif "GOOGLE" in name_clean or "ALPHABET" in name_clean:
                ticker_guesses = ["GOOGL", "GOOG"]
            elif "AMAZON" in name_clean:
                ticker_guesses = ["AMZN"]
            elif "TESLA" in name_clean:
                ticker_guesses = ["TSLA"]
            elif "META" in name_clean or "FACEBOOK" in name_clean:
                ticker_guesses = ["META"]
            else:
                # Try first word as ticker
                first_word = name_clean.split()[0] if name_clean.split() else ""
                if len(first_word) <= 5:
                    ticker_guesses = [first_word]
        else:
            ticker_guesses = [ticker]
        
        # Try each ticker guess
        for ticker_symbol in ticker_guesses:
            try:
                print(f"Trying ticker: {ticker_symbol}")
                stock = yf.Ticker(ticker_symbol)
                info = stock.info
                
                if info and len(info) > 1:  # Valid data returned
                    financial_data.update({
                        "revenue": format_number(info.get("totalRevenue")) if info.get("totalRevenue") else "Not available",
                        "employees": format_number(info.get("fullTimeEmployees")) if info.get("fullTimeEmployees") else "Not available",
                        "industry": info.get("industry", "Not available"),
                        "sector": info.get("sector", "Not available"),
                        "market_cap": format_number(info.get("marketCap")) if info.get("marketCap") else "Not available",
                        "founded": "Not available"
                    })
                    print(f"Found financial data for {ticker_symbol}")
                    break
            except Exception as e:
                print(f"Error with ticker {ticker_symbol}: {str(e)}")
                continue
        
        return financial_data
    
    except Exception as e:
        print(f"Financial data error: {str(e)}")
        return {"revenue": "Error", "employees": "Error", "industry": "Error", "founded": "Error"}

def format_number(num):
    """Format large numbers in readable format"""
    if not num:
        return "Not available"
    try:
        num = float(num)
        if num >= 1e12:
            return f"${num/1e12:.1f}T"
        elif num >= 1e9:
            return f"${num/1e9:.1f}B"
        elif num >= 1e6:
            return f"${num/1e6:.1f}M"
        elif num >= 1e3:
            return f"${num/1e3:.1f}K"
        else:
            return f"${num:,.0f}"
    except:
        return str(num)

def search_company_executives(company_name: str) -> List[Dict]:
    """Search for company executives using multiple sources including LinkedIn"""
    try:
        executives = []
        
        # Regular search for executives
        exec_queries = [
            f"{company_name} CEO CFO executives",
            f"{company_name} leadership team",
            f"{company_name} management team"
        ]
        
        for query in exec_queries:
            search_results = search_serper(query, num=10)
            
            if "organic" in search_results:
                for result in search_results["organic"][:5]:
                    snippet = result.get("snippet", "")
                    title = result.get("title", "")
                    url = result.get("link", "")
                    
                    # Enhanced executive patterns
                    executive_patterns = [
                        (r'CEO[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "CEO"),
                        (r'Chief Executive Officer[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "CEO"),
                        (r'CFO[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "CFO"),
                        (r'Chief Financial Officer[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "CFO"),
                        (r'President[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "President"),
                        (r'Chairman[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "Chairman"),
                        (r'CTO[:\s,]*([A-Z][a-z]+ [A-Z][a-z]+)', "CTO"),
                        (r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]*CEO', "CEO"),
                        (r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]*CFO', "CFO")
                    ]
                    
                    for pattern, position in executive_patterns:
                        matches = re.findall(pattern, snippet + " " + title)
                        for match in matches:
                            if len(match.split()) == 2:  # Ensure it's a proper name
                                executive = {
                                    "name": match,
                                    "position": position,
                                    "background": f"Executive at {company_name}",
                                    "source": url
                                }
                                
                                # Avoid duplicates
                                if not any(exec["name"] == executive["name"] for exec in executives):
                                    executives.append(executive)
            
            if len(executives) >= 3:  # If we found enough, break
                break
        
        # Add LinkedIn executives
        linkedin_executives = search_linkedin_executives(company_name)
        for linkedin_exec in linkedin_executives:
            # Check if not already in list
            if not any(exec["name"] == linkedin_exec["name"] for exec in executives):
                executives.append(linkedin_exec)
        
        print(f"Found {len(executives)} total executives for {company_name}")
        return executives[:10]  # Return top 10 executives
    
    except Exception as e:
        print(f"Executive search error: {str(e)}")
        return []

def search_adverse_media(company_name: str) -> List[Dict]:
    """Search for adverse media and negative news"""
    try:
        adverse_media = []
        
        # Search for negative news using both APIs
        negative_keywords = ["lawsuit", "investigation", "scandal", "controversy", "fraud", "fine"]
        
        for keyword in negative_keywords[:3]:  # Limit to avoid rate limits
            # Try NewsAPI first
            news_query = f"{company_name} {keyword}"
            news_results = search_newsapi(news_query, page_size=5)
            
            if "articles" in news_results and news_results["articles"]:
                for article in news_results["articles"][:2]:
                    title = article.get("title", "")
                    description = article.get("description", "")
                    url = article.get("url", "")
                    published_at = article.get("publishedAt", "")
                    source = article.get("source", {}).get("name", "Unknown")
                    
                    if title and company_name.lower() in title.lower():
                        severity = determine_severity(title, description, keyword)
                        
                        adverse_item = {
                            "title": title,
                            "summary": description or "No summary available",
                            "severity": severity,
                            "date": published_at.split("T")[0] if published_at else "Unknown",
                            "source": url,
                            "category": categorize_news(keyword)
                        }
                        
                        if not any(item["title"] == adverse_item["title"] for item in adverse_media):
                            adverse_media.append(adverse_item)
            
            # Also try Serper for news
            serper_query = f"{company_name} {keyword} news"
            serper_results = search_serper(serper_query, num=5)
            
            if "organic" in serper_results:
                for result in serper_results["organic"][:2]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    url = result.get("link", "")
                    
                    if title and company_name.lower() in title.lower() and keyword in title.lower():
                        severity = determine_severity(title, snippet, keyword)
                        
                        adverse_item = {
                            "title": title,
                            "summary": snippet or "No summary available",
                            "severity": severity,
                            "date": "Recent",
                            "source": url,
                            "category": categorize_news(keyword)
                        }
                        
                        if not any(item["title"] == adverse_item["title"] for item in adverse_media):
                            adverse_media.append(adverse_item)
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"Found {len(adverse_media)} adverse media items for {company_name}")
        return adverse_media[:10]  # Return top 10 items
    
    except Exception as e:
        print(f"Adverse media search error: {str(e)}")
        return []

def determine_severity(title: str, description: str, keyword: str) -> str:
    """Determine severity based on content"""
    text = (title + " " + description).lower()
    
    if any(high_risk in text for high_risk in ["fraud", "criminal", "investigation", "lawsuit", "bankruptcy"]):
        return "High"
    elif any(medium_risk in text for medium_risk in ["controversy", "scandal", "violation"]):
        return "Medium"
    else:
        return "Low"

def categorize_news(keyword: str) -> str:
    """Categorize news based on keyword"""
    if keyword in ["lawsuit", "investigation"]:
        return "Legal"
    elif keyword in ["fraud", "bankruptcy"]:
        return "Financial"
    elif keyword in ["fine", "violation"]:
        return "Regulatory"
    else:
        return "Operational"

def comprehensive_company_search(company_name: str, country: str = "") -> Dict:
    """Perform comprehensive company search combining all sources"""
    try:
        search_term = f"{company_name} {country}".strip()
        print(f"Starting comprehensive search for: {search_term}")
        
        # Run searches with better error handling
        results = {}
        
        # Website search
        try:
            results["website_info"] = search_company_website(company_name)
        except Exception as e:
            print(f"Website search failed: {e}")
            results["website_info"] = {"error": str(e)}
        
        # Executive search (includes LinkedIn)
        try:
            executives = search_company_executives(company_name)
            results["executives"] = executives
        except Exception as e:
            print(f"Executive search failed: {e}")
            results["executives"] = []
        
        # Sanctions check
        try:
            sanctions_results = check_sanctions_databases(company_name, results.get("executives", []))
            results["sanctions_check"] = sanctions_results
        except Exception as e:
            print(f"Sanctions check failed: {e}")
            results["sanctions_check"] = {"error": str(e)}
        
        # Adverse media search
        try:
            results["adverse_media"] = search_adverse_media(company_name)
        except Exception as e:
            print(f"Adverse media search failed: {e}")
            results["adverse_media"] = []
        
        # Financial data
        try:
            results["financial_highlights"] = get_financial_data(company_name)
        except Exception as e:
            print(f"Financial search failed: {e}")
            results["financial_highlights"] = {"error": str(e)}
        
        # General searches
        try:
            results["general_search"] = search_serper(search_term, num=10)
        except Exception as e:
            print(f"General search failed: {e}")
            results["general_search"] = {"error": str(e)}
        
        try:
            results["news_search"] = search_newsapi(search_term, page_size=10)
        except Exception as e:
            print(f"News search failed: {e}")
            results["news_search"] = {"error": str(e)}
        
        print("Comprehensive search completed")
        return results
    
    except Exception as e:
        print(f"Comprehensive search failed: {str(e)}")
        return {"error": f"Comprehensive search failed: {str(e)}"}
