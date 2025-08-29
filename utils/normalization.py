"""
Normalization and Scoring Utilities for Company Registry Matching
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple

try:
    from rapidfuzz import fuzz
    FUZZ_AVAILABLE = True
except ImportError:
    FUZZ_AVAILABLE = False

def normalize_and_score(query: str, address: str, candidates: List[Dict[str, Any]]) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Normalize company names, calculate similarity scores, and pick best matches

    Args:
        query: Original search query
        address: Address hint if provided
        candidates: List of company candidates from various sources

    Returns:
        Tuple of (best_match, alternative_matches)
    """
    if not candidates:
        return None, []

    if not FUZZ_AVAILABLE:
        # Fallback without fuzzy matching
        best = candidates[0] if candidates else None
        alts = candidates[1:3] if len(candidates) > 1 else []
        return best, alts

    def normalize_text(text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""

        # Remove accents and normalize
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

        # Lowercase and remove extra whitespace
        text = re.sub(r'\s+', ' ', text.lower().strip())

        # Remove common company suffixes for better matching
        suffixes = [
            r'\b(ltd|limited|inc|incorporated|corp|corporation|co|company|llc|gmbh|ag|sa|pte|ltd)\.?\b',
            r'\b(gmbh|ag|sa|pte|ltd|inc|corp|llc)\.?\b',
            r'\b(co|company)\.?\b'
        ]

        for suffix in suffixes:
            text = re.sub(suffix, '', text)

        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    # Normalize query
    normalized_query = normalize_text(query)

    # Score and sort candidates
    scored_candidates = []

    for candidate in candidates:
        name = candidate.get('name', '')
        normalized_name = normalize_text(name)

        if not normalized_name:
            continue

        # Calculate multiple similarity scores
        ratio_score = fuzz.ratio(normalized_query, normalized_name)
        token_sort_score = fuzz.token_sort_ratio(normalized_query, normalized_name)
        token_set_score = fuzz.token_set_ratio(normalized_query, normalized_name)

        # Weighted score (customize weights based on your needs)
        final_score = (ratio_score * 0.4) + (token_sort_score * 0.3) + (token_set_score * 0.3)

        # Boost score if address matches
        if address and candidate.get('address'):
            addr_query = normalize_text(address)
            addr_candidate = normalize_text(candidate['address'])
            addr_score = fuzz.token_set_ratio(addr_query, addr_candidate)
            if addr_score > 70:
                final_score += 10  # Small boost for address match

        # Boost score for official sources
        source = candidate.get('source', '').lower()
        if 'opencorporates' in source:
            final_score += 5
        elif 'dart' in source:
            final_score += 8  # Korean official source gets higher boost
        elif 'dilisense' in source:
            final_score += 3

        candidate_copy = candidate.copy()
        candidate_copy['similarity_score'] = final_score
        candidate_copy['normalized_name'] = normalized_name

        scored_candidates.append(candidate_copy)

    # Sort by score descending
    scored_candidates.sort(key=lambda x: x['similarity_score'], reverse=True)

    # Filter out very low matches
    filtered_candidates = [c for c in scored_candidates if c['similarity_score'] > 50]

    best = filtered_candidates[0] if filtered_candidates else None
    alts = filtered_candidates[1:3] if len(filtered_candidates) > 1 else []

    return best, alts

def format_whatsapp_reply(query: str, best: Optional[Dict], alts: List[Dict]) -> str:
    """
    Format company search results for WhatsApp messaging

    Args:
        query: Original search query
        best: Best matching company
        alts: Alternative matches

    Returns:
        Formatted WhatsApp message
    """
    if not best:
        return f"❌ No company found matching '{query}'. Try providing more details or check the spelling."

    # Format main result
    name = best.get('name', 'Unknown Company')
    country = best.get('country', '')
    address = best.get('address', '')
    source = best.get('source', '')

    reply = f"✅ *{name}*\n"

    if country:
        reply += f"📍 {country}\n"

    if address:
        # Truncate long addresses
        if len(address) > 100:
            address = address[:97] + "..."
        reply += f"🏢 {address}\n"

    # Add source
    if source:
        reply += f"🔍 Source: {source}\n"

    # Add confidence score if available
    if 'similarity_score' in best:
        score = best['similarity_score']
        confidence_emoji = "🎯" if score > 85 else "⚡" if score > 70 else "🤔"
        reply += f"{confidence_emoji} Match confidence: {score:.1f}%\n"

    # Add risk indicators if available (from Dilisense)
    if best.get('sanctions_found') or best.get('peps_found'):
        risk_indicators = []
        if best.get('sanctions_found'):
            risk_indicators.append("sanctions")
        if best.get('peps_found'):
            risk_indicators.append("PEP")
        if risk_indicators:
            reply += f"⚠️ Risk indicators: {', '.join(risk_indicators)}\n"

    # Add alternatives if available
    if alts:
        reply += f"\n📋 Similar matches:\n"
        for i, alt in enumerate(alts, 1):
            alt_name = alt.get('name', 'Unknown')
            alt_country = alt.get('country', '')
            alt_score = alt.get('similarity_score', 0)

            reply += f"{i}. {alt_name}"
            if alt_country:
                reply += f" ({alt_country})"
            if alt_score:
                confidence_emoji = "🎯" if alt_score > 85 else "⚡" if alt_score > 70 else "🤔"
                reply += f" {confidence_emoji}{alt_score:.1f}%"
            reply += "\n"

    # Add helpful footer
    reply += "\n💡 For detailed compliance screening, visit our web platform."

    # Ensure message fits WhatsApp limit
    return reply[:4000]

def deduplicate_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate company entries based on normalized name similarity

    Args:
        candidates: List of company candidates

    Returns:
        Deduplicated list
    """
    if not candidates or not FUZZ_AVAILABLE:
        return candidates

    def normalize_for_dedup(text: str) -> str:
        """Normalize for deduplication (stricter than scoring)"""
        if not text:
            return ""
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'\s+', ' ', text.lower().strip())
        text = re.sub(r'[^\w\s]', '', text)
        return text

    unique_candidates = []
    seen_names = set()

    for candidate in candidates:
        name = candidate.get('name', '')
        normalized = normalize_for_dedup(name)

        if normalized and normalized not in seen_names:
            seen_names.add(normalized)
            unique_candidates.append(candidate)
        elif not normalized:
            # Keep candidates without names (edge case)
            unique_candidates.append(candidate)

    return unique_candidates

def rank_by_reliability(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank candidates by data source reliability

    Args:
        candidates: List of company candidates

    Returns:
        Ranked list
    """
    reliability_scores = {
        'dart': 100,      # Korean official registry
        'opencorporates': 90,  # Global official registries
        'dilisense': 85,  # Compliance database
        'default': 50
    }

    for candidate in candidates:
        source = candidate.get('source', '').lower()
        candidate['_reliability_score'] = reliability_scores.get(source, reliability_scores['default'])

    # Sort by reliability, then by any existing score
    candidates.sort(key=lambda x: (
        x.get('_reliability_score', 0),
        x.get('similarity_score', 0)
    ), reverse=True)

    return candidates
