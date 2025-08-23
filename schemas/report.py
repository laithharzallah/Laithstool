"""
Pydantic schemas for Company Screener structured reports.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Data confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class SentimentLevel(str, Enum):
    """News sentiment levels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class ScreeningStatus(str, Enum):
    """Task status levels"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningStep(BaseModel):
    """Individual step in the screening process"""
    name: str = Field(..., description="Step name")
    status: ScreeningStatus = Field(default=ScreeningStatus.PENDING)
    message: Optional[str] = Field(None, description="Status message")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ScreeningProgress(BaseModel):
    """Overall screening progress tracking"""
    task_id: str
    status: ScreeningStatus
    progress_percentage: int = Field(0, ge=0, le=100)
    steps: List[ScreeningStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None


class SourceReference(BaseModel):
    """Reference to a data source"""
    url: str = Field(..., description="Source URL")
    title: Optional[str] = Field(None, description="Page title")
    domain: Optional[str] = Field(None, description="Domain name")
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")


class Address(BaseModel):
    """Company address information"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    address_type: Optional[str] = Field(None, description="e.g., headquarters, registered, mailing")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    source: Optional[SourceReference] = None


class Person(BaseModel):
    """Person/executive information"""
    name: str = Field(..., description="Full name")
    role: Optional[str] = Field(None, description="Job title/position")
    department: Optional[str] = Field(None, description="Department or division")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    background: Optional[str] = Field(None, description="Professional background")
    tenure_start: Optional[str] = Field(None, description="Start date if known")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    source: Optional[SourceReference] = None


class NewsItem(BaseModel):
    """News article or media mention"""
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary")
    url: Optional[str] = Field(None, description="Article URL")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    source_name: Optional[str] = Field(None, description="Publication name")
    sentiment: SentimentLevel = Field(default=SentimentLevel.NEUTRAL)
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance to company")
    is_adverse: bool = Field(False, description="Whether this is adverse media")
    content_snippet: Optional[str] = Field(None, description="Key content excerpt")


class SanctionMatch(BaseModel):
    """Sanctions/watchlist match"""
    list_name: str = Field(..., description="Sanctions list name (e.g., OFAC SDN)")
    match_type: Literal["company", "person"] = Field(..., description="Type of entity matched")
    matched_name: str = Field(..., description="Name that matched")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    list_entry: Dict[str, Any] = Field(..., description="Raw list entry data")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    verification_url: Optional[str] = Field(None, description="Official verification URL")
    notes: Optional[str] = Field(None, description="Additional notes")


class TechStack(BaseModel):
    """Website technology stack"""
    framework: Optional[str] = None
    cms: Optional[str] = None
    analytics: List[str] = Field(default_factory=list)
    hosting: Optional[str] = None
    cdn: Optional[str] = None
    security: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)


class WebFootprint(BaseModel):
    """Digital presence and web footprint"""
    official_website: Optional[str] = Field(None, description="Main company website")
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media profiles")
    tech_stack: Optional[TechStack] = None
    domain_age: Optional[int] = Field(None, description="Domain age in years")
    ssl_certificate: Optional[Dict[str, Any]] = Field(None, description="SSL certificate info")
    website_performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    seo_insights: Optional[Dict[str, Any]] = Field(None, description="SEO analysis")


class CompanyProfile(BaseModel):
    """Core company profile information"""
    legal_name: Optional[str] = Field(None, description="Official legal name")
    trade_names: List[str] = Field(default_factory=list, description="Trading names/aliases")
    incorporation_jurisdiction: Optional[str] = Field(None, description="Jurisdiction of incorporation")
    registration_number: Optional[str] = Field(None, description="Company registration number")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    industry_codes: List[str] = Field(default_factory=list, description="Industry classification codes")
    primary_industry: Optional[str] = Field(None, description="Primary business sector")
    business_description: Optional[str] = Field(None, description="What the company does")
    founded_year: Optional[int] = Field(None, description="Year founded")
    headquarters: Optional[Address] = None
    other_addresses: List[Address] = Field(default_factory=list)
    employee_count_band: Optional[str] = Field(None, description="Employee size band")
    annual_revenue_band: Optional[str] = Field(None, description="Revenue size band")
    ownership_structure: Optional[str] = Field(None, description="Public/private/subsidiary status")
    parent_company: Optional[str] = Field(None, description="Parent company if applicable")
    subsidiaries: List[str] = Field(default_factory=list, description="Known subsidiaries")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)


class RiskFlag(BaseModel):
    """Individual risk flag"""
    category: str = Field(..., description="Risk category")
    severity: RiskLevel = Field(..., description="Risk severity")
    description: str = Field(..., description="Risk description")
    evidence: Optional[str] = Field(None, description="Supporting evidence")
    source: Optional[SourceReference] = None
    mitigation: Optional[str] = Field(None, description="Suggested mitigation")


class ExecutiveSummary(BaseModel):
    """High-level executive summary"""
    overview: str = Field(..., description="Brief company overview")
    key_points: List[str] = Field(..., description="Key findings bullet points")
    overall_risk: RiskLevel = Field(..., description="Overall risk assessment")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in findings")
    recommendation: str = Field(..., description="Due diligence recommendation")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")


class ComplianceNotes(BaseModel):
    """Compliance and methodology notes"""
    data_sources_used: List[str] = Field(default_factory=list)
    search_limitations: List[str] = Field(default_factory=list)
    confidence_notes: str = Field(..., description="Notes on data confidence")
    methodology: str = Field(..., description="Screening methodology used")
    disclaimers: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ScreeningRequest(BaseModel):
    """Input request for company screening"""
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    domain: Optional[str] = Field(None, description="Company domain (optional)")
    country: Optional[str] = Field(None, description="Country hint")
    registry_numbers: Optional[Dict[str, str]] = Field(None, description="Registry/tax numbers")
    options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "deep_crawl": True,
            "include_social": True,
            "include_sanctions": True,
            "include_financials": True,
            "include_tech_stack": False,
            "include_adverse_media": True
        },
        description="Screening options"
    )
    
    @validator('domain')
    def validate_domain(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            # Simple domain validation
            if '.' not in v:
                raise ValueError('Invalid domain format')
        return v


class ScreeningReport(BaseModel):
    """Complete screening report"""
    # Metadata
    task_id: str = Field(..., description="Unique task identifier")
    request: ScreeningRequest = Field(..., description="Original request")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: float = Field(0.0, description="Total processing time")
    
    # Core sections
    executive_summary: Optional[ExecutiveSummary] = None
    company_profile: Optional[CompanyProfile] = None
    key_people: List[Person] = Field(default_factory=list)
    web_footprint: Optional[WebFootprint] = None
    news_and_media: List[NewsItem] = Field(default_factory=list)
    sanctions_matches: List[SanctionMatch] = Field(default_factory=list)
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    
    # References and compliance
    sources_referenced: List[SourceReference] = Field(default_factory=list)
    compliance_notes: Optional[ComplianceNotes] = None
    
    # Status and quality
    completion_status: ScreeningStatus = Field(default=ScreeningStatus.COMPLETED)
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall report quality")
    data_freshness_hours: int = Field(0, description="Age of newest data in hours")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    version: Optional[str] = None