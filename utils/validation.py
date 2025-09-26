"""
Input validation utilities for TPRM application
"""
import re
from datetime import datetime


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_company_name(name):
    """Validate company name input"""
    if not name or not isinstance(name, str):
        raise ValidationError("Company name is required")
    
    name = name.strip()
    if len(name) < 2:
        raise ValidationError("Company name must be at least 2 characters")
    
    if len(name) > 200:
        raise ValidationError("Company name is too long (max 200 characters)")
    
    # Check for suspicious patterns (SQL injection, XSS attempts)
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'union\s+select',
        r'drop\s+table',
        r'insert\s+into',
        r'delete\s+from',
        r'update\s+set',
        r'--',
        r';\s*$'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            raise ValidationError("Invalid characters in company name")
    
    return name


def validate_person_name(name):
    """Validate individual/person name input"""
    if not name or not isinstance(name, str):
        raise ValidationError("Name is required")
    
    name = name.strip()
    if len(name) < 2:
        raise ValidationError("Name must be at least 2 characters")
    
    if len(name) > 150:
        raise ValidationError("Name is too long (max 150 characters)")
    
    # Allow letters, spaces, hyphens, apostrophes, periods
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        raise ValidationError("Name contains invalid characters")
    
    return name


def validate_country(country):
    """Validate country input"""
    if not country:
        return ""  # Country is optional
    
    if not isinstance(country, str):
        raise ValidationError("Invalid country format")
    
    country = country.strip()
    if len(country) > 100:
        raise ValidationError("Country name is too long")
    
    # Basic validation for country names
    if country and not re.match(r"^[a-zA-Z\s\-'\.]+$", country):
        raise ValidationError("Country contains invalid characters")
    
    return country


def validate_domain(domain):
    """Validate domain input"""
    if not domain:
        return ""  # Domain is optional
    
    if not isinstance(domain, str):
        raise ValidationError("Invalid domain format")
    
    domain = domain.strip().lower()
    
    # Basic domain validation
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    
    if not re.match(domain_pattern, domain):
        raise ValidationError("Invalid domain format")
    
    return domain


def validate_date_of_birth(date_str):
    """Validate date of birth input"""
    if not date_str:
        return ""  # Date of birth is optional
    
    if not isinstance(date_str, str):
        raise ValidationError("Invalid date format")
    
    try:
        # Try parsing the date
        date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        
        # Check if date is reasonable
        if date_obj > datetime.now():
            raise ValidationError("Date of birth cannot be in the future")
        
        if date_obj.year < 1900:
            raise ValidationError("Invalid date of birth")
        
        return date_str.strip()
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")


def validate_screening_level(level):
    """Validate screening level input"""
    valid_levels = ['basic', 'standard', 'enhanced']
    
    if not level:
        return 'standard'  # Default
    
    if not isinstance(level, str):
        raise ValidationError("Invalid screening level format")
    
    level = level.strip().lower()
    
    if level not in valid_levels:
        raise ValidationError(f"Invalid screening level. Must be one of: {', '.join(valid_levels)}")
    
    return level


def validate_registry_id(registry_id):
    """Validate registry ID (corp code) input"""
    if not registry_id:
        return ""  # Registry ID is optional
    
    if not isinstance(registry_id, str):
        raise ValidationError("Invalid registry ID format")
    
    registry_id = registry_id.strip()
    
    # Korean corp codes are typically numeric
    if not re.match(r'^\d{8,}$', registry_id):
        raise ValidationError("Invalid registry ID format")
    
    return registry_id


def sanitize_output(data):
    """Sanitize data for safe display in frontend"""
    if isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    elif isinstance(data, str):
        # Replace potentially dangerous characters
        return data.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    else:
        return data