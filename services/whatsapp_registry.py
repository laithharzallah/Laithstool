"""
WhatsApp Registry Agent Service
Handles WhatsApp webhooks and company registry lookups via adapters
"""

import os
import re
import json
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from flask import Flask, request, jsonify

# Configure logging
logger = logging.getLogger("whatsapp-registry")

class WhatsAppRegistryService:
    """WhatsApp-based company registry lookup service"""

    def __init__(self):
        # WhatsApp configuration
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        self.whatsapp_token = os.getenv("WHATSAPP_BEARER", "")
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
        self.sender_e164 = os.getenv("WHATSAPP_SENDER_E164", "")

        # OpenAI for entity extraction
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

        logger.info("WhatsApp Registry Service initialized")

    def verify_webhook(self, token: str, challenge: str) -> Tuple[str, int]:
        """Meta webhook verification handshake"""
        if token == self.verify_token:
            return challenge, 200
        return "forbidden", 403

    def handle_inbound_message(self, data: Dict[str, Any]) -> str:
        """Process incoming WhatsApp message"""
        try:
            change = data["entry"][0]["changes"][0]["value"]
            msg = change.get("messages", [{}])[0]
            text = msg.get("text", {}).get("body", "").strip()
            wa_from = msg.get("from") or change.get("contacts", [{}])[0].get("wa_id", "")

            logger.info(f"INBOUND from {wa_from}: {text!r}")
            reply = self._handle_text(text)
            self._send_whatsapp_text(wa_from, reply)
            return "ok", 200
        except Exception as e:
            logger.exception("Inbound error: %s", e)
            return "error", 500

    def simulate_message(self, text: str, wa_from: str = "+0000000") -> Dict[str, Any]:
        """Local simulation endpoint"""
        reply = self._handle_text(text)
        return {"to": wa_from, "reply": reply}

    def _handle_text(self, text: str) -> str:
        """Process text message and return registry lookup results"""
        try:
            # 1) Extract entities using OpenAI
            entities = self._extract_entities(text)
            company_name = entities.get("company_name") or text
            country_hint = (entities.get("country_hint") or "").upper()
            address = entities.get("address") or ""

            logger.info(f"Extracted: company='{company_name}', country='{country_hint}', address='{address}'")

            # 2) Search using appropriate adapters
            candidates = []
            if country_hint == "KR":
                candidates += self._search_dart(company_name)
            if country_hint == "CN" or not country_hint:
                candidates += self._search_dilisense(company_name, address, country_hint or "CN")
            # Global fallback
            candidates += self._search_opencorporates(company_name)

            # 3) Normalize, score, and pick best matches
            best, alts = self._normalize_and_score(company_name, address, candidates)

            # 4) Format WhatsApp-friendly response
            return self._format_whatsapp_reply(company_name, best, alts)

        except Exception as e:
            logger.exception("Text handling error: %s", e)
            return "Sorry, I encountered an error processing your request. Please try again."

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Use OpenAI to extract company name, country, and address"""
        if not self.openai_api_key:
            # Fallback: extract basic company name
            return {"company_name": text.strip(), "country_hint": "", "address": ""}

        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)

            prompt = f"""
Extract company information from this text: "{text}"

Return JSON with:
- company_name: The company name
- country_hint: 2-letter country code (KR, CN, US, etc.) or empty
- address: Any address mentioned or empty

