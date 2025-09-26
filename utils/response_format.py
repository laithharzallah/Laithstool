"""
Standardized API response formatting
"""
from datetime import datetime
from typing import Dict, Any, Optional, List


def create_api_response(
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response
    
    Args:
        data: The main response data
        error: Error message if any
        status: Status of the request (success, error, validation_error, etc.)
        metadata: Additional metadata (request_id, timestamp, etc.)
    
    Returns:
        Standardized response dictionary
    """
    response = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
        "error": error,
        "metadata": metadata or {}
    }
    
    # Add request ID if not in metadata
    if "request_id" not in response["metadata"]:
        response["metadata"]["request_id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    # Remove None values
    return {k: v for k, v in response.items() if v is not None}


def format_company_screening_response(
    company_name: str,
    country: Optional[str],
    overall_risk_level: str,
    metrics: Dict[str, int],
    executives: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
    executive_summary: str,
    risk_assessment: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format company screening response in standardized format"""
    
    return create_api_response(
        data={
            "screening_type": "company",
            "company": {
                "name": company_name,
                "country": country,
                "risk_level": overall_risk_level,
                "risk_score": calculate_risk_score(overall_risk_level)
            },
            "risk_indicators": {
                "sanctions": metrics.get("sanctions", 0),
                "adverse_media": metrics.get("adverse_media", 0),
                "alerts": metrics.get("alerts", 0),
                "executives_flagged": sum(1 for e in executives if e.get("risk_level") == "High")
            },
            "summary": {
                "executive_summary": executive_summary,
                "risk_assessment": risk_assessment
            },
            "details": {
                "executives": executives,
                "citations": citations,
                **(additional_data or {})
            }
        },
        metadata={
            "screening_level": additional_data.get("level", "standard") if additional_data else "standard",
            "providers_used": additional_data.get("_providers", []) if additional_data else []
        }
    )


def format_individual_screening_response(
    name: str,
    country: Optional[str],
    overall_risk_level: str,
    pep_status: bool,
    metrics: Dict[str, int],
    executive_summary: str,
    risk_assessment: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format individual screening response in standardized format"""
    
    return create_api_response(
        data={
            "screening_type": "individual",
            "individual": {
                "name": name,
                "country": country,
                "risk_level": overall_risk_level,
                "risk_score": calculate_risk_score(overall_risk_level),
                "pep_status": pep_status
            },
            "risk_indicators": {
                "sanctions": metrics.get("sanctions", 0),
                "adverse_media": metrics.get("adverse_media", 0),
                "pep": metrics.get("pep", 0),
                "criminal": metrics.get("criminal", 0)
            },
            "summary": {
                "executive_summary": executive_summary,
                "risk_assessment": risk_assessment
            },
            "details": additional_data or {}
        },
        metadata={
            "screening_level": additional_data.get("level", "standard") if additional_data else "standard"
        }
    )


def format_dart_registry_response(
    company_name: str,
    registry_id: str,
    status: str,
    financial_summary: Optional[Dict[str, Any]] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format DART registry response in standardized format"""
    
    return create_api_response(
        data={
            "registry_type": "dart",
            "company": {
                "name": company_name,
                "registry_id": registry_id,
                "status": status
            },
            "financials": financial_summary or {},
            "details": additional_data or {}
        },
        metadata={
            "source": "Korean Financial Supervisory Service"
        }
    )


def calculate_risk_score(risk_level: str) -> int:
    """Calculate numeric risk score from risk level"""
    scores = {
        "Low": 85,
        "Medium": 50,
        "High": 20
    }
    return scores.get(risk_level, 50)


def format_error_response(
    error_message: str,
    status_code: int = 500,
    error_type: str = "error"
) -> Dict[str, Any]:
    """Format error response in standardized format"""
    
    return create_api_response(
        error=error_message,
        status=error_type,
        metadata={
            "status_code": status_code
        }
    )