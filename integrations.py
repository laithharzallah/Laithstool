import os, requests, json, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yfinance as yf
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional

load_dotenv()

NEWS_API_KEY   = os.getenv("NEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

def search_serper(query, num=10):
    """Enhanced Serper search with better error handling"""
    if not SERPER_API_KEY:
        return {"error":"SERPER_API_KEY missing"}
    
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type":"application/json"}
    payload = {"q": query, "num": num, "gl": "us", "hl": "en"}
    
    try:
        response = requests.post("https://google.serper.dev/search", 
                               headers=headers, json=payload, timeout=20)
        return response.json()
    except Exception as e:
        return {"error": f"Serper search failed: {str(e)}"}

def search_newsapi(query, page_size=10, language="en"):
    """Enhanced NewsAPI search"""
    if not NEWS_API_KEY:
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
        response = requests.get("https://newsapi.org/v2/everything", 
                              params=params, timeout=20)
        return response.json()
    except Exception as e:
        return {"error": f"NewsAPI search failed: {str(e)}"}

def search_company_website(company_name: str) -> Dict:
    """Search for company's official website and extract information"""
    try:
        # First try to find official website
        search_query = f"{company_name} official website"
        search_results = search_serper(search_query, num=5)
        
        if "error" in search_results:
            return {"error": search_results["error"]}
        
        website_info = {"official_website": "Not found", "title": "", "status": "Not found"}
        
        # Look for official website in search results
        if "organic" in search_results:
            for result in search_results["organic"][:3]:
                url = result.get("link", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                # Check if this looks like an official website
                if any(indicator in url.lower() for indicator in ['.com', '.org', '.net']) and \
                   any(indicator in title.lower() or indicator in snippet.lower() 
                       for indicator in ['official', 'company', company_name.lower()]):
                    website_info["official_website"] = url
                    website_info["title"] = title
                    website_info["status"] = "Found"
                    break
        
        return website_info
    except Exception as e:
        return {"error": f"Website search failed: {str(e)}"}

def get_financial_data(company_name: str, ticker: str = None) -> Dict:
    """Get financial data using yfinance and other sources"""
    try:
        financial_data = {}
        
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                financial_data.update({
                    "revenue": info.get("totalRevenue", "Not available"),
                    "employees": info.get("fullTimeEmployees", "Not available"),
                    "industry": info.get("industry", "Not available"),
                    "sector": info.get("sector", "Not available"),
                    "market_cap": info.get("marketCap", "Not available"),
                    "founded": "Not available"  # YFinance doesn't provide this
                })
            except:
                pass
        
        # Try to get additional data from Alpha Vantage if available
        if ALPHA_VANTAGE_KEY and ticker:
            try:
                url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "Symbol" in data:
                    financial_data.update({
                        "revenue": data.get("RevenueTTM", financial_data.get("revenue", "Not available")),
                        "employees": data.get("FullTimeEmployees", financial_data.get("employees", "Not available")),
                        "industry": data.get("Industry", financial_data.get("industry", "Not available")),
                        "description": data.get("Description", "")
                    })
            except:
                pass
        
        return financial_data if financial_data else {"revenue": "Not available", "employees": "Not available", "industry": "Not available", "founded": "Not available"}
    
    except Exception as e:
        return {"error": f"Financial data retrieval failed: {str(e)}"}

def search_company_executives(company_name: str) -> List[Dict]:
    """Search for company executives using multiple sources"""
    try:
        executives = []
        
        # Search for executives
        exec_query = f"{company_name} CEO CFO executives leadership team"
        search_results = search_serper(exec_query, num=10)
        
        if "organic" in search_results:
            for result in search_results["organic"][:5]:
                snippet = result.get("snippet", "")
                title = result.get("title", "")
                url = result.get("link", "")
                
                # Extract executive information from snippets using regex
                executive_patterns = [
                    r'CEO[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'Chief Executive Officer[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'CFO[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'Chief Financial Officer[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'President[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
                    r'Chairman[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)'
                ]
                
                for pattern in executive_patterns:
                    matches = re.findall(pattern, snippet + " " + title)
                    for match in matches:
                        position = "CEO" if "CEO" in pattern or "Chief Executive" in pattern else \
                                  "CFO" if "CFO" in pattern or "Chief Financial" in pattern else \
                                  "President" if "President" in pattern else "Chairman"
                        
                        executive = {
                            "name": match,
                            "position": position,
                            "background": f"Executive at {company_name}",
                            "source": url
                        }
                        
                        # Avoid duplicates
                        if not any(exec["name"] == executive["name"] for exec in executives):
                            executives.append(executive)
        
        return executives[:5]  # Return top 5 executives
    
    except Exception as e:
        return [{"error": f"Executive search failed: {str(e)}"}]

def search_adverse_media(company_name: str) -> List[Dict]:
    """Search for adverse media and negative news"""
    try:
        adverse_media = []
        
        # Search for negative news using NewsAPI
        negative_keywords = ["scandal", "lawsuit", "investigation", "fraud", "controversy", "fine", "violation", "bankruptcy"]
        
        for keyword in negative_keywords[:3]:  # Limit to avoid rate limits
            query = f"{company_name} {keyword}"
            news_results = search_newsapi(query, page_size=5)
            
            if "articles" in news_results:
                for article in news_results["articles"][:2]:  # Limit per keyword
                    title = article.get("title", "")
                    description = article.get("description", "")
                    url = article.get("url", "")
                    published_at = article.get("publishedAt", "")
                    source = article.get("source", {}).get("name", "Unknown")
                    
                    # Determine severity based on keywords
                    severity = "Medium"
                    if any(high_risk in title.lower() or high_risk in description.lower() 
                           for high_risk in ["fraud", "investigation", "lawsuit", "bankruptcy"]):
                        severity = "High"
                    elif any(low_risk in title.lower() or low_risk in description.lower() 
                            for low_risk in ["fine", "violation"]):
                        severity = "Low"
                    
                    adverse_item = {
                        "title": title,
                        "summary": description or "No summary available",
                        "severity": severity,
                        "date": published_at.split("T")[0] if published_at else "Unknown",
                        "source": url,
                        "category": "Legal" if keyword in ["lawsuit", "investigation"] else 
                                   "Financial" if keyword in ["bankruptcy", "fraud"] else "Regulatory"
                    }
                    
                    # Avoid duplicates
                    if not any(item["title"] == adverse_item["title"] for item in adverse_media):
                        adverse_media.append(adverse_item)
            
            time.sleep(0.5)  # Rate limiting
        
        return adverse_media[:10]  # Return top 10 items
    
    except Exception as e:
        return [{"error": f"Adverse media search failed: {str(e)}"}]

def comprehensive_company_search(company_name: str, country: str = "") -> Dict:
    """Perform comprehensive company search combining all sources"""
    try:
        search_term = f"{company_name} {country}".strip()
        
        # Run all searches in parallel conceptually (but sequentially to avoid rate limits)
        results = {
            "website_info": search_company_website(company_name),
            "executives": search_company_executives(company_name),
            "adverse_media": search_adverse_media(company_name),
            "financial_highlights": get_financial_data(company_name),
            "general_search": search_serper(search_term, num=10),
            "news_search": search_newsapi(search_term, page_size=10)
        }
        
        return results
    
    except Exception as e:
        return {"error": f"Comprehensive search failed: {str(e)}"}