Example: {{"company_name": "Samsung Electronics", "country_hint": "KR", "address": "Seoul, South Korea"}}
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()

            # Clean JSON response
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            return json.loads(result)

        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}")
            return {"company_name": text.strip(), "country_hint": "", "address": ""}

    def _search_dart(self, company_name: str) -> List[Dict[str, Any]]:
        """Search Korea DART API"""
        # Placeholder - implement DART API integration
        logger.info(f"DART search for: {company_name}")
        return []

    def _search_dilisense(self, company_name: str, address: str = "", country: str = "") -> List[Dict[str, Any]]:
        """Search Dilisense API"""
        try:
            # Use existing Dilisense service
            from .dilisense import dilisense_service

            if not dilisense_service:
                return []

            # Perform company screening
            results = dilisense_service.screen_company(company_name, country)
            return results.get("found_records", [])

        except Exception as e:
            logger.exception(f"Dilisense search error: {e}")
            return []

    def _search_opencorporates(self, company_name: str) -> List[Dict[str, Any]]:
        """Search OpenCorporates API (global fallback)"""
        try:
            # Placeholder - implement OpenCorporates integration
            logger.info(f"OpenCorporates search for: {company_name}")
            return []

        except Exception as e:
            logger.exception(f"OpenCorporates search error: {e}")
            return []

    def _normalize_and_score(self, query: str, address: str, candidates: List[Dict[str, Any]]) -> Tuple[Optional[Dict], List[Dict]]:
        """Normalize and score company matches"""
        try:
            # Import fuzzy matching
            from rapidfuzz import fuzz
            import unicodedata

            def normalize(text: str) -> str:
                """Normalize text for comparison"""
                if not text:
                    return ""
                # Remove accents
                text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
                # Lowercase and remove extra whitespace
                text = re.sub(r'\s+', ' ', text.lower().strip())
                # Remove common company suffixes
                text = re.sub(r'\b(ltd|limited|inc|incorporated|corp|corporation|co|company|llc|gmbh|ag|sa|pte|ltd)\.?\b', '', text)
                return text.strip()

            normalized_query = normalize(query)
            scored_candidates = []

            for candidate in candidates:
                name = candidate.get('name', '')
                normalized_name = normalize(name)

                # Calculate similarity scores
                ratio = fuzz.ratio(normalized_query, normalized_name)
                token_sort = fuzz.token_sort_ratio(normalized_query, normalized_name)
                token_set = fuzz.token_set_ratio(normalized_query, normalized_name)

                # Weighted score
                score = (ratio * 0.4) + (token_sort * 0.3) + (token_set * 0.3)
                candidate['similarity_score'] = score
                candidate['normalized_name'] = normalized_name

                if score > 60:  # Minimum threshold
                    scored_candidates.append(candidate)

            # Sort by score descending
            scored_candidates.sort(key=lambda x: x['similarity_score'], reverse=True)

            best = scored_candidates[0] if scored_candidates else None
            alts = scored_candidates[1:3] if len(scored_candidates) > 1 else []

            return best, alts

        except ImportError:
            logger.warning("rapidfuzz not available, skipping normalization")
            best = candidates[0] if candidates else None
            alts = candidates[1:3] if len(candidates) > 1 else []
            return best, alts

    def _format_whatsapp_reply(self, query: str, best: Optional[Dict], alts: List[Dict]) -> str:
        """Format results for WhatsApp"""
        if not best:
            return f"❌ No company found matching '{query}'. Try providing more details or check the spelling."

        # Format main result
        name = best.get('name', 'Unknown Company')
        country = best.get('country', '')
        address = best.get('address', '')

        reply = f"✅ *{name}*\n"
        if country:
            reply += f"📍 {country}\n"
        if address:
            reply += f"🏢 {address}\n"

        # Add confidence score if available
        if 'similarity_score' in best:
            score = best['similarity_score']
            reply += f"🎯 Match confidence: {score:.1f}%\n"

        # Add alternatives if available
        if alts:
            reply += f"\n📋 Similar matches:\n"
            for i, alt in enumerate(alts[:2], 1):
                alt_name = alt.get('name', 'Unknown')
                alt_country = alt.get('country', '')
                alt_score = alt.get('similarity_score', 0)
                reply += f"{i}. {alt_name}"
                if alt_country:
                    reply += f" ({alt_country})"
                if alt_score:
                    reply += f" - {alt_score:.1f}%"
                reply += "\n"

        return reply[:4000]  # WhatsApp message limit

    def _send_whatsapp_text(self, to: str, body: str):
        """Send WhatsApp message"""
        if not self.phone_id or not self.whatsapp_token:
            logger.warning("WhatsApp credentials missing; printing reply instead.")
            print(f"[WhatsApp MOCK] to={to}:\n{body}")
            return

        url = f"https://graph.facebook.com/v20.0/{self.phone_id}/messages"
        headers = {"Authorization": f"Bearer {self.whatsapp_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": body[:4000]}
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code >= 400:
                logger.error(f"WhatsApp send failed {response.status_code}: {response.text}")
            else:
                logger.info(f"WhatsApp send ok: {response.text[:200]}")
        except Exception as e:
            logger.exception(f"WhatsApp send error: {e}")

# Global service instance
whatsapp_registry_service = WhatsAppRegistryService()
