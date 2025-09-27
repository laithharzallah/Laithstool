"""
Demo Data Service
Provides realistic demo data when real APIs are not available or for testing
"""
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class DemoDataService:
    """Service for generating realistic demo data"""
    
    def __init__(self):
        self.companies_db = self._load_companies_database()
        self.individuals_db = self._load_individuals_database()
        
    def _load_companies_database(self) -> List[Dict]:
        """Load demo companies database"""
        return [
            {
                "name": "Samsung Electronics",
                "country": "South Korea",
                "industry": "Technology",
                "founded": "1969",
                "website": "https://www.samsung.com",
                "risk_level": "Low",
                "executives": [
                    {"name": "Jong-Hee Han", "position": "Vice Chairman & CEO"},
                    {"name": "Kyung Kye-Hyun", "position": "Vice Chairman & CEO"},
                    {"name": "Young Sohn", "position": "President & Chief Strategy Officer"}
                ],
                "adverse_media": [],
                "sanctions": 0,
                "dart_info": {
                    "corp_code": "00126380",
                    "established": "1969-01-13",
                    "address": "129, Samsung-ro, Yeongtong-gu, Suwon-si, Gyeonggi-do",
                    "ceo": "Jong-Hee Han",
                    "capital": "778,047,000,000 KRW"
                }
            },
            {
                "name": "SK Hynix",
                "country": "South Korea", 
                "industry": "Semiconductors",
                "founded": "1983",
                "website": "https://www.skhynix.com",
                "risk_level": "Low",
                "executives": [
                    {"name": "Kwak Noh-Jung", "position": "CEO"},
                    {"name": "Kim Woo-Hyun", "position": "CFO"}
                ],
                "adverse_media": [],
                "sanctions": 0,
                "dart_info": {
                    "corp_code": "00164779",
                    "established": "1983-02-15",
                    "address": "2091, Gyeongchung-daero, Bubal-eub, Icheon-si, Gyeonggi-do",
                    "ceo": "Kwak Noh-Jung",
                    "capital": "3,657,652,000,000 KRW"
                }
            },
            {
                "name": "Acme Corporation",
                "country": "United States",
                "industry": "Manufacturing",
                "founded": "1995",
                "website": "https://www.acme-corp.com",
                "risk_level": "Medium",
                "executives": [
                    {"name": "John Smith", "position": "CEO"},
                    {"name": "Sarah Johnson", "position": "CFO"},
                    {"name": "Michael Brown", "position": "COO"}
                ],
                "adverse_media": [
                    {
                        "headline": "Acme Corp faces regulatory investigation",
                        "summary": "Company under investigation for environmental compliance",
                        "date": "2024-11-15",
                        "source": "Reuters",
                        "severity": "Medium",
                        "category": "Regulatory"
                    }
                ],
                "sanctions": 0
            },
            {
                "name": "Global Trade Inc",
                "country": "Germany",
                "industry": "Import/Export",
                "founded": "2001",
                "website": "https://www.globaltrade.de",
                "risk_level": "High",
                "executives": [
                    {"name": "Hans Mueller", "position": "CEO"},
                    {"name": "Anna Schmidt", "position": "Managing Director"}
                ],
                "adverse_media": [
                    {
                        "headline": "Global Trade Inc linked to sanctions violations",
                        "summary": "Company allegedly violated international trade sanctions",
                        "date": "2024-10-22",
                        "source": "Financial Times",
                        "severity": "High",
                        "category": "Legal"
                    },
                    {
                        "headline": "Investigation into trade practices",
                        "summary": "Authorities investigating questionable trade practices",
                        "date": "2024-09-18",
                        "source": "Bloomberg",
                        "severity": "High",
                        "category": "Regulatory"
                    }
                ],
                "sanctions": 2
            }
        ]
    
    def _load_individuals_database(self) -> List[Dict]:
        """Load demo individuals database"""
        return [
            {
                "name": "John Smith",
                "country": "United Kingdom",
                "date_of_birth": "1965-03-15",
                "pep_status": False,
                "risk_level": "Low",
                "sanctions": 0,
                "adverse_media": 0,
                "aliases": []
            },
            {
                "name": "Maria Rodriguez",
                "country": "Spain",
                "date_of_birth": "1972-08-22",
                "pep_status": True,
                "pep_details": {
                    "position": "Former Minister of Economy",
                    "country": "Spain",
                    "since": "2018",
                    "source": "World-Check"
                },
                "risk_level": "Medium",
                "sanctions": 0,
                "adverse_media": 1,
                "aliases": ["Maria Rodriguez Gonzalez"]
            },
            {
                "name": "Vladimir Petrov",
                "country": "Russia",
                "date_of_birth": "1958-12-03",
                "pep_status": True,
                "pep_details": {
                    "position": "Former Deputy Minister",
                    "country": "Russia",
                    "since": "2015",
                    "source": "Dow Jones"
                },
                "risk_level": "High",
                "sanctions": 3,
                "adverse_media": 8,
                "aliases": ["V. Petrov", "Vladimir P. Petrov"]
            }
        ]
    
    def get_company_screening_data(self, company: str, country: str = "", domain: str = "") -> Dict[str, Any]:
        """Get demo company screening data"""
        # Try to find exact match first
        for comp in self.companies_db:
            if comp["name"].lower() == company.lower():
                return self._format_company_response(comp)
        
        # Try partial match
        for comp in self.companies_db:
            if company.lower() in comp["name"].lower() or comp["name"].lower() in company.lower():
                return self._format_company_response(comp)
        
        # Generate realistic random data for unknown companies
        return self._generate_company_data(company, country, domain)
    
    def get_individual_screening_data(self, name: str, country: str = "", date_of_birth: str = "") -> Dict[str, Any]:
        """Get demo individual screening data"""
        # Try to find exact match first
        for person in self.individuals_db:
            if person["name"].lower() == name.lower():
                return self._format_individual_response(person)
        
        # Try partial match
        for person in self.individuals_db:
            if any(part.lower() in person["name"].lower() for part in name.split()):
                return self._format_individual_response(person)
        
        # Generate realistic random data for unknown individuals
        return self._generate_individual_data(name, country, date_of_birth)
    
    def get_dart_search_data(self, company: str) -> Dict[str, Any]:
        """Get demo DART search data"""
        results = []
        
        # Check Korean companies in our database
        for comp in self.companies_db:
            if comp["country"] == "South Korea" and (
                company.lower() in comp["name"].lower() or 
                comp["name"].lower() in company.lower()
            ):
                if "dart_info" in comp:
                    dart_info = comp["dart_info"]
                    results.append({
                        "name": comp["name"],
                        "corp_code": dart_info["corp_code"],
                        "stock_code": "",
                        "detailed_info": {
                            "basic_info": {
                                "corp_name": comp["name"],
                                "est_dt": dart_info["established"],
                                "adr": dart_info["address"],
                                "ceo_nm": dart_info["ceo"]
                            },
                            "shareholders": [
                                {"holder": "National Pension Service", "ratio": "8.5%"},
                                {"holder": "BlackRock", "ratio": "5.2%"}
                            ]
                        }
                    })
        
        # If no Korean companies found, generate realistic data
        if not results:
            results = self._generate_dart_search_results(company)
        
        return {
            "success": True,
            "companies": results,
            "total_results": len(results)
        }
    
    def get_dart_lookup_data(self, company: str, registry_id: str = "") -> Dict[str, Any]:
        """Get demo DART lookup data"""
        # Check if we have this company in our database
        for comp in self.companies_db:
            if comp["country"] == "South Korea" and (
                company.lower() in comp["name"].lower() or 
                comp["name"].lower() in company.lower() or
                (registry_id and "dart_info" in comp and comp["dart_info"]["corp_code"] == registry_id)
            ):
                if "dart_info" in comp:
                    return self._format_dart_lookup_response(comp)
        
        # Generate realistic DART data for Korean companies
        if any(keyword in company.lower() for keyword in ["samsung", "lg", "sk", "hyundai", "korean", "korea"]):
            return self._generate_dart_lookup_data(company, registry_id)
        
        # Return error for non-Korean companies
        return {"error": "Company not found in DART registry"}
    
    def _format_company_response(self, comp: Dict) -> Dict[str, Any]:
        """Format company data for API response"""
        return {
            "company_name": comp["name"],
            "country": comp["country"],
            "domain": comp["website"],
            "overall_risk_level": comp["risk_level"],
            "industry": comp["industry"],
            "founded_year": comp["founded"],
            "website": comp["website"],
            "executives": [
                {
                    "name": exec["name"],
                    "position": exec["position"],
                    "risk_level": "Low"
                } for exec in comp["executives"]
            ],
            "metrics": {
                "sanctions": comp["sanctions"],
                "adverse_media": len(comp["adverse_media"]),
                "alerts": comp["sanctions"] + len(comp["adverse_media"])
            },
            "citations": [
                {
                    "title": media["headline"],
                    "url": f"https://example.com/news/{random.randint(1000, 9999)}"
                } for media in comp["adverse_media"]
            ],
            "executive_summary": self._generate_executive_summary(comp),
            "risk_assessment": self._generate_risk_assessment(comp),
            "timestamp": datetime.now().isoformat(),
            "real_data": {
                "company_info": {
                    "legal_name": comp["name"],
                    "website": comp["website"],
                    "industry": comp["industry"],
                    "founded_year": comp["founded"]
                },
                "executives": comp["executives"],
                "adverse_media": comp["adverse_media"]
            },
            "_providers": ["demo_data", "openai_analysis"],
            "_search_timestamp": datetime.now().isoformat(),
            "_demo_mode": True
        }
    
    def _format_individual_response(self, person: Dict) -> Dict[str, Any]:
        """Format individual data for API response"""
        return {
            "name": person["name"],
            "country": person["country"],
            "date_of_birth": person.get("date_of_birth"),
            "overall_risk_level": person["risk_level"],
            "pep_status": person["pep_status"],
            "pep_details": person.get("pep_details"),
            "aliases": person["aliases"],
            "metrics": {
                "sanctions": person["sanctions"],
                "adverse_media": person["adverse_media"],
                "pep": 1 if person["pep_status"] else 0
            },
            "citations": [
                {"title": f"Source {i+1}", "url": f"https://example.com/source/{i+1}"}
                for i in range(person["adverse_media"])
            ],
            "executive_summary": self._generate_individual_summary(person),
            "risk_assessment": self._generate_individual_risk_assessment(person),
            "timestamp": datetime.now().isoformat(),
            "raw": {
                "total_hits": person["sanctions"] + person["adverse_media"] + (1 if person["pep_status"] else 0),
                "sanctions": {"total_hits": person["sanctions"]},
                "pep": {"total_hits": 1 if person["pep_status"] else 0},
                "criminal": {"total_hits": 0},
                "other": {"total_hits": person["adverse_media"]}
            },
            "_demo_mode": True
        }
    
    def _format_dart_lookup_response(self, comp: Dict) -> Dict[str, Any]:
        """Format DART lookup data for API response"""
        dart_info = comp["dart_info"]
        return {
            "company_name": comp["name"],
            "registry_id": dart_info["corp_code"],
            "status": "Active",
            "industry_code": "26210",
            "industry_name": comp["industry"],
            "registration_date": dart_info["established"],
            "address": dart_info["address"],
            "representative": dart_info["ceo"],
            "capital": dart_info["capital"],
            "major_shareholders": [
                {"name": "National Pension Service", "ownership": "8.5%", "relationship": "Institutional Investor"},
                {"name": "BlackRock", "ownership": "5.2%", "relationship": "Institutional Investor"},
                {"name": "Vanguard", "ownership": "3.8%", "relationship": "Institutional Investor"}
            ],
            "subsidiaries": [
                {"name": f"{comp['name']} America", "ownership": "100%", "business": "Regional Operations"},
                {"name": f"{comp['name']} Europe", "ownership": "100%", "business": "Regional Operations"}
            ],
            "financial_summary": {
                "currency": "KRW",
                "revenue": {
                    "2023": random.randint(50000, 200000) * 1000000000,
                    "2024": random.randint(55000, 220000) * 1000000000
                },
                "profit": {
                    "2023": random.randint(5000, 20000) * 1000000000,
                    "2024": random.randint(5500, 22000) * 1000000000
                },
                "assets": {
                    "2023": random.randint(100000, 400000) * 1000000000,
                    "2024": random.randint(110000, 440000) * 1000000000
                }
            },
            "documents": self._generate_dart_documents(dart_info["corp_code"]),
            "timestamp": datetime.now().isoformat(),
            "_demo_mode": True
        }
    
    def _generate_company_data(self, company: str, country: str, domain: str) -> Dict[str, Any]:
        """Generate realistic company data"""
        risk_levels = ["Low", "Medium", "High"]
        risk_weights = [0.6, 0.3, 0.1]
        risk_level = random.choices(risk_levels, weights=risk_weights)[0]
        
        industries = ["Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Energy"]
        industry = random.choice(industries)
        
        # Generate executives
        exec_names = ["Alex Johnson", "Sarah Chen", "Michael Rodriguez", "Emily Davis", "David Kim"]
        positions = ["CEO", "CFO", "COO", "CTO", "VP Operations"]
        executives = []
        for i in range(random.randint(3, 5)):
            executives.append({
                "name": random.choice(exec_names),
                "position": positions[i] if i < len(positions) else "Director",
                "risk_level": random.choices(risk_levels, weights=[0.8, 0.15, 0.05])[0]
            })
        
        # Generate adverse media based on risk level
        adverse_count = 0
        adverse_media = []
        if risk_level == "High":
            adverse_count = random.randint(3, 8)
        elif risk_level == "Medium":
            adverse_count = random.randint(1, 3)
        
        for i in range(adverse_count):
            adverse_media.append({
                "headline": f"{company} faces regulatory scrutiny",
                "summary": "Company under investigation for compliance issues",
                "date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                "source": random.choice(["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal"]),
                "severity": risk_level,
                "category": random.choice(["Regulatory", "Legal", "Financial", "Environmental"])
            })
        
        sanctions = 1 if risk_level == "High" and random.random() < 0.3 else 0
        
        return {
            "company_name": company,
            "country": country or "Unknown",
            "domain": domain or f"https://www.{company.lower().replace(' ', '')}.com",
            "overall_risk_level": risk_level,
            "industry": industry,
            "founded_year": str(random.randint(1980, 2010)),
            "website": domain or f"https://www.{company.lower().replace(' ', '')}.com",
            "executives": executives,
            "metrics": {
                "sanctions": sanctions,
                "adverse_media": adverse_count,
                "alerts": sanctions + adverse_count
            },
            "citations": [
                {"title": media["headline"], "url": f"https://example.com/news/{random.randint(1000, 9999)}"}
                for media in adverse_media
            ],
            "executive_summary": f"{company} is a {industry.lower()} company with {risk_level.lower()} risk profile. {adverse_count} adverse media items found.",
            "risk_assessment": f"Overall risk assessment: {risk_level}. {'Enhanced due diligence recommended.' if risk_level == 'High' else 'Standard monitoring sufficient.'}",
            "timestamp": datetime.now().isoformat(),
            "real_data": {
                "company_info": {
                    "legal_name": company,
                    "website": domain or f"https://www.{company.lower().replace(' ', '')}.com",
                    "industry": industry,
                    "founded_year": str(random.randint(1980, 2010))
                },
                "executives": executives,
                "adverse_media": adverse_media
            },
            "_providers": ["demo_data", "generated"],
            "_search_timestamp": datetime.now().isoformat(),
            "_demo_mode": True
        }
    
    def _generate_individual_data(self, name: str, country: str, date_of_birth: str) -> Dict[str, Any]:
        """Generate realistic individual data"""
        risk_levels = ["Low", "Medium", "High"]
        risk_weights = [0.7, 0.25, 0.05]
        risk_level = random.choices(risk_levels, weights=risk_weights)[0]
        
        pep_status = random.random() < 0.2  # 20% chance of being PEP
        sanctions = 1 if risk_level == "High" and random.random() < 0.4 else 0
        adverse_media = random.randint(0, 3) if risk_level != "Low" else 0
        
        pep_details = None
        if pep_status:
            positions = ["Minister", "Senator", "Ambassador", "Judge", "Central Bank Official"]
            pep_details = {
                "position": random.choice(positions),
                "country": country or "Unknown",
                "since": str(random.randint(2010, 2023)),
                "source": random.choice(["World-Check", "Dow Jones", "LexisNexis"])
            }
        
        return {
            "name": name,
            "country": country or "Unknown",
            "date_of_birth": date_of_birth,
            "overall_risk_level": risk_level,
            "pep_status": pep_status,
            "pep_details": pep_details,
            "aliases": [f"{name} Jr.", f"{name.split()[0]} {name.split()[-1]}"] if random.random() < 0.3 else [],
            "metrics": {
                "sanctions": sanctions,
                "adverse_media": adverse_media,
                "pep": 1 if pep_status else 0
            },
            "citations": [
                {"title": f"Source {i+1}", "url": f"https://example.com/source/{i+1}"}
                for i in range(adverse_media)
            ],
            "executive_summary": f"{name} screening completed. PEP Status: {'Yes' if pep_status else 'No'}. Risk Level: {risk_level}.",
            "risk_assessment": f"Individual presents {risk_level.lower()} risk based on screening results.",
            "timestamp": datetime.now().isoformat(),
            "raw": {
                "total_hits": sanctions + adverse_media + (1 if pep_status else 0),
                "sanctions": {"total_hits": sanctions},
                "pep": {"total_hits": 1 if pep_status else 0},
                "criminal": {"total_hits": 0},
                "other": {"total_hits": adverse_media}
            },
            "_demo_mode": True
        }
    
    def _generate_dart_search_results(self, company: str) -> List[Dict]:
        """Generate realistic DART search results"""
        if not any(keyword in company.lower() for keyword in ["samsung", "lg", "sk", "hyundai", "korean", "korea"]):
            return []  # Only Korean companies in DART
        
        results = []
        for i in range(random.randint(1, 3)):
            corp_code = f"001{random.randint(10000, 99999)}"
            results.append({
                "name": f"{company} Co., Ltd." if i == 0 else f"{company} {random.choice(['Holdings', 'Electronics', 'Industries'])}",
                "corp_code": corp_code,
                "stock_code": f"{random.randint(100000, 999999)}",
                "detailed_info": {
                    "basic_info": {
                        "corp_name": f"{company} Co., Ltd.",
                        "est_dt": f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                        "adr": f"{random.randint(1, 999)} Business St, Seoul, South Korea",
                        "ceo_nm": random.choice(["Kim Min-jun", "Lee Ji-woo", "Park Seo-yeon"])
                    },
                    "shareholders": [
                        {"holder": "National Pension Service", "ratio": "8.5%"},
                        {"holder": "Foreign Institutional Investors", "ratio": "12.3%"}
                    ]
                }
            })
        
        return results
    
    def _generate_dart_lookup_data(self, company: str, registry_id: str) -> Dict[str, Any]:
        """Generate realistic DART lookup data"""
        corp_code = registry_id or f"001{random.randint(10000, 99999)}"
        
        return {
            "company_name": f"{company} Co., Ltd.",
            "registry_id": corp_code,
            "status": "Active",
            "industry_code": "26210",
            "industry_name": "Technology",
            "registration_date": f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "address": f"{random.randint(1, 999)} Business Avenue, Seoul, South Korea",
            "representative": random.choice(["Kim Min-jun", "Lee Ji-woo", "Park Seo-yeon"]),
            "capital": f"{random.randint(100000, 500000):,},000,000 KRW",
            "major_shareholders": [
                {"name": "National Pension Service", "ownership": "8.5%", "relationship": "Institutional Investor"},
                {"name": "BlackRock Inc.", "ownership": "5.2%", "relationship": "Institutional Investor"},
                {"name": "Vanguard Group", "ownership": "3.8%", "relationship": "Institutional Investor"}
            ],
            "subsidiaries": [
                {"name": f"{company} America Inc.", "ownership": "100%", "business": "Regional Operations"},
                {"name": f"{company} Europe GmbH", "ownership": "100%", "business": "Regional Operations"}
            ],
            "financial_summary": {
                "currency": "KRW",
                "revenue": {
                    "2023": random.randint(50000, 200000) * 1000000000,
                    "2024": random.randint(55000, 220000) * 1000000000
                },
                "profit": {
                    "2023": random.randint(5000, 20000) * 1000000000,
                    "2024": random.randint(5500, 22000) * 1000000000
                },
                "assets": {
                    "2023": random.randint(100000, 400000) * 1000000000,
                    "2024": random.randint(110000, 440000) * 1000000000
                }
            },
            "documents": self._generate_dart_documents(corp_code),
            "timestamp": datetime.now().isoformat(),
            "_demo_mode": True
        }
    
    def _generate_dart_documents(self, corp_code: str) -> List[Dict]:
        """Generate realistic DART documents"""
        docs = []
        doc_types = ["Annual Report", "Quarterly Report", "Audit Report", "Corporate Disclosure"]
        
        for i in range(random.randint(10, 20)):
            doc_type = random.choice(doc_types)
            year = random.choice(["2023", "2024"])
            quarter = random.choice(["Q1", "Q2", "Q3", "Q4"]) if "Quarterly" in doc_type else ""
            
            docs.append({
                "id": f"DOC{i+1:03d}",
                "title": f"{doc_type} {quarter} {year}".strip(),
                "date": f"{year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={corp_code}{year}{i:03d}"
            })
        
        return sorted(docs, key=lambda x: x["date"], reverse=True)
    
    def _generate_executive_summary(self, comp: Dict) -> str:
        """Generate executive summary for company"""
        summary = f"{comp['name']} is a {comp['industry'].lower()} company founded in {comp['founded']}. "
        summary += f"The company has an overall {comp['risk_level'].lower()} risk profile. "
        
        if comp["sanctions"] > 0:
            summary += f"There are {comp['sanctions']} active sanctions. "
        else:
            summary += "No sanctions found. "
        
        if comp["adverse_media"]:
            summary += f"Found {len(comp['adverse_media'])} adverse media items. "
        else:
            summary += "No adverse media found. "
        
        summary += f"Leadership team includes {len(comp['executives'])} key executives."
        
        return summary
    
    def _generate_risk_assessment(self, comp: Dict) -> str:
        """Generate risk assessment for company"""
        assessment = f"Based on comprehensive screening, {comp['name']} presents a {comp['risk_level'].lower()} risk. "
        
        if comp["risk_level"] == "High":
            assessment += "High risk factors include sanctions or significant adverse media. Enhanced due diligence strongly recommended."
        elif comp["risk_level"] == "Medium":
            assessment += "Medium risk factors identified. Standard due diligence with additional monitoring recommended."
        else:
            assessment += "No significant risk factors identified. Standard due diligence procedures sufficient."
        
        return assessment
    
    def _generate_individual_summary(self, person: Dict) -> str:
        """Generate executive summary for individual"""
        summary = f"{person['name']} screening completed. "
        summary += f"PEP Status: {'Yes' if person['pep_status'] else 'No'}. "
        
        if person["sanctions"] > 0:
            summary += f"Found {person['sanctions']} sanctions. "
        else:
            summary += "No sanctions found. "
        
        if person["adverse_media"] > 0:
            summary += f"Found {person['adverse_media']} adverse media items. "
        else:
            summary += "No adverse media found. "
        
        summary += f"Overall risk level: {person['risk_level']}."
        
        return summary
    
    def _generate_individual_risk_assessment(self, person: Dict) -> str:
        """Generate risk assessment for individual"""
        assessment = f"{person['name']} presents a {person['risk_level'].lower()} risk profile. "
        
        factors = []
        if person["pep_status"]:
            factors.append("PEP status")
        if person["sanctions"] > 0:
            factors.append(f"sanctions ({person['sanctions']})")
        if person["adverse_media"] > 0:
            factors.append(f"adverse media ({person['adverse_media']})")
        
        if factors:
            assessment += f"Risk factors include: {', '.join(factors)}. "
        
        if person["risk_level"] == "High":
            assessment += "Enhanced due diligence and ongoing monitoring strongly recommended."
        elif person["risk_level"] == "Medium":
            assessment += "Standard due diligence with regular monitoring recommended."
        else:
            assessment += "Standard due diligence procedures sufficient."
        
        return assessment

# Global demo data service instance
demo_data_service = DemoDataService()