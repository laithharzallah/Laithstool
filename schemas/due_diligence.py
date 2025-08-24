from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ExecutiveInfo(BaseModel):
    name: str = Field(..., description="Full name of executive")
    position: str = Field(..., description="Job title/position")
    background: Optional[str] = Field(None, description="Professional background")
    source_url: str = Field(..., description="URL where information was found")

class SanctionFlag(BaseModel):
    entity_name: str = Field(..., description="Name found on sanctions list")
    list_name: str = Field(..., description="Sanctions list (OFAC, EU, UN, etc.)")
    match_type: str = Field(..., description="exact, partial, or alias")
    confidence: str = Field(..., description="high, medium, or low")
    source_url: str = Field(..., description="URL of sanctions list")

class AdverseMediaItem(BaseModel):
    headline: str = Field(..., description="News headline or title")
    date: Optional[str] = Field(None, description="Publication date")
    source: str = Field(..., description="News source name")
    category: str = Field(..., description="Legal, Financial, Regulatory, etc.")
    severity: str = Field(..., description="high, medium, or low")
    summary: str = Field(..., description="Brief summary of the issue")
    source_url: str = Field(..., description="URL of the article")

class PoliticalExposure(BaseModel):
    type: str = Field(..., description="PEP, Government Ownership, Political Connections")
    description: str = Field(..., description="Details of political exposure")
    confidence: str = Field(..., description="high, medium, or low")
    source_url: str = Field(..., description="URL where information was found")

class FinancialMetric(BaseModel):
    value: str = Field(..., description="Financial metric value or assessment")
    source_url: str = Field(..., description="URL where information was found")
    last_updated: Optional[str] = Field(None, description="When data was last updated")

class CompanyProfile(BaseModel):
    legal_name: str = Field(..., description="Official legal company name")
    industry: str = Field(..., description="Primary industry sector")
    founded: Optional[str] = Field(None, description="Year founded")
    employees: Optional[str] = Field(None, description="Number of employees")
    jurisdiction: str = Field(..., description="Country/jurisdiction of incorporation")
    entity_type: Optional[str] = Field(None, description="Corporation, LLC, etc.")
    status: Optional[str] = Field(None, description="Active, Dissolved, etc.")

class DueDiligenceResponse(BaseModel):
    # Executive Summary
    executive_summary: str = Field(..., description="Comprehensive overview and risk assessment")
    risk_flags: List[str] = Field(default_factory=list, description="List of identified risk factors")
    
    # Company Profile
    company_profile: CompanyProfile
    
    # Key Personnel
    key_executives: List[ExecutiveInfo] = Field(default_factory=list, description="Current executives and leadership")
    
    # Digital Presence
    official_website: Optional[str] = Field(None, description="Official company website URL")
    social_media: List[str] = Field(default_factory=list, description="Official social media URLs")
    
    # Financial Metrics (Required fields)
    ability_to_generate_cash: Optional[FinancialMetric] = Field(None, description="Cash generation capability")
    capability_of_paying_debt: Optional[FinancialMetric] = Field(None, description="Debt payment ability")
    cash_reserve: Optional[FinancialMetric] = Field(None, description="Current cash reserves")
    
    # Business Intelligence
    government_contracts: List[str] = Field(default_factory=list, description="Government contract details with URLs")
    expansion_announcements: List[str] = Field(default_factory=list, description="Recent expansion news with URLs")
    future_commitments: List[str] = Field(default_factory=list, description="Future business commitments with URLs")
    
    # Ownership
    shareholders: List[str] = Field(default_factory=list, description="Major shareholders with URLs")
    beneficial_owners: List[str] = Field(default_factory=list, description="Beneficial ownership info with URLs")
    
    # Risk Factors
    sanctions_flags: List[SanctionFlag] = Field(default_factory=list, description="Sanctions screening results")
    adverse_media: List[AdverseMediaItem] = Field(default_factory=list, description="Negative media coverage")
    political_exposure: List[PoliticalExposure] = Field(default_factory=list, description="Political risk factors")
    
    # Bribery/Corruption
    bribery_corruption: List[AdverseMediaItem] = Field(default_factory=list, description="Corruption-related issues")
    
    # Metadata
    search_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When search was performed")
    confidence_level: str = Field(default="medium", description="Overall confidence in data quality")
    citations: List[str] = Field(default_factory=list, description="All source URLs used")